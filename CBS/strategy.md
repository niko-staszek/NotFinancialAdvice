# CBS — "Can't Be Simpler"

A target-driven strategy that calculates a single daily price target from the previous period's OHLC, then trades toward or reacts at that target using Fibonacci retracement clusters, trend confirmation, and line-of-least-resistance breakouts.

The target formula (`High + Low - Open`) is an Open-substituted pivot — a Fibonacci 1.0 expansion that produces the same value regardless of bullish or bearish direction, giving one target per period that price gravitates toward.

---

## Instruments

### Forex
EURUSD, GBPUSD, USDCAD, USDJPY, USDCHF, AUDUSD, NZDUSD

### CFD
XAUUSD (Gold), XTIUSD (Oil)

### Crypto
BTCUSD, ETHUSD

---

## Timeframes

| Timeframe | Role |
|-----------|------|
| **H1** | Primary execution — entries, EMA filter, LLR breaks |
| **H4** | Trend, swings, imbalances, channels |
| **D1** | Monthly range context |
| **M5 / M15** | Signal candle confirmation after LLR break |

---

## Indicators

**EMA 21** — the only indicator. Used on:
- **H1** for the COMING strategy entry filter (price above/below EMA)
- **H4** for trend determination (price relationship to EMA defines trend)

---

## Previous Period Levels

Notation: `P(D/W/M)(O/H/L/C)` = Previous (Day / Week / Month)(Open / High / Low / Close)

Compute OHLC for the previous day, previous week, and previous month, then map them forward as reference levels on the current chart.

---

## Target Calculation

### The Formula

```
Target = High + Low - Open
```

This is a **Fibonacci expansion at the 1.0 level** applied to the previous period's OHLC:

| Direction | A | B | C | Expansion (1.0) |
|-----------|---|---|---|-----------------|
| Bullish | Open | High | Low | Low + (High - Open) = **H + L - O** |
| Bearish | Open | Low | High | High + (Low - Open) = **H + L - O** |

Both directions simplify to the same value. This means there is **one target per period** — the direction price approaches from determines whether it's a bullish or bearish setup.

### Default Period

Previous Day (00:00-24:00) → one target for the entire trading day.

### Multiple Targets via Sub-Windows

Targets can also be computed from **shorter intraday windows** (e.g., 07:00-13:00, 22:00-24:00). Each window produces its own O/H/L and therefore its own target. Different windows may have higher settle-on-day ratios than the default full-day window — a window scanner can identify which sub-periods produce the best targets per instrument and day of week.

### Settle Tolerance

How close price must get to the target for it to count as "settled":

| Instrument Type | Tolerance |
|-----------------|-----------|
| Forex | 5 pips |
| XAUUSD | 15 pips |
| XTIUSD | 15 pips |
| BTCUSD | $10 |
| ETHUSD | $5 |

---

## Fibonacci Retracement

Drawn from PDH (Previous Day High) to PDL (Previous Day Low).

**Formula:** `level_price = PDL + (PDH - PDL) x level`

### Levels

| Category | Levels |
|----------|--------|
| **Internal** (primary) | 0.382, 0.618 |
| **External** | -0.382, -0.618, 1.382, 1.618, 2.618 |

Also computed for Previous Week and Previous Month High/Low — these multi-period retracements feed into the cluster system.

---

## Swings (H4)

### Identification
1. Price moves in one direction for **at least 3 candles**
2. An opposite candle starts approximately at the close of the previous candle (the swing point)
3. Track only the **2-4 most recent swings** (roughly covering day, week, and month range)

### Swing High (SH) / Swing Low (SL)
Used for:
- **Trend determination** — higher highs + higher lows = bullish, lower highs + lower lows = bearish
- **S/R levels** — swings are obstacles between price and the target

---

## Imbalance / Fair Value Gap (H4 and H1)

### Identification
1. Three consecutive candles in one direction
2. **Bullish imbalance:** gap between the high of Candle 1 and the low of Candle 3 (wicks do not overlap)
3. **Bearish imbalance:** gap between the low of Candle 1 and the high of Candle 3
4. The gap defines the **imbalance box** — price tends to return to fill this zone

**Minimum size:** 20 pips (smaller gaps are noise, not tradeable imbalances)

---

## Clusters

Clusters form when **retracement levels from different periods** (day, week, month) land close together.

### Key Principle

Clusters are **day-level, not target-level**. The cluster map is built from retracement levels (PD/PW/PM high-low) which are the same for the entire day. They do not change based on which expansion target you're evaluating. However, when a target lands inside an existing cluster, it becomes a **Target Cluster** — a stronger level with additional confluence.

### Common Cluster Combinations

| Combo | Periods |
|-------|---------|
| 61.8% + 38.2% | Different periods (e.g., PD 61.8% near PW 38.2%) |
| 61.8% + 61.8% | Different periods |
| 61.8% + 161.8% | Different periods |
| 38.2% + 161.8% | Different periods |
| PDH/PDL + any fib | Period boundary + retracement |
| **Target + cluster** | Expansion target inside a retracement cluster = **Target Cluster** |

### Cluster Size (Maximum Distance Between Levels)

| Instrument Type | Max Distance |
|-----------------|-------------|
| Forex | 5 pips |
| Gold, Oil | 15 pips |
| BTCUSD | $10 |
| ETHUSD | $5 |

---

## Support & Resistance (Obstacles)

The following act as S/R and therefore as **obstacles** between price and the target:

