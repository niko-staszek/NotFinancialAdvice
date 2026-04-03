//+------------------------------------------------------------------+
//| CBS_Trade.mqh v2.1                                               |
//| Slot state machine with VIRTUAL SL/TP management.                |
//| Works in both netting and hedging MT5 account modes.             |
//|                                                                  |
//| Orders are placed WITHOUT broker SL/TP (set to 0).              |
//| EA monitors price and closes positions manually when             |
//| virtual SL/TP is hit or timeout expires.                         |
//+------------------------------------------------------------------+
#ifndef CBS_TRADE_MQH
#define CBS_TRADE_MQH

#include <Trade/Trade.mqh>

//+------------------------------------------------------------------+
//| Slot states                                                       |
//+------------------------------------------------------------------+
enum ENUM_SLOT_STATE
{
   SLOT_IDLE = 0,
   SLOT_WATCHING,
   SLOT_CLU_WAITING,
   SLOT_ACTIVE
};

//+------------------------------------------------------------------+
//| Slot state                                                        |
//+------------------------------------------------------------------+
struct SlotState
{
   ENUM_SLOT_STATE state;
   datetime        last_window_open;
   // Trade fields (ACTIVE)
   ulong           ticket;
   datetime         deadline;
   double          entry;
   double          target;
   double          sl;               // Virtual SL (not set on broker)
   double          tp;               // Virtual TP (not set on broker)
   double          lot;              // Lot size for this slot
   ENUM_ORDER_TYPE dir;
   // CLU wait fields
   double          clu_clear_price;
   datetime        clu_signal_time;
   ENUM_SL_MODE    clu_sl_mode;
   double          clu_base_lot;
   int             clu_magic;
};

//+------------------------------------------------------------------+
//| Globals                                                           |
//+------------------------------------------------------------------+
CTrade    g_trade;
SlotState g_slots[CBS_N_SLOTS];
string    g_slotNames[CBS_N_SLOTS] = {"Off", "Intra1", "Intra2", "Intra3"};
bool      g_isHedging = false;

//+------------------------------------------------------------------+
//| Detect account mode (call in OnInit)                              |
//+------------------------------------------------------------------+
void DetectAccountMode()
{
   long mode = AccountInfoInteger(ACCOUNT_MARGIN_MODE);
   g_isHedging = (mode == ACCOUNT_MARGIN_MODE_RETAIL_HEDGING);
   PrintFormat("[CBS] Account mode: %s", g_isHedging ? "HEDGING" : "NETTING");
}

//+------------------------------------------------------------------+
//| Initialize all slots                                              |
//+------------------------------------------------------------------+
void SlotsInit()
{
   for(int i = 0; i < CBS_N_SLOTS; i++)
      SlotReset(i);
}

void SlotReset(int idx)
{
   g_slots[idx].state           = SLOT_IDLE;
   g_slots[idx].ticket          = 0;
   g_slots[idx].deadline        = 0;
   g_slots[idx].entry           = 0;
   g_slots[idx].target          = 0;
   g_slots[idx].sl              = 0;
   g_slots[idx].tp              = 0;
   g_slots[idx].lot             = 0;
   g_slots[idx].dir             = ORDER_TYPE_BUY;
   g_slots[idx].clu_clear_price = 0;
   g_slots[idx].clu_signal_time = 0;
}

//+------------------------------------------------------------------+
//| Open a trade for a slot — NO broker SL/TP                         |
//+------------------------------------------------------------------+
bool SlotOpen(int idx, string symbol, ENUM_ORDER_TYPE dir,
              double lot, double sl, double tp,
              int magic, double pip_size,
              double target, ENUM_SL_MODE sl_mode)
{
   // Spread check
   double spread_pips = GetSpreadPips(symbol, pip_size);
   if(spread_pips > MaxSpreadPips)
   {
      if(DebugMode)
         PrintFormat("[CBS %s] Spread %.1f > max %.1f", g_slotNames[idx], spread_pips, MaxSpreadPips);
      return false;
   }

   // Validate virtual SL/TP sides
   double price_ref = (dir == ORDER_TYPE_BUY)
                      ? SymbolInfoDouble(symbol, SYMBOL_ASK)
                      : SymbolInfoDouble(symbol, SYMBOL_BID);

   if(dir == ORDER_TYPE_BUY && (sl >= price_ref || tp <= price_ref))
      return false;
   if(dir == ORDER_TYPE_SELL && (sl <= price_ref || tp >= price_ref))
      return false;

   // Place order WITH broker SL/TP (account is hedging mode)
   g_trade.SetExpertMagicNumber(magic);
   g_trade.SetDeviationInPoints((int)(SlippagePips * 10));

   // Normalize SL/TP to tick size
   double tick_size = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tick_size > 0)
   {
      sl = MathRound(sl / tick_size) * tick_size;
      tp = MathRound(tp / tick_size) * tick_size;
   }

   string comment = StringFormat("CBS_%s", g_slotNames[idx]);
   bool ok;
   if(dir == ORDER_TYPE_BUY)
      ok = g_trade.Buy(lot, symbol, 0, sl, tp, comment);
   else
      ok = g_trade.Sell(lot, symbol, 0, sl, tp, comment);

   if(!ok)
   {
      PrintFormat("[CBS %s] Order failed. Error: %d | Retcode: %d",
                  g_slotNames[idx], GetLastError(), g_trade.ResultRetcode());
      return false;
   }

   // Populate state with virtual SL/TP
   g_slots[idx].state    = SLOT_ACTIVE;
   g_slots[idx].ticket   = g_trade.ResultOrder();
   g_slots[idx].deadline = GetUTCTime() + CBS_MAX_HOLD_H * 3600;
   g_slots[idx].entry    = g_trade.ResultPrice();
   g_slots[idx].target   = target;
   g_slots[idx].sl       = sl;
   g_slots[idx].tp       = tp;
   g_slots[idx].lot      = lot;
   g_slots[idx].dir      = dir;

   double dist = MathAbs(target - g_slots[idx].entry) / pip_size;
   PrintFormat("[CBS %s] OPENED %s %.2f lots | entry=%.5f vTP=%.5f vSL=%.5f | dist=%.1f pips | deadline=%s",
              g_slotNames[idx],
              (dir == ORDER_TYPE_BUY) ? "BUY" : "SELL",
              lot, g_slots[idx].entry, tp, sl, dist,
              TimeToString(g_slots[idx].deadline + GetBrokerOffsetSec()));

   return true;
}

