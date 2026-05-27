//+------------------------------------------------------------------+
//| PAC_Signals.mqh — §3 direction filter + §4 entry trigger          |
//|                                                                   |
//| Mirrors hedgehog/proposer/pac/signals.py line-for-line:           |
//|   §3.1 Signals_ClassifySentiment    — EMA21/SMA61 price-position  |
//|   §3.2 (MMD delegated to PAC_MMD.mqh ClassifyAlignmentSimple)     |
//|   §3.3 Signals_D1PromoZone          — prev D1 OHLC body/wick zone |
//|   §3.4 Signals_SessionBoxPosition   — session-high/low breakout   |
//|   §3.5 Signals_CompositeDirection   — composite gate (strict)     |
//|   §4.1 Signals_DetectSignalCandle   — wick/body candle classifier |
//|   §4.2 Signals_PassesEMASide        — EMA21 hard-side rule        |
//|   §4.3 Signals_HasConfluence        — wick-extreme vs level list  |
//|                                                                   |
//| Forward declaration: Signals_ComputeDirection and                 |
//| Signals_DetectEntryTrigger are end-to-end orchestrators whose     |
//| bodies need live iMA handles and arrays of active levels — they   |
//| are defined in PAC_EA.mq5 where those handles are wired during    |
//| OnInit. Declared here so call sites in setups / orders modules    |
//| compile against the canonical signatures.                         |
//+------------------------------------------------------------------+
#property strict

#include "PAC_MMD.mqh"
#include "PAC_TimeUtil.mqh"

//+------------------------------------------------------------------+
//| Direction enum — exported to setups/orders/logger.                |
//+------------------------------------------------------------------+
enum DirectionKind {
    DIR_NEUTRAL = 0,
    DIR_BUY     = 1,
    DIR_SELL    = -1
};

//+------------------------------------------------------------------+
//| §3.1 EMA21/SMA61 sentiment classifier                             |
//|                                                                   |
//| Returns "bull"  — close > EMA AND close > SMA                     |
//|         "bear"  — close < EMA AND close < SMA                     |
//|         "transitional" — close between the two MAs                |
//|                                                                   |
//| NaN handling: Python returns "transitional" if either MA is NaN.  |
//| In MQL5, callers pass EMPTY_VALUE (= DBL_MAX) when the iMA buffer |
//| is not yet populated; we treat that as transitional too.          |
//+------------------------------------------------------------------+
string Signals_ClassifySentiment(double close, double ema21, double sma61) {
    if (ema21 == EMPTY_VALUE || sma61 == EMPTY_VALUE) return "transitional";
    if (close > ema21 && close > sma61) return "bull";
    if (close < ema21 && close < sma61) return "bear";
    return "transitional";
}

//+------------------------------------------------------------------+
//| §3.3 D1 OHLC promo zone classifier                                |
//|                                                                   |
//| Python signature: d1_promo_zone(d1_bars: DataFrame, current_utc, |
//| current_price). Python looks up the *previous* D1 bar from the    |
//| frame. The MQL5 EA naturally has access to the previous D1 OHLC   |
//| via CopyRates(symbol, PERIOD_D1, 1, 1, ...) at the call site, so  |
//| this function takes the scalars directly — matches Python's       |
//| classification logic line-for-line, just with the prev-D1 lookup  |
//| hoisted to the caller.                                            |
//|                                                                   |
//| Python algorithm (mirrored exactly):                              |
//|   bearish D1 (prev_close < prev_open):                            |
//|     current > open  → bear_promo (sellers' defended upper wick)   |
//|     current < close → bull_promo (buyers' demand area lower wick) |
//|     else            → neutral (inside body)                       |
//|   bullish D1 (prev_close > prev_open):                            |
//|     current < open  → bull_promo (buyers' launch pad lower wick)  |
//|     current > close → bear_promo (resistance upper wick)          |
//|     else            → neutral (inside body)                       |
//|   doji (prev_close == prev_open):                                 |
//|     always neutral                                                |
//|                                                                   |
//| Unlike the plan sketch, no high/low clamping — matches Python.    |
//+------------------------------------------------------------------+
string Signals_D1PromoZone(double d1_open, double d1_high, double d1_low,
                           double d1_close, double current_price) {
    if (d1_close < d1_open) {
        // Bearish D1
        double body_top = d1_open;
        double body_bot = d1_close;
        if (current_price > body_top) return "bear_promo";
        if (current_price < body_bot) return "bull_promo";
        return "neutral";
    }
    if (d1_close > d1_open) {
        // Bullish D1
        double body_bot = d1_open;
        double body_top = d1_close;
        if (current_price < body_bot) return "bull_promo";
        if (current_price > body_top) return "bear_promo";
        return "neutral";
    }
    // Doji — no clear zone
    return "neutral";
}

