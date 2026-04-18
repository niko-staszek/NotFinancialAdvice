# MMD — Magiczne Średnie (Magic Moving Averages)

A multi-layer cloud system created by Mariusz Maciej Drozdowski that maps higher-timeframe moving average structure onto a single chart. It provides trend direction, dynamic S/R zones, entry signals, and candle-based price levels (diamonds).

**Dual purpose:**
1. **Standalone strategy** — clouds, diamonds, ribbons, and schemas provide complete trade setups with entries, targets, and exits
2. **Indicator/filter for other strategies** — trend confirmation, S/R obstacle detection, regime classification (trending vs. consolidating), and entry timing for PAC, MRD, API, or any other system

---

## Why It Works

1. The cloud periods map directly to standard timeframes (H1, H4, D1, W1) — they capture the same institutional structure that big players use for decision-making
2. Diamonds are effectively "strength tests" — they reveal where large players probed and were rejected, creating levels the market remembers
3. The multi-layer design creates natural confluence — when several clouds align at a price level, that zone concentrates S/R from multiple timeframes

---

## Primary Timeframe

**H1** is the default. The system also works for:
- **M1 / M5** — scalping on CFDs/futures (shorter hold times, tighter targets)
- **H4** — swing trading (wider targets, fewer signals)

When using H1 for trend and M1/M5 for entries:
- Only trade M1/M5 entries **in the direction of** the H1 cloud trend
- Counter-trend scalps on M1/M5 are possible but must be closed quickly — do not hold them

---

## Knowledge Pyramid (Priority Order)

The MMD system is learned and applied top-down:

1. **Magic Clouds** — trend, S/R, regime (foundation)
2. **Cloud Crossings** — entry signals and trend shift confirmation
3. **Diamonds** — key price levels from candle patterns
4. **Ribbons** — channel boundaries and volatility envelope
5. **Schemas** — specific time-of-day and candle-based trade setups (applied last)

---

## Core Concept: What Is a Cloud?

A cloud is the **shaded area between an SMA and an EMA of the same period**.

Because the SMA reacts slower than the EMA, the gap between them forms a dynamic zone:
- When price is **above** the cloud — the cloud is support
- When price is **below** the cloud — the cloud is resistance
- When price is **inside** the cloud — it's a contested area (no clear edge)
- When price **passes through** a cloud — the cloud flips role (support becomes resistance, vice versa)

This is conceptually similar to Ichimoku's Kumo cloud, but MMD uses **multiple clouds at different speeds**, creating a multi-timeframe S/R map on a single chart.

---

## Cloud Periods

### Origin of the Numbers

The periods are **not Fibonacci-based**. They are derived from converting standard timeframes into M5 candle counts:

| Timeframe | Minutes | ÷ 5 (M5 candles) | MMD Period |
|-----------|---------|-------------------|------------|
| H1 | 60 | 12 | **12** |
| H4 | 240 | 48 | **48** |
| H12 | 720 | 144 | **144** |
| D1 | 1440 | 288 | **288** |
| D2.5 | 3600 | 720 | **720** |
| W1 | 7200 | 1440 | **1440** |
| ~MN | ~17280 | ~3456 | **3456** |

> On H1: 48 periods = 2 days, 288 = 12 days (~2.5 weeks), 1440 = 60 days (~3 months). Each cloud on a lower timeframe represents the behavior of a higher timeframe's moving average.

### Cloud Table

| Layer | Period | Color | Represents | Role |
|-------|--------|-------|------------|------|
| **MAIN** | 48 | Orange | H4 | Fast trend / consolidation detection |
| **MAIN** | 288 | Blue | D1 | Medium trend |
| **MAIN** | 1440 | Green | W1 | Slow trend — primary trend direction |
| ADDITIONAL | 12 | Red | H1 | Ultra-fast entry trigger |
| ADDITIONAL | 3456 | Purple | ~MN | Ultra-slow macro trend |
| HELPER | 144 | Light blue | H12 | Bridge between Orange and Blue |
| HELPER | 720 | Light green | D2.5 | Bridge between Blue and Green |
| DELAYED | 12 shifted back 144 bars | — | Lagging H1 | "2nd wave" — lagging confirmation signal |

> The same period set works across all chart timeframes. On M5 the numbers above apply directly. On H1, period 48 = 48 hours (2 days), period 288 = 288 hours (12 days), etc.

---

## Trend Reading

The vertical stacking order of the **three main clouds** (Orange 48, Blue 288, Green 1440) from top to bottom on the chart tells you the market state:

