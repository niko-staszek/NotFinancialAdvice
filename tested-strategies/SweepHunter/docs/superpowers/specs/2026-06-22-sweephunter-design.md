# SweepHunter — Asia/London Liquidity Sweep → NY M1 FVG Reversal

**Status:** Approved design (2026-06-22)
**Engine:** MQL5 Expert Advisor, tested in MT5 Strategy Tester (FTMO terminal)
**Home:** `NotFinancialAdvice/tested-strategies/SweepHunter/` (monorepo; reuses shared `tools/` harness + validation gate)
**Author:** nikof

---

## 1. Premise

ICT-style intraday model on the NY AM session:

1. At **09:00 ET**, mark the high/low of the prior **Asia** and **London** sessions — four liquidity levels.
2. During the NY hunt window, wait for one of those levels to be **swept** (price trades beyond it, grabbing resting liquidity).
3. Drop to **M1**, wait for a **fair value gap (FVG)** in the *reversal* direction (displacement back the other way).
4. Enter on the FVG, stop at the sweep swing, target either a fixed **1:2 RR** or the next **draw on liquidity (DOL)**.

Source idea (user, verbatim): *"at 9 a.m. New York time, mark out the Asia and London high-low, wait for those highs and lows to sweep, then drop down to the one-minute time frame, take a fair value gap reversal to the other side, and target a 1 to 2 RR … instead of just targeting a 1:2 RR, use market structure, target draws on liquidity … set your stop at the swing low and target your next draw on liquidity."*

This spec encodes **both** exit models so they can be compared on identical entries.

---

## 2. Definitions

All session times are in **ET** (US Eastern, with US DST), converted from FTMO server time (EET/EEST) via the existing `ORB_Time.mqh` DST machinery. Times are EA inputs in `HHMM` form.

| Term | Definition |
|------|-----------|
| **Asia session** | Default `20:00–00:00 ET` (input `InpAsiaStartEt=2000`, `InpAsiaEndEt=0000`). Window may wrap midnight → bucketing handles wrap. |
| **London session** | Default `02:00–05:00 ET` (`InpLonStartEt=0200`, `InpLonEndEt=0500`). |
| **Mark time** | `09:00 ET` (`InpMarkEt=0900`) — when the 4 levels are frozen. |
| **Hunt window** | `09:00–11:30 ET` (`InpHuntStartEt=0900`, `InpHuntEndEt=1130`) — sweeps + entries only inside this window. |
| **EOD flat** | `16:00 ET` (`InpFlatEt=1600`) — any open position force-closed. |
| **Marked levels** | `AsiaH, AsiaL, LonH, LonL` = max-high / min-low of M1 bars whose ET time-of-day falls in each session window, scanned at mark time. |
| **Sweep** | An M1 bar where `high > level` (for a high) or `low < level` (for a low), occurring inside the hunt window. Arms the opposite-direction setup. |
| **Sweep extreme (swing)** | The most extreme price (highest high / lowest low) reached from sweep onset until entry — the stop reference. |
| **Bullish FVG** | 3-candle gap on M1: `high[i-2] < low[i]`. Gap zone `[high[i-2], low[i]]`. Proximal edge = `high[i-2]`. |
| **Bearish FVG** | 3-candle gap on M1: `low[i-2] > high[i]`. Gap zone `[high[i], low[i-2]]`. Proximal edge = `low[i-2]`. |
| **R** | `|entry − stop|` (risk per unit). |
| **DOL** | Draw on liquidity = nearest *un-swept* marked level lying in the trade direction beyond entry. |

---

## 3. Daily state machine (per symbol, resets each ET day)

```
WAIT → MARKED → ARMED → INTRADE → DONE
```

### WAIT → MARKED  (at mark time, 09:00 ET)
- Scan trailing M1 history (≥ ~14h back). Bucket each bar by ET time-of-day into Asia / London windows.
- Compute `AsiaH/AsiaL/LonH/LonL`. If a session has zero bars (holiday/gap), that pair is invalid and excluded from the level set.
- Require ≥1 valid level, else `DONE` for the day.

