"""§5 Target Engine — measured move detection, Fibonacci levels, cluster analysis,
extended targets, and settle buffer.

Covers strategy_ea.md §5.1 – §5.4.

Design notes:
    - EMA-CROSS ANCHOR uses the bar CLOSE at each pivot bar, NOT the swing's
      pivot wick price (§5.1: "the bar at point B must close on the opposite
      side from where the impulse started at point A. Wicks that merely touch
      the EMA do not count.").  detect_measured_moves reads close at a/b/c bar
      indices from `bars` and compares each to the EMA at the same index.

    - ATR is computed internally (20-period Wilder) from the `bars` argument.
      The caller does not need to pre-compute it.

    - C-BREACH INVALIDATION is re-derived statelessly from history each call
      (§5.1: "INVALID if price retraces beyond C before reaching D").  After
      A/B/C/D are fixed, the bars AFTER C up to the current bar are scanned:
      for a bull MM, validity flips to 'invalid' if any bar's LOW prints below
      C before any bar's HIGH reaches D; mirror for bear.  Intrabar extremes
      (low/high) are used — not closes — because the spec speaks of price
      "retracing"/"reaching", i.e. the level being touched, consistent with the
      §5.3 overshoot/D-reach test below.  This matches the rebuild-each-bar
      engine architecture (no cross-bar state).

    - OVERSHOOT_BARS is re-derived statelessly from history each call (§5.3).
      After D is first reached (a bar HIGH >= D for bull / LOW <= D for bear),
      the consecutive bars that stay BEYOND D without retracing back through it
      are counted (a bull bar holds the overshoot while its LOW >= D; a bear bar
      while its HIGH <= D).  The first bar that retraces back through D ends the
      run.  extended_mm_target fires once overshoot_bars >= overshoot_bars_min.

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

    All fields (including ``validity`` and ``overshoot_bars``) are derived
    statelessly by detect_measured_moves() from the bars-up-to-current slice.
    The engine rebuilds the MM list each bar, so no cross-bar mutation is
    required: validity and overshoot_bars are re-computed from history every
    call.
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
# §5.1 / §5.3 stateless history scanners (C-breach + overshoot)
#
# The engine rebuilds the MM list each bar from the bars-up-to-current slice,
# so both the C-breach invalidation (§5.1) and the overshoot count (§5.3) are
# re-derived from `bars` here rather than tracked across bars.
#
# Intrabar extremes (low/high) are used throughout — the spec speaks of price
# "retracing beyond C", "reaching D", and "overshooting D", i.e. the price
# level being touched within a bar, not the bar close.  This keeps the C-breach
# and the D-reach tests on the same footing.
# ---------------------------------------------------------------------------

def _bull_validity_after_c(
    bars: pd.DataFrame,
    c_bar: int,
    c_price: float,
    d_target: float,
) -> Literal["valid", "invalid"]:
    """§5.1 bull C-breach: invalid if a low prints below C before a high reaches D."""
    lows = bars["low"]
    highs = bars["high"]
    for i in range(c_bar + 1, len(bars)):
        if highs.iloc[i] >= d_target:
            return "valid"          # D reached first — breach (if any) is moot
        if lows.iloc[i] < c_price:
            return "invalid"        # retraced beyond C before reaching D
    return "valid"


def _bear_validity_after_c(
    bars: pd.DataFrame,
    c_bar: int,
    c_price: float,
    d_target: float,
) -> Literal["valid", "invalid"]:
    """§5.1 bear C-breach: invalid if a high prints above C before a low reaches D."""
    lows = bars["low"]
    highs = bars["high"]
    for i in range(c_bar + 1, len(bars)):
        if lows.iloc[i] <= d_target:
            return "valid"          # D reached first — breach (if any) is moot
        if highs.iloc[i] > c_price:
            return "invalid"        # retraced beyond C before reaching D
    return "valid"


def _bull_overshoot_bars(bars: pd.DataFrame, c_bar: int, d_target: float) -> int:
    """§5.3 bull overshoot: consecutive bars beyond D after D is first reached.

    D is "reached" on the first bar whose HIGH >= d_target.  From the bar AFTER
    that, count consecutive bars that stay beyond D (LOW >= d_target).  The
    first bar that retraces back through D (LOW < d_target) ends the run.
    Returns 0 if D is never reached.
    """
    lows = bars["low"]
    highs = bars["high"]
    n = len(bars)
    reached_at: int | None = None
    for i in range(c_bar + 1, n):
        if highs.iloc[i] >= d_target:
            reached_at = i
            break
    if reached_at is None:
        return 0
    count = 0
    for i in range(reached_at + 1, n):
        if lows.iloc[i] >= d_target:
            count += 1
        else:
            break
    return count


def _bear_overshoot_bars(bars: pd.DataFrame, c_bar: int, d_target: float) -> int:
    """§5.3 bear overshoot: mirror of bull (D reached when LOW <= d_target;
    overshoot held while HIGH <= d_target)."""
    lows = bars["low"]
    highs = bars["high"]
    n = len(bars)
    reached_at: int | None = None
    for i in range(c_bar + 1, n):
        if lows.iloc[i] <= d_target:
            reached_at = i
            break
    if reached_at is None:
        return 0
    count = 0
    for i in range(reached_at + 1, n):
        if highs.iloc[i] <= d_target:
            count += 1
        else:
            break
    return count


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
        - close at bar A < EMA at bar A  (impulse started below EMA)
        - close at bar B > EMA at bar B  (impulse CLOSED above EMA — genuine
          cross; a wick touch is not enough, §5.1)
        - close at bar C < EMA at bar C  (pullback CLOSED back below EMA)
        - C price > A price              (partial pullback, not full retest)
        - AB distance >= impulse_atr_multiple_min × ATR(B)
        - d_target = c_price + (b_price - a_price)

    Bear pattern  (A high → B low → C high): mirror of bull.

    EMA-CROSS ANCHOR uses the bar CLOSE at each pivot's bar index (read from
    `bars`), NOT the swing pivot wick price.  See module docstring.

    Each returned MM also carries:
        - validity:       'invalid' if price breached beyond C before reaching
                          D within `bars` (§5.1 C-breach), else 'valid'.
        - overshoot_bars: consecutive bars beyond D after D was first reached
                          without retracing back through D (§5.3).
    Both are re-derived from `bars` each call (stateless).

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

        # EMA-CROSS ANCHOR (§5.1): use the bar CLOSE at each pivot bar, not the
        # swing wick price.  A wick that merely touches the EMA does not count.
        close_a = float(bars["close"].iloc[a.bar_idx])
        close_b = float(bars["close"].iloc[b.bar_idx])
        close_c = float(bars["close"].iloc[c.bar_idx])

        # ---- Bull: low → high → low ----
        if a.kind == "low" and b.kind == "high" and c.kind == "low":
            ab_distance = b.price - a.price

            if ab_distance < cfg.impulse_atr_multiple_min * atr_at_b:
                continue

            # EMA-side check using bar CLOSES (see module docstring):
            #   A closed below EMA, B closed above EMA (genuine cross),
            #   C closed back below EMA.
            if not (close_a < ema_a and close_b > ema_b and close_c < ema_c):
                continue

            # C must be above A (partial pullback, not full retest).
            if c.price <= a.price:
                continue

            d_target = c.price + ab_distance
            validity = _bull_validity_after_c(bars, c.bar_idx, c.price, d_target)
            overshoot = _bull_overshoot_bars(bars, c.bar_idx, d_target)

            mms.append(MeasuredMove(
                id=next_id,
                direction="bull",
                a_bar=a.bar_idx, a_price=a.price,
                b_bar=b.bar_idx, b_price=b.price,
                c_bar=c.bar_idx, c_price=c.price,
                d_target=d_target,
                validity=validity,
                overshoot_bars=overshoot,
            ))
            next_id += 1

        # ---- Bear: high → low → high ----
        elif a.kind == "high" and b.kind == "low" and c.kind == "high":
            ab_distance = a.price - b.price

            if ab_distance < cfg.impulse_atr_multiple_min * atr_at_b:
                continue

            # EMA-side check using bar CLOSES (mirror of bull):
            #   A closed above EMA, B closed below EMA (genuine cross),
            #   C closed back above EMA.
            if not (close_a > ema_a and close_b < ema_b and close_c > ema_c):
                continue

            # C must be below A (partial pullback, not full retest).
            if c.price >= a.price:
                continue

            d_target = c.price - ab_distance
            validity = _bear_validity_after_c(bars, c.bar_idx, c.price, d_target)
            overshoot = _bear_overshoot_bars(bars, c.bar_idx, d_target)

            mms.append(MeasuredMove(
                id=next_id,
                direction="bear",
                a_bar=a.bar_idx, a_price=a.price,
                b_bar=b.bar_idx, b_price=b.price,
                c_bar=c.bar_idx, c_price=c.price,
                d_target=d_target,
                validity=validity,
                overshoot_bars=overshoot,
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
