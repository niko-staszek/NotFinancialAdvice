// test_orb_time.mq5
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\ORB\\ORB_Time.mqh"

void OnStart() {
  // 2024-07-01 13:30:00 UTC = 09:30 ET (EDT, summer, UTC-4) -> opening range start
  datetime u_summer = D'2024.07.01 13:30:00';
  ASSERT_TRUE(ORB_IsUsDST(u_summer), "us_dst_july_true");
  ASSERT_EQ_INT(ORB_EtMinutesOfDay(ORB_UtcToEt(u_summer)), 570, "summer_0930_et_minutes"); // 9*60+30

  // 2024-01-02 14:30:00 UTC = 09:30 ET (EST, winter, UTC-5)
  datetime u_winter = D'2024.01.02 14:30:00';
  ASSERT_FALSE(ORB_IsUsDST(u_winter), "us_dst_january_false");
  ASSERT_EQ_INT(ORB_EtMinutesOfDay(ORB_UtcToEt(u_winter)), 570, "winter_0930_et_minutes");

  // DST-mismatch week: 2024-03-11 (US already on EDT, EU still on CET).
  // 13:30 UTC must be 09:30 ET even though EU offset would say otherwise.
  datetime u_mismatch = D'2024.03.11 13:30:00';
  ASSERT_TRUE(ORB_IsUsDST(u_mismatch), "us_dst_mar11_true");
  ASSERT_EQ_INT(ORB_EtMinutesOfDay(ORB_UtcToEt(u_mismatch)), 570, "mismatch_0930_et_minutes");

  // Window predicates, given server time + a known server->UTC offset (seconds).
  // FTMO summer = GMT+3 => offset +10800; 16:30 server == 13:30 UTC == 09:30 ET.
  datetime srv_open = D'2024.07.01 16:30:00';
  ASSERT_TRUE(ORB_InOpeningRange(srv_open, 10800, 15), "in_or_at_0930");
  ASSERT_FALSE(ORB_InOpeningRange(srv_open + 15*60, 10800, 15), "not_in_or_at_0945");
  ASSERT_TRUE(ORB_InEntryWindow(srv_open + 30*60, 10800, 945, 1130), "in_entry_1000");
  ASSERT_FALSE(ORB_InEntryWindow(srv_open + 130*60, 10800, 945, 1130), "not_in_entry_1140");
  // 16:00 ET flat. srv_open 16:30 server = 09:30 ET; +7h = 23:30 server = 16:30 ET (>= 16:00).
  ASSERT_TRUE (ORB_AtOrAfterFlat(srv_open + 7*3600, 10800, 1600), "flat_after_1600");
  ASSERT_FALSE(ORB_AtOrAfterFlat(srv_open + 6*3600, 10800, 1600), "not_flat_at_1530"); // 22:30 srv = 15:30 ET

  Sleep(300);        // let Print() flush to the log before shutdown
  TerminalClose(0);  // headless self-terminate so the next cold-start is clean (comment out for interactive F5)
}
