//+------------------------------------------------------------------+
//| PAC_EA.mq5 — Price Action Cycle Expert Advisor (orchestrator)     |
//|                                                                   |
//| MQL5 analogue of hedgehog/proposer/pac/engine.py run_backtest.    |
//| Wires every PAC_*.mqh module into the event-driven §3–§7 decision |
//| chain and writes closed-trade rows to a 21-column ledger that is  |
//| byte-parity with Plan 4's ledger.py output (Phase 3 triangulation |
//| contract).                                                        |
//|                                                                   |
//| Bar-evaluation order (LOCKED — mirrors engine._bar_evaluation_    |
//| order() and run_backtest's bar loop):                             |
//|   drawdown_gate → targets_update → setup_step → session_cap →     |
//|   direction → entry_trigger → correlation/news → should_open →    |
//|   rr_size → submit_log                                            |
//| The two ALWAYS-RUN maintenance modules (targets_update, setup_    |
//| step) execute BEFORE any entry-path gate may short-circuit, so    |
//| the §5 target engine and §6 setup state machines never freeze on  |
//| neutral-direction / session-capped bars.                          |
//|                                                                   |
//| Closure detection is event-driven via OnTradeTransaction (broker- |
//| authoritative, race-free). OnTick handles only per-position       |
//| trailing/partial maintenance plus the bar-change gate that drives |
//| OnNewBar.                                                         |
//|                                                                   |
//| === STRING-VOCABULARY PARITY (CRITICAL) ===                       |
//| Every categorical ledger field uses the EXACT string the Python   |
//| engine writes (verified against engine.py / ledger.py / orders.py |
//| AND the committed smoke artifact runs/2026-05-EURUSD/ledger.csv):  |
//|   direction       : "BUY" / "SELL"   (orders.Position.direction;  |
//|                     ledger.py writes row.direction verbatim — it   |
//|                     is NOT lowercased to long/short anywhere)      |
//|   exit_reason     : "sl_hit" / "tp_hit" / "partial" / "forced_eod" |
//|   setup_type      : "trap" / "fail" / "spike_channel" / "none"     |
//|   confluence_type : "mm_or_fib_or_cluster"  (has_confluence emits  |
//|                     this constant for ANY match) / ""              |
//|   mmd_alignment   : "confirmed" / "weakened" / "vetoed"            |
//|   d1_zone         : "bull_promo" / "bear_promo" / "neutral" / ...  |
//|   direction_strict: "True" / "False"  (Python str(bool) casing —  |
//|                     handled by PAC_Logger.mqh)                     |
//+------------------------------------------------------------------+
#property copyright "PAC"
#property version   "1.00"
#property strict

// CTrade is pulled in transitively via PAC_Orders.mqh (the SOLE stdlib
// import per design Decision 2), but we include it explicitly for clarity.
#include <Trade\Trade.mqh>

#include "..\\..\\Include\\PAC\\PAC_Config.mqh"
#include "..\\..\\Include\\PAC\\PAC_Pip.mqh"
#include "..\\..\\Include\\PAC\\PAC_TimeUtil.mqh"
#include "..\\..\\Include\\PAC\\PAC_Universe.mqh"
#include "..\\..\\Include\\PAC\\PAC_ATR.mqh"
#include "..\\..\\Include\\PAC\\PAC_Swing.mqh"
#include "..\\..\\Include\\PAC\\PAC_MMD.mqh"
#include "..\\..\\Include\\PAC\\PAC_Signals.mqh"
#include "..\\..\\Include\\PAC\\PAC_Targets.mqh"
#include "..\\..\\Include\\PAC\\PAC_Setups.mqh"
#include "..\\..\\Include\\PAC\\PAC_Risk.mqh"
#include "..\\..\\Include\\PAC\\PAC_Orders.mqh"
#include "..\\..\\Include\\PAC\\PAC_Logger.mqh"

//+------------------------------------------------------------------+
//| EA-local inputs not covered by the auto-generated PAC_Config.mqh  |
//+------------------------------------------------------------------+
input long   InpMagicNumber  = 990527;                  // EA magic number
input string InpLedgerPath   = "PAC\\ledger.csv";       // ledger output (MQL5/Files relative)

//+------------------------------------------------------------------+
//| Engine constants — mirror engine.py module-level constants.        |
//+------------------------------------------------------------------+
#define PIP_VALUE_PER_LOT      10.0   // engine._PIP_VALUE_PER_LOT (v1: $10/pip/lot)
#define WARMUP_EXTRA           50     // engine._WARMUP_EXTRA
#define ATR_PERIOD             20     // engine compute_atr(period=20)
#define SESSION_BOX_MIN_ATR    0.5    // signals.session_box_position hard-codes 0.5×ATR

// Window of closed bars copied each new bar for swing/MM/cluster recompute.
// engine.py recomputes over the full series each bar; we cap the lookback to
// a generous window. The signal warmup is max(sma_period, PAC_MMD_SLOWEST_PERIOD)
// + WARMUP_EXTRA.  With the default InpSmaPeriod=61 that is
// max(61, 1440) + 50 = 1490 bars, leaving ~10 bars of headroom under
// BAR_WINDOW=1500.  If InpSmaPeriod is raised above 1450 the warmup would
// exceed BAR_WINDOW — OnInit emits a warning in that case.
#define BAR_WINDOW             1500

// §6 setup priority is applied directly in Setups_StepAll: on simultaneous
// fires the order trap > fail > spike_channel decides ledger.setup_type
// (engine._SETUP_PRIORITY).

//+------------------------------------------------------------------+
//| Module-level globals.                                             |
//+------------------------------------------------------------------+
CTrade        g_trade;
datetime      g_last_bar_time = 0;
AccountState  g_account;
PositionState g_positions[];          // in-flight tracked positions
LedgerWriter  g_ledger;

// Indicator handles (created in OnInit, released in OnDeinit).
int g_ema21_handle = INVALID_HANDLE;
int g_sma61_handle = INVALID_HANDLE;
// ATR handle lives inside PAC_ATR.mqh (g_atr_handle) via ATR_Init/ATR_Release.
// MMD handle lives inside PAC_MMD.mqh (g_mmd_handle) via InitMMD/ReleaseMMD.

// ---- Per-bar §5 target-engine state (rebuilt every new bar) ----
double g_active_levels[];             // candidate TP / confluence levels (prices)
string g_active_types[];              // parallel type tags (informational)
int    g_active_count = 0;

// ---- §6 setup state-machine registry, keyed by MeasuredMove id ----
// Mirrors engine.py setup_machines dict carried across bars. Parallel arrays:
// g_sm_mm_id[i] owns the (trap/fail/spike) triplet at index i.
#define MAX_SETUP_MACHINES 64
int               g_sm_mm_id[MAX_SETUP_MACHINES];
TrapState         g_sm_trap[MAX_SETUP_MACHINES];
FailState         g_sm_fail[MAX_SETUP_MACHINES];
SpikeChannelState g_sm_spike[MAX_SETUP_MACHINES];
int               g_sm_count = 0;

// ---- §6 winning setup for the current bar (set by Setups_StepAll) ----
string g_winning_setup = "none";

