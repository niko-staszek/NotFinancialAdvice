// SH_Stops.mqh — stop just beyond the post-sweep swing.
#ifndef SH_STOPS_MQH
#define SH_STOPS_MQH
// LONG (+1): stop below swing low by buffer. SHORT (-1): stop above swing high by buffer.
double SH_Stop(int dir, double swing, double buffer) {
  return (dir > 0) ? (swing - buffer) : (swing + buffer);
}
#endif
