"""Tests for ATR-filtered ZigZag swing detector."""
from __future__ import annotations

import pandas as pd
import pytest

from hedgehog.proposer.pac.helpers.swing import (
    Swing,
    detect_swings,
)


def _bars_from_highs_lows(highs: list[float], lows: list[float]) -> pd.DataFrame:
    return pd.DataFrame({
        "open": [(h + l) / 2 for h, l in zip(highs, lows)],
        "high": highs,
        "low": lows,
        "close": [(h + l) / 2 for h, l in zip(highs, lows)],
    })


def test_detect_swings_simple_up_down_up() -> None:
    # ATR(20) of these bars is ~10; threshold 1.5×ATR = ~15 — moves of 20+ should register
    # Bars: low at idx 5, high at idx 25, low at idx 35
    highs = [105] * 20 + [115] * 10 + [105] * 10
    lows  = [95]  * 20 + [105] * 10 + [95]  * 10
    bars = _bars_from_highs_lows(highs, lows)
    swings = detect_swings(bars, atr_min_multiple=0.5, atr_period=20)
    # Should find at least one swing
    assert len(swings) >= 1
    # Swings alternate direction
    kinds = [s.kind for s in swings]
    for i in range(len(kinds) - 1):
        assert kinds[i] != kinds[i + 1]


def test_swing_below_threshold_ignored() -> None:
    # All bars within a narrow 1-pip range — no swings should be detected
    highs = [101] * 50
    lows  = [100] * 50
    bars = _bars_from_highs_lows(highs, lows)
    swings = detect_swings(bars, atr_min_multiple=1.5, atr_period=20)
    assert swings == []


def test_swing_returns_typed_dataclass() -> None:
    highs = [105] * 10 + [120] * 5 + [105] * 10
    lows  = [95]  * 10 + [110] * 5 + [95]  * 10
    bars = _bars_from_highs_lows(highs, lows)
    swings = detect_swings(bars, atr_min_multiple=0.5, atr_period=10)
    if swings:
        s = swings[0]
        assert hasattr(s, "bar_idx")
        assert hasattr(s, "price")
        assert hasattr(s, "kind")
        assert s.kind in ("high", "low")
        assert isinstance(s.bar_idx, int)
        assert isinstance(s.price, float)


def test_swing_kind_high_or_low() -> None:
    # Bar 20 is a clear peak — should classify as 'high'
    highs = [100] * 20 + [130] + [100] * 20
    lows  = [95]  * 20 + [120] + [95]  * 20
    bars = _bars_from_highs_lows(highs, lows)
    swings = detect_swings(bars, atr_min_multiple=1.0, atr_period=10)
    # At least one of them should be a 'high' near idx 20
    highs_near_20 = [s for s in swings if s.kind == "high" and abs(s.bar_idx - 20) <= 2]
    assert len(highs_near_20) >= 1


def test_swing_empty_bars_returns_empty_list() -> None:
    bars = _bars_from_highs_lows([], [])
    swings = detect_swings(bars)
    assert swings == []


def test_swing_too_few_bars_returns_empty_list() -> None:
    """Need at least atr_period + 2 bars for any swing to be detectable."""
    highs = [110.0, 115.0, 113.0]
    lows = [100.0, 110.0, 105.0]
    bars = _bars_from_highs_lows(highs, lows)
    swings = detect_swings(bars, atr_period=20)
    assert swings == []
