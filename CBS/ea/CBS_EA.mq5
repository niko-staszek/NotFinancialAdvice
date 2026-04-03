//+------------------------------------------------------------------+
//| CBS_EA.mq5 v2.0                                                  |
//| Can't Be Simpler — Expert Advisor for MT5                        |
//|                                                                  |
//| Target = WHERE (H+L-O of previous window = TP level)            |
//| Filters = WHEN (EMA/H4/CLU/LLR checked continuously)            |
//| Entry = moment ALL enabled filters align                         |
//|                                                                  |
//| 4 slots: 1 Offset + 3 Intraday, each independent.               |
//| Drop on chart, load .set file for instrument-specific config.    |
//+------------------------------------------------------------------+
#property copyright "CBS"
#property version   "2.000"

//+------------------------------------------------------------------+
//| Includes                                                          |
//+------------------------------------------------------------------+
#include "Include/CBS/CBS_Config.mqh"
#include "Include/CBS/CBS_Targets.mqh"
#include "Include/CBS/CBS_SL.mqh"
#include "Include/CBS/CBS_Indicators.mqh"
#include "Include/CBS/CBS_Clusters.mqh"
#include "Include/CBS/CBS_LLR.mqh"
#include "Include/CBS/CBS_Sizing.mqh"
#include "Include/CBS/CBS_Trade.mqh"
#include "Include/CBS/CBS_Journal.mqh"

//+------------------------------------------------------------------+
//| Globals                                                           |
//+------------------------------------------------------------------+
string           g_symbol;
InstrumentConfig g_cfg;
int              g_brokerOffset = 0;

//+------------------------------------------------------------------+
//| OnInit                                                            |
//+------------------------------------------------------------------+
int OnInit()
{
   g_symbol       = _Symbol;
   g_cfg          = DetectInstrumentConfig(g_symbol);
   g_brokerOffset = GetBrokerOffsetSec();

   if(!IndicatorsInit(g_symbol))
   {
      Print("[CBS] Indicator init failed.");
      return INIT_FAILED;
   }

   DetectAccountMode();
   SlotsInit();
   EventSetTimer(CBS_TIMER_SEC);

   PrintFormat("===============================================");
   PrintFormat("[CBS EA v2.0] %s", g_symbol);
   PrintFormat("  pip=%.5f settle=%d cluster=%.0f min_dist=%.0f %s",
               g_cfg.pip_size, g_cfg.settle_tol, g_cfg.cluster_size_pips,
               g_cfg.min_distance_pips, g_cfg.is_forex ? "FOREX" : "STANDARD");
   PrintFormat("  Broker: GMT+%d", BrokerGMTOffset);
   PrintFormat("  Off=%s Intra1=%s Intra2=%s Intra3=%s",
               Off_Enable ? "ON" : "off", Intra1_Enable ? "ON" : "off",
               Intra2_Enable ? "ON" : "off", Intra3_Enable ? "ON" : "off");
   PrintFormat("===============================================");

   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| OnDeinit                                                          |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   EventKillTimer();
   IndicatorsDeinit();

   // Write summary to file (persists after tester run)
   string summaryFile = "CBS_TestResult_" + g_symbol + ".txt";
   int fh = FileOpen(summaryFile, FILE_WRITE | FILE_TXT | FILE_ANSI);
   if(fh != INVALID_HANDLE)
   {
      double balance = AccountInfoDouble(ACCOUNT_BALANCE);
      double equity  = AccountInfoDouble(ACCOUNT_EQUITY);
      FileWriteString(fh, StringFormat("Symbol: %s\n", g_symbol));
      FileWriteString(fh, StringFormat("Balance: %.2f\n", balance));
      FileWriteString(fh, StringFormat("Equity: %.2f\n", equity));
      FileWriteString(fh, StringFormat("P&L: %.2f\n", balance - 10000));
      FileClose(fh);
      PrintFormat("[CBS] Test result saved to MQL5/Files/%s", summaryFile);
   }
}

