//+------------------------------------------------------------------+
//| test_pac_orders.mq5                                               |
//|                                                                   |
//| Per Plan 5 design Decision 5, this script tests MQL5-SPECIFIC     |
//| surfaces only:                                                    |
//|                                                                   |
//|   - Orders_ComputeSL math (wick-based + min-distance clamp)       |
//|   - DealIsCloseEntry helper (HistoryDealGetInteger gate)          |
//|   - Orders_DetectFillingMode bitmask preference                   |
//|   - Orders_MaybePartial / Orders_MaybeTrail state-machine glue    |
//|     where the MQL5 mutate-by-ref deviates from Python's frozen-   |
//|     dataclass + replace semantics                                 |
//|                                                                   |
//| Algorithmic-correctness tests for compute_sl, maybe_partial_close,|
//| maybe_trail_sl, and should_open are covered by                    |
//| hedgehog/proposer/pac/tests/test_orders.py (Plan 4 pytest) — we   |
//| do not duplicate them; Phase 3 ledger-diff catches any divergence.|
//+------------------------------------------------------------------+
#property strict
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\PAC\\PAC_Orders.mqh"

// Config defaults mirroring Config() — needed for ComputeSL test parity
// with hedgehog/proposer/pac/tests/test_orders.py.
#define CFG_WICK_BUFFER_IN_SPREADS           1
#define CFG_MIN_SL_DISTANCE_ATR_MULTIPLE    0.3
#define CFG_PARTIALS_TRIGGER_R              1.0
#define CFG_TRAILING_ACTIVATION_R           1.5
#define CFG_TRAILING_DISTANCE_ATR_MULTIPLE  1.0

//+------------------------------------------------------------------+
//| Anchor: test_compute_sl_bullish_below_low (test_orders.py:28)     |
//|                                                                   |
//| Bullish bar OHLC (100, 101, 99, 100.5), spread=0.5, ATR=10.       |
//| Wick SL = 99 - 0.5 - 1*0.5 = 98.0                                 |
//| min_distance = 0.3 * 10 = 3.0                                     |
//| close - SL = 100.5 - 98 = 2.5 < 3.0 → clamp                       |
//| Final SL = 100.5 - 3.0 = 97.5                                     |
//+------------------------------------------------------------------+
void TestComputeSLBullishBelowLow() {
    double sl = Orders_ComputeSL(
        "bullish",
        /* signal_high */ 101.0, /* signal_low */ 99.0, /* signal_close */ 100.5,
        /* spread */ 0.5, /* atr */ 10.0,
        CFG_WICK_BUFFER_IN_SPREADS, CFG_MIN_SL_DISTANCE_ATR_MULTIPLE
    );
    ASSERT_NEAR(sl, 97.5, 0.01, "ComputeSL_bullish_clamps_to_min_distance");
}

//+------------------------------------------------------------------+
//| Anchor: test_compute_sl_bearish_above_high (test_orders.py:39)    |
//|                                                                   |
//| Bearish bar OHLC (100, 101, 99, 99.5).                            |
//| Wick SL = 101 + 0.5 + 0.5 = 102.0                                 |
//| min_distance = 3.0; SL - close = 102 - 99.5 = 2.5 < 3.0 → clamp   |
//| Final SL = 99.5 + 3.0 = 102.5                                     |
//+------------------------------------------------------------------+
void TestComputeSLBearishAboveHigh() {
    double sl = Orders_ComputeSL(
        "bearish",
        101.0, 99.0, 99.5,
        0.5, 10.0,
        CFG_WICK_BUFFER_IN_SPREADS, CFG_MIN_SL_DISTANCE_ATR_MULTIPLE
    );
    ASSERT_NEAR(sl, 102.5, 0.01, "ComputeSL_bearish_clamps_to_min_distance");
}

