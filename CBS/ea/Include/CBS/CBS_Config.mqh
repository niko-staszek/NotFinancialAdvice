//+------------------------------------------------------------------+
//| CBS_Config.mqh v1.0                                              |
//| Input parameters, enums, constants, instrument auto-detection    |
//| Matches Python INSTRUMENTS dict from 18_best_targets.py L66-77  |
//+------------------------------------------------------------------+
#ifndef CBS_CONFIG_MQH
#define CBS_CONFIG_MQH

//+------------------------------------------------------------------+
//| Enums                                                             |
//+------------------------------------------------------------------+
enum ENUM_SL_MODE
{
   SL_TIER    = 0,   // Tier: forex <=35pip->3x, 35-100->1.5x, >100->1x; standard 1x
   SL_1_1     = 1,   // Fixed 1:1  (SL = target distance)
   SL_1_1_5   = 2,   // Fixed 1:1.5
   SL_1_2     = 3    // Fixed 1:2
};

enum ENUM_LOT_MODE
{
   LOT_FIXED       = 0,  // Fixed lot (BaseLot × distance tier)
   LOT_RISK_PERCENT = 1  // Risk % of balance per trade
};

//+------------------------------------------------------------------+
//| Slot Inputs: Offset (24h window, once per day)                    |
//+------------------------------------------------------------------+
input group "=== Offset Slot ==="
input bool           Off_Enable        = true;    // Enable offset slot
input int            Off_StartHourUTC  = 11;      // UTC hour of 24h window start (0-12)
input bool           Off_UseEMA        = false;   // EMA21 M15 trend filter
input bool           Off_UseH4         = true;    // H4 EMA21 trend filter
input bool           Off_UseCLU        = false;   // Fibonacci cluster blocker
input bool           Off_UseLLR        = false;   // Line of Least Resistance filter
input ENUM_SL_MODE   Off_SLMode        = SL_TIER; // Stop loss mode
input double         Off_BaseLot       = 0.01;    // Base lot size

//+------------------------------------------------------------------+
//| Slot Inputs: Intraday #1 (primary session window)                 |
//+------------------------------------------------------------------+
input group "=== Intraday Slot 1 ==="
input bool           Intra1_Enable     = true;    // Enable intraday slot 1
input int            Intra1_StartHour  = 12;      // UTC session start hour
input int            Intra1_DurationH  = 4;       // Session duration (hours)
input bool           Intra1_UseEMA     = false;   // EMA21 M15 filter
input bool           Intra1_UseH4      = false;   // H4 trend filter
input bool           Intra1_UseCLU     = true;    // CLU cluster blocker
input bool           Intra1_UseLLR     = false;   // LLR filter
input ENUM_SL_MODE   Intra1_SLMode     = SL_TIER; // Stop loss mode
input double         Intra1_BaseLot    = 0.01;    // Base lot size

//+------------------------------------------------------------------+
//| Slot Inputs: Intraday #2 (second non-overlapping window)          |
//+------------------------------------------------------------------+
input group "=== Intraday Slot 2 ==="
input bool           Intra2_Enable     = true;    // Enable intraday slot 2
input int            Intra2_StartHour  = 9;       // UTC session start hour
input int            Intra2_DurationH  = 3;       // Session duration (hours)
input bool           Intra2_UseEMA     = false;   // EMA21 M15 filter
input bool           Intra2_UseH4      = false;   // H4 trend filter
input bool           Intra2_UseCLU     = true;    // CLU cluster blocker
input bool           Intra2_UseLLR     = false;   // LLR filter
input ENUM_SL_MODE   Intra2_SLMode     = SL_TIER; // Stop loss mode
input double         Intra2_BaseLot    = 0.01;    // Base lot size

//+------------------------------------------------------------------+
//| Slot Inputs: Intraday #3 (overnight/Asian session)                |
//+------------------------------------------------------------------+
input group "=== Intraday Slot 3 ==="
input bool           Intra3_Enable     = true;    // Enable intraday slot 3
input int            Intra3_StartHour  = 22;      // UTC session start hour
input int            Intra3_DurationH  = 6;       // Session duration (hours)
input bool           Intra3_UseEMA     = false;   // EMA21 M15 filter
input bool           Intra3_UseH4      = false;   // H4 trend filter
input bool           Intra3_UseCLU     = true;    // CLU cluster blocker
input bool           Intra3_UseLLR     = false;   // LLR filter
input ENUM_SL_MODE   Intra3_SLMode     = SL_TIER; // Stop loss mode
input double         Intra3_BaseLot    = 0.01;    // Base lot size

