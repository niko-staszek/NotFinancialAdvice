//+------------------------------------------------------------------+
//|  ORB_EA.mq5  —  Opening Range Breakout orchestrator (S0/E0 kernel)|
//+------------------------------------------------------------------+
#property copyright "NotFinancialAdvice"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
#include "..\\..\\Include\\ORB\\ORB_Time.mqh"
#include "..\\..\\Include\\ORB\\ORB_Range.mqh"
#include "..\\..\\Include\\ORB\\ORB_Bias.mqh"
#include "..\\..\\Include\\ORB\\ORB_Signals.mqh"
#include "..\\..\\Include\\ORB\\ORB_Stops.mqh"
#include "..\\..\\Include\\ORB\\ORB_Exits.mqh"
#include "..\\..\\Include\\ORB\\ORB_Risk.mqh"
#include "..\\..\\Include\\ORB\\ORB_Ledger.mqh"

//--- inputs
input long   InpMagic            = 20260621;
input int    InpOrMinutes        = 15;       // 15 or 30
input int    InpBiasEmaPeriod    = 50;       // {20,50,100,200}
input ENUM_TIMEFRAMES InpBiasTF  = PERIOD_D1;
input double InpRvolThresh       = 1.5;      // {1.0..2.0}
input int    InpRvolLookback     = 14;
input double InpRangeGuardLo     = 0.5;
input double InpRangeGuardHi     = 2.0;
input double InpBufferFrac       = 0.1;
input int    InpEntryStartEt     = 945;      // HHMM
input int    InpEntryEndEt       = 1130;
input int    InpFlatEt           = 1600;
input int    InpStopArm          = 0;        // 0=S0,1=S1,2=S2
input double InpS2AtrK           = 1.5;
input int    InpAtrPeriod        = 14;
input int    InpExitArm          = 0;        // 0=E0,1=E1,2=E2,3=E3,4=E4
input double InpTargetK          = 1.0;      // E0=1, E1=2/3
input int    InpTrailEmaPeriod   = 8;        // 8 or 21 (E2/E3/E4)
input ENUM_TIMEFRAMES InpTrailTF = PERIOD_M15;
input double InpRiskPct          = 1.0;
input double InpMaxLot           = 50.0;
input int    InpSrvToUtcOffsetSec= 999999;   // 999999 = auto-detect at init
input string InpLedgerLabel      = "smoke";  // ledger filename suffix

//--- globals
CTrade   g_trade;
int      g_biasEmaHandle, g_trailEmaHandle, g_atrHandle;
int      g_srvOffsetSec;
int      g_ledger;
int      g_diag;   // per-day decision diagnostics -> Common\Files\ORB\diag_<label>.csv

enum OrbDay { WAIT, CAPTURING, ARMED, INTRADE, DONE };
OrbDay   g_state;
int      g_curDayEt;          // ET day-of-year to detect rollover
double   g_orHigh, g_orLow, g_orVolAccum;
int      g_bias;
double   g_priorWidths[], g_priorVols[];   // ring buffers length InpRvolLookback
ulong    g_posTicket;
ulong    g_pendTicket;
bool     g_tookPartial;
int      g_tradeSeq;
// open-trade context (captured at arm/fill; consumed by OnTradeTransaction on the OUT deal)
string   g_exitReason;
int      g_tDir;
double   g_tEntry, g_tSL, g_tTP, g_tR, g_tOrWidth, g_tRvol, g_tBiasEma;
datetime g_tOpen;

//+------------------------------------------------------------------+
//| Forward declarations                                             |
//+------------------------------------------------------------------+
double EmaVal(int handle, int shift);
double AtrVal();
void   ArmIfQualified();
void   ManageTrade(datetime srv, int etMin);
void   RollHistory();
void   PushRing(double &arr[], double v, int cap);
void   CloseTrade(string reason);

