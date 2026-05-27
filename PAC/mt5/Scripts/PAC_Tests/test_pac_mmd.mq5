//+------------------------------------------------------------------+
//| test_pac_mmd.mq5                                                  |
//|                                                                   |
//| Tier 1: ClassifyAlignmentSimple math — mirrors the pytest cases   |
//| in hedgehog/proposer/pac/tests/test_mmd.py to keep MQL5 behaviour |
//| byte-equivalent to the Python reference.                          |
//|                                                                   |
//| Tier 2: iCustom load + buffer read on a EURUSD M5 chart.          |
//+------------------------------------------------------------------+
#property strict
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\PAC\\PAC_MMD.mqh"

void OnStart() {
    //------------------------------------------------------------------
    // Tier 1: pure classifier — mirror mmd.py test cases line-for-line.
    //------------------------------------------------------------------

    // test_classify_alignment_confirmed_bull
    //   Orange(1050) > Blue(1040) > Green(1030), sentiment=bull → confirmed
    string r_confirmed_bull = ClassifyAlignmentSimple(1050.0, 1040.0, 1030.0, "bull");
    ASSERT_STR_EQ(r_confirmed_bull, "confirmed", "Classify_confirmed_bull");

    // test_classify_alignment_confirmed_bear
    //   Green(1050) > Blue(1040) > Orange(1030), sentiment=bear → confirmed
    string r_confirmed_bear = ClassifyAlignmentSimple(1030.0, 1040.0, 1050.0, "bear");
    ASSERT_STR_EQ(r_confirmed_bear, "confirmed", "Classify_confirmed_bear");

    // test_classify_alignment_vetoed_when_fully_opposite
    //   Orange(1030) < Blue(1040) < Green(1050) (full bear) but sentiment=bull → vetoed
    string r_vetoed = ClassifyAlignmentSimple(1030.0, 1040.0, 1050.0, "bull");
    ASSERT_STR_EQ(r_vetoed, "vetoed", "Classify_vetoed_full_opposite");

    // Symmetric: full-bull stack but sentiment=bear → vetoed
    string r_vetoed_bear = ClassifyAlignmentSimple(1050.0, 1040.0, 1030.0, "bear");
    ASSERT_STR_EQ(r_vetoed_bear, "vetoed", "Classify_vetoed_bull_stack_bear_sentiment");

    // test_classify_alignment_weakened_when_partial
    //   Orange(1050), Blue(1030), Green(1040) — neither full_bull nor full_bear
    //   sentiment=bull → weakened
    string r_weakened = ClassifyAlignmentSimple(1050.0, 1030.0, 1040.0, "bull");
    ASSERT_STR_EQ(r_weakened, "weakened", "Classify_weakened_partial_stack");

    // test_classify_alignment_transitional_returns_weakened
    //   Even with a perfect bull stack, transitional sentiment → weakened (safe default)
    string r_transitional = ClassifyAlignmentSimple(1050.0, 1040.0, 1030.0, "transitional");
    ASSERT_STR_EQ(r_transitional, "weakened", "Classify_transitional_returns_weakened");

    // CloudMidpoints struct path — same canonical answer via the wrapper.
    CloudMidpoints mids;
    mids.orange_mid = 1050.0;
    mids.blue_mid   = 1040.0;
    mids.green_mid  = 1030.0;
    string r_struct = ClassifyAlignmentFromMidpoints(mids, "bull");
    ASSERT_STR_EQ(r_struct, "confirmed", "Classify_from_midpoints_struct");

    //------------------------------------------------------------------
    // Tier 2: iCustom load + buffer read (requires PAC_MMD_Clouds.ex5
    // installed under Indicators/PAC/ and a EURUSD M5 chart attached).
    //------------------------------------------------------------------
    if (InitMMD("EURUSD")) {
        EMIT_PASS("InitMMD_EURUSD");
        Sleep(500);

        CloudValues live;
        bool ok = ReadCloudValues(1, live);
        ASSERT_TRUE(ok, "ReadCloudValues_succeeds");
        // EMA-minus-SMA on EURUSD should be small (well under 1.0 in raw price units).
        ASSERT_TRUE(MathAbs(live.orange) < 1.0, "CloudValue_orange_sane");

        CloudMidpoints livemids;
        bool ok2 = ReadCloudMidpoints(1, livemids);
        ASSERT_TRUE(ok2, "ReadCloudMidpoints_succeeds");
        // EURUSD midpoint should be in a reasonable FX band (0.5..2.0).
        ASSERT_TRUE(livemids.orange_mid > 0.5 && livemids.orange_mid < 2.0,
                    "CloudMidpoint_orange_sane");

        // End-to-end live classifier — just check it returns one of the
        // three legal labels (no assumption about market state at test time).
        string live_align = ClassifyAlignmentLive(0.0, "bull", 1);
        bool legal = (live_align == "confirmed" || live_align == "weakened"
                   || live_align == "vetoed");
        ASSERT_TRUE(legal, "ClassifyAlignmentLive_returns_legal_label");

        ReleaseMMD();
    } else {
        EMIT_FAIL("InitMMD_EURUSD", "true", "false");
    }
}
