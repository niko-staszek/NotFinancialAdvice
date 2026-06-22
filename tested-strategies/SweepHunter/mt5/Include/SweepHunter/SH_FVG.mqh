// SH_FVG.mqh — 3-candle fair value gap detection and entry pricing.
// Bars indexed oldest->newest as (h2,l2),(h1,l1),(h0,l0); middle bar not needed for the gap test.
#ifndef SH_FVG_MQH
#define SH_FVG_MQH

// dir +1 = look for a BULLISH FVG (for a long); dir -1 = BEARISH (for a short).
bool SH_IsFVG(int dir, double h2,double l2, double h1,double l1, double h0,double l0) {
  if (dir > 0) return (h2 < l0);   // bullish: newest low above oldest high
  if (dir < 0) return (l2 > h0);   // bearish: newest high below oldest low
  return false;
}

// Proximal edge = the gap boundary the retracement reaches first.
double SH_FvgProximal(int dir, double h2,double l2, double h0,double l0) {
  return (dir > 0) ? l0 : h0;
}
// Distal edge = the far boundary.
double SH_FvgDistal(int dir, double h2,double l2, double h0,double l0) {
  return (dir > 0) ? h2 : l2;
}
// Entry at fill depth in [0,1]: 0 = proximal (fills first), 1 = distal (deepest).
double SH_FvgEntry(int dir, double h2,double l2, double h0,double l0, double depth) {
  double p = SH_FvgProximal(dir, h2,l2, h0,l0);
  double d = SH_FvgDistal  (dir, h2,l2, h0,l0);
  return p + depth*(d - p);
}
#endif
