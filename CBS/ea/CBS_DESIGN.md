# CBS EA & Discovery — Design Specification v2

## Lessons from v1

1. **Target is not a signal.** H+L-O is WHERE price goes (TP level). Filters tell us WHEN to enter.
2. **Filters must be checked continuously**, not once at window open. Enter when all align.
3. **CLU delays entry** — waits for price to clear the obstacle, then enters at the new price.
4. **Discovery and EA must simulate the same logic** — otherwise Discovery results don't predict EA performance.
5. **No look-ahead.** Intraday targets must use the PREVIOUS day's session, not the current day's.
6. **TimeGMT() = TimeCurrent() in Strategy Tester.** Must use BrokerGMTOffset input.

---

## Strategy Flow

```
PREVIOUS WINDOW completes
    → Compute target: T = H + L - O of that window
    → T is a PRICE LEVEL (the take-profit destination)

CURRENT WINDOW opens
    → Every 60 seconds, check entry conditions:
        1. Is target still valid? (distance > min_distance)
        2. Direction: BUY if T > price, SELL if T < price
        3. EMA aligned? (if enabled)
        4. H4 trend aligned? (if enabled)
        5. LLR clear? (if enabled)
        6. CLU clear? (if enabled)
            - If cluster blocks path → WAIT for price to cross it
            - When cleared → re-check EMA → enter at new price
    → ALL enabled conditions met simultaneously → ENTER
    → Window closes without entry → no trade (no loss)

TRADE OPEN
    → TP = target ± settlement offset
    → SL = based on distance from entry to target × SL ratio
    → Hold until TP hit, SL hit, or 18h timeout
    → Timeout: close at market (small win or loss)
```

---

## Window Types & Target Computation

### Offset (24h window)
- **Definition:** 24h period starting at `start_hour` UTC
- **Example:** offset_11:00 = 11:00 UTC day 1 → 11:00 UTC day 2
- **Target from:** the PREVIOUS completed 24h window
  - O = Open of first M15 bar in the window
  - H = max(High) of ALL M15 bars in the window
  - L = min(Low) of ALL M15 bars in the window
  - T = H + L - O
- **Entry window:** the CURRENT 24h period (same hours, next day)
- **No look-ahead:** target is fully known when the previous window closes

### Intraday (2-8h session)
- **Definition:** session from `start_hour` to `start_hour + duration` UTC
- **Example:** intra_12-16_4h = 12:00-16:00 UTC
- **Target from:** YESTERDAY's session (same hours, previous day)
  - O = Open of first M15 bar in yesterday's session
  - H = max(High) of ALL M15 bars in yesterday's session
  - L = min(Low) of ALL M15 bars in yesterday's session
  - T = H + L - O
- **Entry window:** TODAY's session (same hours)
- **No look-ahead:** target is from yesterday, fully known before today's session

---

## Filters (Entry Conditions)

Each filter is a YES/NO gate. Checked every tick. Trade enters when ALL enabled filters say YES simultaneously.

### EMA (M15 EMA21)
- **BUY:** current close > EMA21 value (price above = bullish momentum)
- **SELL:** current close < EMA21 value (price below = bearish momentum)
- **Purpose:** ensures short-term momentum agrees with trade direction
- **Behavior:** can toggle on/off throughout the window as price crosses EMA

### H4 (H4 EMA21 trend)
- **BUY:** H4 close > H4 EMA21 (uptrend on higher timeframe)
- **SELL:** H4 close < H4 EMA21 (downtrend on higher timeframe)
- **Purpose:** higher-timeframe trend alignment
- **Behavior:** changes slowly (every 4 hours), usually stable within a window

### LLR (Line of Least Resistance)
- **BUY:** price above ascending support line from recent swing lows
- **SELL:** price below descending resistance line from recent swing highs
- **Purpose:** no micro-structure obstacle in the path to target
- **Behavior:** updates with each new M15 bar

### CLU (Fibonacci Cluster Blocker)
- **Compute:** Fib levels from PD/PW/PM high-low → group into clusters → find blockers between entry and target
- **If no blockers:** PASS (trade can enter)
- **If blockers exist:** WAIT for price to clear the highest/lowest blocker
  - Check each tick: has price crossed the clear_price?
  - When cleared: re-check EMA at new price, then enter
  - If not cleared within window: no trade
- **Purpose:** avoids trading into S/R confluence zones
- **Special:** this is the only filter that can DELAY entry (not just block/allow)

---

## SL/TP Computation

### TP (settlement)
```
settle_offset = (settle_tol + spread) × pip_size

BUY:  TP = target - settle_offset   (don't need price to reach full target)
SELL: TP = target + settle_offset
```