//+------------------------------------------------------------------+
//| Distance-based lot sizing                                         |
//| Close targets settle ~40-60% faster -> higher lot multiplier      |
//| Boundaries are instrument-specific (set via .set file)            |
//+------------------------------------------------------------------+
input group "=== Distance Lot Tiers ==="
input bool           DistTier_Enable   = true;    // Enable distance-based lot sizing
input double         DistTier1Pips     = 36.0;    // Close target threshold (pips)
input double         DistTier1Mult     = 2.0;     // Lot multiplier for close targets
input double         DistTier2Pips     = 47.0;    // Medium target threshold (pips)
input double         DistTier2Mult     = 1.0;     // Lot multiplier for medium targets
input double         DistFarMult       = 0.5;     // Lot multiplier for far targets

//+------------------------------------------------------------------+
//| Lot Sizing Mode                                                   |
//+------------------------------------------------------------------+
input group "=== Lot Sizing ==="
input ENUM_LOT_MODE  LotMode           = LOT_FIXED; // Lot sizing mode
input double         RiskPercent       = 0.2;    // Risk per trade (% of balance). Used when LotMode=Risk%
input double         MaxLotSize        = 1.0;    // Max lot cap (safety)

//+------------------------------------------------------------------+
//| Risk Management                                                   |
//+------------------------------------------------------------------+
input group "=== Risk ==="
input int            MagicBase         = 101000;  // Off=+1, Intra1=+2, Intra2=+3, Intra3=+4
input double         MaxSpreadPips     = 5.0;     // Skip entry if spread exceeds this
input int            SlippagePips      = 2;       // Max slippage for market orders
input double         DailyMaxLossPct   = 5.0;     // Daily loss limit (% of balance)

//+------------------------------------------------------------------+
//| Misc                                                              |
//+------------------------------------------------------------------+
input group "=== Misc ==="
input int            BrokerGMTOffset   = 2;       // Broker server GMT offset (hours). 5ers=2, most EU brokers=2 winter/3 summer
input bool           EnableJournal     = true;    // Write per-trade CSV log
input bool           DebugMode         = false;   // Print detailed debug info

//+------------------------------------------------------------------+
//| Constants                                                         |
//+------------------------------------------------------------------+
#define CBS_TIMER_SEC     60     // OnTimer interval (seconds)
#define CBS_MAX_HOLD_H    18     // Max hold hours before timeout close
#define CBS_N_SLOTS       4      // Off + Intra1 + Intra2 + Intra3

//+------------------------------------------------------------------+
//| Instrument Constants                                              |
//| Matches Python: (pip_size, settle_tol, spread, tier_mode)         |
//| Plus cluster_size_pips and min_distance_pips from EA_PARAMS_REF   |
//+------------------------------------------------------------------+
struct InstrumentConfig
{
   double pip_size;
   int    settle_tol;        // pips
   double default_spread;    // pips (fallback if live spread unavailable)
   bool   is_forex;          // true = forex tier mode, false = standard 1x
   double cluster_size_pips; // CLU: levels within this distance = cluster
   double min_distance_pips; // CLU: target must be at least this far from entry
};

