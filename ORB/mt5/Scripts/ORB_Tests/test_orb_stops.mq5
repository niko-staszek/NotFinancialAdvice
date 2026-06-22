#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\ORB\\ORB_Stops.mqh"
void OnStart(){
  double entryL=20105.0, H=20100.0, L=20050.0, M=20075.0, atr=30.0;
  ASSERT_NEAR(ORB_StopLoss(0,+1,entryL,H,L,M,atr,1.5),20050.0,1e-9,"S0_long_opposite");
  ASSERT_NEAR(ORB_StopLoss(1,+1,entryL,H,L,M,atr,1.5),20075.0,1e-9,"S1_long_mid");
  ASSERT_NEAR(ORB_StopLoss(2,+1,entryL,H,L,M,atr,1.5),20105.0-45.0,1e-9,"S2_long_katr");
  double entryS=20045.0;
  ASSERT_NEAR(ORB_StopLoss(0,-1,entryS,H,L,M,atr,1.5),20100.0,1e-9,"S0_short_opposite");
  ASSERT_NEAR(ORB_StopLoss(2,-1,entryS,H,L,M,atr,1.5),20045.0+45.0,1e-9,"S2_short_katr");
  ASSERT_NEAR(ORB_R(20105.0,20050.0),55.0,1e-9,"R_long");
  Sleep(300);
  TerminalClose(0);
}