// ---- §4 entry-trigger result carried out of the forward-declared
//      bool Signals_DetectEntryTrigger(symbol, dir) into OnNewBar ----
EntryTrigger g_last_trigger;

// ---- Direction-filter context captured for the ledger (mmd/d1) ----
string g_last_mmd_alignment = "weakened";
string g_last_d1_zone       = "neutral";


//==================================================================
// Forward declarations of EA-internal helpers
//==================================================================
void   OnNewBar();
int    CopyClosedBars(MqlRates &out_bars[]);
void   ComputeEmaSeries(const MqlRates &bars[], int n, double &out_ema[]);
double EmaValueAtShift(int handle, int bar_shift);
void   Targets_Update(string symbol, const MqlRates &bars[], int n, double atr_value);
void   Setups_StepAll(string symbol, const MqlRates &bars[], int n, double atr_value);
int    OpenSymbolsArray(string &out_symbols[]);
double PriceDistanceToPips(string symbol, double price_distance);
double PickTP(double entry_price, DirectionKind dir, double atr_value);
void   ForceCloseAllAtExit();
void   CloseTrackedPosition(int idx, double exit_price, datetime ts_close, string exit_reason);
int    FindPositionByTicket(ulong position_id);
bool   SessionBoxHighLow(string symbol, int session, double &out_high, double &out_low);
void   AppendLevel(double price, string type_tag);
int    ParseDoubleCSV(string csv, double &out[]);


//==================================================================
// §3.x / §4.x end-to-end orchestrators
// (forward-declared in PAC_Signals.mqh — bodies live here because they
//  need the iMA / iATR / iCustom handles wired in OnInit).
//==================================================================

//+------------------------------------------------------------------+
//| Signals_ComputeDirection — §3.1–§3.5 composite direction gate.    |
//|                                                                   |
//| Mirrors engine.py run_backtest Step 4:                            |
//|   sent      = sentiment(bars, cfg, bar_idx)                       |
//|   mmd_align = mmd_alignment(clouds, bar_idx, sent, cfg)           |
//|   d1_zone   = _resolve_d1_zone_for_bar(...)                       |
//|   box_pos   = session_box_position(...) if london/america else    |
//|               "inside"                                            |
//|   direction = composite_direction(sent, mmd, d1, box, cfg)        |
//|                                                                   |
//| All scalar inputs are read at bar shift 1 (the most recently      |
//| CLOSED M5 bar), matching engine.py evaluating the current bar in  |
//| a closed-bar backtest.                                            |
//|                                                                   |
//| Side effects: stamps g_last_mmd_alignment and g_last_d1_zone so   |
//| the ledger row can record them (engine.py stores them on the      |
//| Position at open-time).                                           |
//+------------------------------------------------------------------+
DirectionKind Signals_ComputeDirection(string symbol)
{
    double close    = iClose(symbol, PERIOD_M5, 1);
    double ema21    = EmaValueAtShift(g_ema21_handle, 1);
    double sma61    = EmaValueAtShift(g_sma61_handle, 1);
    double atr_val  = ATR_Value(1);

    // §3.1 sentiment
    string sent = Signals_ClassifySentiment(close, ema21, sma61);

    // §3.2 MMD alignment (soft-fails to "weakened" when indicator unavailable).
    string mmd = ClassifyAlignmentLive(close, sent, 1);
    g_last_mmd_alignment = mmd;

    // §3.3 D1 promo zone — resolve against the PREVIOUS D1 bar (shift 1 on
    // PERIOD_D1 is the last fully-closed daily bar; engine.py uses the
    // previous UTC calendar day's D1 bar). engine.py defaults to "neutral"
    // when d1_bars is None (as the Plan 4 smoke artifact did). The EA always
    // has D1 history available, so we compute the real zone here.
    string d1_zone = "neutral";
    double d1o = iOpen(symbol, PERIOD_D1, 1);
    double d1h = iHigh(symbol, PERIOD_D1, 1);
    double d1l = iLow(symbol, PERIOD_D1, 1);
    double d1c = iClose(symbol, PERIOD_D1, 1);
    if (d1o > 0.0 && d1c > 0.0) {
        d1_zone = Signals_D1PromoZone(d1o, d1h, d1l, d1c, close);
    }
    g_last_d1_zone = d1_zone;

    // §3.4 session box — only london / america; else "inside" (engine.py).
    // The London box is the PRIMARY session-box filter during BOTH the London
    // AND America windows (strategy.md §3.4): during the America window we feed
    // the box function SESSION_LONDON so the held London box (08:00–13:59 PLT)
    // drives above/inside/below, rather than building an america-only box that
    // would reset at 14:00 PLT. SessionBoxHighLow filters prior bars by the
    // passed session arg, so passing SESSION_LONDON builds the London box even
    // on an america-time bar.
    int session = TimeUtil_CurrentSessionForUtc(iTime(symbol, PERIOD_M5, 1));
    string box_pos = "inside";
    if (session == SESSION_LONDON || session == SESSION_AMERICA) {
        int box_session = (session == SESSION_AMERICA) ? SESSION_LONDON : session;
        double sh, sl;
        if (SessionBoxHighLow(symbol, box_session, sh, sl)) {
            box_pos = Signals_SessionBoxPosition(close, sh, sl, atr_val,
                                                 SESSION_BOX_MIN_ATR);
        }
    }

    // §3.5 composite (strict toggle from generated config).
    return Signals_CompositeDirection(sent, mmd, d1_zone, box_pos,
                                      InpDirectionStrict);
}

//+------------------------------------------------------------------+
//| Signals_DetectEntryTrigger — §4.1–§4.3 entry trigger.             |
//|                                                                   |
//| Mirrors engine.py run_backtest Steps 5–6:                         |
//|   signal_kind = detect_signal_candle(current_bar, atr, cfg)       |
//|   if signal_kind == "none": skip                                  |
//|   if not passes_ema_side_rule(...): skip                          |
//|   if direction != signal_kind: skip                               |
//|   passed, level, conf_type = has_confluence(...)                  |
//|                                                                   |
//| Returns bool (matches the PAC_Signals.mqh forward declaration);   |
//| the matched-level details are written into the module-level       |
//| g_last_trigger struct for OnNewBar to consume.                    |
//|                                                                   |
//| confluence_type is forced to the Python constant                  |
//| "mm_or_fib_or_cluster" on a match (has_confluence returns that    |
//| literal for ANY level, NOT the per-level tag) — required for      |
//| ledger byte-parity.                                               |
//+------------------------------------------------------------------+
bool Signals_DetectEntryTrigger(string symbol, DirectionKind dir)
{
    g_last_trigger.fired             = false;
    g_last_trigger.signal_candle_low = 0.0;
    g_last_trigger.signal_candle_high= 0.0;
    g_last_trigger.confluence_level  = 0.0;
    g_last_trigger.confluence_type   = "";

    double bo = iOpen(symbol, PERIOD_M5, 1);
    double bh = iHigh(symbol, PERIOD_M5, 1);
    double bl = iLow(symbol, PERIOD_M5, 1);
    double bc = iClose(symbol, PERIOD_M5, 1);
    double atr_val    = ATR_Value(1);
    double ema21_at_1 = EmaValueAtShift(g_ema21_handle, 1);

    // §4.1 signal candle
    string kind = Signals_DetectSignalCandle(bo, bh, bl, bc, atr_val,
                                             InpWickToBodyRatioMin,
                                             InpCandleRangeAtrMultMin,
                                             (double)InpClosePositionWithinWickPct);
    if (kind == "none") return false;

    // Direction must match signal kind (engine.py: bull↔bullish, bear↔bearish).
    bool match_kind = (dir == DIR_BUY  && kind == "bullish")
                   || (dir == DIR_SELL && kind == "bearish");
    if (!match_kind) return false;

    // §4.2 EMA-side hard rule
    if (!Signals_PassesEMASide(kind, bc, ema21_at_1)) return false;

    // §4.3 confluence — wick extreme vs active levels.
    //   bullish → low wick extreme; bearish → high wick extreme. Python's
    //   has_confluence uses min(|high-level|,|low-level|); since the kind
    //   already fixes which wick is dominant we pass that extreme. (Both
    //   engines select the closest level under threshold; the closest level
    //   to the dominant wick is the binding one.)
    double wick_ext = (kind == "bullish") ? bl : bh;
    double thresh   = InpConfluencePipsAtrMult * atr_val;

    double matched_level;
    string matched_type;
    if (!Signals_HasConfluence(wick_ext, g_active_levels, g_active_types,
                               thresh, matched_level, matched_type)) {
        return false;
    }

    g_last_trigger.fired              = true;
    g_last_trigger.signal_candle_low  = bl;
    g_last_trigger.signal_candle_high = bh;
    g_last_trigger.confluence_level   = matched_level;
    // PARITY: Python has_confluence returns the constant for any match.
    g_last_trigger.confluence_type    = "mm_or_fib_or_cluster";
    return true;
}