| Stacking (top → bottom) | Market State |
|--------------------------|--------------|
| Orange, Blue, Green | **Bullish trend** — fast above slow, all aligned |
| Green, Blue, Orange | **Bearish trend** — slow above fast, all aligned |
| Blue, Orange, Green | **Correction in bullish trend** — Orange dipped below Blue, but Green still at the bottom = macro still bullish |
| Green, Orange, Blue | **Correction in bearish trend** — Orange popped above Blue, but Green still on top = macro still bearish |

### Directional Reads

| Condition | Meaning |
|-----------|---------|
| Orange above Blue | Short-term momentum is **up** — direction favors higher highs |
| Blue above Orange | Short-term momentum is **down** — direction favors lower lows |
| Orange consolidating near Blue (not yet crossing) | Orange is signaling **consolidation**. Once Orange crosses Blue → correction has begun |

### Cloud Interaction with Trend

- **Green (1440)** defines the macro trend
- **Blue (288)** confirms the trend and shows medium-term momentum
- **Orange (48)** is the fast read — it shows consolidation before crossing Blue and correction after crossing

---

## Cloud Behavior Rules

1. **Clouds are S/R zones** — price reacts to cloud boundaries (bounces, stalls, reversals)
2. **Clouds are tested before reversals** — before changing direction, price will probe into a cloud to test whether the S/R holds
3. **Break-and-retest** — if price passes through a cloud, it tends to continue to the **next cloud** and then **retest the one it just broke**
4. **Volume confirms** — cloud reactions gain conviction when accompanied by above-average volume

### As an Indicator for Other Strategies

- If a trade target from another strategy (PAC, MRD, API) sits **behind** a cloud, the cloud is an **obstacle** — the target is less likely to be reached without a cloud break first
- If a target **aligns with** a cloud boundary, that's a **confluence zone** — higher probability
- Cloud stacking tells you whether your trade direction aligns with the broader trend — trading against the cloud stack requires extra conviction

---

## Important Crossings

Cloud-to-cloud and price-to-cloud crossings signal trade setups of increasing significance:

| Crossing | Significance | How to Use |
|----------|-------------|------------|
| **Price through Red (12)** | Minor — often at double tops/bottoms | The crossing point becomes the new local extreme |
| **Red (12) through Orange (48)** | Entry signal | Fast momentum shift — look for entries in the cross direction |
| **Orange (48) through Blue (288)** | Strong entry signal | Medium-term trend shift — higher-conviction entries |
| **Blue (288) through Green (1440)** | Trend rotation confirmed | Major direction change — repositioning signal |

### Post-Crossing Behavior

After crossings 2 (Red/Orange) and 3 (Orange/Blue):
- Price often **retests** the cloud it just broke — expect a ~10-15 pip reaction at the retest
- This retest is tradeable on its own (as a standalone MMD play) and serves as an entry timing signal for other strategies

---

## Entry Method: "Na Maćka" (The Maćko Entry)

The signature MMD entry setup:

### Setup
1. The **Red (12) cloud crosses through the Orange (48) cloud**
2. After the cross, price pulls back and **retests the Orange cloud**
3. The retest of the Orange cloud is the **entry point**
4. Direction is determined by the cross: Red crossing **above** Orange → long, Red crossing **below** Orange → short

### Confirmation with Accumulation / Distribution

The "Na Maćka" entry can be combined with Wyckoff-style accumulation and distribution patterns for additional confirmation:

**Accumulation (before a long entry):**

| Phase | Price Action |
|-------|-------------|
| PS (Preliminary Support) | Price drops to a lower level — first significant buying appears |
| SC (Selling Climax) | Panic selling exhausts — approximate bottom of range |
| AR (Automatic Rally) | Sharp bounce off the low — sets upper boundary of range |
| ST (Secondary Test) | Price revisits the SC area on lower volume — testing if selling is done |
| Spring (Shakeout) | Brief dip **below** the range to trap sellers and trigger stops — the key manipulation event |
| SOS (Sign of Strength) | Strong rally on expanding volume — demand has taken control |
| LPS (Last Point of Support) | Pullback after SOS on declining volume — higher low vs. the Spring |
| BU (Back-Up) | Final pullback to the top of the range (now support) — markup begins |

> **Best entry:** At the **Spring** (tightest stop, best R:R) or at the **LPS** after the SOS (more confirmation, slightly worse R:R).

**Distribution (before a short entry):**

| Phase | Price Action |
|-------|-------------|
| PSY (Preliminary Supply) | First notable selling after an uptrend |
| BC (Buying Climax) | Climactic buying on heavy volume — sets upper boundary |
| AR (Automatic Reaction) | Selloff after BC — sets lower boundary |
| SOW (Sign of Weakness) | Drop to or below the AR low on increasing volume |
| LPSY (Last Point of Supply) | Weak rally on low volume — lower high within the range |
| UTAD (Upthrust After Distribution) | False breakout above the range to trap buyers — mirror of the Spring |