//+------------------------------------------------------------------+
//| OnTimer — main loop                                               |
//+------------------------------------------------------------------+
void OnTimer()
{
   if(IsDailyLossExceeded()) return;
   if(!IsMarketOpen())       return;

   g_brokerOffset = GetBrokerOffsetSec();

   // Process each enabled slot
   if(Off_Enable)    TickSlot(0, Off_StartHourUTC, 24,
                              Off_UseEMA, Off_UseH4, Off_UseCLU, Off_UseLLR,
                              Off_SLMode, Off_BaseLot, MagicBase + 1);
   if(Intra1_Enable) TickSlot(1, Intra1_StartHour, Intra1_DurationH,
                              Intra1_UseEMA, Intra1_UseH4, Intra1_UseCLU, Intra1_UseLLR,
                              Intra1_SLMode, Intra1_BaseLot, MagicBase + 2);
   if(Intra2_Enable) TickSlot(2, Intra2_StartHour, Intra2_DurationH,
                              Intra2_UseEMA, Intra2_UseH4, Intra2_UseCLU, Intra2_UseLLR,
                              Intra2_SLMode, Intra2_BaseLot, MagicBase + 3);
   if(Intra3_Enable) TickSlot(3, Intra3_StartHour, Intra3_DurationH,
                              Intra3_UseEMA, Intra3_UseH4, Intra3_UseCLU, Intra3_UseLLR,
                              Intra3_SLMode, Intra3_BaseLot, MagicBase + 4);
}

//+------------------------------------------------------------------+
//| TickSlot — per-slot dispatch based on state                       |
//+------------------------------------------------------------------+
void TickSlot(int idx, int start_h, int dur_h,
              bool use_ema, bool use_h4, bool use_clu, bool use_llr,
              ENUM_SL_MODE sl_mode, double base_lot, int magic)
{
   switch(g_slots[idx].state)
   {
      case SLOT_ACTIVE:
         SlotCheckActive(idx, g_symbol);
         break;

      case SLOT_CLU_WAITING:
         if(SlotCheckCLUWait(idx, g_symbol))
         {
            // CLU cleared — re-check EMA at new price, then enter
            if(use_ema && !EMAFilter(g_symbol, g_slots[idx].dir))
            {
               g_slots[idx].state = SLOT_WATCHING;  // EMA lost alignment, go back
               break;
            }
            // Enter at new price
            CbsTarget tgt;
            tgt.price = g_slots[idx].target;
            tgt.valid = true;
            tgt.window_open = g_slots[idx].last_window_open;
            tgt.window_close = g_slots[idx].last_window_open + dur_h * 3600;
            DoEntry(idx, g_slots[idx].dir, tgt, g_slots[idx].clu_sl_mode,
                    g_slots[idx].clu_base_lot, g_slots[idx].clu_magic);
         }
         break;

      case SLOT_IDLE:
      case SLOT_WATCHING:
      default:
         ProcessSlot(idx, start_h, dur_h, use_ema, use_h4, use_clu, use_llr,
                     sl_mode, base_lot, magic);
         break;
   }
}

