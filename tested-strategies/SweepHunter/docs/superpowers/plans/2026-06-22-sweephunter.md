# SweepHunter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and walk-forward-validate an MQL5 EA that trades the ICT "Asia/London session sweep → NY M1 FVG reversal" model, judged under the repo's acceptance gate.

**Architecture:** Pure, unit-tested `.mqh` logic modules (time/DST, session levels, sweep, FVG, targets, stops, risk, ledger) + a thin orchestrator EA running a daily state machine `WAIT→MARKED→ARMED→INTRADE→DONE`. Validation reuses the monorepo's shared `tools/` harness (headless MT5 compile/test/backtest + walk-forward + `orb_gate`).

**Tech Stack:** MQL5 (EA + test scripts), Python 3 (test/backtest/walk-forward drivers, reused from `tools/`), MT5 Strategy Tester on the FTMO terminal (`81A933A9AFC5DE3C23B15CAB19C63850`).

**Spec:** `tested-strategies/SweepHunter/docs/superpowers/specs/2026-06-22-sweephunter-design.md`

**Conventions (verified against ORB):**
- All commands run from monorepo root `C:\Users\nikof\Documents\GitHub\NotFinancialAdvice`.
- Terminal: `C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe` / `MetaEditor64.exe`.
- Terminal data dir (`DATADIR`): `%APPDATA%\MetaQuotes\Terminal\81A933A9AFC5DE3C23B15CAB19C63850`.
- **`/Script:` is broken on this build** — headless scripts run via `/config:<ini>` with `[StartUp] Script=` (handled by the selftest runner).
- Compile exit code is unreliable — parse the log for exactly `Result: 0 error`.
- MQL5 logs are UTF-16-LE; tester `.ini` files are UTF-16; `.set` and `.mqh` are UTF-8/ANSI.
- Test assertions emit `MQL5TEST {...}` sentinels via `helpers/TestRunner.mqh`.

---

## Task 0: Scaffolding (sync script, test harness copy, strategy.md)

**Files:**
- Create: `tested-strategies/SweepHunter/strategy.md`
- Create: `tested-strategies/SweepHunter/mt5/Scripts/SweepHunter_Tests/helpers/TestRunner.mqh`
- Create: `tools/sync_sweephunter_to_terminal.ps1`
- Create: `tested-strategies/SweepHunter/mt5/.gitignore`

- [ ] **Step 1: Copy the proven TestRunner harness verbatim**

```bash
cp tested-strategies/ORB/mt5/Scripts/ORB_Tests/helpers/TestRunner.mqh \
   tested-strategies/SweepHunter/mt5/Scripts/SweepHunter_Tests/helpers/TestRunner.mqh
```

- [ ] **Step 2: Write `strategy.md`**

```markdown
# SweepHunter

ICT session-liquidity model. At 09:00 ET mark the prior **Asia** (20:00–00:00 ET)
and **London** (02:00–05:00 ET) session highs/lows. During the NY AM hunt window
(09:00–11:30 ET) wait for one of those four levels to be **swept**, then drop to
M1 and enter a **fair-value-gap reversal** the other way. Stop at the sweep swing;
target either fixed **1:2 RR** or the next **draw on liquidity** (nearest un-swept
session level) — both modes carried and compared on identical entries.

- Engine: MQL5 EA, MT5 Strategy Tester (FTMO), `Period=M1`, real ticks.
- Spec: `docs/superpowers/specs/2026-06-22-sweephunter-design.md`
- Plan: `docs/superpowers/plans/2026-06-22-sweephunter.md`
- Validation: walk-forward IS/OOS + `tools/orb_gate.py` + cross-instrument table. See `VERDICT.md` (written at the end).
```

- [ ] **Step 3: Write `tested-strategies/SweepHunter/mt5/.gitignore`**

```gitignore
*.ex5
*.log
```

- [ ] **Step 4: Write `tools/sync_sweephunter_to_terminal.ps1`**

```powershell
# tools/sync_sweephunter_to_terminal.ps1 — mirror SweepHunter sources into the FTMO terminal tree.
# Also copies the shared ORB_Time.mqh dependency (SH_Time.mqh includes ..\ORB\ORB_Time.mqh).
param(
  [string]$DataDir = "$env:APPDATA\MetaQuotes\Terminal\81A933A9AFC5DE3C23B15CAB19C63850"
)
$ErrorActionPreference = "Stop"
$src = "tested-strategies/SweepHunter/mt5"

# SweepHunter's own trees
foreach ($sub in @("Include/SweepHunter","Experts/SweepHunter","Scripts/SweepHunter_Tests")) {
  $dst = Join-Path "$DataDir/MQL5" $sub
  New-Item -ItemType Directory -Force $dst | Out-Null
  Copy-Item "$src/$sub/*" $dst -Recurse -Force
}

# Shared dependency: ORB_Time.mqh (DST/ET calendars) into Include/ORB/
$orbInc = Join-Path "$DataDir/MQL5" "Include/ORB"
New-Item -ItemType Directory -Force $orbInc | Out-Null
Copy-Item "tested-strategies/ORB/mt5/Include/ORB/ORB_Time.mqh" $orbInc -Force

Write-Host "Synced SweepHunter sources (+ ORB_Time dep) to $DataDir/MQL5"
```

- [ ] **Step 5: Commit**

```bash
git add tested-strategies/SweepHunter tools/sync_sweephunter_to_terminal.ps1
git commit -m "scaffold(sweephunter): strategy.md, test harness, sync script"
```

---

## Task 1: SH_Time.mqh — wrap-aware ET session windows

**Files:**
- Create: `tested-strategies/SweepHunter/mt5/Include/SweepHunter/SH_Time.mqh`
- Test: `tested-strategies/SweepHunter/mt5/Scripts/SweepHunter_Tests/test_sh_time.mq5`

- [ ] **Step 1: Write the failing test**

```cpp
// test_sh_time.mq5
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Time.mqh"

void OnStart() {
  // London 02:00-05:00 ET = minutes 120..300 (same-day window)
  ASSERT_TRUE (SH_InWindowEt(120, 200, 500), "lon_start_incl");
  ASSERT_TRUE (SH_InWindowEt(299, 200, 500), "lon_end_excl_inside");
  ASSERT_FALSE(SH_InWindowEt(300, 200, 500), "lon_end_excl");
  ASSERT_FALSE(SH_InWindowEt(119, 200, 500), "lon_before");

  // Asia 20:00-00:00 ET wraps to end-of-day = minutes 1200..1439
  ASSERT_TRUE (SH_InWindowEt(1200, 2000, 0), "asia_2000_incl");
  ASSERT_TRUE (SH_InWindowEt(1380, 2000, 0), "asia_2300_incl");
  ASSERT_FALSE(SH_InWindowEt(1199, 2000, 0), "asia_1959_excl");
  ASSERT_FALSE(SH_InWindowEt(0,    2000, 0), "asia_0000_excl");

  // A genuinely midnight-crossing window 22:00-02:00 = 1320.. || ..120
  ASSERT_TRUE (SH_InWindowEt(1380, 2200, 200), "wrap_2300_in");
  ASSERT_TRUE (SH_InWindowEt(60,   2200, 200), "wrap_0100_in");
  ASSERT_FALSE(SH_InWindowEt(180,  2200, 200), "wrap_0300_out");

  // zero-width window is always false
  ASSERT_FALSE(SH_InWindowEt(120, 200, 200), "zero_width_false");

  Sleep(300);
  TerminalClose(0);
}
```

- [ ] **Step 2: Run test to verify it fails (compile error — SH_Time.mqh missing)**

