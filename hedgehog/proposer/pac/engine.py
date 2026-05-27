"""Event-driven bar-loop orchestrator — wires all 12 PAC modules together.

This is the integration centrepiece of Plan 4.  It processes M5 bars one at a
time, applies the full §3–§7 decision chain, opens and manages positions, and
writes closed-trade rows to the ledger.

v1 simplifications (each marked TODO for the phase they will be resolved):
    - D1 promo zone: when ``d1_bars`` is supplied to ``run_backtest`` the
      engine resolves the §3.3 zone via the previous UTC calendar day's D1
      bar (Task 4). When omitted, the zone defaults to 'neutral' for
      backward compatibility.
    - Asia / dead sessions produce no entries (deferred per spec). TODO Phase 5.
    - Setup state machines (§6) are not updated inside the loop; setup_type is
      logged as 'none'. TODO Phase 3 journaling.
    - pip_value = $10 per pip per lot (broker-independent approximation). TODO real data.
    - SL/TP hit resolution uses bar high/low (no intrabar modelling). Acceptable for M5.
"""
from __future__ import annotations

import uuid
from datetime import timezone
from typing import Any

import pandas as pd

from .bars import BarsMetadata
from .config import Config
from .helpers.atr import compute_atr
from .helpers.swing import detect_swings
from .helpers.timeutil import session_for
from .ledger import LedgerRow, TradeLedger
from .mmd import compute_clouds
from .orders import Position, compute_sl, maybe_partial_close, maybe_trail_sl, should_open
from .risk import AccountState, compute_position_size
from .setups import (
    FailState,
    SpikeChannelState,
    TrapState,
    step_fail,
    step_spike_channel,
    step_trap,
)
from .signals import (
    composite_direction,
    d1_promo_zone,
    detect_signal_candle,
    has_confluence,
    mmd_alignment,
    passes_ema_side_rule,
    sentiment,
    session_box_position,
)
from .targets import (
    MeasuredMove,
    apply_settle_buffer,
    detect_measured_moves,
    extended_mm_target,
    fibonacci_levels,
    find_clusters,
)
from .universe import lookup_pip_factor, normalize_symbol

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PIP_VALUE_PER_LOT = 10.0   # v1: $10 per pip per lot, all instruments
_WARMUP_EXTRA = 50          # bars beyond sma_period before we start evaluating


# ---------------------------------------------------------------------------
# Pip conversion helper — single source of truth for price→pips
# ---------------------------------------------------------------------------

def _price_distance_to_pips(symbol: str, distance_price: float) -> float:
    """Convert a raw price-unit distance to pip count via the symbol's pip factor.

    The symbol is canonicalized via ``normalize_symbol`` before lookup, so
    callers don't need to pre-canonicalize. Centralises the
    ``lookup_pip_factor(normalize_symbol(symbol)) * distance`` pattern used at
    the position-sizing boundary (Task 3) and inside ``_compute_trade_pnl``
    (Task 3b).
    """
    return distance_price * lookup_pip_factor(normalize_symbol(symbol))


# ---------------------------------------------------------------------------
# D1 promo-zone helpers (Task 4)
# ---------------------------------------------------------------------------

