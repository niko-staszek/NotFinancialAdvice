# CBS — Measured-Move Reverse Analysis (Design)

**Date:** 2026-06-09
**Status:** Approved design → implementation plan next
**Parent strategy:** PSND (`PSND/strategy.md`) — target = `High + Low − Open` over a measurement window.

---

## 1. Purpose

PSND forward-trades a daily price target. CBS does the **reverse analysis**: instead of trading the
move, it *characterizes* it from history. Two questions:

1. **How long does the full measured move take?** For every instrument, for the whole day and for
   every intraday window (anchor hour × block size), measure the hours from window-close until price
   first reaches the target.
2. **What is the best entry into that move?** For every completing move, evaluate a menu of entry
   techniques (not only PSND's EMA21) and rank them by realized reward-to-risk.

Deliverables: two auditable tables (T1 time-to-complete, T2 best-entry) plus full audit-trail proof
for every reported number.

---

## 2. Definitions (locked)

### 2.1 Target
For a measurement window `W = [anchor, anchor + N)`:
```
target = high(W) + low(W) − open(W)
```
`open(W)` = open of the first bar in the window; `high(W)`/`low(W)` = extremes over the window
(wicks included). One target per window, direction-agnostic (PSND semantics).

### 2.2 Window grid (per instrument, per day)
- **Anchor hour** `A ∈ {00, 01, …, 23}` (24 anchors, broker/server time).
- **Block size** `N ∈ {1, 2, …, 24}` hours (24 sizes).
- = **576 windows** per instrument per day. Example: `A=01, N=24` → window `01:00→01:00 next day`.
  `A=00, N=24` → `00:00→24:00`.
- "Whole day" is not special — it is simply the cell `A=00, N=24` (and other 24h anchors).

### 2.3 Completion ("full measured move")
Price has **touched within settle tolerance** of the target:

| Instrument        | Tolerance |
|-------------------|-----------|
| Forex majors      | 5 pips    |
| XAUUSD, XTIUSD    | 15 pips   |
| BTCUSD            | $10       |
| ETHUSD            | $5        |

Touch = an M5 bar whose `[low, high]` range comes within tolerance of the target price.

### 2.4 Completion clock
- Clock **starts** at window close (`anchor + N`).
- Clock **cap = 48h** (two cycles — captures slower instruments like gold/crypto).
- If no touch within 48h → `completed = False`, `hours = NaN`.
- `hours_to_complete` = (timestamp of first touching bar − window close) in hours, float.
- A target already within tolerance at the very first post-window bar → `hours ≈ 0` and flagged
  `instant = True` (PSND's "already settled — do not trade" case), reported separately so it does
  not inflate the speed stats.

### 2.5 Direction of the move
At window close, the **approach side** is fixed: if target is above the window-close price → the
move is *up* (a long opportunity); if below → *down* (short). This drives entry-side logic in §4.

---

## 3. Engine A — Timing

For each `(instrument, day, A, N)`:
1. Build window, compute target.
2. Determine approach side (§2.5).
3. Scan M5 bars from window-close forward up to 48h; find first tolerance-touch.
4. Emit one **timing record**:
   `instrument, date, anchor, block, target, approach_side, completed, instant, hours_to_complete,
    window_close_price, bars_scanned`.

All timing records → one tidy CSV per instrument (the raw evidence behind T1).

---

## 4. Engine B — Entry evaluation

Runs only on **completing, non-instant** moves. For each such move, every candidate entry detector
is offered the bar path from window-close to completion (+ a small look-back for structure). A
detector either fires (emitting `entry_price`, `invalidation_price`, `entry_time`) or abstains.

### 4.1 Candidate menu (all tested)

**Structure set**
- `ema21_retest` — PSND's own: price reclaims EMA21 (H1) then retests it from the correct side.
- `swing_retest` — break of a recent swing then retest of the broken level.
- `sr_retest` — retest of a prior horizontal S/R level (PDH/PDL/PWH/PWL).
- `fvg_fill` — entry on fill of a ≥20-pip H1/M5 imbalance in the move direction.
- `fib_cluster` — touch of a fib cluster zone (multi-period 38.2/61.8/161.8 per PSND cluster rules).

**Liquidity / ICT set**
- `order_block` — tap of the last opposing candle before the impulse.
- `liquidity_sweep` — stop-run beyond PDH/PDL (or local extreme) then reclaim.
- `breaker` — failed order block flipped to support/resistance.
- `eqh_eql_raid` — raid of equal highs/lows then reversal.

**Time / level set**
- `session_open_retrace` — retrace to the session open after the move starts.
- `prior_level_react` — reaction off PDH/PDL/PWH (level-based, distinct from `sr_retest` trigger).
- `opening_range_break` — break + retest of the first-hour range.
- `round_number` — tap of the nearest round number in the path.

**Baselines (control group — must be beaten to claim edge)**
- `enter_at_window_close` — naive: enter at window-close price.
- `first_pullback_pct` — enter after price pulls back X% of distance toward start.
- `first_m5_close` — enter on first M5 close in the move direction.

### 4.2 Invalidation (SL) per entry
Each detector defines its own structural invalidation (e.g. swing low beyond a long retest, far side
of the FVG, beyond the swept liquidity). **Fallback:** if no clean structural level, SL = `k × ATR`
(ATR on M5, `k` in config, default documented). This keeps R comparable across detectors.

### 4.3 Metrics per entry instance
Hold from `entry_price` to the target (completion). Record:
- `R = (target − entry) / (entry − invalidation)` (sign-adjusted by side).
- `MFE`, `MAE` (max favorable / adverse excursion, in price and in R).
- `win` = target reached before invalidation hit.
- `cost_spread` = spread at entry bar (from MT5 `spread` column), netted into R.
- `entry_lead_hours` = how early in the move the entry fired.

All entry instances → one tidy CSV per instrument (raw evidence behind T2).

---

## 5. Outputs

### T1 — Time-to-complete
Per anchor, a heatmap-style table: rows = instrument × block(1…24h), values =
`completion_rate%`, `median_hours`, `p25/p75 hours`, `N`, `instant_rate%`. Rendered as markdown
tables + (optional) CSV for plotting. Best cells (high completion %, low median hours) flagged.

### T2 — Best entry
Per instrument: rows = entry type, cols = `median_R`, `win%`, `median_MAE_R`, `N`, `beats_baseline?`.
Winner per instrument flagged. Global rollup: which entry wins most often across instruments, and
whether structure actually beats the baselines.

### Audit trail (mandatory — `audit-trail` skill)
Every run writes to `reports/<name>-<UTCstamp>/`:
- raw per-event CSVs (timing + entries),
- `config.json` (instruments, tolerances, anchors, blocks, ATR k, cost model, data file hashes),
- the driver script copy,
- a run log excerpt proving execution,
- `manifest.sha256` over all artifacts.
No metric appears in any report unless it traces to a file in that folder.

---

## 6. Repo layout

```
CBS/
  README.md              # what CBS is, how to run, how to read reports
  strategy.md            # this methodology, locked for audit
  config.py              # instruments, tolerances, anchors(0-23), blocks(1-24), ATR k, costs
  data/                  # M5 bars dumped from MT5 (large files gitignored)
  cbs/
    bars.py              # load/validate M5 CSV → indexed frames; resample to H1 where needed
    target.py            # window → H+L-O target
    timing.py            # Engine A
    entries.py           # candidate detectors (one function per entry, pure, testable)
    evaluate.py          # Engine B: R / MFE / MAE / cost
    report.py            # T1, T2, audit manifest
  tests/                 # synthetic-bar unit tests (TDD) for every detector + timing + target
  reports/               # audit-trail output per run
```

---

## 7. Data

- Source: running MT5 terminal via `tools/mt5_data.py dump-bars`.
- Instruments: EURUSD, GBPUSD, USDCAD, USDJPY, USDCHF, AUDUSD, NZDUSD, XAUUSD, XTIUSD, BTCUSD,
  ETHUSD. **Query `symbols` first** — broker may not expose all (oil/crypto uncertain per the
  HedgeHog broker inventory). Any dropped instrument is documented in the run config, not silently
  skipped.
- Timeframe: M5 primary (H1 derived by resampling for EMA21/structure where a detector needs it).
- History: ~2 years per instrument, subject to broker availability.
- Pip/point sizes per instrument live in `config.py` (JPY pairs, metals, crypto each differ).

---

## 8. Discipline & risks

- **TDD first** on `target.py`, `timing.py`, and each detector against synthetic bars with known
  answers — these are easy to get subtly wrong (off-by-one on window edges, tolerance sign, side).
- **Cost realism:** spread netted into every R; PSND treats spread as part of entry cost.
- **Survivorship of windows:** 576 cells × ~500 trading days × 11 instruments is a large multiple-
  comparisons surface — best cells will be reported with N and dispersion, and flagged as
  in-sample. A held-out split (e.g. last 6 months OOS) confirms top cells before any are called a
  real edge.
- **Lookahead:** detectors and targets may only use bars at or before their decision time. Enforced
  in code and asserted in tests.
- **Determinism:** no wall-clock/random in the pipeline; same data + config → identical reports.

---

## 9. Out of scope (YAGNI)

- Live trading / order execution.
- MT5 on-chart visual indicator (optional follow-up once winners are known).
- Parameter optimization of the entries themselves (we rank a fixed menu, not tune each).
- Money-management / position-sizing study (PSND already specifies it).
