# CBS EA Parameters Reference
## Complete list of all configurable parameters for MT5 .set file

---

## 1. TARGET CALCULATION

### WindowType (enum)
How the measurement window is defined for CBS target formula: `Target = High + Low - Open`

| Value    | Description |
|----------|-------------|
| `OFFSET`   | 24-hour window starting at a fixed UTC hour offset (e.g. 11:00 UTC to 11:00 UTC next day) |
| `INTRADAY` | Shorter window (2-8 hours) at session-specific times (e.g. 08:00-11:00 UTC) |

### WindowStartHour (int, 0-23)
UTC hour when the measurement window opens.
- For OFFSET: the daily reset hour (0-12 tested, best results at 09-12)
- For INTRADAY: the session start hour (e.g. 0, 7, 8, 14...)

### WindowDurationHours (int, 2-8)
*Only used when WindowType = INTRADAY.*
Length of the measurement window in hours.
- Tested values: 2, 3, 4, 6, 8
- For OFFSET this is always 24h (implicit)

### Tested Window Combinations

**OFFSET windows** (24h, start hour varies):
```
offset_00:00, offset_01:00, offset_02:00, offset_03:00,
offset_04:00, offset_05:00, offset_06:00, offset_07:00,
offset_08:00, offset_09:00, offset_10:00, offset_11:00, offset_12:00
```

**INTRADAY windows** (variable duration):
```
intra_00-06_6h, intra_05-13_8h, intra_07-10_3h, intra_07-11_4h,
intra_07-13_6h, intra_07-15_8h, intra_08-10_2h, intra_08-11_3h,
intra_09-12_3h, intra_10-13_3h, intra_12-16_4h, intra_12-18_6h,
intra_13-17_4h, intra_14-18_4h, intra_14-20_6h, intra_15-18_3h,
intra_16-19_3h, intra_18-21_3h, intra_18-24_6h, intra_20-24_4h,
intra_22-04_6h
```

---

## 2. ENTRY FILTERS (each true/false)

All filters are independent and can be combined. 16 possible combinations (2^4).
A filter being ON means: "only take the trade if this condition is met."

### UseEMA (bool)
**M15 EMA21 direction agreement.**
- Computes 21-period EMA on M15 Close
- BUY allowed only if: entry price > EMA21 (price above EMA = bullish)
- SELL allowed only if: entry price < EMA21 (price below EMA = bearish)
- Purpose: ensures short-term momentum agrees with trade direction

### UseH4 (bool)
**H4 EMA21 trend alignment.**
- Computes 21-period EMA on H4 Close
- BUY allowed only if: H4 close > H4 EMA21 (uptrend on higher timeframe)
- SELL allowed only if: H4 close < H4 EMA21 (downtrend on higher timeframe)
- Purpose: higher-timeframe trend filter, avoids counter-trend trades

### UseCLU (bool)
**Fibonacci retracement cluster obstacle detection.**
- Computes Fibonacci levels from Previous Day, Previous Week, Previous Month high/low
- Fib levels used: 0.382, 0.618, -0.382, -0.618, 1.382, 1.618, 2.618
- Groups nearby fibs into "clusters" within cluster_size_pips of each other
- If a cluster sits between entry and target, the trade waits for price to clear it
- If price doesn't clear the cluster within MAX_HOLD_HOURS, trade is skipped
- Also enforces minimum distance: target must be at least `min_distance` pips from entry
- Purpose: avoids trading into strong S/R confluence zones
- **This was the single most impactful filter across all instruments**

#### CLU sub-parameters (per instrument):
| Parameter | EURUSD | GBPUSD | USDCAD | USDJPY | USDCHF | AUDUSD | NZDUSD | XAUUSD | BTCUSD | ETHUSD |
|-----------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| cluster_size_pips | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 15 | 10 | 5 |
| min_distance_pips | 15 | 15 | 15 | 15 | 15 | 15 | 15 | 50 | 50 | 30 |

