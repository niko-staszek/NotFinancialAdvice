//+------------------------------------------------------------------+
//| test_pac_timeutil.mq5                                             |
//+------------------------------------------------------------------+
#property strict
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\PAC\\PAC_TimeUtil.mqh"

void OnStart() {
    // 2026 DST: CEST starts Sunday 2026-03-29 02:00, CET starts Sunday 2026-10-25 03:00
    // Winter date: 2026-02-15 — CET (UTC+1)
    datetime winter_utc = D'2026.02.15 10:00:00';
    datetime winter_plt = TimeUtil_UtcToPLT(winter_utc);
    ASSERT_EQ_INT(winter_plt - winter_utc, 3600, "UTC_to_PLT_winter_offset_1hr");

    // Summer date: 2026-07-15 — CEST (UTC+2)
    datetime summer_utc = D'2026.07.15 10:00:00';
    datetime summer_plt = TimeUtil_UtcToPLT(summer_utc);
    ASSERT_EQ_INT(summer_plt - summer_utc, 7200, "UTC_to_PLT_summer_offset_2hr");

    // Day before spring-forward: 2026-03-28 (Saturday) — still winter
    datetime before_dst = D'2026.03.28 10:00:00';
    ASSERT_EQ_INT(TimeUtil_UtcToPLT(before_dst) - before_dst, 3600, "UTC_to_PLT_2026-03-28_pre_DST");

    // Day of spring-forward: 2026-03-29 — summer starts at 02:00 PLT (01:00 UTC)
    datetime after_dst = D'2026.03.29 10:00:00';
    ASSERT_EQ_INT(TimeUtil_UtcToPLT(after_dst) - after_dst, 7200, "UTC_to_PLT_2026-03-29_post_DST");

    // Day before fall-back: 2026-10-24 (Saturday) — still summer
    datetime before_fall = D'2026.10.24 10:00:00';
    ASSERT_EQ_INT(TimeUtil_UtcToPLT(before_fall) - before_fall, 7200, "UTC_to_PLT_2026-10-24_pre_fall_back");

    // Day of fall-back: 2026-10-25 — winter starts at 03:00 PLT (01:00 UTC)
    datetime after_fall = D'2026.10.25 10:00:00';
    ASSERT_EQ_INT(TimeUtil_UtcToPLT(after_fall) - after_fall, 3600, "UTC_to_PLT_2026-10-25_post_fall_back");

    // Session classification — strategy_ea.md §2.3
    // London PLT 08:00-13:59 → in winter UTC 07:00-12:59, in summer UTC 06:00-11:59
    // Test winter London: 2026-02-15 09:00 PLT = 08:00 UTC
    datetime london_winter_utc = D'2026.02.15 08:00:00';  // 09:00 PLT
    ASSERT_EQ_INT(TimeUtil_CurrentSessionForUtc(london_winter_utc), 2, "Session_London_winter");

    // Test summer America: 2026-07-15 16:00 PLT = 14:00 UTC
    datetime america_summer_utc = D'2026.07.15 14:00:00';  // 16:00 PLT
    ASSERT_EQ_INT(TimeUtil_CurrentSessionForUtc(america_summer_utc), 3, "Session_America_summer");

    // Dead session: 22:00-22:59 PLT
    datetime dead_winter_utc = D'2026.02.15 21:30:00';  // 22:30 PLT
    ASSERT_EQ_INT(TimeUtil_CurrentSessionForUtc(dead_winter_utc), 0, "Session_Dead_winter");
}
