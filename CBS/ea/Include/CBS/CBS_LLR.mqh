//+------------------------------------------------------------------+
//| CBS_LLR.mqh v1.0                                                 |
//| Line of Least Resistance — micro-swing filter                    |
//|                                                                  |
//| Per strategy.md L257+:                                           |
//| "A line connecting at least 2 micro-swings (the small direction  |
//| changes in the last 5-7 candles)."                               |
//|                                                                  |
//| Matches Python compute_llr_flags() L172-190:                     |
//| Detects ascending support (for BUY) and descending resistance    |
//| (for SELL) from recent M15 micro-swings.                         |
//|                                                                  |
//| BUY pass:  price above ascending support line (lows rising)      |
//| SELL pass: price below descending resistance line (highs falling)|
//+------------------------------------------------------------------+
#ifndef CBS_LLR_MQH
#define CBS_LLR_MQH

#define LLR_LOOKBACK  7    // Number of M15 bars to analyze for micro-swings

//+------------------------------------------------------------------+
//| LLR Filter                                                        |
//|                                                                   |
//| Returns: true = filter passes (trade allowed)                     |
//|          false = filter blocks (trade rejected)                   |
//+------------------------------------------------------------------+
bool LLRFilter(string symbol, ENUM_ORDER_TYPE dir)
{
   MqlRates m15[];
   ArraySetAsSeries(m15, true);

   int copied = CopyRates(symbol, PERIOD_M15, 0, LLR_LOOKBACK + 2, m15);
   if(copied < 4)
      return true;  // Not enough data -> pass

   double close_now = m15[0].close;

   if(dir == ORDER_TYPE_BUY)
   {
      // Find two recent swing lows (micro-support points)
      // A swing low: bar[i].low < bar[i-1].low AND bar[i].low < bar[i+1].low
      // (or simplified: a local minimum)
      double sl_prev_price = 0;
      int    sl_prev_idx   = 0;
      double sl_last_price = 0;
      int    sl_last_idx   = 0;
      bool   found_first   = false;
      bool   found_second  = false;

      for(int i = 1; i < copied - 1; i++)
      {
         if(m15[i].low < m15[i - 1].low && m15[i].low <= m15[i + 1].low)
         {
            // Found a swing low
            if(!found_first)
            {
               sl_last_price = m15[i].low;
               sl_last_idx   = i;
               found_first   = true;
            }
            else if(!found_second)
            {
               sl_prev_price = sl_last_price;
               sl_prev_idx   = sl_last_idx;
               sl_last_price = m15[i].low;
               sl_last_idx   = i;
               found_second  = true;
            }
            else
            {
               sl_prev_price = sl_last_price;
               sl_prev_idx   = sl_last_idx;
               sl_last_price = m15[i].low;
               sl_last_idx   = i;
            }
         }
      }

      if(!found_second || sl_prev_idx == sl_last_idx)
         return true;  // Not enough swing lows -> pass

      // Project support line to current bar (bar 0)
      // Note: ArraySetAsSeries so bar[0] is newest — higher index = older bar
      // Slope should be: (newer - older) / (older_idx - newer_idx) because older has higher index
      double slope = (sl_prev_price - sl_last_price) / (double)(sl_prev_idx - sl_last_idx);
      double projected = sl_last_price + slope * (double)(sl_last_idx - 0);

      // BUY: price must be above the projected support line
      return (close_now > projected);
   }
   else
   {
      // Find two recent swing highs (micro-resistance points)
      double sh_prev_price = 0;
      int    sh_prev_idx   = 0;
      double sh_last_price = 0;
      int    sh_last_idx   = 0;
      bool   found_first   = false;
      bool   found_second  = false;

      for(int i = 1; i < copied - 1; i++)
      {
         if(m15[i].high > m15[i - 1].high && m15[i].high >= m15[i + 1].high)
         {
            if(!found_first)
            {
               sh_last_price = m15[i].high;
               sh_last_idx   = i;
               found_first   = true;
            }
            else if(!found_second)
            {
               sh_prev_price = sh_last_price;
               sh_prev_idx   = sh_last_idx;
               sh_last_price = m15[i].high;
               sh_last_idx   = i;
               found_second  = true;
            }
            else
            {
               sh_prev_price = sh_last_price;
               sh_prev_idx   = sh_last_idx;
               sh_last_price = m15[i].high;
               sh_last_idx   = i;
            }
         }
      }

      if(!found_second || sh_prev_idx == sh_last_idx)
         return true;  // Not enough swing highs -> pass

      // Project resistance line to current bar
      double slope = (sh_prev_price - sh_last_price) / (double)(sh_prev_idx - sh_last_idx);
      double projected = sh_last_price + slope * (double)(sh_last_idx - 0);

      // SELL: price must be below the projected resistance line
      return (close_now < projected);
   }
}

#endif // CBS_LLR_MQH
