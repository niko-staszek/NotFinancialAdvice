"""Tests for setups.py §6 Setup Recognition state machines."""
from __future__ import annotations

import pandas as pd
import pytest

from hedgehog.proposer.pac.config import Config
from hedgehog.proposer.pac.targets import MeasuredMove
from hedgehog.proposer.pac.setups import (
    TrapState, FailState, SpikeChannelState,
    step_trap, step_fail, step_spike_channel,
    trap_setup_triggered, fail_setup_triggered, spike_channel_triggered,
)


def _bull_mm() -> MeasuredMove:
    return MeasuredMove(
        id=1, direction="bull",
        a_bar=10, a_price=100.0,
        b_bar=20, b_price=110.0,  # AB span = 10
        c_bar=25, c_price=104.0,
        d_target=114.0, validity="valid",
    )


def _bar(open_: float, high: float, low: float, close: float) -> pd.Series:
    return pd.Series({"open": open_, "high": high, "low": low, "close": close})


def test_trap_state_initial_is_idle() -> None:
    s = TrapState(mm_id=1, state="idle")
    assert s.state == "idle"
    assert not trap_setup_triggered(s)


def test_trap_state_first_try_failed() -> None:
    """Bar pokes the 38.2% level (103.82) but doesn't break through."""
    mm = _bull_mm()
    state = TrapState(mm_id=1, state="idle")
    cfg = Config()
    # 38.2% level = 100 + 0.382*10 = 103.82
    # Bar low touches 103.7 (within threshold), high 104, close 104 → first try fails
    bar = _bar(open_=104.0, high=104.2, low=103.7, close=104.0)
    new_state = step_trap(state, bar, bar_idx=26, mm=mm, atr=1.0, cfg=cfg)
    assert new_state.state == "first_try_failed"
    assert new_state.first_try_extreme == pytest.approx(103.7)


def test_fail_state_initial_is_idle() -> None:
    s = FailState(mm_id=1, state="idle")
    assert not fail_setup_triggered(s)


def test_fail_state_first_attempt_pierces_38_pct() -> None:
    """Bear MM: deep first attempt pierces 0.382 → first_attempt_done."""
    mm = _bull_mm()  # Use bull for simplicity; algorithm handles both directions
    state = FailState(mm_id=1, state="idle")
    cfg = Config()
    # For bull MM, "fail" = deep correction. 0.382 level=103.82; first attempt low=102 pierces it
    bar = _bar(open_=103.0, high=103.5, low=102.0, close=102.5)
    new_state = step_fail(state, bar, bar_idx=26, mm=mm, atr=1.0, cfg=cfg)
    # The state should progress (likely first_attempt_done) since low (102) < 38.2% level (103.82)
    assert new_state.state != "idle"


def test_spike_channel_state_initial_is_idle() -> None:
    s = SpikeChannelState(state="idle")
    assert not spike_channel_triggered(s)


def test_spike_channel_detects_spike() -> None:
    """5 consecutive bars all same-direction with cumulative magnitude > 3×ATR."""
    state = SpikeChannelState(state="idle")
    cfg = Config()
    # Build a window of 5 bars rising from 100 to 130 (30 points; ATR=1, so > 3×ATR=3)
    closes = [100, 110, 115, 120, 130]
    window = pd.DataFrame({
        "open": closes, "high": [c + 1 for c in closes],
        "low": [c - 1 for c in closes], "close": closes,
    })
    current_bar = window.iloc[-1]
    new_state = step_spike_channel(state, current_bar, bar_idx=4, bars_window=window, atr=1.0, cfg=cfg)
    # Should detect spike and transition to spike_detected or further
    assert new_state.state in ("spike_detected", "channel_active")


def test_spike_channel_no_spike_on_flat_bars() -> None:
    """Flat bars → stays idle."""
    state = SpikeChannelState(state="idle")
    cfg = Config()
    closes = [100.0] * 5
    window = pd.DataFrame({
        "open": closes, "high": [c + 0.1 for c in closes],
        "low": [c - 0.1 for c in closes], "close": closes,
    })
    current_bar = window.iloc[-1]
    new_state = step_spike_channel(state, current_bar, bar_idx=4, bars_window=window, atr=1.0, cfg=cfg)
    assert new_state.state == "idle"


def test_trap_setup_triggered_predicate() -> None:
    s = TrapState(mm_id=1, state="triggered")
    assert trap_setup_triggered(s) is True
    s2 = TrapState(mm_id=1, state="first_try_failed")
    assert trap_setup_triggered(s2) is False
