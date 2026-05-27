"""§7 Order Management — SL placement, market orders, partials, trailing, ShouldOpen.

Implements strategy_ea.md §7.
"""
from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Literal

import pandas as pd

from hedgehog.proposer.pac.config import Config
from hedgehog.proposer.pac.risk import (
    AccountState,
    check_correlation_lock,
    check_daily_dd,
    check_min_rr,
    check_news_blackout,
    check_session_cap,
    check_weekly_dd,
)


@dataclass
class Position:
    symbol: str
    direction: Literal["BUY", "SELL"]
    entry_price: float
    sl_price: float
    tp_price: float
    lot_size: float
    ts_open: datetime
    setup_type: str = "none"            # from §6: 'trap', 'fail', 'spike_channel', or 'none'
    confluence_type: str = ""
    mmd_alignment: str = ""             # 'confirmed'|'weakened'|'vetoed'
    d1_zone: str = ""
    direction_strict_at_entry: bool = True
    partial_taken: bool = False
    trailing_active: bool = False
    trailing_atr_frozen: float | None = None
    peak_price_since_activation: float | None = None
    # Task 6: trade_id is stamped at entry-open so partial-close and final-exit
    # ledger rows can share the same id. Phase-3 diff must collapse rows by
    # trade_id before applying its match-key.
    trade_id: str = ""


def compute_sl(
    signal_kind: Literal["bullish", "bearish"],
    signal_bar: pd.Series,    # has high/low/close
    spread: float,
    atr_value: float,
    cfg: Config,
) -> float:
    """§7.1 — SL beyond signal candle wick + spread + buffer.

    Bullish entry: SL = signal_bar.low - spread - wick_buffer_in_spreads × spread.
    Bearish entry: SL = signal_bar.high + spread + wick_buffer_in_spreads × spread.

    Apply min SL distance check: SL must be at least cfg.min_sl_distance_atr_multiple × atr
    away from the signal_bar.close. If not, push the SL out to that minimum.
    """
    min_distance = cfg.min_sl_distance_atr_multiple * atr_value

    if signal_kind == "bullish":
        raw_sl = signal_bar["low"] - spread - cfg.wick_buffer_in_spreads * spread
        # Ensure minimum distance below close
        if (signal_bar["close"] - raw_sl) < min_distance:
            raw_sl = signal_bar["close"] - min_distance
    else:  # bearish
        raw_sl = signal_bar["high"] + spread + cfg.wick_buffer_in_spreads * spread
        # Ensure minimum distance above close
        if (raw_sl - signal_bar["close"]) < min_distance:
            raw_sl = signal_bar["close"] + min_distance

    return raw_sl


def maybe_partial_close(
    position: Position, current_price: float, cfg: Config,
) -> Position | None:
    """§7.3 — if partials enabled and price reached 1R, return modified position with
    partial_taken=True and SL moved to entry. Otherwise return None.

    Returns None if partials disabled OR position.partial_taken is already True OR
    price hasn't reached 1R yet.
    """
    if not cfg.partials_enabled:
        return None
    if position.partial_taken:
        return None

    r = abs(position.entry_price - position.sl_price)

    if position.direction == "BUY":
        target_price = position.entry_price + cfg.partials_trigger_r * r
        reached = current_price >= target_price
    else:  # SELL
        target_price = position.entry_price - cfg.partials_trigger_r * r
        reached = current_price <= target_price

    if not reached:
        return None

    return dataclasses.replace(
        position,
        partial_taken=True,
        sl_price=position.entry_price,  # breakeven
    )


