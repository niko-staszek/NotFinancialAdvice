"""Tests for signals.py §4 Entry Trigger."""
from __future__ import annotations

import math

import pandas as pd
import pytest

from hedgehog.proposer.pac.config import Config
from hedgehog.proposer.pac.signals import (
    detect_signal_candle,
    passes_ema_side_rule,
    has_confluence,
)


def _bar(o: float, h: float, l: float, c: float) -> pd.Series:
    return pd.Series({"open": o, "high": h, "low": l, "close": c})


def test_bullish_signal_candle() -> None:
    """Body 1, lower wick 3, close in upper third — bullish."""
    # open=10, close=11 → body=1; low=7 → lower_wick = min(10,11)-7 = 3; high=11 → upper_wick=0
    # range = 11-7 = 4; 0.67*4 = 2.68; close (11) >= 7 + 2.68 = 9.68 ✓
    bar = _bar(o=10, h=11, l=7, c=11)
    cfg = Config()
    # ATR=2; range=4 >= 0.5*2=1 ✓; wick=3 >= 2*body(1)=2 ✓
    assert detect_signal_candle(bar, atr=2.0, cfg=cfg) == "bullish"


def test_bearish_signal_candle() -> None:
    """Body 1, upper wick 3, close in lower third — bearish."""
    bar = _bar(o=11, h=14, l=10, c=10)
    cfg = Config()
    assert detect_signal_candle(bar, atr=2.0, cfg=cfg) == "bearish"


def test_doji_returns_none() -> None:
    bar = _bar(o=10, h=11, l=9, c=10)  # body=0
    cfg = Config()
    assert detect_signal_candle(bar, atr=2.0, cfg=cfg) == "none"


def test_small_candle_returns_none() -> None:
    """Range < 0.5*ATR → none."""
    bar = _bar(o=10, h=10.4, l=10, c=10.3)  # range=0.4
    cfg = Config()
    # ATR=5; 0.5*5=2.5 > 0.4 → too small
    assert detect_signal_candle(bar, atr=5.0, cfg=cfg) == "none"


def test_insufficient_wick_returns_none() -> None:
    """Wick < 2x body → not a signal candle."""
    bar = _bar(o=10, h=12, l=9.5, c=11.9)  # body=1.9, upper_wick=0.1, lower_wick=0.5
    cfg = Config()
    assert detect_signal_candle(bar, atr=1.0, cfg=cfg) == "none"


def test_passes_ema_side_rule_bullish_above_ema() -> None:
    assert passes_ema_side_rule("bullish", bar_close=110.0, ema21_value=100.0) is True


def test_passes_ema_side_rule_bullish_below_ema_fails() -> None:
    assert passes_ema_side_rule("bullish", bar_close=90.0, ema21_value=100.0) is False


def test_passes_ema_side_rule_bearish_below_ema() -> None:
    assert passes_ema_side_rule("bearish", bar_close=90.0, ema21_value=100.0) is True


def test_passes_ema_side_rule_none_signal() -> None:
    assert passes_ema_side_rule("none", bar_close=110.0, ema21_value=100.0) is False


def test_passes_ema_side_rule_nan_ema() -> None:
    assert passes_ema_side_rule("bullish", bar_close=110.0, ema21_value=float("nan")) is False


def test_has_confluence_finds_close_level() -> None:
    bar = _bar(o=100, h=101, l=99, c=100.5)
    levels = [100.2, 105.0, 110.0]
    # §4.3: bullish signal → rejection wick is bar.low=99.
    # 100.2: |99 - 100.2| = 1.2
    # 105.0 / 110.0: distance much larger
    # threshold = 0.3 * 5 = 1.5 → 100.2 within threshold via the LOW wick
    cfg = Config()
    passed, matched, ctype = has_confluence(
        bar, levels, atr=5.0, cfg=cfg, signal_kind="bullish",
    )
    assert passed is True
    assert matched == pytest.approx(100.2)


def test_has_confluence_no_levels_in_range() -> None:
    bar = _bar(o=100, h=101, l=99, c=100.5)
    levels = [200.0, 50.0]  # far away
    cfg = Config()
    passed, matched, ctype = has_confluence(
        bar, levels, atr=1.0, cfg=cfg, signal_kind="bullish",
    )
    assert passed is False
    assert matched is None


def test_has_confluence_empty_levels() -> None:
    bar = _bar(o=100, h=101, l=99, c=100.5)
    cfg = Config()
    passed, matched, ctype = has_confluence(
        bar, [], atr=1.0, cfg=cfg, signal_kind="bullish",
    )
    assert passed is False


# ---------------------------------------------------------------------------
# §4.3 rejection-wick-only proximity (LV11) — the proximity check must use the
# rejection wick (bar.low for bullish, bar.high for bearish), NOT either wick.
# ---------------------------------------------------------------------------


def test_has_confluence_bullish_ignores_high_wick() -> None:
    """Bullish: a level touching only the HIGH wick must NOT confluence (§4.3).

    Rejection wick for bullish is bar.low=100. Level=110 sits on the (wrong)
    high wick and is far from the rejection low → spec rejects.
    """
    bar = _bar(o=101, h=110, l=100, c=109)
    levels = [110.0]  # touches bar.high exactly, but bar.high is the WRONG wick
    cfg = Config()
    # threshold = 0.3 * 5 = 1.5; |low(100) - 110| = 10 >> 1.5 → reject
    passed, matched, ctype = has_confluence(
        bar, levels, atr=5.0, cfg=cfg, signal_kind="bullish",
    )
    assert passed is False
    assert matched is None


def test_has_confluence_bullish_matches_low_wick() -> None:
    """Bullish: a level within threshold of bar.low (rejection wick) → match."""
    bar = _bar(o=101, h=110, l=100, c=109)
    levels = [100.5]  # within 0.3*5=1.5 of the rejection low=100
    cfg = Config()
    passed, matched, ctype = has_confluence(
        bar, levels, atr=5.0, cfg=cfg, signal_kind="bullish",
    )
    assert passed is True
    assert matched == pytest.approx(100.5)


def test_has_confluence_bearish_ignores_low_wick() -> None:
    """Bearish: a level touching only the LOW wick must NOT confluence (§4.3).

    Rejection wick for bearish is bar.high=110. Level=100 sits on the (wrong)
    low wick → spec rejects.
    """
    bar = _bar(o=109, h=110, l=100, c=101)
    levels = [100.0]  # touches bar.low exactly, but bar.low is the WRONG wick
    cfg = Config()
    passed, matched, ctype = has_confluence(
        bar, levels, atr=5.0, cfg=cfg, signal_kind="bearish",
    )
    assert passed is False
    assert matched is None


def test_has_confluence_bearish_matches_high_wick() -> None:
    """Bearish: a level within threshold of bar.high (rejection wick) → match."""
    bar = _bar(o=109, h=110, l=100, c=101)
    levels = [109.5]  # within 0.3*5=1.5 of the rejection high=110
    cfg = Config()
    passed, matched, ctype = has_confluence(
        bar, levels, atr=5.0, cfg=cfg, signal_kind="bearish",
    )
    assert passed is True
    assert matched == pytest.approx(109.5)
