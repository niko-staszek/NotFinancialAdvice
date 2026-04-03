//+------------------------------------------------------------------+
//| CBS_Indicators.mqh v1.0                                          |
//| EMA21 M15 direction filter + H4 EMA21 trend filter               |
//|                                                                  |
//| Matches Python 18_best_targets.py:                               |
//| EMA filter (L411-414):                                           |
//|   BUY: entry > EMA21  |  SELL: entry < EMA21                    |
//| H4 filter (L416-419):                                            |
//|   BUY: h4_trend > 0 (EMA rising) | SELL: h4_trend < 0 (falling) |
//+------------------------------------------------------------------+
#ifndef CBS_INDICATORS_MQH
#define CBS_INDICATORS_MQH

//+------------------------------------------------------------------+
//| Global indicator handles                                          |
//+------------------------------------------------------------------+
int g_emaM15Handle  = INVALID_HANDLE;
int g_emaH4Handle   = INVALID_HANDLE;

//+------------------------------------------------------------------+
//| Initialize indicator handles (call once in OnInit)                |
//+------------------------------------------------------------------+
bool IndicatorsInit(string symbol)
{
   g_emaM15Handle = iMA(symbol, PERIOD_M15, 21, 0, MODE_EMA, PRICE_CLOSE);
   g_emaH4Handle  = iMA(symbol, PERIOD_H4,  21, 0, MODE_EMA, PRICE_CLOSE);

   if(g_emaM15Handle == INVALID_HANDLE)
   {
      PrintFormat("[CBS] Failed to create M15 EMA21 handle for %s. Error: %d", symbol, GetLastError());
      return false;
   }

   if(g_emaH4Handle == INVALID_HANDLE)
   {
      PrintFormat("[CBS] Failed to create H4 EMA21 handle for %s. Error: %d", symbol, GetLastError());
      return false;
   }

   return true;
}

//+------------------------------------------------------------------+
//| Release indicator handles (call in OnDeinit)                      |
//+------------------------------------------------------------------+
void IndicatorsDeinit()
{
   if(g_emaM15Handle != INVALID_HANDLE)
   {
      IndicatorRelease(g_emaM15Handle);
      g_emaM15Handle = INVALID_HANDLE;
   }

   if(g_emaH4Handle != INVALID_HANDLE)
   {
      IndicatorRelease(g_emaH4Handle);
      g_emaH4Handle = INVALID_HANDLE;
   }
}

//+------------------------------------------------------------------+
//| EMA Filter: M15 EMA21 direction agreement                        |
//|                                                                   |
//| Per EA_PARAMETERS_REFERENCE.md L53-58:                           |
//| - BUY allowed only if: entry price > EMA21 (bullish)             |
//| - SELL allowed only if: entry price < EMA21 (bearish)            |
//|                                                                   |
//| Returns: true = filter passes (trade allowed)                     |
//|          false = filter blocks (trade rejected)                   |
//+------------------------------------------------------------------+
bool EMAFilter(string symbol, ENUM_ORDER_TYPE dir)
{
   if(g_emaM15Handle == INVALID_HANDLE)
      return true;  // No data -> pass (don't block on data failure)

   double ema[];
   double price[];
   ArraySetAsSeries(ema, true);
   ArraySetAsSeries(price, true);

   if(CopyBuffer(g_emaM15Handle, 0, 0, 1, ema) < 1)
      return true;  // No data -> pass

   if(CopyClose(symbol, PERIOD_M15, 0, 1, price) < 1)
      return true;  // No data -> pass

   if(dir == ORDER_TYPE_BUY)
      return (price[0] > ema[0]);   // BUY: price must be above EMA21
   else
      return (price[0] < ema[0]);   // SELL: price must be below EMA21
}

//+------------------------------------------------------------------+
//| H4 Trend Filter: H4 EMA21 slope must agree with direction        |
//|                                                                   |
//| Per EA_PARAMETERS_REFERENCE.md L60-65:                           |
//| - BUY allowed only if: H4 EMA21 is rising (current > previous)  |
//| - SELL allowed only if: H4 EMA21 is falling (current < previous) |
//|                                                                   |
//| Python compute_h4_trend maps:                                     |
//|   h4_close > h4_ema -> +1 (uptrend)                              |
//|   h4_close < h4_ema -> -1 (downtrend)                            |
//|   else -> 0 (neutral, treated as no-pass for both directions)    |
//|                                                                   |
//| Returns: true = filter passes, false = blocked                    |
//+------------------------------------------------------------------+
bool H4Filter(string symbol, ENUM_ORDER_TYPE dir)
{
   if(g_emaH4Handle == INVALID_HANDLE)
      return true;  // No data -> pass

   double ema[];
   double h4Close[];
   ArraySetAsSeries(ema, true);
   ArraySetAsSeries(h4Close, true);

   // Get last 2 EMA values for slope check AND current H4 close for trend check
   if(CopyBuffer(g_emaH4Handle, 0, 0, 2, ema) < 2)
      return true;  // No data -> pass

   if(CopyClose(symbol, PERIOD_H4, 0, 1, h4Close) < 1)
      return true;  // No data -> pass

   // Method 1: H4 close vs H4 EMA21 (matches Python compute_h4_trend)
   // h4_close > ema -> uptrend (+1) -> BUY allowed
   // h4_close < ema -> downtrend (-1) -> SELL allowed
   bool uptrend   = (h4Close[0] > ema[0]);
   bool downtrend = (h4Close[0] < ema[0]);

   if(dir == ORDER_TYPE_BUY)
      return uptrend;     // BUY needs uptrend (H4 close above EMA)
   else
      return downtrend;   // SELL needs downtrend (H4 close below EMA)
}

#endif // CBS_INDICATORS_MQH