### UseLLR (bool)
**Line of Least Resistance — micro-swing support/resistance.**
- Checks recent M15 swing highs/lows
- BUY allowed only if: no recent swing resistance blocking the path to target
- SELL allowed only if: no recent swing support blocking the path to target
- Purpose: avoids trading into immediate micro-structure obstacles

---

## 3. STOP LOSS MODE

### SLMode (enum)
Determines how the initial stop loss distance is calculated AND how the trade is managed after entry.

#### Basic Modes (static SL, no exit management):

| Value | Initial SL | What happens | R:R if target hit |
|-------|-----------|--------------|-------------------|
| `TIER` | Distance-based tiers (forex only) | SL stays fixed until target or timeout | Varies by tier |
| `RATIO_1_1` | 1.0 × target distance | SL stays fixed | ~1.0 (minus spread) |
| `RATIO_1_1_5` | 1.5 × target distance | SL stays fixed | ~0.67 (minus spread) |
| `RATIO_1_2` | 2.0 × target distance | SL stays fixed | ~0.50 (minus spread) |

#### Tier System Detail (forex only):
| Tier | Target Distance | SL = X × distance | Example: dist=25 pips |
|------|----------------|-------------------|----------------------|
| A | ≤ 35 pips | **3.0×** | SL = 75 pips |
| B | 35 - 100 pips | **1.5×** | SL = 112 pips (if dist=75) |
| C | > 100 pips | **1.0×** | SL = 120 pips (if dist=120) |

For non-forex (XAUUSD, BTCUSD, ETHUSD): tier always uses 1.0× regardless of distance.

#### Managed Modes (dynamic SL with exit management):

All 3 managed modes use **TIER as initial SL**, then modify SL after activation.

| Value | Initial SL | Activation | After Activation |
|-------|-----------|------------|-----------------|
| `BE` | Tier | Price reaches **50%** of target | SL moves to **entry** (breakeven) |
| `TRAIL` | Tier | Price reaches **50%** of target | SL trails at **30%** of target distance behind price |
| `PARTIAL` | Tier | Price reaches **50%** of target | **Close 50%** of position, trail remaining 50% at **30%** behind |

---

### Detailed Managed Mode Explanations:

### BE (Breakeven)
```
1. Trade opens with Tier SL (e.g. entry=1.1000, target=1.1040, SL=1.0880 for Tier A 3×)
2. Price moves to 50% of target (1.1020)
3. SL moves to entry price (1.1000) = breakeven
4. Now the trade can only:
   a) Hit target at 1.1040 -> profit = 40 pips - spread
   b) Come back to 1.1000 -> profit = 0 (minus spread only)
   c) Timeout at 18h -> close at current price (guaranteed near-breakeven or better)
```
**Effect**: Eliminates big losses. Once activated, worst case is ~breakeven.
**Best for**: Forex offsets (EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD)

### Trail (Trailing Stop)
```
1. Trade opens with Tier SL
2. Price moves to 50% of target -> trailing activates
3. Trail distance = max(2 × spread, 30% of target distance)
4. Each bar: SL moves to (Close - trail_distance) for BUY, never moves backward
5. Example: entry=1.1000, target=1.1040, trail=12 pips
   - Price hits 1.1020 -> trail activates, SL = 1.1020 - 0.0012 = 1.1008
   - Price moves to 1.1030 -> SL = 1.1030 - 0.0012 = 1.1018
   - Price moves to 1.1035 -> SL = 1.1035 - 0.0012 = 1.1023
   - Price drops to 1.1023 -> stopped out at +23 pips (locked profit)
   OR
   - Price hits target 1.1040 -> full profit = 40 pips - spread
```
**Effect**: Locks in progressively more profit as price approaches target.
**Trail distance formula**: `max(spread × 2, target_distance × 0.30)`