//+------------------------------------------------------------------+
//| OnInit                                                           |
//+------------------------------------------------------------------+
int OnInit()
{
   g_biasEmaHandle  = iMA(_Symbol, InpBiasTF,   InpBiasEmaPeriod,  0, MODE_EMA, PRICE_CLOSE);
   g_trailEmaHandle = iMA(_Symbol, InpTrailTF,  InpTrailEmaPeriod, 0, MODE_EMA, PRICE_CLOSE);
   g_atrHandle      = iATR(_Symbol, InpTrailTF, InpAtrPeriod);

   if(g_biasEmaHandle  == INVALID_HANDLE ||
      g_trailEmaHandle == INVALID_HANDLE ||
      g_atrHandle      == INVALID_HANDLE)
      return INIT_FAILED;

   g_srvOffsetSec = (InpSrvToUtcOffsetSec != 999999) ? InpSrvToUtcOffsetSec : 0; // recomputed per-tick (tester-safe)

   g_trade.SetExpertMagicNumber((ulong)InpMagic);

   ArrayResize(g_priorWidths, 0);
   ArrayResize(g_priorVols,   0);

   string lp = StringFormat("ORB\\ledger_%s.csv", InpLedgerLabel);
   g_ledger = ORB_LedgerOpen(lp);

   g_diag = FileOpen(StringFormat("ORB\\diag_%s.csv", InpLedgerLabel),
                     FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON, ",");
   if(g_diag != INVALID_HANDLE)
      FileWrite(g_diag,"day_et","ringN","orVol","width","rvol","priorClose","biasEma","bias","reason");

   g_state      = WAIT;
   g_curDayEt   = -1;
   g_tradeSeq   = 0;
   g_posTicket  = 0;
   g_pendTicket = 0;
   g_tookPartial= false;
   g_orHigh     = -DBL_MAX;
   g_orLow      =  DBL_MAX;
   g_orVolAccum = 0;
   g_bias       = 0;
   g_exitReason = "";

   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| OnDeinit                                                         |
//+------------------------------------------------------------------+
void OnDeinit(const int r)
{
   if(g_posTicket > 0 && PositionSelectByTicket(g_posTicket))
      CloseTrade("forced_eod");

   ORB_LedgerClose(g_ledger);
   if(g_diag != INVALID_HANDLE) FileClose(g_diag);
   IndicatorRelease(g_biasEmaHandle);
   IndicatorRelease(g_trailEmaHandle);
   IndicatorRelease(g_atrHandle);
}

//+------------------------------------------------------------------+
//| OnTick — daily state machine                                     |
//+------------------------------------------------------------------+
void OnTick()
{
   datetime srv  = TimeCurrent();
   // deterministic server->UTC offset per tick (handles EU DST; avoids unreliable tester TimeGMT())
   g_srvOffsetSec = (InpSrvToUtcOffsetSec != 999999) ? InpSrvToUtcOffsetSec : ORB_ServerToUtcOffsetSec(srv);
   int      etMin = ORB_EtMinutesFromServer(srv, g_srvOffsetSec);
   MqlDateTime et;
   TimeToStruct(ORB_UtcToEt(srv - g_srvOffsetSec), et);

   // day rollover: first tick of a new ET day
   if(et.day_of_year != g_curDayEt)
   {
      if(g_state != WAIT) RollHistory();   // push yesterday's OR width+vol into ring buffers
      g_curDayEt    = et.day_of_year;
      g_state       = WAIT;
      g_orHigh      = -DBL_MAX;
      g_orLow       =  DBL_MAX;
      g_orVolAccum  = 0;
      g_tookPartial = false;
      g_pendTicket  = 0;
      g_posTicket   = 0;
   }

   // 1) capture OR
   if(ORB_InOpeningRange(srv, g_srvOffsetSec, InpOrMinutes))
   {
      g_state = CAPTURING;
      double hi = iHigh(_Symbol, PERIOD_M1, 0);
      double lo = iLow (_Symbol, PERIOD_M1, 0);
      if(hi > g_orHigh) g_orHigh = hi;
      if(lo < g_orLow)  g_orLow  = lo;
      return;
   }

   // 2) first tick AFTER OR window: compute real OR participation, then decide + arm.
   //    Sum tick volume of the M1 bars whose ET minute falls inside [09:30, 09:30+OR);
   //    filtering by ET time (not a fixed shift) is robust to sparse/gappy opens.
   if(g_state == CAPTURING && etMin >= 570 + InpOrMinutes)
   {
      g_orVolAccum = 0.0;
      for(int s = 1; s <= InpOrMinutes + 5; s++)
      {
         datetime bt = iTime(_Symbol, PERIOD_M1, s);
         if(bt == 0) break;
         int bm = ORB_EtMinutesFromServer(bt, g_srvOffsetSec);
         if(bm >= 570 && bm < 570 + InpOrMinutes)
            g_orVolAccum += (double)iTickVolume(_Symbol, PERIOD_M1, s);
      }
      ArmIfQualified();
   }

   // 3) entry window expiry: cancel unfilled pending
   if(g_state == ARMED && g_pendTicket > 0)
   {
      int endMinutes = (InpEntryEndEt / 100) * 60 + (InpEntryEndEt % 100);
      if(etMin >= endMinutes && !ORB_InEntryWindow(srv, g_srvOffsetSec, InpEntryStartEt, InpEntryEndEt))
      {
         g_trade.OrderDelete(g_pendTicket);
         g_pendTicket = 0;
         g_state = DONE;
      }
   }

   // 4) detect fill ARMED -> INTRADE
   if(g_state == ARMED && g_pendTicket > 0 && PositionSelectByTicket(g_pendTicket))
   {
      g_posTicket  = g_pendTicket;
      g_pendTicket = 0;
      g_state      = INTRADE;
      g_exitReason = "";
      g_tEntry = PositionGetDouble(POSITION_PRICE_OPEN);
      g_tSL    = PositionGetDouble(POSITION_SL);
      g_tTP    = PositionGetDouble(POSITION_TP);
      g_tDir   = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? +1 : -1;
      g_tR     = ORB_R(g_tEntry, g_tSL);
      g_tOpen  = (datetime)(long)PositionGetInteger(POSITION_TIME);
   }

   // 5) manage open trade
   if(g_state == INTRADE)
      ManageTrade(srv, etMin);
}

//+------------------------------------------------------------------+
//| Helpers                                                          |
//+------------------------------------------------------------------+
double EmaVal(int handle, int shift)
{
   double b[];
   if(CopyBuffer(handle, 0, shift, 1, b) < 1) return 0.0;
   return b[0];
}

double AtrVal()
{
   double b[];
   if(CopyBuffer(g_atrHandle, 0, 1, 1, b) < 1) return 0.0;
   return b[0];
}

void ArmIfQualified()
{
   int    n          = ArraySize(g_priorWidths);
   double width      = ORB_Width(g_orHigh, g_orLow);
   double rvol       = (n > 0) ? ORB_Rvol(g_orVolAccum, g_priorVols, n) : 0.0;
   double priorClose = iClose(_Symbol, InpBiasTF, 1);
   double biasEma    = EmaVal(g_biasEmaHandle, 1);
   int    bias       = ORB_Bias(priorClose, biasEma);
   string reason     = "armed";

   if(n < InpRvolLookback)                                                               reason = "warmup";
   else if(!ORB_RangeGuardOk(width, g_priorWidths, n, InpRangeGuardLo, InpRangeGuardHi)) reason = "range_guard";
   else if(rvol < InpRvolThresh)                                                         reason = "rvol_low";
   else if(bias == 0)                                                                    reason = "bias_flat";

   if(g_diag != INVALID_HANDLE)
      FileWrite(g_diag, g_curDayEt, n, (long)g_orVolAccum, width, rvol, priorClose, biasEma, bias, reason);

   if(reason != "armed"){ g_state = DONE; return; }

   g_bias       = bias;
   double entry = ORB_EntryPrice(g_bias, g_orHigh, g_orLow, InpBufferFrac);
   double sl    = ORB_StopLoss(InpStopArm, g_bias, entry,
                               g_orHigh, g_orLow,
                               ORB_Mid(g_orHigh, g_orLow),
                               AtrVal(), InpS2AtrK);
   double R  = ORB_R(entry, sl);
   double tp = (InpExitArm <= 1) ? ORB_Target(g_bias, entry, R, InpTargetK) : 0.0;

   // context consumed by OnTradeTransaction on the OUT deal (entry/sl refreshed at actual fill)
   g_tOrWidth = width; g_tRvol = rvol; g_tBiasEma = biasEma;
   g_tDir = g_bias; g_tEntry = entry; g_tSL = sl; g_tTP = tp; g_tR = R;

   double tickVal  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double valPerUnit = (tickSize > 0.0) ? (tickVal / tickSize) : 0.0;

   double lots = ORB_LotsFromRisk(AccountInfoDouble(ACCOUNT_EQUITY), InpRiskPct, R,
                                  valPerUnit,
                                  SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP),
                                  SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN),
                                  InpMaxLot);
   if(lots <= 0.0)
   {
      if(g_diag != INVALID_HANDLE)
         FileWrite(g_diag, g_curDayEt, n, (long)g_orVolAccum, width, R, entry, sl, valPerUnit, "lots_zero");
      g_state = DONE; return;
   }

   bool ok = (g_bias > 0)
             ? g_trade.BuyStop (lots, entry, _Symbol, sl, tp, ORDER_TIME_GTC, 0, "")
             : g_trade.SellStop(lots, entry, _Symbol, sl, tp, ORDER_TIME_GTC, 0, "");

   if(ok){ g_pendTicket = g_trade.ResultOrder(); g_state = ARMED; }
   else
   {
      if(g_diag != INVALID_HANDLE)
         FileWrite(g_diag, g_curDayEt, n, (long)g_orVolAccum, width, rvol, entry, sl, (double)g_trade.ResultRetcode(), "order_fail");
      g_state = DONE;
   }
}

