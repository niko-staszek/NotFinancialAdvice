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
    - Setup state machines (§6) ARE stepped inside the loop (Task 5). Each
      active MM owns one (TrapState, FailState, SpikeChannelState) triplet;
      on simultaneous fires the priority order trap > fail > spike_channel
      decides the ledger.setup_type written for opened trades.
    - pip_value = $10 per pip per lot (broker-independent approximation). TODO real data.
    - SL/TP hit resolution uses bar high/low (no intrabar modelling). Acceptable for M5.
"""
from __future__ import annotations

import dataclasses
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

# §6 setup priority — higher index = lower priority. When multiple §6
# state machines reach 'triggered' on the same bar, the leftmost-listed
# setup wins and is written to ledger.setup_type. Matches the conviction
# hierarchy in strategy_ea.md §6: a trap (two-failed-attempts reversal)
# carries more conviction than a fail (one deep failed correction), which
# in turn carries more than a spike-and-channel pullback.
_SETUP_PRIORITY: tuple[str, ...] = ("trap", "fail", "spike_channel")


# ---------------------------------------------------------------------------
# Bar-evaluation order — canonical sequence locked across Python + MQL5 engines
# ---------------------------------------------------------------------------

def _bar_evaluation_order() -> list[str]:
    """Returns the canonical bar-evaluation order. Used by tests and docs.

    Production code must implement the loop in this exact order — see
    Plan 5 design spec § 'Bar-evaluation order — locked'. The crucial
    invariant: targets_update and setup_step are ALWAYS-RUN modules that
    must execute BEFORE any entry-path gate (session_cap, direction_filter,
    etc.) may short-circuit the bar via `continue`. Otherwise the §5 target
    engine and §6 setup state machines miss bars where direction is neutral
    or the session cap is hit, leaving them frozen with stale state.

    Pre-fix bug: targets_update + setup_step were downstream of the direction
    filter, so neutral-direction bars left them un-stepped → on the next
    non-neutral bar, the state machines fired against stale MMs or missed
    in-progress trap/fail/spike patterns entirely.
    """
    return [
        "drawdown_gate",      # cheap; halts entry path on circuit-breaker trip
        "targets_update",     # ALWAYS — maintains MM/Fib/cluster state
        "setup_step",         # ALWAYS — accumulates per-MM trap/fail/spike state
        "session_cap",        # entry gate
        "direction_filter",   # entry gate (may short-circuit)
        "entry_trigger",      # only if direction non-neutral
        "correlation_news",   # entry gate
        "should_open",        # checklist §7.5
        "rr_size",            # min R:R + position size
        "submit_log",         # OrderSend + ledger row
    ]


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
# Multi-symbol iteration order — deterministic, matches Plan 5 EA
# ---------------------------------------------------------------------------

def _order_symbols_for_iteration(
    symbols: list[str],
    alphabetize: bool = False,
) -> list[str]:
    """Return symbol iteration order.

    Default: declaration order (stable). Sets ordering for correlation-
    lockout first-triggered semantics — matches Plan 5's InpTradableSymbols
    declaration order.

    alphabetize=True: sort alphabetically (testing/diagnostic flag).
    """
    if alphabetize:
        return sorted(symbols)
    return list(symbols)


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

    # §6 setup state-machine registry, keyed by mm.id. Carried across bars
    # so progress (e.g. trap first_try_failed → second_try_failed) survives.
    setup_machines: dict[int, dict[str, object]] = {}

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
                # Task 6: emit a separate ledger row for the partial leg.
                #
                # PnL math: compute against a *temporary* Position that has:
                #   - the ORIGINAL sl_price (pre-`pos` had it; updated_pos has
                #     it moved to breakeven), so r_multiple ≈ +partials_trigger_r
                #     instead of div-by-zero on the BE'd updated_pos.
                #   - lot_size scaled to cfg.partials_close_fraction so pnl_money
                #     reflects the actual money taken off the table for just the
                #     partial portion.
                partial_pos_for_pnl = dataclasses.replace(
                    pos,
                    lot_size=pos.lot_size * cfg.partials_close_fraction,
                )
                p_pips, p_money, p_r = _compute_trade_pnl(
                    partial_pos_for_pnl, current_price,
                )
                # write_partial reads pos.lot_size and pos.trade_id, scales
                # lot_size by cfg.partials_close_fraction internally, writes
                # the row, and returns the closed lot count.
                partial_lot_closed = ledger.write_partial(
                    pos=updated_pos,
                    ts_signal=updated_pos.ts_open,
                    ts_close=current_bar_time,
                    exit_price=current_price,
                    cfg=cfg,
                    pnl_pips=p_pips,
                    pnl_money=p_money,
                    r_multiple=p_r,
                )
                account.equity += p_money
                # Shrink the in-flight position so the eventual SL/TP/EOD exit
                # row writes the remaining size — not the original full size.
                updated_pos.lot_size -= partial_lot_closed
                pos = updated_pos

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

        # ------------------------------------------------------------------
        # §6 setup state-machine lifecycle (Task 5)
        # ------------------------------------------------------------------
        # 1) Rebuild registry: add fresh idle machines for new MMs, carry
        #    forward existing machines for known MMs, drop machines for any
        #    MM that vanished or flipped to validity='invalid'.
        # 2) Step every live machine by one bar — trap/fail are MM-anchored;
        #    spike_channel reads the recent bars window for impulse detection.
        # 3) Collect (mm_id, setup_name) for any machine that just transitioned
        #    to 'triggered'; pick the winner by _SETUP_PRIORITY for ledger.
        setup_machines = _setup_machines_for_mms(mms, existing=setup_machines)
        mms_by_id = {mm.id: mm for mm in mms if mm.validity == "valid"}
        spike_window_size = max(cfg.spike_min_bars, 1)
        sc_window = bars_slice.iloc[-spike_window_size:] if len(bars_slice) >= spike_window_size else bars_slice
        setup_machines = _step_all_setups(
            machines=setup_machines,
            mms_by_id=mms_by_id,
            bar=current_bar,
            bar_idx=bar_idx,
            bars_window=sc_window,
            atr=atr_value,
            cfg=cfg,
        )
        fires = _collect_triggered_fires(setup_machines)
        winning_setup = _pick_winning_setup(fires)

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
            # §6 winning setup (Task 5): trap > fail > spike_channel by
            # _SETUP_PRIORITY; falls back to 'none' when no machine fired
            # this bar. Used for journaling/conviction only — §3-§5-§7
            # agreement still gates the trade.
            setup_type=winning_setup or "none",
            confluence_type=confluence_type or "",
            mmd_alignment=mmd_align,
            d1_zone=d1_zone_val,
            direction_strict_at_entry=cfg.direction_strict,
            # Task 6: stamp trade_id at open-time so partial-close + final-exit
            # rows share the id. (Previously _make_ledger_row generated a fresh
            # uuid at write-time, which made partial+exit rows unrelated.)
            trade_id=str(uuid.uuid4())[:8],
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
# §6 setup state-machine lifecycle helpers (Task 5)
# ---------------------------------------------------------------------------

def _setup_machines_for_mms(
    mms: list[MeasuredMove],
    existing: dict[int, dict[str, object]],
) -> dict[int, dict[str, object]]:
    """Build the per-MM §6 state-machine registry for the current bar.

    For each MM with ``validity == 'valid'``:
      - Carry forward the existing TrapState / FailState / SpikeChannelState
        objects if this MM was tracked on the previous bar (so progress like
        ``first_try_failed`` is preserved).
      - Otherwise instantiate fresh ``idle`` states (new MM detected).

    MMs with ``validity == 'invalid'`` — or MMs that vanish from the active
    list because ``detect_measured_moves`` capped to the most-recent N — are
    dropped from the registry.

    Returns a new dict; ``existing`` is not mutated.
    """
    next_registry: dict[int, dict[str, object]] = {}
    for mm in mms:
        if mm.validity != "valid":
            continue
        if mm.id in existing:
            # Carry forward the live state objects unchanged.
            next_registry[mm.id] = existing[mm.id]
        else:
            next_registry[mm.id] = {
                "trap": TrapState(mm_id=mm.id, state="idle"),
                "fail": FailState(mm_id=mm.id, state="idle"),
                "spike_channel": SpikeChannelState(state="idle"),
            }
    return next_registry


def _step_all_setups(
    machines: dict[int, dict[str, object]],
    mms_by_id: dict[int, MeasuredMove],
    bar: pd.Series,
    bar_idx: int,
    bars_window: pd.DataFrame,
    atr: float,
    cfg: Config,
) -> dict[int, dict[str, object]]:
    """Step every live state machine by one bar; return a new registry with
    each ``State`` dataclass replaced by its post-step (immutable) value.

    The trap and fail machines are MM-anchored so they receive the matching
    ``MeasuredMove``. The spike-and-channel detector is MM-agnostic in the
    spec (it discovers its own A/B pivots from the bar window) — we still
    key it per-MM so each MM gets its own independent S&C tracker.
    """
    next_registry: dict[int, dict[str, object]] = {}
    for mm_id, by_name in machines.items():
        mm = mms_by_id.get(mm_id)
        if mm is None:
            # Defensive: shouldn't happen if machines was just rebuilt by
            # _setup_machines_for_mms with the same mms list.
            next_registry[mm_id] = by_name
            continue
        next_registry[mm_id] = {
            "trap": step_trap(by_name["trap"], bar, bar_idx, mm, atr, cfg),
            "fail": step_fail(by_name["fail"], bar, bar_idx, mm, atr, cfg),
            "spike_channel": step_spike_channel(
                by_name["spike_channel"], bar, bar_idx, bars_window, atr, cfg,
            ),
        }
    return next_registry


def _collect_triggered_fires(
    machines: dict[int, dict[str, object]],
) -> list[tuple[int, str]]:
    """Scan every state object; return ``(mm_id, setup_name)`` for any
    machine whose ``.state == 'triggered'`` on this bar.

    The state-machine dataclasses all expose a ``state`` field; we read it
    directly rather than re-importing each ``*_triggered`` predicate.
    """
    fires: list[tuple[int, str]] = []
    for mm_id, by_name in machines.items():
        for name in _SETUP_PRIORITY:
            machine = by_name.get(name)
            if machine is not None and getattr(machine, "state", None) == "triggered":
                fires.append((mm_id, name))
    return fires


def _pick_winning_setup(fires: list[tuple[int, str]]) -> str | None:
    """Apply ``_SETUP_PRIORITY`` to pick the winning setup name.

    Returns ``None`` when no setup fired (caller writes 'none' to ledger).
    """
    if not fires:
        return None
    fire_names = {name for _mm_id, name in fires}
    for name in _SETUP_PRIORITY:
        if name in fire_names:
            return name
    return None


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
    """Construct a LedgerRow from an open position + close event.

    Task 6: ``trade_id`` is taken from ``pos`` (stamped at open-time) so the
    final-exit row shares its id with any partial-close row written earlier.
    """
    return LedgerRow(
        trade_id=pos.trade_id,
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
