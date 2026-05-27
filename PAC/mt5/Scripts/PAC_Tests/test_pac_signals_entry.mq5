//+------------------------------------------------------------------+
//| test_pac_signals_entry.mq5                                        |
//|                                                                   |
//| Verifies PAC_Signals.mqh §4 entry-trigger pure functions —        |
//| matches semantics of hedgehog/proposer/pac/signals.py            |
//| detect_signal_candle / passes_ema_side_rule / has_confluence.     |
//+------------------------------------------------------------------+
#property strict
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\PAC\\PAC_Signals.mqh"

void OnStart() {
    //--- §4.1 DetectSignalCandle ----------------------------------------
    // Bullish signal: long lower wick, close in upper third
    //   OHLC: open 1.0820, high 1.0825, low 1.0800, close 1.0823
    //   body = 0.0003, range = 0.0025
    //   lower_wick = 0.0020, upper_wick = 0.0002
    //   wick_body_ratio_min=2.0 → 0.0020 >= 2*0.0003=0.0006 ✓
    //   close_position_pct=33.0 → upper-third floor = lo + 0.67*range = 1.0816750
    //   close (1.0823) >= 1.0816750 ✓ → bullish
    string r1 = Signals_DetectSignalCandle(1.0820, 1.0825, 1.0800, 1.0823,
                                           0.0020, 2.0, 0.5, 33.0);
    ASSERT_STR_EQ(r1, "bullish", "Detect_bullish_signal_candle");

    // Bearish signal: long upper wick, close in lower third
    //   OHLC: open 1.0822, high 1.0840, low 1.0820, close 1.0825
    //   body = 0.0003, range = 0.0020
    //   upper_wick = 0.0015 >= 2*0.0003=0.0006 ✓
    //   lower-third ceil = lo + 0.33*range = 1.0820 + 0.00066 = 1.08266
    //   close (1.0825) <= 1.08266 ✓ → bearish
    string r2 = Signals_DetectSignalCandle(1.0822, 1.0840, 1.0820, 1.0825,
                                           0.0020, 2.0, 0.5, 33.0);
    ASSERT_STR_EQ(r2, "bearish", "Detect_bearish_signal_candle");

    // Doji rejected (body == 0)
    string r3 = Signals_DetectSignalCandle(1.0820, 1.0825, 1.0815, 1.0820,
                                           0.0010, 2.0, 0.5, 33.0);
    ASSERT_STR_EQ(r3, "none", "Doji_rejected");

    // Range below ATR threshold
    //   range = 0.0013, threshold = 0.5*0.0030 = 0.0015 → none
    string r4 = Signals_DetectSignalCandle(1.0820, 1.0823, 1.0810, 1.0822,
                                           0.0030, 2.0, 0.5, 33.0);
    ASSERT_STR_EQ(r4, "none", "Range_below_atr_threshold");

    // Long lower wick but close NOT in upper third → none
    //   OHLC: 1.0810, 1.0825, 1.0800, 1.0815
    //   body=0.0005, lower_wick=0.0010 (>= 2*0.0005=0.0010), upper_wick=0.0010
    //   upper-third floor = 1.0816750; close 1.0815 < floor → bullish fails
    //   lower-third ceil = 1.08083; close 1.0815 > ceil → bearish fails
    string r5 = Signals_DetectSignalCandle(1.0810, 1.0825, 1.0800, 1.0815,
                                           0.0020, 2.0, 0.5, 33.0);
    ASSERT_STR_EQ(r5, "none", "Lower_wick_OK_close_not_in_upper_third");

    //--- §4.2 PassesEMASide ---------------------------------------------
    ASSERT_TRUE (Signals_PassesEMASide("bullish", 1.0823, 1.0815),
                 "EMA_side_bullish_above");
    ASSERT_FALSE(Signals_PassesEMASide("bullish", 1.0810, 1.0815),
                 "EMA_side_bullish_below_FAIL");
    ASSERT_TRUE (Signals_PassesEMASide("bearish", 1.0810, 1.0815),
                 "EMA_side_bearish_below");
    ASSERT_FALSE(Signals_PassesEMASide("bearish", 1.0820, 1.0815),
                 "EMA_side_bearish_above_FAIL");
    ASSERT_FALSE(Signals_PassesEMASide("none", 1.0820, 1.0815),
                 "EMA_side_none_kind_FAIL");
    // EMPTY_VALUE EMA (insufficient warmup) → always false
    ASSERT_FALSE(Signals_PassesEMASide("bullish", 1.0820, EMPTY_VALUE),
                 "EMA_side_empty_value_FAIL");

    //--- §4.3 HasConfluence ---------------------------------------------
    double levels[2]; levels[0] = 1.0795; levels[1] = 1.0820;
    string types[2];  types[0]  = "mm";    types[1]  = "fib";

    double matched_lvl = 0.0;
    string matched_typ = "";

    // wick_extreme 1.0800, threshold 0.0005
    //   |1.0800-1.0795|=0.0005 (== threshold qualifies)
    //   |1.0800-1.0820|=0.0020 (out of range)
    //   → best = index 0, type "mm"
    bool hit = Signals_HasConfluence(1.0800, levels, types, 0.0005,
                                     matched_lvl, matched_typ);
    ASSERT_TRUE(hit, "Confluence_within_threshold_hit");
    ASSERT_NEAR(matched_lvl, 1.0795, 1e-9, "Confluence_matched_level_price");
    ASSERT_STR_EQ(matched_typ, "mm", "Confluence_matched_level_type");

    // wick_extreme 1.0750, threshold 0.0005 → both levels too far
    matched_lvl = 0.0; matched_typ = "";
    bool miss = Signals_HasConfluence(1.0750, levels, types, 0.0005,
                                      matched_lvl, matched_typ);
    ASSERT_FALSE(miss, "Confluence_outside_threshold_miss");
    ASSERT_STR_EQ(matched_typ, "", "Confluence_miss_clears_type");

    // Empty levels array → false
    double empty_lvls[];
    string empty_typs[];
    matched_lvl = 0.0; matched_typ = "";
    bool e_miss = Signals_HasConfluence(1.0800, empty_lvls, empty_typs, 0.0005,
                                        matched_lvl, matched_typ);
    ASSERT_FALSE(e_miss, "Confluence_empty_levels_miss");

    // Closer level wins among multiple in-range
    double levels2[3];
    levels2[0] = 1.0795;  // dist 0.0005
    levels2[1] = 1.0801;  // dist 0.0001 ← closest
    levels2[2] = 1.0804;  // dist 0.0004
    string types2[3];
    types2[0] = "mm"; types2[1] = "fib"; types2[2] = "cluster";
    matched_lvl = 0.0; matched_typ = "";
    bool closest = Signals_HasConfluence(1.0800, levels2, types2, 0.0010,
                                         matched_lvl, matched_typ);
    ASSERT_TRUE(closest, "Confluence_picks_closest_hit");
    ASSERT_NEAR(matched_lvl, 1.0801, 1e-9, "Confluence_closest_level_picked");
    ASSERT_STR_EQ(matched_typ, "fib", "Confluence_closest_type_picked");
}
