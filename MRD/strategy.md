# Midweek Range Division (MRD)

A weekly-cycle strategy that uses the Monday-Tuesday price range as a reference box, then trades the Wednesday directional move when price breaks out with a confirming trendline.

---

## Core Concept

Markets tend to establish a range early in the week (Monday-Tuesday) as liquidity builds on both sides. By midweek (Wednesday), institutional flow typically commits to a direction — either continuing the weekly trend or reversing after a liquidity sweep of the Mon-Tue extremes. MRD captures this transition by:

1. Defining the range (the "box")
2. Waiting for Wednesday to reveal direction via a trendline break
3. Entering on the correct side of the break

> This concept is related to the ICT Weekly Opening Range and the broader "Midweek Reversal" pattern. The Mon-Tue box represents the zone where liquidity accumulates before the real weekly move begins.

---

## Instruments

| Symbol | Type |
|--------|------|
| EURUSD | Forex |
| US500 | S&P 500 index CFD |
| US100 | Nasdaq 100 index CFD |

> These instruments have strong weekly cyclical behavior and sufficient Wednesday volatility to produce clean breakouts.

---

## Timeframe

**H1** — all analysis, box definition, trendline drawing, and entries are on the 1-hour chart.

---

## Risk-to-Reward

**Minimum:** 1:2

**Extended:** Can be increased beyond 1:2 when MMD Clouds (see `MMD/MMD_CLOUDS.md`) confirm the trend direction — cloud stacking aligned with the trade provides confidence to hold for a larger target or trail the stop.

---

## Strategy Rules

### Step 1 — Define the Monday-Tuesday Box

- Mark the **highest high** and **lowest low** from the Monday and Tuesday sessions combined
- This creates a horizontal range (the "box") that represents the weekly opening range
- The box is your reference for the rest of the week

### Step 2 — Wednesday Trendline

- On **Wednesday**, draw a trendline on H1 using the developing price structure:
  - For a potential **bullish** setup: draw a descending trendline connecting Wednesday's swing highs (price is pulling back or drifting down)
  - For a potential **bearish** setup: draw an ascending trendline connecting Wednesday's swing lows (price is pushing up or drifting higher)

### Step 3 — Entry Conditions

**Bullish entry:**
- Price is **below** the descending trendline (in the pullback zone)
- Look for price to break above the trendline, confirming buyers are taking control
- Ideally, price is **outside and below** the Mon-Tue box — this means a liquidity sweep of the box low may have occurred, making the reversal higher-probability

**Bearish entry:**
- Price is **above** the ascending trendline (in the rally zone)
- Look for price to break below the trendline, confirming sellers are taking control
- Ideally, price is **outside and above** the Mon-Tue box — a liquidity sweep of the box high may have occurred

### Step 4 — Filter: Price vs. Box

| Price Location on Wednesday | Action |
|-----------------------------|--------|
| **Outside the box** (above high or below low) | Preferred — clean setup, take the trade |
| **Inside the box** (between high and low) | **No trade** — price is still in the congestion zone, direction is unclear |

> This filter is critical. Trading inside the box means you are in the range where both buyers and sellers have been active — there is no edge.

---

## Stop Loss

Place the stop loss at the **top of the highest swing high since Monday**.

For bearish trades, this means the SL sits above the entire Mon-Tue-Wed structure — giving the trade room to breathe while protecting against a full reversal.

For bullish trades, mirror the logic: SL at the **bottom of the lowest swing low since Monday**.

> If the distance from entry to SL does not allow at least a 1:2 R:R to a reasonable target, skip the trade.

---

## Take Profit

**Minimum target:** 2x the stop loss distance (1:2 R:R).

**Extended targets** (when MMD Clouds confirm direction):
- Opposite end of the Mon-Tue box (if entry was outside the box)
- Next significant S/R level on H1/H4
- Weekly liquidity zones beyond the box range
- Trail the stop after 1:2 is reached — move SL to breakeven and let the trade run toward Thursday/Friday

---

## Ideal Setup Characteristics

The highest-probability MRD trades have:

1. **Price outside the Mon-Tue box on Wednesday** — a clear breakout or sweep has occurred
2. **Clean trendline break** — not a choppy, ambiguous break but a decisive H1 candle closing through the trendline
3. **MMD Cloud alignment** — cloud stacking confirms the trade direction (see `MMD/MMD_CLOUDS.md`)
4. **Sufficient range** — the Mon-Tue box is not unusually narrow (low-volatility weeks produce weak setups)
5. **No major news** — avoid entries directly before high-impact scheduled events (NFP, FOMC, ECB) that could override the weekly cycle

---

## When NOT to Trade

- Price is **inside** the Mon-Tue box on Wednesday — no edge
- The Mon-Tue range is extremely **narrow** — not enough liquidity was built; the breakout may be weak
- Wednesday produces **no clear trendline** — if the H1 structure is choppy with no discernible swing pattern, there is nothing to draw
- A high-impact news event is imminent — the weekly cycle may be overridden
- R:R does not reach 1:2 — the math doesn't work, skip it

---

## Execution Checklist

Before entering:

1. [ ] Mon-Tue box is drawn (high and low marked)
2. [ ] It is Wednesday
3. [ ] Price is **outside** the box
4. [ ] A valid H1 trendline exists and has been broken
5. [ ] Trade direction is clear (bullish below broken descending TL / bearish above broken ascending TL)
6. [ ] SL is placed at the highest swing high (short) or lowest swing low (long) since Monday
7. [ ] R:R is at least 1:2
8. [ ] Optional: MMD Clouds confirm direction for extended target