```bash
python tools/run_sweephunter_selftest.py --name test_sh_time
```
Expected: `[test_sh_time] COMPILE FAILED` (cannot open `SH_Time.mqh`). *(The selftest runner is created in Task 8; until then, this step's failure is the missing include — that is the intended red.)*

- [ ] **Step 3: Write minimal implementation**

```cpp
// SH_Time.mqh — wrap-aware ET session-window predicate. Reuses ORB_Time DST/ET calendars.
#ifndef SH_TIME_MQH
#define SH_TIME_MQH
#include "..\\ORB\\ORB_Time.mqh"   // ORB_EtMinutesFromServer, ORB_ServerToUtcOffsetSec, ORB_UtcToEt

// Is ET minute-of-day `m` inside [startHHMM, endHHMM)? Handles windows that wrap midnight
// (end <= start, e.g. Asia 2000->0000). A zero-width window (start==end) is always false.
bool SH_InWindowEt(int m, int startHHMM, int endHHMM) {
  int s = (startHHMM/100)*60 + (startHHMM%100);
  int e = (endHHMM/100)*60   + (endHHMM%100);
  if (s == e) return false;
  if (s <  e) return (m >= s && m < e);   // same-day
  return (m >= s || m < e);               // wraps midnight
}

// ET minute-of-day for a server timestamp given the server->UTC offset (seconds).
int SH_EtMin(datetime srv, int offsetSec) { return ORB_EtMinutesFromServer(srv, offsetSec); }
#endif
```

- [ ] **Step 4: Run test to verify it passes** (after Task 8 exists, this is the real green; if implementing in order, defer the run to Task 8 Step 3 and just confirm compile here)

```bash
"/c/Program Files/FTMO Global Markets MT5 Terminal/MetaEditor64.exe" \
  /compile:"$APPDATA/MetaQuotes/Terminal/81A933A9AFC5DE3C23B15CAB19C63850/MQL5/Scripts/SweepHunter_Tests/test_sh_time.mq5" \
  /log:"$APPDATA/MetaQuotes/Terminal/81A933A9AFC5DE3C23B15CAB19C63850/MQL5/Logs/sh_compile.log"
```
*(First run `pwsh tools/sync_sweephunter_to_terminal.ps1` to copy sources + ORB_Time into the terminal.)*
Expected (after sync): compile log contains `Result: 0 error`.

- [ ] **Step 5: Commit**

```bash
git add tested-strategies/SweepHunter/mt5/Include/SweepHunter/SH_Time.mqh \
        tested-strategies/SweepHunter/mt5/Scripts/SweepHunter_Tests/test_sh_time.mq5
git commit -m "feat(sweephunter): SH_Time wrap-aware ET session windows + tests"
```

---

## Task 2: SH_Sessions.mqh — scan M1 → Asia/London H/L

**Files:**
- Create: `tested-strategies/SweepHunter/mt5/Include/SweepHunter/SH_Sessions.mqh`
- Test: `tested-strategies/SweepHunter/mt5/Scripts/SweepHunter_Tests/test_sh_sessions.mq5`

- [ ] **Step 1: Write the failing test**

```cpp
// test_sh_sessions.mq5
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Sessions.mqh"

void OnStart() {
  // bars tagged by ET minute-of-day with (high, low)
  int    et[6]  = { 1230, 1380,  130,  240,  600,  900 }; // 20:30,23:00 (Asia); 02:10,04:00 (London); 10:00,15:00 (neither)
  double hi[6]  = {  101,  105,   98,  103,  110,  108 };
  double lo[6]  = {   99,  100,   95,   97,  104,  102 };

  SHLevels L = SH_ComputeLevels(et, hi, lo, 6, 2000, 0, 200, 500);

  ASSERT_TRUE (L.asiaValid, "asia_valid");
  ASSERT_EQ   (L.asiaH, 105.0, "asia_high");   // max(101,105)
  ASSERT_EQ   (L.asiaL, 99.0,  "asia_low");    // min(99,100)
  ASSERT_TRUE (L.lonValid, "lon_valid");
  ASSERT_EQ   (L.lonH, 103.0, "lon_high");     // max(98,103)
  ASSERT_EQ   (L.lonL, 95.0,  "lon_low");      // min(95,97)

  // empty session -> invalid pair, no crash
  int    et2[1] = { 600 };
  double hi2[1] = { 110 };
  double lo2[1] = { 104 };
  SHLevels E = SH_ComputeLevels(et2, hi2, lo2, 1, 2000, 0, 200, 500);
  ASSERT_FALSE(E.asiaValid, "empty_asia_invalid");
  ASSERT_FALSE(E.lonValid,  "empty_lon_invalid");

  Sleep(300);
  TerminalClose(0);
}
```

- [ ] **Step 2: Run to verify it fails**

```bash
python tools/run_sweephunter_selftest.py --name test_sh_sessions
```
Expected: COMPILE FAILED (missing `SH_Sessions.mqh`).

- [ ] **Step 3: Write minimal implementation**

```cpp
// SH_Sessions.mqh — compute Asia/London session high/low by bucketing M1 bars on ET time-of-day.
#ifndef SH_SESSIONS_MQH
#define SH_SESSIONS_MQH
#include "SH_Time.mqh"

struct SHLevels {
  double asiaH, asiaL, lonH, lonL;
  bool   asiaValid, lonValid;
};

// Pure core: parallel arrays of per-bar ET-minute, high, low (length n).
SHLevels SH_ComputeLevels(const int &etmin[], const double &highs[], const double &lows[], int n,
                          int asiaStart, int asiaEnd, int lonStart, int lonEnd) {
  SHLevels L;
  L.asiaH = -DBL_MAX; L.asiaL = DBL_MAX; L.lonH = -DBL_MAX; L.lonL = DBL_MAX;
  L.asiaValid = false; L.lonValid = false;
  for (int i = 0; i < n; i++) {
    if (SH_InWindowEt(etmin[i], asiaStart, asiaEnd)) {
      if (highs[i] > L.asiaH) L.asiaH = highs[i];
      if (lows[i]  < L.asiaL) L.asiaL = lows[i];
      L.asiaValid = true;
    }
    if (SH_InWindowEt(etmin[i], lonStart, lonEnd)) {
      if (highs[i] > L.lonH) L.lonH = highs[i];
      if (lows[i]  < L.lonL) L.lonL = lows[i];
      L.lonValid = true;
    }
  }
  return L;
}

// Live wrapper: scan the last `lookback` closed M1 bars (shift 1..lookback) at mark time.
SHLevels SH_ScanLevels(string sym, int offsetSec, int lookback,
                       int asiaStart, int asiaEnd, int lonStart, int lonEnd) {
  int    etmin[]; double highs[], lows[];
  ArrayResize(etmin, lookback); ArrayResize(highs, lookback); ArrayResize(lows, lookback);
  int n = 0;
  for (int s = 1; s <= lookback; s++) {
    datetime bt = iTime(sym, PERIOD_M1, s);
    if (bt == 0) break;
    etmin[n] = ORB_EtMinutesFromServer(bt, offsetSec);
    highs[n] = iHigh(sym, PERIOD_M1, s);
    lows[n]  = iLow (sym, PERIOD_M1, s);
    n++;
  }
  return SH_ComputeLevels(etmin, highs, lows, n, asiaStart, asiaEnd, lonStart, lonEnd);
}
#endif
```

- [ ] **Step 4: Run to verify it passes**

```bash
python tools/run_sweephunter_selftest.py --name test_sh_sessions
```
Expected: `N passed, 0 failed, 0 malformed` (after Task 8). If implementing before Task 8, confirm `Result: 0 error` from a MetaEditor compile of the test script.

- [ ] **Step 5: Commit**

```bash
git add tested-strategies/SweepHunter/mt5/Include/SweepHunter/SH_Sessions.mqh \
        tested-strategies/SweepHunter/mt5/Scripts/SweepHunter_Tests/test_sh_sessions.mq5
git commit -m "feat(sweephunter): SH_Sessions Asia/London H-L bucketing + tests"
```

---

## Task 3: SH_FVG.mqh — 3-candle FVG detection + entry edge

**Files:**
- Create: `tested-strategies/SweepHunter/mt5/Include/SweepHunter/SH_FVG.mqh`
- Test: `tested-strategies/SweepHunter/mt5/Scripts/SweepHunter_Tests/test_sh_fvg.mq5`

- [ ] **Step 1: Write the failing test**

```cpp
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
```

- [ ] **Step 2: Run to verify it fails**

```bash
python tools/run_sweephunter_selftest.py --name test_sh_fvg
```
Expected: COMPILE FAILED (missing `SH_FVG.mqh`).

- [ ] **Step 3: Write minimal implementation**

```cpp
// SH_FVG.mqh — 3-candle fair value gap detection and entry pricing.
// Bars indexed oldest->newest as (h2,l2),(h1,l1),(h0,l0); middle bar not needed for the gap test.
#ifndef SH_FVG_MQH
#define SH_FVG_MQH

// dir +1 = look for a BULLISH FVG (for a long); dir -1 = BEARISH (for a short).
bool SH_IsFVG(int dir, double h2,double l2, double h1,double l1, double h0,double l0) {
  if (dir > 0) return (h2 < l0);   // bullish: newest low above oldest high
  if (dir < 0) return (l2 > h0);   // bearish: newest high below oldest low
  return false;
}

// Proximal edge = the gap boundary the retracement reaches first.
double SH_FvgProximal(int dir, double h2,double l2, double h0,double l0) {
  return (dir > 0) ? l0 : h0;
}
// Distal edge = the far boundary.
double SH_FvgDistal(int dir, double h2,double l2, double h0,double l0) {
  return (dir > 0) ? h2 : l2;
}
// Entry at fill depth in [0,1]: 0 = proximal (fills first), 1 = distal (deepest).
double SH_FvgEntry(int dir, double h2,double l2, double h0,double l0, double depth) {
  double p = SH_FvgProximal(dir, h2,l2, h0,l0);
  double d = SH_FvgDistal  (dir, h2,l2, h0,l0);
  return p + depth*(d - p);
}
#endif
```

- [ ] **Step 4: Run to verify it passes**

```bash
python tools/run_sweephunter_selftest.py --name test_sh_fvg
```
Expected: `N passed, 0 failed, 0 malformed`.

- [ ] **Step 5: Commit**

```bash
git add tested-strategies/SweepHunter/mt5/Include/SweepHunter/SH_FVG.mqh \
        tested-strategies/SweepHunter/mt5/Scripts/SweepHunter_Tests/test_sh_fvg.mq5
git commit -m "feat(sweephunter): SH_FVG 3-candle detection + entry edge + tests"
```

---

## Task 4: SH_Sweep.mqh — sweep test + swing tracker

**Files:**
- Create: `tested-strategies/SweepHunter/mt5/Include/SweepHunter/SH_Sweep.mqh`
- Test: `tested-strategies/SweepHunter/mt5/Scripts/SweepHunter_Tests/test_sh_sweep.mq5`

- [ ] **Step 1: Write the failing test**

```cpp
// test_sh_sweep.mq5
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Sweep.mqh"

void OnStart() {
  // side +1 = a HIGH level: swept when bar high exceeds it.
  ASSERT_TRUE (SH_Swept(+1, 105.0, 100.0, 104.0), "high_swept");
  ASSERT_FALSE(SH_Swept(+1, 103.0, 100.0, 104.0), "high_not_swept");
  // side -1 = a LOW level: swept when bar low drops below it.
  ASSERT_TRUE (SH_Swept(-1, 100.0,  95.0,  96.0), "low_swept");
  ASSERT_FALSE(SH_Swept(-1, 100.0,  97.0,  96.0), "low_not_swept");

  // Direction: sweeping a high -> short; sweeping a low -> long.
  ASSERT_EQ_INT(SH_DirFromSweepSide(+1), -1, "high_sweep_short");
  ASSERT_EQ_INT(SH_DirFromSweepSide(-1), +1, "low_sweep_long");

  // Swing: short tracks highest high; long tracks lowest low.
  ASSERT_EQ(SH_UpdateSwing(-1, 105.0, 107.0, 102.0), 107.0, "short_swing_up");
  ASSERT_EQ(SH_UpdateSwing(-1, 105.0, 104.0, 102.0), 105.0, "short_swing_keep");
  ASSERT_EQ(SH_UpdateSwing(+1,  95.0,  98.0,  93.0), 93.0,  "long_swing_down");
  ASSERT_EQ(SH_UpdateSwing(+1,  95.0,  98.0,  96.0), 95.0,  "long_swing_keep");

  Sleep(300);
  TerminalClose(0);
}
```

- [ ] **Step 2: Run to verify it fails**

```bash
python tools/run_sweephunter_selftest.py --name test_sh_sweep
```
Expected: COMPILE FAILED (missing `SH_Sweep.mqh`).

- [ ] **Step 3: Write minimal implementation**

```cpp
// SH_Sweep.mqh — liquidity sweep detection and post-sweep swing tracking.
#ifndef SH_SWEEP_MQH
#define SH_SWEEP_MQH

// side +1 = high level (swept when bar high > level); side -1 = low level (swept when bar low < level).
bool SH_Swept(int side, double barHigh, double barLow, double level) {
  return (side > 0) ? (barHigh > level) : (barLow < level);
}

// Trade direction after a sweep: sweeping a high -> SHORT (-1); sweeping a low -> LONG (+1).
int SH_DirFromSweepSide(int side) { return (side > 0) ? -1 : +1; }

// Running swing extreme since the sweep: SHORT tracks highest high, LONG tracks lowest low.
double SH_UpdateSwing(int dir, double prevSwing, double barHigh, double barLow) {
  if (dir < 0) return MathMax(prevSwing, barHigh);
  return MathMin(prevSwing, barLow);
}
#endif
```

- [ ] **Step 4: Run to verify it passes**

```bash
python tools/run_sweephunter_selftest.py --name test_sh_sweep
```
Expected: `N passed, 0 failed, 0 malformed`.

- [ ] **Step 5: Commit**

```bash
git add tested-strategies/SweepHunter/mt5/Include/SweepHunter/SH_Sweep.mqh \
        tested-strategies/SweepHunter/mt5/Scripts/SweepHunter_Tests/test_sh_sweep.mq5
git commit -m "feat(sweephunter): SH_Sweep detection + swing tracker + tests"
```

---

## Task 5: SH_Targets.mqh — RR + draw-on-liquidity targets

**Files:**
- Create: `tested-strategies/SweepHunter/mt5/Include/SweepHunter/SH_Targets.mqh`
- Test: `tested-strategies/SweepHunter/mt5/Scripts/SweepHunter_Tests/test_sh_targets.mq5`

- [ ] **Step 1: Write the failing test**

```cpp
// test_sh_targets.mq5
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Targets.mqh"

void OnStart() {
  ASSERT_EQ(SH_R(100.0, 98.0), 2.0, "risk_distance");

  // RR target: long 2R from entry 100 risk 2 -> 104; short -> 96.
  ASSERT_EQ(SH_TargetRR(+1, 100.0, 2.0, 2.0), 104.0, "rr_long");
  ASSERT_EQ(SH_TargetRR(-1, 100.0, 2.0, 2.0),  96.0, "rr_short");

  // DOL long: levels above entry, pick nearest (lowest above).
  double lv[4] = { 95.0, 103.0, 107.0, 99.0 };
  bool found;
  double dolL = SH_TargetDOL(+1, 100.0, lv, 4, 999.0, found);
  ASSERT_TRUE(found, "dol_long_found");
  ASSERT_EQ(dolL, 103.0, "dol_long_nearest_above");

  // DOL short: levels below entry, pick nearest (highest below).
  double dolS = SH_TargetDOL(-1, 100.0, lv, 4, 999.0, found);
  ASSERT_TRUE(found, "dol_short_found");
  ASSERT_EQ(dolS, 99.0, "dol_short_nearest_below");

  // DOL fallback: no level in direction -> return fallback, found=false.
  double only_below[2] = { 90.0, 95.0 };
  double fb = SH_TargetDOL(+1, 100.0, only_below, 2, 108.0, found);
  ASSERT_FALSE(found, "dol_fallback_notfound");
  ASSERT_EQ(fb, 108.0, "dol_fallback_value");

  Sleep(300);
  TerminalClose(0);
}
```

- [ ] **Step 2: Run to verify it fails**

```bash
python tools/run_sweephunter_selftest.py --name test_sh_targets
```
Expected: COMPILE FAILED (missing `SH_Targets.mqh`).

- [ ] **Step 3: Write minimal implementation**

```cpp
// SH_Targets.mqh — risk distance, fixed-RR target, and draw-on-liquidity target.
#ifndef SH_TARGETS_MQH
#define SH_TARGETS_MQH

double SH_R(double entry, double stop) { return MathAbs(entry - stop); }

double SH_TargetRR(int dir, double entry, double R, double rr) { return entry + dir*rr*R; }

// Nearest un-swept marked level strictly beyond entry in the trade direction.
// LONG (+1): lowest level above entry. SHORT (-1): highest level below entry.
// If none qualifies, return `rrFallback` and set found=false.
double SH_TargetDOL(int dir, double entry, const double &levels[], int n, double rrFallback, bool &found) {
  found = false;
  double best = 0.0;
  for (int i = 0; i < n; i++) {
    double lv = levels[i];
    if (dir > 0 && lv > entry) { if (!found || lv < best) { best = lv; found = true; } }
    if (dir < 0 && lv < entry) { if (!found || lv > best) { best = lv; found = true; } }
  }
  return found ? best : rrFallback;
}
#endif
```

- [ ] **Step 4: Run to verify it passes**

```bash
python tools/run_sweephunter_selftest.py --name test_sh_targets
```
Expected: `N passed, 0 failed, 0 malformed`.

- [ ] **Step 5: Commit**

```bash
git add tested-strategies/SweepHunter/mt5/Include/SweepHunter/SH_Targets.mqh \
        tested-strategies/SweepHunter/mt5/Scripts/SweepHunter_Tests/test_sh_targets.mq5
git commit -m "feat(sweephunter): SH_Targets RR + draw-on-liquidity + tests"
```

---

## Task 6: SH_Stops.mqh + SH_Risk.mqh — stop placement + lot sizing

**Files:**
- Create: `tested-strategies/SweepHunter/mt5/Include/SweepHunter/SH_Stops.mqh`
- Create: `tested-strategies/SweepHunter/mt5/Include/SweepHunter/SH_Risk.mqh`
- Test: `tested-strategies/SweepHunter/mt5/Scripts/SweepHunter_Tests/test_sh_stops.mq5`

- [ ] **Step 1: Write the failing test**

```cpp
// test_sh_stops.mq5
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Stops.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Risk.mqh"

void OnStart() {
  // Long: stop below swing low by buffer. Short: stop above swing high by buffer.
  ASSERT_EQ(SH_Stop(+1, 95.0, 0.5),  94.5, "long_stop_below_swing");
  ASSERT_EQ(SH_Stop(-1, 105.0, 0.5), 105.5, "short_stop_above_swing");

  // Lots from risk: equity 10000, risk 1% = $100; SL dist 2.0 units; $1/unit/lot -> 50 lots,
  // capped at volMax 10 -> 10.0; step 0.01, min 0.01.
  ASSERT_EQ(SH_LotsFromRisk(10000, 1.0, 2.0, 1.0, 0.01, 0.01, 10.0), 10.0, "lots_capped");
  // risk too small -> below volMin -> 0.
  ASSERT_EQ(SH_LotsFromRisk(10000, 0.0001, 2.0, 1.0, 0.01, 0.01, 10.0), 0.0, "lots_zero_below_min");
  // invalid SL dist -> 0.
  ASSERT_EQ(SH_LotsFromRisk(10000, 1.0, 0.0, 1.0, 0.01, 0.01, 10.0), 0.0, "lots_zero_bad_sl");

  Sleep(300);
  TerminalClose(0);
}
```

- [ ] **Step 2: Run to verify it fails**

```bash
python tools/run_sweephunter_selftest.py --name test_sh_stops
```
Expected: COMPILE FAILED (missing `SH_Stops.mqh` / `SH_Risk.mqh`).

- [ ] **Step 3: Write minimal implementations**

`SH_Stops.mqh`:
```cpp
// SH_Stops.mqh — stop just beyond the post-sweep swing.
#ifndef SH_STOPS_MQH
#define SH_STOPS_MQH
// LONG (+1): stop below swing low by buffer. SHORT (-1): stop above swing high by buffer.
double SH_Stop(int dir, double swing, double buffer) {
  return (dir > 0) ? (swing - buffer) : (swing + buffer);
}
#endif
```

`SH_Risk.mqh` (vendored copy of ORB_LotsFromRisk, renamed — keeps SweepHunter self-contained):
```cpp
// SH_Risk.mqh — position size from fixed fractional risk. (Same math as ORB_LotsFromRisk.)
#ifndef SH_RISK_MQH
#define SH_RISK_MQH
double SH_LotsFromRisk(double equity, double riskPct, double slDistUnits,
                       double valuePerUnitPerLot, double volStep, double volMin, double volMax) {
  if (slDistUnits <= 0.0 || valuePerUnitPerLot <= 0.0) return 0.0;
  double riskAmt = equity*(riskPct/100.0);
  double raw     = riskAmt/(slDistUnits*valuePerUnitPerLot);
  double lots    = MathFloor(raw/volStep)*volStep;
  if (lots > volMax) lots = volMax;
  if (lots < volMin) return 0.0;
  return lots;
}
#endif
```

- [ ] **Step 4: Run to verify it passes**

```bash
python tools/run_sweephunter_selftest.py --name test_sh_stops
```
Expected: `N passed, 0 failed, 0 malformed`.

- [ ] **Step 5: Commit**

```bash
git add tested-strategies/SweepHunter/mt5/Include/SweepHunter/SH_Stops.mqh \
        tested-strategies/SweepHunter/mt5/Include/SweepHunter/SH_Risk.mqh \
        tested-strategies/SweepHunter/mt5/Scripts/SweepHunter_Tests/test_sh_stops.mq5
git commit -m "feat(sweephunter): SH_Stops + SH_Risk sizing + tests"
```

---

## Task 7: SH_Ledger.mqh — gate-compatible CSV ledger

**Files:**
- Create: `tested-strategies/SweepHunter/mt5/Include/SweepHunter/SH_Ledger.mqh`

*(No unit test: this is thin file I/O exercised by the smoke backtest in Task 10. The contract is the header — it must include `net_pnl` so `tools/orb_gate.py` reads it directly.)*

- [ ] **Step 1: Write implementation**

```cpp
// SH_Ledger.mqh — one UTF-8 CSV row per closed trade, written FILE_COMMON so the
// Strategy Tester and live share the same path. Header is gate-compatible (net_pnl).
#ifndef SH_LEDGER_MQH
#define SH_LEDGER_MQH
int SH_LedgerOpen(string path) {
  int h = FileOpen(path, FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON, ",");
  if (h != INVALID_HANDLE)
    FileWrite(h, "trade_id","symbol","dir","ts_open_utc","ts_close_utc","entry","sl","tp",
                 "lots","exit_reason","gross_pnl","commission","swap","net_pnl","r_multiple",
                 "swept_level","sweep_side","target_mode","fill_depth");
  return h;
}
void SH_LedgerRow(int h,int id,string sym,int dir,datetime to,datetime tc,double entry,double sl,
                  double tp,double lots,string reason,double gross,double comm,double swap,double net,
                  double rmult,double sweptLevel,int sweepSide,string targetMode,double fillDepth) {
  if (h == INVALID_HANDLE) return;
  FileWrite(h, id, sym, (dir>0?"long":"short"), (string)(long)to, (string)(long)tc, entry, sl, tp,
               lots, reason, gross, comm, swap, net, rmult,
               sweptLevel, sweepSide, targetMode, fillDepth);
}
void SH_LedgerClose(int h) { if (h != INVALID_HANDLE) FileClose(h); }
#endif
```

- [ ] **Step 2: Commit**

```bash
git add tested-strategies/SweepHunter/mt5/Include/SweepHunter/SH_Ledger.mqh
git commit -m "feat(sweephunter): SH_Ledger gate-compatible trade ledger"
```

---

## Task 8: run_sweephunter_selftest.py — headless test runner; full green

**Files:**
- Create: `tools/run_sweephunter_selftest.py`

- [ ] **Step 1: Write the runner** (adapted from `tools/run_orb_selftest.py`, reusing its tested parse layer)

```python
#!/usr/bin/env python
"""Headless SweepHunter MQL5 self-test runner (FTMO terminal).

Mirrors run_orb_selftest.py: sync -> MetaEditor /compile -> [StartUp] ini ->
cold-start terminal64 /config (script self-closes via TerminalClose) -> parse
MQL5TEST sentinels with the tested parse layer from run_mql5_tests.
`/Script:` is broken on this build; /config + [StartUp] is the working path.
"""
from __future__ import annotations
import argparse, os, re, subprocess, sys, time
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from run_mql5_tests import parse_log_file, TestResults

FTMO_DATA = Path(os.environ["APPDATA"]) / "MetaQuotes/Terminal/81A933A9AFC5DE3C23B15CAB19C63850"
TERMINAL = Path(r"C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe")
MEDITOR  = Path(r"C:\Program Files\FTMO Global Markets MT5 Terminal\MetaEditor64.exe")
SCRIPTS_SUBDIR = "SweepHunter_Tests"
REPO = Path(__file__).resolve().parents[1]


def _close_terminals():
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-Process terminal64 -ErrorAction SilentlyContinue | "
         "ForEach-Object { $null = $_.CloseMainWindow() }"],
        check=False,
    )
    time.sleep(3)


def _sync():
    subprocess.run(["pwsh", str(REPO / "tools" / "sync_sweephunter_to_terminal.ps1")], check=False)


def compile_test(name, data_dir=FTMO_DATA, meditor=MEDITOR):
    mq5 = data_dir / "MQL5" / "Scripts" / SCRIPTS_SUBDIR / f"{name}.mq5"
    log = data_dir / "sh_compile.log"
    subprocess.run([str(meditor), f"/compile:{mq5}", f"/log:{log}"], check=False)
    time.sleep(2)
    txt = log.read_text(encoding="utf-16", errors="ignore") if log.exists() else ""
    last = txt.strip().splitlines()[-1] if txt.strip() else "no compile log"
    m = re.search(r"Result:\s*(\d+)\s*error", txt)
    ok = (m is not None and int(m.group(1)) == 0)
    return ok, last


def run_test(name, data_dir=FTMO_DATA, terminal=TERMINAL, timeout=120):
    ini = data_dir / f"sh_selftest_{name}.ini"
    ini.write_text(
        f"[StartUp]\nScript={SCRIPTS_SUBDIR}\\{name}\nSymbol=EURUSD\nPeriod=M5\n",
        encoding="ascii",
    )
    logdir = data_dir / "MQL5" / "Logs"
    for f in logdir.glob("2*.log"):
        try:
            f.unlink()
        except OSError:
            pass
    try:
        subprocess.run([str(terminal), f"/config:{ini}"], check=False, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"[{name}] TIMEOUT — terminal did not self-close")
        _close_terminals()
    logs = sorted(logdir.glob("2*.log"))
    return parse_log_file(logs[-1]) if logs else TestResults()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--name", help="single test (e.g. test_sh_fvg); default runs all test_sh_*")
    ap.add_argument("--no-sync", action="store_true")
    args = ap.parse_args(argv)

    if not args.no_sync:
        _sync()
    _close_terminals()

    src_dir = REPO / "tested-strategies" / "SweepHunter" / "mt5" / "Scripts" / SCRIPTS_SUBDIR
    names = [args.name] if args.name else [p.stem for p in sorted(src_dir.glob("test_sh_*.mq5"))]
    if not names:
        print("no test_sh_*.mq5 scripts found")
        return 1

    results = []
    for nm in names:
        ok, line = compile_test(nm)
        print(f"[{nm}] compile: {line}")
        if not ok:
            print(f"[{nm}] COMPILE FAILED")
            results.append(TestResults(failed=1))
            continue
        r = run_test(nm)
        print(f"[{nm}] {r.passed} passed, {r.failed} failed, {r.malformed} malformed")
        for f in r.failures:
            print(f"    FAIL {f['test']}: expected={f['expected']} got={f['got']}")
        results.append(r)

    merged = TestResults.merge(results)
    print(f"=== TOTAL {merged.passed} passed, {merged.failed} failed, {merged.malformed} malformed ===")
    return merged.exit_code


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run the full suite — all modules green**

```bash
python tools/run_sweephunter_selftest.py
```
Expected: every `test_sh_*` prints `M passed, 0 failed, 0 malformed`, ending `=== TOTAL N passed, 0 failed, 0 malformed ===`, exit code 0. If any FAIL, fix the corresponding module (Tasks 1–6) before continuing.

- [ ] **Step 3: Commit**

```bash
git add tools/run_sweephunter_selftest.py
git commit -m "tooling(sweephunter): headless self-test runner; suite green"
```

---

## Task 9: SweepHunter_EA.mq5 — orchestrator state machine

**Files:**
- Create: `tested-strategies/SweepHunter/mt5/Experts/SweepHunter/SweepHunter_EA.mq5`

- [ ] **Step 1: Write the EA** (mirrors ORB_EA structure: inputs → globals → OnInit/OnTick/OnTradeTransaction/OnTester)

```cpp
//+------------------------------------------------------------------+
//|  SweepHunter_EA.mq5 — Asia/London sweep -> NY M1 FVG reversal     |
//+------------------------------------------------------------------+
#property copyright "NotFinancialAdvice"
#property version   "1.00"
#property strict

#include <Trade\Trade.mqh>
#include "..\\..\\Include\\SweepHunter\\SH_Time.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Sessions.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Sweep.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_FVG.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Targets.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Stops.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Risk.mqh"
#include "..\\..\\Include\\SweepHunter\\SH_Ledger.mqh"

//--- inputs
input long   InpMagic          = 20260622;
input int    InpAsiaStartEt    = 2000;
input int    InpAsiaEndEt      = 0;       // 0000
input int    InpLonStartEt     = 200;
input int    InpLonEndEt       = 500;
input int    InpMarkEt         = 900;
input int    InpHuntStartEt    = 900;
input int    InpHuntEndEt      = 1130;
input int    InpFlatEt         = 1600;
input int    InpLevelMode      = 0;       // 0=FOUR, 1=COMBINED
input int    InpEntryMode      = 0;       // 0=LIMIT, 1=MARKET
input double InpFillDepth      = 0.0;     // 0=proximal..1=distal
input int    InpTargetMode     = 0;       // 0=RR, 1=DOL
input double InpTargetRR       = 2.0;
input double InpStopBufferAtrK = 0.15;
input int    InpAtrPeriod      = 14;
input int    InpScanLookback   = 900;     // M1 bars scanned at mark (>= 15h)
input double InpRiskPct        = 1.0;
input double InpMaxLot         = 50.0;
input int    InpSrvToUtcOffsetSec = 999999; // 999999 = auto-detect per tick
input string InpLedgerLabel    = "smoke";

//--- globals
CTrade   g_trade;
int      g_atrHandle;
int      g_srvOffsetSec;
int      g_ledger;

enum SHState { WAIT, MARKED, ARMED, INTRADE, DONE };
SHState  g_state;
int      g_curDayEt;
datetime g_lastBar;            // last processed M1 bar time (new-bar detection)

SHLevels g_lvl;
double   g_levelArr[4];        // marked levels for DOL candidates
int      g_levelN;

bool     g_marked;
int      g_setupDir;           // +1 long, -1 short
int      g_sweptSide;          // +1 high, -1 low
double   g_sweptLevel;
double   g_swing;              // running swing extreme since sweep
ulong    g_pendTicket, g_posTicket;

// open-trade context consumed by OnTradeTransaction on the OUT deal
int      g_tDir; double g_tEntry,g_tSL,g_tTP,g_tR,g_tSwept; int g_tSide; double g_tDepth;
datetime g_tOpen; string g_exitReason;

double AtrVal();
void   ResetDay();
void   TryMark(int etMin);
void   TryArm();
void   TryEnter();
void   ManageTrade(datetime srv,int etMin);
void   CloseTrade(string reason);
string TargetModeStr(){ return (InpTargetMode==1)?"DOL":"RR"; }

int OnInit() {
  g_atrHandle = iATR(_Symbol, PERIOD_M1, InpAtrPeriod);
  if (g_atrHandle == INVALID_HANDLE) return INIT_FAILED;
  g_trade.SetExpertMagicNumber((ulong)InpMagic);
  string lp = StringFormat("SweepHunter\\ledger_%s.csv", InpLedgerLabel);
  g_ledger = SH_LedgerOpen(lp);
  g_curDayEt = -1; g_lastBar = 0; g_exitReason = "";
  ResetDay();
  return INIT_SUCCEEDED;
}

void OnDeinit(const int r) {
  if (g_posTicket > 0 && PositionSelectByTicket(g_posTicket)) CloseTrade("forced_eod");
  SH_LedgerClose(g_ledger);
  IndicatorRelease(g_atrHandle);
}

double AtrVal() {
  double b[];
  if (CopyBuffer(g_atrHandle, 0, 1, 1, b) < 1) return 0.0;
  return b[0];
}

void ResetDay() {
  g_state = WAIT; g_marked = false; g_levelN = 0;
  g_setupDir = 0; g_sweptSide = 0; g_sweptLevel = 0; g_swing = 0;
  g_pendTicket = 0; g_posTicket = 0;
}

void OnTick() {
  datetime srv = TimeCurrent();
  g_srvOffsetSec = (InpSrvToUtcOffsetSec != 999999) ? InpSrvToUtcOffsetSec
                                                    : ORB_ServerToUtcOffsetSec(srv);
  int etMin = SH_EtMin(srv, g_srvOffsetSec);
  MqlDateTime et; TimeToStruct(ORB_UtcToEt(srv - g_srvOffsetSec), et);

  if (et.day_of_year != g_curDayEt) { g_curDayEt = et.day_of_year; ResetDay(); }

  // act once per closed M1 bar
  datetime bar = iTime(_Symbol, PERIOD_M1, 0);
  bool newBar = (bar != g_lastBar);
  if (newBar) g_lastBar = bar;

  if (g_state == WAIT && etMin >= InpMarkEt/100*60 + InpMarkEt%100) { TryMark(etMin); return; }
  if (!newBar && g_state != INTRADE) return;

  if (g_state == MARKED && SH_InWindowEt(etMin, InpHuntStartEt, InpHuntEndEt)) TryArm();
  if (g_state == ARMED) {
    // cancel unfilled limit at hunt end
    if (!SH_InWindowEt(etMin, InpHuntStartEt, InpHuntEndEt)) {
      if (g_pendTicket > 0) g_trade.OrderDelete(g_pendTicket);
      g_state = DONE; return;
    }
    // fill detection
    if (g_pendTicket > 0 && PositionSelectByTicket(g_pendTicket)) {
      g_posTicket = g_pendTicket; g_pendTicket = 0; g_state = INTRADE;
      g_tEntry = PositionGetDouble(POSITION_PRICE_OPEN);
      g_tSL = PositionGetDouble(POSITION_SL); g_tTP = PositionGetDouble(POSITION_TP);
      g_tDir = (PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY)?+1:-1;
      g_tR = SH_R(g_tEntry, g_tSL); g_tOpen = (datetime)(long)PositionGetInteger(POSITION_TIME);
    } else {
      g_swing = SH_UpdateSwing(g_setupDir, g_swing, iHigh(_Symbol,PERIOD_M1,1), iLow(_Symbol,PERIOD_M1,1));
      TryEnter();
    }
  }
  if (g_state == INTRADE) ManageTrade(srv, etMin);
}

void TryMark(int etMin) {
  g_lvl = SH_ScanLevels(_Symbol, g_srvOffsetSec, InpScanLookback,
                        InpAsiaStartEt, InpAsiaEndEt, InpLonStartEt, InpLonEndEt);
  g_levelN = 0;
  if (InpLevelMode == 1) { // COMBINED outer H/L
    double hi=-DBL_MAX, lo=DBL_MAX; bool ok=false;
    if (g_lvl.asiaValid){ hi=MathMax(hi,g_lvl.asiaH); lo=MathMin(lo,g_lvl.asiaL); ok=true; }
    if (g_lvl.lonValid){  hi=MathMax(hi,g_lvl.lonH);  lo=MathMin(lo,g_lvl.lonL);  ok=true; }
    if (ok){ g_levelArr[g_levelN++]=hi; g_levelArr[g_levelN++]=lo; }
  } else {                 // FOUR distinct
    if (g_lvl.asiaValid){ g_levelArr[g_levelN++]=g_lvl.asiaH; g_levelArr[g_levelN++]=g_lvl.asiaL; }
    if (g_lvl.lonValid){  g_levelArr[g_levelN++]=g_lvl.lonH;  g_levelArr[g_levelN++]=g_lvl.lonL; }
  }
  g_state = (g_levelN > 0) ? MARKED : DONE;
  g_marked = (g_levelN > 0);
}

// Each level is paired (high then low). Determine side from its index parity.
void TryArm() {
  double hi = iHigh(_Symbol, PERIOD_M1, 1), lo = iLow(_Symbol, PERIOD_M1, 1);
  for (int i = 0; i < g_levelN; i++) {
    int side = (i % 2 == 0) ? +1 : -1;   // even idx = high level, odd = low level
    if (SH_Swept(side, hi, lo, g_levelArr[i])) {
      g_sweptSide = side; g_sweptLevel = g_levelArr[i];
      g_setupDir = SH_DirFromSweepSide(side);
      g_swing = (g_setupDir < 0) ? hi : lo;   // seed swing with the sweep bar
      g_state = ARMED;
      return;
    }
  }
}

void TryEnter() {
  double h2=iHigh(_Symbol,PERIOD_M1,3), l2=iLow(_Symbol,PERIOD_M1,3);
  double h1=iHigh(_Symbol,PERIOD_M1,2), l1=iLow(_Symbol,PERIOD_M1,2);
  double h0=iHigh(_Symbol,PERIOD_M1,1), l0=iLow(_Symbol,PERIOD_M1,1);
  if (!SH_IsFVG(g_setupDir, h2,l2, h1,l1, h0,l0)) return;

  double entry = (InpEntryMode==1)
                 ? ((g_setupDir>0)?SymbolInfoDouble(_Symbol,SYMBOL_ASK):SymbolInfoDouble(_Symbol,SYMBOL_BID))
                 : SH_FvgEntry(g_setupDir, h2,l2, h0,l0, InpFillDepth);
  double atr    = AtrVal();
  double buffer = InpStopBufferAtrK * atr;
  double sl     = SH_Stop(g_setupDir, g_swing, buffer);
  double R      = SH_R(entry, sl);
  if (R <= 0.0) { g_state = DONE; return; }

  double tp;
  if (InpTargetMode == 1) { bool found; tp = SH_TargetDOL(g_setupDir, entry, g_levelArr, g_levelN,
                                              SH_TargetRR(g_setupDir, entry, R, InpTargetRR), found); }
  else                    { tp = SH_TargetRR(g_setupDir, entry, R, InpTargetRR); }

  double tickVal=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_VALUE);
  double tickSize=SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);
  double valPerUnit=(tickSize>0.0)?(tickVal/tickSize):0.0;
  double lots = SH_LotsFromRisk(AccountInfoDouble(ACCOUNT_EQUITY), InpRiskPct, R, valPerUnit,
                                SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP),
                                SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN), InpMaxLot);
  if (lots <= 0.0) { g_state = DONE; return; }

  // context for the ledger
  g_tDir=g_setupDir; g_tSide=g_sweptSide; g_tSwept=g_sweptLevel; g_tDepth=InpFillDepth;

  bool ok;
  if (InpEntryMode == 1)
    ok = (g_setupDir>0) ? g_trade.Buy(lots,_Symbol,entry,sl,tp) : g_trade.Sell(lots,_Symbol,entry,sl,tp);
  else
    ok = (g_setupDir>0) ? g_trade.BuyLimit(lots,entry,_Symbol,sl,tp,ORDER_TIME_GTC,0,"")
                        : g_trade.SellLimit(lots,entry,_Symbol,sl,tp,ORDER_TIME_GTC,0,"");
  if (ok) g_pendTicket = g_trade.ResultOrder();
  else    g_state = DONE;
}

