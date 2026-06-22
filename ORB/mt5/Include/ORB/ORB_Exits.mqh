#ifndef ORB_EXITS_MQH
#define ORB_EXITS_MQH
double ORB_Target(int bias,double entry,double R,double K){
  return (bias>0)? entry+K*R : entry-K*R;
}
bool ORB_EmaCloseCrossExit(int bias,double m15Close,double ema){
  return (bias>0)? (m15Close<ema) : (m15Close>ema);
}
#endif
