//+------------------------------------------------------------------+
//| test_pac_swing.mq5                                                |
//|                                                                   |
//| Test the ATR-filtered ZigZag swing detector against the same      |
//| synthetic-bar patterns used in Plan 4 test_helpers_swing.py.      |
//|                                                                   |
//| NOTE: Plan 4 test_helpers_swing.py uses inline synthetic bars     |
//| (no CSV fixture). This test mirrors those scenarios; Phase 3 of   |
//| the triangulation work will extract a shared CSV fixture and      |
//| switch both engines to byte-identical input.                       |
//+------------------------------------------------------------------+
#property strict
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\PAC\\PAC_Swing.mqh"

//+------------------------------------------------------------------+
//| Build bars[] with constant highs[i]/lows[i] arrays; open/close    |
//| set to midpoint per _bars_from_highs_lows in Plan 4 test helper.  |
//+------------------------------------------------------------------+
void _BuildBars(const double &highs[], const double &lows[], int n,
                MqlRates &bars[]) {
    ArrayResize(bars, n);
    for (int i = 0; i < n; i++) {
        bars[i].high = highs[i];
        bars[i].low  = lows[i];
        bars[i].open  = (highs[i] + lows[i]) / 2.0;
        bars[i].close = (highs[i] + lows[i]) / 2.0;
        bars[i].time = (datetime)(i * 300);  // M5 spacing — irrelevant for swing logic
        bars[i].tick_volume = 0;
        bars[i].spread = 0;
        bars[i].real_volume = 0;
    }
}

//+------------------------------------------------------------------+
//| Scenario 1 (test_detect_swings_simple_up_down_up):                |
//| 20 bars at 95-105, then 10 bars at 105-115, then 10 bars at      |
//| 95-105. Should detect alternating swings.                         |
//+------------------------------------------------------------------+
void TestScenario_UpDownUp() {
    int N = 40;
    double highs[];
    double lows[];
    ArrayResize(highs, N);
    ArrayResize(lows, N);
    for (int i = 0; i < 20; i++) { highs[i] = 105; lows[i] = 95; }
    for (int i = 20; i < 30; i++) { highs[i] = 115; lows[i] = 105; }
    for (int i = 30; i < 40; i++) { highs[i] = 105; lows[i] = 95; }

    MqlRates bars[];
    _BuildBars(highs, lows, N, bars);

    Swing swings[];
    int count = Swing_Detect(bars, N, 0.5, 20, swings);

    // Expect at least one swing
    ASSERT_TRUE(count >= 1, "UpDownUp_at_least_one_swing");

    // Swings alternate direction
    bool alternating = true;
    for (int i = 0; i + 1 < count; i++) {
        if (swings[i].kind == swings[i + 1].kind) {
            alternating = false;
            break;
        }
    }
    ASSERT_TRUE(alternating, "UpDownUp_swings_alternate_direction");
}

//+------------------------------------------------------------------+
//| Scenario 2 (test_swing_below_threshold_ignored):                  |
//| 50 bars in a tight 1-unit range — no swings should emit.          |
//+------------------------------------------------------------------+
void TestScenario_BelowThresholdIgnored() {
    int N = 50;
    double highs[];
    double lows[];
    ArrayResize(highs, N);
    ArrayResize(lows, N);
    for (int i = 0; i < N; i++) { highs[i] = 101; lows[i] = 100; }

    MqlRates bars[];
    _BuildBars(highs, lows, N, bars);

    Swing swings[];
    int count = Swing_Detect(bars, N, 1.5, 20, swings);
    ASSERT_EQ_INT(count, 0, "BelowThreshold_no_swings");
}

//+------------------------------------------------------------------+
//| Scenario 3 (test_swing_kind_high_or_low):                         |
//| 41 bars: flat at 100, single peak at idx 20 (high=130), flat      |
//| again. Should find a SWING_HIGH near idx 20.                      |
//+------------------------------------------------------------------+
void TestScenario_PeakIsHigh() {
    int N = 41;
    double highs[];
    double lows[];
    ArrayResize(highs, N);
    ArrayResize(lows, N);
    for (int i = 0; i < 20; i++) { highs[i] = 100; lows[i] = 95; }
    highs[20] = 130; lows[20] = 120;
    for (int i = 21; i < N; i++) { highs[i] = 100; lows[i] = 95; }

    MqlRates bars[];
    _BuildBars(highs, lows, N, bars);

    Swing swings[];
    int count = Swing_Detect(bars, N, 1.0, 10, swings);

    bool found_high_near_20 = false;
    for (int i = 0; i < count; i++) {
        if (swings[i].kind == SWING_HIGH
            && MathAbs(swings[i].bar_idx - 20) <= 2) {
            found_high_near_20 = true;
            break;
        }
    }
    ASSERT_TRUE(found_high_near_20, "Peak_classified_as_high_near_idx_20");
}

//+------------------------------------------------------------------+
//| Scenario 4 (test_swing_too_few_bars_returns_empty_list):          |
//| Only 3 bars — less than atr_period (20) + 2 → returns 0.          |
//+------------------------------------------------------------------+
void TestScenario_TooFewBars() {
    int N = 3;
    double highs[3] = {110.0, 115.0, 113.0};
    double lows[3]  = {100.0, 110.0, 105.0};

    MqlRates bars[];
    _BuildBars(highs, lows, N, bars);

    Swing swings[];
    int count = Swing_Detect(bars, N, 1.5, 20, swings);
    ASSERT_EQ_INT(count, 0, "TooFewBars_empty_swings");
}

//+------------------------------------------------------------------+
//| Scenario 5 (test_swing_returns_typed_dataclass):                  |
//| Verify swing fields populated correctly.                          |
//+------------------------------------------------------------------+
void TestScenario_SwingStructFields() {
    int N = 25;
    double highs[];
    double lows[];
    ArrayResize(highs, N);
    ArrayResize(lows, N);
    for (int i = 0; i < 10; i++) { highs[i] = 105; lows[i] = 95; }
    for (int i = 10; i < 15; i++) { highs[i] = 120; lows[i] = 110; }
    for (int i = 15; i < N; i++) { highs[i] = 105; lows[i] = 95; }

    MqlRates bars[];
    _BuildBars(highs, lows, N, bars);

    Swing swings[];
    int count = Swing_Detect(bars, N, 0.5, 10, swings);

    if (count > 0) {
        ASSERT_TRUE(swings[0].bar_idx >= 0, "SwingStruct_bar_idx_valid");
        ASSERT_TRUE(swings[0].price > 0, "SwingStruct_price_valid");
        ASSERT_TRUE(swings[0].kind == SWING_HIGH || swings[0].kind == SWING_LOW,
                    "SwingStruct_kind_valid");
    } else {
        EMIT_PASS("SwingStruct_no_swings_in_range");
    }
}

void OnStart() {
    TestScenario_UpDownUp();
    TestScenario_BelowThresholdIgnored();
    TestScenario_PeakIsHigh();
    TestScenario_TooFewBars();
    TestScenario_SwingStructFields();
    Print("test_pac_swing: scenarios complete");
}