### MARKED → ARMED  (hunt window, sweep detection)
- On each new M1 bar in `[InpHuntStartEt, InpHuntEndEt)`, test the active level set:
  - High swept (`high > level`) → arm **SHORT** side; reversal FVG sought = **bearish**.
  - Low swept (`low < level`) → arm **LONG** side; reversal FVG sought = **bullish**.
- **First** sweep arms the setup (`InpMaxSetupsPerDay=1`). Record swept level, direction, and begin tracking the sweep extreme.
- **Level mode** (`InpLevelMode`): `FOUR` (default) = 4 distinct levels, first swept arms. `COMBINED` = use only outer `max(AsiaH,LonH)` / `min(AsiaL,LonL)`.

### ARMED → INTRADE  (FVG entry)
- On each completed M1 bar after the sweep, scan the last 3 closed bars for an FVG in the reversal direction.
- On detection, place entry per `InpEntryMode`:
  - `LIMIT` (default): limit order at FVG proximal edge × depth (`InpFillDepth=0.0` → proximal, `0.5` → mid, `1.0` → distal). Buy-limit for longs, sell-limit for shorts. Order valid until hunt-window close, then cancelled.
  - `MARKET`: market order at close of the 3rd FVG bar.
- **Stop:** sweep extreme ± buffer. `buffer = InpStopBufferAtrK × ATR(M1, InpAtrPeriod)`. Long: `stop = swingLow − buffer`. Short: `stop = swingHigh + buffer`.
- **Target** (`InpTargetMode`):
  - `RR`: `TP = entry + dir × InpTargetRR × R` (default `InpTargetRR=2.0`).
  - `DOL`: `TP = ` nearest un-swept marked level in trade direction beyond entry. If none qualifies, fall back to `RR` at `InpTargetRR`.
- **Sizing:** risk `InpRiskPct=1.0` % of equity over `R`, via `ORB_LotsFromRisk` logic (tick-value aware; respects volume step/min/`InpMaxLot`).
- One setup per day: after order placed (or window closes unfilled) no further setups.

### INTRADE → DONE
- Position managed to SL / TP by broker.
- `InpFlatEt` (16:00 ET) force-flat if still open.
- Unfilled limit cancelled at hunt-window close → `DONE`.

---

## 4. Architecture

Mirror the ORB EA: pure, unit-testable logic in `.mqh`; orchestrator wires the state machine.

```
tested-strategies/SweepHunter/
  mt5/Include/SweepHunter/
    SH_Time.mqh       # ET/DST/session-window bucketing. Reuses ORB_Time DST calendars.
    SH_Sessions.mqh   # scan M1 → AsiaH/L, LonH/L (wrap-aware bucketing)
    SH_Sweep.mqh      # level set, sweep test, swing-extreme tracker
    SH_FVG.mqh        # 3-candle bullish/bearish FVG detect + edge/depth price
    SH_Targets.mqh    # RR target + DOL resolution (nearest un-swept level in dir)
    SH_Stops.mqh      # swing ± ATR buffer
    SH_Risk.mqh       # lots-from-risk (adapt ORB_Risk)
    SH_Ledger.mqh     # CSV trade ledger — gate-compatible header (incl. net_pnl)
  mt5/Experts/SweepHunter/SweepHunter_EA.mq5   # orchestrator + OnTradeTransaction accounting + OnTester
  mt5/Scripts/SweepHunter_Tests/
    helpers/TestRunner.mqh                      # copied from ORB_Tests (MQL5TEST sentinels)
    test_sh_time.mq5 / test_sh_sessions.mq5 / test_sh_sweep.mq5 /
    test_sh_fvg.mq5 / test_sh_targets.mq5 / test_sh_stops.mq5     # per-module unit tests
  mt5/Presets/                                  # .set per symbol & target mode (RR / DOL)
  docs/superpowers/{specs,plans}/   reports/   strategy.md   VERDICT.md
```