def _resolve_d1_zone_for_bar(
    signal_bar_time: pd.Timestamp,
    current_price: float,
    d1_bars: pd.DataFrame | None,
) -> str:
    """Resolve the §3.3 D1 promo zone for one signal bar.

    Delegates to :func:`signals.d1_promo_zone`, which itself looks up the
    previous-day D1 bar relative to ``signal_bar_time`` and classifies
    ``current_price`` against its body/wicks.

    Returns ``'neutral'`` if ``d1_bars`` is None (v1-pre-fix backward-compat
    behavior).
    """
    if d1_bars is None:
        return "neutral"
    # Convert the signal bar timestamp to a tz-aware UTC datetime for
    # signals.d1_promo_zone(), which compares on date().
    current_utc = signal_bar_time
    if hasattr(current_utc, "to_pydatetime"):
        current_utc = current_utc.to_pydatetime()
    if current_utc.tzinfo is None:
        current_utc = current_utc.replace(tzinfo=timezone.utc)
    return d1_promo_zone(
        d1_bars=d1_bars,
        current_utc=current_utc,
        current_price=current_price,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_backtest(
    bars: pd.DataFrame,
    symbol: str,
    cfg: Config,
    ledger: TradeLedger,
    initial_equity: float = 10_000.0,
    d1_bars: pd.DataFrame | None = None,
) -> dict:
    """Run the event-driven bar loop.

    Parameters
    ----------
    d1_bars : pd.DataFrame | None, optional
        Daily (D1) OHLC bars with columns ``time_utc, open, high, low, close``.
        When supplied, each signal bar resolves the §3.3 D1 promo zone against
        the *previous* UTC calendar day's D1 bar. When None (default), the
        zone is hardcoded to ``'neutral'`` for v1-pre-fix backward compatibility.

    Returns a summary dict:
        {
            'bars_processed': int,
            'trades_opened':  int,
            'trades_closed':  int,
            'final_equity':   float,
            'final_pnl':      float,
        }
    """
    if len(bars) == 0:
        return {
            "bars_processed": 0,
            "trades_opened":  0,
            "trades_closed":  0,
            "final_equity":   initial_equity,
            "final_pnl":      0.0,
        }

    account = AccountState(
        equity=initial_equity,
        starting_equity_daily=initial_equity,
        starting_equity_weekly=initial_equity,
    )

    trades_opened = 0
    trades_closed = 0

    # ------------------------------------------------------------------
    # Step 1 — precompute full-series indicators ONCE
    # ------------------------------------------------------------------
    atr_series   = compute_atr(bars, period=20)
    ema_series   = bars["close"].ewm(span=cfg.ema_period, adjust=False).mean()
    sma_series   = bars["close"].rolling(window=cfg.sma_period).mean()
    clouds       = compute_clouds(bars)

    warmup_bars = cfg.sma_period + _WARMUP_EXTRA

    # ------------------------------------------------------------------
    # Step 2 — bar loop
    # ------------------------------------------------------------------
    for bar_idx in range(len(bars)):
        current_bar  = bars.iloc[bar_idx]
        atr_value    = atr_series.iloc[bar_idx]

        if pd.isna(atr_value) or atr_value <= 0:
            # ATR not yet warmed up — skip position management too
            continue

        current_bar_time = current_bar["time_utc"]
        if hasattr(current_bar_time, "to_pydatetime"):
            current_bar_time = current_bar_time.to_pydatetime()
        if current_bar_time.tzinfo is None:
            current_bar_time = current_bar_time.replace(tzinfo=timezone.utc)

        current_session = session_for(current_bar_time)

        # ------------------------------------------------------------------
        # Step 2a — update / check open positions (SL, TP, trailing, partials)
        # ------------------------------------------------------------------
        remaining_positions: list[Position] = []
        for pos in account.open_positions:
            closed = False
            exit_price: float | None = None
            exit_reason: str | None = None

            bar_high = float(current_bar["high"])
            bar_low  = float(current_bar["low"])

            if pos.direction == "BUY":
                if bar_low <= pos.sl_price:
                    exit_price  = pos.sl_price
                    exit_reason = "sl_hit"
                    closed = True
                elif bar_high >= pos.tp_price:
                    exit_price  = pos.tp_price
                    exit_reason = "tp_hit"
                    closed = True
            else:  # SELL
                if bar_high >= pos.sl_price:
                    exit_price  = pos.sl_price
                    exit_reason = "sl_hit"
                    closed = True
                elif bar_low <= pos.tp_price:
                    exit_price  = pos.tp_price
                    exit_reason = "tp_hit"
                    closed = True

            if closed:
                assert exit_price is not None
                assert exit_reason is not None
                pnl_pips, pnl_money, r_mult = _compute_trade_pnl(pos, exit_price)
                account.equity += pnl_money
                trades_closed += 1
                ledger.append(_make_ledger_row(
                    symbol=symbol,
                    pos=pos,
                    ts_signal=pos.ts_open,
                    ts_close=current_bar_time,
                    exit_price=exit_price,
                    exit_reason=exit_reason,
                    pnl_pips=pnl_pips,
                    pnl_money=pnl_money,
                    r_multiple=r_mult,
                    cfg=cfg,
                ))
                continue

            # --- Partials (§7.3) ---
            current_price = float(current_bar["close"])
            updated_pos = maybe_partial_close(pos, current_price, cfg)
            if updated_pos is not None:
                pos = updated_pos
                # Note: partial close writes a separate ledger row in spec v1
                # For v1 we just update the position in-place (no separate row).

            # --- Trailing SL (§7.4) ---
            pos = maybe_trail_sl(pos, current_bar, atr_value, cfg)

            remaining_positions.append(pos)

        account.open_positions = remaining_positions

        # ------------------------------------------------------------------
        # Skip warmup period for signal evaluation
        # ------------------------------------------------------------------
        if bar_idx < warmup_bars:
            continue

        # ------------------------------------------------------------------
        # Step 3 — detect swings, MMs, Fib, clusters
        # ------------------------------------------------------------------
        bars_slice = bars.iloc[: bar_idx + 1]
        ema_slice  = ema_series.iloc[: bar_idx + 1]

        swings = detect_swings(
            bars_slice,
            atr_min_multiple=cfg.impulse_atr_multiple_min,
            atr_period=20,
        )
        mms        = detect_measured_moves(bars_slice, swings, ema_slice, cfg)
        fib_levels = fibonacci_levels(bars_slice, mms, cfg)
        clusters   = find_clusters(fib_levels, atr_value=atr_value, cfg=cfg)

        # Build active_levels: D-targets + raw Fib prices + cluster prices
        active_levels: list[float] = []
        for mm in mms:
            if mm.validity == "valid":
                active_levels.append(mm.d_target)
                ext = extended_mm_target(mm, bars_slice, cfg)
                if ext is not None:
                    active_levels.append(ext)
        active_levels += [price for price, _label in fib_levels]
        active_levels += [price for price, _labels in clusters]

        # ------------------------------------------------------------------
        # Step 4 — composite direction
        # ------------------------------------------------------------------
        sent      = sentiment(bars, cfg, bar_idx)
        mmd_align = mmd_alignment(clouds, bar_idx, sent, cfg)

        # §3.3 D1 promo zone — resolves against previous UTC calendar day
        # when caller supplied d1_bars (Task 4). When d1_bars is None we keep
        # the v1-pre-fix neutral behavior for backward compatibility.
        current_price_close = float(current_bar["close"])
        d1_zone_val = _resolve_d1_zone_for_bar(
            signal_bar_time=pd.Timestamp(current_bar["time_utc"]),
            current_price=current_price_close,
            d1_bars=d1_bars,
        )

        # Session box (§3.4): only london / america; skip asia / dead
        if current_session in ("london", "america"):
            box_pos = session_box_position(
                bars, bar_idx, current_session, cfg, atr_value=atr_value,
            )
        else:
            # Asia / dead — no entry per v1 spec; use 'inside' to make composite neutral
            box_pos = "inside"

        direction = composite_direction(sent, mmd_align, d1_zone_val, box_pos, cfg)

        if direction == "neutral":
            continue

        # ------------------------------------------------------------------
        # Step 5 — signal candle + EMA-side rule + direction match
        # ------------------------------------------------------------------
        ema_val      = ema_series.iloc[bar_idx]
        signal_kind  = detect_signal_candle(current_bar, atr_value, cfg)

        if signal_kind == "none":
            continue

        if not passes_ema_side_rule(signal_kind, float(current_bar["close"]), float(ema_val)):
            continue

        # Direction must match signal kind
        if direction == "bull" and signal_kind != "bullish":
            continue
        if direction == "bear" and signal_kind != "bearish":
            continue

        # ------------------------------------------------------------------
        # Step 6 — confluence check
        # ------------------------------------------------------------------
        passed, matched_level, confluence_type = has_confluence(
            current_bar, active_levels, atr_value, cfg,
        )
        if not passed:
            continue

        # ------------------------------------------------------------------
        # Step 7 — build trade proposal (SL, TP, entry)
        # ------------------------------------------------------------------
        direction_order: str = "BUY" if direction == "bull" else "SELL"
        entry_price: float   = float(current_bar["close"])

        spread = float(current_bar.get("spread", 0)) if "spread" in current_bar.index else 0.0
        sl_price = compute_sl(signal_kind, current_bar, spread=spread, atr_value=atr_value, cfg=cfg)

        # Pick nearest viable TP from active_levels
        tp_price = _pick_tp(active_levels, entry_price, direction, atr_value, cfg)
        if tp_price is None:
            # No viable target — skip
            continue

        # Apply settle buffer
        tp_price = apply_settle_buffer(tp_price, direction, atr_value, cfg)

        # ------------------------------------------------------------------
        # Step 8 — ShouldOpen gate (§7.5)
        # ------------------------------------------------------------------
        should, reason = should_open(
            account=account,
            direction=direction,
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=tp_price,
            composite_direction_value=direction,
            entry_triggered=True,
            symbol=symbol,
            current_session=current_session,
            cfg=cfg,
        )
        if not should:
            continue

        # ------------------------------------------------------------------
        # Step 9 — open position
        # ------------------------------------------------------------------
        # Convert raw price-unit SL distance to pip count via the shared
        # _price_distance_to_pips helper — fixes the v1 bug where engine.py
        # passed raw price units (e.g. 0.00065 for EURUSD) to
        # compute_position_size, yielding ~15,384 lots instead of ~1.5.
        # The helper canonicalizes the symbol via normalize_symbol() before
        # the pip-factor lookup (which is intentionally not auto-canonicalizing
        # per the precondition documented in universe.lookup_pip_factor).
        sl_distance_price = abs(entry_price - sl_price)
        sl_distance_pips = _price_distance_to_pips(symbol, sl_distance_price)
        lot_size = compute_position_size(
            account=account,
            sl_distance_pips=sl_distance_pips,
            symbol=symbol,
            cfg=cfg,
        )
        if lot_size <= 0:
            continue

        pos = Position(
            symbol=symbol,
            direction=direction_order,
            entry_price=entry_price,
            sl_price=sl_price,
            tp_price=tp_price,
            lot_size=lot_size,
            ts_open=current_bar_time,
            setup_type="none",        # TODO Phase 3: integrate §6 state machines
            confluence_type=confluence_type or "",
            mmd_alignment=mmd_align,
            d1_zone=d1_zone_val,
            direction_strict_at_entry=cfg.direction_strict,
        )
        account.open_positions.append(pos)
        account.trades_this_session[current_session] = (
            account.trades_this_session.get(current_session, 0) + 1
        )
        trades_opened += 1

    # ------------------------------------------------------------------
    # Step 10 — force-close remaining open positions at final bar close
    # ------------------------------------------------------------------
    if len(bars) > 0:
        final_bar       = bars.iloc[-1]
        final_close     = float(final_bar["close"])
        final_bar_time  = final_bar["time_utc"]
        if hasattr(final_bar_time, "to_pydatetime"):
            final_bar_time = final_bar_time.to_pydatetime()
        if final_bar_time.tzinfo is None:
            final_bar_time = final_bar_time.replace(tzinfo=timezone.utc)

        for pos in account.open_positions:
            pnl_pips, pnl_money, r_mult = _compute_trade_pnl(pos, final_close)
            account.equity += pnl_money
            trades_closed += 1
            ledger.append(_make_ledger_row(
                symbol=symbol,
                pos=pos,
                ts_signal=pos.ts_open,
                ts_close=final_bar_time,
                exit_price=final_close,
                exit_reason="forced_eod",
                pnl_pips=pnl_pips,
                pnl_money=pnl_money,
                r_multiple=r_mult,
                cfg=cfg,
            ))
        account.open_positions = []

    ledger.flush()

    return {
        "bars_processed": len(bars),
        "trades_opened":  trades_opened,
        "trades_closed":  trades_closed,
        "final_equity":   account.equity,
        "final_pnl":      account.equity - initial_equity,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _compute_trade_pnl(
    pos: Position,
    exit_price: float,
) -> tuple[float, float, float]:
    """Return (pnl_pips, pnl_money, r_multiple) for a closed position.

    pnl_pips encodes direction: positive = profitable, negative = loss.
    v1 pip_value = $10 per pip per lot.

    Both pnl_pips and sl_distance_pips are converted from raw price-unit
    deltas to real pip counts via _price_distance_to_pips so that:
      - pnl_money math is real pips × $/pip × lots (was undersized by
        the pip factor pre-fix — Task 3b).
      - r_multiple is unit-consistent (was correct by accident pre-fix
        when both numerator and denominator were in price units).
    """
    if pos.direction == "BUY":
        pnl_price = exit_price - pos.entry_price
    else:
        pnl_price = pos.entry_price - exit_price

    pnl_pips = _price_distance_to_pips(pos.symbol, pnl_price)

    pnl_money = pnl_pips * pos.lot_size * _PIP_VALUE_PER_LOT

    sl_distance_price = abs(pos.entry_price - pos.sl_price)
    sl_distance_pips = _price_distance_to_pips(pos.symbol, sl_distance_price)
    if sl_distance_pips > 0:
        r_multiple = pnl_pips / sl_distance_pips
    else:
        r_multiple = 0.0

    return pnl_pips, pnl_money, r_multiple


def _pick_tp(
    active_levels: list[float],
    entry_price: float,
    direction: str,
    atr_value: float,
    cfg: Config,
) -> float | None:
    """Pick the nearest valid TP level from active_levels in the trade direction.

    For BUY: smallest level > entry_price + min_rr × sl_distance (approximated by atr).
    For SELL: largest level < entry_price - min_rr × sl_distance.

    v1 approximation: use atr as a proxy for the minimum TP distance so we can
    filter without knowing the exact SL distance at this point.  The should_open()
    gate with check_min_rr() will do the definitive check.
    """
    if not active_levels:
        return None

    min_move = cfg.min_rr * cfg.min_sl_distance_atr_multiple * atr_value

    if direction == "bull":
        candidates = [lvl for lvl in active_levels if lvl > entry_price + min_move]
        return min(candidates) if candidates else None
    else:
        candidates = [lvl for lvl in active_levels if lvl < entry_price - min_move]
        return max(candidates) if candidates else None


def _make_ledger_row(
    symbol: str,
    pos: Position,
    ts_signal: Any,
    ts_close: Any,
    exit_price: float,
    exit_reason: str,
    pnl_pips: float,
    pnl_money: float,
    r_multiple: float,
    cfg: Config,
) -> LedgerRow:
    """Construct a LedgerRow from an open position + close event."""
    return LedgerRow(
        trade_id=str(uuid.uuid4())[:8],
        ts_signal=ts_signal,
        ts_open=pos.ts_open,
        ts_close=ts_close,
        symbol=symbol,
        direction=pos.direction,
        entry_price=pos.entry_price,
        sl_price=pos.sl_price,
        tp_price=pos.tp_price,
        exit_price=exit_price,
        exit_reason=exit_reason,
        pnl_pips=pnl_pips,
        pnl_money=pnl_money,
        r_multiple=r_multiple,
        setup_type=pos.setup_type,
        direction_strict=cfg.direction_strict,
        mmd_alignment=pos.mmd_alignment,
        d1_zone=pos.d1_zone,
        confluence_type=pos.confluence_type,
        lot_size=pos.lot_size,
        risk_pct=cfg.risk_percent,
    )
