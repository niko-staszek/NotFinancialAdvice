//+------------------------------------------------------------------+
//| test_pac_universe.mq5                                             |
//+------------------------------------------------------------------+
#property strict
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\PAC\\PAC_Universe.mqh"

void OnStart() {
    // Default whitelist
    ASSERT_TRUE(Universe_VerifySymbol("EURUSD"), "VerifySymbol_EURUSD");
    ASSERT_TRUE(Universe_VerifySymbol("XAUUSD"), "VerifySymbol_XAUUSD");
    ASSERT_TRUE(Universe_VerifySymbol("US500"),  "VerifySymbol_US500");
    ASSERT_FALSE(Universe_VerifySymbol("UNKNOWN"), "VerifySymbol_Unknown_Rejected");

    // Correlation groups (default 3 groups from strategy_ea.md §1.6)
    Universe_InitCorrelationGroups("{XAUUSD,US500};{US500,US30,USTECH};{USOIL,US500}");

    // XAUUSD is in group 0
    int xau_group = Universe_CorrelationGroupId("XAUUSD");
    ASSERT_TRUE(xau_group >= 0, "CorrelationGroup_XAUUSD_found");

    // US500 is in 3 groups (0, 1, 2) — function returns the FIRST match
    int us500_group = Universe_CorrelationGroupId("US500");
    ASSERT_EQ_INT(us500_group, 0, "CorrelationGroup_US500_first_match_is_group_0");

    // Same-group lockout check
    ASSERT_TRUE(Universe_AreCorrelated("XAUUSD", "US500"), "Correlation_XAUUSD_US500");
    ASSERT_TRUE(Universe_AreCorrelated("US500", "US30"), "Correlation_US500_US30");
    ASSERT_FALSE(Universe_AreCorrelated("EURUSD", "USOIL"), "Correlation_EURUSD_USOIL_independent");
}
