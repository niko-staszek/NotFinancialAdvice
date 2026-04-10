# MMD Clouds — Reference & Analysis

Claude's understanding of the MMD system. Niko corrects when wrong.

---

## Core Concept

A "cloud" is the space between an SMA and EMA of the **same period**. Because SMA reacts slower than EMA, the gap between them forms a dynamic zone that acts as support/resistance. When price enters a cloud, it's in a contested area. When it passes through, the cloud flips from support to resistance (or vice versa).

This is similar to Ichimoku's Kumo cloud but with multiple layers at different speeds, giving you a multi-timeframe trend and S/R map from a single chart.

---

## Cloud Levels

Each cloud is defined by its period (applied to both SMA and EMA):

| Layer | Period | Color | Role |
|-------|--------|-------|------|
| **MAIN** | 48 | Orange | Fast trend / consolidation detection |
| **MAIN** | 288 | Blue | Medium trend |
| **MAIN** | 1440 | Green | Slow trend (D1 equivalent on H1) |
| ADDITIONAL | 12 | Red | Ultra-fast, entry trigger |
| ADDITIONAL | 3456 | Purple | Ultra-slow, macro trend |
| HELPER | 144 | Light blue | Between orange and blue |
| HELPER | 720 | Light green | Between blue and green |
| DELAYED | 12 shifted back 144 bars | — | "2nd wave" — lagging confirmation |

**Period logic on H1:** 48 = 2 days, 288 = 12 days (~2.5 weeks), 1440 = 60 days (~3 months). So on H1 the three main clouds roughly represent intra-week, multi-week, and quarterly trend. The same periods work on other timeframes — on M1, 48 would be ~48 minutes, 288 ~5 hours, etc.

---

## Trend Reading

The vertical stacking order of the three main clouds tells you the market state:

**Bullish trend** — top to bottom: Orange, Blue, Green (fast above slow)

**Bearish trend** — top to bottom: Green, Blue, Orange (slow above fast)

**Correction in bullish trend** — Blue, Orange, Green (orange dips below blue but green still underneath = still bullish macro, just correcting)

**Correction in bearish trend** — Green, Orange, Blue (orange pops above blue but green still on top = still bearish macro, just correcting)

**Direction for highs** — Orange above Blue (short-term momentum up)

**Direction for lows** — Blue above Orange (short-term momentum down)

---

## Cloud Behavior Rules

1. Clouds are S/R zones — price reacts to them.
2. Before reversing direction, price will "test" the clouds.
3. If price passes through a cloud, it tends to continue to the next cloud and then retest the one it just broke.
4. Cloud reactions can be confirmed with volume (and other tools).

**For CBS:** This means if a CBS target sits behind a cloud, the cloud is an obstacle. If the target aligns with a cloud boundary, that's a confluence zone — higher probability. The cloud stacking tells us whether the CBS trade direction aligns with the broader trend.

---

## Important Crossings

Crossings between clouds/price signal trade setups:

1. **Price through Red (12)** — often happens at double tops/bottoms; the crossing point becomes the new extreme.
2. **Red (12) through Orange (48)** — entry signal. Fast momentum shift.
3. **Orange (48) through Blue (288)** — stronger entry signal. Medium-term trend shift.
4. **Blue (288) through Green (1440)** — trend rotation confirmed. Major direction change.

On crossings 2 and 3: after the cross, price often retests the cloud (~10–15 pip reaction). This is playable on its own but also valuable as a CBS entry timing signal.

---

## Diamonds

Special candle patterns that create key price levels.

### Types

**Common Diamond:** A candle in the opposite direction to its neighbors — at least 2 candles the same direction on each side, with the diamond candle going against them. Usually has wicks in both directions (indecision + rejection).

**Reverse Diamond:** Not a single candle but a pair of opposite candles in the center, wrapped by the same conditions as a common diamond. Take the open and close from the "central" candle pair.

**Cross Diamond (Doji):** After a move, a Doji candle appears. If price then moves away from the Doji and retests it, the subsequent move will be deeper. Volume confirmation adds strength.

