//+------------------------------------------------------------------+
//| test_pac_targets.mq5                                              |
//|                                                                   |
//| Mirrors hedgehog/proposer/pac/tests/test_targets.py scenarios     |
//| against the MQL5 port in PAC_Targets.mqh. Expected outputs are    |
//| anchored to the same numeric assertions Python pytest verifies.   |
//+------------------------------------------------------------------+
#property strict
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\PAC\\PAC_Targets.mqh"

//+------------------------------------------------------------------+
//| Construct a MeasuredMove inline for the dataclass tests.          |
//+------------------------------------------------------------------+
MeasuredMove _MakeBullMM() {
    MeasuredMove mm;
    mm.id = 1;
    mm.direction = "bull";
    mm.a_bar = 10;   mm.a_price = 100.0;
    mm.b_bar = 20;   mm.b_price = 110.0;
    mm.c_bar = 25;   mm.c_price = 104.0;
    mm.d_target = 114.0;
    mm.validity = "valid";
    mm.overshoot_bars = 0;
    return mm;
}

//+------------------------------------------------------------------+
//| Anchor: test_measured_move_dataclass_fields                       |
//+------------------------------------------------------------------+
void TestMeasuredMoveFields() {
    MeasuredMove mm = _MakeBullMM();
    ASSERT_EQ_INT(mm.id, 1, "MMFields_id_is_1");
    ASSERT_STR_EQ(mm.direction, "bull", "MMFields_direction_is_bull");
    ASSERT_EQ_INT(mm.overshoot_bars, 0, "MMFields_overshoot_default_0");
}

//+------------------------------------------------------------------+
//| Anchor: test_fibonacci_levels_bull_mm                             |
//| AB span = 10 → retracement at 0.382=103.82, 0.5=105.0, 0.618=106.18|
//+------------------------------------------------------------------+
void TestFibLevelsBullMM() {
    MeasuredMove mm = _MakeBullMM();
    MeasuredMove mms[1];
    mms[0] = mm;

    double ratios_R[3] = {0.382, 0.5, 0.618};
    double ratios_E[3] = {1.382, 1.618, 2.618};

    FibLevel out[];
    int n = Targets_FibLevels(mms, 1, ratios_R, 3, ratios_E, 3, out);

    ASSERT_EQ_INT(n, 6, "FibLevels_total_count_is_6");

    // Find the 3 retracement prices anywhere in output.
    bool found_R_382  = false;
    bool found_R_500  = false;
    bool found_R_618  = false;
    bool found_E_1382 = false;

    for (int i = 0; i < n; i++) {
        if (MathAbs(out[i].price - 103.82) < 0.01) found_R_382 = true;
        if (MathAbs(out[i].price - 105.00) < 0.01) found_R_500 = true;
        if (MathAbs(out[i].price - 106.18) < 0.01) found_R_618 = true;
        if (MathAbs(out[i].price - 113.82) < 0.01) found_E_1382 = true;
    }
    ASSERT_TRUE(found_R_382,  "FibLevels_0382_price_103_82");
    ASSERT_TRUE(found_R_500,  "FibLevels_0500_price_105_00");
    ASSERT_TRUE(found_R_618,  "FibLevels_0618_price_106_18");
    ASSERT_TRUE(found_E_1382, "FibLevels_1382_price_113_82");

    // Verify labels mirror Python "fib_R_<ratio>" / "fib_E_<ratio>".
    bool label_R_382_seen = false;
    bool label_E_1382_seen = false;
    for (int i = 0; i < n; i++) {
        if (out[i].label == "fib_R_0.382")  label_R_382_seen = true;
        if (out[i].label == "fib_E_1.382")  label_E_1382_seen = true;
    }
    ASSERT_TRUE(label_R_382_seen,  "FibLevels_label_fib_R_0_382");
    ASSERT_TRUE(label_E_1382_seen, "FibLevels_label_fib_E_1_382");
}

//+------------------------------------------------------------------+
//| Anchor: test_fibonacci_levels_no_active_mms                       |
//+------------------------------------------------------------------+
void TestFibLevelsNoMMs() {
    MeasuredMove mms[];
    double ratios_R[3] = {0.382, 0.5, 0.618};
    double ratios_E[3] = {1.382, 1.618, 2.618};

    FibLevel out[];
    int n = Targets_FibLevels(mms, 0, ratios_R, 3, ratios_E, 3, out);
    ASSERT_EQ_INT(n, 0, "FibLevels_empty_mms_returns_0");
}

