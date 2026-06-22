//+------------------------------------------------------------------+
//|                                           ScalperProReconEA.mq5   |
//|   Self-contained MT5 Expert Advisor implementing the SPZ          |
//|   reconstruction (v3.2 logic) of "Scalper Pro v4.1 [ZynAlgo]".    |
//|                                                                  |
//|   IMPORTANT: this is OUR RECONSTRUCTION, not the original         |
//|   indicator. Measured ~PF 1.5-2 GROSS of costs, OOS unvalidated,  |
//|   partly trend-exposure. NOT the original's claimed PF 6.         |
//|   -> Forward-test on DEMO and verify net-of-cost edge before any  |
//|      real capital. Live trading is blocked unless explicitly      |
//|      enabled (AllowLiveTrading=true). See SPZ/NOTES.md.            |
//|                                                                  |
//|   Attach ONE instance per symbol on its recommended timeframe:    |
//|     XAUUSD -> H1 ,  BTCUSD -> H4   (Intraday EMAs 13/34).          |
//+------------------------------------------------------------------+
#property copyright "NotFinancialAdvice / SPZ reconstruction"
#property version   "1.00"
#property description "SPZ reconstruction auto-trader (DEMO-first). Not the original Scalper Pro."
#include <Trade/Trade.mqh>

input group "=== Strategy (recon v3.2, Intraday default) ==="
input int    EmaFastLen    = 13;       // Intraday fast EMA (Scalp 9 / Swing 21)
input int    EmaSlowLen    = 34;       // Intraday slow EMA (Scalp 21 / Swing 50)
input int    SlopeLen      = 10;       // bars for slow-EMA slope (regime)
input double FlatBand      = 0.6;      // |slope|/ATR below this => SIDEWAY (no trade)
input int    AdxLen        = 14;
input double AdxStrongTh   = 20.0;     // ADX >= this contributes to score
input int    RsiLen        = 14;
input int    AtrLen        = 14;
input int    MinScore      = 60;       // score (0-100) gate
input int    CooldownBars  = 25;       // min bars between entries (anti-flip)
input bool   ReverseOnOpposite = true; // flip on a cooled opposite signal
input ENUM_TIMEFRAMES HtfTimeframe = PERIOD_CURRENT; // PERIOD_CURRENT = auto (H1->H4, H4->D1)

input group "=== Session (broker/server time) ==="
input bool   UseSession    = true;
input int    SessStartHour = 7;
input int    SessEndHour    = 18;

input group "=== Risk / SL / TP ==="
input double RiskPctPerTrade = 0.625;  // prop-safe combined sizing (XAU+BTC, 2x buffer)
input double SlAtrMult       = 2.8;    // SL distance = SlAtrMult * ATR  (= 1R)
input double TpRR            = 3.0;     // TP = +3R (TP3)

input group "=== Safety ==="
input bool   AllowLiveTrading = false; // MUST be true to trade a REAL-money account
input long   MagicNumber      = 920622;
input int    SlippagePoints   = 30;

CTrade        trade;
int           hEmaF, hEmaS, hHtf, hAdx, hRsi, hAtr;
datetime      lastBarTime  = 0;
datetime      lastEntryBar = 0;
ENUM_TIMEFRAMES g_htf;

//+------------------------------------------------------------------+
ENUM_TIMEFRAMES AutoHtf(ENUM_TIMEFRAMES tf)
{
   if(HtfTimeframe != PERIOD_CURRENT) return HtfTimeframe;
   switch(tf)
   {
      case PERIOD_M1:
      case PERIOD_M5:   return PERIOD_H1;
      case PERIOD_M15:
      case PERIOD_M30:  return PERIOD_H4;
      case PERIOD_H1:   return PERIOD_H4;
      case PERIOD_H4:   return PERIOD_D1;
      case PERIOD_D1:   return PERIOD_W1;
      default:          return PERIOD_W1;
   }
}

