# ORB — Opening Range Breakout with Imbalance Entry

A session-open breakout strategy on the S&P 500 that uses the first 15 minutes of the US cash session to define a range, then enters on a pullback to a Fair Value Gap (imbalance) created during the breakout.

---

## Core Concept

The first 15 minutes of the US cash session (9:30-9:45 AM ET) are the highest-volatility period as the opening auction settles and institutional orders execute. This creates a price range that often defines the session's direction.

Rather than entering on the raw breakout (which risks chasing), this strategy waits for:
1. A breakout from the opening range
2. An **imbalance (Fair Value Gap)** to form during the breakout impulse
3. Price to **retrace back** to the imbalance zone
4. A reaction at the imbalance — confirming the zone holds — before entering

This combines the directional bias of ORB with the precision entry of FVG retracement.

> The ORB concept originates from Toby Crabel's work. The imbalance/FVG entry refinement comes from ICT (Inner Circle Trader) methodology.

---

## Instrument

| Symbol | Market |
|--------|--------|
| **US500 / ES / SPX** | S&P 500 |

---

## Timeframe

**M5** — all box definition, imbalance identification, and entries on the 5-minute chart.

---

## Timing

| Event | Time (Polish / CET) | Time (ET) |
|-------|---------------------|-----------|
| US cash session open | 15:30 | 9:30 AM |
| Box closes | 15:45 | 9:45 AM |
| Earliest entry | 15:45+ | 9:45 AM+ |

> During CEST (summer), Polish time = CET + 1 hour, but the US session open remains at the same local ET time. Adjust accordingly.

---

## Risk-to-Reward

**Minimum:** 1:2

---

## What Is an Imbalance (Fair Value Gap)?

An imbalance — also called a Fair Value Gap (FVG) — is a price gap within an impulse move where the market moved so aggressively that it left an unfilled zone. Price tends to return to this zone before continuing.

### Identification (Bullish Example)

Requires **at least 3 consecutive candles** in an impulse move:

```
Candle 1:  [body + wick up to some high]
Candle 2:  [large body — the impulse candle]
Candle 3:  [body + wick down to some low]
```

**The imbalance zone** = the gap between:
- The **highest wick** of Candle 1 (top of C1's upper wick)
- The **lowest wick** of Candle 3 (bottom of C3's lower wick)

**Critical rule:** These wicks must **not overlap**. If they overlap, there is no imbalance — the zone was filled during the impulse and there's nothing for price to come back to.

### Bearish Imbalance

Mirror the logic:
- The **lowest wick** of Candle 1
- The **highest wick** of Candle 3
- The gap between them (C1 low wick to C3 high wick) is the bearish imbalance zone

### Visual Test

The imbalance must be **visually obvious** — a clear gap between the wicks. If you have to zoom in or squint to see it, the gap is too small to be meaningful.

---

## Strategy Rules

### Step 1 — Define the Box

Mark the **High** and **Low** of the 15:30-15:45 (Polish time) period on M5.

This gives you 3 M5 candles. The box is the range from the highest wick to the lowest wick across those candles.

### Step 2 — Wait for the Breakout

After 15:45, wait for price to **exit the box**:
- Price closes **above** the box high → bullish breakout
- Price closes **below** the box low → bearish breakout

> A wick poking outside the box does not count — the **candle body must close** outside the range for a valid breakout.

### Step 3 — Identify the Imbalance

During or immediately after the breakout impulse, look for an imbalance (FVG) to form:
- **Bullish breakout** → look for a bullish imbalance (gap between C1 high wick and C3 low wick, wicks not overlapping)
- **Bearish breakout** → look for a bearish imbalance

If no imbalance forms during the breakout, **skip the trade** — the breakout lacked the impulsive character needed for this setup.

### Step 4 — Wait for the Retracement

After the imbalance forms, wait for price to **come back to the imbalance zone**.

The retracement should be **strong and rapid** — a clean pullback into the FVG, not a slow, grinding drift. A sharp retracement indicates the pullback is a healthy retest, not a trend reversal.

### Step 5 — Enter on Reaction

**Do not enter the moment price touches the imbalance.** Wait for a **reaction** confirming the zone holds:
- 1-2 candles after price reaches the imbalance zone
- Look for a rejection candle (wick into the zone, body closing away from it) or a stall followed by continuation in the breakout direction

**Bullish entry:** Price retraces down into the bullish FVG, reacts (rejection candle or 1-2 candles holding the zone), enter long.

**Bearish entry:** Price retraces up into the bearish FVG, reacts, enter short.

### Step 6 — Stop Loss

Place the SL **above/below the candle that created the imbalance**:
- **Long trade:** SL below the low of the imbalance candle (Candle 2 of the FVG) or below the bottom of the FVG zone
- **Short trade:** SL above the high of the imbalance candle or above the top of the FVG zone

> The SL must be beyond the full FVG. If price moves through the entire imbalance zone, the setup is invalidated — the FVG has been "filled" and the breakout thesis is broken.

### Step 7 — Take Profit

**Minimum target:** 2x the stop loss distance (1:2 R:R).

**Extended targets** (if additional confluence supports holding):
- Next significant S/R level
- Session high/low
- Fibonacci extension from the breakout impulse
- Trail the stop after 1:2 is reached

---

## Complete Trade Sequence (Bullish Example)

```
1. 15:30-15:45  →  Box forms: High = 5,250, Low = 5,235
2. 15:50         →  M5 candle closes above 5,250 (breakout)
3. 15:50-16:00   →  Impulse continues, 3-candle FVG forms:
                      C1 high wick = 5,252
                      C3 low wick  = 5,258
                      Imbalance zone = 5,252 - 5,258
4. 16:10         →  Price retraces sharply back to 5,255 (inside the FVG)
5. 16:15         →  Rejection candle forms — wick dips to 5,253, body closes at 5,257
6. 16:20         →  Enter long at ~5,257
7. SL            →  Below FVG: 5,251 (6 points risk)
8. TP            →  1:2 R:R = 5,269 (12 points reward)
```

---

## When NOT to Trade

- **No breakout by ~16:30 (Polish time)** — if the box hasn't been broken within ~45 minutes, the session lacks the momentum for this setup
- **No imbalance on the breakout** — a slow, grinding breakout without an FVG means the move lacks impulsive character
- **Slow/grinding retracement** — the pullback to the FVG should be sharp and rapid, not a slow drift that suggests trend exhaustion
- **R:R does not reach 1:2** — if the FVG is too far from the breakout and the SL is too wide, the math doesn't work
- **Major news imminent** — avoid if FOMC, NFP, or other high-impact events are within the next 30-60 minutes
- **Box is extremely narrow** — a very tight opening range may produce false breakouts

---

## Execution Checklist

Before entering:

1. [ ] Box is drawn (15:30-15:45 Polish time, High and Low marked)
2. [ ] Price has closed **outside** the box (valid breakout)
3. [ ] An imbalance (FVG) has formed during the breakout impulse
4. [ ] Wicks of C1 and C3 **do not overlap** (valid imbalance)
5. [ ] Price has retraced **back to** the imbalance zone (sharp, rapid pullback)
6. [ ] A reaction is visible (1-2 candles confirming the zone holds)
7. [ ] SL is placed beyond the FVG / imbalance candle
8. [ ] R:R is at least 1:2