### SL (from entry to RAW target, not TP)
```
distance = |target - entry| / pip_size

Tier mode (forex):
  dist ≤ 35 pips  → SL = distance × 3.0
  35 < dist ≤ 100 → SL = distance × 1.5
  dist > 100      → SL = distance × 1.0

Tier mode (standard/non-forex): always 1.0×

Fixed ratio: 1:1 = 1.0×, 1:1.5 = 1.5×, 1:2 = 2.0×

BUY:  SL_price = entry - SL_pips × pip_size
SELL: SL_price = entry + SL_pips × pip_size
```

### Minimum distance (strategy.md rule 2)
```
ALWAYS enforced — not just when CLU is on.
"If less than 15 pips to the target → do NOT open. Spread is additional."
Effective minimum = min_distance_pips + current_spread
Forex: 15 + spread (~16.5 pips)
XAUUSD: 50 + spread (~75 pips)
BTCUSD: 50 + spread (~100 pips)
```

### Entry price
```
BUY:  entry = ASK (spread baked in)
SELL: entry = BID (spread baked in)
```

---

## Timeout
```
deadline = entry_time + 18 hours
If neither TP nor SL hit by deadline → close at market price
```

---

## Slot Architecture

4 independent slots per chart: Off, Intra1, Intra2, Intra3.

Each slot has its own:
- Window definition (start_hour, duration)
- Filter flags (use_ema, use_h4, use_clu, use_llr)
- SL mode (tier, 1:1, 1:1.5, 1:2)
- Base lot size
- State (idle / watching / clu_waiting / active / done)

Slots never interfere with each other. All 4 can be open simultaneously.

### Slot State Machine
```
IDLE
  → New window detected → compute target → go to WATCHING

WATCHING
  → Every tick: check EMA + H4 + LLR + CLU
  → All pass → ENTER → go to ACTIVE
  → CLU blocks → go to CLU_WAITING
  → Any other filter fails → stay in WATCHING (retry next tick)
  → Window closes → go to IDLE (no trade, no loss)

CLU_WAITING
  → Every tick: has price cleared the cluster?
  → Yes + EMA still OK → ENTER → go to ACTIVE
  → 18h timeout from signal → go to IDLE (abandon)
  → Window closes → go to IDLE

ACTIVE
  → Trade is open with SL/TP set
  → Every tick: check if position still exists (SL/TP may have fired)
  → Deadline reached → close at market → go to IDLE

IDLE (ready for next window)
```

---

## Broker Time Handling

All window hours in config are **UTC**. MT5 bars are in **broker time**.

```
broker_offset = BrokerGMTOffset × 3600  (input parameter, default 2 for 5ers)
UTC_time = TimeCurrent() - broker_offset
broker_time_of_utc_event = utc_timestamp + broker_offset
```

`TimeGMT()` is NOT used (returns `TimeCurrent()` in Strategy Tester).

---

## Discovery Script (CBS_Discovery.mq5)

MQL5 Script that tests all combos using broker's own bar data.

### Must simulate EXACTLY what the EA does:

