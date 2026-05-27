//+------------------------------------------------------------------+
//| test_pac_risk.mq5                                                 |
//|                                                                   |
//| Mirrors hedgehog/proposer/pac/tests/test_risk.py scenarios        |
//| against the MQL5 port in PAC_Risk.mqh. Each MQL5 assertion         |
//| anchors a specific pytest line so divergence is immediately       |
//| visible from either side.                                         |
//|                                                                   |
//| Config defaults baked in (must match Python Config defaults):     |
//|   risk_percent                = 1.0                               |
//|   min_rr                      = 1.5                               |
//|   max_trades_per_session      = 3                                 |
//|   daily_dd_stop_pct           = -3.0                              |
//|   weekly_dd_stop_pct          = -5.0                              |
//|   news_filter_enabled         = false                             |
//|   news_filter_window_min      = 15                                |
//|   correlation_groups          = {XAUUSD,US500};{US500,US30,...}   |
//+------------------------------------------------------------------+
#property strict
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\PAC\\PAC_Risk.mqh"

// Local cfg defaults that mirror Config().
#define CFG_RISK_PERCENT             1.0
#define CFG_MIN_RR                   1.5
#define CFG_MAX_TRADES_PER_SESSION   3
#define CFG_DAILY_DD_STOP_PCT       -3.0
#define CFG_WEEKLY_DD_STOP_PCT      -5.0
#define CFG_NEWS_FILTER_WINDOW_MIN   15

//+------------------------------------------------------------------+
//| Helper — build a default AccountState with given equity.          |
//+------------------------------------------------------------------+
AccountState _MakeAccount(double equity) {
    AccountState acc;
    Risk_InitAccountState(acc, equity);
    return acc;
}

//+------------------------------------------------------------------+
//| Anchor: test_compute_position_size_basic                          |
//|   $10k equity, 10-pip SL, 1% risk → $100 / ($10×10) = 1.0 lots.   |
//+------------------------------------------------------------------+
void TestComputePositionSizeBasic() {
    AccountState acc = _MakeAccount(10000.0);
    double lots = Risk_ComputePositionSize(acc, 10.0, "EURUSD", CFG_RISK_PERCENT);
    ASSERT_NEAR(lots, 1.0, 0.01, "ComputePositionSize_basic_10k_10pip_1pct");
}

//+------------------------------------------------------------------+
//| Anchor: test_compute_position_size_tighter_sl_larger_lot          |
//|   $10k equity, 5-pip SL, 1% risk → $100 / ($10×5) = 2.0 lots.     |
//+------------------------------------------------------------------+
void TestComputePositionSizeTighterSL() {
    AccountState acc = _MakeAccount(10000.0);
    double lots = Risk_ComputePositionSize(acc, 5.0, "EURUSD", CFG_RISK_PERCENT);
    ASSERT_NEAR(lots, 2.0, 0.01, "ComputePositionSize_tighter_sl_2pct");
}

//+------------------------------------------------------------------+
//| Anchor: test_compute_position_size guards zero SL.                |
//+------------------------------------------------------------------+
void TestComputePositionSizeZeroSL() {
    AccountState acc = _MakeAccount(10000.0);
    double lots = Risk_ComputePositionSize(acc, 0.0, "EURUSD", CFG_RISK_PERCENT);
    ASSERT_NEAR(lots, 0.0, 1e-9, "ComputePositionSize_zero_sl_returns_zero");
}

//+------------------------------------------------------------------+
//| Anchor: test_check_min_rr_passes / test_check_min_rr_fails        |
//|   entry=100, sl=99, tp=102 → R:R = 2.0 ≥ 1.5 → pass               |
//|   entry=100, sl=99, tp=101 → R:R = 1.0 < 1.5 → block              |
//+------------------------------------------------------------------+
void TestCheckMinRR() {
    ASSERT_TRUE(Risk_CheckMinRR(100.0, 99.0, 102.0, CFG_MIN_RR),
                "CheckMinRR_rr_2_passes_1_5min");
    ASSERT_FALSE(Risk_CheckMinRR(100.0, 99.0, 101.0, CFG_MIN_RR),
                 "CheckMinRR_rr_1_blocks_1_5min");

    // Zero-risk guard: entry == sl → div-by-zero protection.
    ASSERT_FALSE(Risk_CheckMinRR(100.0, 100.0, 101.0, CFG_MIN_RR),
                 "CheckMinRR_zero_risk_returns_false");
}