void ManageTrade(datetime srv, int etMin)
{
   if(!PositionSelectByTicket(g_posTicket)){ g_state = DONE; return; } // closed by SL/TP

   int    dir   = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY) ? +1 : -1;
   double entry = PositionGetDouble(POSITION_PRICE_OPEN);
   double sl    = PositionGetDouble(POSITION_SL);

   // EOD flat
   if(ORB_AtOrAfterFlat(srv, g_srvOffsetSec, InpFlatEt))
      { CloseTrade("forced_eod"); return; }

   // E2/E3/E4: partial and/or EMA trail
   if(InpExitArm >= 2)
   {
      double R = ORB_R(entry, sl);

      // E2: partial at 1R
      if(InpExitArm == 2 && !g_tookPartial)
      {
         double oneR = ORB_Target(dir, entry, R, 1.0);
         double px   = (dir > 0)
                       ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                       : SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         if((dir > 0 && px >= oneR) || (dir < 0 && px <= oneR))
         {
            double halfLots = PositionGetDouble(POSITION_VOLUME) / 2.0;
            g_trade.PositionClosePartial(g_posTicket, halfLots);
            g_tookPartial = true;
         }
      }

      // EMA close-cross on newly completed M15 bar
      static datetime lastM15 = 0;
      datetime m15t = iTime(_Symbol, InpTrailTF, 0);
      if(m15t != lastM15)
      {
         lastM15 = m15t;
         double m15close = iClose(_Symbol, InpTrailTF, 1);
         double ema      = EmaVal(g_trailEmaHandle, 1);
         if(ORB_EmaCloseCrossExit(dir, m15close, ema))
            CloseTrade("ema_cross");
      }
   }
}

