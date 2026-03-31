//+------------------------------------------------------------------+
//| CBS_DataExport.mq5 — Export OHLC history to CSV                  |
//| Drop on any chart → exports M15, H1, H4, D1 for that symbol     |
//| Files go to: MQL5/Files/CBS_DATA/<SYMBOL>/                       |
//+------------------------------------------------------------------+
#property copyright "CBS"
#property version   "1.000"
#property script_show_inputs

//--- Inputs
input int    YearsBack   = 3;         // How many years of history to export
input bool   Export_M5   = true;       // Export M5 data
input bool   Export_M15  = true;       // Export M15 data
input bool   Export_H1   = true;       // Export H1 data
input bool   Export_H4   = true;       // Export H4 data
input bool   Export_D1   = true;       // Export D1 data
input string SubFolder   = "CBS_DATA"; // Subfolder in MQL5/Files/

//+------------------------------------------------------------------+
void OnStart()
{
   string symbol = _Symbol;
   string cleanSymbol = CleanSymbolName(symbol);

   datetime startDate = TimeCurrent() - YearsBack * 365 * 86400;
   datetime endDate   = TimeCurrent();

   Print("CBS DataExport: ", symbol, " (clean: ", cleanSymbol, ")");
   Print("  Range: ", TimeToString(startDate), " → ", TimeToString(endDate));

   int exported = 0;

   if(Export_M5)  exported += ExportTimeframe(symbol, cleanSymbol, PERIOD_M5,  "M5",  startDate, endDate);
   if(Export_M15) exported += ExportTimeframe(symbol, cleanSymbol, PERIOD_M15, "M15", startDate, endDate);
   if(Export_H1)  exported += ExportTimeframe(symbol, cleanSymbol, PERIOD_H1,  "H1",  startDate, endDate);
   if(Export_H4)  exported += ExportTimeframe(symbol, cleanSymbol, PERIOD_H4,  "H4",  startDate, endDate);
   if(Export_D1)  exported += ExportTimeframe(symbol, cleanSymbol, PERIOD_D1,  "D1",  startDate, endDate);

   // Export spread info
   ExportSpread(symbol, cleanSymbol);

   string msg = StringFormat("CBS DataExport complete: %s\nExported %d files\nLocation: MQL5\\Files\\%s\\%s\\",
                              cleanSymbol, exported, SubFolder, cleanSymbol);
   Alert(msg);
   Print(msg);
}

//+------------------------------------------------------------------+
void ExportSpread(string symbol, string cleanSymbol)
{
   string file = SubFolder + "\\" + "spreads.csv";

   int handle = FileOpen(file, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   if(handle == INVALID_HANDLE)
   {
      Print("  [WARN] Cannot write spreads.csv, error: ", GetLastError());
      return;
   }

   FileSeek(handle, 0, SEEK_END);

   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   int spreadPoints = (int)SymbolInfoInteger(symbol, SYMBOL_SPREAD);
   double point = SymbolInfoDouble(symbol, SYMBOL_POINT);

   // Convert points to pips
   double pipMultiplier = 1.0;
   if(digits == 5 || digits == 3)
      pipMultiplier = 10.0;

   double spreadPips = spreadPoints / pipMultiplier;

   FileWrite(handle, cleanSymbol, DoubleToString(spreadPips, 1));
   FileClose(handle);

   Print("  Spread for ", cleanSymbol, ": ", DoubleToString(spreadPips, 1),
         " pips (", IntegerToString(spreadPoints), " points, ",
         IntegerToString(digits), " digits)");
}

//+------------------------------------------------------------------+
int ExportTimeframe(string symbol, string cleanSymbol, ENUM_TIMEFRAMES tf,
                    string tfName, datetime startDate, datetime endDate)
{
   MqlRates rates[];
   ArraySetAsSeries(rates, false);

   int copied = CopyRates(symbol, tf, startDate, endDate, rates);
   if(copied <= 0)
   {
      Print("  [WARN] No ", tfName, " data for ", symbol, " Error: ", GetLastError());
      return 0;
   }

   string dir  = SubFolder + "\\" + cleanSymbol;
   string file = dir + "\\" + cleanSymbol + "_" + tfName + ".csv";

   int handle = FileOpen(file, FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   if(handle == INVALID_HANDLE)
   {
      Print("  [ERROR] Cannot create file: ", file, " Error: ", GetLastError());
      return 0;
   }

   int digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);

   // Header
   FileWrite(handle, "datetime", "Open", "High", "Low", "Close", "Volume");

   for(int i = 0; i < copied; i++)
   {
      string dt = TimeToString(rates[i].time, TIME_DATE | TIME_SECONDS);
      StringReplace(dt, ".", "-");

      FileWrite(handle, dt,
                DoubleToString(rates[i].open,  digits),
                DoubleToString(rates[i].high,  digits),
                DoubleToString(rates[i].low,   digits),
                DoubleToString(rates[i].close, digits),
                IntegerToString(rates[i].tick_volume));
   }

   FileClose(handle);
   Print("  Exported ", tfName, ": ", copied, " bars → ", file);
   return 1;
}

//+------------------------------------------------------------------+
string CleanSymbolName(string sym)
{
   string clean = sym;
   string suffixes[] = {".pro", ".raw", ".ecn", ".std", "_SB", "m", ".i", ".s"};

   for(int i = 0; i < ArraySize(suffixes); i++)
   {
      int pos = StringFind(clean, suffixes[i]);
      if(pos > 4 && pos == StringLen(clean) - StringLen(suffixes[i]))
      {
         clean = StringSubstr(clean, 0, pos);
         break;
      }
   }
   return clean;
}
//+------------------------------------------------------------------+
