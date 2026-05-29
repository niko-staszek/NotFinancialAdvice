"""Tests for risk.py §1 Risk Management."""
from __future__ import annotations

import pytest

from hedgehog.proposer.pac.config import Config
from hedgehog.proposer.pac.risk import (
    AccountState,
    compute_position_size,
    check_min_rr,
    check_session_cap,
    check_daily_dd,
    check_weekly_dd,
    check_correlation_lock,
    check_news_blackout,
)


def _account(equity: float = 10000.0) -> AccountState:
    return AccountState(
        equity=equity,
        starting_equity_daily=equity,
        starting_equity_weekly=equity,
    )


def test_compute_position_size_basic() -> None:
    cfg = Config()
    account = _account(10000.0)
    lot = compute_position_size(account, sl_distance_pips=10.0, symbol="EURUSD", cfg=cfg)
    assert lot == pytest.approx(1.0, abs=0.01)


def test_compute_position_size_tighter_sl_larger_lot() -> None:
    cfg = Config()
    account = _account(10000.0)
    lot = compute_position_size(account, sl_distance_pips=5.0, symbol="EURUSD", cfg=cfg)
    assert lot == pytest.approx(2.0, abs=0.01)


def test_compute_position_size_floors_not_rounds() -> None:
    """§1.1 — lot size must floor to the 0.01 step, never round up.

    equity=15380, risk 1% = $153.80; sl=10 pips × $10/pip/lot = $100/lot.
    raw = 153.80 / 100 = 1.538 lots. round(1.538, 2) == 1.54 (rounds UP →
    risks slightly MORE than RiskPercent); the spec requires floor → 1.53.
    """
    cfg = Config()
    account = _account(15380.0)
    lot = compute_position_size(account, sl_distance_pips=10.0, symbol="EURUSD", cfg=cfg)
    assert lot == pytest.approx(1.53, abs=1e-9)


def test_compute_position_size_below_min_rejected() -> None:
    """§1.1 — raw lots < broker minimum (0.01) → trade rejected, returns 0.0.

    equity=50, risk 1% = $0.50; sl=10 pips × $10/pip/lot = $100/lot.
    raw = 0.50 / 100 = 0.005 lots, which floors to 0.00 (< 0.01 min) → 0.0.
    """
    cfg = Config()
    account = _account(50.0)
    lot = compute_position_size(account, sl_distance_pips=10.0, symbol="EURUSD", cfg=cfg)
    assert lot == 0.0


def test_check_min_rr_passes() -> None:
    cfg = Config()
    assert check_min_rr(entry=100.0, sl=99.0, tp=102.0, cfg=cfg) is True


def test_check_min_rr_fails() -> None:
    cfg = Config()
    assert check_min_rr(entry=100.0, sl=99.0, tp=101.0, cfg=cfg) is False


def test_check_session_cap_passes_under_limit() -> None:
    cfg = Config()
    account = _account()
    account.trades_this_session["london"] = 2
    assert check_session_cap(account, "london", cfg) is True


def test_check_session_cap_fails_at_limit() -> None:
    cfg = Config()
    account = _account()
    account.trades_this_session["london"] = 3
    assert check_session_cap(account, "london", cfg) is False


def test_check_daily_dd_passes_when_above_floor() -> None:
    cfg = Config()
    account = AccountState(equity=9800.0, starting_equity_daily=10000.0, starting_equity_weekly=10000.0)
    assert check_daily_dd(account, cfg) is True


def test_check_daily_dd_fails_when_below_floor() -> None:
    cfg = Config()
    account = AccountState(equity=9600.0, starting_equity_daily=10000.0, starting_equity_weekly=10000.0)
    assert check_daily_dd(account, cfg) is False


def test_check_weekly_dd_passes() -> None:
    cfg = Config()
    account = AccountState(equity=9700.0, starting_equity_daily=10000.0, starting_equity_weekly=10000.0)
    assert check_weekly_dd(account, cfg) is True


def test_check_weekly_dd_fails() -> None:
    cfg = Config()
    account = AccountState(equity=9400.0, starting_equity_daily=10000.0, starting_equity_weekly=10000.0)
    assert check_weekly_dd(account, cfg) is False


def test_check_correlation_lock_blocks_overlap() -> None:
    cfg = Config()
    account = _account()
    account.open_positions = [{"symbol": "XAUUSD"}]
    assert check_correlation_lock(account, "US500", "BUY", cfg) is False


def test_check_correlation_lock_passes_no_overlap() -> None:
    cfg = Config()
    account = _account()
    account.open_positions = [{"symbol": "EURUSD"}]
    assert check_correlation_lock(account, "US500", "BUY", cfg) is True


def test_check_news_blackout_disabled_always_passes() -> None:
    cfg = Config()
    account = _account()
    assert check_news_blackout(account, cfg) is True


def test_check_news_blackout_enabled_within_window_fails() -> None:
    cfg = Config().replace(news_filter_enabled=True, news_filter_window_min=15)
    account = _account()
    account.last_news_event_minutes_ago = 10
    assert check_news_blackout(account, cfg) is False


def test_check_news_blackout_enabled_outside_window_passes() -> None:
    cfg = Config().replace(news_filter_enabled=True, news_filter_window_min=15)
    account = _account()
    account.last_news_event_minutes_ago = 30
    assert check_news_blackout(account, cfg) is True
