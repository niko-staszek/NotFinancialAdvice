//+------------------------------------------------------------------+
//| PAC_Orders.mqh — §7 order management + CTrade integration         |
//|                                                                   |
//| Port of hedgehog/proposer/pac/orders.py — algorithmic functions   |
//| (Orders_ComputeSL, Orders_MaybePartial, Orders_MaybeTrail,        |
//| Orders_ShouldOpen) plus MQL5-specific glue (Orders_BuildPlan,     |
//| Orders_Submit, Orders_DetectFillingMode, Orders_HandleClosedDeal, |
//| Orders_CheckTrailingAndPartial, DealIsCloseEntry).                |
//|                                                                   |
//| Structs:                                                          |
//|   OrderPlan      — input to Orders_Submit (proposed trade)        |
//|   PositionState  — in-flight position (mirrors orders.Position +  |
//|                    design spec Section 3 fix 3d ulong ticket)     |
//|   EntryTrigger   — output of §4 detection                         |
//|                                                                   |
//| DEVIATIONS from the plan sketch in favour of Python source:       |
//|   - Orders_ComputeSL signature mirrors Python compute_sl (signal  |
//|     kind + bar high/low/close + spread + atr_value + cfg params)  |
//|     NOT the plan's simplified `atr_value × sl_atr_multiple`. The  |
//|     Python implementation is wick-based with min-distance fallback|
//|     and that is the canonical truth.                              |
//|   - Orders_MaybePartial / Orders_MaybeTrail MUTATE PositionState  |
//|     by reference and return a bool indicating "state changed".    |
//|     Python uses frozen dataclass + dataclasses.replace (returns   |
//|     new instance / None). MQL5 mutation-by-ref is the natural fit |
//|     and matches existing PAC_Setups.mqh convention.               |
//|   - PositionState.trade_id is `string` not `long` — Python uses   |
//|     str (uuid via str(uuid.uuid4())). The design spec called for  |
//|     `long`, but the Python source is the canonical truth.         |
//|   - The plan sketch's PositionState includes `trail_anchor`;      |
//|     Python uses peak_price_since_activation + trailing_atr_frozen.|
//|     We adopt Python's field names for 1:1 parity with the         |
//|     algorithmic state.                                            |
//|                                                                   |
//| Test scope (per design spec Decision 5):                          |
//|   MQL5-specific surfaces only — Orders_ComputeSL math,            |
//|   DealIsCloseEntry helper, Orders_DetectFillingMode bitmask logic.|
//|   Algorithmic tests (MaybePartial/MaybeTrail/ShouldOpen branches) |
//|   are covered by Plan 4 pytest + Phase 3 ledger diff.             |
//+------------------------------------------------------------------+
#property strict

// CTrade is the SOLE MQL5-stdlib import allowed by design Decision 2.
#include <Trade\Trade.mqh>

#include "PAC_Risk.mqh"      // AccountState + 7 risk checks
#include "PAC_Signals.mqh"   // DirectionKind enum

//+------------------------------------------------------------------+
//| EntryTrigger — output of §4 detection.                            |
//|                                                                   |
//| Per design spec Section 3:                                        |
//|   fired              : true iff §4.1 + §4.2 + §4.3 all pass       |
//|   signal_candle_low  : low of the signal candle (used as wick     |
//|                        extreme for bullish confluence + SL)       |
//|   signal_candle_high : high of the signal candle (bearish side)   |
//|   confluence_level   : matched level price (from §4.3)            |
//|   confluence_type    : type tag ("mm_a"|"fib_retracement"|...)    |
//+------------------------------------------------------------------+
struct EntryTrigger {
    bool     fired;
    double   signal_candle_low;
    double   signal_candle_high;
    double   confluence_level;
    string   confluence_type;
};