//+------------------------------------------------------------------+
//| Anchor: test_find_clusters_groups_nearby_levels                   |
//| Levels [100.0, 100.2, 105.0], ATR=10, threshold=3.                |
//| → 100.0 & 100.2 cluster (mean 100.1), 105.0 alone (dropped).      |
//+------------------------------------------------------------------+
void TestFindClustersGroupsNearby() {
    FibLevel levels[3];
    levels[0].price = 100.0; levels[0].label = "fib_R_0.5";
    levels[1].price = 100.2; levels[1].label = "fib_R_0.618";
    levels[2].price = 105.0; levels[2].label = "fib_E_1.382";

    Cluster out[];
    int n = Targets_FindClusters(levels, 3, 10.0, 0.3, 2, out);

    ASSERT_EQ_INT(n, 1, "FindClusters_one_cluster_emitted");
    ASSERT_NEAR(out[0].price, 100.1, 0.01, "FindClusters_price_is_100_1");
    ASSERT_EQ_INT(out[0].member_count, 2, "FindClusters_two_members");
}

//+------------------------------------------------------------------+
//| Anchor: test_find_clusters_below_min_members_no_cluster           |
//+------------------------------------------------------------------+
void TestFindClustersBelowMin() {
    FibLevel levels[1];
    levels[0].price = 100.0;
    levels[0].label = "fib_R_0.5";

    Cluster out[];
    int n = Targets_FindClusters(levels, 1, 10.0, 0.3, 2, out);
    ASSERT_EQ_INT(n, 0, "FindClusters_below_min_no_cluster");
}

//+------------------------------------------------------------------+
//| Anchor: test_extended_mm_target_returns_none_before_overshoot     |
//+------------------------------------------------------------------+
void TestExtendedMMBelowOvershoot() {
    MeasuredMove mm = _MakeBullMM();
    mm.overshoot_bars = 0;
    double target = Targets_ExtendedMM(mm, 3);
    ASSERT_TRUE(target == EMPTY_VALUE, "ExtendedMM_empty_when_below_overshoot");
}

//+------------------------------------------------------------------+
//| Anchor: test_extended_mm_target_returns_138_after_overshoot       |
//| 1.382 × 10 + 104 = 117.82                                         |
//+------------------------------------------------------------------+
void TestExtendedMMTriggered() {
    MeasuredMove mm = _MakeBullMM();
    mm.overshoot_bars = 5;
    double target = Targets_ExtendedMM(mm, 3);
    ASSERT_NEAR(target, 117.82, 0.01, "ExtendedMM_bull_target_117_82");
}

//+------------------------------------------------------------------+
//| Bear ExtendedMM symmetry check (not in Python but mirror logic).  |
//| Bear MM A=110, B=100, C=106, ab=10 → 106 - 1.382*10 = 92.18       |
//+------------------------------------------------------------------+
void TestExtendedMMBear() {
    MeasuredMove mm;
    mm.id = 1;
    mm.direction = "bear";
    mm.a_bar = 10;  mm.a_price = 110.0;
    mm.b_bar = 20;  mm.b_price = 100.0;
    mm.c_bar = 25;  mm.c_price = 106.0;
    mm.d_target = 96.0;
    mm.validity = "valid";
    mm.overshoot_bars = 5;
    double target = Targets_ExtendedMM(mm, 3);
    ASSERT_NEAR(target, 92.18, 0.01, "ExtendedMM_bear_target_92_18");
}

//+------------------------------------------------------------------+
//| Anchor: test_apply_settle_buffer_bull_pulls_target_down           |
//| 100 - 0.5*10 = 95                                                 |
//+------------------------------------------------------------------+
void TestSettleBufferBull() {
    double out = Targets_ApplySettle(100.0, "bull", 10.0, 0.5);
    ASSERT_NEAR(out, 95.0, 1e-9, "SettleBuffer_bull_target_95");
}

//+------------------------------------------------------------------+
//| Anchor: test_apply_settle_buffer_bear_pushes_target_up            |
//| 100 + 0.5*10 = 105                                                |
//+------------------------------------------------------------------+
void TestSettleBufferBear() {
    double out = Targets_ApplySettle(100.0, "bear", 10.0, 0.5);
    ASSERT_NEAR(out, 105.0, 1e-9, "SettleBuffer_bear_target_105");
}

