//+------------------------------------------------------------------+
//| PAC_Universe.mqh — symbol whitelist + correlation groups          |
//| Mirrors hedgehog/proposer/pac/universe.py                         |
//+------------------------------------------------------------------+
#property strict
#include "PAC_Pip.mqh"

//+------------------------------------------------------------------+
//| Default whitelist — must match config.tradable_symbols default    |
//+------------------------------------------------------------------+
bool Universe_VerifySymbol(string symbol) {
    if (symbol == "XAUUSD") return true;
    if (symbol == "USOIL")  return true;
    if (symbol == "US500")  return true;
    if (symbol == "NAS100") return true;
    if (symbol == "EURUSD") return true;
    if (symbol == "GBPUSD") return true;
    if (symbol == "USDCAD") return true;
    if (symbol == "GC")     return true;  // gold futures — opt-in
    return false;
}

//+------------------------------------------------------------------+
//| Correlation groups state                                          |
//+------------------------------------------------------------------+
#define MAX_CORR_GROUPS 16
#define MAX_GROUP_SIZE  8

string  g_corr_groups[MAX_CORR_GROUPS][MAX_GROUP_SIZE];
int     g_corr_group_sizes[MAX_CORR_GROUPS];
int     g_corr_group_count = 0;

//+------------------------------------------------------------------+
//| Parse InpCorrelationGroups string of form                        |
//|   "{XAUUSD,US500};{US500,US30,USTECH};{USOIL,US500}"             |
//+------------------------------------------------------------------+
void Universe_InitCorrelationGroups(string spec) {
    g_corr_group_count = 0;

    string raw_groups[];
    int n = StringSplit(spec, ';', raw_groups);
    for (int i = 0; i < n && g_corr_group_count < MAX_CORR_GROUPS; i++) {
        string group_str = raw_groups[i];
        StringReplace(group_str, "{", "");
        StringReplace(group_str, "}", "");
        StringReplace(group_str, " ", "");
        if (StringLen(group_str) == 0) continue;

        string members[];
        int m = StringSplit(group_str, ',', members);
        if (m == 0) continue;

        for (int j = 0; j < m && j < MAX_GROUP_SIZE; j++) {
            g_corr_groups[g_corr_group_count][j] = members[j];
        }
        g_corr_group_sizes[g_corr_group_count] = m;
        g_corr_group_count++;
    }
}

//+------------------------------------------------------------------+
//| Return the FIRST group index that contains the symbol, or -1.    |
//+------------------------------------------------------------------+
int Universe_CorrelationGroupId(string symbol) {
    for (int g = 0; g < g_corr_group_count; g++) {
        for (int k = 0; k < g_corr_group_sizes[g]; k++) {
            if (g_corr_groups[g][k] == symbol) return g;
        }
    }
    return -1;
}

//+------------------------------------------------------------------+
//| True iff a and b appear in the SAME correlation group.           |
//+------------------------------------------------------------------+
bool Universe_AreCorrelated(string a, string b) {
    if (a == b) return false;  // identical symbol is not "correlated" in lockout sense
    for (int g = 0; g < g_corr_group_count; g++) {
        bool has_a = false, has_b = false;
        for (int k = 0; k < g_corr_group_sizes[g]; k++) {
            if (g_corr_groups[g][k] == a) has_a = true;
            if (g_corr_groups[g][k] == b) has_b = true;
        }
        if (has_a && has_b) return true;
    }
    return false;
}
