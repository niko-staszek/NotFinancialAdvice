// test_sh_fvg.mq5
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_FVG.mqh"

void OnStart() {
  // Bars are (h2,l2)=oldest .. (h0,l0)=newest.
  // Bullish FVG: high[2] < low[0]  -> gap [h2, l0]
  ASSERT_TRUE (SH_IsFVG(+1, 10.0,9.0,  10.5,9.5,  12.0,11.0), "bull_fvg_true");   // 10 < 11
  ASSERT_FALSE(SH_IsFVG(+1, 10.0,9.0,  10.5,9.5,  10.5,9.8 ), "bull_fvg_false");  // 10 !< 9.8
  // Bearish FVG: low[2] > high[0]  -> gap [h0, l2]
  ASSERT_TRUE (SH_IsFVG(-1, 12.0,11.0, 10.5,9.5,  10.0,9.0 ), "bear_fvg_true");   // 11 > 10
  ASSERT_FALSE(SH_IsFVG(-1, 12.0,11.0, 10.5,9.5,  11.5,11.2), "bear_fvg_false");  // 11 !> 11.5

  // Bullish gap [h2=10, l0=11]: proximal=l0=11 (top, retrace from above hits first), distal=h2=10.
  ASSERT_EQ(SH_FvgEntry(+1, 10.0,9.0, 12.0,11.0, 0.0), 11.0, "bull_entry_proximal");
  ASSERT_EQ(SH_FvgEntry(+1, 10.0,9.0, 12.0,11.0, 1.0), 10.0, "bull_entry_distal");
  ASSERT_EQ(SH_FvgEntry(+1, 10.0,9.0, 12.0,11.0, 0.5), 10.5, "bull_entry_mid");

  // Bearish gap [h0=10, l2=11]: proximal=h0=10 (bottom, retrace from below hits first), distal=l2=11.
  ASSERT_EQ(SH_FvgEntry(-1, 12.0,11.0, 10.0,9.0, 0.0), 10.0, "bear_entry_proximal");
  ASSERT_EQ(SH_FvgEntry(-1, 12.0,11.0, 10.0,9.0, 1.0), 11.0, "bear_entry_distal");

  Sleep(300);
  TerminalClose(0);
}
