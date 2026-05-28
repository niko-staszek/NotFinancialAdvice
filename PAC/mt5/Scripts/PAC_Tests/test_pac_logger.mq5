//+------------------------------------------------------------------+
//| test_pac_logger.mq5                                               |
//| Verifies PAC_Logger.mqh emits byte-identical CSV to Plan 4        |
//| ledger.py: 21-column header, exact per-column formatting,         |
//| CRLF line endings, no BOM, isoformat "+00:00" timestamps.         |
//+------------------------------------------------------------------+
#property strict
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\PAC\\PAC_Logger.mqh"

void OnStart() {
    string path = "PAC_Tests\\out\\test_ledger.csv";

    LedgerWriter w;
    ASSERT_TRUE(Logger_Init(w, path), "Logger_Init_succeeds");

    // Mirror the exact row used to capture the ledger.py reference bytes.
    LedgerEntryRow r;
    r.trade_id         = "T1";
    r.ts_signal        = D'2024.01.15 08:30:00';
    r.ts_open          = D'2024.01.15 08:35:00';
    r.ts_close         = D'2024.01.15 09:00:00';
    r.symbol           = "EURUSD";
    r.direction        = "long";
    r.entry_price      = 1.085;
    r.sl_price         = 1.082;
    r.tp_price         = 1.091;
    r.exit_price       = 1.0905;
    r.exit_reason      = "tp";
    r.pnl_pips         = 55.0;
    r.pnl_money        = 123.45;
    r.r_multiple       = 1.83;
    r.setup_type       = "trap";
    r.direction_strict = true;
    r.mmd_alignment    = "confirmed";
    r.d1_zone          = "demand";
    r.confluence_type  = "fib_cluster";
    r.lot_size         = 0.1;
    r.risk_pct         = 1.0;

    Logger_WriteRow(w, r);
    Logger_Close(w);

    // Re-open in binary to inspect raw bytes.
    int h = FileOpen(path, FILE_READ|FILE_BIN|FILE_ANSI);
    ASSERT_TRUE(h != INVALID_HANDLE, "Reopen_for_byte_inspection");
    string content = "";
    while (!FileIsEnding(h)) content += CharToString((uchar)FileReadInteger(h, CHAR_VALUE));
    FileClose(h);

    // --- Header: byte-exact canonical 21-column order ---
    string header = "trade_id,ts_signal,ts_open,ts_close,symbol,direction,"
                    "entry_price,sl_price,tp_price,exit_price,exit_reason,"
                    "pnl_pips,pnl_money,r_multiple,setup_type,direction_strict,"
                    "mmd_alignment,d1_zone,confluence_type,lot_size,risk_pct";
    ASSERT_TRUE(StringFind(content, header) == 0, "Header_byte_exact_at_offset_0");

    // --- CRLF line endings, no lone LF before a CR ---
    ASSERT_TRUE(StringFind(content, "\r\n") >= 0, "Has_CRLF_line_endings");

    // --- No UTF-8 BOM ---
    ASSERT_FALSE(StringFind(content, "\xEF\xBB\xBF") == 0, "No_BOM");

    // --- Data row: byte-exact against ledger.py reference ---
    string data_row = "T1,2024-01-15T08:30:00+00:00,2024-01-15T08:35:00+00:00,"
                      "2024-01-15T09:00:00+00:00,EURUSD,long,1.085000,1.082000,"
                      "1.091000,1.090500,tp,55.0,123.45,1.83,trap,True,confirmed,"
                      "demand,fib_cluster,0.10,1.00";
    ASSERT_TRUE(StringFind(content, data_row) > 0, "Data_row_byte_exact");

    // --- Full file equality: header + CRLF + row + CRLF ---
    string expected = header + "\r\n" + data_row + "\r\n";
    ASSERT_STR_EQ(content, expected, "Full_file_byte_identical_to_ledger_py");
}