//+------------------------------------------------------------------+
//| Anchor: test_check_session_cap_passes_under_limit /               |
//|         test_check_session_cap_fails_at_limit                     |
//+------------------------------------------------------------------+
void TestCheckSessionCap() {
    AccountState acc = _MakeAccount(10000.0);

    acc.trades_session_london = 2;
    ASSERT_TRUE(Risk_CheckSessionCap(acc, SESSION_LONDON, CFG_MAX_TRADES_PER_SESSION),
                "CheckSessionCap_london_2of3_passes");

    acc.trades_session_london = 3;
    ASSERT_FALSE(Risk_CheckSessionCap(acc, SESSION_LONDON, CFG_MAX_TRADES_PER_SESSION),
                 "CheckSessionCap_london_3of3_blocks");

    // Asia counter independent from London.
    acc.trades_session_asia = 0;
    ASSERT_TRUE(Risk_CheckSessionCap(acc, SESSION_ASIA, CFG_MAX_TRADES_PER_SESSION),
                "CheckSessionCap_asia_independent_of_london");
}

//+------------------------------------------------------------------+
//| Anchor: test_check_daily_dd_passes_when_above_floor /             |
//|         test_check_daily_dd_fails_when_below_floor                |
//|                                                                   |
//|   $9800 equity from $10000 start → -2% DD > -3% threshold → pass  |
//|   $9600 equity from $10000 start → -4% DD < -3% threshold → block |
//+------------------------------------------------------------------+
void TestCheckDailyDD() {
    AccountState acc = _MakeAccount(10000.0);

    acc.equity = 9800.0;
    ASSERT_TRUE(Risk_CheckDailyDD(acc, CFG_DAILY_DD_STOP_PCT),
                "CheckDailyDD_minus_2pct_passes");

    acc.equity = 9600.0;
    ASSERT_FALSE(Risk_CheckDailyDD(acc, CFG_DAILY_DD_STOP_PCT),
                 "CheckDailyDD_minus_4pct_blocks");

    // Boundary: exactly -3% → 9700 / 10000 = -3% → NOT > -3% → blocks.
    acc.equity = 9700.0;
    ASSERT_FALSE(Risk_CheckDailyDD(acc, CFG_DAILY_DD_STOP_PCT),
                 "CheckDailyDD_at_floor_blocks");

    // Defensive guard: zero starting equity → return true.
    acc.starting_equity_daily = 0.0;
    acc.equity = 5000.0;
    ASSERT_TRUE(Risk_CheckDailyDD(acc, CFG_DAILY_DD_STOP_PCT),
                "CheckDailyDD_zero_starting_returns_true");
}

//+------------------------------------------------------------------+
//| Anchor: test_check_weekly_dd_passes / test_check_weekly_dd_fails  |
//|                                                                   |
//|   $9700 equity from $10000 start → -3% > -5% → pass               |
//|   $9400 equity from $10000 start → -6% < -5% → block              |
//+------------------------------------------------------------------+
void TestCheckWeeklyDD() {
    AccountState acc = _MakeAccount(10000.0);

    acc.equity = 9700.0;
    ASSERT_TRUE(Risk_CheckWeeklyDD(acc, CFG_WEEKLY_DD_STOP_PCT),
                "CheckWeeklyDD_minus_3pct_passes_5pct_floor");

    acc.equity = 9400.0;
    ASSERT_FALSE(Risk_CheckWeeklyDD(acc, CFG_WEEKLY_DD_STOP_PCT),
                 "CheckWeeklyDD_minus_6pct_blocks_5pct_floor");
}