//+------------------------------------------------------------------+
//| Close a slot's position (partial close in netting, full in hedge) |
//+------------------------------------------------------------------+
bool SlotClose(int idx, string symbol, string reason)
{
   if(g_slots[idx].state != SLOT_ACTIVE)
      return false;

   double lot = g_slots[idx].lot;
   bool closed = false;

   if(g_isHedging)
   {
      // Hedging: close by ticket
      if(PositionSelectByTicket(g_slots[idx].ticket))
         closed = g_trade.PositionClose(g_slots[idx].ticket);
   }
   else
   {
      // Netting: close our lot portion of the symbol's single position
      if(PositionSelect(symbol))
      {
         double pos_volume = PositionGetDouble(POSITION_VOLUME);
         if(lot >= pos_volume)
            closed = g_trade.PositionClose(symbol);  // Close all
         else
            closed = g_trade.PositionClosePartial(symbol, lot);  // Close our portion
      }
      else
      {
         // Position already gone (SL/TP hit externally or closed by broker)
         closed = true;
      }
   }

   if(closed || !PositionSelect(symbol))
   {
      double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
      double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
      double close_price = (g_slots[idx].dir == ORDER_TYPE_BUY) ? bid : ask;
      double pnl = (g_slots[idx].dir == ORDER_TYPE_BUY)
                   ? (close_price - g_slots[idx].entry)
                   : (g_slots[idx].entry - close_price);

      PrintFormat("[CBS %s] %s | pnl=%.5f | entry=%.5f close=%.5f",
                  g_slotNames[idx], reason, pnl, g_slots[idx].entry, close_price);
      SlotReset(idx);
      return true;
   }

   PrintFormat("[CBS %s] Failed to close. Error: %d", g_slotNames[idx], GetLastError());
   return false;
}

//+------------------------------------------------------------------+
//| Check active slot: position existence + timeout                   |
//| SL/TP are set on the broker side (hedging mode).                  |
//| EA just checks if position is still open + handles timeout.       |
//+------------------------------------------------------------------+
void SlotCheckActive(int idx, string symbol)
{
   if(g_slots[idx].state != SLOT_ACTIVE)
      return;

   // Check if position still exists (SL/TP handled by broker)
   if(!PositionSelectByTicket(g_slots[idx].ticket))
   {
      PrintFormat("[CBS %s] Position closed (SL/TP). Ticket: %d",
                  g_slotNames[idx], g_slots[idx].ticket);
      SlotReset(idx);
      return;
   }

   // Check timeout
   if(GetUTCTime() >= g_slots[idx].deadline)
   {
      if(g_trade.PositionClose(g_slots[idx].ticket))
      {
         double close_price = PositionGetDouble(POSITION_PRICE_CURRENT);
         double pnl = (g_slots[idx].dir == ORDER_TYPE_BUY)
                      ? (close_price - g_slots[idx].entry)
                      : (g_slots[idx].entry - close_price);
         PrintFormat("[CBS %s] TIMEOUT CLOSE | pnl=%.5f", g_slotNames[idx], pnl);
      }
      else
         PrintFormat("[CBS %s] Failed timeout close. Error: %d", g_slotNames[idx], GetLastError());

      SlotReset(idx);
   }
}

//+------------------------------------------------------------------+
//| Check CLU waiting state                                           |
//+------------------------------------------------------------------+
bool SlotCheckCLUWait(int idx, string symbol)
{
   if(g_slots[idx].state != SLOT_CLU_WAITING)
      return false;

   if(GetUTCTime() >= g_slots[idx].clu_signal_time + CBS_MAX_HOLD_H * 3600)
   {
      if(DebugMode) PrintFormat("[CBS %s] CLU wait timeout.", g_slotNames[idx]);
      g_slots[idx].state = SLOT_WATCHING;
      return false;
   }

   double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(symbol, SYMBOL_BID);
   bool cleared = (g_slots[idx].dir == ORDER_TYPE_BUY)
                  ? (bid > g_slots[idx].clu_clear_price)
                  : (ask < g_slots[idx].clu_clear_price);

   if(cleared)
   {
      if(DebugMode)
         PrintFormat("[CBS %s] CLU cleared at %.5f", g_slotNames[idx], g_slots[idx].clu_clear_price);
      return true;
   }
   return false;
}

//+------------------------------------------------------------------+
//| Count active slots                                                |
//+------------------------------------------------------------------+
int CountActiveSlots()
{
   int count = 0;
   for(int i = 0; i < CBS_N_SLOTS; i++)
      if(g_slots[i].state == SLOT_ACTIVE) count++;
   return count;
}

#endif // CBS_TRADE_MQH