1. **Load bars:** M15, M5 (fallback M15), H4, D1 into arrays
2. **Pre-compute:** EMA21, H4 trend, LLR flags, CLU period levels
3. **For each window × each day:**
   - Compute target from PREVIOUS completed window (offset: prev 24h; intraday: yesterday's session)
   - Determine entry point: simulate continuous filter checking
     - Scan M15 bars within the entry window
     - For each bar: check filters at that bar's close
     - First bar where ALL enabled filters pass → entry point
     - CLU: if blocked, scan forward for clear, then check EMA at clear point
   - If no bar passes all filters within the window → skip (no trade)
4. **Forward simulation from entry:**
   - Scan M5 (or M15) bars forward from entry
   - Check TP threshold: BUY high >= target - settle_offset; SELL low <= target + settle_offset
   - Check SL: BUY low <= sl_price; SELL high >= sl_price
   - First hit wins. Same bar: SL wins (conservative).
   - 18h timeout: close at last bar's close

### Key difference from v1 Discovery:
- v1 entered at midnight (first bar of day) — WRONG
- v2 simulates continuous filter checking within the window — matches EA behavior
- v1 had intraday look-ahead (same-day session) — WRONG
- v2 uses previous day's session for intraday targets — no look-ahead

### Output CSV:
Same columns as before:
```
symbol, target_type, window, flags, n, settle_rate, win_rate, pf, total_pips,
avg_pips, avg_settle_h, med_settle_h, avg_rr, med_rr, avg_dist, pct_timeout
```

---

## Live EA (CBS_EA.mq5)

### OnInit
1. Detect instrument config (pip_size, settle_tol, etc.)
2. Compute broker offset from input
3. Initialize indicator handles (EMA21 M15, H4 EMA21)
4. Initialize 4 slots to IDLE
5. Start 60-second timer

### OnTimer / OnTick (throttled to 60s)
1. Daily loss guard check
2. Weekend check (skip Sat/Sun)
3. For each slot:
   - If ACTIVE: check position exists + timeout
   - If CLU_WAITING: check if price cleared → enter or abandon
   - If IDLE/WATCHING: ProcessSlot()

### ProcessSlot
1. Compute target for this window
2. Check we're inside the entry window
3. Check we haven't already traded this window
4. Determine direction from current price vs target
5. Check min distance (if CLU enabled)
6. Check EMA → if fail, return (retry next tick)
7. Check H4 → if fail, return (retry next tick)
8. Check LLR → if fail, return (retry next tick)
9. Check CLU → if blocked, set CLU_WAITING state, return
10. ALL conditions met → compute SL/TP/lot → open trade → mark window done

### ExecuteEntry
1. Entry price = ASK (BUY) or BID (SELL)
2. TP = target ± settle_offset
3. SL from entry to RAW target × SL ratio
4. Lot = base_lot × distance tier multiplier
5. Deadline = now + 18h
6. Place market order via CTrade
7. Log to journal CSV

---

## File Structure

```
CBS/ea/
├── CBS_EA.mq5              ← Live EA (rewrite)
├── CBS_Discovery.mq5       ← Discovery Script (rewrite)
├── CBS_DESIGN.md           ← This file
├── CBS_ARCHITECTURE.md     ← Reference (keep as-is)
└── Include/CBS/
    ├── CBS_Config.mqh      ← Keep (inputs, instrument detect, weekend check, daily guard)
    ├── CBS_Targets.mqh     ← Rewrite (fix entry timing, match Discovery)
    ├── CBS_SL.mqh          ← Keep (SL/TP computation is correct)
    ├── CBS_Indicators.mqh  ← Keep (EMA/H4 filters are correct)
    ├── CBS_Clusters.mqh    ← Keep (CLU logic is correct)
    ├── CBS_LLR.mqh         ← Keep (LLR logic is correct)
    ├── CBS_Sizing.mqh      ← Keep (distance tier is correct)
    ├── CBS_Trade.mqh       ← Rewrite (slot state machine)
    └── CBS_Journal.mqh     ← Keep (CSV logging is correct)
```

### What to KEEP (correct, tested):
- `CBS_Config.mqh` — instrument detection, inputs, daily guard, weekend check
- `CBS_SL.mqh` — SL ratio, TP settlement offset, entry price helpers
- `CBS_Indicators.mqh` — EMA21 + H4 iMA-based filters
- `CBS_Clusters.mqh` — Fib cluster building, blocker detection, clear check
- `CBS_LLR.mqh` — micro-swing detection
- `CBS_Sizing.mqh` — distance tier lot adjustment
- `CBS_Journal.mqh` — CSV trade logging

### What to REWRITE:
- `CBS_Targets.mqh` — target computation with correct window boundaries
- `CBS_Trade.mqh` — slot state machine (IDLE/WATCHING/CLU_WAITING/ACTIVE)
- `CBS_EA.mq5` — ProcessSlot with continuous filter monitoring
- `CBS_Discovery.mq5` — simulate continuous filter checking, no look-ahead

---

## Instrument Constants

| Symbol | pip_size | settle_tol | spread | is_forex | cluster_pips | min_dist |
|--------|----------|-----------|--------|----------|-------------|---------|
| EURUSD | 0.0001 | 5 | 1.5 | yes | 5 | 15 |
| GBPUSD | 0.0001 | 5 | 1.5 | yes | 5 | 15 |
| USDCAD | 0.0001 | 5 | 2.0 | yes | 5 | 15 |
| USDJPY | 0.01 | 5 | 1.5 | yes | 5 | 15 |
| USDCHF | 0.0001 | 5 | 1.5 | yes | 5 | 15 |
| AUDUSD | 0.0001 | 5 | 1.5 | yes | 5 | 15 |
| NZDUSD | 0.0001 | 5 | 1.5 | yes | 5 | 15 |
| XAUUSD | 0.1 | 15 | 25.0 | no | 15 | 50 |
| BTCUSD | 1.0 | 10 | 50.0 | no | 10 | 50 |
| ETHUSD | 1.0 | 5 | 15.0 | no | 5 | 30 |

---

## .set File Format

MT5 Strategy Tester format:
```
ParameterName=value||start||step||stop||Y/N
```

Booleans: `true`/`false`. Extension: `.set`.
Location: `MQL5/Profiles/Tester/` or `MQL5/Files/`.

Generated by `gen_sets_from_csv.py` from Discovery CSV results.

---

## Validation Checklist

1. **Discovery on EURUSD** → check offset WR ~89%, intraday WR with CLU should be high but NOT 100% (no look-ahead)
2. **EA backtest on EURUSD** with Discovery .set file → results should closely match Discovery
3. **Compare specific dates:** pick 5 random dates, verify EA enters at same time Discovery simulates
4. **Timeout rate < 15%** (v1 had 47% — the continuous monitoring should reduce this)
5. **No "Market closed" errors** (weekend check works)
6. **No "Invalid stops" errors** (SL/TP validation works)
7. **CLU wait-for-clear fires** at least some trades (verify in debug log)
