"""ATR(N) — Wilder-smoothed Average True Range on bar OHLC.

Per strategy_ea.md §0.4: ATR(20) is computed as the Wilder smoothed average
of true ranges over the most recent `period` closed bars. The current
forming bar (bar 0) is excluded from ATR inputs to avoid look-ahead bias —
callers must pass only closed bars to `compute_atr`.

True range per bar:
    TR_t = max(
        high_t - low_t,
        |high_t - close_{t-1}|,
        |low_t  - close_{t-1}|,
    )

Wilder smoothing after the first `period` bars (which use a simple average):
    ATR_t = (ATR_{t-1} * (period - 1) + TR_t) / period
"""
from __future__ import annotations

import pandas as pd


def compute_atr(bars: pd.DataFrame, period: int = 20) -> pd.Series:
    """Return a Series of ATR values aligned with `bars` (NaN before period fills)."""
    high = bars["high"]
    low = bars["low"]
    close = bars["close"]
    prev_close = close.shift(1)

    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # First TR has no prev_close; force it to tr1 (high - low).
    tr.iloc[0] = tr1.iloc[0]

    atr = pd.Series(index=bars.index, dtype="float64")

    # First (period - 1) values are NaN.
    if len(bars) < period:
        return atr

    # Simple average over the first `period` TR values.
    atr.iloc[period - 1] = tr.iloc[:period].mean()

    # Recursive Wilder smoothing for the rest.
    for i in range(period, len(bars)):
        atr.iloc[i] = (atr.iloc[i - 1] * (period - 1) + tr.iloc[i]) / period

    return atr