void ManageTrade(datetime srv,int etMin) {
  if (!PositionSelectByTicket(g_posTicket)) { g_state = DONE; return; } // SL/TP closed it
  if (etMin >= InpFlatEt/100*60 + InpFlatEt%100) CloseTrade("forced_eod");
}

void CloseTrade(string reason) {
  if (!PositionSelectByTicket(g_posTicket)) return;
  g_exitReason = reason; g_trade.PositionClose(g_posTicket); g_state = DONE;
}

void OnTradeTransaction(const MqlTradeTransaction &trans, const MqlTradeRequest &request,
                        const MqlTradeResult &result) {
  if (trans.type != TRADE_TRANSACTION_DEAL_ADD) return;
  ulong deal = trans.deal;
  if (!HistoryDealSelect(deal)) return;
  if ((long)HistoryDealGetInteger(deal, DEAL_MAGIC) != InpMagic) return;
  if ((ENUM_DEAL_ENTRY)HistoryDealGetInteger(deal, DEAL_ENTRY) != DEAL_ENTRY_OUT) return;

  double exitPx=HistoryDealGetDouble(deal,DEAL_PRICE), profit=HistoryDealGetDouble(deal,DEAL_PROFIT);
  double swap=HistoryDealGetDouble(deal,DEAL_SWAP), comm=HistoryDealGetDouble(deal,DEAL_COMMISSION);
  double lots=HistoryDealGetDouble(deal,DEAL_VOLUME);
  ENUM_DEAL_REASON dr=(ENUM_DEAL_REASON)HistoryDealGetInteger(deal,DEAL_REASON);
  string reason=(dr==DEAL_REASON_SL)?"sl_hit":(dr==DEAL_REASON_TP)?"tp_hit":
                (g_exitReason!=""?g_exitReason:"expert");
  double rmult=(g_tR>0.0)?(((g_tDir>0)?(exitPx-g_tEntry):(g_tEntry-exitPx))/g_tR):0.0;

  SH_LedgerRow(g_ledger, 0, _Symbol, g_tDir,
               (datetime)((long)g_tOpen-(long)g_srvOffsetSec),
               (datetime)((long)TimeCurrent()-(long)g_srvOffsetSec),
               g_tEntry, g_tSL, g_tTP, lots, reason, profit, comm, swap, profit+swap+comm, rmult,
               g_tSwept, g_tSide, TargetModeStr(), g_tDepth);
  g_exitReason = "";
}

