//+------------------------------------------------------------------+
//| CBS_Targets.mqh v2.0                                             |
//| Target = H + L - O of the PREVIOUS completed window              |
//|                                                                  |
//| Offset (24h):   prev window fully elapsed -> target known        |
//| Intraday (2-8h): YESTERDAY's session -> target known today       |
//|                                                                  |
//| All window hours are UTC. Broker time = UTC + BrokerGMTOffset.   |
//| TimeGMT() is NOT used (broken in Strategy Tester).               |
//+------------------------------------------------------------------+
#ifndef CBS_TARGETS_MQH
#define CBS_TARGETS_MQH

//+------------------------------------------------------------------+
//| Target struct                                                     |
//+------------------------------------------------------------------+
struct CbsTarget
{
   double   price;            // H + L - O
   datetime window_open;      // UTC: current entry window start
   datetime window_close;     // UTC: current entry window end
   bool     valid;
};

//+------------------------------------------------------------------+
//| UTC time from broker time (reliable in tester + live)             |
//+------------------------------------------------------------------+
datetime GetUTCTime()
{
   return TimeCurrent() - BrokerGMTOffset * 3600;
}

int GetBrokerOffsetSec()
{
   return BrokerGMTOffset * 3600;
}

//+------------------------------------------------------------------+
//| Get midnight (00:00) of a given UTC timestamp                     |
//+------------------------------------------------------------------+
datetime MidnightUTC(datetime utc_time)
{
   MqlDateTime dt;
   TimeToStruct(utc_time, dt);
   dt.hour = 0; dt.min = 0; dt.sec = 0;
   return StructToTime(dt);
}

//+------------------------------------------------------------------+
//| Compute CBS target                                                |
//|                                                                   |
//| OFFSET (dur=24): target from prev 24h window.                    |
//|   prev_window: [today-24h at start_hour] to [today at start_hour]|
//|   entry_window: [today at start_hour] to [tomorrow at start_hour]|
//|                                                                   |
//| INTRADAY (dur<24): target from YESTERDAY's session.              |
//|   prev_window: [yesterday start_hour] to [yesterday start+dur]   |
//|   entry_window: [today start_hour] to [today start+dur]          |
//+------------------------------------------------------------------+
CbsTarget ComputeTarget(string symbol, int start_hour_utc, int duration_hours,
                         int broker_offset)
{
   CbsTarget tgt;
   tgt.valid = false;
   tgt.price = 0;

   datetime now_utc    = TimeCurrent() - broker_offset;
   datetime today_midnight = MidnightUTC(now_utc);

   // ── Current entry window (UTC) ───────────────────────────────
   datetime curr_open = today_midnight + start_hour_utc * 3600;

   if(duration_hours == 24)
   {
      // Offset: if window hasn't opened yet today, use yesterday's as current
      if(curr_open > now_utc)
         curr_open -= 86400;
   }
   else
   {
      // Intraday: if session hasn't started today, yesterday's is "current"
      if(curr_open > now_utc)
         curr_open -= 86400;
   }

   datetime curr_close = curr_open + duration_hours * 3600;
   // Handle wrap-around for intraday (e.g., 22:00-04:00)
   // curr_close naturally wraps via addition

   // ── Previous window (where we get the target) ────────────────
   datetime prev_open, prev_close;

   if(duration_hours == 24)
   {
      // Offset: previous window is exactly 24h before current
      prev_open  = curr_open - 86400;
      prev_close = curr_open;  // prev window ends when current begins
   }
   else
   {
      // Intraday: previous = yesterday's same session
      prev_open  = curr_open - 86400;
      prev_close = prev_open + duration_hours * 3600;
   }

   // ── Convert to broker time for CopyRates ─────────────────────
   datetime prev_open_broker  = prev_open  + broker_offset;
   datetime prev_close_broker = prev_close + broker_offset;

   // ── Fetch ALL M15 bars in previous window ────────────────────
   MqlRates rates[];
   ArraySetAsSeries(rates, false);  // chronological

   int copied = CopyRates(symbol, PERIOD_M15, prev_open_broker, prev_close_broker, rates);

   if(copied < 2)
   {
      if(DebugMode)
         PrintFormat("[CBS Target] No bars for prev window %s->%s broker",
                     TimeToString(prev_open_broker), TimeToString(prev_close_broker));
      return tgt;
   }

   // ── Compute O, H, L from all bars ────────────────────────────
   double O = rates[0].open;
   double H = rates[0].high;
   double L = rates[0].low;

   for(int i = 1; i < copied; i++)
   {
      if(rates[i].high > H) H = rates[i].high;
      if(rates[i].low  < L) L = rates[i].low;
   }

   tgt.price        = H + L - O;
   tgt.window_open  = curr_open;   // UTC
   tgt.window_close = curr_close;  // UTC
   tgt.valid        = true;

   if(DebugMode)
      PrintFormat("[CBS Target] %s %dh | prev=%s->%s | O=%.5f H=%.5f L=%.5f | T=%.5f | %d bars",
                  symbol, duration_hours,
                  TimeToString(prev_open_broker), TimeToString(prev_close_broker),
                  O, H, L, tgt.price, copied);

   return tgt;
}

//+------------------------------------------------------------------+
//| Direction: BUY if target > mid price, SELL if below               |
//+------------------------------------------------------------------+
ENUM_ORDER_TYPE TargetDirection(double target, string symbol)
{
   double mid = (SymbolInfoDouble(symbol, SYMBOL_ASK) + SymbolInfoDouble(symbol, SYMBOL_BID)) * 0.5;
   return (target > mid) ? ORDER_TYPE_BUY : ORDER_TYPE_SELL;
}

//+------------------------------------------------------------------+
//| Are we inside the entry window?                                   |
//+------------------------------------------------------------------+
bool IsInEntryWindow(const CbsTarget &tgt)
{
   if(!tgt.valid) return false;
   datetime now_utc = GetUTCTime();
   return (now_utc >= tgt.window_open && now_utc < tgt.window_close);
}

//+------------------------------------------------------------------+
//| Is this a new window (not yet traded)?                            |
//+------------------------------------------------------------------+
bool IsNewWindow(datetime current_window_open, datetime last_window_open)
{
   return (current_window_open != last_window_open);
}

#endif // CBS_TARGETS_MQH
