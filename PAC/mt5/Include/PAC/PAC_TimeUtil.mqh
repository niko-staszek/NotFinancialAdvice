//+------------------------------------------------------------------+
//| PAC_TimeUtil.mqh — DST-aware UTC↔PLT + session windows            |
//| Mirrors Plan 4 hedgehog/proposer/pac/helpers/timeutil.py          |
//+------------------------------------------------------------------+
#property strict

enum SessionKind {
    SESSION_DEAD    = 0,
    SESSION_ASIA    = 1,
    SESSION_LONDON  = 2,
    SESSION_AMERICA = 3,
};

//+------------------------------------------------------------------+
//| Return the day-of-month for the last Sunday in given year+month. |
//+------------------------------------------------------------------+
int _LastSundayOfMonth(int year, int month) {
    // MQL5 datetime is seconds since 1970-01-01 00:00:00 UTC.
    // Build the last day of the month and walk back to Sunday.
    int days_in_month = (month == 2)
        ? (((year % 4 == 0) && (year % 100 != 0)) || (year % 400 == 0) ? 29 : 28)
        : ((month == 4 || month == 6 || month == 9 || month == 11) ? 30 : 31);

    MqlDateTime mdt;
    mdt.year = year; mdt.mon = month; mdt.day = days_in_month;
    mdt.hour = 0; mdt.min = 0; mdt.sec = 0;
    datetime t = StructToTime(mdt);
    MqlDateTime out;
    TimeToStruct(t, out);
    // out.day_of_week: 0=Sunday, 1=Monday ... 6=Saturday
    int back = out.day_of_week;
    return days_in_month - back;
}

//+------------------------------------------------------------------+
//| Determine whether the given UTC moment is in CEST (summer).      |
//| Rule: from last Sunday of March 01:00 UTC through last Sunday of |
//| October 01:00 UTC.                                                 |
//+------------------------------------------------------------------+
bool TimeUtil_IsDST(datetime utc_time) {
    MqlDateTime m;
    TimeToStruct(utc_time, m);
    int year = m.year;

    int spring_day = _LastSundayOfMonth(year, 3);
    int fall_day   = _LastSundayOfMonth(year, 10);

    MqlDateTime spring_mdt;
    spring_mdt.year = year; spring_mdt.mon = 3; spring_mdt.day = spring_day;
    spring_mdt.hour = 1; spring_mdt.min = 0; spring_mdt.sec = 0;
    datetime spring_start = StructToTime(spring_mdt);

    MqlDateTime fall_mdt;
    fall_mdt.year = year; fall_mdt.mon = 10; fall_mdt.day = fall_day;
    fall_mdt.hour = 1; fall_mdt.min = 0; fall_mdt.sec = 0;
    datetime fall_end = StructToTime(fall_mdt);

    return (utc_time >= spring_start) && (utc_time < fall_end);
}

datetime TimeUtil_UtcToPLT(datetime utc_time) {
    return utc_time + (TimeUtil_IsDST(utc_time) ? 7200 : 3600);
}

//+------------------------------------------------------------------+
//| Classify the session window for a given UTC moment.              |
//| Sessions in Polish local time per strategy_ea.md §2.3:           |
//|   Asia:    23:00 → 07:59 (wraps midnight)                         |
//|   London:  08:00 → 13:59                                          |
//|   America: 14:00 → 21:59                                          |
//|   Dead:    22:00 → 22:59                                          |
//+------------------------------------------------------------------+
int TimeUtil_CurrentSessionForUtc(datetime utc_time) {
    datetime plt = TimeUtil_UtcToPLT(utc_time);
    MqlDateTime m;
    TimeToStruct(plt, m);
    int h = m.hour;

    if (h >= 8 && h < 14)  return SESSION_LONDON;
    if (h >= 14 && h < 22) return SESSION_AMERICA;
    if (h == 22)           return SESSION_DEAD;
    return SESSION_ASIA;   // 23, 0-7 wraps midnight
}

int TimeUtil_CurrentSession() {
    return TimeUtil_CurrentSessionForUtc(TimeGMT());
}
