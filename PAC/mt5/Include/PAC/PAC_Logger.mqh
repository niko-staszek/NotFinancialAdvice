//+------------------------------------------------------------------+
//| PAC_Logger.mqh — 21-column trade ledger writer                    |
//| Byte-parity with Plan 4 hedgehog/proposer/pac/ledger.py           |
//| File mode: FILE_WRITE|FILE_CSV|FILE_ANSI, comma delimiter         |
//+------------------------------------------------------------------+
#property strict
#ifndef __PAC_LOGGER_MQH__
#define __PAC_LOGGER_MQH__

//+------------------------------------------------------------------+
//| One ledger row — mirrors ledger.py LedgerRow field order exactly. |
//| trade_id is a string to match Python (e.g. "T0001"); the engine   |
//| formats it before populating this struct.                          |
//+------------------------------------------------------------------+
struct LedgerEntryRow {
    string     trade_id;
    datetime   ts_signal;
    datetime   ts_open;
    datetime   ts_close;
    string     symbol;
    string     direction;          // matches ledger.py row.direction verbatim
    double     entry_price;
    double     sl_price;
    double     tp_price;
    double     exit_price;
    string     exit_reason;
    double     pnl_pips;
    double     pnl_money;
    double     r_multiple;
    string     setup_type;
    bool       direction_strict;
    string     mmd_alignment;
    string     d1_zone;
    string     confluence_type;
    double     lot_size;
    double     risk_pct;
};

struct LedgerWriter {
    int    handle;
};

//+------------------------------------------------------------------+
//| Format a UTC datetime to match Python datetime.isoformat() on a   |
//| tz-aware UTC datetime: "2024-01-15T08:30:00+00:00".               |
//|                                                                    |
//| NOTE (deviation from Plan 5 sketch): the plan suggested a trailing |
//| "Z", but engine.py stamps every ledger datetime as tz-aware UTC   |
//| via .replace(tzinfo=timezone.utc), and Python's isoformat() then  |
//| emits the "+00:00" offset — NOT "Z". To keep the CSV byte-identical|
//| to ledger.py we must emit "+00:00".                                |
//+------------------------------------------------------------------+
string FormatTimeISO(datetime t) {
    MqlDateTime m;
    TimeToStruct(t, m);
    return StringFormat("%04d-%02d-%02dT%02d:%02d:%02d+00:00",
                        m.year, m.mon, m.day, m.hour, m.min, m.sec);
}

//+------------------------------------------------------------------+
//| Open the ledger file (overwrite) and write the 21-column header.  |
//| FILE_CSV + comma delimiter makes FileWrite join args with "," and |
//| terminate each record with "\r\n" — matching Python csv.writer.   |
//+------------------------------------------------------------------+
bool Logger_Init(LedgerWriter &w, string path) {
    w.handle = FileOpen(path, FILE_WRITE|FILE_CSV|FILE_ANSI, ',');
    if (w.handle == INVALID_HANDLE) {
        PrintFormat("Logger_Init: FileOpen failed for %s (err=%d)", path, GetLastError());
        return false;
    }
    FileWrite(w.handle,
        "trade_id","ts_signal","ts_open","ts_close","symbol","direction",
        "entry_price","sl_price","tp_price","exit_price","exit_reason",
        "pnl_pips","pnl_money","r_multiple","setup_type","direction_strict",
        "mmd_alignment","d1_zone","confluence_type","lot_size","risk_pct");
    return true;
}

//+------------------------------------------------------------------+
//| Write one row. Column order + per-column formatting mirror        |
//| ledger.py TradeLedger.append():                                    |
//|   prices            -> 6 decimals                                  |
//|   pnl_pips          -> 1 decimal                                   |
//|   pnl_money         -> 2 decimals                                  |
//|   r_multiple        -> 2 decimals                                  |
//|   lot_size          -> 2 decimals                                  |
//|   risk_pct          -> 2 decimals                                  |
//|   direction_strict  -> "True"/"False" (Python str(bool) casing)   |
//+------------------------------------------------------------------+
void Logger_WriteRow(LedgerWriter &w, LedgerEntryRow &r) {
    FileWrite(w.handle,
        r.trade_id,
        FormatTimeISO(r.ts_signal),
        FormatTimeISO(r.ts_open),
        FormatTimeISO(r.ts_close),
        r.symbol,
        r.direction,
        DoubleToString(r.entry_price, 6),
        DoubleToString(r.sl_price, 6),
        DoubleToString(r.tp_price, 6),
        DoubleToString(r.exit_price, 6),
        r.exit_reason,
        DoubleToString(r.pnl_pips, 1),
        DoubleToString(r.pnl_money, 2),
        DoubleToString(r.r_multiple, 2),
        r.setup_type,
        r.direction_strict ? "True" : "False",
        r.mmd_alignment,
        r.d1_zone,
        r.confluence_type,
        DoubleToString(r.lot_size, 2),
        DoubleToString(r.risk_pct, 2));
}

//+------------------------------------------------------------------+
//| Convenience wrappers — identical 21-column layout, they only set  |
//| exit_reason for the caller (mirrors ledger.py write_partial /     |
//| the engine's final-exit row).                                      |
//+------------------------------------------------------------------+
void Logger_WriteEntry(LedgerWriter &w, LedgerEntryRow &r) {
    Logger_WriteRow(w, r);
}

void Logger_WritePartial(LedgerWriter &w, LedgerEntryRow &r) {
    r.exit_reason = "partial";
    Logger_WriteRow(w, r);
}

void Logger_WriteExit(LedgerWriter &w, LedgerEntryRow &r) {
    // Final close — caller sets exit_reason (e.g. "tp", "sl", "trailing").
    Logger_WriteRow(w, r);
}

void Logger_Close(LedgerWriter &w) {
    if (w.handle != INVALID_HANDLE) {
        FileClose(w.handle);
        w.handle = INVALID_HANDLE;
    }
}

#endif // __PAC_LOGGER_MQH__
