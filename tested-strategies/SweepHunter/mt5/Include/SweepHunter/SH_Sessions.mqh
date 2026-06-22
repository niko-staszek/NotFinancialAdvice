// SH_Sessions.mqh — compute Asia/London session high/low by bucketing M1 bars on ET time-of-day.
#ifndef SH_SESSIONS_MQH
#define SH_SESSIONS_MQH
#include "SH_Time.mqh"

struct SHLevels {
  double asiaH, asiaL, lonH, lonL;
  bool   asiaValid, lonValid;
};

// Pure core: parallel arrays of per-bar ET-minute, high, low (length n).
SHLevels SH_ComputeLevels(const int &etmin[], const double &highs[], const double &lows[], int n,
                          int asiaStart, int asiaEnd, int lonStart, int lonEnd) {
  SHLevels L;
  L.asiaH = -DBL_MAX; L.asiaL = DBL_MAX; L.lonH = -DBL_MAX; L.lonL = DBL_MAX;
  L.asiaValid = false; L.lonValid = false;
  for (int i = 0; i < n; i++) {
    if (SH_InWindowEt(etmin[i], asiaStart, asiaEnd)) {
      if (highs[i] > L.asiaH) L.asiaH = highs[i];
      if (lows[i]  < L.asiaL) L.asiaL = lows[i];
      L.asiaValid = true;
    }
    if (SH_InWindowEt(etmin[i], lonStart, lonEnd)) {
      if (highs[i] > L.lonH) L.lonH = highs[i];
      if (lows[i]  < L.lonL) L.lonL = lows[i];
      L.lonValid = true;
    }
  }
  return L;
}

// Live wrapper: scan the last `lookback` closed M1 bars (shift 1..lookback) at mark time.
SHLevels SH_ScanLevels(string sym, int offsetSec, int lookback,
                       int asiaStart, int asiaEnd, int lonStart, int lonEnd) {
  int    etmin[]; double highs[], lows[];
  ArrayResize(etmin, lookback); ArrayResize(highs, lookback); ArrayResize(lows, lookback);
  int n = 0;
  for (int s = 1; s <= lookback; s++) {
    datetime bt = iTime(sym, PERIOD_M1, s);
    if (bt == 0) break;
    etmin[n] = ORB_EtMinutesFromServer(bt, offsetSec);
    highs[n] = iHigh(sym, PERIOD_M1, s);
    lows[n]  = iLow (sym, PERIOD_M1, s);
    n++;
  }
  return SH_ComputeLevels(etmin, highs, lows, n, asiaStart, asiaEnd, lonStart, lonEnd);
}
#endif
