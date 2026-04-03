//+------------------------------------------------------------------+
//| CBS_SL.mqh v1.0                                                  |
//| Stop loss calculation: Tier (forex adaptive) + Fixed ratios      |
//|                                                                  |
//| Matches Python 18_best_targets.py L476-483:                      |
//|   if fc.sl_ratio_fixed > 0:                                      |
//|       sl_ratio = fc.sl_ratio_fixed                               |
//|   elif tier_mode == "forex":                                     |
//|       sl_ratio = 3.0 if dist<=35 else (1.5 if dist<=100 else 1) |
//|   else:                                                          |
//|       sl_ratio = 1.0                                             |
//|   sl_pips = dist * sl_ratio                                      |
//+------------------------------------------------------------------+
#ifndef CBS_SL_MQH
#define CBS_SL_MQH

//+------------------------------------------------------------------+
//| Get SL ratio multiplier for the given mode and distance           |
//|                                                                   |
//| mode      : SL_TIER, SL_1_1, SL_1_1_5, SL_1_2                  |
//| dist_pips : distance from entry to target in pips                |
//| is_forex  : true for forex tier logic, false for standard        |
//|                                                                   |
//| Returns: multiplier (SL distance = target distance * ratio)      |
//+------------------------------------------------------------------+
double GetSLRatio(ENUM_SL_MODE mode, double dist_pips, bool is_forex)
{
   switch(mode)
   {
      case SL_1_1:   return 1.0;
      case SL_1_1_5: return 1.5;
      case SL_1_2:   return 2.0;

      case SL_TIER:
      default:
         if(is_forex)
         {
            // Per strategy.md and EA_PARAMETERS_REFERENCE.md L107-112:
            // Tier A: dist <= 35 pips -> 3.0x
            // Tier B: 35 < dist <= 100 pips -> 1.5x
            // Tier C: dist > 100 pips -> 1.0x
            if(dist_pips <= 35.0)       return 3.0;
            else if(dist_pips <= 100.0) return 1.5;
            else                        return 1.0;
         }
         else
         {
            // Standard (non-forex): always 1.0x
            // Per EA_PARAMETERS_REFERENCE.md L114
            return 1.0;
         }
   }
}

//+------------------------------------------------------------------+
//| Compute SL price given entry, target, direction, and mode         |
//|                                                                   |
//| entry     : actual entry price (ASK for BUY, BID for SELL)       |
//| target    : CBS target price (H + L - O)                         |
//| dir       : ORDER_TYPE_BUY or ORDER_TYPE_SELL                    |
//| mode      : SL mode from config                                  |
//| pip_size  : instrument pip size (e.g. 0.0001 for EURUSD)         |
//| is_forex  : true = forex tier mode                                |
//|                                                                   |
//| Returns: SL price level                                           |
//+------------------------------------------------------------------+
double ComputeSL(double entry, double target, ENUM_ORDER_TYPE dir,
                 ENUM_SL_MODE mode, double pip_size, bool is_forex)
{
   // Distance from entry to target in pips
   double dist       = MathAbs(target - entry);
   double dist_pips  = dist / pip_size;

   // Get SL ratio multiplier
   double sl_ratio   = GetSLRatio(mode, dist_pips, is_forex);

   // SL distance in price
   double sl_dist    = dist * sl_ratio;

   // Place SL on opposite side of entry from target
   double sl_price;
   if(dir == ORDER_TYPE_BUY)
      sl_price = entry - sl_dist;   // BUY: SL below entry
   else
      sl_price = entry + sl_dist;   // SELL: SL above entry

   return sl_price;
}

//+------------------------------------------------------------------+
//| Compute TP price with settlement tolerance offset                 |
//|                                                                   |
//| Per strategy.md: "Target is considered reached within the settle  |
//| tolerance PLUS spread."                                           |
//| Python L363: settle_offset = (settle_tol + spread) * pip_size    |
//|                                                                   |
//| For BUY:  TP = target - settle_offset  (don't need full reach)   |
//| For SELL: TP = target + settle_offset  (don't need full reach)   |
//+------------------------------------------------------------------+
double ComputeTP(double target, ENUM_ORDER_TYPE dir,
                 double pip_size, int settle_tol, double spread_pips)
{
   double settle_offset = (settle_tol + spread_pips) * pip_size;

   if(dir == ORDER_TYPE_BUY)
      return target - settle_offset;    // TP slightly below target
   else
      return target + settle_offset;    // TP slightly above target
}

//+------------------------------------------------------------------+
//| Get entry price with spread baked in                              |
//| Per Python L363-366: BUY at ask, SELL at bid                     |
//| (spread is in the entry, not flat-deducted from PnL)             |
//+------------------------------------------------------------------+
double GetEntryPrice(string symbol, ENUM_ORDER_TYPE dir)
{
   if(dir == ORDER_TYPE_BUY)
      return SymbolInfoDouble(symbol, SYMBOL_ASK);
   else
      return SymbolInfoDouble(symbol, SYMBOL_BID);
}

//+------------------------------------------------------------------+
//| Get current spread in pips                                        |
//+------------------------------------------------------------------+
double GetSpreadPips(string symbol, double pip_size)
{
   double ask    = SymbolInfoDouble(symbol, SYMBOL_ASK);
   double bid    = SymbolInfoDouble(symbol, SYMBOL_BID);
   double spread = (ask - bid) / pip_size;
   return spread;
}

#endif // CBS_SL_MQH