double OnTester() {
  double t = TesterStatistics(STAT_TRADES);
  return (t > 0.0) ? TesterStatistics(STAT_PROFIT)/t : 0.0;
}
```

- [ ] **Step 2: Compile clean**

```bash
pwsh tools/sync_sweephunter_to_terminal.ps1
"/c/Program Files/FTMO Global Markets MT5 Terminal/MetaEditor64.exe" \
  /compile:"$APPDATA/MetaQuotes/Terminal/81A933A9AFC5DE3C23B15CAB19C63850/MQL5/Experts/SweepHunter/SweepHunter_EA.mq5" \
  /log:"$APPDATA/MetaQuotes/Terminal/81A933A9AFC5DE3C23B15CAB19C63850/MQL5/Logs/sh_ea_compile.log"
```
Expected: the log's last `Result:` line reads `Result: 0 errors, 0 warnings` (read the UTF-16 log; warnings about unused `request`/`result` params are acceptable but aim for 0).

- [ ] **Step 3: Commit**

```bash
git add tested-strategies/SweepHunter/mt5/Experts/SweepHunter/SweepHunter_EA.mq5
git commit -m "feat(sweephunter): orchestrator EA state machine; compiles clean"
```

---

## Task 10: run_sweephunter_backtest.py + smoke run

**Files:**
- Create: `tools/run_sweephunter_backtest.py`
- Create: `tested-strategies/SweepHunter/mt5/Presets/SweepHunter_smoke.set`

- [ ] **Step 1: Write the single-run backtest driver** (adapted from `tools/run_orb_backtest.py`)

```python
"""Drive one headless MT5 Strategy Tester run for SweepHunter; return the EA ledger path."""
from __future__ import annotations
import os, subprocess, time
from pathlib import Path

