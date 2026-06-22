// test_sh_targets.mq5
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Targets.mqh"

void OnStart() {
  ASSERT_EQ(SH_R(100.0, 98.0), 2.0, "risk_distance");

  // RR target: long 2R from entry 100 risk 2 -> 104; short -> 96.
  ASSERT_EQ(SH_TargetRR(+1, 100.0, 2.0, 2.0), 104.0, "rr_long");
  ASSERT_EQ(SH_TargetRR(-1, 100.0, 2.0, 2.0),  96.0, "rr_short");

  // DOL long: levels above entry, pick nearest (lowest above).
  double lv[4] = { 95.0, 103.0, 107.0, 99.0 };
  bool found;
  double dolL = SH_TargetDOL(+1, 100.0, lv, 4, 999.0, found);
  ASSERT_TRUE(found, "dol_long_found");
  ASSERT_EQ(dolL, 103.0, "dol_long_nearest_above");

  // DOL short: levels below entry, pick nearest (highest below).
  double dolS = SH_TargetDOL(-1, 100.0, lv, 4, 999.0, found);
  ASSERT_TRUE(found, "dol_short_found");
  ASSERT_EQ(dolS, 99.0, "dol_short_nearest_below");

  // DOL fallback: no level in direction -> return fallback, found=false.
  double only_below[2] = { 90.0, 95.0 };
  double fb = SH_TargetDOL(+1, 100.0, only_below, 2, 108.0, found);
  ASSERT_FALSE(found, "dol_fallback_notfound");
  ASSERT_EQ(fb, 108.0, "dol_fallback_value");

  Sleep(300);
  TerminalClose(0);
}
