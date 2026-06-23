// test_sh_time.mq5
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Time.mqh"

void OnStart() {
  // London 02:00-05:00 ET = minutes 120..300 (same-day window)
  ASSERT_TRUE (SH_InWindowEt(120, 200, 500), "lon_start_incl");
  ASSERT_TRUE (SH_InWindowEt(299, 200, 500), "lon_end_excl_inside");
  ASSERT_FALSE(SH_InWindowEt(300, 200, 500), "lon_end_excl");
  ASSERT_FALSE(SH_InWindowEt(119, 200, 500), "lon_before");

  // Asia 20:00-00:00 ET wraps to end-of-day = minutes 1200..1439
  ASSERT_TRUE (SH_InWindowEt(1200, 2000, 0), "asia_2000_incl");
  ASSERT_TRUE (SH_InWindowEt(1380, 2000, 0), "asia_2300_incl");
  ASSERT_FALSE(SH_InWindowEt(1199, 2000, 0), "asia_1959_excl");
  ASSERT_FALSE(SH_InWindowEt(0,    2000, 0), "asia_0000_excl");

  // A genuinely midnight-crossing window 22:00-02:00 = 1320.. || ..120
  ASSERT_TRUE (SH_InWindowEt(1380, 2200, 200), "wrap_2300_in");
  ASSERT_TRUE (SH_InWindowEt(60,   2200, 200), "wrap_0100_in");
  ASSERT_FALSE(SH_InWindowEt(180,  2200, 200), "wrap_0300_out");

  // zero-width window is always false
  ASSERT_FALSE(SH_InWindowEt(120, 200, 200), "zero_width_false");

  Sleep(300);
  TerminalClose(0);
}
