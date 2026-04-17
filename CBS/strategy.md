# CBS — "Can't Be Simpler" (PSND)

A target-driven strategy built around a single daily price target derived from the previous period's OHLC. All three sub-strategies — Reaction, Coming, and Averaging — orbit this target. The strategy's core claim: the formula `High + Low - Open` produces a level that price gravitates toward and reacts at, with approximately 70% same-day settlement rate on default settings — and up to 90–93% on optimised time windows.

---

## Instruments

| Category | Symbols |
|----------|---------|
| Forex (major) | EURUSD, GBPUSD, USDCAD, USDJPY, USDCHF, AUDUSD, NZDUSD |
| Commodities | XAUUSD (Gold), XTIUSD (Oil) |
| Crypto | BTCUSD, ETHUSD |

All are USD-paired because USD pairs carry the lowest spread — spread minimisation is explicitly part of the entry cost calculation.

---

## Timeframes

| Timeframe | Role |
|-----------|------|
| **H1** | Primary execution: entries, EMA21 filter, target drawing, NLO identification |
| **H4** | Trend, swing structure, imbalances, trend channels |
| **D1** | Previous month context |
| **M5 / M15** | Signal candle confirmation after NLO break; low-TF reaction verification |

---

## The Only Indicator

**EMA 21 (Exponential Moving Average, period 21)**

- **H1**: Entry direction filter — price must be fully above EMA21 for longs, fully below for shorts ("full candle" = entire high-to-low range on one side)
- **H4**: Trend determination — price relationship to EMA21 defines the macro bias

EMA21 is also a structural obstacle (see Obstacles section).

---

## Previous Period Levels

Notation: `P(D/W/M)(H/L/O/C)` = Previous (Day/Week/Month)(High/Low/Open/Close)

Draw horizontal lines for:
- PDH, PDL — previous day high/low (update daily)
- PWH, PWL — previous week high/low (update weekly)
- PMH, PML — previous month high/low (update monthly)