//+------------------------------------------------------------------+
//| OrderPlan — proposed trade descriptor for Orders_Submit.          |
//|                                                                   |
//| Fields mirror the design spec PositionState shape (entry/sl/tp/  |
//| lot_size + metadata) since the plan becomes the position after   |
//| fill. trade_id is stamped at plan build to give partial-close +  |
//| final-exit ledger rows a shared key.                              |
//+------------------------------------------------------------------+
struct OrderPlan {
    string         symbol;
    DirectionKind  direction;
    double         entry_price;
    double         sl_price;
    double         tp_price;
    double         lot_size;
    string         setup_type;
    string         confluence_type;
    string         mmd_alignment;
    string         d1_zone;
    bool           direction_strict_at_entry;
    string         trade_id;
};

//+------------------------------------------------------------------+
//| PositionState — in-flight position (mirrors orders.Position).     |
//|                                                                   |
//| ticket is `ulong` per design spec Section 3 fix 3d (MQL5 canonical|
//| for position tickets). trade_id is `string` (UUID) per Python.    |
//|                                                                   |
//| Trailing state (peak_price_since_activation, trailing_atr_frozen) |
//| is initialised to EMPTY_VALUE meaning "not yet activated".        |
//+------------------------------------------------------------------+
struct PositionState {
    ulong          ticket;
    string         symbol;
    DirectionKind  direction;
    double         entry_price;
    double         sl_price;
    double         tp_price;
    double         lot_size;
    datetime       ts_open;
    string         setup_type;
    string         confluence_type;
    string         mmd_alignment;
    string         d1_zone;
    bool           direction_strict_at_entry;
    bool           partial_taken;
    bool           trailing_active;
    double         trailing_atr_frozen;        // EMPTY_VALUE = not activated
    double         peak_price_since_activation;// EMPTY_VALUE = not activated
    string         trade_id;
};

//+------------------------------------------------------------------+
//| Helper — initialise a PositionState from an OrderPlan + ticket.   |
//+------------------------------------------------------------------+
void Orders_InitPositionState(PositionState &pos, const OrderPlan &plan,
                              ulong ticket, datetime ts_open) {
    pos.ticket                      = ticket;
    pos.symbol                      = plan.symbol;
    pos.direction                   = plan.direction;
    pos.entry_price                 = plan.entry_price;
    pos.sl_price                    = plan.sl_price;
    pos.tp_price                    = plan.tp_price;
    pos.lot_size                    = plan.lot_size;
    pos.ts_open                     = ts_open;
    pos.setup_type                  = plan.setup_type;
    pos.confluence_type             = plan.confluence_type;
    pos.mmd_alignment               = plan.mmd_alignment;
    pos.d1_zone                     = plan.d1_zone;
    pos.direction_strict_at_entry   = plan.direction_strict_at_entry;
    pos.partial_taken               = false;
    pos.trailing_active             = false;
    pos.trailing_atr_frozen         = EMPTY_VALUE;
    pos.peak_price_since_activation = EMPTY_VALUE;
    pos.trade_id                    = plan.trade_id;
}