void RollHistory()
{
   PushRing(g_priorWidths, ORB_Width(g_orHigh, g_orLow), InpRvolLookback);
   PushRing(g_priorVols,   g_orVolAccum,                 InpRvolLookback);
}

void PushRing(double &arr[], double v, int cap)
{
   int n = ArraySize(arr);
   if(n < cap){ ArrayResize(arr, n + 1); arr[n] = v; return; }
   for(int i = 0; i < cap - 1; i++) arr[i] = arr[i + 1];
   arr[cap - 1] = v;
}

//+------------------------------------------------------------------+
//| CloseTrade — set the exit reason and close; the ledger row is     |
//| written by OnTradeTransaction on the resulting OUT deal.          |
//+------------------------------------------------------------------+
void CloseTrade(string reason)
{
   if(!PositionSelectByTicket(g_posTicket)) return;
   g_exitReason = reason;
   g_trade.PositionClose(g_posTicket);
   g_state = DONE;
}

//+------------------------------------------------------------------+
//| OnTradeTransaction — single ledger source: logs every closing     |
//| deal, incl. broker SL/TP hits AND EA-initiated EOD/EMA closes.    |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest &request,
                        const MqlTradeResult &result)
{
   if(trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
   ulong deal = trans.deal;
   if(!HistoryDealSelect(deal)) return;
   if((long)HistoryDealGetInteger(deal, DEAL_MAGIC) != InpMagic) return;
   if((ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal, DEAL_ENTRY) != DEAL_ENTRY_OUT) return;

   double exitPx = HistoryDealGetDouble(deal, DEAL_PRICE);
   double profit = HistoryDealGetDouble(deal, DEAL_PROFIT);
   double swap   = HistoryDealGetDouble(deal, DEAL_SWAP);
   double comm   = HistoryDealGetDouble(deal, DEAL_COMMISSION);
   double lots   = HistoryDealGetDouble(deal, DEAL_VOLUME);
   ENUM_DEAL_REASON dr = (ENUM_DEAL_REASON)HistoryDealGetInteger(deal, DEAL_REASON);

   string reason = (dr == DEAL_REASON_SL) ? "sl_hit"
                 : (dr == DEAL_REASON_TP) ? "tp_hit"
                 : (g_exitReason != "" ? g_exitReason : "expert");

   double rmult = (g_tR > 0.0)
                  ? ((g_tDir > 0) ? (exitPx - g_tEntry) : (g_tEntry - exitPx)) / g_tR
                  : 0.0;

   ORB_LedgerRow(g_ledger, ++g_tradeSeq, _Symbol, g_tDir,
                 (datetime)((long)g_tOpen - (long)g_srvOffsetSec),
                 (datetime)((long)TimeCurrent() - (long)g_srvOffsetSec),
                 g_tEntry, g_tSL, g_tTP, lots, reason,
                 profit, comm, swap, profit + swap + comm, rmult,
                 g_tBiasEma, g_tRvol, g_tOrWidth, InpStopArm, InpExitArm);

   g_exitReason = "";
}

//+------------------------------------------------------------------+
//| OnTester                                                         |
//+------------------------------------------------------------------+
double OnTester()
{
   double t = TesterStatistics(STAT_TRADES);
   return (t > 0.0) ? TesterStatistics(STAT_PROFIT) / t : 0.0;
}
//+------------------------------------------------------------------+