//+------------------------------------------------------------------+
//| §3.4 Session box position classifier                              |
//|                                                                   |
//| Python signature also takes a DataFrame + session label + cfg +   |
//| atr_value and discovers session bars internally. The EA caller    |
//| computes session_high / session_low via PAC_TimeUtil session-     |
//| filter accumulation, so this function takes the already-computed  |
//| scalars. Box-range narrow filter (< 0.5*ATR → inside) mirrors     |
//| Python exactly.                                                   |
//|                                                                   |
//| min_box_atr_multiple is a config-supplied multiplier; Python uses |
//| a hard-coded 0.5. Caller passes cfg.session_box_min_atr_multiple  |
//| (or 0.5 by default) for parity.                                   |
//+------------------------------------------------------------------+
string Signals_SessionBoxPosition(double current_price, double session_high,
                                  double session_low, double atr_value,
                                  double min_box_atr_multiple) {
    double box_range = session_high - session_low;
    if (box_range < (min_box_atr_multiple * atr_value)) return "inside";
    if (current_price > session_high) return "above";
    if (current_price < session_low)  return "below";
    return "inside";
}

//+------------------------------------------------------------------+
//| §3.5 Composite direction rule (strict mode)                       |
//|                                                                   |
//| Mirrors signals.py composite_direction strict branch:             |
//|   bull iff sentiment=="bull" AND mmd_ok AND d1 in bull-permissive |
//|            set AND box_position != "inside"                       |
//|   bear iff sentiment=="bear" AND mmd_ok AND d1 in bear-permissive |
//|            set AND box_position != "inside"                       |
//|   neutral otherwise                                               |
//|                                                                   |
//| mmd_ok: in v1 (mmd_strict=False), mmd_alignment != "vetoed".      |
//| The cfg.mmd_strict path (require "confirmed") is deferred — when  |
//| Plan 5 Task 18 generates PAC_Config.mqh from the Python Config    |
//| dataclass it will surface a g_cfg.mmd_strict flag; until then,    |
//| caller passes strict_mode for the "direction_strict" toggle only. |
//|                                                                   |
//| Loose mode (strict_mode=false): sentiment alone decides direction.|
//+------------------------------------------------------------------+
DirectionKind Signals_CompositeDirection(
    string sentiment, string mmd_alignment, string d1_zone,
    string box_position, bool strict_mode
) {
    if (!strict_mode) {
        // Loose mode — only sentiment matters
        if (sentiment == "bull") return DIR_BUY;
        if (sentiment == "bear") return DIR_SELL;
        return DIR_NEUTRAL;
    }

    // Strict mode: MMD veto is a hard block
    bool mmd_ok = (mmd_alignment != "vetoed");
    if (!mmd_ok) return DIR_NEUTRAL;

    bool box_ok = (box_position != "inside");
    if (!box_ok) return DIR_NEUTRAL;

    if (sentiment == "bull"
        && (d1_zone == "bull_promo"
            || d1_zone == "first_touch_bull_promo"
            || d1_zone == "neutral"))
        return DIR_BUY;

    if (sentiment == "bear"
        && (d1_zone == "bear_promo"
            || d1_zone == "first_touch_bear_promo"
            || d1_zone == "neutral"))
        return DIR_SELL;

    return DIR_NEUTRAL;
}

//+------------------------------------------------------------------+
//| ComputeDirection — production end-to-end entry point. Body lives  |
//| in PAC_EA.mq5 where iMA handles and session-box state are wired.  |
//+------------------------------------------------------------------+
DirectionKind Signals_ComputeDirection(string symbol);