1. **Clusters** — strongest when they are Target Clusters
2. **Trend channels** (H4)
3. **EMA 21** (H1 and H4)
4. **Imbalance boxes** (H4 and H1)
5. **Last 2 swings** (H4)

> Obstacle count matters: if there are **2+ obstacles** between price and the target, the path is too contested — see COMING strategy rules.

---

## Trend Determination (H4)

### Bullish
- Price is **above** EMA 21 and bounces from it
- Each new Swing High is **higher** than the previous
- Each new Swing Low is **higher** than the previous

### Bearish
- Price is **below** EMA 21 and bounces from it
- Each new Swing Low is **lower** than the previous
- Each new Swing High is **lower** than the previous

### Trend Channel
1. Connect at least 2 swing points to draw a trendline
2. Draw a parallel line on the opposite side — attach to the "biggest bump" if no clean fit exists
3. Channel boundaries act as S/R (obstacles)

---

## LLR — Line of Least Resistance (H1)

A trendline connecting **at least 2 swings** on H1. Draw from both sides (support-side LLR and resistance-side LLR).

### Trading the LLR Break
1. Price breaks through the LLR
2. Price **reacts on the other side** (confirms the break — not just a wick through)
3. Switch to **M5 or M15**
4. Wait for a **signal candle**:
   - Candle body > 60% of total range (strong conviction)
   - Closes in the direction of the break
5. Enter the trade

---

## Strategy #1 — REACTION

A limit-order strategy that trades the **bounce at the target**.

### Rules

| Parameter | Value |
|-----------|-------|
| **Order type** | BUY/SELL limit at target ± offset |
| **Offset** | 5 pips (wider if the cluster containing the target is >15 pips) |
| **Spread** | Must be factored into the limit price |
| **TP** | 15 pips in the bounce direction |
| **SL** | Risk to Reward 1:1 (but may vary on backtests)


### Escalation
If price does **not react** and moves **100+ pips past the target** → trigger Strategy #3 (AVERAGING).

---

## Strategy #2 — COMING

A trend-following strategy that trades **toward the target**.

### Entry Rules (in order)

**1. EMA 21 Filter (H1)**
- Full candle **above** EMA 21 → BUY direction only
- Full candle **below** EMA 21 → SELL direction only
- "Full candle" = entire bar (high to low) is on one side of the EMA

**2. H4 Trend Confirmation**
- Trade direction must agree with the H4 trend
- Bullish trade requires bullish H4 trend; bearish trade requires bearish H4 trend

**3. Minimum Distance**
- If less than **15 pips** to the target → do NOT open
- Effective minimum = 15 pips + spread

**4. Entry Timing**
- On H1, when the candle is clearly above/below EMA 21 (~80%+ of the bar on one side)
- Switch to M5/M15 and wait for trend confirmation before opening the order

**5. Obstacle Filter**
- Create the order **after the last obstacle** between price and target

**6. Stop Loss**
- Risk to Reward 5:1 (but may vary on backtests)

### Take Profit

**6. Cluster-Aware TP**
- If the target is inside a cluster: set TP to the **closer edge** of the cluster (minus settle tolerance)
- If the target is standalone: set TP at the target (minus settle tolerance and spread)

**7. Spread Awareness**
- Factored into entry price and settle calculation


---

## Strategy #3 — AVERAGING

A recovery strategy for underwater positions.

### All Conditions Must Be Met

| Condition | Rule |
|-----------|------|
| **Minimum depth** | SL must be **100+ pips** away (the trade is deep enough that averaging makes sense) |
| **Direction** | Price must be moving in the recovery direction |
| **EMA 21 confirmation** | BUY averaging only when price is **above** EMA 21; SELL averaging only when **below** |
| **Max exposure** | Total averaging lots ≤ **4x** the original position's lot size |

> Averaging is a **last resort**, not a primary strategy. It is only deployed when Strategy #1 (REACTION) fails to produce a bounce and price moves 100+ pips past the target.

---

## How the Three Strategies Work Together

```
Target is calculated (H + L - O)
    |
    +-- Price is approaching target
    |       |
    |       +-- COMING (#2): Trade toward target with trend
    |
    +-- Price reaches target
    |       |
    |       +-- REACTION (#1): Limit order catches the bounce
    |
    +-- Price blows past target (100+ pips)
            |
            +-- AVERAGING (#3): Recovery mode on the REACTION position
```

---

## Execution Checklist

### Before Any Trade

1. [ ] Target is calculated from previous period OHLC
2. [ ] Fibonacci retracements are drawn (PD, PW, PM)
3. [ ] Clusters are identified and mapped
4. [ ] H4 trend is determined (above/below EMA 21, swing structure)
5. [ ] Obstacles between price and target are counted (max 1 allowed for COMING)

### For COMING Entry

6. [ ] H1 candle is fully above/below EMA 21
7. [ ] Distance to target is ≥ 15 pips + spread
8. [ ] H4 trend confirms the direction
9. [ ] M5/M15 signal confirms entry timing
10. [ ] SL tier is set (A/B/C for forex; 1:1 for gold/crypto)
11. [ ] Position size matches distance-based risk tier

### For REACTION Entry

12. [ ] Limit order is placed at target ± offset
13. [ ] Spread is factored into the limit price
14. [ ] TP = 15 pips, SL = 15 pips (1:1)
15. [ ] Lot size = 0.01 per $1,000 balance