> **Best entry:** At the **UTAD** (tightest stop above the false breakout) or at the **LPSY** after the SOW.

In both cases, **volume divergence** is the key confirmation: climactic volume at extremes followed by declining volume on tests.

---

## Diamonds

Diamonds are specific **candle patterns** (not the classical chart pattern) that create horizontal price levels. They reveal where large players tested strength and were rejected.

### Types

**Common Diamond:**
- At least 2 candles of the same color on each side
- The center candle is in the **opposite direction** to its neighbors
- Usually has wicks in both directions (indecision + rejection)
- Pattern: e.g., 2 Red → 1 Green → 2 Red (bearish diamond) or 2 Green → 1 Red → 2 Green (bullish diamond)

**Reverse Diamond:**
- Not a single center candle but a **pair of opposite candles** in the center
- Wrapped by the same neighbor conditions as a Common Diamond
- Take the Open and Close from the "central" candle pair to define the zone

**Cross Diamond (Doji):**
- After a directional move, a **Doji candle** appears
- If price moves away from the Doji and later **retests** it, the subsequent move will be deeper than the initial one
- Volume confirmation strengthens the signal

**Gap Diamond (Zbyszek's Diamond):**
- A large gap between candle bodies (measured body-to-body, not wick-to-wick)
- Has its own **50% level** between the bodies
- If the 50% level is visually clean and prominent, it becomes a strong retest target
- Best on H1 or H4

### Diamond Zone

The zone is defined by the **Open and Close** of the diamond candle(s).

- The **50% midpoint** of the zone is the most important level — price frequently retests it
- If price breaks through a diamond zone, previous resistance becomes support (and vice versa)
- Diamonds from **higher timeframes** can be traded on lower timeframes (e.g., H4 diamond levels traded on M5)

### Diamond Detection Logic

Detection must focus on the **relationship with neighboring candles** (2+ candles on each side in the opposite direction), not on wick/body ratio thresholds of the diamond candle itself. The context pattern defines the diamond — not the candle internals.

### Current Implementation Status (Pine)

The reference Pine implementation (`pine/mmd_clouds.pine`) currently detects **Common Diamonds only**, with `N` candles of the same direction before and after an opposite-direction centre (`N` configurable 2–4). The wick requirement is **not enforced** in code — any body-direction pattern matching the neighbour rule fires a diamond, regardless of wick shape.

Not yet implemented (tracked for future work):

- **Reverse Diamond** — two-candle opposite centre
- **Cross Diamond** — Doji centre with subsequent retest
- **Gap Diamond** — body-to-body gap with its own 50% level

The Python port should match Pine's Common-Diamond detection first, then add the other three variants as separate detectors.

---

## Ribbons

Ribbons are the **Blue (288) cloud displaced vertically**, creating a price channel similar to Envelopes.

### Formula

A single `ribbon_width` is computed once and added to / subtracted from both the SMA(288) and EMA(288) baselines:

```
ribbon_width = SMA(288) × multiplier        # Fixed %
ribbon_width = ATR(288) × multiplier        # ATR-based

Upper SMA boundary = SMA(288) + ribbon_width
Lower SMA boundary = SMA(288) - ribbon_width
Upper EMA boundary = EMA(288) + ribbon_width
Lower EMA boundary = EMA(288) - ribbon_width
```

Two modes are supported:

- **Fixed %** — width is a constant fraction of price (`SMA(288) × mult`). Multiplier scales with pip-level price moves; typical default is **`0.00144`** for EURUSD (≈17 pips at 1.17 spot). The value `0.00144` comes from the cloud period 144 reinterpreted as a pip-scale fraction, not a percentage (earlier docs stating "144 → 0.144" were off by 100× and would yield absurd widths on FX).
- **ATR-based** (recommended) — width is `ATR(288) × ATR_multiplier`. Auto-scales with realised volatility, so the same multiplier carries across instruments. Typical default is `2.0`.

The multiplier **must be calibrated per instrument** — what works for EURUSD may not work for XAUUSD. ATR mode reduces but does not eliminate this need.

> Only use the ribbon calculation on the **timeframe it was computed for** — do not apply H1 ribbon values to M5 charts.

### How to Use

- Price tends to **bounce between the Blue cloud and the upper/lower ribbon boundary** — this creates a tradeable channel
- In **consolidating markets**, the "halves" of the top and bottom ribbons (midpoints between Blue cloud and ribbon edge) also act as bounce levels — a tighter inner channel
- **Narrow ribbons** = low volatility = smaller moves, ranging environment
- **Wide ribbons** = high volatility = larger moves, trending environment

### As an Indicator

- A trade target from another strategy landing at or near a ribbon boundary is a **confluence zone**
- Ribbon width indicates regime: narrow = consolidation (favors mean-reversion strategies like API Box), wide = trend (favors directional strategies like PAC)

---

## Schemas (Trading Setups)

Specific time-of-day and candle-based setups. These are **discrete plays, not full strategies** — they can be traded standalone or used as entry timing signals within other strategies.

### Wick Schema

**When:** During candle formation (H1, H4, or non-standard intervals like M16)

**How:**
1. Note the **open price** of the current forming candle
2. If price moves **away** from the open, pyramid limit orders in the **opposite direction**:
   - First orders: 4, 8, 12 pips from open
   - If it goes deeper: 20, 40 pips from open
3. **Target:** The open price — statistically, price retests the open level (may take the current candle or the next few)
4. Observe candle formation, nearby cloud levels as S/R, and volume

**Trend consideration:**
- Always check the cloud stacking for trend direction
- If the trend favors your position (you're fading into the trend direction), **hold longer** — don't close at the open level
- If the trend is against your position, **close at the open level** or sooner

### C/O Schema (Close/Open)

**When:** After a candle closes (H1)

**How:** Trade toward the **open level** of the just-closed candle. The premise is the same as the Wick Schema — price tends to retest the open — but the entry happens after the candle is complete, not during formation.

### 228 Schema

**When:** M1 timeframe at specific times

| Instrument | Time (GMT+1) | TP |
|------------|-------------|-----|
| USDJPY | 20:59 | 4 pips below close |
| GBPUSD | 19:59 | 8 pips below close |

**How:**
1. Take the last M1 candle at the specified time
2. Trade **against** the direction of that candle
3. Pyramid sell limits: 4, 8, 12 pips above the close
4. The setup works because the market **consolidates** during these hours

**Filters:**
- Confirm with clouds and volume — determine how many orders to open
- **No Doji candles** — skip if the trigger candle is a Doji
- If the market has tested a cloud and is moving toward the 228 schema candle, the TP at 4 pips below close (USDJPY) is well-supported

### Evening Setups (GMT+1)

| Setup | Time | Instruments | Schema |
|-------|------|-------------|--------|
| **"-3k"** | 20:00 - 21:00 | USDJPY, GBPUSD | Wick Schema only |
| **"-3"** | 21:00 - 22:00 | USDJPY, GBPUSD | C/O Schema only |
| **228** | As above | USDJPY, GBPUSD | 228 Schema |

### Morning Setups

| Setup | Schema |
|-------|--------|
| **"6k"** | Wick Schema |
| **"6"** | C/O Schema |

> All schemas are **setups, not strategies**. They define specific entries at specific times. Context from clouds, volume, and other PAC/MRD/API tools determines whether the setup is worth taking.

---

## Using MMD as an Indicator for Other Strategies

| MMD Component | What It Provides | Use In Other Strategies |
|---------------|-----------------|------------------------|
| Cloud stacking (trend) | Macro trend direction | Confirm trade direction aligns with trend (PAC, MRD) |
| Cloud S/R zones | Dynamic support/resistance | Identify obstacles between price and target |
| Cloud + target overlap | Confluence | Higher probability when target aligns with cloud boundary |
| Red/Orange crossing | Momentum shift timing | Entry timing signal |
| Post-crossing retest | ~10-15 pip reaction | Standalone quick play or entry timing |
| Diamond zones | Horizontal S/R levels | Confluence with Fibonacci clusters, battle zones |
| Diamond 50% level | High-probability retest level | Target validation |
| Ribbons (width) | Volatility regime | Regime filter — consolidation vs. trend |
| Ribbon boundaries | Channel S/R | Confluence with targets, obstacle detection |
| Time-of-day schemas | Session behavior patterns | Entry timing features |
| Volume confirmation | Signal strength | All MMD signals strengthen with volume |

---

## Open Questions

1. **Ribbon multipliers** — need calibration per instrument through testing (e.g., 0.144 works for EURUSD, but XAUUSD may need a different value)
2. **Cloud periods on different TFs** — should clouds be computed on H1 only, or should H4/D1 cloud readings be overlaid? Needs experimentation
3. **Delayed cloud (12 shifted 144 bars)** — expected to serve as a lagging confirmation signal ("2nd wave"). Needs validation through backtesting
4. **Schema integration** — Wick, C/O, 228, evening/morning setups are currently **manual plays**. Future roadmap: automate as part of a multi-strategy trading bot
5. **Diamond detection edge cases** — Reverse Diamonds and Gap Diamonds need precise detection rules. Inner Diamonds (within cloud zones) may be more reliable than Swing Diamonds (at swing points) — needs statistical validation