### Partial (Partial Close + Trail)
```
1. Trade opens with Tier SL (full position, e.g. 1.0 lot)
2. Price moves to 50% of target -> partial close triggers
3. Close 50% of position at current price
   - Locked profit = 0.5 × (50% of target distance - spread)
   - Example: entry=1.1000, target=1.1040, close 0.5 lot at 1.1020
   - Locked = 0.5 × (20 - 1.5) = 9.25 pips equivalent
4. Remaining 50% trails at 30% of target distance (same as Trail mode)
5. Final P&L = locked_partial + remaining_half_result
```
**Effect**: Guarantees some profit early, lets the rest run with protection.
**Best for**: NZDUSD offset (100% WR in backtest)

---

## 4. TRADE MANAGEMENT

### MaxHoldHours (int)
Maximum time to hold a trade before forced close. Default: **18 hours**.
If neither target nor SL is hit within this time, trade closes at current market price.

### SettleTolerance (pips)
How close price must get to the target to count as "settled" (target hit).
| Symbol | Settle Tolerance |
|--------|-----------------|
| EURUSD | 5 pips |
| GBPUSD | 5 pips |
| USDCAD | 5 pips |
| USDJPY | 5 pips |
| USDCHF | 5 pips |
| AUDUSD | 5 pips |
| NZDUSD | 5 pips |
| XAUUSD | 15 pips |
| BTCUSD | 10 pips |
| ETHUSD | 5 pips |

---

## 5. INSTRUMENT-SPECIFIC CONSTANTS

| Parameter | EURUSD | GBPUSD | USDCAD | USDJPY | USDCHF | AUDUSD | NZDUSD | XAUUSD | BTCUSD | ETHUSD |
|-----------|--------|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| pip_size | 0.0001 | 0.0001 | 0.0001 | 0.01 | 0.0001 | 0.0001 | 0.0001 | 0.1 | 1.0 | 1.0 |
| settle_tol | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 15 | 10 | 5 |
| spread_pips | 1.5 | 1.5 | 2.0 | 1.5 | 1.5 | 1.5 | 1.5 | 25.0 | 50.0 | 15.0 |
| tier_mode | forex | forex | forex | forex | forex | forex | forex | standard | standard | standard |
| cluster_size | 5 | 5 | 5 | 5 | 5 | 5 | 5 | 15 | 10 | 5 |
| min_distance | 15 | 15 | 15 | 15 | 15 | 15 | 15 | 50 | 50 | 30 |

---

## 6. MANAGED EXIT SUB-PARAMETERS

These apply only when SLMode is BE, TRAIL, or PARTIAL:

| Parameter | Value | Description |
|-----------|-------|-------------|
| ActivationPct | 0.50 (50%) | Price must reach this % of target distance to activate managed exit |
| TrailPct | 0.30 (30%) | Trail distance as % of target distance (used by TRAIL and PARTIAL) |
| TrailMinSpreadMult | 2.0 | Trail distance minimum = spread × this multiplier (avoids too-tight trail) |

**Trail distance formula:**
```
trail_pips = max(spread_pips × TrailMinSpreadMult, target_distance_pips × TrailPct)
```

---

## 7. PROPOSED EA INPUT STRUCTURE FOR .SET FILE

The EA runs **two independent target slots** on the same chart — one OFFSET and one INTRADAY.
Each slot has its own filters, SL mode, and trade management. Both can be active at the same time,
meaning the EA can hold **up to 2 trades simultaneously** per instrument (one from each slot).

Each slot can be enabled/disabled independently via `Offset_Enabled` and `Intra_Enabled`.

