//+------------------------------------------------------------------+
//| PAC_Risk.mqh — §1 risk-rule checks                                |
//|                                                                   |
//| Port of hedgehog/proposer/pac/risk.py line-for-line:              |
//|   §1.1 Position sizing   — Risk_ComputePositionSize               |
//|   §1.2 Min R:R           — Risk_CheckMinRR                        |
//|   §1.3 Session cap       — Risk_CheckSessionCap                   |
//|   §1.4 Daily DD          — Risk_CheckDailyDD                      |
//|   §1.5 Weekly DD         — Risk_CheckWeeklyDD                     |
//|   §1.6 Correlation lock  — Risk_CheckCorrelationLock              |
//|   §1.7 News blackout     — Risk_CheckNewsBlackout                 |
//|                                                                   |
//| All seven check functions return `true` when the check PASSES     |
//| (i.e. the trade is permitted) and `false` when the check BLOCKS   |
//| (i.e. the trade must be rejected). This matches risk.py exactly.  |
//|                                                                   |
//| DEVIATIONS from the plan sketch in favour of Python source:       |
//|   - AccountState session-trade counts are int scalars per session |
//|     (asia/london/america) — MQL5 lacks dict. Asia/London/America  |
//|     mirror SessionKind values exactly.                            |
//|   - Risk_ComputePositionSize uses pip_value_per_lot = 10.0 (v1    |
//|     assumption identical to risk.py — broker-dependent in reality |
//|     but consistent for single-account backtests).                 |
//|   - Risk_CheckDailyDD / Risk_CheckWeeklyDD return TRUE (pass) on  |
//|     starting_equity == 0 — matches risk.py defensive guard.       |
//|   - Risk_CheckCorrelationLock delegates the group-membership test |
//|     to Universe_AreCorrelated (PAC_Universe.mqh), which is the    |
//|     MQL5 equivalent of risk.py's `for group in cfg.correlation_   |
//|     groups: if pos_symbol in group ...`. Caller passes a list of  |
//|     currently-open symbols, mirroring the python signature that   |
//|     takes account.open_positions.                                 |
//|   - last_news_event_minutes_ago sentinel: risk.py uses None /     |
//|     Python Optional[int]; MQL5 lacks Optional, so we use INT_MAX  |
//|     to denote "no recent event" (per design spec Section 3 fix 3c)|
//|     — the comparison `> window_min` trivially passes.             |
//+------------------------------------------------------------------+
#property strict

#include "PAC_TimeUtil.mqh"   // SessionKind enum
#include "PAC_Universe.mqh"   // Universe_AreCorrelated for §1.6

//+------------------------------------------------------------------+
//| AccountState — mirrors risk.AccountState dataclass.               |
//|                                                                   |
//| Field naming follows the design spec Section 3:                   |
//|   equity                       : current account equity           |
//|   starting_equity_daily        : equity at session open today     |
//|   starting_equity_weekly       : equity at week-start             |
//|   trades_session_asia/london/  : per-session trade counts (int    |
//|     america                      replaces Python dict[str,int])   |
//|   last_news_event_minutes_ago  : INT_MAX = no recent event        |
//+------------------------------------------------------------------+
struct AccountState {
    double   equity;
    double   starting_equity_daily;
    double   starting_equity_weekly;
    int      trades_session_asia;
    int      trades_session_london;
    int      trades_session_america;
    int      last_news_event_minutes_ago;
};

//+------------------------------------------------------------------+
//| Helper — initialise an AccountState to its starting defaults.    |
//+------------------------------------------------------------------+
void Risk_InitAccountState(AccountState &acc, double starting_equity) {
    acc.equity                       = starting_equity;
    acc.starting_equity_daily        = starting_equity;
    acc.starting_equity_weekly       = starting_equity;
    acc.trades_session_asia          = 0;
    acc.trades_session_london        = 0;
    acc.trades_session_america       = 0;
    acc.last_news_event_minutes_ago  = INT_MAX;
}

