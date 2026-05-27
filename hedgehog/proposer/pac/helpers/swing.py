"""ATR-filtered ZigZag swing detector.

A swing is a pivot point — a local high or low whose distance from the
prior pivot exceeds `atr_min_multiple × ATR(atr_period)`. Used by §5.1
(Measured Move impulse detection) and §6 (setup state machines).

Algorithm:
    1. Compute ATR(atr_period) over the bar series.
    2. Walk bars forward, tracking the current "direction" (up or down).
    3. In up state: extend the current high; when price drops by ≥ threshold
       from the current high, emit a 'high' pivot at the cached idx and
       switch to down state.
    4. In down state: mirror — extend low, emit 'low' on rally of ≥ threshold.

The threshold is recomputed per bar (it scales with current ATR), so a
trending market emits swings less often than a choppy market.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from .atr import compute_atr


@dataclass(frozen=True)
class Swing:
    bar_idx: int
    price: float
    kind: Literal["high", "low"]


def detect_swings(
    bars: pd.DataFrame,
    atr_min_multiple: float = 1.5,
    atr_period: int = 20,
) -> list[Swing]:
    """Detect swing pivots in `bars`.

    Returns a list of `Swing` objects in chronological order.
    Empty list if the move never exceeds the ATR threshold or there are
    too few bars to compute ATR.
    """
    if len(bars) < atr_period + 2:
        return []

    atr = compute_atr(bars, period=atr_period)
    highs = bars["high"].values
    lows = bars["low"].values

    swings: list[Swing] = []
    # Start scanning from first bar with valid ATR.
    start = atr_period - 1
    cur_high_idx = start
    cur_high_price = float(highs[start])
    cur_low_idx = start
    cur_low_price = float(lows[start])

    # Initial direction — try both, accept whichever fires first.
    direction: Literal["up", "down"] = "up"

    for i in range(start + 1, len(bars)):
        threshold = atr.iloc[i] * atr_min_multiple
        if pd.isna(threshold):
            continue

        if direction == "up":
            if highs[i] > cur_high_price:
                cur_high_price = float(highs[i])
                cur_high_idx = i
            elif cur_high_price - lows[i] >= threshold:
                # Drop from tracked high exceeded threshold — emit the high.
                swings.append(Swing(bar_idx=int(cur_high_idx), price=cur_high_price, kind="high"))
                cur_low_price = float(lows[i])
                cur_low_idx = i
                direction = "down"
        else:  # direction == "down"
            if lows[i] < cur_low_price:
                cur_low_price = float(lows[i])
                cur_low_idx = i
            elif highs[i] - cur_low_price >= threshold:
                swings.append(Swing(bar_idx=int(cur_low_idx), price=cur_low_price, kind="low"))
                cur_high_price = float(highs[i])
                cur_high_idx = i
                direction = "up"

    return swings