//+------------------------------------------------------------------+
int OnInit()
{
   g_htf = AutoHtf((ENUM_TIMEFRAMES)_Period);
   hEmaF = iMA(_Symbol, _Period, EmaFastLen, 0, MODE_EMA, PRICE_CLOSE);
   hEmaS = iMA(_Symbol, _Period, EmaSlowLen, 0, MODE_EMA, PRICE_CLOSE);
   hHtf  = iMA(_Symbol, g_htf,   EmaSlowLen, 0, MODE_EMA, PRICE_CLOSE);
   hAdx  = iADX(_Symbol, _Period, AdxLen);
   hRsi  = iRSI(_Symbol, _Period, RsiLen, PRICE_CLOSE);
   hAtr  = iATR(_Symbol, _Period, AtrLen);
   if(hEmaF==INVALID_HANDLE || hEmaS==INVALID_HANDLE || hHtf==INVALID_HANDLE ||
      hAdx==INVALID_HANDLE || hRsi==INVALID_HANDLE || hAtr==INVALID_HANDLE)
   {
      Print("ScalperProReconEA: failed to create indicator handles");
      return(INIT_FAILED);
   }
   trade.SetExpertMagicNumber(MagicNumber);
   trade.SetDeviationInPoints(SlippagePoints);
   trade.SetTypeFillingBySymbol(_Symbol);

   long mode = AccountInfoInteger(ACCOUNT_TRADE_MODE);
   if(mode == ACCOUNT_TRADE_MODE_REAL && !AllowLiveTrading)
      Alert("ScalperProReconEA: REAL account + AllowLiveTrading=false -> TRADING DISABLED. ",
            "This is the unvalidated reconstruction; forward-test on demo first.");
   Print("ScalperProReconEA init: ", _Symbol, " ", EnumToString((ENUM_TIMEFRAMES)_Period),
         " HTF=", EnumToString(g_htf), " mode=", mode==ACCOUNT_TRADE_MODE_REAL?"REAL":"DEMO/CONTEST");
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason)
{
   IndicatorRelease(hEmaF); IndicatorRelease(hEmaS); IndicatorRelease(hHtf);
   IndicatorRelease(hAdx);  IndicatorRelease(hRsi);  IndicatorRelease(hAtr);
}

//+------------------------------------------------------------------+
bool TradingAllowed()
{
   long mode = AccountInfoInteger(ACCOUNT_TRADE_MODE);
   if(mode == ACCOUNT_TRADE_MODE_REAL && !AllowLiveTrading) return(false);
   if(!MQLInfoInteger(MQL_TRADE_ALLOWED))                   return(false);
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))         return(false);
   return(true);
}

double Buf(int handle, int shift)
{
   double b[];
   if(CopyBuffer(handle, 0, shift, 1, b) < 1) return(EMPTY_VALUE);
   return(b[0]);
}

int PosDir()  // 0 flat, 1 long, -1 short for THIS symbol+magic (netting accounts)
{
   if(PositionSelect(_Symbol) && PositionGetInteger(POSITION_MAGIC) == MagicNumber)
      return(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? 1 : -1);
   return(0);
}

double CalcLots(double slPriceDist)
{
   double eq        = AccountInfoDouble(ACCOUNT_EQUITY);
   double riskMoney = eq * RiskPctPerTrade / 100.0;
   double tickVal   = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickSize <= 0 || tickVal <= 0 || slPriceDist <= 0) return(0.0);
   double lossPerLot = slPriceDist / tickSize * tickVal;
   double lots       = riskMoney / lossPerLot;
   double minL = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxL = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   if(step <= 0) step = 0.01;
   lots = MathFloor(lots / step) * step;
   lots = MathMax(minL, MathMin(maxL, lots));
   return(lots);
}

double Nz(double x) { return(NormalizeDouble(x, _Digits)); }

