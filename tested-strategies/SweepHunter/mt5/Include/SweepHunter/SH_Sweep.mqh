// SH_Sweep.mqh — liquidity sweep detection and post-sweep swing tracking.
#ifndef SH_SWEEP_MQH
#define SH_SWEEP_MQH

// side +1 = high level (swept when bar high > level); side -1 = low level (swept when bar low < level).
bool SH_Swept(int side, double barHigh, double barLow, double level) {
  return (side > 0) ? (barHigh > level) : (barLow < level);
}

// Trade direction after a sweep: sweeping a high -> SHORT (-1); sweeping a low -> LONG (+1).
int SH_DirFromSweepSide(int side) { return (side > 0) ? -1 : +1; }

// Running swing extreme since the sweep: SHORT tracks highest high, LONG tracks lowest low.
double SH_UpdateSwing(int dir, double prevSwing, double barHigh, double barLow) {
  if (dir < 0) return MathMax(prevSwing, barHigh);
  return MathMin(prevSwing, barLow);
}
#endif