**How to read them by timeframe:**
- **H1** → identifies PDH/PDL (separator shows yesterday's session)
- **H4** → identifies PWH/PWL (separator shows previous week)
- **D1** → identifies PMH/PML (separator shows previous month)

Opening candle wicks count — the first candle of each period may have its open coincide with the period's extreme.

---

## Target Calculation

### Formula

```
Target = High + Low - Open
```

This is a **Fibonacci 1.0 expansion** on the previous period's OHLC:

| Direction | A | B | C | Expansion (1.0) |
|-----------|---|---|---|-----------------|
| Bullish | Open | High | Low | Low + (High − Open) = **H + L − O** |
| Bearish | Open | Low | High | High + (Low − Open) = **H + L − O** |

Both directions resolve to the same value — **one target per period**, direction-agnostic. Which side price approaches from determines whether the trade is long or short.

### Default Period

Previous day (00:00–23:59) → one target valid for the entire trading day.

Open for bullish candle = bottom of body. Open for bearish candle = top of body. High and Low = wicks.

### Custom Time Windows

The All-in Panel allows specifying custom `Start Hour → End Hour → Check Time` windows. Each window produces its own O/H/L and therefore its own target. Use the panel's **statistics button** to find windows with the highest "closed the same day" percentage per instrument.

**Threshold guidelines:**

| Same-day rate | Interpretation |
|---------------|----------------|
| < 80% | Not worth the edge — use default daily target instead |
| 80–85% | Acceptable edge |
| 85–93% | Strong edge — prioritise these targets |
| > 93% | Exceptional — highest conviction trades |

Standard windows tested: 00:00–23:59 (default, ~70%), 02:00–09:00 (often 85–95% on forex majors). Run your own scan for each instrument.

### Settle Tolerance

How close price must come to the target for it to count as "settled" (reacted):

| Instrument | Tolerance |
|------------|-----------|
| Forex | 5 pips |
| XAUUSD, XTIUSD | 15 pips |
| BTCUSD | $10 |
| ETHUSD | $5 |

A target that was touched within tolerance by the opening candle of the day is **already settled** — do not trade it.

---

## Fibonacci Levels

Drawn from PDH → PDL, PWH → PWL, PMH → PML (separately).

**Formula:** `level = Low + (High − Low) × ratio`

| Type | Levels | Notes |
|------|--------|-------|
| Internal | 0.382, 0.618 | Primary. The 0.5 level is explicitly de-emphasised ("not needed at this stage") |
| External | 1.382, 1.618, 2.618 | Extended targets and cluster partners |
| Negative | −0.382, −0.618 | Mirror of external on the opposite side; mathematically identical placement |

> Note: entering point A at bottom vs. top changes the sign but not the price level — the same zone appears whether marked as −38.2% or +138.2% depending on tool orientation.

---

## Swings (H4)

### Identification Rules
1. Price moves in one direction for **at least 3 consecutive candles**
2. A candle in the opposite direction appears, opening approximately at the prior candle's close
3. Mark the swing at the **highest wick** (swing high) or **lowest wick** (swing low) of the reversal point — not at the body
4. Keep only the **2–4 most recent swings** (covering approximately day/week/month range)

### Swing High / Swing Low
- **Trend reading**: higher highs + higher lows = bullish; lower highs + lower lows = bearish
- **Obstacles**: active swings sit between price and the target as resistance/support levels to respect

---

## Imbalance / Fair Value Gap (H4 and H1)

### Identification
Three consecutive candles in one direction:

**Bullish imbalance:** C1 high wick < C3 low wick (gap between them, no overlap)
**Bearish imbalance:** C1 low wick > C3 high wick (gap between them, no overlap)

**Minimum size: 20 pips.** Anything smaller is noise.

The imbalance box is the zone between C1's extreme wick and C3's extreme wick. Price tends to return to fill this zone.

Used primarily from **H4 and H1**. Smaller imbalances on H1 are valid; H4 imbalances carry more weight.

---

## Clusters

Clusters form when Fibonacci retracement levels from **different periods** (day, week, month) land close enough together to define a single zone.

### Rules
- **Same period, same direction is not a cluster** — you must have levels from at least two different measurement windows (e.g., PDH/PDL + PWH/PWL, or PDH/PDL + PMH/PML)
- Measurement must be symmetric: PDH to PDL, not PDH to PWL
- The cluster map is **day-level** — retracement levels don't change intraday; only the daily target changes

### Maximum cluster width (distance between constituent levels)

| Instrument | Max width |
|------------|-----------|
| Forex | 5 pips |
| XTIUSD (Oil) | 10 pips |
| XAUUSD (Gold) | 15 pips |

### Highest-priority cluster combinations

| Combination | Type |
|-------------|------|
| 38.2% + 61.8% | Different periods (e.g., PD 38.2 + PW 61.8) |
| 61.8% + 61.8% | Different periods |
| 61.8% + 161.8% | Different periods |
| 38.2% + 161.8% | Different periods |
| PDH/PDL + any fib | Period boundary + retracement |
| **Target inside cluster** | **Target Cluster — strongest setup** |

Avoid clusters built on 50% levels — explicitly de-emphasised.

### Cluster behaviour
- **Cluster below price**: acts as support — strengthens a Coming (approach) long scenario
- **Cluster above price**: acts as resistance — potential obstacle for an upward Coming trade; also a Reaction TP target
- **Cluster at target level**: Target Cluster — highest-confidence reaction zone; both attracts price and expects a reversal

---

## Trend Determination (H4)

### Bullish trend (all three preferred)
1. Price **above** EMA21 and bouncing from it
2. Each new swing high is **higher** than the previous (higher highs)
3. Each new swing low is **higher** than the previous (higher lows)

### Bearish trend (all three preferred)
1. Price **below** EMA21 and bouncing from it
2. Each new swing low is **lower** than the previous (lower lows)
3. Each new swing high is **lower** than the previous (lower highs)

### Trend Channel (H4)
1. Connect at least **2 swing points** on one side to draw a trendline
2. Draw a **parallel line** on the opposite side — attach it to the "biggest bump" if no clean second touch exists
3. Ideally 2–3 touch points on each side for confirmation
4. Channel boundaries act as S/R obstacles

---

## Support & Resistance — Obstacles

The following act as obstacles between price and the target (ranked approximately by significance):

1. **Clusters** — especially Target Clusters
2. **Trend channels** (H4) — channel walls
3. **EMA 21** (H1 and H4)
4. **Imbalance boxes** (H4 and H1)
5. **Last 2 swings** (H4)
6. **PDH / PDL / PWH / PWL / PMH / PML** — period boundaries

> **Critical rule for Coming strategy**: if there are **2 or more obstacles** between current price and the target, the path is too contested — skip the trade.

---

## NLO — Line of Least Resistance

A trendline connecting **at least 2 swing wicks** on H1 (occasionally H4). Draw from both sides (support-side NLO and resistance-side NLO). Constructed from wicks, not bodies.

### Why it matters
NLO is a daily decision-making tool. Ignoring it means entering trades that immediately stall or reverse at invisible structure.

### Entry procedure after NLO break
1. Price **closes** through the NLO (wick-through does not count — wait for candle close)
2. Price **retraces back** to the NLO and reacts from the other side (the broken resistance becomes support, or vice versa)
3. Drop to **M5 or M15**
4. Wait for a **signal candle**: body > ~60% of total range, closing in the breakout direction
5. Enter

### NLO from different sides
- **Resistance-side NLO** break → confirmation for upward move → long entry toward target above
- **Support-side NLO** break → confirmation for downward move → short entry toward target below

### Validity
NLO with 2 swings = minimum valid. 3+ touch points = high-confidence. Assess visually — if it isn't obvious at a normal zoom level, the line is too subjective to trade.

---

## Strategy #1 — Reaction

Trade the **bounce at the target**. Price arrives at the target; you collect a short reaction in the opposite direction.

### Entry

| Parameter | Value |
|-----------|-------|
| Order type | Limit order (BUY LIMIT below price / SELL LIMIT above price) |
| Entry offset | 5 pips from target (plus spread) |
| Direction | BUY LIMIT if target is below current price; SELL LIMIT if target is above |

### Basic version (TP/SL)

| Parameter | Value |
|-----------|-------|
| Take profit | **5 pips** from entry |
| Stop loss | **5 pips** (1:1 R:R) |
| Lot size | 0.01 per $1,000 balance |

### Pro version

When a cluster exists **within ~15 pips** of the target:

| Parameter | Rule |
|-----------|------|
| Take profit | Closer edge of the cluster (minus settle tolerance and spread) |
| Stop loss | Adjusted proportionally to maintain reasonable R:R |
| Preferred cluster types | 38.2+61.8, 61.8+61.8, 61.8+161.8 from different periods — not 50% |

If no cluster within 15 pips, keep the basic 5-pip TP.

### How to verify a reaction on H1

If the H1 candle body is ambiguous (reaction not visible), **drop to M5**. The reaction will show as a clear rejection candle (wick into target zone, body closing away). This is a valid setup — the H1 candle simply compressed the M5 detail.

### Escalation rule

If price does **not react** and moves **100+ pips past the target** → evaluate Strategy #3 (Averaging).

---

## Strategy #2 — Coming

Trade **toward the target**. Price is away from the target; you enter in the direction of the target and hold until it arrives.

### Entry conditions (all must be met)

**1. EMA21 filter (H1)**
- Full candle body above EMA21 → BUY only
- Full candle body below EMA21 → SELL only
- "Full" = entire candle (high to low) on one side — ~80%+ of the bar past EMA21

**2. H4 trend confirmation**
- Long trade: H4 trend is bullish (price above EMA21, higher highs + higher lows)
- Short trade: H4 trend is bearish (price below EMA21, lower highs + lower lows)

**3. Minimum distance to target**
- Must be ≥ **15 pips** remaining to the target (Paweł's personal threshold: 20 pips)
- Effective minimum = 15 pips + spread
- Opening candle touching the target disqualifies it

**4. Obstacle count**
- Maximum **1 obstacle** between price and target
- 2+ obstacles → skip the trade

**5. NLO confirmation**
- Ideally enter after price has broken the relevant NLO and reacted from the correct side
- Signal candle on M5/M15 confirms the entry timing

**6. Order type**
- Use a **pending stop order** (SELL STOP below price / BUY STOP above price) triggered when price moves into position
- Do not enter at a swing (obstacle) — wait for the break

### Take Profit

| Condition | TP placement |
|-----------|-------------|
| Cluster within reach before target | TP at the **near edge** of the cluster (minus settle tolerance + spread) |
| No cluster in path | TP at the target (minus settle tolerance + spread) |

Prefer the cluster TP over the raw target TP — clusters are where reversals happen and price may not reach the final target.

### Trailing Stop

**Activate the trailing stop when price has covered 50% of the distance from entry to TP.**

This rule is non-negotiable. At the midpoint, you move the stop to break-even (or activate the platform's trailing stop). If price reverses from there, you exit at worst flat. The trailing stop only functions while the MT4/MT5 platform is running — closing the platform disables it.

### Stop Loss

Initial SL: capital-based approach (see Money Management). Adjusted closer after confirming H4 swing structure and based on personal stats after 150+ setups.

---

## Strategy #3 — Averaging

Recovery strategy for positions that went against the scenario. **Not a primary strategy — last resort only.**

### All conditions required

| Condition | Rule |
|-----------|------|
| Minimum adverse move | Price has moved **100+ pips** against the original entry |
| Structure change | Price has crossed back over EMA21 in the recovery direction |
| EMA21 reaction | Price has **reacted** from the correct side of EMA21 (it acted as support/resistance) |
| Platform requirement | MT4/MT5 must be running throughout |

### Averaging mechanics

1. Original position: 0.01 lots, open at a loss
2. Add averaging position: **2x the original** (0.02 lots) after the above conditions are met
3. Maximum multiplier: **4x original** (0.04 lots) — only when you have high conviction the recovery direction is locked in
4. The averaging entry is a **market order** at a better price than the original, entered after EMA21 reaction confirmation

### Goal

Break even or minimal loss — not profit. The combined setup (original + averaging positions) must close within the **5% capital stop loss budget**.

| Position | P&L example |
|----------|------------|
| Original (0.01) | −$10 |
| Averaging (0.02) | +$9 |
| **Net** | **−$1** (vs −$10 from original alone) |

The 2x multiplier shrinks the required recovery distance roughly in half. The 4x multiplier shrinks it further but doubles the loss if the recovery fails.

**Hard limit**: Total averaging lots ≤ **4× original position size**.

---

## Money Management

### Starting parameters (mandatory for first 150 setups)

| Parameter | Value |
|-----------|-------|
| Lot size | 0.01 per $1,000 account balance |
| Capital risk | 5% per trade ($50 on $1,000) |
| Pip distance to stop loss | ~500 pips (forex) |

The 500-pip SL isn't about expecting that loss — it's about giving the position room to breathe while you learn. On most forex majors the 500-pip threshold is almost never hit by a properly managed Reaction trade. Gold is an exception: with 1,000+ pip daily ranges, apply a tighter position size or avoid until experienced.

### Why capital management (not risk:reward) at this stage

The R:R approach requires statistical baseline data. You build that baseline first through 150+ setups on the capital-management system. After 150 setups you can measure your real maximum adverse excursion per instrument and tighten the SL/lot size intelligently.

### Adjusting after experience

Only change MM parameters when:
1. 150+ setups completed
2. Statistical records show real maximum drawdown per instrument
3. You can demonstrate the adjusted parameters fit within the 5% risk budget

### Gold note

Gold's daily volatility (currently 1,000–2,000 pip ranges) makes the standard 0.01/1,000 rule inadequate as-is. Beginners should avoid gold until completing the 150-setup baseline on forex majors.

---

## How the Three Strategies Work Together

```
Target calculated (H + L − O from previous day or custom window)
    │
    ├── Price is far from target (>15 pips)
    │       │
    │       └── COMING (#2): Trend-following entry toward the target
    │                         Trailing stop at 50% of journey
    │                         TP at nearest cluster or target
    │
    ├── Price reaches the target zone
    │       │
    │       └── REACTION (#1): Limit order at target ± 5 pip offset
    │                           TP = 5 pips (basic) or cluster edge (pro)
    │
    └── Price blows past target by 100+ pips
            │
            └── AVERAGING (#3): Add position after EMA21 structure change
                                 Goal = break even, not profit
```

---

## Execution Checklist

### Daily setup (before session)
- [ ] Draw PDH, PDL (H1 separator)
- [ ] Draw PWH, PWL (H4 separator)
- [ ] Draw PMH, PML (D1 separator)
- [ ] Compute and plot PSND target(s) — default + any high-stat custom windows
- [ ] Draw Fib retracements: PD, PW, PM high-to-low
- [ ] Identify clusters (≤5 pips forex / ≤10 pips oil / ≤15 pips gold) — flag Target Clusters
- [ ] Check for imbalances ≥20 pips on H4 and H1
- [ ] Update swing structure on H4 (last 2–4 swings)
- [ ] Draw/update trend channel on H4
- [ ] Note EMA21 position on H1 and H4
- [ ] Identify and draw NLO lines from H1 swings (both sides)

### Before any entry

**Reaction:**
- [ ] Target has not been touched by the opening candle today
- [ ] Limit order placed at target ± offset (spread factored in)
- [ ] TP set: 5 pips basic, or cluster edge (pro)
- [ ] SL set: 5 pips (basic), or adjust for pro
- [ ] Lot size = 0.01 per $1,000

**Coming:**
- [ ] H1 candle fully above/below EMA21
- [ ] H4 trend confirms direction
- [ ] Distance to target ≥ 15 pips (+ spread)
- [ ] At most 1 obstacle between price and target
- [ ] NLO has been broken; price reacted from correct side
- [ ] Signal candle on M5/M15 confirms timing
- [ ] Trailing stop reminder set (activate at 50% of range)
- [ ] TP set at cluster or target (minus tolerance)

**Averaging:**
- [ ] Position is 100+ pips adverse
- [ ] Price has crossed back over EMA21
- [ ] Price has reacted from EMA21 (support/resistance confirmed)
- [ ] New position size ≤ 2× original (or up to 4× with high conviction)
- [ ] Combined loss if both positions stopped = still within 5% capital budget

---

## Practice Recommendation

Use **FX Blue Trading Simulator** (fxblue.com → Tools → Simulator) to replay market days you missed. Install as an MT4/MT5 expert, set date range, and simulate candle-by-candle. Target: analyse 3–5 instruments per session, mark targets, execute scenarios, record outcomes. Minimum 150 full setups before adjusting any parameters.
