//+------------------------------------------------------------------+
//| test_pac_atr.mq5                                                  |
//+------------------------------------------------------------------+
#property strict
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\PAC\\PAC_ATR.mqh"

void OnStart() {
    if (!ATR_Init("EURUSD", PERIOD_M5, 20)) {
        EMIT_FAIL("ATR_Init_EURUSD_M5", "true", "init_failed");
        return;
    }
    EMIT_PASS("ATR_Init_EURUSD_M5");

    // Wait for indicator to compute (CopyBuffer returns 0 if not ready)
    int retries = 10;
    double v = 0.0;
    while (retries-- > 0) {
        v = ATR_Value(1);   // bar 1 = most recently closed
        if (v > 0) break;
        Sleep(200);
    }

    // EURUSD M5 ATR(20) typically in [0.00005, 0.001] range
    ASSERT_TRUE(v > 0.00001 && v < 0.01, "ATR_Value_EURUSD_in_expected_range");

    ATR_Release();
    EMIT_PASS("ATR_Release_no_crash");
}