FTMO_DATA = Path(os.environ["APPDATA"]) / "MetaQuotes/Terminal/81A933A9AFC5DE3C23B15CAB19C63850"
TERMINAL = Path(r"C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe")

def build_tester_ini(symbol, from_date, to_date, expert, set_file, report, label):
    return "\n".join([
        "[Tester]", f"Expert={expert}", f"Symbol={symbol}", "Period=M1", "Model=1",
        "Optimization=0", f"FromDate={from_date}", f"ToDate={to_date}", "Deposit=10000",
        "Currency=USD", "Leverage=1:100", f"Report={report}", "ReplaceReport=1",
        "ShutdownTerminal=1", f"ExpertParameters={set_file}", "",
    ])

def ledger_path_for(data_dir, label):
    return str(Path(data_dir).parent / "Common" / "Files" / "SweepHunter" / f"ledger_{label}.csv")

def run(symbol, from_date, to_date, set_file, label, data_dir=FTMO_DATA, terminal=TERMINAL, timeout=1800):
    report = str(Path(data_dir) / f"sh_report_{label}.htm")
    ini = build_tester_ini(symbol, from_date, to_date, "SweepHunter\\SweepHunter_EA.ex5", set_file, report, label)
    ini_path = Path(data_dir) / f"sh_tester_{label}.ini"
    ini_path.write_text(ini, encoding="utf-16")
    tester_presets = Path(data_dir) / "MQL5" / "Profiles" / "Tester"
    tester_presets.mkdir(parents=True, exist_ok=True)
    src_set = Path("tested-strategies/SweepHunter/mt5/Presets") / set_file
    lines = [ln for ln in src_set.read_text().splitlines() if not ln.strip().startswith("InpLedgerLabel=")]
    lines.append(f"InpLedgerLabel={label}")
    (tester_presets / set_file).write_text("\n".join(lines) + "\n", encoding="utf-8")
    ledger = ledger_path_for(data_dir, label)
    if os.path.exists(ledger): os.remove(ledger)
    subprocess.run([str(terminal), f"/config:{ini_path}"], check=False, timeout=timeout)
    for _ in range(60):
        if os.path.exists(ledger): break
        time.sleep(1)
    if not os.path.exists(ledger):
        raise RuntimeError(f"no ledger produced for {label} — check {report}")
    return ledger

