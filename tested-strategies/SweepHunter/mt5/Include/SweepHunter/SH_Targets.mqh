// SH_Targets.mqh — risk distance, fixed-RR target, and draw-on-liquidity target.
#ifndef SH_TARGETS_MQH
#define SH_TARGETS_MQH

double SH_R(double entry, double stop) { return MathAbs(entry - stop); }

double SH_TargetRR(int dir, double entry, double R, double rr) { return entry + dir*rr*R; }

// Nearest un-swept marked level strictly beyond entry in the trade direction.
// LONG (+1): lowest level above entry. SHORT (-1): highest level below entry.
// If none qualifies, return `rrFallback` and set found=false.
double SH_TargetDOL(int dir, double entry, const double &levels[], int n, double rrFallback, bool &found) {
  found = false;
  double best = 0.0;
  for (int i = 0; i < n; i++) {
    double lv = levels[i];
    if (dir > 0 && lv > entry) { if (!found || lv < best) { best = lv; found = true; } }
    if (dir < 0 && lv < entry) { if (!found || lv > best) { best = lv; found = true; } }
  }
  return found ? best : rrFallback;
}
#endif
