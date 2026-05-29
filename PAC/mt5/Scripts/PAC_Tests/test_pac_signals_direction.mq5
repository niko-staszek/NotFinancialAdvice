//+------------------------------------------------------------------+
//| test_pac_signals_direction.mq5                                    |
//|                                                                   |
//| Verifies PAC_Signals.mqh §3 direction-filter pure functions —     |
//| matches semantics of hedgehog/proposer/pac/signals.py one-for-one.|
//| All cases here are stateless (no chart/handle deps), runnable     |
//| under MetaEditor's standalone script test runner.                 |
//+------------------------------------------------------------------+
#property strict
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\PAC\\PAC_Signals.mqh"

void OnStart() {
    //--- §3.1 Sentiment classifier --------------------------------------
    ASSERT_STR_EQ(Signals_ClassifySentiment(1.0850, 1.0820, 1.0810), "bull",
                  "Sentiment_close_above_both_bull");
    ASSERT_STR_EQ(Signals_ClassifySentiment(1.0800, 1.0820, 1.0810), "bear",
                  "Sentiment_close_below_both_bear");
    ASSERT_STR_EQ(Signals_ClassifySentiment(1.0815, 1.0820, 1.0810), "transitional",
                  "Sentiment_between_MAs_transitional");
    // EMPTY_VALUE MA → transitional (insufficient warmup, mirrors Python NaN)
    ASSERT_STR_EQ(Signals_ClassifySentiment(1.0850, EMPTY_VALUE, 1.0810), "transitional",
                  "Sentiment_empty_ema_transitional");

    //--- §3.3 D1 promo zone ---------------------------------------------
    // Bullish D1 (open 1.0780 < close 1.0815) — body_bot=1.0780, body_top=1.0815
    ASSERT_STR_EQ(Signals_D1PromoZone(1.0780, 1.0820, 1.0775, 1.0815, 1.0779), "bull_promo",
                  "D1_bullish_lower_wick_buyers_promo");
    ASSERT_STR_EQ(Signals_D1PromoZone(1.0780, 1.0820, 1.0775, 1.0815, 1.0819), "bear_promo",
                  "D1_bullish_upper_wick_sellers_promo");
    ASSERT_STR_EQ(Signals_D1PromoZone(1.0780, 1.0820, 1.0775, 1.0815, 1.0800), "neutral",
                  "D1_inside_body_neutral");
    // Bearish D1 (open 1.0815 > close 1.0780) — body_top=1.0815, body_bot=1.0780
    ASSERT_STR_EQ(Signals_D1PromoZone(1.0815, 1.0820, 1.0775, 1.0780, 1.0819), "bear_promo",
                  "D1_bearish_upper_wick_sellers_promo");
    ASSERT_STR_EQ(Signals_D1PromoZone(1.0815, 1.0820, 1.0775, 1.0780, 1.0779), "bull_promo",
                  "D1_bearish_lower_wick_buyers_promo");
    // Doji (close == open) → always neutral
    ASSERT_STR_EQ(Signals_D1PromoZone(1.0800, 1.0820, 1.0775, 1.0800, 1.0810), "neutral",
                  "D1_doji_always_neutral");

    //--- §3.4 Session box position --------------------------------------
    // box_range = 1.0850 - 1.0800 = 0.0050; atr=0.0020, multiplier=0.5 → threshold=0.0010
    // box_range > threshold → not narrow. Current 1.0860 > high → above
    ASSERT_STR_EQ(Signals_SessionBoxPosition(1.0860, 1.0850, 1.0800, 0.0020, 0.5), "above",
                  "SessionBox_break_above");
    ASSERT_STR_EQ(Signals_SessionBoxPosition(1.0790, 1.0850, 1.0800, 0.0020, 0.5), "below",
                  "SessionBox_break_below");
    ASSERT_STR_EQ(Signals_SessionBoxPosition(1.0830, 1.0850, 1.0800, 0.0020, 0.5), "inside",
                  "SessionBox_within_box_inside");
    // Narrow box: range 0.0005 < 0.5*0.0020 = 0.0010 → forced inside even on breakout
    ASSERT_STR_EQ(Signals_SessionBoxPosition(1.0860, 1.0805, 1.0800, 0.0020, 0.5), "inside",
                  "SessionBox_narrow_filter_forces_inside");

    //--- §3.5 Composite direction (strict mode) -------------------------
    DirectionKind d_bull = Signals_CompositeDirection(
        "bull", "confirmed", "bull_promo", "above", true);
    ASSERT_EQ_INT((int)d_bull, (int)DIR_BUY, "Composite_strict_all_bull_DIR_BUY");

    DirectionKind d_bull_neutral_d1 = Signals_CompositeDirection(
        "bull", "weakened", "neutral", "above", true);
    ASSERT_EQ_INT((int)d_bull_neutral_d1, (int)DIR_BUY,
                  "Composite_strict_bull_neutral_d1_DIR_BUY");

    DirectionKind d_bear = Signals_CompositeDirection(
        "bear", "confirmed", "bear_promo", "below", true);
    ASSERT_EQ_INT((int)d_bear, (int)DIR_SELL, "Composite_strict_all_bear_DIR_SELL");

    DirectionKind d_mmd_vetoed = Signals_CompositeDirection(
        "bull", "vetoed", "bull_promo", "above", true);
    ASSERT_EQ_INT((int)d_mmd_vetoed, (int)DIR_NEUTRAL, "Composite_mmd_vetoed_neutral");

    DirectionKind d_box_inside = Signals_CompositeDirection(
        "bull", "confirmed", "bull_promo", "inside", true);
    ASSERT_EQ_INT((int)d_box_inside, (int)DIR_NEUTRAL, "Composite_box_inside_neutral");

    DirectionKind d_wrong_d1 = Signals_CompositeDirection(
        "bull", "confirmed", "bear_promo", "above", true);
    ASSERT_EQ_INT((int)d_wrong_d1, (int)DIR_NEUTRAL, "Composite_bull_sentiment_bear_d1_neutral");

    DirectionKind d_transitional = Signals_CompositeDirection(
        "transitional", "confirmed", "neutral", "above", true);
    ASSERT_EQ_INT((int)d_transitional, (int)DIR_NEUTRAL,
                  "Composite_transitional_sentiment_neutral");

    //--- §3.5 Composite direction (loose mode) --------------------------
    DirectionKind d_loose_bull = Signals_CompositeDirection(
        "bull", "vetoed", "bear_promo", "inside", false);
    ASSERT_EQ_INT((int)d_loose_bull, (int)DIR_BUY,
                  "Composite_loose_sentiment_bull_overrides_DIR_BUY");
    DirectionKind d_loose_transitional = Signals_CompositeDirection(
        "transitional", "confirmed", "neutral", "above", false);
    ASSERT_EQ_INT((int)d_loose_transitional, (int)DIR_NEUTRAL,
                  "Composite_loose_transitional_neutral");
}
