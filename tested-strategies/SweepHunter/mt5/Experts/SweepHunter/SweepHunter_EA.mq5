//+------------------------------------------------------------------+
//|  SweepHunter_EA.mq5 — Asia/London sweep -> NY M1 FVG reversal     |
//+------------------------------------------------------------------+
#property copyright "NotFinancialAdvice"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
#include "..\\..\\Include\\SweepHunter\\SH_Time.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Sessions.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Sweep.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_FVG.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Targets.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Stops.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Risk.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Ledger.mqh"

//--- inputs
input long   InpMagic          = 20260622;
input int    InpAsiaStartEt    = 2000;
input int    InpAsiaEndEt      = 0;       // 0000
input int    InpLonStartEt     = 200;
input int    InpLonEndEt       = 500;
input int    InpMarkEt         = 900;
input int    InpHuntStartEt    = 900;
input int    InpHuntEndEt      = 1130;
input int    InpFlatEt         = 1600;
input int    InpLevelMode      = 0;       // 0=FOUR, 1=COMBINED
input int    InpEntryMode      = 0;       // 0=LIMIT, 1=MARKET
input double InpFillDepth      = 0.0;     // 0=proximal..1=distal
input int    InpTargetMode     = 0;       // 0=RR, 1=DOL
input double InpTargetRR       = 2.0;
input double InpStopBufferAtrK = 0.15;
input int    InpAtrPeriod      = 14;
input int    InpScanLookback   = 900;     // M1 bars scanned at mark (>= 15h)
input double InpRiskPct        = 1.0;
input double InpMaxLot         = 50.0;
input int    InpSrvToUtcOffsetSec = 999999; // 999999 = auto-detect per tick
input string InpLedgerLabel    = "smoke";

//--- globals
CTrade   g_trade;
int      g_atrHandle;
int      g_srvOffsetSec;
int      g_ledger;

enum SHState { WAIT, MARKED, ARMED, INTRADE, DONE };
SHState  g_state;
int      g_curDayEt;
datetime g_lastBar;            // last processed M1 bar time (new-bar detection)

SHLevels g_lvl;
double   g_levelArr[4];        // marked levels for DOL candidates
int      g_levelN;

bool     g_marked;
int      g_setupDir;           // +1 long, -1 short
int      g_sweptSide;          // +1 high, -1 low
double   g_sweptLevel;
double   g_swing;              // running swing extreme since sweep
ulong    g_pendTicket, g_posTicket;

// open-trade context consumed by OnTradeTransaction on the OUT deal
int      g_tDir; double g_tEntry,g_tSL,g_tTP,g_tR,g_tSwept; int g_tSide; double g_tDepth;
datetime g_tOpen; string g_exitReason;

double AtrVal();
void   ResetDay();
void   TryMark(int etMin);
void   TryArm();
void   TryEnter();
void   ManageTrade(datetime srv,int etMin);
void   CloseTrade(string reason);
string TargetModeStr(){ return (InpTargetMode==1)?"DOL":"RR"; }

int OnInit() {
  g_atrHandle = iATR(_Symbol, PERIOD_M1, InpAtrPeriod);
  if (g_atrHandle == INVALID_HANDLE) return INIT_FAILED;
  g_trade.SetExpertMagicNumber((ulong)InpMagic);
  string lp = StringFormat("SweepHunter\\ledger_%s.csv", InpLedgerLabel);
  g_ledger = SH_LedgerOpen(lp);
  g_curDayEt = -1; g_lastBar = 0; g_exitReason = "";
  ResetDay();
  return INIT_SUCCEEDED;
}

void OnDeinit(const int r) {
  if (g_posTicket > 0 && PositionSelectByTicket(g_posTicket)) CloseTrade("forced_eod");
  SH_LedgerClose(g_ledger);
  IndicatorRelease(g_atrHandle);
}

double AtrVal() {
  double b[];
  if (CopyBuffer(g_atrHandle, 0, 1, 1, b) < 1) return 0.0;
  return b[0];
}

void ResetDay() {
  g_state = WAIT; g_marked = false; g_levelN = 0;
  g_setupDir = 0; g_sweptSide = 0; g_sweptLevel = 0; g_swing = 0;
  g_pendTicket = 0; g_posTicket = 0;
}

