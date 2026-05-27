"""Tests for orders.py §7 Order Management + ShouldOpen Checklist."""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from hedgehog.proposer.pac.config import Config
from hedgehog.proposer.pac.orders import (
    Position,
    compute_sl,
    maybe_partial_close,
    maybe_trail_sl,
    should_open,
)
from hedgehog.proposer.pac.risk import AccountState


def _bar(o: float, h: float, l: float, c: float) -> pd.Series:
    return pd.Series({"open": o, "high": h, "low": l, "close": c})


def _account(equity: float = 10000.0) -> AccountState:
    return AccountState(equity=equity, starting_equity_daily=equity, starting_equity_weekly=equity)


def test_compute_sl_bullish_below_low() -> None:
    """Bullish SL = low - spread - wick_buffer*spread."""
    cfg = Config()  # wick_buffer_in_spreads=1
    bar = _bar(o=100, h=101, l=99, c=100.5)
    sl = compute_sl("bullish", bar, spread=0.5, atr_value=10.0, cfg=cfg)
    # SL = 99 - 0.5 - 1*0.5 = 98.0
    # min_sl_distance = 0.3 * 10 = 3; close-SL distance = 100.5 - 98 = 2.5 → push out
    # New SL = 100.5 - 3 = 97.5
    assert sl == pytest.approx(97.5, abs=0.01)


def test_compute_sl_bearish_above_high() -> None:
    cfg = Config()
    bar = _bar(o=100, h=101, l=99, c=99.5)
    sl = compute_sl("bearish", bar, spread=0.5, atr_value=10.0, cfg=cfg)
    # SL = 101 + 0.5 + 0.5 = 102.0
    # min_sl_distance = 3; SL-close = 102 - 99.5 = 2.5 → push out to 99.5 + 3 = 102.5
    assert sl == pytest.approx(102.5, abs=0.01)


def test_compute_sl_respects_natural_wick_when_wider_than_min() -> None:
    """When the wick-based SL is already wider than min, use the wick SL."""
    cfg = Config()
    bar = _bar(o=100, h=101, l=95, c=100.5)  # wide bar, low=95
    # SL = 95 - 0.5 - 0.5 = 94.0
    # min_sl_distance = 3; close-SL = 100.5 - 94 = 6.5 > 3 → keep 94
    sl = compute_sl("bullish", bar, spread=0.5, atr_value=10.0, cfg=cfg)
    assert sl == pytest.approx(94.0, abs=0.01)