//+------------------------------------------------------------------+
//| §1.1 — Position sizing.                                           |
//|                                                                   |
//| Mirrors compute_position_size():                                  |
//|   risk_amount   = equity × (risk_percent / 100)                   |
//|   pip_value_per_lot = 10.0  (v1 assumption — same as risk.py)     |
//|   lot_size      = risk_amount / (sl_distance_pips × pip_value)    |
//|   return round(lot_size, 2)                                       |
//|                                                                   |
//| Returns 0.0 when sl_distance_pips <= 0 (matches Python guard).    |
//|                                                                   |
//| Parameters:                                                       |
//|   acc        — current account state (only .equity is read)       |
//|   sl_pips    — stop-loss distance in pips                         |
//|   symbol     — instrument symbol (unused in v1; retained for API  |
//|                parity so v2 broker-dependent pip values can hook  |
//|                in without signature breakage)                     |
//|   risk_pct   — cfg.risk_percent (e.g. 1.0 = 1% of equity)         |
//+------------------------------------------------------------------+
double Risk_ComputePositionSize(const AccountState &acc, double sl_pips,
                                string symbol, double risk_pct) {
    double risk_amount = acc.equity * (risk_pct / 100.0);
    double pip_value_per_lot = 10.0;   // v1 assumption per risk.py
    if (sl_pips <= 0) return 0.0;
    double lots = risk_amount / (sl_pips * pip_value_per_lot);
    return NormalizeDouble(lots, 2);
}

//+------------------------------------------------------------------+
//| §1.2 — Minimum R:R check.                                         |
//|                                                                   |
//| Mirrors check_min_rr():                                           |
//|   risk = |entry - sl|                                             |
//|   if risk == 0: return False  (would div-by-zero)                 |
//|   rr   = |tp - entry| / risk                                      |
//|   return rr >= min_rr                                             |
//|                                                                   |
//| True iff the trade's R:R meets or exceeds the threshold.          |
//+------------------------------------------------------------------+
bool Risk_CheckMinRR(double entry, double sl, double tp, double min_rr) {
    double risk = MathAbs(entry - sl);
    if (risk == 0.0) return false;
    double rr = MathAbs(tp - entry) / risk;
    return rr >= min_rr;
}

//+------------------------------------------------------------------+
//| §1.3 — Session cap check.                                         |
//|                                                                   |
//| Mirrors check_session_cap():                                      |
//|   count = trades_this_session.get(current_session, 0)             |
//|   return count < max_trades_per_session                           |
//|                                                                   |
//| MQL5 lacks dict; we dispatch on SessionKind enum. SESSION_DEAD    |
//| returns true (no cap applies — but no trades should fire in dead  |
//| time anyway — checked upstream by direction filter).              |
//+------------------------------------------------------------------+
bool Risk_CheckSessionCap(const AccountState &acc, int session, int max_trades) {
    int count = 0;
    if      (session == SESSION_ASIA)    count = acc.trades_session_asia;
    else if (session == SESSION_LONDON)  count = acc.trades_session_london;
    else if (session == SESSION_AMERICA) count = acc.trades_session_america;
    // SESSION_DEAD: count stays 0 → always passes (no trades expected anyway)
    return count < max_trades;
}

//+------------------------------------------------------------------+
//| §1.4 — Daily drawdown check.                                      |
//|                                                                   |
//| Mirrors check_daily_dd():                                         |
//|   if starting_equity_daily == 0: return True   (defensive guard)  |
//|   dd_pct = ((equity - starting) / starting) × 100                 |
//|   return dd_pct > daily_dd_stop_pct                               |
//|                                                                   |
//| daily_dd_stop_pct is NEGATIVE in spec (e.g. -3.0). The trade is   |
//| permitted while DD% remains ABOVE (i.e. less negative than) the   |
//| threshold. Example:                                               |
//|   DD% = -2.0, stop = -3.0  →  -2.0 > -3.0 = TRUE  → pass          |
//|   DD% = -4.0, stop = -3.0  →  -4.0 > -3.0 = FALSE → block         |
//+------------------------------------------------------------------+
bool Risk_CheckDailyDD(const AccountState &acc, double dd_stop_pct) {
    if (acc.starting_equity_daily == 0.0) return true;
    double dd_pct = ((acc.equity - acc.starting_equity_daily)
                     / acc.starting_equity_daily) * 100.0;
    return dd_pct > dd_stop_pct;
}