**Gap Diamond (Zbyszek's Diamond):** Large gap between candle bodies. Has its own 50% level. If that 50% is visually prominent (clean level), it's a strong retest target. On H1 or H4.

### Diamond Zone

Defined by the Open and Close of the diamond candle, with the **50% midpoint** being the most important level — price frequently retests it.

If price breaks through a diamond zone, previous resistance becomes support (and vice versa). Diamonds from higher timeframes can be traded on lower timeframes.

**For CBS:** Diamond zones are S/R levels. A CBS target landing on a diamond zone (especially the 50% level) has additional confluence. Diamonds from H4 are particularly relevant since CBS already uses H4 for trend/swings.

---

## Ribbons

Ribbons are the Blue (288) cloud displaced vertically — like Envelopes. The formula: `SMA/EMA ± SMA/EMA × multiplier`, where the multiplier is derived from the cloud periods (e.g., 0.144 from the 144 helper period).

The exact multiplier needs to be calibrated per instrument. The result is a channel: price tends to bounce between the main Blue cloud and the upper/lower ribbon.

In consolidation, "halves" of the top and bottom ribbons can also act as bounce levels, giving you a tighter inner channel.

**For CBS:** Ribbons define a price channel. If a CBS target sits at or near a ribbon boundary, that's a confluence zone. The channel width also indicates volatility — narrow ribbons = low volatility = smaller targets more likely to settle.

---

## Schemas (Trading Patterns)

These are specific patterns/setups from MMD, not full strategies. They're played on specific timeframes and times of day.

### Wick Schema
Played **during** candle formation (H1, H4, or custom intervals). At candle open, if price moves away from open, pyramid limit orders in the opposite direction (4, 8, 12, then 20, 40 pips). Target is the open level — statistically, price retests it. Confirm with clouds (trend direction) and volume. If the trend favors your position, hold longer.

### C/O Schema
Played **after** a candle closes (H1). Trade toward the open level of the just-closed candle.

### 228 Schema
M1 timeframe. At specific times (USDJPY 20:59 GMT+1, GBPUSD 19:59 GMT+1), play against the direction of the last candle. Pyramid sell limits 4, 8, 12 pips above close. Works because the market consolidates during these hours. No Doji candles. Confirm with clouds and volume.

### Evening Setups
- **"-3k"** (20:00–21:00 GMT+1): USDJPY, GBPUSD — Wick Schema only
- **"-3"** (21:00–22:00 GMT+1): USDJPY, GBPUSD — C/O Schema only
- **228**: as above

### Morning Setups
- **"6k"**: Wick Schema
- **"6"**: C/O Schema

**For CBS:** The schemas themselves are separate from CBS, but two things are directly useful: the time-of-day patterns (evening and morning setups confirm that certain hours favor certain behaviors) feed into our entry timing model, and the Wick Schema's principle of "price retests open" is essentially what CBS targets predict — a reversion level.

---

## How MMD Supports CBS — Summary

| MMD Component | CBS Use |
|---------------|---------|
| Cloud stacking (trend) | Confirm CBS trade direction aligns with macro trend |
| Cloud S/R zones | Obstacles between price and CBS target |
| Cloud + CBS target overlap | Confluence = higher probability target |
| Red/Orange crossing | Entry timing signal for CBS trades |
| Diamond zones | Additional S/R levels, confluence with CBS targets |
| Diamond 50% level | High-probability retest level near CBS targets |
| Ribbons | Channel boundaries as confluence / obstacle detection |
| Time-of-day schemas | Entry timing features for the ML model |
| Volume confirmation | All MMD signals strengthen with volume — same applies to CBS |

---

## Open Questions & Decisions

1. **Ribbon multipliers** — need to calibrate per instrument. TBD through testing.
2. **Diamond detection** — pattern recognition is about the relationship with neighbor candles (2+ candles on each side in opposite direction), not a wick/body ratio threshold. Detection logic needs to focus on the context pattern, not candle internals.
3. **Cloud periods on different TFs** — unknown whether to compute on H1 only or overlay H4/D1 cloud readings. Needs discovery/experimentation.
4. **Delayed cloud (12 shifted 144)** — likely a lagging confirmation signal. To be validated.
5. **Schema integration** — Wick, C/O, 228, evening/morning setups stay as **separate manual plays**. Not part of CBS engine. On the roadmap for future implementation as part of a bigger multi-strategy trading bot.

---

*Last updated: 2026-03-19*
*Maintained by: Claude (corrected by Niko)*