```
; ===================================================================
; CBS EA Configuration — Dual Slot (Offset + Intraday)
; ===================================================================

; ===================== SLOT 1: OFFSET TARGET =======================
Offset_Enabled=true          ; Enable/disable offset slot

; -- Target Window --
Offset_StartHour=12          ; UTC hour for 24h window start (0-12)

; -- Entry Filters --
Offset_UseEMA=false          ; M15 EMA21 direction filter
Offset_UseH4=true            ; H4 EMA21 trend filter
Offset_UseCLU=false          ; Fibonacci cluster obstacle filter
Offset_UseLLR=false          ; Line of Least Resistance filter

; -- Stop Loss --
Offset_SLMode=4              ; 0=TIER, 1=RATIO_1_1, 2=RATIO_1_1_5, 3=RATIO_1_2,
                             ; 4=BE, 5=TRAIL, 6=PARTIAL

; -- Managed Exit (only when SLMode >= 4) --
Offset_ActivationPct=50     ; % of target distance to activate (default 50)
Offset_TrailPct=30           ; % of target distance for trail (default 30)

; -- Trade Management --
Offset_MaxHoldHours=18       ; Max hours before forced close
Offset_MagicNumber=100001    ; Unique magic number for offset trades

; =================== SLOT 2: INTRADAY TARGET =======================
Intra_Enabled=true           ; Enable/disable intraday slot

; -- Target Window --
Intra_StartHour=14           ; UTC hour for session start (0-23)
Intra_DurationHours=6        ; Session length in hours (2-8)

; -- Entry Filters --
Intra_UseEMA=false           ; M15 EMA21 direction filter
Intra_UseH4=true             ; H4 EMA21 trend filter
Intra_UseCLU=true            ; Fibonacci cluster obstacle filter
Intra_UseLLR=false           ; Line of Least Resistance filter

; -- Stop Loss --
Intra_SLMode=0               ; 0=TIER, 1=RATIO_1_1, 2=RATIO_1_1_5, 3=RATIO_1_2,
                             ; 4=BE, 5=TRAIL, 6=PARTIAL

; -- Managed Exit (only when SLMode >= 4) --
Intra_ActivationPct=50      ; % of target distance to activate (default 50)
Intra_TrailPct=30            ; % of target distance for trail (default 30)

; -- Trade Management --
Intra_MaxHoldHours=18        ; Max hours before forced close
Intra_MagicNumber=100002     ; Unique magic number for intraday trades

; =================== SHARED / INSTRUMENT ===========================
SettleTolerancePips=5        ; How close to target = "hit"
PipSize=0.0001               ; Price unit per pip (auto-detect from chart)
SpreadPips=1.5               ; Expected spread in pips
ClusterSizePips=5            ; Fib cluster grouping threshold
MinDistancePips=15           ; Minimum entry-to-target distance
TierMode=0                   ; 0=forex (A/B/C tiers), 1=standard (always 1x)
Offset_RiskPercent=1.0       ; Risk % of account for offset trades
Intra_RiskPercent=1.0        ; Risk % of account for intraday trades
MaxSlippage=3                ; Max slippage in points
```

### How the two slots work together:
```
Timeline example for EURUSD:

  OFFSET slot (24h window from 12:00 UTC):
    12:00 UTC -> compute target from yesterday's 12:00-12:00 OHLC
    12:01 UTC -> check filters, if pass -> open OFFSET trade (magic 100001)
    Holds up to 18h (until 06:00 next day)

  INTRADAY slot (14:00-20:00 UTC window):
    20:00 UTC -> compute target from today's 14:00-20:00 OHLC
    20:01 UTC -> check filters, if pass -> open INTRADAY trade (magic 100002)
    Holds up to 18h (until 14:00 next day)

  Both trades can coexist! Different magic numbers keep them separate.
  Risk management should account for both positions being open.
```

---

## 8. BEST CONFIGS FROM BACKTEST — DUAL SLOT PER INSTRUMENT

Each instrument runs both an offset and intraday slot simultaneously.