//+------------------------------------------------------------------+
//| §7.1 — Stop-loss placement.                                       |
//|                                                                   |
//| Mirrors orders.compute_sl line-for-line:                          |
//|                                                                   |
//|   min_distance = cfg.min_sl_distance_atr_multiple * atr_value     |
//|                                                                   |
//|   if signal_kind == "bullish":                                    |
//|     raw_sl = signal_bar.low - spread - wick_buffer * spread       |
//|     # ensure minimum distance below close                         |
//|     if (signal_bar.close - raw_sl) < min_distance:                |
//|       raw_sl = signal_bar.close - min_distance                    |
//|   else:  # bearish                                                |
//|     raw_sl = signal_bar.high + spread + wick_buffer * spread      |
//|     if (raw_sl - signal_bar.close) < min_distance:                |
//|       raw_sl = signal_bar.close + min_distance                    |
//|                                                                   |
//| Parameters:                                                       |
//|   signal_kind             — "bullish" | "bearish" (from §4.1)     |
//|   signal_high/low/close   — signal-candle OHLC                    |
//|   spread                  — current bid/ask spread (price units)  |
//|   atr_value               — ATR(20) at signal bar                 |
//|   wick_buffer_in_spreads  — cfg.wick_buffer_in_spreads (int, 1)   |
//|   min_sl_dist_atr_mult    — cfg.min_sl_distance_atr_multiple      |
//+------------------------------------------------------------------+
double Orders_ComputeSL(string signal_kind,
                        double signal_high, double signal_low, double signal_close,
                        double spread, double atr_value,
                        int wick_buffer_in_spreads, double min_sl_dist_atr_mult) {
    double min_distance = min_sl_dist_atr_mult * atr_value;

    if (signal_kind == "bullish") {
        double raw_sl = signal_low - spread - wick_buffer_in_spreads * spread;
        if ((signal_close - raw_sl) < min_distance) {
            raw_sl = signal_close - min_distance;
        }
        return raw_sl;
    }
    // bearish
    double raw_sl = signal_high + spread + wick_buffer_in_spreads * spread;
    if ((raw_sl - signal_close) < min_distance) {
        raw_sl = signal_close + min_distance;
    }
    return raw_sl;
}

//+------------------------------------------------------------------+
//| §7.3 — Partial close at 1R + move SL to breakeven.                |
//|                                                                   |
//| Mirrors orders.maybe_partial_close:                               |
//|   if not partials_enabled: return false  (no change)              |
//|   if pos.partial_taken: return false                              |
//|   r = |entry - sl|                                                |
//|   target = entry + trigger_r × r   (BUY)                          |
//|          = entry - trigger_r × r   (SELL)                         |
//|   if not reached: return false                                    |
//|   pos.partial_taken = true                                        |
//|   pos.sl_price      = pos.entry_price   (move to breakeven)       |
//|   return true                                                     |
//|                                                                   |
//| Returns true iff the position was updated (caller emits a partial-|
//| close ledger row and shrinks the broker lot size).                |
//|                                                                   |
//| Parameters:                                                       |
//|   pos                — in/out                                     |
//|   current_price      — latest bid/last for BUY-side comparison    |
//|                        OR ask/last for SELL-side                  |
//|   partials_enabled   — cfg.partials_enabled                       |
//|   partials_trigger_r — cfg.partials_trigger_r (e.g. 1.0)          |
//+------------------------------------------------------------------+
bool Orders_MaybePartial(PositionState &pos, double current_price,
                        bool partials_enabled, double partials_trigger_r) {
    if (!partials_enabled) return false;
    if (pos.partial_taken) return false;

    double r = MathAbs(pos.entry_price - pos.sl_price);
    double target_price;
    bool reached;
    if (pos.direction == DIR_BUY) {
        target_price = pos.entry_price + partials_trigger_r * r;
        reached = (current_price >= target_price);
    } else {
        target_price = pos.entry_price - partials_trigger_r * r;
        reached = (current_price <= target_price);
    }

    if (!reached) return false;

    pos.partial_taken = true;
    pos.sl_price = pos.entry_price;   // breakeven
    return true;
}

