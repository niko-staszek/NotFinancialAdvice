#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\ORB\\ORB_Signals.mqh"
void OnStart(){
  ASSERT_NEAR(ORB_EntryPrice(+1,20100.0,20050.0,0.1),20105.0,1e-9,"long_entry_above_high");
  ASSERT_NEAR(ORB_EntryPrice(-1,20100.0,20050.0,0.1),20045.0,1e-9,"short_entry_below_low");
  Sleep(300);
  TerminalClose(0);
}
