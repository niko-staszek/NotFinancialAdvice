#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\ORB\\ORB_Risk.mqh"
void OnStart(){
  ASSERT_NEAR(ORB_LotsFromRisk(10000,1.0,50,1.0,0.01,0.01,100.0),2.0,1e-9,"lots_basic");
  ASSERT_NEAR(ORB_LotsFromRisk(10000,1.0,42.79,1.0,0.01,0.01,100.0),
              MathFloor((100.0/42.79)/0.01)*0.01,1e-9,"lots_floor_step");
  ASSERT_NEAR(ORB_LotsFromRisk(10000,50,1,1.0,0.01,0.01,5.0),5.0,1e-9,"lots_capped");
  ASSERT_NEAR(ORB_LotsFromRisk(100,0.01,9999,1.0,0.01,0.01,100.0),0.0,1e-9,"lots_below_min_zero");
  Sleep(300);
  TerminalClose(0);
}