//+------------------------------------------------------------------+
//| ProcessSlot — continuous filter monitoring                        |
//|                                                                   |
//| Called every tick for IDLE/WATCHING slots.                        |
//| Target = WHERE. Filters = WHEN. Enter when ALL align.            |
//| If filters reject: return (DON'T mark window done). Retry next.  |
//+------------------------------------------------------------------+
void ProcessSlot(int idx, int start_h, int dur_h,
                 bool use_ema, bool use_h4, bool use_clu, bool use_llr,
                 ENUM_SL_MODE sl_mode, double base_lot, int magic)
{
   // Compute target
   CbsTarget tgt = ComputeTarget(g_symbol, start_h, dur_h, g_brokerOffset);
   if(!tgt.valid) return;

   // Inside entry window?
   if(!IsInEntryWindow(tgt)) return;

   // Already traded this window?
   if(!IsNewWindow(tgt.window_open, g_slots[idx].last_window_open)) return;

   // Direction from current price
   ENUM_ORDER_TYPE dir = TargetDirection(tgt.price, g_symbol);
   double cur_price = GetEntryPrice(g_symbol, dir);
   double dist_pips = MathAbs(tgt.price - cur_price) / g_cfg.pip_size;

   // Min distance: per strategy.md rule 2 — ALWAYS enforced, not just for CLU
   // "If less than 15 pips to the target -> do NOT open. Spread is additional."
   double spread_now = GetSpreadPips(g_symbol, g_cfg.pip_size);
   if(dist_pips < g_cfg.min_distance_pips + spread_now) return;

   // ── ENTRY CONDITIONS — retry each tick until all align ────────

   // EMA: momentum agrees
   if(use_ema && !EMAFilter(g_symbol, dir)) return;

   // H4: trend agrees
   if(use_h4 && !H4Filter(g_symbol, dir)) return;

   // LLR: path clear
   if(use_llr && !LLRFilter(g_symbol, dir)) return;

   // CLU: no cluster obstacle
   if(use_clu)
   {
      double clu_clear = 0;
      bool blocked = CLUFilter(g_symbol, cur_price, tgt.price, dir,
                                g_cfg.pip_size, g_cfg.cluster_size_pips,
                                g_cfg.min_distance_pips, clu_clear);
      if(blocked)
      {
         if(clu_clear > 0 && g_slots[idx].state != SLOT_CLU_WAITING)
         {
            // Park in CLU_WAITING — will check each tick for clear
            g_slots[idx].state           = SLOT_CLU_WAITING;
            g_slots[idx].clu_clear_price = clu_clear;
            g_slots[idx].clu_signal_time = GetUTCTime();
            g_slots[idx].dir             = dir;
            g_slots[idx].target          = tgt.price;
            g_slots[idx].clu_sl_mode     = sl_mode;
            g_slots[idx].clu_base_lot    = base_lot;
            g_slots[idx].clu_magic       = magic;

            if(DebugMode)
               PrintFormat("[CBS %s] CLU obstacle at %.5f. Waiting for clear.",
                           g_slotNames[idx], clu_clear);
         }
         return;
      }
   }

   // ── ALL conditions met — ENTER NOW ───────────────────────────
   g_slots[idx].state = SLOT_WATCHING;  // Will be set to ACTIVE by DoEntry
   g_slots[idx].last_window_open = tgt.window_open;  // Mark window as done
   DoEntry(idx, dir, tgt, sl_mode, base_lot, magic);
}

//+------------------------------------------------------------------+
//| DoEntry — compute SL/TP/lot and open the trade                    |
//+------------------------------------------------------------------+
void DoEntry(int idx, ENUM_ORDER_TYPE dir, const CbsTarget &tgt,
             ENUM_SL_MODE sl_mode, double base_lot, int magic)
{
   double entry      = GetEntryPrice(g_symbol, dir);
   double spread     = GetSpreadPips(g_symbol, g_cfg.pip_size);
   double tp         = ComputeTP(tgt.price, dir, g_cfg.pip_size, g_cfg.settle_tol, spread);
   double sl         = ComputeSL(entry, tgt.price, dir, sl_mode, g_cfg.pip_size, g_cfg.is_forex);
   double dist_pips  = MathAbs(tgt.price - entry) / g_cfg.pip_size;
   double sl_pips    = MathAbs(sl - entry) / g_cfg.pip_size;
   double lot        = CalculateLot(g_symbol, base_lot, dist_pips, sl_pips, g_cfg.pip_size);

   if(DebugMode)
      PrintFormat("[CBS %s] ENTRY: target=%.5f entry=%.5f tp=%.5f sl=%.5f dist=%.1f %s",
                  g_slotNames[idx], tgt.price, entry, tp, sl, dist_pips,
                  (dir == ORDER_TYPE_BUY) ? "BUY" : "SELL");

   if(SlotOpen(idx, g_symbol, dir, lot, sl, tp, magic,
               g_cfg.pip_size, tgt.price, sl_mode))
   {
      JournalLogEntry(idx, g_symbol, dir, g_slots[idx].entry, tp, sl,
                       lot, dist_pips, tgt.window_open, g_slots[idx].deadline);
   }
   else
   {
      // Open failed — reset state so slot can retry or move to next window
      g_slots[idx].state = SLOT_IDLE;
   }
}

//+------------------------------------------------------------------+
//| OnTick — throttled to 60 sec (broker handles SL/TP in hedging)    |
//+------------------------------------------------------------------+
datetime g_lastTickProcess = 0;

void OnTick()
{
   datetime now = TimeCurrent();
   if(now - g_lastTickProcess < CBS_TIMER_SEC) return;
   g_lastTickProcess = now;
   OnTimer();
}