//+------------------------------------------------------------------+
void OnTick()
{
   datetime bt = iTime(_Symbol, _Period, 0);
   if(bt == lastBarTime) return;          // process once per new bar
   lastBarTime = bt;
   if(Bars(_Symbol, _Period) < EmaSlowLen + SlopeLen + 5) return;

   // confirmed (closed) bar = shift 1
   double emaS     = Buf(hEmaS, 1);
   double emaSprev = Buf(hEmaS, 1 + SlopeLen);
   double htfEma   = Buf(hHtf, 1);
   double adx      = Buf(hAdx, 1);        // iADX buffer 0 = ADX main line
   double rsi      = Buf(hRsi, 1);
   double atr      = Buf(hAtr, 1);
   double closed   = iClose(_Symbol, _Period, 1);
   if(emaS==EMPTY_VALUE || emaSprev==EMPTY_VALUE || htfEma==EMPTY_VALUE ||
      adx==EMPTY_VALUE || rsi==EMPTY_VALUE || atr==EMPTY_VALUE || atr<=0.0) return;

   double slope   = (emaS - emaSprev) / atr;
   bool   mBull   = slope >  FlatBand;
   bool   mBear   = slope < -FlatBand;
   bool   htfUp   = closed > htfEma;
   bool   rsiBull = rsi > 50.0;
   bool   adxStr  = adx >= AdxStrongTh;
   int    bull    = (mBull?1:0) + (htfUp?1:0) + (rsiBull?1:0);
   int    bear    = (mBear?1:0) + (htfUp?0:1) + (rsiBull?0:1);
   int    score   = (int)MathMin(100, MathMax(bull, bear) * 25 + (adxStr ? 25 : 0));

   MqlDateTime mt; TimeToStruct(bt, mt);
   bool inSess = !UseSession || (mt.hour >= SessStartHour && mt.hour < SessEndHour);

   int  barsSince  = (lastEntryBar > 0) ? (int)((bt - lastEntryBar) / PeriodSeconds(_Period)) : 1000000;
   bool cooldownOk = barsSince >= CooldownBars;

   bool sigLong  = inSess && score >= MinScore && bull >= 2 && mBull;
   bool sigShort = inSess && score >= MinScore && bear >= 2 && mBear;

   if(!TradingAllowed()) return;
   int dir = PosDir();

   // reverse on a cooled opposite signal (TP/SL otherwise handled broker-side)
   if(ReverseOnOpposite && dir == 1 && sigShort && cooldownOk) { trade.PositionClose(_Symbol); dir = 0; }
   else if(ReverseOnOpposite && dir == -1 && sigLong && cooldownOk) { trade.PositionClose(_Symbol); dir = 0; }

   if(dir != 0) return;            // already in a position
   if(!cooldownOk) return;

   double risk = SlAtrMult * atr;  // 1R in price
   if(sigLong)
   {
      double px = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      double lots = CalcLots(risk);
      if(lots > 0 && trade.Buy(lots, _Symbol, px, Nz(px - risk), Nz(px + TpRR*risk), "SPZ recon long"))
         lastEntryBar = bt;
   }
   else if(sigShort)
   {
      double px = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double lots = CalcLots(risk);
      if(lots > 0 && trade.Sell(lots, _Symbol, px, Nz(px + risk), Nz(px - TpRR*risk), "SPZ recon short"))
         lastEntryBar = bt;
   }
}

//+------------------------------------------------------------------+
//| Strategy-Tester summary -> Common\Files\SPZ\result_<symbol>.txt  |
//+------------------------------------------------------------------+
double OnTester()
{
   double pf     = TesterStatistics(STAT_PROFIT_FACTOR);
   double net    = TesterStatistics(STAT_PROFIT);
   double trades = TesterStatistics(STAT_TRADES);
   double wins   = TesterStatistics(STAT_PROFIT_TRADES);
   double losses = TesterStatistics(STAT_LOSS_TRADES);
   double ddmon  = TesterStatistics(STAT_EQUITY_DD);
   double ddpct  = TesterStatistics(STAT_EQUITYDD_PERCENT);
   double expR   = TesterStatistics(STAT_EXPECTED_PAYOFF);
   string s = StringFormat("symbol=%s tf=%s pf=%.2f net=%.2f ddmoney=%.2f ddpct=%.2f trades=%.0f wins=%.0f losses=%.0f expPayoff=%.2f",
                           _Symbol, EnumToString((ENUM_TIMEFRAMES)_Period), pf, net, ddmon, ddpct, trades, wins, losses, expR);
   int h = FileOpen("SPZ\\result_" + _Symbol + ".txt", FILE_WRITE | FILE_TXT | FILE_COMMON);
   if(h != INVALID_HANDLE) { FileWrite(h, s); FileClose(h); }
   Print("RESULT ", s);
   return(net);
}
//+------------------------------------------------------------------+