if __name__ == "__main__":
    import sys
    sym = sys.argv[1] if len(sys.argv) > 1 else "XAUUSD"
    frm = sys.argv[2] if len(sys.argv) > 2 else "2024.01.01"
    to  = sys.argv[3] if len(sys.argv) > 3 else "2024.06.30"
    setf = sys.argv[4] if len(sys.argv) > 4 else "SweepHunter_smoke.set"
    print(run(sym, frm, to, setf, "smoke"))
```

- [ ] **Step 2: Write the smoke preset** `SweepHunter_smoke.set` (RR mode, defaults)

```ini
InpMagic=20260622
InpAsiaStartEt=2000
InpAsiaEndEt=0
InpLonStartEt=200
InpLonEndEt=500
InpMarkEt=900
InpHuntStartEt=900
InpHuntEndEt=1130
InpFlatEt=1600
InpLevelMode=0
InpEntryMode=0
InpFillDepth=0.0
InpTargetMode=0
InpTargetRR=2.0
InpStopBufferAtrK=0.15
InpAtrPeriod=14
InpScanLookback=900
InpRiskPct=1.0
InpMaxLot=50.0
InpSrvToUtcOffsetSec=999999
InpLedgerLabel=smoke
```

- [ ] **Step 3: Run the smoke backtest (XAUUSD, 6 months)**

```bash
python tools/run_sweephunter_backtest.py XAUUSD 2024.01.01 2024.06.30 SweepHunter_smoke.set
```
Expected: prints the ledger path; the file exists at `<DATADIR>\..\Common\Files\SweepHunter\ledger_smoke.csv`.

- [ ] **Step 4: Inspect the ledger — proof it traded**

```bash
head -5 "$APPDATA/MetaQuotes/Terminal/Common/Files/SweepHunter/ledger_smoke.csv"
wc -l "$APPDATA/MetaQuotes/Terminal/Common/Files/SweepHunter/ledger_smoke.csv"
```
Expected: header row matches the SH_Ledger header; ≥1 data row (a 6-month window should yield tens of trades). If 0 rows: debug session timing / sweep logic before continuing — check `sh_report_smoke.htm` for tester errors. **Do not report any metric yet** — this is a wiring smoke test only.

- [ ] **Step 5: Commit**

```bash
git add tools/run_sweephunter_backtest.py tested-strategies/SweepHunter/mt5/Presets/SweepHunter_smoke.set
git commit -m "tooling(sweephunter): single-run backtest driver + smoke preset; EA trades"
```

---

## Task 11: Candidate presets (RR / DOL × variants)

**Files:**
- Create: `tested-strategies/SweepHunter/mt5/Presets/SweepHunter_rr.set`
- Create: `tested-strategies/SweepHunter/mt5/Presets/SweepHunter_dol.set`
- Create: `tested-strategies/SweepHunter/mt5/Presets/SweepHunter_rr_combined.set`
- Create: `tested-strategies/SweepHunter/mt5/Presets/SweepHunter_dol_combined.set`

- [ ] **Step 1: Write the four candidate `.set` files**

`SweepHunter_rr.set` — copy of `SweepHunter_smoke.set` (RR, FOUR).
`SweepHunter_dol.set` — same but `InpTargetMode=1`.
`SweepHunter_rr_combined.set` — RR with `InpLevelMode=1`.
`SweepHunter_dol_combined.set` — `InpTargetMode=1` and `InpLevelMode=1`.

*(Each file is the full key=value block from Task 10 Step 2 with only the noted lines changed. Repeat the whole block per file; the walk-forward driver picks the best on IS Sharpe.)*

- [ ] **Step 2: Commit**

```bash
git add tested-strategies/SweepHunter/mt5/Presets/SweepHunter_rr.set \
        tested-strategies/SweepHunter/mt5/Presets/SweepHunter_dol.set \
        tested-strategies/SweepHunter/mt5/Presets/SweepHunter_rr_combined.set \
        tested-strategies/SweepHunter/mt5/Presets/SweepHunter_dol_combined.set
