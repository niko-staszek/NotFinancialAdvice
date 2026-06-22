#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\ORB\\ORB_Range.mqh"
void OnStart(){
  ASSERT_NEAR(ORB_Width(20100.0,20050.0),50.0,1e-9,"width");
  ASSERT_NEAR(ORB_Mid(20100.0,20050.0),20075.0,1e-9,"mid");
  double v[5]={100,120,80,110,90};
  ASSERT_NEAR(ORB_Median(v,5),100.0,1e-9,"median_odd");
  double v4[4]={100,200,300,400};
  ASSERT_NEAR(ORB_Median(v4,4),250.0,1e-9,"median_even");
  ASSERT_NEAR(ORB_Rvol(150.0,v,5),1.5,1e-9,"rvol_1p5");
  double w[5]={40,42,38,41,39};
  ASSERT_TRUE (ORB_RangeGuardOk(50.0,w,5,0.5,2.0),"guard_ok_50");
  ASSERT_FALSE(ORB_RangeGuardOk(15.0,w,5,0.5,2.0),"guard_dead_15");
  ASSERT_FALSE(ORB_RangeGuardOk(90.0,w,5,0.5,2.0),"guard_blowoff_90");
  Sleep(300);
  TerminalClose(0);
}