//==================================================================
// EA lifecycle handlers
//==================================================================

//+------------------------------------------------------------------+
//| OnInit — verify whitelist, init indicators / logger / account.    |
//+------------------------------------------------------------------+
int OnInit()
{
    if (Period() != PERIOD_M5) {
        Print("PAC_EA: requires M5 chart timeframe — exiting");
        return INIT_FAILED;
    }

    if (!Universe_VerifySymbol(_Symbol)) {
        PrintFormat("PAC_EA: %s not in whitelist — exiting", _Symbol);
        return INIT_FAILED;
    }

    // Reject symbols with an unknown pip size — the trade math depends on it.
    if (PipSize(_Symbol) <= 0.0) {
        PrintFormat("PAC_EA: %s has unknown pip size — exiting", _Symbol);
        return INIT_FAILED;
    }

    // Parse correlation groups from the generated config string.
    Universe_InitCorrelationGroups(InpCorrelationGroups);

    // §3.2 MMD — soft-fail to weakened (does NOT block trading per §3.2).
    if (!InitMMD(_Symbol))
        Print("PAC_EA: MMD unavailable — running with mmd_alignment=weakened");

    // Indicator handles: EMA(21), SMA(61), ATR(20) on M5 close.
    g_ema21_handle = iMA(_Symbol, PERIOD_M5, InpEmaPeriod, 0, MODE_EMA, PRICE_CLOSE);
    g_sma61_handle = iMA(_Symbol, PERIOD_M5, InpSmaPeriod, 0, MODE_SMA, PRICE_CLOSE);
    if (g_ema21_handle == INVALID_HANDLE || g_sma61_handle == INVALID_HANDLE) {
        PrintFormat("PAC_EA: iMA handle init failed (err=%d)", GetLastError());
        return INIT_FAILED;
    }
    if (!ATR_Init(_Symbol, PERIOD_M5, ATR_PERIOD)) {
        Print("PAC_EA: ATR_Init failed — exiting");
        return INIT_FAILED;
    }

    // Ledger.
    if (!Logger_Init(g_ledger, InpLedgerPath)) {
        Print("PAC_EA: Logger_Init failed — exiting");
        return INIT_FAILED;
    }

    // CTrade config.
    g_trade.SetExpertMagicNumber((ulong)InpMagicNumber);
    // Slippage: cfg.max_slippage_pips × pip → points. Points-per-pip = pip/point.
    double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
    if (point > 0.0) {
        double pip = PipSize(_Symbol);
        int slippage_points = (int)MathRound((InpMaxSlippagePips * pip) / point);
        g_trade.SetDeviationInPoints(slippage_points);
    }

    // Account state.
    Risk_InitAccountState(g_account, AccountInfoDouble(ACCOUNT_EQUITY));

    ArrayResize(g_positions, 0);
    g_sm_count       = 0;
    g_active_count   = 0;
    g_last_bar_time  = 0;

    // Server-time vs UTC caveat (design spec open-question 2). Session
    // classification feeds iTime() bar timestamps (broker SERVER time) into
    // TimeUtil_CurrentSessionForUtc(), which expects UTC. If the broker
    // server is not UTC the session windows shift by the server offset. Log
    // the detected offset so Phase 3 triangulation can account for any skew.
    long srv_utc_offset = (long)TimeGMT() - (long)TimeCurrent();
    if (MathAbs(srv_utc_offset) > 1) {   // tolerate ±1s clock jitter
        PrintFormat("PAC_EA: WARNING broker server time differs from UTC by %d s; "
                    "session windows are computed from bar (server) time — "
                    "Phase 3 must reconcile any session-boundary skew.",
                    (int)srv_utc_offset);
    }

    // Diagnostic: warn when warmup_bars would exceed BAR_WINDOW, which means
    // the EA will never become warm and will silently never trade.
    int computed_warmup = MathMax(InpSmaPeriod, PAC_MMD_SLOWEST_PERIOD) + WARMUP_EXTRA;
    if (computed_warmup > BAR_WINDOW) {
        PrintFormat("PAC_EA: WARNING: warmup_bars (%d) exceeds BAR_WINDOW (%d) "
                    "— EA will never warm up; raise BAR_WINDOW or lower InpSmaPeriod.",
                    computed_warmup, BAR_WINDOW);
    }

    PrintFormat("PAC_EA: initialized for %s", _Symbol);
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| OnTick — per-tick trailing/partial maintenance + bar-change gate. |
//|                                                                   |
//| Mirrors engine.py Step 2a position management (partials/trailing) |
//| running each tick; SL/TP HIT detection is delegated to the broker |
//| and surfaced via OnTradeTransaction (Decision 6).                 |
//+------------------------------------------------------------------+
void OnTick()
{
    // --- Per-position trailing + partial decisions (EA-driven) ---
    double bar_high = iHigh(_Symbol, PERIOD_M5, 0);
    double bar_low  = iLow(_Symbol, PERIOD_M5, 0);
    double atr_val  = ATR_Value(0);
    double last     = SymbolInfoDouble(_Symbol, SYMBOL_LAST);
    if (last <= 0.0) last = SymbolInfoDouble(_Symbol, SYMBOL_BID);

    for (int i = 0; i < ArraySize(g_positions); i++) {
        // Only manage positions still alive at the broker.
        if (!PositionSelectByTicket(g_positions[i].ticket)) continue;

        double current_price = last;
        // Capture the ORIGINAL SL before the maintenance call — Orders_MaybePartial
        // moves SL to breakeven on a partial fire, but engine.py computes the
        // partial-leg r_multiple against the pre-breakeven SL (≈ +trigger_r).
        double orig_sl = g_positions[i].sl_price;
        bool partial_fired = false;
        bool changed = Orders_CheckTrailingAndPartial(
            g_positions[i], current_price, bar_high, bar_low, atr_val,
            InpPartialsEnabled, InpPartialsTriggerR,
            InpTrailingEnabled, InpTrailingActivationR, InpTrailingDistanceAtrMult,
            partial_fired);

        if (partial_fired) {
            // §7.3 partial-close: take partials_close_fraction off, move to BE.
            double close_lots = NormalizeDouble(
                g_positions[i].lot_size * InpPartialsCloseFraction, 2);
            if (close_lots > 0.0) {
                if (g_trade.PositionClosePartial(g_positions[i].ticket, close_lots)) {
                    // Emit a partial-close ledger row sharing the trade_id.
                    // PnL math against the ORIGINAL sl so r ≈ +trigger_r (engine.py).
                    double r_dist = MathAbs(g_positions[i].entry_price - orig_sl);
                    double pnl_price = (g_positions[i].direction == DIR_BUY)
                        ? (current_price - g_positions[i].entry_price)
                        : (g_positions[i].entry_price - current_price);
                    double p_pips = PriceDistanceToPips(g_positions[i].symbol, pnl_price);
                    double p_money = p_pips * close_lots * PIP_VALUE_PER_LOT;
                    double sl_pips = PriceDistanceToPips(g_positions[i].symbol, r_dist);
                    double p_r = (sl_pips > 0.0) ? (p_pips / sl_pips) : 0.0;

                    LedgerEntryRow row;
                    row.trade_id        = g_positions[i].trade_id;
                    row.ts_signal       = g_positions[i].ts_open;
                    row.ts_open         = g_positions[i].ts_open;
                    row.ts_close        = TimeGMT();
                    row.symbol          = g_positions[i].symbol;
                    row.direction       = (g_positions[i].direction == DIR_BUY) ? "BUY" : "SELL";
                    row.entry_price     = g_positions[i].entry_price;
                    row.sl_price        = g_positions[i].sl_price;
                    row.tp_price        = g_positions[i].tp_price;
                    row.exit_price      = current_price;
                    row.exit_reason     = "partial";
                    row.pnl_pips        = p_pips;
                    row.pnl_money       = p_money;
                    row.r_multiple      = p_r;
                    row.setup_type      = g_positions[i].setup_type;
                    row.direction_strict= g_positions[i].direction_strict_at_entry;
                    row.mmd_alignment   = g_positions[i].mmd_alignment;
                    row.d1_zone         = g_positions[i].d1_zone;
                    row.confluence_type = g_positions[i].confluence_type;
                    row.lot_size        = close_lots;
                    row.risk_pct        = InpRiskPercent;
                    Logger_WritePartial(g_ledger, row);

                    g_positions[i].lot_size -= close_lots;
                }
            }
        }

        if (changed) {
            // Push the ratcheted SL (and breakeven from partial) to the broker.
            g_trade.PositionModify(g_positions[i].ticket,
                                   g_positions[i].sl_price,
                                   g_positions[i].tp_price);
        }
    }

    // --- Bar-change gate: signal logic on closed M5 bars only ---
    datetime current_bar_time = iTime(_Symbol, PERIOD_M5, 0);
    if (current_bar_time == g_last_bar_time) return;
    g_last_bar_time = current_bar_time;
    OnNewBar();
}

//+------------------------------------------------------------------+
//| OnNewBar — the §3–§7 decision chain, run once per closed M5 bar.  |
//|                                                                   |
//| Order mirrors engine.py run_backtest exactly (post pre-flight     |
//| bar-evaluation-order fix).                                        |
//+------------------------------------------------------------------+
void OnNewBar()
{
    // Sync account equity to the live broker figure (ST updates per pass).
    g_account.equity = AccountInfoDouble(ACCOUNT_EQUITY);

    // --- ATR warmup guard (engine.py skips bars with NaN/<=0 ATR) ---
    double atr_value = ATR_Value(1);
    if (atr_value <= 0.0) return;

    // --- Copy the closed-bar window for swing/MM/cluster recompute ---
    MqlRates bars[];
    int n = CopyClosedBars(bars);
    if (n <= 0) return;

    // --- Warmup: signal evaluation must wait for the slowest MMD cloud
    //     (Green, period 1440) to be warm. Mirrors engine._signal_warmup_bars
    //     = max(sma_period, 1440) + WARMUP_EXTRA. We also require the MMD
    //     cloud-midpoint reads to return valid non-empty values (i.e. the
    //     iCustom buffers are populated). Per §3.2 the MMD indicator being
    //     entirely unavailable soft-fails to "weakened" and does NOT block
    //     trading, so the read requirement applies only when MMD is available.
    int warmup_bars = MathMax(InpSmaPeriod, PAC_MMD_SLOWEST_PERIOD) + WARMUP_EXTRA;
    bool warmed = (n >= warmup_bars);
    if (warmed && MMD_Available()) {
        CloudMidpoints warm_mids;
        if (!ReadCloudMidpoints(1, warm_mids)) warmed = false;
    }

    // ============================================================
    // 1. Drawdown gate (cheap; halts entry path on circuit-breaker)
    // ============================================================
    bool dd_ok = Risk_CheckDailyDD(g_account, InpDailyDDStopPct)
              && Risk_CheckWeeklyDD(g_account, InpWeeklyDDStopPct);

    // ============================================================
    // 2 & 3. ALWAYS-RUN maintenance — targets + setup state machines.
    //   Must step every bar regardless of entry outcome (engine.py).
    //   Skipped only during warmup, exactly like engine.py's
    //   `if bar_idx < warmup_bars: continue` (which sits AFTER position
    //   management but BEFORE swing/MM detection).
    // ============================================================
    if (warmed) {
        Targets_Update(_Symbol, bars, n, atr_value);
        Setups_StepAll(_Symbol, bars, n, atr_value);
    }

    // The drawdown circuit-breaker halts the entry path (but maintenance
    // above has already run, matching engine ordering).
    if (!dd_ok) return;
    if (!warmed) return;   // no entries until warmed (engine.py)

    // ============================================================
    // 4. Session + per-session cap (entry gate)
    // ============================================================
    int session = TimeUtil_CurrentSessionForUtc(iTime(_Symbol, PERIOD_M5, 1));
    if (session == SESSION_DEAD) return;            // no entries in dead time
    if (session == SESSION_ASIA) return;            // engine.py v1: asia → no entry
    if (!Risk_CheckSessionCap(g_account, session, InpMaxTradesPerSession)) return;

    // ============================================================
    // 5. Direction filter (may short-circuit)
    // ============================================================
    DirectionKind dir = Signals_ComputeDirection(_Symbol);
    if (dir == DIR_NEUTRAL) return;

    // ============================================================
    // 6. Entry trigger (only reached when direction is non-neutral)
    // ============================================================
    if (!Signals_DetectEntryTrigger(_Symbol, dir)) return;

    // ============================================================
    // 7. Correlation + news gates
    // ============================================================
    string open_symbols[];
    int open_n = OpenSymbolsArray(open_symbols);
    if (!Risk_CheckCorrelationLock(g_account, _Symbol, dir, open_symbols, open_n)) return;
    if (!Risk_CheckNewsBlackout(g_account, InpNewsFilterEnabled, InpNewsFilterWindowMin)) return;

    // ============================================================
    // Build the trade proposal (SL, TP, entry) — engine.py Step 7
    // ============================================================
    string signal_kind = (dir == DIR_BUY) ? "bullish" : "bearish";
    double entry_price = iClose(_Symbol, PERIOD_M5, 1);

    // Spread in price units (engine.py reads current_bar["spread"], 0 if absent).
    long spread_points = SymbolInfoInteger(_Symbol, SYMBOL_SPREAD);
    double point = SymbolInfoDouble(_Symbol, SYMBOL_POINT);
    double spread = (double)spread_points * point;

    double sl_price = Orders_ComputeSL(signal_kind,
                                       g_last_trigger.signal_candle_high,
                                       g_last_trigger.signal_candle_low,
                                       entry_price,
                                       spread, atr_value,
                                       InpWickBufferInSpreads,
                                       InpMinSlDistanceAtrMult);

    // Pick nearest viable TP from active levels (engine.py _pick_tp).
    double tp_price = PickTP(entry_price, dir, atr_value);
    if (tp_price == EMPTY_VALUE) return;   // no viable target — skip

    // Apply settle buffer (engine.py apply_settle_buffer).
    string dir_str = (dir == DIR_BUY) ? "bull" : "bear";
    tp_price = Targets_ApplySettle(tp_price, dir_str, atr_value, InpSettleBufferAtrMult);

    // ============================================================
    // 8. ShouldOpen gate (§7.5 checklist) — engine.py Step 8
    // ============================================================
    string reason = "";
    if (!Orders_ShouldOpen(g_account, dir, dir, /*entry_triggered=*/true,
                           entry_price, sl_price, tp_price,
                           _Symbol, session, open_symbols, open_n,
                           InpMinRR, InpMaxTradesPerSession,
                           InpDailyDDStopPct, InpWeeklyDDStopPct,
                           InpNewsFilterEnabled, InpNewsFilterWindowMin,
                           reason)) {
        return;
    }

    // ============================================================
    // 9. Min R:R + position size — engine.py Step 9
    //   ShouldOpen already checked min R:R; the explicit re-check mirrors
    //   the design-spec skeleton's Risk_CheckMinRR(plan) step (harmless).
    // ============================================================
    if (!Risk_CheckMinRR(entry_price, sl_price, tp_price, InpMinRR)) return;

    // Convert raw price-unit SL distance to pip count BEFORE sizing — fixes
    // the engine.py v1 bug (pip-unit conversion at the risk boundary).
    double sl_distance_price = MathAbs(entry_price - sl_price);
    double sl_distance_pips  = PriceDistanceToPips(_Symbol, sl_distance_price);
    double lot_size = Risk_ComputePositionSize(g_account, sl_distance_pips,
                                               _Symbol, InpRiskPercent);
    if (lot_size <= 0.0) return;

    // ============================================================
    // 10. Submit + log — engine.py Step 10 (open position)
    // ============================================================
    OrderPlan plan = Orders_BuildPlan(_Symbol, dir, entry_price, sl_price, tp_price,
                                      lot_size,
                                      g_winning_setup,                  // setup_type
                                      g_last_trigger.confluence_type,   // confluence_type
                                      g_last_mmd_alignment,             // mmd_alignment
                                      g_last_d1_zone,                   // d1_zone
                                      InpDirectionStrict);

    if (Orders_Submit(g_trade, plan)) {
        // Resolve the broker POSITION id for this fill so OnTradeTransaction
        // can match the eventual close (which reports DEAL_POSITION_ID). The
        // opening deal's DEAL_POSITION_ID is the canonical position id; fall
        // back to the result order/deal ticket if history isn't selectable.
        ulong pos_ticket = g_trade.ResultOrder();
        ulong open_deal  = g_trade.ResultDeal();
        if (open_deal != 0 && HistoryDealSelect(open_deal)) {
            pos_ticket = (ulong)HistoryDealGetInteger(open_deal, DEAL_POSITION_ID);
        }

        // Tick session trade count (engine.py trades_this_session[session] += 1).
        if      (session == SESSION_ASIA)    g_account.trades_session_asia++;
        else if (session == SESSION_LONDON)  g_account.trades_session_london++;
        else if (session == SESSION_AMERICA) g_account.trades_session_america++;

        // Track the in-flight position for OnTick maintenance + closure logging.
        datetime ts_open = iTime(_Symbol, PERIOD_M5, 1);
        PositionState pos;
        Orders_InitPositionState(pos, plan, pos_ticket, ts_open);
        int sz = ArraySize(g_positions);
        ArrayResize(g_positions, sz + 1);
        g_positions[sz] = pos;
    }
}

//+------------------------------------------------------------------+
//| OnTradeTransaction — event-driven closure detection (Decision 6). |
//|                                                                   |
//| Fires once per broker-confirmed trade event. We act only on       |
//| position-close fills (DEAL_ENTRY_OUT), look up the matching        |
//| tracked PositionState by position-id, compute PnL, write the final |
//| ledger row, and drop the position from g_positions[].             |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
{
    if (trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
    if (trans.deal == 0) return;
    if (!DealIsCloseEntry(trans.deal)) return;

    double   exit_price; double volume; datetime ts_close;
    string   sym; ulong position_id;
    if (!Orders_HandleClosedDeal(trans.deal, exit_price, volume, ts_close,
                                 sym, position_id)) {
        return;
    }

    int idx = FindPositionByTicket(position_id);
    if (idx < 0) return;   // not one of ours (or already logged)

    // Distinguish a PARTIAL close (position still open at the broker) from a
    // FULL close. Partial-close deals are already logged in OnTick via
    // Logger_WritePartial — logging them again here would double-count. A full
    // close leaves no remaining position for this id.
    if (PositionSelectByTicket(position_id)) return;   // still open → was a partial

    // Classify the exit reason from the deal reason. SL / TP are broker-
    // tagged; everything else (trailing-stop hit lands here too) maps to
    // sl_hit/tp_hit by price proximity. engine.py only emits sl_hit / tp_hit /
    // partial / forced_eod, so we collapse to those.
    string exit_reason = "tp_hit";
    long deal_reason = HistoryDealGetInteger(trans.deal, DEAL_REASON);
    if (deal_reason == DEAL_REASON_SL) {
        exit_reason = "sl_hit";
    } else if (deal_reason == DEAL_REASON_TP) {
        exit_reason = "tp_hit";
    } else {
        // Fallback by direction + price (manual / trailing close).
        if (g_positions[idx].direction == DIR_BUY)
            exit_reason = (exit_price <= g_positions[idx].sl_price) ? "sl_hit" : "tp_hit";
        else
            exit_reason = (exit_price >= g_positions[idx].sl_price) ? "sl_hit" : "tp_hit";
    }

    CloseTrackedPosition(idx, exit_price, ts_close, exit_reason);
}

//+------------------------------------------------------------------+
//| OnDeinit — force-close ledger rows, close logger, release handles.|
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    // engine.py Step 10: force-close any still-open positions at final close.
    // In a Strategy Tester pass OnDeinit fires once after the last bar; we
    // write a forced_eod row for any position the broker hasn't already
    // surfaced a close for.
    ForceCloseAllAtExit();

    Logger_Close(g_ledger);

    if (g_ema21_handle != INVALID_HANDLE) IndicatorRelease(g_ema21_handle);
    if (g_sma61_handle != INVALID_HANDLE) IndicatorRelease(g_sma61_handle);
    ATR_Release();
    ReleaseMMD();
}

//+------------------------------------------------------------------+
//| OnTester — v1 placeholder fitness (Phase 4 refines).              |
//|                                                                   |
//| Design spec open-question 3: v1 = pnl_money / trade_count proxy.  |
//| We return final closed-trade equity gain; with no trades the      |
//| Strategy Tester default (profit) is used by returning 0.          |
//+------------------------------------------------------------------+
double OnTester()
{
    double profit = TesterStatistics(STAT_PROFIT);
    double trades = TesterStatistics(STAT_TRADES);
    if (trades <= 0.0) return 0.0;
    return profit / trades;   // pnl per trade (v1 proxy)
}


//==================================================================
// EA-internal helpers
//==================================================================

//+------------------------------------------------------------------+
//| Copy the closed-bar window into out_bars (chronological, oldest   |
//| first; index n-1 = most recently closed bar = shift 1). Excludes  |
//| the still-forming bar 0. Returns count (<= BAR_WINDOW).           |
//+------------------------------------------------------------------+
int CopyClosedBars(MqlRates &out_bars[])
{
    // Copy starting at shift 1 (skip the forming bar) for BAR_WINDOW bars.
    MqlRates tmp[];
    int got = CopyRates(_Symbol, PERIOD_M5, 1, BAR_WINDOW, tmp);
    if (got <= 0) {
        ArrayResize(out_bars, 0);
        return 0;
    }
    // CopyRates with (start_pos, count) returns oldest-first already.
    ArrayResize(out_bars, got);
    for (int i = 0; i < got; i++) out_bars[i] = tmp[i];
    return got;
}

//+------------------------------------------------------------------+
//| Compute an EMA(InpEmaPeriod) series aligned 1:1 with bars[] using |
//| the same recursive formula as pandas ewm(span=N, adjust=False)    |
//| (engine.py ema_series). Seeded with bars[0].close. Mirrors        |
//| signals.sentiment's EMA basis used by the §5 EMA-side check.      |
//|                                                                   |
//| NOTE: PAC_Targets.Targets_DetectMeasuredMoves reads this series   |
//| at pivot bars; building it natively (rather than via the iMA      |
//| handle) guarantees the same warmup/seed semantics as Plan 4.      |
//+------------------------------------------------------------------+
void ComputeEmaSeries(const MqlRates &bars[], int n, double &out_ema[])
{
    ArrayResize(out_ema, n);
    if (n == 0) return;
    double alpha = 2.0 / (InpEmaPeriod + 1.0);
    out_ema[0] = bars[0].close;
    for (int i = 1; i < n; i++) {
        out_ema[i] = alpha * bars[i].close + (1.0 - alpha) * out_ema[i - 1];
    }
}

//+------------------------------------------------------------------+
//| Read an iMA handle value at the given bar shift; EMPTY_VALUE when |
//| the buffer isn't yet populated (mirrors Python NaN handling that  |
//| PAC_Signals.mqh checks for via == EMPTY_VALUE).                   |
//+------------------------------------------------------------------+
double EmaValueAtShift(int handle, int bar_shift)
{
    double tmp[1];
    if (CopyBuffer(handle, 0, bar_shift, 1, tmp) != 1) return EMPTY_VALUE;
    return tmp[0];
}

//+------------------------------------------------------------------+
//| Targets_Update — §5 ALWAYS-RUN target-engine maintenance.         |
//|                                                                   |
//| Mirrors engine.py Step 3 + active_levels assembly:                |
//|   swings  = detect_swings(bars_slice, impulse_atr_mult_min, 20)   |
//|   mms     = detect_measured_moves(bars_slice, swings, ema_slice)  |
//|   fibs    = fibonacci_levels(bars_slice, mms)                     |
//|   clusters= find_clusters(fibs, atr_value)                        |
//|   active_levels = [valid mm.d_target] + [extended_mm (if any)]    |
//|                 + [fib prices] + [cluster prices]                 |
//|                                                                   |
//| Rebuilds g_active_levels / g_active_types each bar (state-free —  |
//| engine.py recomputes from scratch every bar). overshoot_bars is   |
//| re-derived from the post-C price scan inside detect_measured_     |
//| moves, so the §5.3 extended (138.2%) target fires once a valid MM |
//| has held beyond D for overshoot_bars_min bars (matches engine.py).|
//+------------------------------------------------------------------+
void Targets_Update(string symbol, const MqlRates &bars[], int n, double atr_value)
{
    g_active_count = 0;
    ArrayResize(g_active_levels, 0);
    ArrayResize(g_active_types, 0);

    // EMA series aligned to bars (for the MM EMA-side pivot check).
    double ema_series[];
    ComputeEmaSeries(bars, n, ema_series);

    // §5.1 swings → measured moves.
    Swing swings[];
    int sw_count = Swing_Detect(bars, n, InpImpulseAtrMultMin, ATR_PERIOD, swings);

    MeasuredMove mms[];
    int n_mms = Targets_DetectMeasuredMoves(bars, n, swings, sw_count,
                                            ema_series, n,
                                            InpImpulseAtrMultMin,
                                            InpMaxActiveMeasuredMoves,
                                            ATR_PERIOD, mms);

    // §5.2 fib levels.
    double ratios_R[]; double ratios_E[];
    int nR = ParseDoubleCSV(InpFibLevelsRetracement, ratios_R);
    int nE = ParseDoubleCSV(InpFibLevelsExtension, ratios_E);
    FibLevel fibs[];
    int n_fibs = Targets_FibLevels(mms, n_mms, ratios_R, nR, ratios_E, nE, fibs);

    // §5.2 clusters.
    Cluster clusters[];
    int n_clusters = Targets_FindClusters(fibs, n_fibs, atr_value,
                                          InpClusterPipsAtrMult,
                                          InpClusterMemberMin, clusters);

    // Assemble active levels (engine.py order: d_target, extended, fib, cluster).
    for (int m = 0; m < n_mms; m++) {
        if (mms[m].validity != "valid") continue;
        AppendLevel(mms[m].d_target, "mm_d");
        double ext = Targets_ExtendedMM(mms[m], InpOvershootBarsMin);
        if (ext != EMPTY_VALUE) AppendLevel(ext, "mm_extended");
    }
    for (int f = 0; f < n_fibs; f++) AppendLevel(fibs[f].price, fibs[f].label);
    for (int c = 0; c < n_clusters; c++) AppendLevel(clusters[c].price, "cluster");
}

//+------------------------------------------------------------------+
//| Append a (price, type) pair to the active-levels parallel arrays. |
//+------------------------------------------------------------------+
void AppendLevel(double price, string type_tag)
{
    int sz = g_active_count;
    ArrayResize(g_active_levels, sz + 1);
    ArrayResize(g_active_types,  sz + 1);
    g_active_levels[sz] = price;
    g_active_types[sz]  = type_tag;
    g_active_count = sz + 1;
}

//+------------------------------------------------------------------+
//| Parse a comma-separated list of doubles (e.g. "0.382,0.5,0.618"). |
//| Returns count; fills out[].                                       |
//+------------------------------------------------------------------+
int ParseDoubleCSV(string csv, double &out[])
{
    string parts[];
    int k = StringSplit(csv, ',', parts);
    if (k <= 0) { ArrayResize(out, 0); return 0; }
    ArrayResize(out, k);
    for (int i = 0; i < k; i++) {
        string s = parts[i];
        StringTrimLeft(s);
        StringTrimRight(s);
        out[i] = StringToDouble(s);
    }
    return k;
}

//+------------------------------------------------------------------+
//| Setups_StepAll — §6 ALWAYS-RUN setup-state-machine maintenance.   |
//|                                                                   |
//| Mirrors engine.py Step §6 lifecycle:                              |
//|   1. Rebuild registry: fresh idle machines for new MM ids, carry  |
//|      forward existing machines for known ids, drop vanished MMs.  |
//|   2. Step every live machine by one bar (trap/fail MM-anchored;   |
//|      spike reads the recent bars window).                         |
//|   3. Collect (mm_id, setup) for machines that reached 'triggered';|
//|      pick winner by SETUP_PRIORITY (trap > fail > spike_channel)  |
//|      into g_winning_setup.                                        |
//|                                                                   |
//| The just-closed bar (index n-1) is the "current bar" being        |
//| stepped, matching engine.py's current_bar = bars.iloc[bar_idx].   |
//+------------------------------------------------------------------+
void Setups_StepAll(string symbol, const MqlRates &bars[], int n, double atr_value)
{
    g_winning_setup = "none";
    if (n == 0) return;

    // Recompute current MMs (same inputs as Targets_Update).
    double ema_series[];
    ComputeEmaSeries(bars, n, ema_series);
    Swing swings[];
    int sw_count = Swing_Detect(bars, n, InpImpulseAtrMultMin, ATR_PERIOD, swings);
    MeasuredMove mms[];
    int n_mms = Targets_DetectMeasuredMoves(bars, n, swings, sw_count,
                                            ema_series, n,
                                            InpImpulseAtrMultMin,
                                            InpMaxActiveMeasuredMoves,
                                            ATR_PERIOD, mms);

    // ---- 1. Rebuild registry against the current valid-MM id set ----
    int next_mm_id[MAX_SETUP_MACHINES];
    TrapState         next_trap[MAX_SETUP_MACHINES];
    FailState         next_fail[MAX_SETUP_MACHINES];
    SpikeChannelState next_spike[MAX_SETUP_MACHINES];
    int next_count = 0;

    for (int m = 0; m < n_mms && next_count < MAX_SETUP_MACHINES; m++) {
        if (mms[m].validity != "valid") continue;
        int mm_id = mms[m].id;

        int existing = -1;
        for (int e = 0; e < g_sm_count; e++) {
            if (g_sm_mm_id[e] == mm_id) { existing = e; break; }
        }

        next_mm_id[next_count] = mm_id;
        if (existing >= 0) {
            next_trap[next_count]  = g_sm_trap[existing];
            next_fail[next_count]  = g_sm_fail[existing];
            next_spike[next_count] = g_sm_spike[existing];
        } else {
            Setups_InitTrapState(next_trap[next_count], mm_id);
            Setups_InitFailState(next_fail[next_count], mm_id);
            Setups_InitSpikeChannelState(next_spike[next_count]);
        }
        next_count++;
    }

    // ---- Prepare the spike window (last spike_min_bars closes/opens) ----
    int spike_window = (InpSpikeMinBars > 1) ? InpSpikeMinBars : 1;
    int from = (n >= spike_window) ? (n - spike_window) : 0;
    int wn = n - from;
    double w_opens[]; double w_closes[];
    ArrayResize(w_opens, wn);
    ArrayResize(w_closes, wn);
    for (int i = 0; i < wn; i++) {
        w_opens[i]  = bars[from + i].open;
        w_closes[i] = bars[from + i].close;
    }

    int cur_idx = n - 1;                  // engine.py bar_idx (current bar)
    double bo = bars[cur_idx].open;
    double bh = bars[cur_idx].high;
    double bl = bars[cur_idx].low;
    double bc = bars[cur_idx].close;

    // ---- 2. Step every live machine by one bar ----
    for (int s = 0; s < next_count; s++) {
        // Find the matching MM struct for trap/fail (MM-anchored).
        int mi = -1;
        for (int m = 0; m < n_mms; m++) {
            if (mms[m].validity == "valid" && mms[m].id == next_mm_id[s]) { mi = m; break; }
        }
        if (mi < 0) continue;

        Setups_StepTrap(next_trap[s], bo, bh, bl, bc, cur_idx, mms[mi], atr_value,
                        InpTrapFirstTryLevel, InpTrapFailureThreshAtrMult,
                        InpTrapMaxBarsBetweenTries, InpTrapMaxFirstTryPenetrationFib);

        Setups_StepFail(next_fail[s], bo, bh, bl, bc, cur_idx, mms[mi], atr_value,
                        InpFailMinFirstAttemptDepthFib,
                        InpFailSecondAttemptShortfallAtrMult,
                        InpFailMaxBarsBetweenAttempts);

        Setups_StepSpikeChannel(next_spike[s], bo, bh, bl, bc, cur_idx,
                                w_opens, w_closes, wn, atr_value,
                                InpSpikeMinBars, InpSpikeMinMagnitudeAtr,
                                InpSpikeMaxCounterBars, InpChannelMinBars,
                                InpPullbackInvalidationFib);
    }

    // ---- 3. Collect fires + pick winner by priority ----
    bool fired_trap = false, fired_fail = false, fired_spike = false;
    for (int s = 0; s < next_count; s++) {
        if (Setups_TrapTriggered(next_trap[s]))          fired_trap = true;
        if (Setups_FailTriggered(next_fail[s]))          fired_fail = true;
        if (Setups_SpikeChannelTriggered(next_spike[s])) fired_spike = true;
    }
    if      (fired_trap)  g_winning_setup = "trap";
    else if (fired_fail)  g_winning_setup = "fail";
    else if (fired_spike) g_winning_setup = "spike_channel";
    else                  g_winning_setup = "none";

    // ---- Commit the rebuilt registry back to the globals ----
    g_sm_count = next_count;
    for (int s = 0; s < next_count; s++) {
        g_sm_mm_id[s] = next_mm_id[s];
        g_sm_trap[s]  = next_trap[s];
        g_sm_fail[s]  = next_fail[s];
        g_sm_spike[s] = next_spike[s];
    }
}

//+------------------------------------------------------------------+
//| Session high/low box for §3.4 — high/low of all bars earlier than |
//| the just-closed bar (shift 1) that fall in the SAME session on    |
//| the SAME calendar day. Mirrors signals.session_box_position bar   |
//| collection (prior bars only, same day, same session).            |
//|                                                                   |
//| Returns false if no prior session bars exist (caller treats the   |
//| box as 'inside', matching the Python early return).               |
//+------------------------------------------------------------------+
bool SessionBoxHighLow(string symbol, int session, double &out_high, double &out_low)
{
    datetime cur_time = iTime(symbol, PERIOD_M5, 1);
    MqlDateTime cur_m;
    TimeToStruct(cur_time, cur_m);

    out_high = -DBL_MAX;
    out_low  =  DBL_MAX;
    bool found = false;

    // Walk backward from shift 2 (strictly-earlier bars) within the day.
    for (int shift = 2; shift < BAR_WINDOW; shift++) {
        datetime t = iTime(symbol, PERIOD_M5, shift);
        if (t == 0) break;
        MqlDateTime m;
        TimeToStruct(t, m);
        // Stop once we cross to a previous calendar day (UTC).
        if (m.day != cur_m.day || m.mon != cur_m.mon || m.year != cur_m.year) break;
        if (TimeUtil_CurrentSessionForUtc(t) != session) continue;

        double hi = iHigh(symbol, PERIOD_M5, shift);
        double lo = iLow(symbol, PERIOD_M5, shift);
        if (hi > out_high) out_high = hi;
        if (lo < out_low)  out_low  = lo;
        found = true;
    }
    return found;
}

//+------------------------------------------------------------------+
//| Build the parallel array of currently-open symbols for §1.6.      |
//+------------------------------------------------------------------+
int OpenSymbolsArray(string &out_symbols[])
{
    int n = ArraySize(g_positions);
    ArrayResize(out_symbols, n);
    for (int i = 0; i < n; i++) out_symbols[i] = g_positions[i].symbol;
    return n;
}

//+------------------------------------------------------------------+
//| Convert a raw price-unit distance to pip count via PipSize.       |
//| Single source of truth (mirrors engine._price_distance_to_pips).  |
//+------------------------------------------------------------------+
double PriceDistanceToPips(string symbol, double price_distance)
{
    double ps = PipSize(symbol);
    if (ps <= 0.0) return 0.0;
    return price_distance / ps;
}

//+------------------------------------------------------------------+
//| Pick nearest viable TP from g_active_levels in the trade          |
//| direction. Mirrors engine.py _pick_tp:                            |
//|   min_move = min_rr × min_sl_distance_atr_multiple × atr          |
//|   bull → smallest level > entry + min_move                        |
//|   bear → largest  level < entry - min_move                        |
//| Returns EMPTY_VALUE when no candidate qualifies.                  |
//+------------------------------------------------------------------+
double PickTP(double entry_price, DirectionKind dir, double atr_value)
{
    if (g_active_count == 0) return EMPTY_VALUE;
    double min_move = InpMinRR * InpMinSlDistanceAtrMult * atr_value;

    double best = EMPTY_VALUE;
    if (dir == DIR_BUY) {
        for (int i = 0; i < g_active_count; i++) {
            double lvl = g_active_levels[i];
            if (lvl > entry_price + min_move) {
                if (best == EMPTY_VALUE || lvl < best) best = lvl;
            }
        }
    } else {
        for (int i = 0; i < g_active_count; i++) {
            double lvl = g_active_levels[i];
            if (lvl < entry_price - min_move) {
                if (best == EMPTY_VALUE || lvl > best) best = lvl;
            }
        }
    }
    return best;
}

//+------------------------------------------------------------------+
//| Find a tracked position by broker position-id (ticket). -1 = none.|
//+------------------------------------------------------------------+
int FindPositionByTicket(ulong position_id)
{
    for (int i = 0; i < ArraySize(g_positions); i++) {
        if (g_positions[i].ticket == position_id) return i;
    }
    return -1;
}

//+------------------------------------------------------------------+
//| Compute PnL, write the final ledger row, and drop the position    |
//| at index idx from g_positions[]. Mirrors engine.py's close path   |
//| (_compute_trade_pnl + _make_ledger_row).                          |
//+------------------------------------------------------------------+
void CloseTrackedPosition(int idx, double exit_price, datetime ts_close, string exit_reason)
{
    PositionState pos = g_positions[idx];

    double pnl_price = (pos.direction == DIR_BUY)
        ? (exit_price - pos.entry_price)
        : (pos.entry_price - exit_price);
    double pnl_pips  = PriceDistanceToPips(pos.symbol, pnl_price);
    double pnl_money = pnl_pips * pos.lot_size * PIP_VALUE_PER_LOT;
    double sl_dist_pips = PriceDistanceToPips(pos.symbol,
                            MathAbs(pos.entry_price - pos.sl_price));
    double r_mult = (sl_dist_pips > 0.0) ? (pnl_pips / sl_dist_pips) : 0.0;

    LedgerEntryRow row;
    row.trade_id        = pos.trade_id;
    row.ts_signal       = pos.ts_open;
    row.ts_open         = pos.ts_open;
    row.ts_close        = ts_close;
    row.symbol          = pos.symbol;
    row.direction       = (pos.direction == DIR_BUY) ? "BUY" : "SELL";
    row.entry_price     = pos.entry_price;
    row.sl_price        = pos.sl_price;
    row.tp_price        = pos.tp_price;
    row.exit_price      = exit_price;
    row.exit_reason     = exit_reason;
    row.pnl_pips        = pnl_pips;
    row.pnl_money       = pnl_money;
    row.r_multiple      = r_mult;
    row.setup_type      = pos.setup_type;
    row.direction_strict= pos.direction_strict_at_entry;
    row.mmd_alignment   = pos.mmd_alignment;
    row.d1_zone         = pos.d1_zone;
    row.confluence_type = pos.confluence_type;
    row.lot_size        = pos.lot_size;
    row.risk_pct        = InpRiskPercent;
    Logger_WriteExit(g_ledger, row);

    // Remove from g_positions[] (shift tail down).
    int last = ArraySize(g_positions) - 1;
    for (int i = idx; i < last; i++) g_positions[i] = g_positions[i + 1];
    ArrayResize(g_positions, last);
}

//+------------------------------------------------------------------+
//| Force-close any still-tracked positions at EA shutdown (engine.py |
//| Step 10 forced_eod). Uses the latest close price for PnL.         |
//| Only writes a row if the broker position is genuinely still open  |
//| (otherwise OnTradeTransaction already logged the close).          |
//+------------------------------------------------------------------+
void ForceCloseAllAtExit()
{
    double final_close = iClose(_Symbol, PERIOD_M5, 0);
    datetime final_time = iTime(_Symbol, PERIOD_M5, 0);

    // Iterate from the back since CloseTrackedPosition mutates the array.
    for (int i = ArraySize(g_positions) - 1; i >= 0; i--) {
        // If the broker no longer holds this position, its close already
        // flowed through OnTradeTransaction — skip to avoid a duplicate row.
        if (!PositionSelectByTicket(g_positions[i].ticket)) {
            int last = ArraySize(g_positions) - 1;
            for (int j = i; j < last; j++) g_positions[j] = g_positions[j + 1];
            ArrayResize(g_positions, last);
            continue;
        }
        CloseTrackedPosition(i, final_close, final_time, "forced_eod");
    }
}
//+------------------------------------------------------------------+