**Build/test/run harness — reuse the shared `tools/` (monorepo), do NOT reinvent:**
- `tools/run_mql5_tests.py` (+ offline `--log-file`) — pure MQL5TEST log parser; unit-tested.
- `tools/run_orb_selftest.py` pattern — the **working** headless runner: MetaEditor `/compile` → `[StartUp] Script=` ini → `terminal64 /config` (the `/Script:` flag is broken on this FTMO build). SweepHunter gets a sibling `run_sweephunter_selftest.py`.
- `tools/run_orb_backtest.py` pattern → `run_sweephunter_backtest.py`: UTF-16 `[Tester]` ini, `Period=M1`, `Model=1` (real ticks), `.set`→`Profiles/Tester/`, ledger via `FILE_COMMON` → `Common/Files/SweepHunter/ledger_<label>.csv`.
- `tools/run_orb_walkforward.py` pattern → `run_sweephunter_walkforward.py`: rolling IS/OOS, select-on-IS-Sharpe, blind OOS, stitch, gate, manifest.
- `tools/orb_gate.py` — **reused as-is** (generic; needs only `net_pnl`). The ledger header below is gate-compatible.
- `tools/sync_orb_to_terminal.ps1` pattern → `sync_sweephunter_to_terminal.ps1`: copies `Include/SweepHunter`, `Experts/SweepHunter`, `Scripts/SweepHunter_Tests` into the FTMO terminal `MQL5/` tree (MT5 compiles from the synced copy; not a live symlink).

**Ledger header** (`SH_Ledger.mqh`, written `FILE_COMMON`): `trade_id, symbol, dir, ts_open_utc, ts_close_utc, entry, sl, tp, lots, exit_reason, gross_pnl, commission, swap, net_pnl, r_multiple, swept_level, sweep_side, target_mode, fill_depth`. `net_pnl = gross + commission + swap` so the gate's metrics are net of costs.

**Time module note:** `ORB_Time.mqh` already provides `ORB_UtcToEt`, `ORB_IsUsDST`, `ORB_ServerToUtcOffsetSec` (FTMO EET/EEST), `ORB_EtMinutesFromServer`. `SH_Time.mqh` reuses these and adds a generic wrap-aware window test `SH_InWindowEt(etMin, startHHMM, endHHMM)` and a per-bar ET-minute bucketer.

---

## 5. Inputs (summary)

| Input | Default | Notes |
|-------|---------|-------|
| `InpMagic` | 20260622 | |
| `InpAsiaStartEt / InpAsiaEndEt` | 2000 / 0000 | Asia window (ET) |
| `InpLonStartEt / InpLonEndEt` | 0200 / 0500 | London window (ET) |
| `InpMarkEt` | 0900 | freeze levels |
| `InpHuntStartEt / InpHuntEndEt` | 0900 / 1130 | sweep+entry window |
| `InpFlatEt` | 1600 | EOD flat |
| `InpLevelMode` | FOUR | FOUR \| COMBINED |
| `InpEntryMode` | LIMIT | LIMIT \| MARKET |
| `InpFillDepth` | 0.0 | 0=proximal,0.5=mid,1=distal |
| `InpTargetMode` | RR | RR \| DOL |
| `InpTargetRR` | 2.0 | RR target & DOL fallback |
| `InpStopBufferAtrK` | 0.15 | stop buffer = K×ATR(M1) |
| `InpAtrPeriod` | 14 | |
| `InpMaxSetupsPerDay` | 1 | |
| `InpRiskPct` | 1.0 | % equity per trade |
| `InpMaxLot` | 50.0 | |
| `InpSrvToUtcOffsetSec` | 999999 | 999999 = auto-detect per tick |
| `InpLedgerLabel` | "smoke" | ledger filename suffix |

---

## 6. Validation & reporting (audit-trail discipline)

### 6.1 Self-test first (TDD)
`SweepHunter_selftest.mq5` builds synthetic OHLC arrays and asserts the pure functions, **must pass before any backtest**:
- FVG detect: bullish/bearish positives + non-FVG negatives; proximal/mid/distal price math.
- Sweep detect: high/low sweeps, no false sweep when bar stays inside; swing-extreme tracking.
- Session bucketing: bars correctly assigned; **Asia midnight-wrap** correctness; empty-session → invalid pair.
- DOL: picks nearest un-swept level in direction; fallback to RR when none.
- Time/DST: ET minutes correct on US-DST and EU-DST boundary days; FTMO offset.
- Stop/target/lots arithmetic.

### 6.2 Backtests — walk-forward, per the repo's standing rule
This repo's bar (`docs/strategy-validation.md`, monorepo `CLAUDE.md`): **out-of-sample or it didn't happen.** ORB, SPZ, IVB, ETR were all rejected under it. SweepHunter is judged identically.