//+------------------------------------------------------------------+
//| §7.4 — Trailing-SL ratchet after 1.5R.                            |
//|                                                                   |
//| Mirrors orders.maybe_trail_sl. Algorithm:                         |
//|                                                                   |
//|   if not trailing_enabled: return false                           |
//|   r = |entry - sl|                                                |
//|   if not pos.trailing_active:                                     |
//|     activation = entry + activation_r × r   (BUY)                 |
//|                = entry - activation_r × r   (SELL)                |
//|     BUY:  if bar.high >= activation:                              |
//|             trailing_active = True; frozen_atr = atr_at_activation|
//|             peak = bar.high                                       |
//|           else: return false                                      |
//|     SELL: if bar.low <= activation: ...peak = bar.low             |
//|                                                                   |
//|   # active branch                                                 |
//|   frozen_atr = pos.trailing_atr_frozen (set above on activation)  |
//|   trail_distance = distance_atr_mult × frozen_atr                 |
//|   BUY:  peak = max(peak, bar.high)                                |
//|         new_sl = peak - trail_distance                            |
//|         new_sl = max(new_sl, pos.sl_price)   (never widen)        |
//|   SELL: peak = min(peak, bar.low)                                 |
//|         new_sl = peak + trail_distance                            |
//|         new_sl = min(new_sl, pos.sl_price)                        |
//|                                                                   |
//| Returns true iff pos.sl_price was updated (caller modifies broker |
//| SL via CTrade.PositionModify).                                    |
//|                                                                   |
//| Parameters:                                                       |
//|   pos                   — in/out                                  |
//|   bar_high / bar_low    — current bar's high & low                |
//|   atr_at_activation     — ATR(20) value to freeze on activation   |
//|   trailing_enabled      — cfg.trailing_enabled                    |
//|   trailing_activation_r — cfg.trailing_activation_r (1.5)         |
//|   distance_atr_mult     — cfg.trailing_distance_atr_multiple (1.0)|
//+------------------------------------------------------------------+
bool Orders_MaybeTrail(PositionState &pos, double bar_high, double bar_low,
                      double atr_at_activation,
                      bool trailing_enabled,
                      double trailing_activation_r,
                      double distance_atr_mult) {
    if (!trailing_enabled) return false;

    double r = MathAbs(pos.entry_price - pos.sl_price);

    if (!pos.trailing_active) {
        if (pos.direction == DIR_BUY) {
            double activation_price = pos.entry_price + trailing_activation_r * r;
            if (bar_high >= activation_price) {
                pos.trailing_active             = true;
                pos.trailing_atr_frozen         = atr_at_activation;
                pos.peak_price_since_activation = bar_high;
                // fall through to ratchet update
            } else {
                return false;
            }
        } else {
            // SELL
            double activation_price = pos.entry_price - trailing_activation_r * r;
            if (bar_low <= activation_price) {
                pos.trailing_active             = true;
                pos.trailing_atr_frozen         = atr_at_activation;
                pos.peak_price_since_activation = bar_low;
            } else {
                return false;
            }
        }
    }

    // Active branch — update peak + ratchet SL.
    double frozen_atr = (pos.trailing_atr_frozen != EMPTY_VALUE)
                        ? pos.trailing_atr_frozen
                        : atr_at_activation;
    double trail_distance = distance_atr_mult * frozen_atr;

    double old_sl = pos.sl_price;
    if (pos.direction == DIR_BUY) {
        double new_peak = (pos.peak_price_since_activation == EMPTY_VALUE)
                          ? bar_high
                          : MathMax(pos.peak_price_since_activation, bar_high);
        double new_sl = new_peak - trail_distance;
        new_sl = MathMax(new_sl, pos.sl_price);  // never widen
        pos.peak_price_since_activation = new_peak;
        pos.sl_price = new_sl;
    } else {
        double new_peak = (pos.peak_price_since_activation == EMPTY_VALUE)
                          ? bar_low
                          : MathMin(pos.peak_price_since_activation, bar_low);
        double new_sl = new_peak + trail_distance;
        new_sl = MathMin(new_sl, pos.sl_price);
        pos.peak_price_since_activation = new_peak;
        pos.sl_price = new_sl;
    }

    return (pos.sl_price != old_sl);
}

