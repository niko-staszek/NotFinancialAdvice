//+------------------------------------------------------------------+
//| test_pac_pip.mq5                                                  |
//+------------------------------------------------------------------+
#property strict
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\PAC\\PAC_Pip.mqh"

void OnStart() {
    ASSERT_NEAR(PipSize("EURUSD"), 0.0001, 1e-10, "PipSize_EURUSD");
    ASSERT_NEAR(PipSize("GBPUSD"), 0.0001, 1e-10, "PipSize_GBPUSD");
    ASSERT_NEAR(PipSize("USDCAD"), 0.0001, 1e-10, "PipSize_USDCAD");
    ASSERT_NEAR(PipSize("USDJPY"), 0.01,   1e-10, "PipSize_USDJPY");
    ASSERT_NEAR(PipSize("XAUUSD"), 0.10,   1e-10, "PipSize_XAUUSD");
    ASSERT_NEAR(PipSize("USOIL"),  0.01,   1e-10, "PipSize_USOIL");
    ASSERT_NEAR(PipSize("US500"),  1.0,    1e-10, "PipSize_US500");
    ASSERT_NEAR(PipSize("NAS100"), 1.0,    1e-10, "PipSize_NAS100");

    ASSERT_NEAR(PriceToPips("EURUSD", 0.00065), 6.5, 1e-9, "PriceToPips_EURUSD_6.5pips");
    ASSERT_NEAR(PriceToPips("XAUUSD", 5.0), 50.0, 1e-9, "PriceToPips_XAUUSD_50pips");

    ASSERT_NEAR(PipsToPrice("EURUSD", 6.5), 0.00065, 1e-9, "PipsToPrice_EURUSD");
    ASSERT_NEAR(PipsToPrice("XAUUSD", 50.0), 5.0, 1e-9, "PipsToPrice_XAUUSD");

    // Unknown symbol fail-loud — returns 0 and logs
    ASSERT_EQ(PipSize("UNKNOWN"), 0.0, "PipSize_Unknown_Returns_Zero");
}