//+------------------------------------------------------------------+
//| Anchor: test_check_correlation_lock_blocks_overlap /              |
//|         test_check_correlation_lock_passes_no_overlap             |
//|                                                                   |
//| Group setup mirrors Config defaults:                              |
//|   {XAUUSD,US500};{US500,US30,USTECH};{USOIL,US500}                |
//+------------------------------------------------------------------+
void TestCheckCorrelationLock() {
    Universe_InitCorrelationGroups(
        "{XAUUSD,US500};{US500,US30,USTECH};{USOIL,US500}");

    AccountState acc = _MakeAccount(10000.0);

    // Overlap case: open XAUUSD, propose US500 — same group → block.
    string open1[1] = {"XAUUSD"};
    ASSERT_FALSE(Risk_CheckCorrelationLock(acc, "US500", DIR_BUY, open1, 1),
                 "CheckCorrelationLock_XAUUSD_vs_US500_blocks");

    // No-overlap case: open EURUSD, propose US500 — different group → pass.
    string open2[1] = {"EURUSD"};
    ASSERT_TRUE(Risk_CheckCorrelationLock(acc, "US500", DIR_BUY, open2, 1),
                "CheckCorrelationLock_EURUSD_vs_US500_passes");

    // No open positions → trivially pass.
    string open0[];
    ArrayResize(open0, 0);
    ASSERT_TRUE(Risk_CheckCorrelationLock(acc, "US500", DIR_BUY, open0, 0),
                "CheckCorrelationLock_no_open_positions_passes");

    // Identical symbol does NOT count as correlated (Universe_AreCorrelated
    // returns false for a == b). The downstream session-cap or duplicate-
    // position guard handles same-symbol cases.
    string open3[1] = {"US500"};
    ASSERT_TRUE(Risk_CheckCorrelationLock(acc, "US500", DIR_BUY, open3, 1),
                "CheckCorrelationLock_same_symbol_not_correlated");
}

//+------------------------------------------------------------------+
//| Anchor: test_check_news_blackout_disabled_always_passes /         |
//|         test_check_news_blackout_enabled_within_window_fails /    |
//|         test_check_news_blackout_enabled_outside_window_passes    |
//+------------------------------------------------------------------+
void TestCheckNewsBlackout() {
    AccountState acc = _MakeAccount(10000.0);

    // Disabled — even a recent event passes.
    acc.last_news_event_minutes_ago = 5;
    ASSERT_TRUE(Risk_CheckNewsBlackout(acc, false, CFG_NEWS_FILTER_WINDOW_MIN),
                "CheckNewsBlackout_disabled_always_passes");

    // Enabled + within window (10 < 15) → block.
    acc.last_news_event_minutes_ago = 10;
    ASSERT_FALSE(Risk_CheckNewsBlackout(acc, true, CFG_NEWS_FILTER_WINDOW_MIN),
                 "CheckNewsBlackout_within_window_blocks");

    // Enabled + outside window (30 > 15) → pass.
    acc.last_news_event_minutes_ago = 30;
    ASSERT_TRUE(Risk_CheckNewsBlackout(acc, true, CFG_NEWS_FILTER_WINDOW_MIN),
                "CheckNewsBlackout_outside_window_passes");

    // Enabled + INT_MAX sentinel (no event) → pass trivially.
    acc.last_news_event_minutes_ago = INT_MAX;
    ASSERT_TRUE(Risk_CheckNewsBlackout(acc, true, CFG_NEWS_FILTER_WINDOW_MIN),
                "CheckNewsBlackout_int_max_sentinel_passes");
}

void OnStart() {
    TestComputePositionSizeBasic();
    TestComputePositionSizeTighterSL();
    TestComputePositionSizeZeroSL();
    TestCheckMinRR();
    TestCheckSessionCap();
    TestCheckDailyDD();
    TestCheckWeeklyDD();
    TestCheckCorrelationLock();
    TestCheckNewsBlackout();
    Print("test_pac_risk: scenarios complete");
}
