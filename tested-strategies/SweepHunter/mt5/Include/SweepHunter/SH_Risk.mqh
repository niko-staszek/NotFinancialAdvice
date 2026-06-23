// SH_Risk.mqh — position size from fixed fractional risk. (Same math as ORB_LotsFromRisk.)
#ifndef SH_RISK_MQH
#define SH_RISK_MQH
double SH_LotsFromRisk(double equity, double riskPct, double slDistUnits,
                       double valuePerUnitPerLot, double volStep, double volMin, double volMax) {
  if (slDistUnits <= 0.0 || valuePerUnitPerLot <= 0.0) return 0.0;
  double riskAmt = equity*(riskPct/100.0);
  double raw     = riskAmt/(slDistUnits*valuePerUnitPerLot);
  double lots    = MathFloor(raw/volStep)*volStep;
  if (lots > volMax) lots = volMax;
  if (lots < volMin) return 0.0;
  return lots;
}
#endif