def maybe_trail_sl(
    position: Position, current_bar: pd.Series, atr_at_activation: float, cfg: Config,
) -> Position:
    """§7.4 — if trailing enabled and price reached 1.5R, activate trailing.
    Update peak_price_since_activation and ratchet SL by atr × trailing_distance.

    Returns the (possibly modified) position. Never widens SL.
    """
    if not cfg.trailing_enabled:
        return position

    r = abs(position.entry_price - position.sl_price)
    activation_level_r = cfg.trailing_activation_r

    pos = position

    if not pos.trailing_active:
        # Check if activation level is reached
        if pos.direction == "BUY":
            activation_price = pos.entry_price + activation_level_r * r
            if current_bar["high"] >= activation_price:
                pos = dataclasses.replace(
                    pos,
                    trailing_active=True,
                    trailing_atr_frozen=atr_at_activation,
                    peak_price_since_activation=current_bar["high"],
                )
            else:
                return pos
        else:  # SELL
            activation_price = pos.entry_price - activation_level_r * r
            if current_bar["low"] <= activation_price:
                pos = dataclasses.replace(
                    pos,
                    trailing_active=True,
                    trailing_atr_frozen=atr_at_activation,
                    peak_price_since_activation=current_bar["low"],
                )
            else:
                return pos

    # Trailing is active — update peak and ratchet SL
    frozen_atr = pos.trailing_atr_frozen if pos.trailing_atr_frozen is not None else atr_at_activation
    trail_distance = cfg.trailing_distance_atr_multiple * frozen_atr

    if pos.direction == "BUY":
        new_peak = max(pos.peak_price_since_activation or current_bar["high"], current_bar["high"])
        new_sl = new_peak - trail_distance
        # Never widen (SL must only move up for BUY)
        new_sl = max(new_sl, pos.sl_price)
        pos = dataclasses.replace(pos, peak_price_since_activation=new_peak, sl_price=new_sl)
    else:  # SELL
        new_peak = min(pos.peak_price_since_activation or current_bar["low"], current_bar["low"])
        new_sl = new_peak + trail_distance
        # Never widen (SL must only move down for SELL)
        new_sl = min(new_sl, pos.sl_price)
        pos = dataclasses.replace(pos, peak_price_since_activation=new_peak, sl_price=new_sl)

    return pos


def should_open(
    account: AccountState,
    direction: Literal["bull", "bear"],
    entry_price: float,
    sl_price: float,
    tp_price: float,
    composite_direction_value: Literal["bull", "bear", "neutral"],
    entry_triggered: bool,
    symbol: str,
    current_session: str,
    cfg: Config,
) -> tuple[bool, str | None]:
    """§7.5 Trade Execution Checklist — final binary gate.

    Returns (True, None) iff all checks pass; (False, rejection_reason) on first failure.

    Order of checks (short-circuit on first failure):
        1. composite_direction_value matches direction
        2. entry_triggered
        3. Risk Rules (§1): check_min_rr, check_session_cap, check_daily_dd,
           check_weekly_dd, check_correlation_lock, check_news_blackout
        4. Position size computable (sl_distance > 0)
    """
    # 1. Direction match
    if composite_direction_value != direction:
        return False, f"direction mismatch: composite={composite_direction_value}, required={direction}"

    # 2. Entry triggered
    if not entry_triggered:
        return False, "no entry trigger"

    # 3. Risk Rules
    if not check_min_rr(entry_price, sl_price, tp_price, cfg):
        return False, f"min rr not met (required {cfg.min_rr}): check entry/sl/tp levels"

    if not check_session_cap(account, current_session, cfg):
        return False, f"session cap reached: {current_session} already at {cfg.max_trades_per_session} trades"

    if not check_daily_dd(account, cfg):
        return False, f"daily drawdown limit hit ({cfg.daily_dd_stop_pct}%)"

    if not check_weekly_dd(account, cfg):
        return False, f"weekly drawdown limit hit ({cfg.weekly_dd_stop_pct}%)"

    if not check_correlation_lock(account, symbol, direction, cfg):
        return False, f"correlation lock: existing open position in correlated symbol to {symbol}"

    if not check_news_blackout(account, cfg):
        return False, "news blackout: recent high-impact news event"

    # 4. SL distance > 0
    sl_distance = abs(entry_price - sl_price)
    if sl_distance <= 0:
        return False, "position size not computable: sl_distance is zero"

    return True, None