//+------------------------------------------------------------------+
//| Anchor: test_detect_measured_moves_empty_swings                   |
//+------------------------------------------------------------------+
void TestDetectMMsEmptySwings() {
    MqlRates bars[1];
    bars[0].high = 101.0; bars[0].low = 99.0; bars[0].open = 100.0; bars[0].close = 100.0;

    Swing swings[];
    double ema[1] = {100.0};
    MeasuredMove out[];
    int n = Targets_DetectMeasuredMoves(bars, 1, swings, 0, ema, 1, 1.5, 5, 20, out);
    ASSERT_EQ_INT(n, 0, "DetectMMs_empty_swings_returns_0");
}

//+------------------------------------------------------------------+
//| Anchor: test_detect_measured_moves_bull_pattern                   |
//| Construct ~100 bars + 3 pre-built swings; expect ≥1 bull MM with  |
//| d_target = 105 + (116-94) = 127.                                  |
//+------------------------------------------------------------------+
void TestDetectMMsBullPattern() {
    int N = 100;
    MqlRates bars[];
    ArrayResize(bars, N);
    double closes[];
    ArrayResize(closes, N);
    for (int i = 0; i < 30; i++) closes[i] = 95.0;
    for (int i = 0; i < 40; i++) closes[30 + i] = 95.0 + 0.5 * i;
    for (int i = 0; i < 20; i++) closes[70 + i] = 115.0 - 0.5 * i;
    for (int i = 0; i < 10; i++) closes[90 + i] = 105.0;

    for (int i = 0; i < N; i++) {
        bars[i].open  = closes[i];
        bars[i].high  = closes[i] + 1.0;
        bars[i].low   = closes[i] - 1.0;
        bars[i].close = closes[i];
        bars[i].time  = (datetime)(i * 300);
    }

    // Compute EMA(21) on closes — same formula as pandas ewm(span=21,adjust=False).
    // alpha = 2/(span+1) = 2/22 = 0.0909...
    double ema[];
    ArrayResize(ema, N);
    double alpha = 2.0 / 22.0;
    ema[0] = closes[0];
    for (int i = 1; i < N; i++) {
        ema[i] = alpha * closes[i] + (1.0 - alpha) * ema[i - 1];
    }

    // Pre-built swings: low at 29 (94.0), high at 69 (116.0), low at 79 (105.0).
    Swing swings[3];
    swings[0].bar_idx = 29; swings[0].price = 94.0;  swings[0].kind = SWING_LOW;
    swings[1].bar_idx = 69; swings[1].price = 116.0; swings[1].kind = SWING_HIGH;
    swings[2].bar_idx = 79; swings[2].price = 105.0; swings[2].kind = SWING_LOW;

    MeasuredMove out[];
    int n = Targets_DetectMeasuredMoves(bars, N, swings, 3, ema, N, 1.5, 5, 20, out);

    // Expect at least one bull MM; Python test asserts >= 1.
    ASSERT_TRUE(n >= 1, "DetectMMs_bull_at_least_one");
    if (n >= 1) {
        ASSERT_STR_EQ(out[0].direction, "bull", "DetectMMs_bull_direction");
        // d_target = c + (b - a) = 105 + 22 = 127
        ASSERT_NEAR(out[0].d_target, 127.0, 0.01, "DetectMMs_bull_d_target_127");
        ASSERT_EQ_INT(out[0].a_bar, 29, "DetectMMs_bull_a_bar_29");
        ASSERT_EQ_INT(out[0].b_bar, 69, "DetectMMs_bull_b_bar_69");
        ASSERT_EQ_INT(out[0].c_bar, 79, "DetectMMs_bull_c_bar_79");
        ASSERT_STR_EQ(out[0].validity, "valid", "DetectMMs_bull_validity_valid");
    }
}

void OnStart() {
    TestMeasuredMoveFields();
    TestFibLevelsBullMM();
    TestFibLevelsNoMMs();
    TestFindClustersGroupsNearby();
    TestFindClustersBelowMin();
    TestExtendedMMBelowOvershoot();
    TestExtendedMMTriggered();
    TestExtendedMMBear();
    TestSettleBufferBull();
    TestSettleBufferBear();
    TestDetectMMsEmptySwings();
    TestDetectMMsBullPattern();
    Print("test_pac_targets: scenarios complete");
}
