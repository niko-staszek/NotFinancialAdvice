#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\ORB\\ORB_Bias.mqh"
void OnStart(){
  ASSERT_EQ_INT(ORB_Bias(20100.0,20000.0),+1,"bias_long_above_ema");
  ASSERT_EQ_INT(ORB_Bias(19900.0,20000.0),-1,"bias_short_below_ema");
  ASSERT_EQ_INT(ORB_Bias(20000.0,20000.0), 0,"bias_flat_equal_skip");
  Sleep(300);
  TerminalClose(0);
}