### EURUSD
```
; Slot 1: OFFSET  ->  WR 84.1%, PF 12.43, +8295 pips, settle 4.4h
Offset_Enabled=true
Offset_StartHour=12
Offset_UseEMA=false
Offset_UseH4=true
Offset_UseCLU=false
Offset_UseLLR=false
Offset_SLMode=4              ; BE

; Slot 2: INTRADAY  ->  WR 100%, PF inf, +12699 pips, settle 12.5h
Intra_Enabled=true
Intra_StartHour=14
Intra_DurationHours=6
Intra_UseEMA=false
Intra_UseH4=true
Intra_UseCLU=true
Intra_UseLLR=false
Intra_SLMode=0               ; TIER
```

### GBPUSD
```
; Slot 1: OFFSET  ->  WR 78.0%, PF 18.78, +3791 pips, settle 5.0h
Offset_Enabled=true
Offset_StartHour=12
Offset_UseEMA=true
Offset_UseH4=true
Offset_UseCLU=false
Offset_UseLLR=true
Offset_SLMode=4              ; BE

; Slot 2: INTRADAY  ->  WR 100%, PF inf, +18126 pips, settle 8.6h
Intra_Enabled=true
Intra_StartHour=7
Intra_DurationHours=6
Intra_UseEMA=false
Intra_UseH4=false
Intra_UseCLU=true
Intra_UseLLR=false
Intra_SLMode=0               ; TIER
```

### USDCAD
```
; Slot 1: OFFSET  ->  WR 97.7%, PF 30.89, +954 pips, settle 5.0h
Offset_Enabled=true
Offset_StartHour=9
Offset_UseEMA=true
Offset_UseH4=true
Offset_UseCLU=true
Offset_UseLLR=true
Offset_SLMode=0              ; TIER

; Slot 2: INTRADAY  ->  WR 100%, PF inf, +18183 pips, settle 11.7h
Intra_Enabled=true
Intra_StartHour=14
Intra_DurationHours=4
Intra_UseEMA=false
Intra_UseH4=false
Intra_UseCLU=true
Intra_UseLLR=false
Intra_SLMode=0               ; TIER
```

### USDJPY
```
; Slot 1: OFFSET  ->  WR 75.1%, PF 62.04, +10691 pips, settle 5.2h
Offset_Enabled=true
Offset_StartHour=11
Offset_UseEMA=true
Offset_UseH4=true
Offset_UseCLU=true
Offset_UseLLR=false
Offset_SLMode=4              ; BE

; Slot 2: INTRADAY  ->  WR 100%, PF inf, +22234 pips, settle 2.8h
Intra_Enabled=true
Intra_StartHour=0
Intra_DurationHours=6
Intra_UseEMA=false
Intra_UseH4=false
Intra_UseCLU=true
Intra_UseLLR=false
Intra_SLMode=0               ; TIER
```

### USDCHF
```
; Slot 1: OFFSET  ->  WR 81.9%, PF 19.35, +7471 pips, settle 6.0h
Offset_Enabled=true
Offset_StartHour=12
Offset_UseEMA=false
Offset_UseH4=false
Offset_UseCLU=true
Offset_UseLLR=false
Offset_SLMode=4              ; BE

; Slot 2: INTRADAY  ->  WR 100%, PF inf, +13226 pips, settle 8.4h
Intra_Enabled=true
Intra_StartHour=7
Intra_DurationHours=8
Intra_UseEMA=false
Intra_UseH4=false
Intra_UseCLU=true
Intra_UseLLR=false
Intra_SLMode=0               ; TIER
```

### AUDUSD
```
; Slot 1: OFFSET  ->  WR 84.2%, PF inf, +2733 pips, settle 5.2h
Offset_Enabled=true
Offset_StartHour=12
Offset_UseEMA=true
Offset_UseH4=false
Offset_UseCLU=true
Offset_UseLLR=true
Offset_SLMode=4              ; BE

; Slot 2: INTRADAY  ->  WR 100%, PF inf, +13959 pips, settle 9.8h
Intra_Enabled=true
Intra_StartHour=13
Intra_DurationHours=4
Intra_UseEMA=false
Intra_UseH4=false
Intra_UseCLU=true
Intra_UseLLR=false
Intra_SLMode=0               ; TIER
```