- **Method:** walk-forward (`run_sweephunter_walkforward.py`). Rolling windows (default IS 12mo / OOS 3mo, slide 3mo). Optimize on IS (select best-IS-Sharpe config among the candidate `.set`s), run **blind** on OOS, **stitch** all OOS segments, report the stitched result.
- **Acceptance gate** (`orb_gate.py`, applied automatically — never eyeballed): OOS max DD better than −30% (tighter than −35% for leveraged FX), OOS Sharpe ∈ [0.5, 2.5], OOS Sharpe ≤ IS+30%, ≥30 trades, no single trade > 30% of net P&L, all metrics **net of** spread/commission/swap.
- **Cross-instrument generalization** (ORB's lesson): the *same* fixed config must hold on multiple instruments. Passing on one symbol only = exposure/cherry-pick, not edge. Run the cross-instrument table on: XAUUSD, EURUSD, GBPUSD, USDJPY, USDCHF, US30, US100, US500, BTCUSD (whatever FTMO carries).
- **Buy-and-hold sanity:** would dumb buy-and-hold of the asset have matched it? If yes → exposure, reject (the Tesla trap).
- **Cost realism:** `Model=1` real ticks (spread from ticks); EA ledger captures `commission`+`swap` so `net_pnl` is net.
- **Both exit modes** (`InpTargetMode=RR` / `DOL`) carried as candidates and reported side by side on identical entries.

### 6.3 Reporting
Every run writes to `reports/<run-name>-<UTC stamp>/`:
- tester `.ini` (exact config) + the EA `.set`,
- per-window IS/OOS ledgers + `oos_stitched.csv`,
- `gate_*.txt` (gate verdict + metrics) and `summary.md`,
- a log excerpt proving the run executed (bars, trades, date span),
- `manifest.md` / `manifest.sha256`.

Final judgement recorded in `VERDICT.md` (🟢 accepted / 🔴 rejected, with the cross-instrument table), and the finding logged to `docs/strategy-validation.md`'s Findings table.

**No metric** (PF, DD, win rate, expectancy, trade count, R-multiple, net %) is stated in any summary unless it traces to a result file inspected that turn. (Per `feedback_verify_before_reporting`.)

---

## 7. Known risks / decisions

- **Session-time correctness is the #1 bug source.** Mitigated by reusing the proven `ORB_Time.mqh` DST/offset code and asserting boundary days in the self-test.
- **Nested levels:** when London range sits inside Asia (or vice-versa), the first-swept-arms rule may arm on an inner level while outer liquidity remains. Accepted for v1; `COMBINED` mode and per-level comparison available as levers.
- **Limit-fill realism:** proximal-edge limits assume price trades to the level; Strategy Tester real-tick fills handle this. MARKET mode is the robustness fallback.
- **DOL objectivity:** DOL is defined mechanically (nearest un-swept marked level in direction) — no discretionary structure reading — so it is reproducible. This is a simplification of "market structure draw"; richer DOL (intraday swing structure) is a possible v2.
- **Multi-instrument session validity:** BTCUSD has no true Asia/London open; results there test the concept's robustness, not its thesis.
- **WF warmup fragmentation (ORB's logged pitfall):** ORB's walk-forward falsely failed once because a per-window indicator warmup dropped ~1mo of each OOS segment. SweepHunter's state resets *daily* (no multi-day warmup), so risk is low — but the WF driver must still feed each OOS window enough lead-in M1 history for the 09:00 session-marking scan on its first day. Asserted in the self-test (`SH_Sessions` with a truncated history → invalid pair, not a crash).

---

## 8. Out of scope (v1, YAGNI)

- Multi-timeframe FVG confirmation beyond M1.
- Partial take-profits / trailing (RR and DOL are single-target exits).
- Discretionary market-structure DOL (swing-based) — v2 candidate.
- Live/forward deployment — backtest validation only.
- **Large parameter optimization sweeps** (MT5 genetic/grid over the full input space). The walk-forward *validation* selects among a **small, hand-authored candidate `.set` list** (e.g. RR vs DOL × a couple of session-window / entry-mode variants) — not an exhaustive optimizer. Broad sweeps are a separate effort only if a baseline first shows promise.
