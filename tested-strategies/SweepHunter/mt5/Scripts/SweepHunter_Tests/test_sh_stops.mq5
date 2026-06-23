// test_sh_stops.mq5
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Stops.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Risk.mqh"

void OnStart() {
  // Long: stop below swing low by buffer. Short: stop above swing high by buffer.
  ASSERT_EQ(SH_Stop(+1, 95.0, 0.5),  94.5, "long_stop_below_swing");
  ASSERT_EQ(SH_Stop(-1, 105.0, 0.5), 105.5, "short_stop_above_swing");

  // Lots from risk: equity 10000, risk 1% = $100; SL dist 2.0 units; $1/unit/lot -> 50 lots,
  // capped at volMax 10 -> 10.0; step 0.01, min 0.01.
  ASSERT_EQ(SH_LotsFromRisk(10000, 1.0, 2.0, 1.0, 0.01, 0.01, 10.0), 10.0, "lots_capped");
  // risk too small -> below volMin -> 0.
  ASSERT_EQ(SH_LotsFromRisk(10000, 0.0001, 2.0, 1.0, 0.01, 0.01, 10.0), 0.0, "lots_zero_below_min");
  // invalid SL dist -> 0.
  ASSERT_EQ(SH_LotsFromRisk(10000, 1.0, 0.0, 1.0, 0.01, 0.01, 10.0), 0.0, "lots_zero_bad_sl");

  Sleep(300);
  TerminalClose(0);
}
