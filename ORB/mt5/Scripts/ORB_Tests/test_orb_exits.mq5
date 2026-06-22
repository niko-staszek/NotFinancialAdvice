#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\ORB\\ORB_Exits.mqh"
void OnStart(){
  double entryL=20105.0, R=55.0;
  ASSERT_NEAR(ORB_Target(+1,entryL,R,1.0),20160.0,1e-9,"E0_long_1R");
  ASSERT_NEAR(ORB_Target(+1,entryL,R,2.0),20215.0,1e-9,"E1_long_2R");
  ASSERT_NEAR(ORB_Target(-1,20045.0,55.0,1.0),19990.0,1e-9,"E0_short_1R");
  ASSERT_TRUE (ORB_EmaCloseCrossExit(+1,20070.0,20080.0),"long_exit_close_below_ema");
  ASSERT_FALSE(ORB_EmaCloseCrossExit(+1,20090.0,20080.0),"long_hold_close_above_ema");
  ASSERT_TRUE (ORB_EmaCloseCrossExit(-1,20090.0,20080.0),"short_exit_close_above_ema");
  Sleep(300);
  TerminalClose(0);
}