git commit -m "config(sweephunter): RR/DOL x FOUR/COMBINED candidate presets"
```

---

## Task 12: run_sweephunter_walkforward.py — WF + gate + report

**Files:**
- Create: `tools/run_sweephunter_walkforward.py`

- [ ] **Step 1: Write the walk-forward driver** (adapted from `run_orb_walkforward.py`; reuses `orb_gate.py`; writes a self-contained report dir — no dependency on the `audit` module)

```python
"""SweepHunter walk-forward: rolling IS/OOS, select best-IS-Sharpe candidate, blind OOS,
stitch OOS ledgers, apply orb_gate, write an audit report dir. Pass timestamp via --stamp
(scripts cannot call Date.now)."""
from __future__ import annotations
import argparse, csv, hashlib, os, sys
from datetime import date
from dateutil.relativedelta import relativedelta
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path: sys.path.insert(0, _HERE)
import orb_gate
from run_sweephunter_backtest import run

CANDIDATES = [  # (label, set_file)
    ("rr",          "SweepHunter_rr.set"),
    ("dol",         "SweepHunter_dol.set"),
    ("rr_combined", "SweepHunter_rr_combined.set"),
    ("dol_combined","SweepHunter_dol_combined.set"),
]

def _d(s): y,m,d = map(int, s.replace(".","-").split("-")); return date(y,m,d)
def _s(d): return f"{d.year:04d}.{d.month:02d}.{d.day:02d}"

def rolling_windows(start, end, is_months=12, oos_months=3):
    s, e = _d(start), _d(end); out=[]; is_from=s
    while True:
        oos_from = is_from + relativedelta(months=is_months)
        oos_to   = oos_from + relativedelta(months=oos_months)
        if oos_to > e: break
        out.append(dict(is_from=_s(is_from), is_to=_s(oos_from), oos_from=_s(oos_from), oos_to=_s(oos_to)))
        is_from = is_from + relativedelta(months=oos_months)
    return out

def select_on_is(symbol, win):
    best=None
    for label,setf in CANDIDATES:
        ledg = run(symbol, win["is_from"], win["is_to"], setf, f"is_{symbol}_{label}_{win['oos_from']}")
        rows = orb_gate.read_ledger(ledg)
        sh = orb_gate.sharpe([float(r["net_pnl"]) for r in rows])
        if best is None or sh>best[0]: best=(sh,setf,label)
    return best[1], best[2], best[0]

