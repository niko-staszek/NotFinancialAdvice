"""Tests for ATR(20) Wilder-smoothed calculation per strategy_ea.md §0.4."""
from __future__ import annotations

import pandas as pd
import pytest

from hedgehog.proposer.pac.helpers.atr import compute_atr


def _bars(highs: list[float], lows: list[float], closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"high": highs, "low": lows, "close": closes})


def test_atr_first_period_simple_average() -> None:
    # 20 bars each with high=110, low=100, close=105 → TR=10, ATR=10
    bars = _bars(highs=[110] * 20, lows=[100] * 20, closes=[105] * 20)
    atr = compute_atr(bars, period=20)
    # Position 19 is the 20th bar (index 0-based) — Wilder ATR is defined from index 19 onwards
    assert atr.iloc[19] == pytest.approx(10.0)


def test_atr_returns_nan_before_period_full() -> None:
    bars = _bars(highs=[110] * 20, lows=[100] * 20, closes=[105] * 20)
    atr = compute_atr(bars, period=20)
    # Indices 0..18 are NaN — not enough bars yet
    for i in range(19):
        assert pd.isna(atr.iloc[i])


def test_atr_wilder_smoothing_after_period() -> None:
    # Spike on bar 20 (index 20) — TR jumps from 10 to 30
    highs = [110.0] * 20 + [130.0]
    lows = [100.0] * 20 + [100.0]
    closes = [105.0] * 20 + [125.0]
    bars = _bars(highs=highs, lows=lows, closes=closes)
    atr = compute_atr(bars, period=20)
    # Wilder formula: new_atr = ((prev_atr * (period - 1)) + new_tr) / period
    # prev_atr = 10, new_tr = 30 → (10*19 + 30) / 20 = 220/20 = 11.0
    assert atr.iloc[20] == pytest.approx(11.0)


def test_atr_uses_true_range_with_gap() -> None:
    # Bar 1 closes at 105; bar 2 opens with high=115, low=112, close=113 — gap up
    # True range = max(high-low, |high-prev_close|, |low-prev_close|) = max(3, 10, 7) = 10
    highs = [110.0, 115.0]
    lows = [100.0, 112.0]
    closes = [105.0, 113.0]
    bars = _bars(highs=highs, lows=lows, closes=closes)
    atr = compute_atr(bars, period=2)
    # period=2 → atr from index 1
    # TR bar 0 = 110-100 = 10 (no prev_close); TR bar 1 = max(3, |115-105|, |112-105|) = 10
    # ATR(2) at index 1 = avg(10, 10) = 10
    assert atr.iloc[1] == pytest.approx(10.0)
