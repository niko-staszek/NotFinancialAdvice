// test_sh_sweep.mq5
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Sweep.mqh"

void OnStart() {
  // side +1 = a HIGH level: swept when bar high exceeds it.
  ASSERT_TRUE (SH_Swept(+1, 105.0, 100.0, 104.0), "high_swept");
  ASSERT_FALSE(SH_Swept(+1, 103.0, 100.0, 104.0), "high_not_swept");
  // side -1 = a LOW level: swept when bar low drops below it.
  ASSERT_TRUE (SH_Swept(-1, 100.0,  95.0,  96.0), "low_swept");
  ASSERT_FALSE(SH_Swept(-1, 100.0,  97.0,  96.0), "low_not_swept");

  // Direction: sweeping a high -> short; sweeping a low -> long.
  ASSERT_EQ_INT(SH_DirFromSweepSide(+1), -1, "high_sweep_short");
  ASSERT_EQ_INT(SH_DirFromSweepSide(-1), +1, "low_sweep_long");

  // Swing: short tracks highest high; long tracks lowest low.
  ASSERT_EQ(SH_UpdateSwing(-1, 105.0, 107.0, 102.0), 107.0, "short_swing_up");
  ASSERT_EQ(SH_UpdateSwing(-1, 105.0, 104.0, 102.0), 105.0, "short_swing_keep");
  ASSERT_EQ(SH_UpdateSwing(+1,  95.0,  98.0,  93.0), 93.0,  "long_swing_down");
  ASSERT_EQ(SH_UpdateSwing(+1,  95.0,  98.0,  96.0), 95.0,  "long_swing_keep");

  Sleep(300);
  TerminalClose(0);
}