void OnTick() {
  datetime srv = TimeCurrent();
  g_srvOffsetSec = (InpSrvToUtcOffsetSec != 999999) ? InpSrvToUtcOffsetSec
                                                    : ORB_ServerToUtcOffsetSec(srv);
  int etMin = SH_EtMin(srv, g_srvOffsetSec);
  MqlDateTime et; TimeToStruct(ORB_UtcToEt(srv - g_srvOffsetSec), et);

  if (et.day_of_year != g_curDayEt) { g_curDayEt = et.day_of_year; ResetDay(); }

  // act once per closed M1 bar
  datetime bar = iTime(_Symbol, PERIOD_M1, 0);
  bool newBar = (bar != g_lastBar);
  if (newBar) g_lastBar = bar;

  if (g_state == WAIT && etMin >= InpMarkEt/100*60 + InpMarkEt%100) { TryMark(etMin); return; }
  if (!newBar && g_state != INTRADE) return;

  if (g_state == MARKED && SH_InWindowEt(etMin, InpHuntStartEt, InpHuntEndEt)) TryArm();
  if (g_state == ARMED) {
    // cancel unfilled limit at hunt end
    if (!SH_InWindowEt(etMin, InpHuntStartEt, InpHuntEndEt)) {
      if (g_pendTicket > 0) g_trade.OrderDelete(g_pendTicket);
      g_state = DONE; return;
    }
    // fill detection
    if (g_pendTicket > 0 && PositionSelectByTicket(g_pendTicket)) {
      g_posTicket = g_pendTicket; g_pendTicket = 0; g_state = INTRADE;
      g_tEntry = PositionGetDouble(POSITION_PRICE_OPEN);
      g_tSL = PositionGetDouble(POSITION_SL); g_tTP = PositionGetDouble(POSITION_TP);
      g_tDir = (PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY)?+1:-1;
      g_tR = SH_R(g_tEntry, g_tSL); g_tOpen = (datetime)(long)PositionGetInteger(POSITION_TIME);
    } else {
      g_swing = SH_UpdateSwing(g_setupDir, g_swing, iHigh(_Symbol,PERIOD_M1,1), iLow(_Symbol,PERIOD_M1,1));
      TryEnter();
    }
  }
  if (g_state == INTRADE) ManageTrade(srv, etMin);
}

void TryMark(int etMin) {
  g_lvl = SH_ScanLevels(_Symbol, g_srvOffsetSec, InpScanLookback,
                        InpAsiaStartEt, InpAsiaEndEt, InpLonStartEt, InpLonEndEt);
  g_levelN = 0;
  if (InpLevelMode == 1) { // COMBINED outer H/L
    double hi=-DBL_MAX, lo=DBL_MAX; bool ok=false;
    if (g_lvl.asiaValid){ hi=MathMax(hi,g_lvl.asiaH); lo=MathMin(lo,g_lvl.asiaL); ok=true; }
    if (g_lvl.lonValid){  hi=MathMax(hi,g_lvl.lonH);  lo=MathMin(lo,g_lvl.lonL);  ok=true; }
    if (ok){ g_levelArr[g_levelN++]=hi; g_levelArr[g_levelN++]=lo; }
  } else {                 // FOUR distinct
    if (g_lvl.asiaValid){ g_levelArr[g_levelN++]=g_lvl.asiaH; g_levelArr[g_levelN++]=g_lvl.asiaL; }
    if (g_lvl.lonValid){  g_levelArr[g_levelN++]=g_lvl.lonH;  g_levelArr[g_levelN++]=g_lvl.lonL; }
  }
  g_state = (g_levelN > 0) ? MARKED : DONE;
  g_marked = (g_levelN > 0);
}

// Each level is paired (high then low). Determine side from its index parity.
void TryArm() {
  double hi = iHigh(_Symbol, PERIOD_M1, 1), lo = iLow(_Symbol, PERIOD_M1, 1);
  for (int i = 0; i < g_levelN; i++) {
    int side = (i % 2 == 0) ? +1 : -1;   // even idx = high level, odd = low level
    if (SH_Swept(side, hi, lo, g_levelArr[i])) {
      g_sweptSide = side; g_sweptLevel = g_levelArr[i];
      g_setupDir = SH_DirFromSweepSide(side);
      g_swing = (g_setupDir < 0) ? hi : lo;   // seed swing with the sweep bar
      g_state = ARMED;
      return;
    }
  }
}