//+------------------------------------------------------------------+
//| §7.5 — Trade-execution checklist (final binary gate).             |
//|                                                                   |
//| Mirrors orders.should_open exactly — short-circuits on first      |
//| failed check. Returns true iff ALL gates pass.                    |
//|                                                                   |
//| Order of checks (matches Python):                                 |
//|   1. composite_direction == required direction                    |
//|   2. entry_triggered                                              |
//|   3. Risk_CheckMinRR                                              |
//|   4. Risk_CheckSessionCap                                         |
//|   5. Risk_CheckDailyDD                                            |
//|   6. Risk_CheckWeeklyDD                                           |
//|   7. Risk_CheckCorrelationLock                                    |
//|   8. Risk_CheckNewsBlackout                                       |
//|   9. SL distance > 0                                              |
//|                                                                   |
//| Parameters mirror should_open() + open_symbols/n for the          |
//| correlation check (Python uses account.open_positions list of     |
//| objects; the MQL5 EA maintains g_positions[] and derives a parallel|
//| symbols array at the call site).                                  |
//|                                                                   |
//| `reason_out` receives a human-readable rejection string on first  |
//| failure (empty string on success).                                |
//+------------------------------------------------------------------+
bool Orders_ShouldOpen(
    const AccountState &acc,
    DirectionKind direction,
    DirectionKind composite_direction,
    bool entry_triggered,
    double entry_price, double sl_price, double tp_price,
    string symbol, int current_session,
    const string &open_symbols[], int open_n,
    // cfg passthrough
    double cfg_min_rr,
    int    cfg_max_trades_per_session,
    double cfg_daily_dd_stop_pct,
    double cfg_weekly_dd_stop_pct,
    bool   cfg_news_filter_enabled,
    int    cfg_news_filter_window_min,
    string &reason_out
) {
    // 1. Direction match
    if (composite_direction != direction) {
        reason_out = "direction mismatch: composite != required";
        return false;
    }

    // 2. Entry triggered
    if (!entry_triggered) {
        reason_out = "no entry trigger";
        return false;
    }

    // 3. Min R:R
    if (!Risk_CheckMinRR(entry_price, sl_price, tp_price, cfg_min_rr)) {
        reason_out = StringFormat("min rr not met (required %.2f)", cfg_min_rr);
        return false;
    }

    // 4. Session cap
    if (!Risk_CheckSessionCap(acc, current_session, cfg_max_trades_per_session)) {
        reason_out = "session cap reached";
        return false;
    }

    // 5. Daily DD
    if (!Risk_CheckDailyDD(acc, cfg_daily_dd_stop_pct)) {
        reason_out = StringFormat("daily drawdown limit hit (%.2f%%)",
                                  cfg_daily_dd_stop_pct);
        return false;
    }

    // 6. Weekly DD
    if (!Risk_CheckWeeklyDD(acc, cfg_weekly_dd_stop_pct)) {
        reason_out = StringFormat("weekly drawdown limit hit (%.2f%%)",
                                  cfg_weekly_dd_stop_pct);
        return false;
    }

    // 7. Correlation lock
    if (!Risk_CheckCorrelationLock(acc, symbol, direction, open_symbols, open_n)) {
        reason_out = StringFormat("correlation lock: existing open position correlated to %s", symbol);
        return false;
    }

    // 8. News blackout
    if (!Risk_CheckNewsBlackout(acc, cfg_news_filter_enabled, cfg_news_filter_window_min)) {
        reason_out = "news blackout: recent high-impact news event";
        return false;
    }

    // 9. SL distance > 0
    double sl_distance = MathAbs(entry_price - sl_price);
    if (sl_distance <= 0) {
        reason_out = "position size not computable: sl_distance is zero";
        return false;
    }

    reason_out = "";
    return true;
}

//+------------------------------------------------------------------+
//| DealIsCloseEntry — true iff the deal-ticket refers to a position- |
//| close fill (not an open/in fill or balance op).                   |
//|                                                                   |
//| Used by OnTradeTransaction handlers to identify position-close    |
//| events so the engine can emit the final ledger row and shrink     |
//| g_positions[]. Per design spec Section 3 — event-driven closures  |
//| via OnTradeTransaction, not polling on OnTick.                    |
//|                                                                   |
//| Returns false for invalid/unknown deal tickets (defensive guard). |
//+------------------------------------------------------------------+
bool DealIsCloseEntry(ulong deal_ticket) {
    if (!HistoryDealSelect(deal_ticket)) return false;
    long entry = HistoryDealGetInteger(deal_ticket, DEAL_ENTRY);
    return (entry == DEAL_ENTRY_OUT);
}

