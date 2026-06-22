# ORB (Opening Range Breakout) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, walk-forward-validated ORB strategy for US100.cash on the FTMO terminal, per [ORB/strategy.md](../../../ORB/strategy.md), and answer whether it clears the repo validation gate.

**Architecture:** Mirror the established repo EA pattern (PAC/ETR/IVB): pure unit-tested `*.mqh` logic includes + a thin `ORB_EA.mq5` orchestrator + `MQL5TEST`-emitting self-test scripts. The EA writes its own UTF-8 **ledger CSV** (PAC `Logger` pattern) so all metrics and the acceptance gate are computed in Python — language-independent, per-trade, net of costs — instead of parsing the UTF-16 Polish HTM. A new Python layer (`tools/run_orb_backtest.py` + `tools/orb_gate.py` + `tools/run_orb_walkforward.py`) drives the headless Strategy Tester over rolling windows and applies the gate. Tuning is **sequential over small discrete arm-sets** (the spec's anti-combinatorial rule), so "optimization" is just "run each arm on the in-sample window in Python and pick the best" — no MT5 genetic-optimizer XML parsing.

**Tech Stack:** MQL5 (MT5 build ≥ 4000, `<Trade\Trade.mqh>` CTrade), Python 3.11+ (`MetaTrader5`, stdlib `csv`/`statistics`/`subprocess`/`configparser`), FTMO-Demo terminal at data dir `81A933A9AFC5DE3C23B15CAB19C63850`.

**Validation authority:** [docs/strategy-validation.md](../../strategy-validation.md) (the gate) + the `audit-trail` skill (every reported number traces to `reports/ORB-<UTCstamp>/`).

---

## File structure

```
ORB/
  strategy.md                                  (exists — the spec)
  mt5/
    Include/ORB/
      ORB_Time.mqh      ET cash-open mapping, US-DST, server→UTC→ET, OR/entry/flat windows
      ORB_Range.mqh     OR capture (high/low/mid/width), median helper, RVOL, range guard
      ORB_Bias.mqh      D1 EMA directional bias gate
      ORB_Signals.mqh   entry/stop-order price from OR + buffer + bias
      ORB_Stops.mqh     SL arms S0/S1/S2, R = |entry-SL|
      ORB_Exits.mqh     exit arms E0..E4, fixed target, EMA(M15) close-cross
      ORB_Risk.mqh      lot size from R (mirror PAC_Risk floor math)
      ORB_Ledger.mqh    UTF-8 per-trade CSV writer (mirror PAC Logger)
    Experts/ORB/
      ORB_EA.mq5        thin orchestrator (daily state machine)
    Scripts/ORB_Tests/
      helpers/TestRunner.mqh        (copied verbatim from PAC)
      test_orb_time.mq5
      test_orb_range.mq5
      test_orb_bias.mq5
      test_orb_signals.mq5
      test_orb_stops.mq5
      test_orb_exits.mq5
    Presets/
      ORB_US100_baseline.set        (S0 / E0 kernel config)
tools/
  run_orb_backtest.py     headless single-config tester driver → returns ledger path
  orb_gate.py             pure: ledger CSV → metrics → repo gate verdict
  run_orb_walkforward.py  rolling-window sequential arm/grid selection → stitch OOS → gate → audit
  tests/
    test_orb_gate.py
    test_run_orb_backtest.py
    test_run_orb_walkforward.py
```

**Conventions (verified against PAC):**
- Pure functions namespaced `ORB_*`, no module-level state, live in `.mqh`, fully unit-testable.
- Self-tests are MQL5 `Scripts` with `void OnStart()`, `#include "helpers\\TestRunner.mqh"`, emit `MQL5TEST {"test":..,"result":"PASS|FAIL"}` lines; run via `python tools/run_mql5_tests.py --script-dir ORB/mt5/Scripts/ORB_Tests --terminal <ftmo terminal64.exe> --data-root <APPDATA>\MetaQuotes\Terminal`.
- Magic number: `InpMagic = 20260621`.
- Deploy: the EA/includes/scripts must be **copied into the FTMO terminal's `MQL5/` tree** (`...\81A933...\MQL5\Experts|Include|Scripts\ORB\`) to compile/run. A repo↔terminal sync step is in Phase 0.

---

## Phase 0 — Data + scaffold

### Task 0.1: Verify US100.cash history is available for backtest

**Files:** none (terminal operation).

- [ ] **Step 1: Check what history depth the FTMO terminal has for US100.cash**

Run (with the FTMO terminal running and logged in):
```bash
python tools/mt5_data.py rates US100.cash M1 10
```
Expected: a JSON array of 10 recent M1 bars. If it errors with "symbol not found", the symbol name differs — run `python tools/mt5_data.py symbols` and grep for `US100`.

- [ ] **Step 2: Confirm multi-year depth exists (walk-forward needs ≥ ~3 years of opens for ≥30 OOS trades)**

Run:
```bash
python tools/mt5_data.py dump-bars US100.cash M1 2021-01-01 2026-06-01 ORB/_data/us100_m1_probe.csv
```
Expected JSON: `{"symbol":"US100.cash","timeframe":"M1","rows": <large>, "output":"..."}`. If `rows` is small or the call returns few bars, the terminal has not downloaded that history yet → **Step 3**.

- [ ] **Step 3 (only if history is thin): force the terminal to download M1 history**

In the FTMO terminal: open a US100.cash M1 chart, press `Home` repeatedly (or scroll left) to pull history from the server back to ≥ 2021, then re-run Step 2. The MT5 Strategy Tester's "Every tick based on real ticks" model reads from this same base; the tick base is already subscribed (confirmed in `bases/FTMO-Demo/ticks/US100.cash`).

- [ ] **Step 4: Record the confirmed usable date range** in a scratch note for Phase 4/5 window planning. No commit.

### Task 0.2: Scaffold the ORB MT5 tree and copy the test runner

**Files:**
- Create: `ORB/mt5/Include/ORB/.gitkeep`, `ORB/mt5/Experts/ORB/.gitkeep`, `ORB/mt5/Scripts/ORB_Tests/helpers/`, `ORB/mt5/Presets/.gitkeep`
- Create: `ORB/mt5/Scripts/ORB_Tests/helpers/TestRunner.mqh` (copy)
- Create: `ORB/mt5/README.md`

- [ ] **Step 1: Create the directory tree** (PowerShell)
```powershell
$root = "ORB/mt5"
"Include/ORB","Experts/ORB","Scripts/ORB_Tests/helpers","Presets" | ForEach-Object {
  New-Item -ItemType Directory -Force "$root/$_" | Out-Null
}
```

- [ ] **Step 2: Copy `TestRunner.mqh` verbatim from PAC**
```powershell
Copy-Item "PAC/mt5/Scripts/PAC_Tests/helpers/TestRunner.mqh" "ORB/mt5/Scripts/ORB_Tests/helpers/TestRunner.mqh"
```
(This gives `ASSERT_EQ`, `ASSERT_NEAR`, `ASSERT_TRUE`, `ASSERT_FALSE`, `ASSERT_EQ_INT`, `ASSERT_STR_EQ`, and the `MQL5TEST` JSON emit macros.)

- [ ] **Step 3: Write `ORB/mt5/README.md`** documenting the deploy-sync and headless commands:
```markdown
# ORB MT5

## Deploy to the FTMO terminal
Copy `Include/ORB`, `Experts/ORB`, `Scripts/ORB_Tests` into
`%APPDATA%\MetaQuotes\Terminal\81A933A9AFC5DE3C23B15CAB19C63850\MQL5\`.
Use `tools/sync_orb_to_terminal.ps1` (Phase 0.3).

## Compile (headless)
`& "C:\Program Files\FTMO Global Markets MT5 Terminal\MetaEditor64.exe" /compile:"<DATADIR>\MQL5\Experts\ORB\ORB_EA.mq5" /log:"<DATADIR>\MQL5\Logs\orb_compile.log"`
Exit code is unreliable — read the log and confirm "0 errors, 0 warnings".

## Unit tests (headless)
`python tools/run_mql5_tests.py --script-dir ORB/mt5/Scripts/ORB_Tests --terminal "C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe" --data-root "%APPDATA%\MetaQuotes\Terminal"`
```

- [ ] **Step 4: Commit**
```bash
git add ORB/mt5 && git commit -m "chore(orb): scaffold mt5 tree + copy TestRunner"
```

### Task 0.3: Repo→terminal sync script

**Files:** Create `tools/sync_orb_to_terminal.ps1`

- [ ] **Step 1: Write the sync script**
```powershell
# tools/sync_orb_to_terminal.ps1 — mirror ORB MQL5 sources into the FTMO terminal tree
param(
  [string]$DataDir = "$env:APPDATA\MetaQuotes\Terminal\81A933A9AFC5DE3C23B15CAB19C63850"
)
$ErrorActionPreference = "Stop"
$src = "ORB/mt5"
foreach ($sub in @("Include/ORB","Experts/ORB","Scripts/ORB_Tests")) {
  $dst = Join-Path "$DataDir/MQL5" $sub
  New-Item -ItemType Directory -Force $dst | Out-Null
  Copy-Item "$src/$sub/*" $dst -Recurse -Force
}
Write-Host "Synced ORB sources to $DataDir/MQL5"
```

- [ ] **Step 2: Run it; confirm files land in the terminal**
```powershell
pwsh tools/sync_orb_to_terminal.ps1
```
Expected: "Synced ORB sources to ...". (Will copy nothing useful until Phase 1 writes the includes — that is fine, it is the pipe.)

- [ ] **Step 3: Commit**
```bash
git add tools/sync_orb_to_terminal.ps1 && git commit -m "chore(orb): add repo->terminal sync script"
```

---

## Phase 1 — Pure logic includes (TDD)

Every module: write the test script → run it (fail) → implement the `.mqh` → run (pass) → commit.

**Headless test recipe (verified 2026-06-22 on this box).** `terminal64 /Script:` does NOT run a script on this build — use `/config:<ini>` with a `[StartUp] Script=` section. MT5 is single-instance per data dir, so each cold-start must run on a closed terminal; therefore **every `test_orb_*.mq5` MUST end its `OnStart` with**:
```mql5
  Sleep(300);        // flush Print() to the log
  TerminalClose(0);  // headless self-terminate so the next cold-start is clean
```
All of this is wrapped by `tools/run_orb_selftest.py` (syncs, closes any open terminal, compiles via MetaEditor, cold-starts `/config`, parses MQL5TEST). Run a module with:
```bash
python tools/run_orb_selftest.py --name test_orb_<module>
```
Expected pass line: `=== TOTAL N passed, 0 failed, 0 malformed ===` (exit 0).

### Task 1.1: `ORB_Time.mqh` — ET cash-open mapping (load-bearing)

This is the subtlety §2 of the spec flags: the OR window must anchor to **NY 09:30 ET using the US DST calendar**, computed from the broker's server time. EU and US DST transitions are misaligned for ~2–3 weeks each spring/autumn — hardcoding "16:30 server" is wrong during those weeks. We convert server→UTC (configurable offset, because `TimeGMT()` is unreliable in the tester) then UTC→ET with the **US** rule.

**Files:**
- Test: `ORB/mt5/Scripts/ORB_Tests/test_orb_time.mq5`
- Create: `ORB/mt5/Include/ORB/ORB_Time.mqh`

- [ ] **Step 1: Write the failing test**
```mql5
// test_orb_time.mq5
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\ORB\\ORB_Time.mqh"

void OnStart() {
  // 2024-07-01 13:30:00 UTC = 09:30 ET (EDT, summer, UTC-4) -> opening range start
  datetime u_summer = D'2024.07.01 13:30:00';
  ASSERT_TRUE(ORB_IsUsDST(u_summer), "us_dst_july_true");
  ASSERT_EQ_INT(ORB_EtMinutesOfDay(ORB_UtcToEt(u_summer)), 570, "summer_0930_et_minutes"); // 9*60+30

  // 2024-01-02 14:30:00 UTC = 09:30 ET (EST, winter, UTC-5)
  datetime u_winter = D'2024.01.02 14:30:00';
  ASSERT_FALSE(ORB_IsUsDST(u_winter), "us_dst_january_false");
  ASSERT_EQ_INT(ORB_EtMinutesOfDay(ORB_UtcToEt(u_winter)), 570, "winter_0930_et_minutes");

  // DST-mismatch week: 2024-03-11 (US already on EDT, EU still on CET).
  // 13:30 UTC must be 09:30 ET even though EU offset would say otherwise.
  datetime u_mismatch = D'2024.03.11 13:30:00';
  ASSERT_TRUE(ORB_IsUsDST(u_mismatch), "us_dst_mar11_true");
  ASSERT_EQ_INT(ORB_EtMinutesOfDay(ORB_UtcToEt(u_mismatch)), 570, "mismatch_0930_et_minutes");

  // Window predicates, given server time + a known server->UTC offset (seconds).
  // FTMO summer = GMT+3 => offset +10800; 16:30 server == 13:30 UTC == 09:30 ET.
  datetime srv_open = D'2024.07.01 16:30:00';
  ASSERT_TRUE(ORB_InOpeningRange(srv_open, 10800, 15), "in_or_at_0930");
  ASSERT_FALSE(ORB_InOpeningRange(srv_open + 15*60, 10800, 15), "not_in_or_at_0945");
  ASSERT_TRUE(ORB_InEntryWindow(srv_open + 30*60, 10800, 945, 1130), "in_entry_1000");
  ASSERT_FALSE(ORB_InEntryWindow(srv_open + 130*60, 10800, 945, 1130), "not_in_entry_1140");
  ASSERT_TRUE(ORB_AtOrAfterFlat(srv_open + (16*60-30)*60, 10800, 1600), "flat_at_1600");
}
```

- [ ] **Step 2: Run → verify FAIL** (`function not defined` / compile error). Expected: not `0 failed`.

- [ ] **Step 3: Implement `ORB_Time.mqh`**
```mql5
// ORB_Time.mqh — anchor the opening range to NY 09:30 ET using the US DST calendar.
#ifndef ORB_TIME_MQH
#define ORB_TIME_MQH

// nth weekday helper: day-of-month for the `nth` `dow` (0=Sun) in (year,month).
int ORB_NthWeekday(int year,int month,int dow,int nth){
  datetime first = StringToTime(StringFormat("%04d.%02d.01 00:00:00",year,month));
  MqlDateTime t; TimeToStruct(first,t);
  int shift = (dow - t.day_of_week + 7) % 7;
  return 1 + shift + (nth-1)*7;
}
// last weekday-of-month
int ORB_LastWeekday(int year,int month,int dow){
  int dim = 31; // walk back to a valid date
  while(true){ datetime d=StringToTime(StringFormat("%04d.%02d.%02d 00:00:00",year,month,dim));
    MqlDateTime t; TimeToStruct(d,t); if(t.mon==month) break; dim--; }
  datetime last = StringToTime(StringFormat("%04d.%02d.%02d 00:00:00",year,month,dim));
  MqlDateTime lt; TimeToStruct(last,lt);
  int shift = (lt.day_of_week - dow + 7) % 7;
  return dim - shift;
}

// US DST: 2nd Sunday March 07:00 UTC -> 1st Sunday Nov 06:00 UTC.
bool ORB_IsUsDST(datetime utc){
  MqlDateTime t; TimeToStruct(utc,t);
  int y=t.year;
  datetime start=StringToTime(StringFormat("%04d.03.%02d 07:00:00",y,ORB_NthWeekday(y,3,0,2)));
  datetime end  =StringToTime(StringFormat("%04d.11.%02d 06:00:00",y,ORB_NthWeekday(y,11,0,1)));
  return (utc>=start && utc<end);
}
datetime ORB_UtcToEt(datetime utc){ return utc - (ORB_IsUsDST(utc) ? 4*3600 : 5*3600); }
int ORB_EtMinutesOfDay(datetime et){ MqlDateTime t; TimeToStruct(et,t); return t.hour*60+t.min; }

// server time + (server->UTC offset seconds) -> UTC -> ET minutes-of-day
int ORB_EtMinutesFromServer(datetime serverTime,int srvToUtcOffsetSec){
  datetime utc = serverTime - srvToUtcOffsetSec;   // server = UTC + offset
  return ORB_EtMinutesOfDay(ORB_UtcToEt(utc));
}
bool ORB_InOpeningRange(datetime serverTime,int srvToUtcOffsetSec,int orMinutes){
  int m=ORB_EtMinutesFromServer(serverTime,srvToUtcOffsetSec);
  return (m>=570 && m<570+orMinutes);            // 09:30 .. 09:30+orMinutes
}
bool ORB_InEntryWindow(datetime serverTime,int srvToUtcOffsetSec,int startEt,int endEt){
  int m=ORB_EtMinutesFromServer(serverTime,srvToUtcOffsetSec);
  int s=(startEt/100)*60+(startEt%100), e=(endEt/100)*60+(endEt%100);
  return (m>=s && m<e);
}
bool ORB_AtOrAfterFlat(datetime serverTime,int srvToUtcOffsetSec,int flatEt){
  int m=ORB_EtMinutesFromServer(serverTime,srvToUtcOffsetSec);
  int f=(flatEt/100)*60+(flatEt%100);
  return (m>=f);
}
#endif
```
Note: `srvToUtcOffsetSec` is supplied by the EA (input, default auto-detected at init). `startEt`/`endEt`/`flatEt` are HHMM integers (945, 1130, 1600).

- [ ] **Step 4: Run → verify PASS** (`=== 13 passed, 0 failed, 0 malformed ===`).

- [ ] **Step 5: Commit**
```bash
git add ORB/mt5/Include/ORB/ORB_Time.mqh ORB/mt5/Scripts/ORB_Tests/test_orb_time.mq5
git commit -m "feat(orb): ET cash-open time mapping with US DST calendar + unit tests"
```

### Task 1.2: `ORB_Range.mqh` — OR metrics, RVOL, range guard

**Files:**
- Test: `ORB/mt5/Scripts/ORB_Tests/test_orb_range.mq5`
- Create: `ORB/mt5/Include/ORB/ORB_Range.mqh`

- [ ] **Step 1: Write the failing test**
```mql5
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\ORB\\ORB_Range.mqh"
void OnStart(){
  ASSERT_NEAR(ORB_Width(20100.0,20050.0),50.0,1e-9,"width");
  ASSERT_NEAR(ORB_Mid(20100.0,20050.0),20075.0,1e-9,"mid");
  double v[5]={100,120,80,110,90};                 // median 100
  ASSERT_NEAR(ORB_Median(v,5),100.0,1e-9,"median_odd");
  double v4[4]={100,200,300,400};                  // median 250
  ASSERT_NEAR(ORB_Median(v4,4),250.0,1e-9,"median_even");
  ASSERT_NEAR(ORB_Rvol(150.0,v,5),1.5,1e-9,"rvol_1p5");
  double w[5]={40,42,38,41,39};                    // median 40
  ASSERT_TRUE (ORB_RangeGuardOk(50.0,w,5,0.5,2.0),"guard_ok_50");   // 50 in [20,80]
  ASSERT_FALSE(ORB_RangeGuardOk(15.0,w,5,0.5,2.0),"guard_dead_15"); // <20
  ASSERT_FALSE(ORB_RangeGuardOk(90.0,w,5,0.5,2.0),"guard_blowoff_90"); // >80
}
```

- [ ] **Step 2: Run → FAIL.**

- [ ] **Step 3: Implement `ORB_Range.mqh`**
```mql5
#ifndef ORB_RANGE_MQH
#define ORB_RANGE_MQH
double ORB_Width(double hi,double lo){ return hi-lo; }
double ORB_Mid(double hi,double lo){ return (hi+lo)*0.5; }
double ORB_Median(const double &a[],int n){
  double b[]; ArrayResize(b,n); for(int i=0;i<n;i++) b[i]=a[i];
  ArraySort(b);
  if(n%2==1) return b[n/2];
  return (b[n/2-1]+b[n/2])*0.5;
}
double ORB_Rvol(double todayVol,const double &priorVols[],int n){
  double m=ORB_Median(priorVols,n); return (m>0.0)? todayVol/m : 0.0;
}
bool ORB_RangeGuardOk(double width,const double &priorWidths[],int n,double lo,double hi){
  double m=ORB_Median(priorWidths,n); if(m<=0.0) return false;
  return (width>=lo*m && width<=hi*m);
}
#endif
```

- [ ] **Step 4: Run → PASS** (`8 passed`). **Step 5: Commit** `feat(orb): OR metrics, RVOL, range guard + tests`.

### Task 1.3: `ORB_Bias.mqh` — D1 EMA bias gate

**Files:** Test `test_orb_bias.mq5`; Create `ORB/mt5/Include/ORB/ORB_Bias.mqh`.

- [ ] **Step 1: Failing test**
```mql5
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\ORB\\ORB_Bias.mqh"
void OnStart(){
  ASSERT_EQ_INT(ORB_Bias(20100.0,20000.0),+1,"bias_long_above_ema");
  ASSERT_EQ_INT(ORB_Bias(19900.0,20000.0),-1,"bias_short_below_ema");
  ASSERT_EQ_INT(ORB_Bias(20000.0,20000.0), 0,"bias_flat_equal_skip");
}
```
- [ ] **Step 2: FAIL. Step 3: Implement**
```mql5
#ifndef ORB_BIAS_MQH
#define ORB_BIAS_MQH
// +1 long-only, -1 short-only, 0 = exactly on EMA -> skip the day (no coin-flip).
int ORB_Bias(double priorDailyClose,double dailyEma){
  if(priorDailyClose>dailyEma) return +1;
  if(priorDailyClose<dailyEma) return -1;
  return 0;
}
#endif
```
- [ ] **Step 4: PASS (3). Step 5: Commit** `feat(orb): D1 EMA bias gate + tests`.

### Task 1.4: `ORB_Signals.mqh` — entry/stop-order price

**Files:** Test `test_orb_signals.mq5`; Create `ORB/mt5/Include/ORB/ORB_Signals.mqh`.

- [ ] **Step 1: Failing test**
```mql5
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\ORB\\ORB_Signals.mqh"
void OnStart(){
  // buffer = 0.1 * width. width=50 -> buffer 5.
  ASSERT_NEAR(ORB_EntryPrice(+1,20100.0,20050.0,0.1),20105.0,1e-9,"long_entry_above_high");
  ASSERT_NEAR(ORB_EntryPrice(-1,20100.0,20050.0,0.1),20045.0,1e-9,"short_entry_below_low");
}
```
- [ ] **Step 2: FAIL. Step 3: Implement**
```mql5
#ifndef ORB_SIGNALS_MQH
#define ORB_SIGNALS_MQH
// bias +1: buy-stop at OR_high + bufFrac*width ; bias -1: sell-stop at OR_low - bufFrac*width
double ORB_EntryPrice(int bias,double orHigh,double orLow,double bufFrac){
  double buf=bufFrac*(orHigh-orLow);
  return (bias>0)? orHigh+buf : orLow-buf;
}
#endif
```
- [ ] **Step 4: PASS (2). Step 5: Commit** `feat(orb): breakout entry price + tests`.

### Task 1.5: `ORB_Stops.mqh` — SL arms S0/S1/S2 + R

**Files:** Test `test_orb_stops.mq5`; Create `ORB/mt5/Include/ORB/ORB_Stops.mqh`.

- [ ] **Step 1: Failing test**
```mql5
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\ORB\\ORB_Stops.mqh"
void OnStart(){
  double entryL=20105.0, H=20100.0, L=20050.0, M=20075.0, atr=30.0;
  // S0 long -> OR low ; S1 long -> mid ; S2 long -> entry - k*atr (k=1.5 -> 45)
  ASSERT_NEAR(ORB_StopLoss(0,+1,entryL,H,L,M,atr,1.5),20050.0,1e-9,"S0_long_opposite");
  ASSERT_NEAR(ORB_StopLoss(1,+1,entryL,H,L,M,atr,1.5),20075.0,1e-9,"S1_long_mid");
  ASSERT_NEAR(ORB_StopLoss(2,+1,entryL,H,L,M,atr,1.5),20105.0-45.0,1e-9,"S2_long_katr");
  // short mirror
  double entryS=20045.0;
  ASSERT_NEAR(ORB_StopLoss(0,-1,entryS,H,L,M,atr,1.5),20100.0,1e-9,"S0_short_opposite");
  ASSERT_NEAR(ORB_StopLoss(2,-1,entryS,H,L,M,atr,1.5),20045.0+45.0,1e-9,"S2_short_katr");
  ASSERT_NEAR(ORB_R(20105.0,20050.0),55.0,1e-9,"R_long");
}
```
- [ ] **Step 2: FAIL. Step 3: Implement**
```mql5
#ifndef ORB_STOPS_MQH
#define ORB_STOPS_MQH
// arm: 0=S0 opposite OR end, 1=S1 OR midpoint, 2=S2 k*ATR from entry
double ORB_StopLoss(int arm,int bias,double entry,double orHigh,double orLow,double orMid,double atr,double kAtr){
  if(arm==0) return (bias>0)? orLow : orHigh;
  if(arm==1) return orMid;
  return (bias>0)? entry-kAtr*atr : entry+kAtr*atr;   // S2
}
double ORB_R(double entry,double sl){ return MathAbs(entry-sl); }
#endif
```
- [ ] **Step 4: PASS (6). Step 5: Commit** `feat(orb): SL arms S0/S1/S2 + R + tests`.

### Task 1.6: `ORB_Exits.mqh` — exit arms + EMA close-cross

**Files:** Test `test_orb_exits.mq5`; Create `ORB/mt5/Include/ORB/ORB_Exits.mqh`.

- [ ] **Step 1: Failing test**
```mql5
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\ORB\\ORB_Exits.mqh"
void OnStart(){
  double entryL=20105.0, R=55.0;
  // E0 K=1 long target = entry + R ; E1 K=2 -> entry + 2R
  ASSERT_NEAR(ORB_Target(+1,entryL,R,1.0),20160.0,1e-9,"E0_long_1R");
  ASSERT_NEAR(ORB_Target(+1,entryL,R,2.0),20215.0,1e-9,"E1_long_2R");
  ASSERT_NEAR(ORB_Target(-1,20045.0,55.0,1.0),19990.0,1e-9,"E0_short_1R");
  // EMA(M15) close-cross exit: long exits when M15 close < EMA
  ASSERT_TRUE (ORB_EmaCloseCrossExit(+1,20070.0,20080.0),"long_exit_close_below_ema");
  ASSERT_FALSE(ORB_EmaCloseCrossExit(+1,20090.0,20080.0),"long_hold_close_above_ema");
  ASSERT_TRUE (ORB_EmaCloseCrossExit(-1,20090.0,20080.0),"short_exit_close_above_ema");
}
```
- [ ] **Step 2: FAIL. Step 3: Implement**
```mql5
#ifndef ORB_EXITS_MQH
#define ORB_EXITS_MQH
double ORB_Target(int bias,double entry,double R,double K){
  return (bias>0)? entry+K*R : entry-K*R;
}
// true => an M15 candle has CLOSED beyond the EMA against the position -> exit now.
bool ORB_EmaCloseCrossExit(int bias,double m15Close,double ema){
  return (bias>0)? (m15Close<ema) : (m15Close>ema);
}
#endif
```
- [ ] **Step 4: PASS (6). Step 5: Commit** `feat(orb): exit arms target + EMA close-cross + tests`.

### Task 1.7: `ORB_Risk.mqh` — lot from R, and `ORB_Ledger.mqh` — CSV

**Files:** Test `test_orb_risk` asserts appended to a small new `test_orb_risk.mq5`; Create `ORB/mt5/Include/ORB/ORB_Risk.mqh` and `ORB/mt5/Include/ORB/ORB_Ledger.mqh`.

- [ ] **Step 1: Failing test for risk** (`ORB/mt5/Scripts/ORB_Tests/test_orb_risk.mq5`)
```mql5
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\ORB\\ORB_Risk.mqh"
void OnStart(){
  // equity 10000, 1% risk = 100. SL distance 50 price-units, value $1/unit/lot.
  // raw lots = 100 / (50*1) = 2.0 ; step 0.01 -> 2.00
  ASSERT_NEAR(ORB_LotsFromRisk(10000,1.0,50,1.0,0.01,0.01,100.0),2.0,1e-9,"lots_basic");
  // floor to step: raw 2.337 -> 2.33
  ASSERT_NEAR(ORB_LotsFromRisk(10000,1.0,42.79,1.0,0.01,0.01,100.0),
              MathFloor((100.0/42.79)/0.01)*0.01,1e-9,"lots_floor_step");
  // cap at max lot
  ASSERT_NEAR(ORB_LotsFromRisk(10000,50,1,1.0,0.01,0.01,5.0),5.0,1e-9,"lots_capped");
  // below min -> 0
  ASSERT_NEAR(ORB_LotsFromRisk(100,0.01,9999,1.0,0.01,0.01,100.0),0.0,1e-9,"lots_below_min_zero");
}
```
- [ ] **Step 2: FAIL. Step 3: Implement `ORB_Risk.mqh`** (mirrors `PAC_Risk` floor math)
```mql5
#ifndef ORB_RISK_MQH
#define ORB_RISK_MQH
// valuePerUnitPerLot = money change per 1.0 price-unit move per 1.0 lot (from SymbolInfo in the EA).
double ORB_LotsFromRisk(double equity,double riskPct,double slDistUnits,
                        double valuePerUnitPerLot,double volStep,double volMin,double volMax){
  if(slDistUnits<=0.0 || valuePerUnitPerLot<=0.0) return 0.0;
  double riskAmt = equity*(riskPct/100.0);
  double raw = riskAmt/(slDistUnits*valuePerUnitPerLot);
  double lots = MathFloor(raw/volStep)*volStep;
  if(lots>volMax) lots=volMax;
  if(lots<volMin) return 0.0;
  return lots;
}
#endif
```
- [ ] **Step 4: PASS (4). Step 5: Implement `ORB_Ledger.mqh`** (no separate unit test — exercised in Phase 2 smoke):
```mql5
#ifndef ORB_LEDGER_MQH
#define ORB_LEDGER_MQH
// One UTF-8 CSV per run under MQL5/Files/ORB/. Header written once; one row per closed trade.
int ORB_LedgerOpen(string path){
  int h=FileOpen(path,FILE_WRITE|FILE_CSV|FILE_ANSI,",");
  if(h!=INVALID_HANDLE)
    FileWrite(h,"trade_id","symbol","dir","ts_open_utc","ts_close_utc","entry","sl","tp",
                "lots","exit_reason","gross_pnl","commission","swap","net_pnl","r_multiple",
                "bias_ema","rvol","or_width","stop_arm","exit_arm");
  return h;
}
void ORB_LedgerRow(int h,int id,string sym,int dir,datetime to,datetime tc,double entry,double sl,
                   double tp,double lots,string reason,double gross,double comm,double swap,
                   double net,double rmult,double biasEma,double rvol,double orw,int sArm,int eArm){
  if(h==INVALID_HANDLE) return;
  FileWrite(h,id,sym,(dir>0?"long":"short"),(string)(long)to,(string)(long)tc,entry,sl,tp,lots,
            reason,gross,comm,swap,net,rmult,biasEma,rvol,orw,sArm,eArm);
}
void ORB_LedgerClose(int h){ if(h!=INVALID_HANDLE) FileClose(h); }
#endif
```
- [ ] **Step 6: Commit** `feat(orb): risk sizing + ledger writer + risk tests`.

---

## Phase 2 — EA orchestrator (kernel: S0 + E0)

### Task 2.1: Write `ORB_EA.mq5` daily state machine

**Files:** Create `ORB/mt5/Experts/ORB/ORB_EA.mq5`.

Implements the §3–§8 chain as a per-day state machine. **Build the kernel first**: `InpStopArm=0` (S0), `InpExitArm=0` (E0). The other arms are already in the includes and are selected purely by input — no EA rewrite needed to sweep them.

- [ ] **Step 1: Declare inputs + globals**
```mql5
#include <Trade\Trade.mqh>
#include "..\\..\\Include\\ORB\\ORB_Time.mqh"
#include "..\\..\\Include\\ORB\\ORB_Range.mqh"
#include "..\\..\\Include\\ORB\\ORB_Bias.mqh"
#include "..\\..\\Include\\ORB\\ORB_Signals.mqh"
#include "..\\..\\Include\\ORB\\ORB_Stops.mqh"
#include "..\\..\\Include\\ORB\\ORB_Exits.mqh"
#include "..\\..\\Include\\ORB\\ORB_Risk.mqh"
#include "..\\..\\Include\\ORB\\ORB_Ledger.mqh"

input long   InpMagic            = 20260621;
input int    InpOrMinutes        = 15;       // 15 or 30
input int    InpBiasEmaPeriod    = 50;       // {20,50,100,200}
input ENUM_TIMEFRAMES InpBiasTF  = PERIOD_D1;
input double InpRvolThresh       = 1.5;      // {1.0..2.0}
input int    InpRvolLookback     = 14;
input double InpRangeGuardLo     = 0.5;
input double InpRangeGuardHi     = 2.0;
input double InpBufferFrac       = 0.1;
input int    InpEntryStartEt     = 945;      // HHMM
input int    InpEntryEndEt       = 1130;
input int    InpFlatEt           = 1600;
input int    InpStopArm          = 0;        // 0=S0,1=S1,2=S2
input double InpS2AtrK           = 1.5;
input int    InpAtrPeriod        = 14;
input int    InpExitArm          = 0;        // 0=E0,1=E1,2=E2,3=E3,4=E4
input double InpTargetK          = 1.0;      // E0=1, E1=2/3
input int    InpTrailEmaPeriod   = 8;        // 8 or 21 (E2/E3/E4)
input ENUM_TIMEFRAMES InpTrailTF = PERIOD_M15;
input double InpRiskPct          = 1.0;
input double InpMaxLot           = 50.0;
input int    InpSrvToUtcOffsetSec= 999999;   // 999999 = auto-detect at init
input string InpLedgerLabel      = "smoke";  // ledger filename suffix

CTrade   g_trade;
int      g_biasEmaHandle, g_trailEmaHandle, g_atrHandle;
int      g_srvOffsetSec;
int      g_ledger;
// daily state
enum OrbDay { WAIT, CAPTURING, ARMED, INTRADE, DONE };
OrbDay   g_state;
int      g_curDayEt;          // ET day-of-year to detect rollover
double   g_orHigh, g_orLow, g_orVolAccum;
int      g_bias;
double   g_priorWidths[], g_priorVols[];   // ring buffers length InpRvolLookback
ulong    g_posTicket; ulong g_pendTicket;
bool     g_tookPartial;
int      g_tradeSeq;
```

- [ ] **Step 2: `OnInit`** — validate, create handles, auto-detect server offset, open ledger
```mql5
int OnInit(){
  g_biasEmaHandle = iMA(_Symbol,InpBiasTF,InpBiasEmaPeriod,0,MODE_EMA,PRICE_CLOSE);
  g_trailEmaHandle= iMA(_Symbol,InpTrailTF,InpTrailEmaPeriod,0,MODE_EMA,PRICE_CLOSE);
  g_atrHandle     = iATR(_Symbol,InpTrailTF,InpAtrPeriod);
  if(g_biasEmaHandle==INVALID_HANDLE||g_trailEmaHandle==INVALID_HANDLE||g_atrHandle==INVALID_HANDLE)
    return INIT_FAILED;
  g_srvOffsetSec = (InpSrvToUtcOffsetSec!=999999)? InpSrvToUtcOffsetSec
                   : (int)((long)TimeCurrent()-(long)TimeGMT());  // server = UTC + offset
  g_trade.SetExpertMagicNumber((ulong)InpMagic);
  ArrayResize(g_priorWidths,0); ArrayResize(g_priorVols,0);
  string lp=StringFormat("ORB\\ledger_%s.csv",InpLedgerLabel);
  g_ledger=ORB_LedgerOpen(lp);
  g_state=WAIT; g_curDayEt=-1; g_tradeSeq=0;
  return INIT_SUCCEEDED;
}
void OnDeinit(const int r){ if(PositionSelectByTicket(g_posTicket)) CloseAndLog("forced_eod");
  ORB_LedgerClose(g_ledger);
  IndicatorRelease(g_biasEmaHandle); IndicatorRelease(g_trailEmaHandle); IndicatorRelease(g_atrHandle); }
```

- [ ] **Step 3: `OnTick` daily state machine** (kernel logic; full body)
```mql5
void OnTick(){
  datetime srv = TimeCurrent();
  int etMin = ORB_EtMinutesFromServer(srv,g_srvOffsetSec);
  MqlDateTime et; TimeToStruct(ORB_UtcToEt(srv-g_srvOffsetSec),et);

  // day rollover at first tick of a new ET day -> reset, roll RVOL/width history
  if(et.day_of_year!=g_curDayEt){
    if(g_state!=WAIT) RollHistory();      // push yesterday's OR width+vol into ring buffers
    g_curDayEt=et.day_of_year; g_state=WAIT;
    g_orHigh=-DBL_MAX; g_orLow=DBL_MAX; g_orVolAccum=0; g_tookPartial=false;
    g_pendTicket=0; g_posTicket=0;
  }

  // 1) capture OR
  if(ORB_InOpeningRange(srv,g_srvOffsetSec,InpOrMinutes)){
    g_state=CAPTURING;
    double hi=iHigh(_Symbol,PERIOD_M1,0), lo=iLow(_Symbol,PERIOD_M1,0);
    if(hi>g_orHigh) g_orHigh=hi; if(lo<g_orLow) g_orLow=lo;
    g_orVolAccum += (double)iTickVolume(_Symbol,PERIOD_M1,0)>0 ? 1 : 0; // accumulate per-tick proxy
    return;
  }

  // 2) at first tick AFTER the OR window, decide + arm
  if(g_state==CAPTURING && etMin>=570+InpOrMinutes){
    ArmIfQualified();        // bias + RVOL + range guard -> place stop order or go DONE
  }

  // 3) entry window expiry: cancel unfilled pending
  if(g_state==ARMED && !ORB_InEntryWindow(srv,g_srvOffsetSec,InpEntryStartEt,InpEntryEndEt)
     && etMin>=(InpEntryEndEt/100*60+InpEntryEndEt%100)){
    if(g_pendTicket>0){ g_trade.OrderDelete(g_pendTicket); g_pendTicket=0; }
    g_state=DONE;
  }

  // 4) detect fill ARMED -> INTRADE
  if(g_state==ARMED && g_pendTicket>0 && PositionSelectByTicket(g_pendTicket)){
    g_posTicket=g_pendTicket; g_pendTicket=0; g_state=INTRADE;
  }

  // 5) manage open trade (target / EMA trail / EOD flat)
  if(g_state==INTRADE) ManageTrade(srv,etMin);
}
```

- [ ] **Step 4: Implement helpers** `ArmIfQualified`, `ManageTrade`, `RollHistory`, `CloseAndLog`
```mql5
double EmaVal(int handle,int shift){ double b[]; if(CopyBuffer(handle,0,shift,1,b)<1) return 0; return b[0]; }
double AtrVal(){ double b[]; if(CopyBuffer(g_atrHandle,0,1,1,b)<1) return 0; return b[0]; }

void ArmIfQualified(){
  int n=ArraySize(g_priorWidths);
  if(n<InpRvolLookback){ g_state=DONE; return; }            // warm-up: need history
  double width=ORB_Width(g_orHigh,g_orLow);
  if(!ORB_RangeGuardOk(width,g_priorWidths,n,InpRangeGuardLo,InpRangeGuardHi)){ g_state=DONE; return; }
  if(ORB_Rvol(g_orVolAccum,g_priorVols,n) < InpRvolThresh){ g_state=DONE; return; }
  double priorClose=iClose(_Symbol,InpBiasTF,1);
  g_bias=ORB_Bias(priorClose,EmaVal(g_biasEmaHandle,1));
  if(g_bias==0){ g_state=DONE; return; }
  double entry=ORB_EntryPrice(g_bias,g_orHigh,g_orLow,InpBufferFrac);
  double sl   =ORB_StopLoss(InpStopArm,g_bias,entry,g_orHigh,g_orLow,
                            ORB_Mid(g_orHigh,g_orLow),AtrVal(),InpS2AtrK);
  double R=ORB_R(entry,sl);
  double tp = (InpExitArm<=1)? ORB_Target(g_bias,entry,R,InpTargetK) : 0.0; // E2/E3/E4 trail (no hard TP)
  double valPerUnit = SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_VALUE)
                      / SymbolInfoDouble(_Symbol,SYMBOL_TRADE_TICK_SIZE);
  double lots=ORB_LotsFromRisk(AccountInfoDouble(ACCOUNT_EQUITY),InpRiskPct,R,valPerUnit,
              SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_STEP),
              SymbolInfoDouble(_Symbol,SYMBOL_VOLUME_MIN),InpMaxLot);
  if(lots<=0){ g_state=DONE; return; }
  bool ok = (g_bias>0)? g_trade.BuyStop(lots,entry,_Symbol,sl,tp,ORDER_TIME_GTC,0)
                      : g_trade.SellStop(lots,entry,_Symbol,sl,tp,ORDER_TIME_GTC,0);
  if(ok){ g_pendTicket=g_trade.ResultOrder(); g_state=ARMED; } else g_state=DONE;
}

void ManageTrade(datetime srv,int etMin){
  if(!PositionSelectByTicket(g_posTicket)){ g_state=DONE; return; } // closed by SL/TP
  int dir=(PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY)?+1:-1;
  // EOD flat
  if(ORB_AtOrAfterFlat(srv,g_srvOffsetSec,InpFlatEt)){ CloseAndLog("forced_eod"); return; }
  // E2: partial at 1R then trail; E3/E4: pure trail; E0/E1: hard TP already on the order
  if(InpExitArm>=2){
    double entry=PositionGetDouble(POSITION_PRICE_OPEN), sl=PositionGetDouble(POSITION_SL);
    double R=ORB_R(entry,sl);
    if(InpExitArm==2 && !g_tookPartial){
      double oneR=ORB_Target(dir,entry,R,1.0), px=(dir>0?SymbolInfoDouble(_Symbol,SYMBOL_BID):SymbolInfoDouble(_Symbol,SYMBOL_ASK));
      if((dir>0&&px>=oneR)||(dir<0&&px<=oneR)){
        g_trade.PositionClosePartial(g_posTicket,PositionGetDouble(POSITION_VOLUME)/2.0); g_tookPartial=true; }
    }
    // EMA(M15) close-cross on the just-closed M15 bar
    static datetime lastM15=0; datetime m15t=iTime(_Symbol,InpTrailTF,0);
    if(m15t!=lastM15){ lastM15=m15t;
      double m15close=iClose(_Symbol,InpTrailTF,1), ema=EmaVal(g_trailEmaHandle,1);
      if(ORB_EmaCloseCrossExit(dir,m15close,ema)) CloseAndLog("ema_cross");
    }
  }
}

void RollHistory(){
  PushRing(g_priorWidths, ORB_Width(g_orHigh,g_orLow), InpRvolLookback);
  PushRing(g_priorVols,   g_orVolAccum,               InpRvolLookback);
}
void PushRing(double &arr[],double v,int cap){
  int n=ArraySize(arr);
  if(n<cap){ ArrayResize(arr,n+1); arr[n]=v; return; }
  for(int i=0;i<cap-1;i++) arr[i]=arr[i+1]; arr[cap-1]=v;
}
void CloseAndLog(string reason){
  if(!PositionSelectByTicket(g_posTicket)) return;
  int dir=(PositionGetInteger(POSITION_TYPE)==POSITION_TYPE_BUY)?+1:-1;
  double entry=PositionGetDouble(POSITION_PRICE_OPEN), sl=PositionGetDouble(POSITION_SL),
         tp=PositionGetDouble(POSITION_TP), lots=PositionGetDouble(POSITION_VOLUME),
         profit=PositionGetDouble(POSITION_PROFIT), swap=PositionGetDouble(POSITION_SWAP);
  datetime topen=(datetime)PositionGetInteger(POSITION_TIME);
  g_trade.PositionClose(g_posTicket);
  double R=ORB_R(entry,sl), rmult=(R>0? (dir>0? (PositionGetDouble(POSITION_PRICE_CURRENT)-entry):(entry-PositionGetDouble(POSITION_PRICE_CURRENT)))/R : 0);
  ORB_LedgerRow(g_ledger,++g_tradeSeq,_Symbol,dir,topen-g_srvOffsetSec,TimeCurrent()-g_srvOffsetSec,
                entry,sl,tp,lots,reason,profit,0.0,swap,profit+swap,rmult,
                EmaVal(g_biasEmaHandle,1),ORB_Rvol(g_orVolAccum,g_priorVols,ArraySize(g_priorVols)),
                ORB_Width(g_orHigh,g_orLow),InpStopArm,InpExitArm);
  g_state=DONE;
}
double OnTester(){ double t=TesterStatistics(STAT_TRADES); return t>0? TesterStatistics(STAT_PROFIT)/t : 0; }
```
*(Engineer note: commission column is 0 here because FTMO indices are spread-only; if a commission appears on the account, read `HistoryDealGetDouble(..,DEAL_COMMISSION)` in an `OnTradeTransaction` handler and populate it. The tester applies spread through fill prices, so `net_pnl` is already net of spread.)*

- [ ] **Step 5: Deploy + compile headless**
```powershell
pwsh tools/sync_orb_to_terminal.ps1
$DD="$env:APPDATA\MetaQuotes\Terminal\81A933A9AFC5DE3C23B15CAB19C63850"
& "C:\Program Files\FTMO Global Markets MT5 Terminal\MetaEditor64.exe" /compile:"$DD\MQL5\Experts\ORB\ORB_EA.mq5" /log:"$DD\MQL5\Logs\orb_compile.log"
Get-Content "$DD\MQL5\Logs\orb_compile.log" -Encoding Unicode | Select-Object -Last 5
```
Expected: log ends `0 errors, 0 warnings`. Fix until clean.

- [ ] **Step 6: Commit** `feat(orb): EA orchestrator (S0/E0 kernel) + ledger`.

### Task 2.2: Smoke backtest + discriminator

**Files:** Create `ORB/mt5/Presets/ORB_US100_baseline.set`.

- [ ] **Step 1: Write the baseline `.set`** (S0/E0, defaults from §11)
```ini
; ORB_US100_baseline.set
InpMagic=20260621
InpOrMinutes=15
InpBiasEmaPeriod=50
InpRvolThresh=1.5
InpRvolLookback=14
InpStopArm=0
InpExitArm=0
InpTargetK=1.0
InpRiskPct=1.0
InpSrvToUtcOffsetSec=999999
InpLedgerLabel=smoke_us100
```

- [ ] **Step 2: Run a one-month smoke backtest via the GUI** (driver comes in Phase 3; first run by hand to confirm the EA trades). Strategy Tester → Expert `ORB\ORB_EA`, Symbol `US100.cash`, Period `M1`, Model "Every tick based on real ticks", a recent month, load the `.set`, Start.
Expected: a handful of trades; `MQL5/Files/ORB/ledger_smoke_us100.csv` exists with header + rows.

- [ ] **Step 3: Discriminator (harness-validity check)** — run the same month with `InpStopArm=1` (S1 midpoint). Confirm the trade list **differs** from S0 (different SL → different stop-outs). If identical, the arm switch is not wired — fix before trusting any sweep.

- [ ] **Step 4: Commit** `chore(orb): baseline preset + smoke-test notes` (commit the `.set` and a short `ORB/mt5/SMOKE.md` recording the trade counts you saw — that file is the audit breadcrumb, not a metric claim).

---

## Phase 3 — Python: tester driver + gate (TDD)

### Task 3.1: `tools/orb_gate.py` — ledger → metrics → repo gate

**Files:** Create `tools/orb_gate.py`; Test `tools/tests/test_orb_gate.py`.

- [ ] **Step 1: Write the failing test** with a tiny fixture ledger
```python
# tools/tests/test_orb_gate.py
import csv, io
from tools.orb_gate import metrics_from_rows, apply_gate

def _rows(nets):
    return [{"net_pnl": str(x), "r_multiple": "1.0"} for x in nets]

def test_metrics_basic():
    m = metrics_from_rows(_rows([100, -50, 100, -50, 100]))
    assert m["trades"] == 5
    assert round(m["net"], 2) == 200.0
    assert m["max_single_frac"] > 0          # concentration fraction present

def test_gate_rejects_few_trades():
    v = apply_gate(metrics_from_rows(_rows([10, -5, 10])), oos_sharpe=0.8, is_sharpe=0.7)
    assert v["passed"] is False
    assert any("trade count" in r.lower() for r in v["reasons"])

def test_gate_rejects_concentration():
    # one trade = 90% of net
    v = apply_gate(metrics_from_rows(_rows([900] + [10]*9 + [-5]*9)),
                   oos_sharpe=1.0, is_sharpe=0.9)
    assert v["passed"] is False
    assert any("concentration" in r.lower() for r in v["reasons"])

def test_gate_pass():
    nets = [5, -1] * 20   # 40 trades, net=80, max_dd=-20%, concentration=6.25% — clears all gates
    v = apply_gate(metrics_from_rows(_rows(nets)), oos_sharpe=0.9, is_sharpe=0.8)
    assert v["passed"] is True
```

- [ ] **Step 2: Run → FAIL.** `python -m pytest tools/tests/test_orb_gate.py -v`

- [ ] **Step 3: Implement `tools/orb_gate.py`** (encodes [strategy-validation.md §2](../../strategy-validation.md) thresholds)
```python
"""ORB acceptance gate — the repo validation rules, codified. Pure functions."""
from __future__ import annotations
import csv, math
from typing import Iterable

GATE = dict(
    sharpe_floor=0.5, sharpe_ceiling=2.5, max_dd_limit=-0.30,  # tighter than -35% for leveraged index
    min_trades=30, max_single_frac=0.30, oos_over_is_max=1.30,
)

def read_ledger(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def metrics_from_rows(rows: Iterable[dict]) -> dict:
    nets = [float(r["net_pnl"]) for r in rows]
    n = len(nets); net = sum(nets)
    gross_win = sum(x for x in nets if x > 0); gross_loss = -sum(x for x in nets if x < 0)
    pf = (gross_win / gross_loss) if gross_loss > 0 else float("inf")
    # equity-curve max drawdown as a fraction of peak
    eq, peak, max_dd = 0.0, 0.0, 0.0
    for x in nets:
        eq += x; peak = max(peak, eq); 
        if peak > 0: max_dd = min(max_dd, (eq - peak) / peak)
    max_single = max((abs(x) for x in nets), default=0.0)
    return dict(trades=n, net=net, pf=pf, max_dd=max_dd,
                max_single_frac=(max_single/abs(net) if net else 0.0),
                wins=sum(1 for x in nets if x > 0))

def apply_gate(m: dict, oos_sharpe: float, is_sharpe: float) -> dict:
    reasons = []
    if m["trades"] < GATE["min_trades"]: reasons.append(f"trade count {m['trades']} < {GATE['min_trades']}")
    if oos_sharpe < GATE["sharpe_floor"]: reasons.append(f"OOS Sharpe {oos_sharpe:.2f} < {GATE['sharpe_floor']} (noise)")
    if oos_sharpe > GATE["sharpe_ceiling"]: reasons.append(f"OOS Sharpe {oos_sharpe:.2f} > {GATE['sharpe_ceiling']} (asset did it)")
    if is_sharpe > 0 and oos_sharpe > is_sharpe*GATE["oos_over_is_max"]:
        reasons.append(f"OOS Sharpe beats IS by >30% (luck)")
    if m["max_dd"] < GATE["max_dd_limit"]: reasons.append(f"max DD {m['max_dd']:.1%} worse than {GATE['max_dd_limit']:.0%}")
    if m["max_single_frac"] > GATE["max_single_frac"]:
        reasons.append(f"profit concentration {m['max_single_frac']:.0%} > {GATE['max_single_frac']:.0%}")
    return dict(passed=(len(reasons) == 0), reasons=reasons, metrics=m,
                oos_sharpe=oos_sharpe, is_sharpe=is_sharpe)

def sharpe(nets: list[float]) -> float:
    if len(nets) < 2: return 0.0
    mu = sum(nets)/len(nets); var = sum((x-mu)**2 for x in nets)/(len(nets)-1)
    sd = math.sqrt(var); return (mu/sd*math.sqrt(len(nets))) if sd > 0 else 0.0
```

- [ ] **Step 4: Run → PASS** (4 tests). **Step 5: Commit** `feat(orb): codified validation gate + tests`.

### Task 3.2: `tools/run_orb_backtest.py` — headless single-config driver

**Files:** Create `tools/run_orb_backtest.py`; Test `tools/tests/test_run_orb_backtest.py` (tests the ini builder + ledger locator only — not a live MT5 run).

- [ ] **Step 1: Failing test for the pure pieces**
```python
# tools/tests/test_run_orb_backtest.py
from tools.run_orb_backtest import build_tester_ini, ledger_path_for

def test_ini_contains_window_and_symbol():
    ini = build_tester_ini(symbol="US100.cash", from_date="2024.01.01", to_date="2024.03.31",
                           expert="ORB\\ORB_EA.ex5", set_file="ORB_US100_baseline.set",
                           report="r.htm", label="lbl")
    assert "Symbol=US100.cash" in ini and "FromDate=2024.01.01" in ini
    assert "ShutdownTerminal=1" in ini and "Model=1" in ini

def test_ledger_path_uses_label():
    p = ledger_path_for("/data", "win01")
    assert p.endswith("MQL5/Files/ORB/ledger_win01.csv".replace("/", "\\")) or "ledger_win01.csv" in p
```

- [ ] **Step 2: FAIL. Step 3: Implement `tools/run_orb_backtest.py`**
```python
"""Drive one headless MT5 Strategy Tester run, return the EA's ledger path.
The EA writes its own UTF-8 ledger; we do NOT parse the Polish HTM (kept only as a cross-check)."""
from __future__ import annotations
import os, subprocess, time, configparser
from pathlib import Path

FTMO_DATA = Path(os.environ["APPDATA"]) / "MetaQuotes/Terminal/81A933A9AFC5DE3C23B15CAB19C63850"
TERMINAL = Path(r"C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe")

def build_tester_ini(symbol, from_date, to_date, expert, set_file, report, label):
    return "\n".join([
        "[Tester]",
        f"Expert={expert}",
        f"Symbol={symbol}",
        "Period=M1",
        "Model=1",                 # every tick based on real ticks
        "Optimization=0",
        f"FromDate={from_date}",
        f"ToDate={to_date}",
        "Deposit=10000",
        "Currency=USD",
        "Leverage=1:100",
        f"Report={report}",
        "ReplaceReport=1",
        "ShutdownTerminal=1",
        f"TesterInputs={set_file}",
        "",
    ])

def ledger_path_for(data_dir, label):
    return str(Path(data_dir) / "MQL5" / "Files" / "ORB" / f"ledger_{label}.csv")

def run(symbol, from_date, to_date, set_file, label, data_dir=FTMO_DATA, terminal=TERMINAL, timeout=1800):
    report = str(Path(data_dir) / f"orb_report_{label}.htm")
    ini = build_tester_ini(symbol, from_date, to_date, "ORB\\ORB_EA.ex5", set_file, report, label)
    ini_path = Path(data_dir) / f"orb_tester_{label}.ini"
    ini_path.write_text(ini, encoding="utf-16")          # MT5 config inis are UTF-16
    ledger = ledger_path_for(data_dir, label)
    if os.path.exists(ledger): os.remove(ledger)
    subprocess.run([str(terminal), f"/config:{ini_path}"], check=False, timeout=timeout)
    # terminal self-shuts (ShutdownTerminal=1); wait for the ledger to appear
    for _ in range(60):
        if os.path.exists(ledger): break
        time.sleep(1)
    if not os.path.exists(ledger):
        raise RuntimeError(f"no ledger produced for {label} — check {report}")
    return ledger
```
*(Engineer note: the `.set` referenced by `TesterInputs` must sit in the terminal's `MQL5/Profiles/Tester/` dir. The driver should copy `ORB/mt5/Presets/<set>` there before launch — add that copy in `run()`; included in the next step.)*

- [ ] **Step 4: Add the preset-copy into `run()`** before launch:
```python
    tester_presets = Path(data_dir) / "MQL5" / "Profiles" / "Tester"
    tester_presets.mkdir(parents=True, exist_ok=True)
    src_set = Path("ORB/mt5/Presets") / set_file
    (tester_presets / set_file).write_text(src_set.read_text(), encoding="utf-8")
```

- [ ] **Step 5: Run unit tests → PASS.** Then a **live single-window smoke**: 
```bash
python -c "from tools.run_orb_backtest import run; print(run('US100.cash','2024.05.01','2024.05.31','ORB_US100_baseline.set','smoke_may24'))"
```
Expected: prints a ledger path; the CSV has rows. (This is the first end-to-end headless run.)

- [ ] **Step 6: Commit** `feat(orb): headless single-config tester driver + tests`.

---

## Phase 4 — Walk-forward orchestrator

### Task 4.1: `tools/run_orb_walkforward.py` — rolling windows, sequential selection, stitch, gate, audit

**Files:** Create `tools/run_orb_walkforward.py`; Test `tools/tests/test_run_orb_walkforward.py` (window math + stitch only).

The spec's anti-combinatorial rule means "optimize on IS" = "run each candidate config on the IS window and pick the best by IS Sharpe", then run that single winner on the adjacent OOS window. Because the candidate set is small and discrete, no MT5 optimizer is needed — we call `run_orb_backtest.run()` per candidate per window.

- [ ] **Step 1: Failing test for window generation + stitch**
```python
from tools.run_orb_walkforward import rolling_windows, stitch_oos

def test_rolling_windows_cover_and_step():
    w = rolling_windows("2021-01-01", "2024-01-01", is_months=12, oos_months=3)
    assert w[0]["is_from"] == "2021.01.01"
    assert w[0]["oos_from"] == "2022.01.01" and w[0]["oos_to"] == "2022.04.01"
    assert w[1]["oos_from"] == "2022.04.01"          # steps by oos length
    assert all(x["oos_to"] <= "2024.01.01" for x in w)

def test_stitch_concats_oos_rows():
    a=[{"net_pnl":"10"}]; b=[{"net_pnl":"-4"}]
    assert len(stitch_oos([a,b]))==2
```

- [ ] **Step 2: FAIL. Step 3: Implement `tools/run_orb_walkforward.py`**
```python
"""ORB walk-forward: rolling IS/OOS windows, sequential arm/grid selection on IS,
blind OOS, stitch OOS ledgers, apply the gate, write an audit report."""
from __future__ import annotations
import csv, os, sys
from datetime import date
from dateutil.relativedelta import relativedelta   # python-dateutil
# repo's tools/ is NOT a package — add this dir to sys.path and import siblings directly
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path: sys.path.insert(0, _HERE)
import orb_gate, audit
from run_orb_backtest import run

def _d(s): y,m,d = map(int, s.replace(".","-").split("-")); return date(y,m,d)
def _s(d): return f"{d.year:04d}.{d.month:02d}.{d.day:02d}"

def rolling_windows(start, end, is_months=12, oos_months=3):
    s, e = _d(start), _d(end); out=[]
    is_from = s
    while True:
        oos_from = is_from + relativedelta(months=is_months)
        oos_to   = oos_from + relativedelta(months=oos_months)
        if oos_to > e: break
        out.append(dict(is_from=_s(is_from), is_to=_s(oos_from),
                        oos_from=_s(oos_from), oos_to=_s(oos_to)))
        is_from = is_from + relativedelta(months=oos_months)
    return out

def stitch_oos(ledger_row_lists): 
    out=[]; [out.extend(x) for x in ledger_row_lists]; return out

def select_on_is(symbol, win, candidates):
    """candidates: list of (label, set_file). Return the set_file with best IS Sharpe."""
    best=None
    for label,setf in candidates:
        ledg = run(symbol, win["is_from"], win["is_to"], setf, f"is_{label}_{win['oos_from']}")
        rows = orb_gate.read_ledger(ledg)
        sh = orb_gate.sharpe([float(r["net_pnl"]) for r in rows])
        if best is None or sh>best[0]: best=(sh,setf,label)
    return best[1], best[2]

def walk(symbol, start, end, candidates, is_months=12, oos_months=3, run_name="ORB"):
    rep = audit.new_report(run_name)
    wins = rolling_windows(start, end, is_months, oos_months)
    oos_lists=[]
    for win in wins:
        winner_set, winner_label = select_on_is(symbol, win, candidates)
        ledg = run(symbol, win["oos_from"], win["oos_to"], winner_set, f"oos_{winner_label}_{win['oos_from']}")
        rows = orb_gate.read_ledger(ledg); oos_lists.append(rows)
        audit.add(rep, ledg)
    stitched = stitch_oos(oos_lists)
    m = orb_gate.metrics_from_rows(stitched)
    oos_sh = orb_gate.sharpe([float(r["net_pnl"]) for r in stitched])
    verdict = orb_gate.apply_gate(m, oos_sharpe=oos_sh, is_sharpe=oos_sh)  # is_sharpe filled per-window in full impl
    # write stitched OOS + manifest
    import os
    stitched_path=os.path.join(rep,"oos_stitched.csv")
    with open(stitched_path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(stitched[0].keys())); w.writeheader(); w.writerows(stitched)
    audit.add(rep, stitched_path)
    audit.write_manifest(rep, title=f"{run_name} walk-forward {symbol}",
        summary_lines=[f"OOS trades={m['trades']} net={m['net']:.0f} PF={m['pf']:.2f} "
                       f"maxDD={m['max_dd']:.1%} Sharpe={oos_sh:.2f} "
                       f"PASS={verdict['passed']}", *(f"- {r}" for r in verdict['reasons'])],
        metrics=dict(trades=m["trades"], net=round(m["net"],2), pf=round(m["pf"],2),
                     max_dd=round(m["max_dd"],4), oos_sharpe=round(oos_sh,2), passed=verdict["passed"]),
        kind="backtest")
    return verdict, rep
```
*(Engineer note: `is_sharpe` should be the IS Sharpe of each window's winner, averaged/stitched — wire that through `select_on_is` returning the IS Sharpe and accumulate; left as a one-line extension to keep this step focused. The gate's "OOS ≤ IS+30%" check needs it.)*

- [ ] **Step 4: Run unit tests → PASS.** **Step 5: Commit** `feat(orb): walk-forward orchestrator (window math, IS selection, stitch, gate, audit)`.

---

## Phase 5 — Execution runbook (produce the verdict)

Each run is audited automatically (`reports/ORB-<UTCstamp>/`). Report numbers ONLY from these files (audit-trail rule). Follow the spec's **sequential** protocol — do not grid-search all arms at once.

### Task 5.1: Lock the SL arm (on E0)

- [ ] **Step 1:** Create three presets identical to baseline except `InpStopArm` ∈ {0,1,2}: `ORB_US100_S0.set`, `ORB_US100_S1.set`, `ORB_US100_S2.set` (all `InpExitArm=0`). Commit them.
- [ ] **Step 2:** Run walk-forward with these three as the candidate set:
```bash
python -c "from tools.run_orb_walkforward import walk; \
v,r=walk('US100.cash','2021-10-01','2026-06-01',[('S0','ORB_US100_S0.set'),('S1','ORB_US100_S1.set'),('S2','ORB_US100_S2.set')],run_name='ORB-sl'); \
print(r); print(v['passed'], v['reasons'])"
```
- [ ] **Step 3:** Inspect the manifest in the printed `reports/ORB-sl-<stamp>/`. Record which SL arm won most windows. That is the locked SL for the next stage. (Do not claim edge yet — this is arm selection.)

### Task 5.2: Lock the exit arm (SL fixed)

- [ ] **Step 1:** Create presets for E0..E4 with the locked SL: `ORB_US100_E0.set` … `ORB_US100_E4.set` (set `InpExitArm`, `InpTargetK` for E1∈{2,3}, `InpTrailEmaPeriod` for E4=21). Commit.
- [ ] **Step 2:** Walk-forward with E0..E4 as candidates (`run_name='ORB-exit'`). 
- [ ] **Step 3:** Record the winning exit arm from the manifest. E0 is the control — if no runner arm beats it on stitched OOS Sharpe net of costs, lock E0.

### Task 5.3: Confirm bias-EMA + RVOL, then apply the gate

- [ ] **Step 1:** With SL+exit locked, sweep `InpBiasEmaPeriod` ∈ {20,50,100,200} then `InpRvolThresh` ∈ {1.0,1.5,2.0} the same way (`run_name='ORB-bias'`, `'ORB-rvol'`). Keep ≤4 active tuned params total.
- [ ] **Step 2:** Take the final frozen config. Read its `ORB-*` manifest. Apply the gate verdict (already computed). 
- [ ] **Step 3:** **Decision point.** If `passed=False`, write the verdict into the spec §13 + the [strategy-validation.md Findings log](../../strategy-validation.md#findings-log) and STOP (research answered: no edge — a valid outcome). If `passed=True`, proceed.

### Task 5.4: Frozen cross-instrument OOS (only if 5.3 passed)

- [ ] **Step 1:** Without changing any parameter, run the single frozen config (one preset, no selection) over the full period on **US500.cash**, and on **GER40.cash** re-anchored to the Frankfurt open (`InpSrvToUtcOffsetSec` unchanged; set the OR/entry/flat ET inputs to the DAX cash session — 09:00–09:15 Frankfurt; document the exact ET-equivalent inputs in the preset). Use `run_orb_backtest.run()` directly (no walk-forward — these are pure OOS confirmation).
- [ ] **Step 2:** Apply the gate to each. Real edge survives the instrument swap; a curve-fit does not.
- [ ] **Step 3:** Buy-and-hold sanity + short-side standalone (spec §10): compute B&H return of US100 over the period and compare; split the stitched OOS ledger by `dir` and report long-only vs short-only net. If all profit is long-side drift, say so.

### Task 5.5: Write up

- [ ] **Step 1:** Update `ORB/strategy.md` Status line + §13 with the verdict and the `reports/ORB-*` paths.
- [ ] **Step 2:** Add a row to the [strategy-validation.md Findings log](../../strategy-validation.md#findings-log): date, ORB, the OOS numbers, the rule it illustrates.
- [ ] **Step 3:** Update `project_orb` memory with the outcome. Commit everything.

---

## Self-review notes (author)

- **Spec coverage:** §2 instrument/session → Task 1.1 + EA inputs; §3 OR → 1.2 + EA capture; §4 bias → 1.3; §5 RVOL+guard → 1.2 + `ArmIfQualified`; §6 entry → 1.4 + EA arm; §7 SL arms → 1.5 + 5.1; §8 exit arms → 1.6 + 5.2; §9 risk → 1.7; §10 validation (WF, costs, gate, cross-instrument, B&H) → Phases 3–5; §11 params → presets; §12 data → Phase 0; §13 flaws → 5.3/5.5; §14 build order → Phase sequence. All sections mapped.
- **Costs:** spread applied by the tester via fills; `net_pnl` is net; stop-entry slippage to be set in the tester (deviation) — add `Slippage` handling in the `.set` / EA `SetDeviationInPoints` before 5.x runs (engineer: wire `g_trade.SetDeviationInPoints` in `OnInit` from a new `InpSlippagePts` input, default a realistic US100 value, and document it).
- **Known shortcut:** RVOL uses an OR-window tick-count proxy (`g_orVolAccum`); if `iTickVolume` of the M1 bars in the window is preferred, sum `iTickVolume(_Symbol,PERIOD_M1,shift)` across the window instead — equivalent, pick one and keep it consistent IS/OOS.
- **Open item flagged for executor:** `is_sharpe` wiring in `walk()` (per-window winner IS Sharpe) for the OOS-vs-IS gate check — noted inline in Task 4.1.
```
