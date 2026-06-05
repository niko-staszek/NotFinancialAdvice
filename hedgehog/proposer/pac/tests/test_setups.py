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


def _bear_mm() -> MeasuredMove:
    return MeasuredMove(
        id=2, direction="bear",
        a_bar=10, a_price=110.0,
        b_bar=20, b_price=100.0,  # AB span = -10
        c_bar=25, c_price=106.0,
        d_target=96.0, validity="valid",
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


# ---------------------------------------------------------------------------
# §6.2 Fail — second-attempt SHORTFALL (Bug 1: spec wants SHALLOWER 2nd attempt)
#
# strategy.md §6.2 (~562/566): "they FAIL TO REACH the same level as the first
# attempt" / "Second attempt must fail to reach the first attempt's level".
# The 2nd counter-trend attempt must be SHALLOWER than the 1st by at least
# second_attempt_shortfall_atr_multiple × ATR, then trend resumes.
# Bull MM (downward correction): shallower ⇒ 2nd low HIGHER than 1st low.
# Bear MM (upward correction):   shallower ⇒ 2nd high LOWER than 1st high.
# ---------------------------------------------------------------------------

def test_fail_bull_second_attempt_shallower_advances() -> None:
    """Bull MM: 2nd low HIGHER than 1st (shallower) → second_attempt_done."""
    mm = _bull_mm()  # a=100 b=110, fib_382 = 100 + 0.382*10 = 103.82
    cfg = Config()   # shortfall thr = 0.3 * atr
    # 1st attempt: deep low 101.0 pierces fib_382 → first_attempt_done.
    s0 = FailState(mm_id=1, state="idle")
    s1 = step_fail(s0, _bar(102.0, 102.5, 101.0, 101.5), bar_idx=26, mm=mm, atr=1.0, cfg=cfg)
    assert s1.state == "first_attempt_done"
    assert s1.first_attempt_extreme == pytest.approx(101.0)
    # 2nd attempt: SHALLOWER low 102.0 (>= 101.0 + 0.3) → advances (spec-valid).
    s2 = step_fail(s1, _bar(102.5, 103.0, 102.0, 102.7), bar_idx=27, mm=mm, atr=1.0, cfg=cfg)
    assert s2.state == "second_attempt_done"
    assert s2.second_attempt_extreme == pytest.approx(102.0)


def test_fail_bull_second_attempt_deeper_does_not_advance() -> None:
    """Bull MM: 2nd low LOWER than 1st (deeper) → must NOT advance (was the bug)."""
    mm = _bull_mm()
    cfg = Config()
    s0 = FailState(mm_id=1, state="idle")
    s1 = step_fail(s0, _bar(102.0, 102.5, 101.0, 101.5), bar_idx=26, mm=mm, atr=1.0, cfg=cfg)
    assert s1.state == "first_attempt_done"
    # 2nd attempt goes DEEPER (low 100.5 < 101.0) → spec-invalid, stays put.
    s2 = step_fail(s1, _bar(101.0, 101.5, 100.5, 100.8), bar_idx=27, mm=mm, atr=1.0, cfg=cfg)
    assert s2.state == "first_attempt_done"


def test_fail_bear_second_attempt_shallower_advances() -> None:
    """Bear MM: 2nd high LOWER than 1st (shallower) → second_attempt_done."""
    mm = _bear_mm()  # a=110 b=100, fib_382 = 110 + 0.382*(-10) = 106.18
    cfg = Config()
    s0 = FailState(mm_id=2, state="idle")
    # 1st attempt: deep high 109.0 pierces fib_382 → first_attempt_done.
    s1 = step_fail(s0, _bar(108.0, 109.0, 107.5, 108.5), bar_idx=26, mm=mm, atr=1.0, cfg=cfg)
    assert s1.state == "first_attempt_done"
    assert s1.first_attempt_extreme == pytest.approx(109.0)
    # 2nd attempt: SHALLOWER high 108.0 (<= 109.0 - 0.3) → advances (spec-valid).
    s2 = step_fail(s1, _bar(107.5, 108.0, 107.0, 107.3), bar_idx=27, mm=mm, atr=1.0, cfg=cfg)
    assert s2.state == "second_attempt_done"
    assert s2.second_attempt_extreme == pytest.approx(108.0)


def test_fail_bear_second_attempt_deeper_does_not_advance() -> None:
    """Bear MM: 2nd high HIGHER than 1st (deeper) → must NOT advance (was the bug)."""
    mm = _bear_mm()
    cfg = Config()
    s0 = FailState(mm_id=2, state="idle")
    s1 = step_fail(s0, _bar(108.0, 109.0, 107.5, 108.5), bar_idx=26, mm=mm, atr=1.0, cfg=cfg)
    assert s1.state == "first_attempt_done"
    # 2nd attempt goes DEEPER (high 109.5 > 109.0) → spec-invalid, stays put.
    s2 = step_fail(s1, _bar(108.5, 109.5, 108.0, 109.2), bar_idx=27, mm=mm, atr=1.0, cfg=cfg)
    assert s2.state == "first_attempt_done"


# ---------------------------------------------------------------------------
# §6.3 Spike & channel — 50%-WICK invalidation (Bug 2)
#
# strategy.md §6.3 (~461, emphatic): "if even a WICK penetrates past 50%
# [of A→B, = level C], the entire setup is invalidated."
# During pullback, a wick beyond C invalidates: bull low < c_price,
# bear high > c_price. The entry trigger must NOT fire if a wick breached.
# ---------------------------------------------------------------------------

def _pullback_bull_state() -> SpikeChannelState:
    """Bull S&C in pullback_active: A=100, B=116 → C=108."""
    return SpikeChannelState(
        state="pullback_active",
        a_bar=0, a_price=100.0,
        a_prime_bar=4, a_prime_price=112.0,
        b_bar=5, b_price=116.0,
        c_price=108.0,  # 50% of A→B
        direction="bull",
    )


def _pullback_bear_state() -> SpikeChannelState:
    """Bear S&C in pullback_active: A=120, B=104 → C=112."""
    return SpikeChannelState(
        state="pullback_active",
        a_bar=0, a_price=120.0,
        a_prime_bar=4, a_prime_price=108.0,
        b_bar=5, b_price=104.0,
        c_price=112.0,  # 50% of A→B
        direction="bear",
    )


def test_spike_bull_wick_past_c_invalidates() -> None:
    """Bull: wick dips below C (108) but stays above A → INVALIDATED, not triggered."""
    state = _pullback_bull_state()
    cfg = Config()
    # Wick to 105 (< C=108, > A=100), close 108.5 (>= C). Old code triggered.
    bar = _bar(open_=109.0, high=110.0, low=105.0, close=108.5)
    new_state = step_spike_channel(state, bar, bar_idx=15, bars_window=pd.DataFrame(), atr=1.0, cfg=cfg)
    assert new_state.state == "invalidated"
    assert not spike_channel_triggered(new_state)


def test_spike_bull_clean_react_at_c_triggers() -> None:
    """Bull: no wick past C, close back above C → triggers (still valid)."""
    state = _pullback_bull_state()
    cfg = Config()
    # Low 108.0 == C exactly (does NOT go past), close 109.0 above C → trigger.
    bar = _bar(open_=108.5, high=110.0, low=108.0, close=109.0)
    new_state = step_spike_channel(state, bar, bar_idx=15, bars_window=pd.DataFrame(), atr=1.0, cfg=cfg)
    assert new_state.state == "triggered"


def test_spike_bear_wick_past_c_invalidates() -> None:
    """Bear: wick spikes above C (112) but stays below A → INVALIDATED, not triggered."""
    state = _pullback_bear_state()
    cfg = Config()
    # Wick to 115 (> C=112, < A=120), close 111.5 (<= C). Old code triggered.
    bar = _bar(open_=111.0, high=115.0, low=110.0, close=111.5)
    new_state = step_spike_channel(state, bar, bar_idx=15, bars_window=pd.DataFrame(), atr=1.0, cfg=cfg)
    assert new_state.state == "invalidated"
    assert not spike_channel_triggered(new_state)


def test_spike_bear_clean_react_at_c_triggers() -> None:
    """Bear: no wick past C, close back below C → triggers (still valid)."""
    state = _pullback_bear_state()
    cfg = Config()
    # High 112.0 == C exactly (does NOT go past), close 111.0 below C → trigger.
    bar = _bar(open_=111.5, high=112.0, low=110.0, close=111.0)
    new_state = step_spike_channel(state, bar, bar_idx=15, bars_window=pd.DataFrame(), atr=1.0, cfg=cfg)
    assert new_state.state == "triggered"