//+------------------------------------------------------------------+
//| Auto-detect instrument config from symbol name                    |
//| Strips common broker suffixes (.pro, .raw, .ecn, etc.)           |
//+------------------------------------------------------------------+
InstrumentConfig DetectInstrumentConfig(string symbol)
{
   InstrumentConfig cfg;
   // Default: forex
   cfg.pip_size          = 0.0001;
   cfg.settle_tol        = 5;
   cfg.default_spread    = 1.5;
   cfg.is_forex          = true;
   cfg.cluster_size_pips = 5.0;
   cfg.min_distance_pips = 15.0;

   // Clean symbol: strip suffixes
   string clean = symbol;
   string suffixes[] = {".pro", ".raw", ".ecn", ".std", ".stp", ".m", ".z", "."};
   for(int i = 0; i < ArraySize(suffixes); i++)
   {
      int pos = StringFind(clean, suffixes[i]);
      if(pos > 0)
         clean = StringSubstr(clean, 0, pos);
   }
   StringToUpper(clean);

   // Match known instruments
   if(clean == "EURUSD")
   {
      cfg.pip_size = 0.0001; cfg.settle_tol = 5; cfg.default_spread = 1.5;
      cfg.is_forex = true; cfg.cluster_size_pips = 5; cfg.min_distance_pips = 15;
   }
   else if(clean == "GBPUSD")
   {
      cfg.pip_size = 0.0001; cfg.settle_tol = 5; cfg.default_spread = 1.5;
      cfg.is_forex = true; cfg.cluster_size_pips = 5; cfg.min_distance_pips = 15;
   }
   else if(clean == "USDCAD")
   {
      cfg.pip_size = 0.0001; cfg.settle_tol = 5; cfg.default_spread = 2.0;
      cfg.is_forex = true; cfg.cluster_size_pips = 5; cfg.min_distance_pips = 15;
   }
   else if(clean == "USDJPY")
   {
      cfg.pip_size = 0.01; cfg.settle_tol = 5; cfg.default_spread = 1.5;
      cfg.is_forex = true; cfg.cluster_size_pips = 5; cfg.min_distance_pips = 15;
   }
   else if(clean == "USDCHF")
   {
      cfg.pip_size = 0.0001; cfg.settle_tol = 5; cfg.default_spread = 1.5;
      cfg.is_forex = true; cfg.cluster_size_pips = 5; cfg.min_distance_pips = 15;
   }
   else if(clean == "AUDUSD")
   {
      cfg.pip_size = 0.0001; cfg.settle_tol = 5; cfg.default_spread = 1.5;
      cfg.is_forex = true; cfg.cluster_size_pips = 5; cfg.min_distance_pips = 15;
   }
   else if(clean == "NZDUSD")
   {
      cfg.pip_size = 0.0001; cfg.settle_tol = 5; cfg.default_spread = 1.5;
      cfg.is_forex = true; cfg.cluster_size_pips = 5; cfg.min_distance_pips = 15;
   }
   else if(clean == "XAUUSD")
   {
      cfg.pip_size = 0.1; cfg.settle_tol = 15; cfg.default_spread = 25.0;
      cfg.is_forex = false; cfg.cluster_size_pips = 15; cfg.min_distance_pips = 50;
   }
   else if(clean == "BTCUSD")
   {
      cfg.pip_size = 1.0; cfg.settle_tol = 10; cfg.default_spread = 50.0;
      cfg.is_forex = false; cfg.cluster_size_pips = 10; cfg.min_distance_pips = 50;
   }
   else if(clean == "ETHUSD")
   {
      cfg.pip_size = 1.0; cfg.settle_tol = 5; cfg.default_spread = 15.0;
      cfg.is_forex = false; cfg.cluster_size_pips = 5; cfg.min_distance_pips = 30;
   }
   else
   {
      // Try to auto-detect pip_size from digits
      int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
      if(digits == 5 || digits == 3)
         cfg.pip_size = SymbolInfoDouble(symbol, SYMBOL_POINT) * 10;
      else
         cfg.pip_size = SymbolInfoDouble(symbol, SYMBOL_POINT);

      // For unknown instruments: use non-forex mode
      cfg.is_forex = false;
      PrintFormat("[CBS] Unknown symbol '%s' (cleaned: '%s'). Using defaults.", symbol, clean);
   }

   return cfg;
}

//+------------------------------------------------------------------+
//| Daily loss guard                                                  |
//+------------------------------------------------------------------+
//+------------------------------------------------------------------+
//| Market hours check — skip weekends                                |
//+------------------------------------------------------------------+
bool IsMarketOpen()
{
   MqlDateTime dt;
   TimeCurrent(dt);
   // Saturday=6, Sunday=0
   if(dt.day_of_week == 0 || dt.day_of_week == 6)
      return false;
   // Also skip Friday after 22:00 broker time (market closes)
   if(dt.day_of_week == 5 && dt.hour >= 22)
      return false;
   return true;
}

double g_dailyStartBalance = 0.0;
bool   g_dailyLocked       = false;

bool IsDailyLossExceeded()
{
   MqlDateTime dt;
   TimeCurrent(dt);
   static int lastDay = -1;

   if(dt.day != lastDay)
   {
      lastDay = dt.day;
      g_dailyStartBalance = AccountInfoDouble(ACCOUNT_BALANCE);
      g_dailyLocked = false;
   }

   if(g_dailyLocked)
      return true;

   double dd = (g_dailyStartBalance - AccountInfoDouble(ACCOUNT_BALANCE))
               / g_dailyStartBalance * 100.0;

   if(dd >= DailyMaxLossPct)
   {
      g_dailyLocked = true;
      PrintFormat("[CBS] Daily loss limit reached (%.1f%% >= %.1f%%). Trading locked.", dd, DailyMaxLossPct);
      return true;
   }

   return false;
}

#endif // CBS_CONFIG_MQH
