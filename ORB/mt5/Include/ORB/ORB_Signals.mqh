#ifndef ORB_SIGNALS_MQH
#define ORB_SIGNALS_MQH
double ORB_EntryPrice(int bias,double orHigh,double orLow,double bufFrac){
  double buf=bufFrac*(orHigh-orLow);
  return (bias>0)? orHigh+buf : orLow-buf;
}
#endif
