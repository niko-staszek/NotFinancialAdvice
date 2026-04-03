//+------------------------------------------------------------------+
//| CBS_Journal.mqh v1.0                                             |
//| Per-trade CSV logging to MQL5/Files/CBS_Journal.csv              |
//|                                                                  |
//| Logs entry and exit events with full trade details.              |
//| File is opened in append mode, header written once.              |
//+------------------------------------------------------------------+
#ifndef CBS_JOURNAL_MQH
#define CBS_JOURNAL_MQH

string g_journalPath = "CBS_Journal.csv";
bool   g_journalHeaderWritten = false;

//+------------------------------------------------------------------+
//| Write CSV header if not already written                           |
//+------------------------------------------------------------------+
void JournalWriteHeader()
{
   if(g_journalHeaderWritten)
      return;

   int fh = FileOpen(g_journalPath, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   if(fh == INVALID_HANDLE)
   {
      PrintFormat("[CBS Journal] Failed to open %s. Error: %d", g_journalPath, GetLastError());
      return;
   }

   // Check if file is empty (new file)
   if(FileSize(fh) == 0)
   {
      FileWrite(fh,
         "time_utc", "symbol", "slot", "event", "direction",
         "entry", "tp", "sl", "lot", "dist_pips",
         "close_price", "close_reason", "pips_result",
         "window_open", "deadline");
   }

   FileClose(fh);
   g_journalHeaderWritten = true;
}

//+------------------------------------------------------------------+
//| Log a trade entry event                                           |
//+------------------------------------------------------------------+
void JournalLogEntry(int slot_idx, string symbol, ENUM_ORDER_TYPE dir,
                      double entry, double tp, double sl, double lot,
                      double dist_pips, datetime window_open, datetime deadline)
{
   if(!EnableJournal)
      return;

   JournalWriteHeader();

   int fh = FileOpen(g_journalPath, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   if(fh == INVALID_HANDLE)
      return;

   FileSeek(fh, 0, SEEK_END);

   string dir_str = (dir == ORDER_TYPE_BUY) ? "BUY" : "SELL";

   FileWrite(fh,
      TimeToString(GetUTCTime(), TIME_DATE | TIME_SECONDS),    // time_utc
      symbol,                                                 // symbol
      g_slotNames[slot_idx],                                  // slot
      "ENTRY",                                                // event
      dir_str,                                                // direction
      DoubleToString(entry, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS)), // entry
      DoubleToString(tp, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS)),    // tp
      DoubleToString(sl, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS)),    // sl
      DoubleToString(lot, 2),                                 // lot
      DoubleToString(dist_pips, 1),                           // dist_pips
      "",                                                     // close_price (empty for entry)
      "",                                                     // close_reason (empty for entry)
      "",                                                     // pips_result (empty for entry)
      TimeToString(window_open, TIME_DATE | TIME_SECONDS),    // window_open
      TimeToString(deadline, TIME_DATE | TIME_SECONDS)        // deadline
   );

   FileClose(fh);
}

//+------------------------------------------------------------------+
//| Log a trade close event                                           |
//+------------------------------------------------------------------+
void JournalLogClose(int slot_idx, string symbol,
                      double close_price, string close_reason,
                      double pips_result)
{
   if(!EnableJournal)
      return;

   JournalWriteHeader();

   int fh = FileOpen(g_journalPath, FILE_READ | FILE_WRITE | FILE_CSV | FILE_ANSI, ',');
   if(fh == INVALID_HANDLE)
      return;

   FileSeek(fh, 0, SEEK_END);

   string dir_str = (g_slots[slot_idx].dir == ORDER_TYPE_BUY) ? "BUY" : "SELL";

   FileWrite(fh,
      TimeToString(GetUTCTime(), TIME_DATE | TIME_SECONDS),    // time_utc
      symbol,                                                 // symbol
      g_slotNames[slot_idx],                                  // slot
      "CLOSE",                                                // event
      dir_str,                                                // direction
      DoubleToString(g_slots[slot_idx].entry, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS)),
      DoubleToString(g_slots[slot_idx].tp, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS)),
      DoubleToString(g_slots[slot_idx].sl, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS)),
      "",                                                     // lot (from entry)
      "",                                                     // dist_pips (from entry)
      DoubleToString(close_price, (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS)),
      close_reason,
      DoubleToString(pips_result, 1),
      "",                                                     // window_open
      ""                                                      // deadline
   );

   FileClose(fh);
}

#endif // CBS_JOURNAL_MQH