//+------------------------------------------------------------------+
//| Anchor: test_compute_sl_respects_natural_wick_when_wider_than_min |
//|                                                                   |
//| Wide bullish bar (low=95). Wick SL = 95 - 0.5 - 0.5 = 94.0.       |
//| close - SL = 100.5 - 94 = 6.5 > min_distance 3.0 → keep 94.0.     |
//+------------------------------------------------------------------+
void TestComputeSLNaturalWickWiderThanMin() {
    double sl = Orders_ComputeSL(
        "bullish",
        101.0, 95.0, 100.5,
        0.5, 10.0,
        CFG_WICK_BUFFER_IN_SPREADS, CFG_MIN_SL_DISTANCE_ATR_MULTIPLE
    );
    ASSERT_NEAR(sl, 94.0, 0.01, "ComputeSL_wide_wick_kept");
}

//+------------------------------------------------------------------+
//| DealIsCloseEntry — invalid deal ticket must return false          |
//| (defensive guard; HistoryDealSelect rejects unknown id).          |
//+------------------------------------------------------------------+
void TestDealIsCloseEntryInvalidReturnsFalse() {
    // 0 is never a valid deal ticket — HistoryDealSelect returns false.
    bool result = DealIsCloseEntry(0);
    ASSERT_FALSE(result, "DealIsCloseEntry_invalid_ticket_returns_false");
}

//+------------------------------------------------------------------+
//| Orders_DetectFillingMode — must return a valid ENUM_ORDER_TYPE_   |
//| FILLING value (FOK | IOC | RETURN) for any tradable symbol.      |
//|                                                                   |
//| We don't assert a specific mode (broker-dependent), just that the |
//| returned value is one of the three known constants.               |
//+------------------------------------------------------------------+
void TestDetectFillingModeReturnsValid() {
    int mode = Orders_DetectFillingMode(_Symbol);
    bool valid = (mode == ORDER_FILLING_FOK)
              || (mode == ORDER_FILLING_IOC)
              || (mode == ORDER_FILLING_RETURN);
    ASSERT_TRUE(valid, "DetectFillingMode_returns_valid_enum_value");
}

//+------------------------------------------------------------------+
//| Orders_MaybePartial — disabled returns false, position unchanged. |
//+------------------------------------------------------------------+
void TestMaybePartialDisabledReturnsFalse() {
    PositionState pos;
    pos.symbol         = "EURUSD";
    pos.direction      = DIR_BUY;
    pos.entry_price    = 100.0;
    pos.sl_price       = 99.0;
    pos.tp_price       = 102.0;
    pos.partial_taken  = false;

    bool changed = Orders_MaybePartial(pos, /* current */ 101.0,
                                       /* enabled */ false,
                                       CFG_PARTIALS_TRIGGER_R);
    ASSERT_FALSE(changed, "MaybePartial_disabled_returns_false");
    ASSERT_FALSE(pos.partial_taken, "MaybePartial_disabled_partial_taken_unchanged");
    ASSERT_NEAR(pos.sl_price, 99.0, 1e-9, "MaybePartial_disabled_sl_unchanged");
}

//+------------------------------------------------------------------+
//| Orders_MaybePartial — fires at 1R for BUY, moves SL to BE.        |
//| Mirrors test_orders.py:test_maybe_partial_close_fires_at_1r.      |
//+------------------------------------------------------------------+
void TestMaybePartialFiresAt1R_Buy() {
    PositionState pos;
    pos.symbol         = "EURUSD";
    pos.direction      = DIR_BUY;
    pos.entry_price    = 100.0;
    pos.sl_price       = 99.0;
    pos.tp_price       = 102.0;
    pos.partial_taken  = false;

    bool changed = Orders_MaybePartial(pos, /* current */ 101.0,
                                       /* enabled */ true,
                                       CFG_PARTIALS_TRIGGER_R);
    ASSERT_TRUE(changed, "MaybePartial_buy_at_1R_fires");
    ASSERT_TRUE(pos.partial_taken, "MaybePartial_buy_partial_taken_set");
    ASSERT_NEAR(pos.sl_price, 100.0, 1e-9, "MaybePartial_buy_sl_moves_to_BE");
}

