// SH_Time.mqh — wrap-aware ET session-window predicate. Reuses ORB_Time DST/ET calendars.
#ifndef SH_TIME_MQH
#define SH_TIME_MQH
#include "..\\ORB\\ORB_Time.mqh"   // ORB_EtMinutesFromServer, ORB_ServerToUtcOffsetSec, ORB_UtcToEt

// Is ET minute-of-day `m` inside [startHHMM, endHHMM)? Handles windows that wrap midnight
// (end <= start, e.g. Asia 2000->0000). A zero-width window (start==end) is always false.
bool SH_InWindowEt(int m, int startHHMM, int endHHMM) {
  int s = (startHHMM/100)*60 + (startHHMM%100);
  int e = (endHHMM/100)*60   + (endHHMM%100);
  if (s == e) return false;
  if (s <  e) return (m >= s && m < e);   // same-day
  return (m >= s || m < e);               // wraps midnight
}

// ET minute-of-day for a server timestamp given the server->UTC offset (seconds).
int SH_EtMin(datetime srv, int offsetSec) { return ORB_EtMinutesFromServer(srv, offsetSec); }
#endif