### NZDUSD
```
; Slot 1: OFFSET  ->  WR 100%, PF inf, +2000 pips, settle 3.9h
Offset_Enabled=true
Offset_StartHour=10
Offset_UseEMA=true
Offset_UseH4=false
Offset_UseCLU=true
Offset_UseLLR=true
Offset_SLMode=6              ; PARTIAL

; Slot 2: INTRADAY  ->  WR 100%, PF inf, +10934 pips, settle 6.7h
Intra_Enabled=true
Intra_StartHour=5
Intra_DurationHours=8
Intra_UseEMA=false
Intra_UseH4=false
Intra_UseCLU=true
Intra_UseLLR=false
Intra_SLMode=0               ; TIER
```

### XAUUSD
```
; Slot 1: OFFSET  ->  WR 97.0%, PF 41.70, +30382 pips, settle 4.5h
Offset_Enabled=true
Offset_StartHour=11
Offset_UseEMA=true
Offset_UseH4=true
Offset_UseCLU=true
Offset_UseLLR=true
Offset_SLMode=3              ; RATIO_1_2

; Slot 2: INTRADAY  ->  WR 100%, PF inf, +35257 pips, settle 5.6h
Intra_Enabled=true
Intra_StartHour=8
Intra_DurationHours=3
Intra_UseEMA=true
Intra_UseH4=true
Intra_UseCLU=true
Intra_UseLLR=false
Intra_SLMode=3               ; RATIO_1_2
```

### BTCUSD
```
; Slot 1: OFFSET  ->  WR 84.7%, PF 6.94, +207238 pips, settle 4.2h
Offset_Enabled=true
Offset_StartHour=11
Offset_UseEMA=true
Offset_UseH4=true
Offset_UseCLU=true
Offset_UseLLR=true
Offset_SLMode=3              ; RATIO_1_2

; Slot 2: INTRADAY  ->  WR 98.6%, PF 86.83, +329239 pips, settle 2.6h
Intra_Enabled=true
Intra_StartHour=0
Intra_DurationHours=6
Intra_UseEMA=false
Intra_UseH4=true
Intra_UseCLU=true
Intra_UseLLR=true
Intra_SLMode=3               ; RATIO_1_2
```

### ETHUSD
```
; Slot 1: OFFSET  ->  WR 97.6%, PF 30.16, +5087 pips, settle 5.1h
Offset_Enabled=true
Offset_StartHour=11
Offset_UseEMA=true
Offset_UseH4=true
Offset_UseCLU=true
Offset_UseLLR=true
Offset_SLMode=2              ; RATIO_1_1_5

; Slot 2: INTRADAY  ->  WR 100%, PF inf, +11937 pips, settle 7.8h
Intra_Enabled=true
Intra_StartHour=9
Intra_DurationHours=3
Intra_UseEMA=false
Intra_UseH4=false
Intra_UseCLU=true
Intra_UseLLR=false
Intra_SLMode=3               ; RATIO_1_2
```

---

## 9. TOTAL PARAMETER SPACE

| Dimension | Values | Count |
|-----------|--------|-------|
| WindowType | OFFSET, INTRADAY | 2 |
| WindowStartHour | 0-23 | 24 |
| WindowDurationHours | 2, 3, 4, 6, 8 | 5 |
| UseEMA | true, false | 2 |
| UseH4 | true, false | 2 |
| UseCLU | true, false | 2 |
| UseLLR | true, false | 2 |
| SLMode | TIER, 1:1, 1:1.5, 1:2, BE, TRAIL, PARTIAL | 7 |
| ActivationPct | 50 (default, tunable) | 1 |
| TrailPct | 30 (default, tunable) | 1 |
| MaxHoldHours | 18 (default, tunable) | 1 |

**Tested combinations per instrument**: 34 windows × 16 filter combos × 7 SL modes = **3,808**
