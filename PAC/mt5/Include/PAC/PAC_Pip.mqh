//+------------------------------------------------------------------+
//| PAC_Pip.mqh — per-symbol pip-size lookups                         |
//| Mirrors Plan 4 universe.PIP_FACTOR_BY_SYMBOL semantics            |
//| Source: strategy_ea.md §0.4 "Pip definitions"                     |
//+------------------------------------------------------------------+
#property strict
#ifndef __PAC_PIP_MQH__
#define __PAC_PIP_MQH__

//+------------------------------------------------------------------+
//| PipSize: returns the price-unit value of 1 pip for the symbol.   |
//| Returns 0 for unknown symbols (caller must check and reject the  |
//| trade). Logs the failure via Print.                                |
//+------------------------------------------------------------------+
double PipSize(string symbol) {
    // 4-digit FX majors: 1 pip = 0.0001
    if (symbol == "EURUSD" || symbol == "GBPUSD" || symbol == "USDCAD"
        || symbol == "AUDUSD" || symbol == "NZDUSD" || symbol == "EURGBP")
        return 0.0001;

    // 2-digit JPY pairs: 1 pip = 0.01
    if (StringFind(symbol, "JPY") >= 0)
        return 0.01;

    // Gold: 1 pip = $0.10
    if (symbol == "XAUUSD" || symbol == "GC")
        return 0.10;

    // Oil: 1 pip = $0.01
    if (symbol == "USOIL" || symbol == "WTIUSD" || symbol == "UKOIL")
        return 0.01;

    // Indices: 1 pip = 1 index point
    if (symbol == "US500" || symbol == "NAS100" || symbol == "US30"
        || symbol == "USTECH" || symbol == "DAX40" || symbol == "UK100")
        return 1.0;

    PrintFormat("PAC_Pip: unknown symbol %s — returning 0; trade must be rejected", symbol);
    return 0.0;
}

double PriceToPips(string symbol, double price_distance) {
    double ps = PipSize(symbol);
    if (ps == 0.0) return 0.0;
    return price_distance / ps;
}

double PipsToPrice(string symbol, double pips) {
    double ps = PipSize(symbol);
    if (ps == 0.0) return 0.0;
    return pips * ps;
}

#endif // __PAC_PIP_MQH__