//+------------------------------------------------------------------+
//| §1.5 — Weekly drawdown check.                                     |
//|                                                                   |
//| Mirrors check_weekly_dd() — identical semantics to daily DD with  |
//| starting_equity_weekly and weekly_dd_stop_pct (e.g. -5.0).        |
//+------------------------------------------------------------------+
bool Risk_CheckWeeklyDD(const AccountState &acc, double dd_stop_pct) {
    if (acc.starting_equity_weekly == 0.0) return true;
    double dd_pct = ((acc.equity - acc.starting_equity_weekly)
                     / acc.starting_equity_weekly) * 100.0;
    return dd_pct > dd_stop_pct;
}

//+------------------------------------------------------------------+
//| §1.6 — Correlation lockout.                                       |
//|                                                                   |
//| Mirrors check_correlation_lock():                                 |
//|   for group in cfg.correlation_groups:                            |
//|     if new_symbol in group:                                       |
//|       for pos in account.open_positions:                          |
//|         if pos.symbol in group AND pos.symbol != new_symbol:      |
//|           return False                                            |
//|   return True                                                     |
//|                                                                   |
//| Caller passes the list of currently-open symbols (the MQL5 EA     |
//| maintains this from g_positions[]). The group-membership test is  |
//| delegated to Universe_AreCorrelated — that helper returns true    |
//| only when a and b appear in the SAME group AND a != b, matching   |
//| risk.py's "pos_symbol.upper() != new_canonical" guard.            |
//|                                                                   |
//| v1: blocks ANY same-group position regardless of direction. v2    |
//| can refine with direction-aware carve-outs once Phase 3 parity    |
//| diff exposes any direction-dependent edge cases.                  |
//|                                                                   |
//| Parameters:                                                       |
//|   acc            — account state (unused in v1 but kept for API)  |
//|   new_symbol     — symbol of the proposed new trade               |
//|   new_direction  — DirectionKind of proposed trade (DIR_BUY/SELL) |
//|                    Currently unused (v1 ignores direction).       |
//|   open_symbols[] — symbols of currently-open positions            |
//|   n              — array length                                   |
//+------------------------------------------------------------------+
bool Risk_CheckCorrelationLock(const AccountState &acc, string new_symbol,
                               int new_direction,
                               const string &open_symbols[], int n) {
    for (int i = 0; i < n; i++) {
        if (Universe_AreCorrelated(new_symbol, open_symbols[i])) {
            return false;
        }
    }
    return true;
}

//+------------------------------------------------------------------+
//| §1.7 — News blackout check.                                       |
//|                                                                   |
//| Mirrors check_news_blackout():                                    |
//|   if not enabled: return True                                     |
//|   if last_news_event_minutes_ago is None: return True             |
//|   return last_news_event_minutes_ago > window_min                 |
//|                                                                   |
//| INT_MAX sentinel handling: comparison `INT_MAX > window_min` is   |
//| always true, so the "no recent event" case trivially passes —     |
//| matches Python's `last_news_event_minutes_ago is None → True`     |
//| branch without needing an explicit early return.                  |
//+------------------------------------------------------------------+
bool Risk_CheckNewsBlackout(const AccountState &acc, bool enabled, int window_min) {
    if (!enabled) return true;
    if (acc.last_news_event_minutes_ago == INT_MAX) return true;
    return acc.last_news_event_minutes_ago > window_min;
}
