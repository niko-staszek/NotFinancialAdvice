"""§5 Target Engine — measured move detection, Fibonacci levels, cluster analysis,
extended targets, and settle buffer.

Covers strategy_ea.md §5.1 – §5.4.

Design notes:
    - EMA-side check uses the swing's pivot *price* (the actual high/low extreme)
      rather than the bar's close.  Rationale: the swing price IS the EMA-relevant
      price at that pivot — a low swing of 94.0 clearly sits below an EMA of 95.0
      even when the bar's close happens to equal the EMA exactly.  Using bar close
      would create false negatives on borderline fixtures.  This choice is documented
      here so callers can reason about it.

    - ATR is computed internally (20-period Wilder) from the `bars` argument.
      The caller does not need to pre-compute it.

    - Validity starts at 'valid' for every newly created MM.  Downstream callers
      (engine.py) are responsible for flipping to 'invalid' when price retraces
      past C or other invalidation conditions occur.

    - find_clusters uses a forward-greedy walk: once a level has been assigned to a
      group, it is not revisited.  This means the first level in a price run anchors
      the group boundary.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import Literal

import pandas as pd

from hedgehog.proposer.pac.config import Config
from hedgehog.proposer.pac.helpers.atr import compute_atr
from hedgehog.proposer.pac.helpers.swing import Swing


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class MeasuredMove:
    """One detected AB=CD measured-move pattern.

    Fields set by detect_measured_moves(); overshoot_bars updated by engine.py
    as live price action unfolds.
    """
    id: int
    direction: Literal["bull", "bear"]
    a_bar: int
    a_price: float
    b_bar: int
    b_price: float
    c_bar: int
    c_price: float
    d_target: float
    validity: Literal["valid", "invalid"]
    overshoot_bars: int = field(default=0)


# ---------------------------------------------------------------------------
# §5.1 Measured-move detection
# ---------------------------------------------------------------------------

def detect_measured_moves(
    bars: pd.DataFrame,
    swings: list[Swing],
    ema_series: pd.Series,
    cfg: Config,
) -> list[MeasuredMove]:
    """Detect AB=CD measured-move patterns from a swing list (§5.1).

    For each consecutive triple of swings (A, B, C) the function checks whether
    the arrangement satisfies a bull or bear AB=CD pattern.

    Bull pattern  (A low → B high → C low):
        - A swing price < EMA at bar A  (pivot low clearly below EMA)
        - B swing price > EMA at bar B  (impulse crossed EMA)
        - C swing price < EMA at bar C  (pullback returned to low side)
        - C price > A price             (partial pullback, not full retest)
        - AB distance >= impulse_atr_multiple_min × ATR(B)
        - d_target = c_price + (b_price - a_price)

    Bear pattern  (A high → B low → C high): mirror of bull.

    EMA-side check uses the swing pivot *price*, not bar close.
    See module docstring for rationale.

    Returns at most cfg.max_active_measured_moves MMs (the most recent ones).
    Each MM receives a sequential integer id starting from 1.
    """
    if not swings:
        return []

    atr_series = compute_atr(bars)
    mms: list[MeasuredMove] = []
    next_id = 1

    for i in range(len(swings) - 2):
        a, b, c = swings[i], swings[i + 1], swings[i + 2]

        # Retrieve ATR at the B bar; skip if unavailable (insufficient history).
        if b.bar_idx >= len(atr_series):
            continue
        atr_at_b = atr_series.iloc[b.bar_idx]
        if pd.isna(atr_at_b):
            continue

        # Retrieve EMA values at each pivot bar.
        if (
            a.bar_idx >= len(ema_series)
            or b.bar_idx >= len(ema_series)
            or c.bar_idx >= len(ema_series)
        ):
            continue
        ema_a = ema_series.iloc[a.bar_idx]
        ema_b = ema_series.iloc[b.bar_idx]
        ema_c = ema_series.iloc[c.bar_idx]
        if pd.isna(ema_a) or pd.isna(ema_b) or pd.isna(ema_c):
            continue

        # ---- Bull: low → high → low ----
        if a.kind == "low" and b.kind == "high" and c.kind == "low":
            ab_distance = b.price - a.price

            if ab_distance < cfg.impulse_atr_multiple_min * atr_at_b:
                continue

            # EMA-side check using pivot prices (see module docstring).
            if not (a.price < ema_a and b.price > ema_b and c.price < ema_c):
                continue

            # C must be above A (partial pullback, not full retest).
            if c.price <= a.price:
                continue

            mms.append(MeasuredMove(
                id=next_id,
                direction="bull",
                a_bar=a.bar_idx, a_price=a.price,
                b_bar=b.bar_idx, b_price=b.price,
                c_bar=c.bar_idx, c_price=c.price,
                d_target=c.price + ab_distance,
                validity="valid",
            ))
            next_id += 1

        # ---- Bear: high → low → high ----
        elif a.kind == "high" and b.kind == "low" and c.kind == "high":
            ab_distance = a.price - b.price

            if ab_distance < cfg.impulse_atr_multiple_min * atr_at_b:
                continue

            if not (a.price > ema_a and b.price < ema_b and c.price > ema_c):
                continue

            # C must be below A (partial pullback, not full retest).
            if c.price >= a.price:
                continue

            mms.append(MeasuredMove(
                id=next_id,
                direction="bear",
                a_bar=a.bar_idx, a_price=a.price,
                b_bar=b.bar_idx, b_price=b.price,
                c_bar=c.bar_idx, c_price=c.price,
                d_target=c.price - ab_distance,
                validity="valid",
            ))
            next_id += 1

    # Cap to the most-recent N active MMs.
    if len(mms) > cfg.max_active_measured_moves:
        mms = mms[-cfg.max_active_measured_moves :]

    return mms


# ---------------------------------------------------------------------------
# §5.2 Fibonacci levels
# ---------------------------------------------------------------------------

def fibonacci_levels(
    bars: pd.DataFrame,
    mms: list[MeasuredMove],
    cfg: Config,
) -> list[tuple[float, str]]:
    """Compute Fibonacci retracement and extension levels for all active MMs (§5.2).

    For a bull MM with A→B impulse up:
        Retracement levels: price = a_price + ratio * (b_price - a_price)
            for each ratio in cfg.fib_levels_retracement
        Extension levels:   price = a_price + ratio * (b_price - a_price)
            for each ratio in cfg.fib_levels_extension

    Bear MM: same formula, but the A→B impulse is downward so the ratios
    naturally produce the correct levels without special-casing.

    `bars` is accepted for API consistency (not used in v1; callers may need
    it in v2 for dynamic level re-anchoring).

    Returns a flat list of (price, label) tuples from ALL valid MMs.
    """
    levels: list[tuple[float, str]] = []

    for mm in mms:
        if mm.validity != "valid":
            continue

        ab_span = mm.b_price - mm.a_price  # positive for bull, negative for bear

        for ratio in cfg.fib_levels_retracement:
            price = mm.a_price + ratio * ab_span
            levels.append((price, f"fib_R_{ratio}"))

        for ratio in cfg.fib_levels_extension:
            price = mm.a_price + ratio * ab_span
            levels.append((price, f"fib_E_{ratio}"))

    return levels


# ---------------------------------------------------------------------------
# §5.2 Cluster analysis
# ---------------------------------------------------------------------------

def find_clusters(
    levels: list[tuple[float, str]],
    atr_value: float,
    cfg: Config,
) -> list[tuple[float, list[str]]]:
    """Group nearby Fibonacci / structural levels into price clusters (§5.2).

    Algorithm:
        1. Sort levels by price (ascending).
        2. Walk forward; start a new group whenever the distance from the last
           member of the current group exceeds the threshold.
           threshold = cfg.cluster_pips_threshold_atr_multiple * atr_value
        3. Emit a cluster only if the group has >= cfg.cluster_member_min members.
           cluster_price = arithmetic mean of member prices.

    Returns a list of (cluster_price, member_labels) sorted by cluster_price.
    """
    if not levels:
        return []

    threshold = cfg.cluster_pips_threshold_atr_multiple * atr_value
    sorted_levels = sorted(levels, key=lambda x: x[0])

    clusters: list[tuple[float, list[str]]] = []
    group_prices: list[float] = [sorted_levels[0][0]]
    group_labels: list[str] = [sorted_levels[0][1]]

    for price, label in sorted_levels[1:]:
        if price - group_prices[-1] <= threshold:
            # Still within threshold of the last member — extend group.
            group_prices.append(price)
            group_labels.append(label)
        else:
            # Gap too large — flush current group if it qualifies.
            if len(group_prices) >= cfg.cluster_member_min:
                clusters.append((mean(group_prices), list(group_labels)))
            # Start fresh group.
            group_prices = [price]
            group_labels = [label]

    # Flush the last group.
    if len(group_prices) >= cfg.cluster_member_min:
        clusters.append((mean(group_prices), list(group_labels)))

    return clusters


# ---------------------------------------------------------------------------
# §5.3 Extended MM target
# ---------------------------------------------------------------------------

def extended_mm_target(
    mm: MeasuredMove,
    bars: pd.DataFrame,
    cfg: Config,
) -> float | None:
    """Return the 1.382-extension target once price overshoots D (§5.3).

    Trigger condition: mm.overshoot_bars >= cfg.overshoot_bars_min.
    Returns None if not yet triggered.

    v1: returns the 1.382 target unconditionally when triggered.
    v2 will escalate to 1.618 once the 1.382 target has been reached.

    `bars` is accepted for API consistency (unused in v1).

    Bull: extended_target = c_price + 1.382 * (b_price - a_price)
    Bear: extended_target = c_price - 1.382 * (a_price - b_price)
    """
    if mm.overshoot_bars < cfg.overshoot_bars_min:
        return None

    ab_span = abs(mm.b_price - mm.a_price)

    if mm.direction == "bull":
        return mm.c_price + 1.382 * ab_span
    else:
        return mm.c_price - 1.382 * ab_span


# ---------------------------------------------------------------------------
# §5.4 Settle buffer
# ---------------------------------------------------------------------------

def apply_settle_buffer(
    target_price: float,
    direction: Literal["bull", "bear"],
    atr_value: float,
    cfg: Config,
) -> float:
    """Offset a raw target price inward by the settle buffer (§5.4).

    The settle buffer prevents targeting the exact D level, leaving a margin
    so the trade exits before price fully reaches the target (reducing the
    risk of a late-touch miss).

    settle_buffer = cfg.settle_buffer_atr_multiple * atr_value

    Bull (long): target moves DOWN  → target_price - settle_buffer
    Bear (short): target moves UP   → target_price + settle_buffer
    """
    settle_buffer = cfg.settle_buffer_atr_multiple * atr_value

    if direction == "bull":
        return target_price - settle_buffer
    return target_price + settle_buffer