//+------------------------------------------------------------------+
//| Orders_DetectFillingMode — pick the best supported filling mode   |
//| for the given symbol.                                             |
//|                                                                   |
//| MQL5 brokers advertise allowed filling modes as a bitmask via     |
//| SYMBOL_FILLING_MODE. The bitmask exposes:                         |
//|   SYMBOL_FILLING_FOK (=1) — Fill-Or-Kill (all-or-nothing)         |
//|   SYMBOL_FILLING_IOC (=2) — Immediate-Or-Cancel (partial allowed) |
//|   (RETURN is the catch-all for pending orders)                    |
//|                                                                   |
//| Preference order: FOK > IOC > RETURN. Returns one of the          |
//| ENUM_ORDER_TYPE_FILLING values, ready to pass to CTrade.          |
//+------------------------------------------------------------------+
int Orders_DetectFillingMode(string symbol) {
    long flags = SymbolInfoInteger(symbol, SYMBOL_FILLING_MODE);
    if ((flags & SYMBOL_FILLING_FOK) != 0) return ORDER_FILLING_FOK;
    if ((flags & SYMBOL_FILLING_IOC) != 0) return ORDER_FILLING_IOC;
    return ORDER_FILLING_RETURN;
}

//+------------------------------------------------------------------+
//| Orders_BuildPlan — package a proposed trade for ShouldOpen +      |
//| Submit. Stamps a fresh trade_id (UUID-like via MathRand + time).  |
//|                                                                   |
//| Caller provides everything except trade_id; this helper centralises|
//| id generation so partial+final ledger rows share the same key.    |
//|                                                                   |
//| The trade_id format matches Python's str(uuid.uuid4()) only in    |
//| spirit — MQL5 has no UUID stdlib, so we generate a string from    |
//| (timestamp_ns + rand32) that is unique within a Strategy Tester   |
//| run. Phase 3 parity diff collapses rows by trade_id before its    |
//| match key, so monotonic uniqueness is sufficient.                 |
//+------------------------------------------------------------------+
OrderPlan Orders_BuildPlan(string symbol, DirectionKind direction,
                          double entry_price, double sl_price, double tp_price,
                          double lot_size, string setup_type,
                          string confluence_type, string mmd_alignment,
                          string d1_zone, bool direction_strict_at_entry) {
    OrderPlan plan;
    plan.symbol                     = symbol;
    plan.direction                  = direction;
    plan.entry_price                = entry_price;
    plan.sl_price                   = sl_price;
    plan.tp_price                   = tp_price;
    plan.lot_size                   = lot_size;
    plan.setup_type                 = setup_type;
    plan.confluence_type            = confluence_type;
    plan.mmd_alignment              = mmd_alignment;
    plan.d1_zone                    = d1_zone;
    plan.direction_strict_at_entry  = direction_strict_at_entry;
    plan.trade_id                   = StringFormat("%I64d-%d", (long)TimeGMT(), MathRand());
    return plan;
}

//+------------------------------------------------------------------+
//| Orders_Submit — open a market order via CTrade.                   |
//|                                                                   |
//| Wires:                                                            |
//|   - filling mode auto-detected per symbol                         |
//|   - SL / TP from plan                                             |
//|   - comment encodes trade_id + setup_type + confluence_type so    |
//|     the broker journal and ledger can be cross-referenced         |
//|                                                                   |
//| Returns true iff the order was accepted by the broker. On failure |
//| the CTrade retcode + description are printed for diagnosis.       |
//|                                                                   |
//| Caller is responsible for slippage/deviation configuration BEFORE |
//| invoking Submit (CTrade.SetDeviationInPoints — typically in OnInit|
//| based on cfg.max_slippage_pips × PipSize).                        |
//+------------------------------------------------------------------+
bool Orders_Submit(CTrade &trade, const OrderPlan &plan) {
    int fill_mode = Orders_DetectFillingMode(plan.symbol);
    trade.SetTypeFilling((ENUM_ORDER_TYPE_FILLING)fill_mode);

    string comment = StringFormat("PAC|tid=%s|setup=%s|conf=%s",
                                  plan.trade_id, plan.setup_type,
                                  plan.confluence_type);

    bool ok;
    if (plan.direction == DIR_BUY) {
        ok = trade.Buy(plan.lot_size, plan.symbol, plan.entry_price,
                       plan.sl_price, plan.tp_price, comment);
    } else {
        ok = trade.Sell(plan.lot_size, plan.symbol, plan.entry_price,
                        plan.sl_price, plan.tp_price, comment);
    }

    if (!ok) {
        PrintFormat("Orders_Submit FAILED %s %s: retcode=%d %s",
                    plan.symbol,
                    (plan.direction == DIR_BUY ? "BUY" : "SELL"),
                    trade.ResultRetcode(),
                    trade.ResultRetcodeDescription());
    }
    return ok;
}

