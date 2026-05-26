"""Tests for PAC component keyword classification."""
from __future__ import annotations

import pytest

from hedgehog.proposer.pac.components import Component, classify_components


def test_signal_candle() -> None:
    out = classify_components("ładna signalka po EMA")
    assert Component.SIGNAL_CANDLE in out
    assert Component.EMA_SMA in out


def test_measured_move_polish() -> None:
    out = classify_components("miarka ruchu z poziomu 1.382")
    assert Component.MEASURED_MOVE in out
    assert Component.FIBONACCI in out


def test_session_box_and_d1() -> None:
    out = classify_components("breakout asia box, D1 promo zone bull")
    assert Component.SESSION_BOX in out
    assert Component.D1_OHLC_BIAS in out


def test_trap_and_fail_setups() -> None:
    out_trap = classify_components("trap setup po dwóch próbach")
    out_fail = classify_components("fail po głębokiej korekcie 61.8")
    assert Component.TRAP_SETUP in out_trap
    assert Component.FAIL_SETUP in out_fail


def test_spike_flag() -> None:
    out = classify_components("spike & flag na US500, wybicie kanału")
    assert Component.SPIKE_FLAG in out


def test_no_components() -> None:
    out = classify_components("dzień dobry wszystkim")
    assert out == set()


def test_mmd_clouds_polish() -> None:
    out = classify_components("MMD chmury wskazują trend bullish")
    assert Component.MMD_CLOUDS in out


@pytest.mark.parametrize("text,expected_component", [
    # Existing canonical variant — must still match.
    ("range trap zaraz po wybiciu", Component.RANGE_TRAP),
    ("range fail przy expansion", Component.RANGE_FAIL),

    # New variants the real chatdump actually uses.
    ("Range 2-Trap na EURUSD", Component.RANGE_TRAP),
    ("Range 2 try trap formuje się", Component.RANGE_TRAP),
    ("Range-2 Try Trap", Component.RANGE_TRAP),
    ("range 2 try fail po expansion", Component.RANGE_FAIL),
])
def test_range_trap_fail_widened_patterns(text: str, expected_component: Component) -> None:
    out = classify_components(text)
    assert expected_component in out
