"""§1 Risk Management — 7 risk-rule check functions per strategy_ea.md §1."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from hedgehog.proposer.pac.config import Config


@dataclass
class AccountState:
    equity: float
    starting_equity_daily: float
    starting_equity_weekly: float
    trades_this_session: dict[str, int] = field(default_factory=dict)
    # Forward reference to Position (Task 14 orders.py) — use Any for v1.
    open_positions: list[Any] = field(default_factory=list)
    last_news_event_minutes_ago: int | None = None


def compute_position_size(
    account: AccountState,
    sl_distance_pips: float,
    symbol: str,
    cfg: Config,
) -> float:
    """§1.1 — lot_size such that loss-if-SL-hit = risk_percent × equity.

    v1 assumption: $10 per pip per lot for all instruments (broker-dependent in
    reality, but consistent for single-account backtests).
    """
    risk_amount = account.equity * (cfg.risk_percent / 100.0)
    pip_value_per_lot = 10.0
    if sl_distance_pips <= 0:
        return 0.0
    lot_size = risk_amount / (sl_distance_pips * pip_value_per_lot)
    return round(lot_size, 2)


def check_min_rr(entry: float, sl: float, tp: float, cfg: Config) -> bool:
    """§1.2 — True iff |tp-entry|/|entry-sl| >= cfg.min_rr."""
    risk = abs(entry - sl)
    if risk == 0:
        return False
    rr = abs(tp - entry) / risk
    return rr >= cfg.min_rr


def check_session_cap(account: AccountState, current_session: str, cfg: Config) -> bool:
    """§1.3 — True iff trades_this_session[current_session] < cfg.max_trades_per_session."""
    count = account.trades_this_session.get(current_session, 0)
    return count < cfg.max_trades_per_session


def check_daily_dd(account: AccountState, cfg: Config) -> bool:
    """§1.4 — True iff DD% > cfg.daily_dd_stop_pct (negative threshold)."""
    if account.starting_equity_daily == 0:
        return True
    dd_pct = ((account.equity - account.starting_equity_daily) / account.starting_equity_daily) * 100.0
    return dd_pct > cfg.daily_dd_stop_pct


def check_weekly_dd(account: AccountState, cfg: Config) -> bool:
    """§1.5 — True iff weekly DD% > cfg.weekly_dd_stop_pct."""
    if account.starting_equity_weekly == 0:
        return True
    dd_pct = ((account.equity - account.starting_equity_weekly) / account.starting_equity_weekly) * 100.0
    return dd_pct > cfg.weekly_dd_stop_pct


def check_correlation_lock(
    account: AccountState, new_symbol: str, new_direction: str, cfg: Config,
) -> bool:
    """§1.6 — True iff no open position in a correlated symbol.

    v1: blocks ANY same-group position regardless of direction. v2 can refine
    with direction-aware carve-outs (e.g., long XAU + short US500 allowed).
    """
    new_canonical = new_symbol.upper()
    for group in cfg.correlation_groups:
        if new_canonical in group:
            for pos in account.open_positions:
                if isinstance(pos, dict):
                    pos_symbol = pos.get("symbol")
                else:
                    pos_symbol = getattr(pos, "symbol", None)
                if pos_symbol and pos_symbol.upper() in group and pos_symbol.upper() != new_canonical:
                    return False
    return True


def check_news_blackout(account: AccountState, cfg: Config) -> bool:
    """§1.7 — True iff news filter disabled OR no recent news event."""
    if not cfg.news_filter_enabled:
        return True
    if account.last_news_event_minutes_ago is None:
        return True
    return account.last_news_event_minutes_ago > cfg.news_filter_window_min
