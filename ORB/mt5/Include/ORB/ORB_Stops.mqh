#ifndef ORB_STOPS_MQH
#define ORB_STOPS_MQH
double ORB_StopLoss(int arm,int bias,double entry,double orHigh,double orLow,double orMid,double atr,double kAtr){
  if(arm==0) return (bias>0)? orLow : orHigh;
  if(arm==1) return orMid;
  return (bias>0)? entry-kAtr*atr : entry+kAtr*atr;
}
double ORB_R(double entry,double sl){ return MathAbs(entry-sl); }
#endif
