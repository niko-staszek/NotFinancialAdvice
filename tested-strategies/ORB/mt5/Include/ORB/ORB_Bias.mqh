#ifndef ORB_BIAS_MQH
#define ORB_BIAS_MQH
int ORB_Bias(double priorDailyClose,double dailyEma){
  if(priorDailyClose>dailyEma) return +1;
  if(priorDailyClose<dailyEma) return -1;
  return 0;
}
#endif
