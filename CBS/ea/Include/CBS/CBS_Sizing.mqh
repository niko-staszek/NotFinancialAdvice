//+------------------------------------------------------------------+
//| CBS_Sizing.mqh v2.0                                              |
//| Two modes: Fixed lot or Risk% of balance                         |
//|                                                                  |
//| Fixed:  lot = BaseLot × distance_tier_mult                      |
//| Risk%:  lot = (balance × risk%) / (sl_pips × pip_value)         |
//|         then × distance_tier_mult                                |
//|                                                                  |
//| Risk% compounds automatically — bigger balance = bigger lots.    |
//+------------------------------------------------------------------+
#ifndef CBS_SIZING_MQH
#define CBS_SIZING_MQH

//+------------------------------------------------------------------+
//| Distance from current price to target in pips                     |
//+------------------------------------------------------------------+
double TargetDistPips(double target, double current_price, double pip_size)
{
   return MathAbs(target - current_price) / pip_size;
}

//+------------------------------------------------------------------+
//| Get distance tier multiplier                                      |
//+------------------------------------------------------------------+
double GetDistTierMult(double dist_pips, bool enabled,
                        double t1, double t1m,
                        double t2, double t2m,
                        double far_m)
{
   if(!enabled) return 1.0;
   if(dist_pips <= t1) return t1m;
   if(dist_pips <= t2) return t2m;
   return far_m;
}

//+------------------------------------------------------------------+
//| Calculate lot size based on risk % of balance                     |
//|                                                                   |
//| risk_pct  : e.g. 0.2 for 0.2% of balance                       |
//| sl_pips   : stop loss distance in pips                            |
//| pip_size  : instrument pip size (e.g. 0.0001)                    |
//+------------------------------------------------------------------+
double CalcRiskLot(string symbol, double risk_pct, double sl_pips, double pip_size)
{
   if(sl_pips <= 0) return 0.01;

   double balance    = AccountInfoDouble(ACCOUNT_BALANCE);
   double risk_money = balance * risk_pct / 100.0;

   // pip_value = how much 1 pip costs for 1 standard lot
   double tick_value = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
   double tick_size  = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);

   if(tick_value <= 0 || tick_size <= 0) return 0.01;

   // Cost of sl_pips for 1 lot = sl_pips * pip_size / tick_size * tick_value
   double sl_cost_per_lot = sl_pips * pip_size / tick_size * tick_value;

   if(sl_cost_per_lot <= 0) return 0.01;

   double lot = risk_money / sl_cost_per_lot;
   return lot;
}

//+------------------------------------------------------------------+
//| Main lot calculation — dispatches to Fixed or Risk% mode          |
//|                                                                   |
//| base_lot  : from slot config (Off_BaseLot etc)                   |
//| dist_pips : distance to target in pips                            |
//| sl_pips   : stop loss distance in pips (for risk% mode)          |
//+------------------------------------------------------------------+
double CalculateLot(string symbol, double base_lot, double dist_pips,
                     double sl_pips, double pip_size)
{
   // Distance tier multiplier
   double tier_mult = GetDistTierMult(dist_pips, DistTier_Enable,
                                       DistTier1Pips, DistTier1Mult,
                                       DistTier2Pips, DistTier2Mult,
                                       DistFarMult);

   double lot;

   if(LotMode == LOT_RISK_PERCENT)
   {
      // Risk% mode: calculate from balance and SL
      // Apply tier to the risk% (close targets get higher risk)
      double effective_risk = RiskPercent * tier_mult;
      lot = CalcRiskLot(symbol, effective_risk, sl_pips, pip_size);
   }
   else
   {
      // Fixed mode: base_lot × tier multiplier
      lot = base_lot * tier_mult;
   }

   // Clamp to broker limits
   double min_lot  = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double max_lot  = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   double lot_step = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);

   if(lot_step > 0)
      lot = MathFloor(lot / lot_step) * lot_step;

   lot = MathMax(min_lot, lot);
   lot = MathMin(lot, MathMin(max_lot, MaxLotSize));

   // Margin safety: don't exceed 50% of free margin
   double margin_req = 0;
   if(OrderCalcMargin(ORDER_TYPE_BUY, symbol, lot,
                       SymbolInfoDouble(symbol, SYMBOL_ASK), margin_req))
   {
      double free = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
      if(margin_req > free * 0.5 && margin_req > 0)
      {
         lot = lot * (free * 0.5) / margin_req;
         if(lot_step > 0) lot = MathFloor(lot / lot_step) * lot_step;
         lot = MathMax(min_lot, lot);
      }
   }

   return lot;
}

#endif // CBS_SIZING_MQH