//+------------------------------------------------------------------+
//| Orders_MaybePartial — already taken returns false (idempotent).   |
//+------------------------------------------------------------------+
void TestMaybePartialAlreadyTaken() {
    PositionState pos;
    pos.symbol         = "EURUSD";
    pos.direction      = DIR_BUY;
    pos.entry_price    = 100.0;
    pos.sl_price       = 100.0;   // already at BE
    pos.tp_price       = 102.0;
    pos.partial_taken  = true;

    bool changed = Orders_MaybePartial(pos, 101.5, true, CFG_PARTIALS_TRIGGER_R);
    ASSERT_FALSE(changed, "MaybePartial_already_taken_returns_false");
}

//+------------------------------------------------------------------+
//| Orders_MaybePartial — SELL fires when price drops to 1R below.    |
//+------------------------------------------------------------------+
void TestMaybePartialFiresAt1R_Sell() {
    PositionState pos;
    pos.symbol         = "EURUSD";
    pos.direction      = DIR_SELL;
    pos.entry_price    = 100.0;
    pos.sl_price       = 101.0;   // 1R = 1.0
    pos.tp_price       = 98.0;
    pos.partial_taken  = false;

    // Price at 99.0 = entry - 1.0 = exactly 1R below
    bool changed = Orders_MaybePartial(pos, 99.0, true, CFG_PARTIALS_TRIGGER_R);
    ASSERT_TRUE(changed, "MaybePartial_sell_at_1R_fires");
    ASSERT_TRUE(pos.partial_taken, "MaybePartial_sell_partial_taken_set");
    ASSERT_NEAR(pos.sl_price, 100.0, 1e-9, "MaybePartial_sell_sl_moves_to_BE");
}

//+------------------------------------------------------------------+
//| Orders_MaybeTrail — disabled returns false, no activation.        |
//+------------------------------------------------------------------+
void TestMaybeTrailDisabledNoActivation() {
    PositionState pos;
    pos.symbol                       = "EURUSD";
    pos.direction                    = DIR_BUY;
    pos.entry_price                  = 100.0;
    pos.sl_price                     = 99.0;
    pos.tp_price                     = 103.0;
    pos.trailing_active              = false;
    pos.trailing_atr_frozen          = EMPTY_VALUE;
    pos.peak_price_since_activation  = EMPTY_VALUE;

    bool changed = Orders_MaybeTrail(pos, /* bar_high */ 101.5, /* bar_low */ 100.8,
                                     /* atr */ 1.0,
                                     /* enabled */ false,
                                     CFG_TRAILING_ACTIVATION_R,
                                     CFG_TRAILING_DISTANCE_ATR_MULTIPLE);
    ASSERT_FALSE(changed, "MaybeTrail_disabled_returns_false");
    ASSERT_FALSE(pos.trailing_active, "MaybeTrail_disabled_not_activated");
}

//+------------------------------------------------------------------+
//| Orders_MaybeTrail — activates at 1.5R for BUY, ratchets SL up.    |
//| Mirrors test_orders.py:test_maybe_trail_sl_activates_at_1_5r.     |
//|                                                                   |
//| Entry=100, SL=99 → R=1.0; activation_price = 100 + 1.5 = 101.5    |
//| bar_high=101.6 ≥ 101.5 → activate, peak = 101.6                   |
//| trail_distance = 1.0 × 1.0 = 1.0; new_sl = 101.6 - 1.0 = 100.6    |
//| max(100.6, 99) = 100.6 → ratchets up from 99 to 100.6              |
//+------------------------------------------------------------------+
void TestMaybeTrailActivatesAt1_5R_Buy() {
    PositionState pos;
    pos.symbol                       = "EURUSD";
    pos.direction                    = DIR_BUY;
    pos.entry_price                  = 100.0;
    pos.sl_price                     = 99.0;
    pos.tp_price                     = 105.0;
    pos.trailing_active              = false;
    pos.trailing_atr_frozen          = EMPTY_VALUE;
    pos.peak_price_since_activation  = EMPTY_VALUE;

    bool changed = Orders_MaybeTrail(pos, 101.6, 100.8, 1.0,
                                     true,
                                     CFG_TRAILING_ACTIVATION_R,
                                     CFG_TRAILING_DISTANCE_ATR_MULTIPLE);
    ASSERT_TRUE(changed, "MaybeTrail_buy_activates_at_1_5R");
    ASSERT_TRUE(pos.trailing_active, "MaybeTrail_buy_trailing_active_set");
    ASSERT_NEAR(pos.peak_price_since_activation, 101.6, 1e-9,
                "MaybeTrail_buy_peak_recorded");
    ASSERT_NEAR(pos.sl_price, 100.6, 0.01, "MaybeTrail_buy_sl_ratchets_to_100_6");
    ASSERT_NEAR(pos.trailing_atr_frozen, 1.0, 1e-9, "MaybeTrail_buy_atr_frozen");
}

