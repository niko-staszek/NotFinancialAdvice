// test_sh_sessions.mq5
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Sessions.mqh"

void OnStart() {
  // bars tagged by ET minute-of-day with (high, low)
  int    et[6]  = { 1230, 1380,  130,  240,  600,  900 }; // 20:30,23:00 (Asia); 02:10,04:00 (London); 10:00,15:00 (neither)
  double hi[6]  = {  101,  105,   98,  103,  110,  108 };
  double lo[6]  = {   99,  100,   95,   97,  104,  102 };

  SHLevels L = SH_ComputeLevels(et, hi, lo, 6, 2000, 0, 200, 500);

  ASSERT_TRUE (L.asiaValid, "asia_valid");
  ASSERT_EQ   (L.asiaH, 105.0, "asia_high");   // max(101,105)
  ASSERT_EQ   (L.asiaL, 99.0,  "asia_low");    // min(99,100)
  ASSERT_TRUE (L.lonValid, "lon_valid");
  ASSERT_EQ   (L.lonH, 103.0, "lon_high");     // max(98,103)
  ASSERT_EQ   (L.lonL, 95.0,  "lon_low");      // min(95,97)

  // empty session -> invalid pair, no crash
  int    et2[1] = { 600 };
  double hi2[1] = { 110 };
  double lo2[1] = { 104 };
  SHLevels E = SH_ComputeLevels(et2, hi2, lo2, 1, 2000, 0, 200, 500);
  ASSERT_FALSE(E.asiaValid, "empty_asia_invalid");
  ASSERT_FALSE(E.lonValid,  "empty_lon_invalid");

  Sleep(300);
  TerminalClose(0);
}