def walk(symbol, start, end, stamp, is_months=12, oos_months=3):
    repo = os.path.dirname(_HERE)
    rep = os.path.join(repo, "tested-strategies", "SweepHunter", "reports", f"SweepHunter-wf-{symbol}-{stamp}")
    os.makedirs(rep, exist_ok=True)
    wins = rolling_windows(start, end, is_months, oos_months)
    oos_rows=[]; is_sharpes=[]
    for win in wins:
        setf, label, is_sh = select_on_is(symbol, win)
        is_sharpes.append(is_sh)
        ledg = run(symbol, win["oos_from"], win["oos_to"], setf, f"oos_{symbol}_{label}_{win['oos_from']}")
        rows = orb_gate.read_ledger(ledg); oos_rows.extend(rows)
        # copy each OOS window ledger into the report dir
        with open(os.path.join(rep, f"ledger_oos_{label}_{win['oos_from']}.csv"),"w",newline="",encoding="utf-8") as f:
            if rows:
                w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    m = orb_gate.metrics_from_rows(oos_rows)
    oos_sh = orb_gate.sharpe([float(r["net_pnl"]) for r in oos_rows])
    is_sh_avg = sum(is_sharpes)/len(is_sharpes) if is_sharpes else 0.0
    verdict = orb_gate.apply_gate(m, oos_sharpe=oos_sh, is_sharpe=is_sh_avg)
    if oos_rows:
        with open(os.path.join(rep,"oos_stitched.csv"),"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(oos_rows[0].keys())); w.writeheader(); w.writerows(oos_rows)
    summary = [f"SweepHunter walk-forward {symbol} ({start}..{end})",
               f"OOS trades={m['trades']} net={m['net']:.0f} PF={m['pf']:.2f} maxDD={m['max_dd']:.1%} "
               f"OOS_Sharpe={oos_sh:.2f} IS_Sharpe(avg)={is_sh_avg:.2f} PASS={verdict['passed']}"]
    summary += [f"- {r}" for r in verdict["reasons"]]
    with open(os.path.join(rep,"gate.txt"),"w",encoding="utf-8") as f: f.write("\n".join(summary)+"\n")
    # manifest
    man=[]
    for fn in sorted(os.listdir(rep)):
        p=os.path.join(rep,fn)
        if os.path.isfile(p):
            man.append(f"{hashlib.sha256(open(p,'rb').read()).hexdigest()}  {fn}")
    with open(os.path.join(rep,"manifest.sha256"),"w",encoding="utf-8") as f: f.write("\n".join(man)+"\n")
    print("\n".join(summary)); print("report:", rep)
    return verdict, rep

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol"); ap.add_argument("start"); ap.add_argument("end")
    ap.add_argument("--stamp", required=True, help="UTC stamp, e.g. 20260622-1700Z")
    ap.add_argument("--is-months", type=int, default=12); ap.add_argument("--oos-months", type=int, default=3)
    a = ap.parse_args()
    v,_ = walk(a.symbol, a.start, a.end, a.stamp, a.is_months, a.oos_months)
    sys.exit(0 if v["passed"] else 2)
```

- [ ] **Step 2: Smoke the WF driver on one symbol, short span (proves wiring, not edge)**

```bash
python tools/run_sweephunter_walkforward.py XAUUSD 2022.01.01 2023.09.30 --stamp smoke
```
Expected: prints a gate summary line and `report:` path; the report dir contains `gate.txt`, `oos_stitched.csv`, per-window OOS ledgers, `manifest.sha256`. (Pass/fail is irrelevant here — only that it runs and writes the audit dir.)

- [ ] **Step 3: Commit**

```bash
git add tools/run_sweephunter_walkforward.py
git commit -m "tooling(sweephunter): walk-forward driver + gate + audit report"
```

---

## Task 13: Full validation — cross-instrument walk-forward + VERDICT

**Files:**
- Create: `tested-strategies/SweepHunter/VERDICT.md`
- Modify: `docs/strategy-validation.md` (append a Findings-log row)
- Create: `tested-strategies/SweepHunter/reports/SweepHunter-xinstr-<stamp>/summary.md`

- [ ] **Step 1: Determine max available history per symbol** (don't assume — check the tester)

For each of XAUUSD, EURUSD, GBPUSD, USDJPY, USDCHF, US30, US100, US500, BTCUSD: run a 1-month probe backtest at the earliest plausible date and at recent dates to bracket the FTMO M1 history. Record the usable `[start,end]` per symbol. (A symbol with < ~3 years usable is noted as limited.)

- [ ] **Step 2: Run the walk-forward per instrument** (use the real UTC stamp — get it from the shell, scripts can't)

```bash
STAMP=$(date -u +%Y%m%d-%H%M%SZ)
for SYM in XAUUSD EURUSD GBPUSD USDJPY USDCHF US30 US100 US500 BTCUSD; do
  python tools/run_sweephunter_walkforward.py $SYM <start> <end> --stamp $STAMP
done
```
Expected: one report dir per symbol under `tested-strategies/SweepHunter/reports/`. Each has a `gate.txt`.

- [ ] **Step 3: Build the cross-instrument table from the gate.txt files** (read every file; no remembered numbers)

```bash
for f in tested-strategies/SweepHunter/reports/SweepHunter-wf-*-$STAMP/gate.txt; do echo "== $f =="; cat "$f"; done
```
Assemble a markdown table: Instrument | candidate-won | n | PF | OOS Sharpe | maxDD | gate PASS/FAIL. Save to `reports/SweepHunter-xinstr-<stamp>/summary.md`.

- [ ] **Step 4: Buy-and-hold sanity per symbol** — for any symbol that PASSES, compare stitched-OOS net to a buy-and-hold of the same span (the Tesla-trap check). Note it in the summary.

- [ ] **Step 5: Write `VERDICT.md`** (model on `tested-strategies/ORB/VERDICT.md`)

```markdown
# SweepHunter — Verdict

**Strategy:** Asia/London session-liquidity sweep → NY M1 FVG reversal (mark 09:00 ET,
hunt 09:00–11:30 ET, stop at sweep swing, RR vs draw-on-liquidity targets). MQL5 EA on the FTMO feed.
**Outcome:** <🟢 ACCEPTED / 🔴 REJECTED> — <one-line reason from the cross-instrument gate>.

## The numbers (walk-forward OOS, cross-instrument, stamp <STAMP>)
Source: `reports/SweepHunter-xinstr-<stamp>/summary.md` + per-symbol `reports/SweepHunter-wf-*-<stamp>/gate.txt`.

<cross-instrument table here — only numbers read from gate.txt this session>

## Why <accepted/rejected>
1. <generalization across instruments — pass on >1 uncorrelated symbol, or fail>
2. <buy-and-hold sanity>
3. <gate filters that fired>

## Note
Build + harness sound (unit-tested pure modules, headless tester, OnTradeTransaction ledger,
codified gate). Spec/plan in `docs/superpowers/`.
```

- [ ] **Step 6: Append the Findings-log row to `docs/strategy-validation.md`**

Add one row to the table: `| <date> | **SweepHunter** (Asia/London sweep + M1 FVG, FTMO) | <finding> | <rule it illustrates> |`.

- [ ] **Step 7: Commit**

```bash
git add tested-strategies/SweepHunter/VERDICT.md \
        tested-strategies/SweepHunter/reports \
        docs/strategy-validation.md
git commit -m "result(sweephunter): walk-forward cross-instrument verdict + findings"
```

---

## Self-review notes (for the executor)

- **Spec coverage:** Tasks 1–7 cover every pure module in spec §4; Task 9 the state machine (§3); Tasks 10–12 the backtest/WF harness (§6.2); Task 13 the gate + cross-instrument + VERDICT (§6.2–6.3). Entry modes (LIMIT/MARKET), level modes (FOUR/COMBINED), and target modes (RR/DOL) are all wired in the EA and exposed as candidate presets.
- **Order of greens:** the per-task "verify it fails" steps assume `run_sweephunter_selftest.py` exists (Task 8). If executing strictly in order, Tasks 1–6 confirm RED via a MetaEditor compile of the test (missing include); after Task 8, re-run the whole suite green before Task 9.
- **Type consistency:** `SHLevels`, `SH_ComputeLevels`, `SH_IsFVG/SH_FvgEntry`, `SH_Swept/SH_DirFromSweepSide/SH_UpdateSwing`, `SH_R/SH_TargetRR/SH_TargetDOL`, `SH_Stop`, `SH_LotsFromRisk`, `SH_Ledger*` signatures are identical between their defining task, the EA (Task 9), and the harness (`net_pnl` column ↔ `orb_gate`).
- **No metric before its file:** Tasks 10/13 explicitly forbid quoting numbers until a result/gate file is inspected that session (repo audit-trail rule).
```