//+------------------------------------------------------------------+
//| Orders_MaybeTrail — second call ratchets further, never widens.   |
//|                                                                   |
//| After first activation (peak=101.6, sl=100.6), feed another bar   |
//| with high=102.0. New peak=102.0, new_sl=102.0-1.0=101.0 → ratchet.|
//| Then feed a lower bar high=101.5: peak stays 102.0 (max),         |
//| computed new_sl=102.0-1.0=101.0 → keeps SL at 101.0 (no widen).   |
//+------------------------------------------------------------------+
void TestMaybeTrailNeverWidens_Buy() {
    PositionState pos;
    pos.symbol                       = "EURUSD";
    pos.direction                    = DIR_BUY;
    pos.entry_price                  = 100.0;
    pos.sl_price                     = 99.0;
    pos.tp_price                     = 105.0;
    pos.trailing_active              = false;
    pos.trailing_atr_frozen          = EMPTY_VALUE;
    pos.peak_price_since_activation  = EMPTY_VALUE;

    // Activate at 1.5R
    Orders_MaybeTrail(pos, 101.6, 100.8, 1.0, true,
                      CFG_TRAILING_ACTIVATION_R,
                      CFG_TRAILING_DISTANCE_ATR_MULTIPLE);
    // Ratchet up
    Orders_MaybeTrail(pos, 102.0, 101.5, 1.0, true,
                      CFG_TRAILING_ACTIVATION_R,
                      CFG_TRAILING_DISTANCE_ATR_MULTIPLE);
    ASSERT_NEAR(pos.sl_price, 101.0, 0.01, "MaybeTrail_buy_ratchets_to_101");

    // Lower bar — peak unchanged; new_sl computed = 101.0 (same) → no widen.
    double old_sl = pos.sl_price;
    Orders_MaybeTrail(pos, 101.5, 100.9, 1.0, true,
                      CFG_TRAILING_ACTIVATION_R,
                      CFG_TRAILING_DISTANCE_ATR_MULTIPLE);
    ASSERT_TRUE(pos.sl_price >= old_sl,
                "MaybeTrail_buy_lower_bar_does_not_widen_sl");
    ASSERT_NEAR(pos.peak_price_since_activation, 102.0, 1e-9,
                "MaybeTrail_buy_peak_stays_at_max");
}

void OnStart() {
    TestComputeSLBullishBelowLow();
    TestComputeSLBearishAboveHigh();
    TestComputeSLNaturalWickWiderThanMin();
    TestDealIsCloseEntryInvalidReturnsFalse();
    TestDetectFillingModeReturnsValid();
    TestMaybePartialDisabledReturnsFalse();
    TestMaybePartialFiresAt1R_Buy();
    TestMaybePartialAlreadyTaken();
    TestMaybePartialFiresAt1R_Sell();
    TestMaybeTrailDisabledNoActivation();
    TestMaybeTrailActivatesAt1_5R_Buy();
    TestMaybeTrailNeverWidens_Buy();
    Print("test_pac_orders: scenarios complete");
}