void TryEnter() {
  double h2=iHigh(_Symbol,PERIOD_M1,3), l2=iLow(_Symbol,PERIOD_M1,3);
  double h1=iHigh(_Symbol,PERIOD_M1,2), l1=iLow(_Symbol,PERIOD_M1,2);
  double h0=iHigh(_Symbol,PERIOD_M1,1), l0=iLow(_Symbol,PERIOD_M1,1);
  if (!SH_IsFVG(g_setupDir, h2,l2, h1,l1, h0,l0)) return;

  double entry = (InpEntryMode==1)
                 ? ((g_setupDir>0)?SymbolInfoDouble(_Symbol,SYMBOL_ASK):SymbolInfoDouble(_Symbol,SYMBOL_BID))
                 : SH_FvgEntry(g_setupDir, h2,l2, h0,l0, InpFillDepth);
  double atr    = AtrVal();
  double buffer = InpStopBufferAtrK * atr;
  double sl     = SH_Stop(g_setupDir, g_swing, buffer);
  double R      = SH_R(entry, sl);
  if (R <= 0.0) { g_state = DONE; return; }

  double tp;
  if (InpTargetMode == 1) { bool found; tp = SH_TargetDOL(g_setupDir, entry, g_levelArr, g_levelN,
                                              SH_TargetRR(g_setupDir, entry, R, InpTargetRR), found); }
  else                    { tp = SH_TargetRR(g_setupDir, entry, R, InpTargetRR); }

  double tickVal=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_VALUE);
  double tickSize=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);
  double valPerUnit=(tickSize>0.0)?(tickVal/tickSize):0.0;
  double lots = SH_LotsFromRisk(AccountInfoDouble(ACCOUNT_EQUITY), InpRiskPct, R, valPerUnit,
                                SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP),
                                SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN), InpMaxLot);
  if (lots <= 0.0) { g_state = DONE; return; }

  // context for the ledger
  g_tDir=g_setupDir; g_tSide=g_sweptSide; g_tSwept=g_sweptLevel; g_tDepth=InpFillDepth;

  bool ok;
  if (InpEntryMode == 1)
    ok = (g_setupDir>0) ? g_trade.Buy(lots,_Symbol,entry,sl,tp) : g_trade.Sell(lots,_Symbol,entry,sl,tp);
  else
    ok = (g_setupDir>0) ? g_trade.BuyLimit(lots,entry,_Symbol,sl,tp,ORDER_TIME_GTC,0,"")
                        : g_trade.SellLimit(lots,entry,_Symbol,sl,tp,ORDER_TIME_GTC,0,"");
  if (ok) g_pendTicket = g_trade.ResultOrder();
  else    g_state = DONE;
}

void ManageTrade(datetime srv,int etMin) {
  if (!PositionSelectByTicket(g_posTicket)) { g_state = DONE; return; } // SL/TP closed it
  if (etMin >= InpFlatEt/100*60 + InpFlatEt%100) CloseTrade("forced_eod");
}

void CloseTrade(string reason) {
  if (!PositionSelectByTicket(g_posTicket)) return;
  g_exitReason = reason; g_trade.PositionClose(g_posTicket); g_state = DONE;
}

void OnTradeTransaction(const MqlTradeTransaction &trans, const MqlTradeRequest &request,
                        const MqlTradeResult &result) {
  if (trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
  ulong deal = trans.deal;
  if (!HistoryDealSelect(deal)) return;
  if ((long)HistoryDealGetInteger(deal, DEAL_MAGIC) != InpMagic) return;
  if ((ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal, DEAL_ENTRY) != DEAL_ENTRY_OUT) return;

  double exitPx=HistoryDealGetDouble(deal,DEAL_PRICE), profit=HistoryDealGetDouble(deal,DEAL_PROFIT);
  double swap=HistoryDealGetDouble(deal,DEAL_SWAP), comm=HistoryDealGetDouble(deal,DEAL_COMMISSION);
  double lots=HistoryDealGetDouble(deal,DEAL_VOLUME);
  ENUM_DEAL_REASON dr=(ENUM_DEAL_REASON)HistoryDealGetInteger(deal,DEAL_REASON);
  string reason=(dr==DEAL_REASON_SL)?"sl_hit":(dr==DEAL_REASON_TP)?"tp_hit":
                (g_exitReason!=""?g_exitReason:"expert");
  double rmult=(g_tR>0.0)?(((g_tDir>0)?(exitPx-g_tEntry):(g_tEntry-exitPx))/g_tR):0.0;

  SH_LedgerRow(g_ledger, 0, _Symbol, g_tDir,
               (datetime)((long)g_tOpen-(long)g_srvOffsetSec),
               (datetime)((long)TimeCurrent()-(long)g_srvOffsetSec),
               g_tEntry, g_tSL, g_tTP, lots, reason, profit, comm, swap, profit+swap+comm, rmult,
               g_tSwept, g_tSide, TargetModeStr(), g_tDepth);
  g_exitReason = "";
}

double OnTester() {
  double t = TesterStatistics(STAT_TRADES);
  return (t > 0.0) ? TesterStatistics(STAT_PROFIT)/t : 0.0;
}