//+------------------------------------------------------------------+
//| Orders_CheckTrailingAndPartial — combined per-bar maintenance hook|
//| called from the EA's OnTick / OnNewBar handler.                   |
//|                                                                   |
//| Runs §7.3 partial-close check then §7.4 trailing-SL ratchet on a  |
//| single position. Returns true iff EITHER stage updated state      |
//| (signalling the caller to push the new SL to the broker via       |
//| CTrade.PositionModify and/or emit a partial-close ledger row).    |
//|                                                                   |
//| Forward declared here for the EA's bar loop. The implementation   |
//| just composes Orders_MaybePartial + Orders_MaybeTrail; an `out`   |
//| flag distinguishes which stage fired so the caller can dispatch.  |
//+------------------------------------------------------------------+
bool Orders_CheckTrailingAndPartial(
    PositionState &pos, double current_price,
    double bar_high, double bar_low, double atr_at_activation,
    bool partials_enabled, double partials_trigger_r,
    bool trailing_enabled, double trailing_activation_r,
    double distance_atr_mult,
    bool &partial_fired_out
) {
    partial_fired_out = Orders_MaybePartial(pos, current_price,
                                            partials_enabled,
                                            partials_trigger_r);
    bool trail_changed = Orders_MaybeTrail(pos, bar_high, bar_low,
                                           atr_at_activation,
                                           trailing_enabled,
                                           trailing_activation_r,
                                           distance_atr_mult);
    return (partial_fired_out || trail_changed);
}

//+------------------------------------------------------------------+
//| Orders_HandleClosedDeal — extract close-side details from a       |
//| HistoryDealSelect-ed deal ticket.                                 |
//|                                                                   |
//| Called from OnTradeTransaction when a TRADE_TRANSACTION_DEAL_ADD  |
//| event fires with DealIsCloseEntry(deal) == true. Populates the    |
//| out-params from the broker's history record so the EA can build   |
//| a final ledger row.                                               |
//|                                                                   |
//| Returns true iff the deal was successfully selected and read.     |
//+------------------------------------------------------------------+
bool Orders_HandleClosedDeal(ulong deal_ticket,
                            double &exit_price_out,
                            double &volume_out,
                            datetime &ts_close_out,
                            string &symbol_out,
                            ulong &position_id_out) {
    if (!HistoryDealSelect(deal_ticket)) return false;
    if (HistoryDealGetInteger(deal_ticket, DEAL_ENTRY) != DEAL_ENTRY_OUT) return false;

    exit_price_out  = HistoryDealGetDouble(deal_ticket, DEAL_PRICE);
    volume_out      = HistoryDealGetDouble(deal_ticket, DEAL_VOLUME);
    ts_close_out    = (datetime)HistoryDealGetInteger(deal_ticket, DEAL_TIME);
    symbol_out      = HistoryDealGetString(deal_ticket, DEAL_SYMBOL);
    position_id_out = (ulong)HistoryDealGetInteger(deal_ticket, DEAL_POSITION_ID);
    return true;
}