def test_maybe_partial_close_disabled_returns_none() -> None:
    cfg = Config()  # partials_enabled=False
    pos = Position(
        symbol="EURUSD", direction="BUY", entry_price=100.0, sl_price=99.0, tp_price=102.0,
        lot_size=1.0, ts_open=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    assert maybe_partial_close(pos, current_price=101.0, cfg=cfg) is None


def test_maybe_partial_close_fires_at_1r() -> None:
    cfg = Config().replace(partials_enabled=True)
    pos = Position(
        symbol="EURUSD", direction="BUY", entry_price=100.0, sl_price=99.0, tp_price=102.0,
        lot_size=1.0, ts_open=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    # 1R = 1.0 (entry-SL distance). Price at 101.0 = exactly 1R above entry → fire.
    result = maybe_partial_close(pos, current_price=101.0, cfg=cfg)
    assert result is not None
    assert result.partial_taken is True
    assert result.sl_price == pytest.approx(100.0)  # moved to BE


def test_maybe_partial_close_not_fired_yet() -> None:
    cfg = Config().replace(partials_enabled=True)
    pos = Position(
        symbol="EURUSD", direction="BUY", entry_price=100.0, sl_price=99.0, tp_price=102.0,
        lot_size=1.0, ts_open=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    # Price at 100.5 — only 0.5R, not at 1R yet
    assert maybe_partial_close(pos, current_price=100.5, cfg=cfg) is None


def test_maybe_partial_close_already_taken() -> None:
    cfg = Config().replace(partials_enabled=True)
    pos = Position(
        symbol="EURUSD", direction="BUY", entry_price=100.0, sl_price=99.0, tp_price=102.0,
        lot_size=1.0, ts_open=datetime(2026, 1, 1, tzinfo=timezone.utc),
        partial_taken=True,
    )
    assert maybe_partial_close(pos, current_price=101.5, cfg=cfg) is None


def test_maybe_trail_sl_disabled_returns_unchanged() -> None:
    cfg = Config()  # trailing_enabled=False
    pos = Position(
        symbol="EURUSD", direction="BUY", entry_price=100.0, sl_price=99.0, tp_price=103.0,
        lot_size=1.0, ts_open=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    bar = _bar(o=101, h=101.5, l=100.8, c=101.2)
    result = maybe_trail_sl(pos, bar, atr_at_activation=1.0, cfg=cfg)
    assert result.trailing_active is False


def test_maybe_trail_sl_activates_at_1_5r() -> None:
    cfg = Config().replace(trailing_enabled=True)
    pos = Position(
        symbol="EURUSD", direction="BUY", entry_price=100.0, sl_price=99.0, tp_price=105.0,
        lot_size=1.0, ts_open=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    # 1.5R for entry=100, SL=99 → 100 + 1.5 = 101.5; bar high reaches 101.6
    bar = _bar(o=101, h=101.6, l=100.8, c=101.5)
    result = maybe_trail_sl(pos, bar, atr_at_activation=1.0, cfg=cfg)
    assert result.trailing_active is True
    # SL trailed to: peak (101.6) - 1.0*atr (1.0) = 100.6. Should ratchet (was 99 → 100.6)
    assert result.sl_price == pytest.approx(100.6, abs=0.01)


def test_should_open_passes_all_gates() -> None:
    cfg = Config()
    account = _account()
    passed, reason = should_open(
        account=account,
        direction="bull",
        entry_price=100.0, sl_price=99.0, tp_price=102.0,
        composite_direction_value="bull",
        entry_triggered=True,
        symbol="EURUSD",
        current_session="london",
        cfg=cfg,
    )
    assert passed is True
    assert reason is None


def test_should_open_blocks_on_direction_mismatch() -> None:
    cfg = Config()
    account = _account()
    passed, reason = should_open(
        account=account,
        direction="bull",
        entry_price=100.0, sl_price=99.0, tp_price=102.0,
        composite_direction_value="neutral",  # blocks
        entry_triggered=True,
        symbol="EURUSD",
        current_session="london",
        cfg=cfg,
    )
    assert passed is False
    assert reason and "direction" in reason.lower()


def test_should_open_blocks_on_no_entry_trigger() -> None:
    cfg = Config()
    account = _account()
    passed, reason = should_open(
        account=account, direction="bull",
        entry_price=100.0, sl_price=99.0, tp_price=102.0,
        composite_direction_value="bull",
        entry_triggered=False,  # blocks
        symbol="EURUSD", current_session="london", cfg=cfg,
    )
    assert passed is False
    assert reason and "trigger" in reason.lower()


def test_should_open_blocks_on_min_rr_fail() -> None:
    cfg = Config()
    account = _account()
    # Entry 100, SL 99, TP 100.5 → R:R = 0.5, below 1.5
    passed, reason = should_open(
        account=account, direction="bull",
        entry_price=100.0, sl_price=99.0, tp_price=100.5,
        composite_direction_value="bull",
        entry_triggered=True,
        symbol="EURUSD", current_session="london", cfg=cfg,
    )
    assert passed is False
    assert reason and ("rr" in reason.lower() or "ratio" in reason.lower())


def test_should_open_blocks_on_session_cap() -> None:
    cfg = Config()
    account = _account()
    account.trades_this_session["london"] = 3  # at cap
    passed, reason = should_open(
        account=account, direction="bull",
        entry_price=100.0, sl_price=99.0, tp_price=102.0,
        composite_direction_value="bull",
        entry_triggered=True,
        symbol="EURUSD", current_session="london", cfg=cfg,
    )
    assert passed is False
    assert reason and ("session" in reason.lower() or "cap" in reason.lower())
