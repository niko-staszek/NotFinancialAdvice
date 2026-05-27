//+------------------------------------------------------------------+
//| PAC_ATR.mqh — ATR(20) handle wrapper                              |
//| Mirrors helpers/atr.py                                            |
//+------------------------------------------------------------------+
#property strict

int g_atr_handle = INVALID_HANDLE;

bool ATR_Init(string symbol, ENUM_TIMEFRAMES tf, int period) {
    g_atr_handle = iATR(symbol, tf, period);
    if (g_atr_handle == INVALID_HANDLE) {
        PrintFormat("PAC_ATR: iATR failed for %s tf=%d period=%d (err=%d)",
                    symbol, (int)tf, period, GetLastError());
        return false;
    }
    return true;
}

double ATR_Value(int bar_shift) {
    double tmp[1];
    if (CopyBuffer(g_atr_handle, 0, bar_shift, 1, tmp) != 1) return 0.0;
    return tmp[0];
}

void ATR_Release() {
    if (g_atr_handle != INVALID_HANDLE) {
        IndicatorRelease(g_atr_handle);
        g_atr_handle = INVALID_HANDLE;
    }
}
