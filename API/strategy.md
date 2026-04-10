# API Box (American Petroleum Institute Range Strategy)

A session-range mean-reversion strategy that defines a pre-session box, then uses Fibonacci extension levels as scaled limit-order entries expecting price to revert back to the box.

---

## Background: API Oil Inventory Reports

The American Petroleum Institute (API) Weekly Statistical Bulletin has been published since 1929. It provides weekly estimates of changes in U.S. and regional crude oil inventories, based on surveys from refineries, terminals, and importers (covering ~90% of the industry).

**Schedule:** Every Tuesday at 4:30 PM ET (22:30 CET / 22:30 CEST).
When a US federal holiday falls on Monday, the release shifts to Wednesday at the same time.

**Data covered:** Crude oil, gasoline, distillates, and other petroleum products (over 90% of refinery production).

> **Note on forex impact:** The API report primarily moves oil and energy markets. Its direct impact on major USD forex pairs is minimal — the EIA report (Wednesday 10:30 AM ET) carries more weight. However, large API surprises can create short-term USD volatility, and the report serves as a timing anchor for this strategy's mean-reversion logic. USDCAD is the most directly affected forex pair, though it is not part of this strategy's instrument list.

---

## Instruments

| Symbol | Type |
|--------|------|
| EURUSD | Major |
| GBPUSD | Major |
| USDCHF | Major |
| USDJPY | Major |

---

## Timeframe

**Execution:** M5

---

## Core Theory

### The Box

Define a range ("box") using the **High** and **Low** from **00:00 to 07:59 Polish time**.

> **Time zone note:** Polish time = CET (UTC+1) in winter, CEST (UTC+2) in summer. The box window covers the Asian session and early European pre-market — a period of typically lower volatility that establishes the session's initial range.

The expectation is that after price breaks out of the box, it will eventually **revert back to the box edge**. This is a mean-reversion play — the box represents fair value, and spikes beyond it are fading opportunities.

**Both sides are tradeable** (buy from below, sell from above), but this should be validated through backtesting per instrument before going live on both directions.

### Market Regime Filter

This strategy works in **consolidating/ranging markets**, not trending ones. In a trending market, breakouts beyond the box are more likely to follow through rather than revert, making the fade a losing trade.

Use MMD Clouds (see `MMD/MMD_CLOUDS.md`) to confirm the market is in a ranging regime before deploying this strategy. If clouds are stacked in a clear trend, skip the session.

### Time Deadline

If the box has not triggered a trade (price has not reached SET 1) **or** an open trade has not settled by **12:00-14:00 Polish time**, abandon the setup for the day.

> The exact deadline needs to be optimized per instrument through backtesting. The logic: after European/early US session hours, the range dynamics that drive this strategy lose relevance.

---

## Fibonacci Setup

Draw a Fibonacci retracement from the **top** to the **bottom** of the box.

**For sell orders (trades from the top side):**
- 0 = Box Low
- 1 = Box High
- Extensions project above the box

**For buy orders (trades from the bottom side):**
- 0 = Box High
- 1 = Box Low
- Extensions project below the box

### Levels

| Level | Label | Role |
|-------|-------|------|
| 0 | Box edge (far side) | — |
| 0.382 | — | Reference level inside the box |
| 0.618 | **TP 1** | Take-profit target for SET 1 and SET 2 |
| 1.0 | **SET 1** | First limit-order entry (at the box edge) |
| 1.272 | **SET 2** | Second limit-order entry (first extension beyond the box) |
| 1.618 | **SET 3** | Third limit-order entry (deep extension beyond the box) |

---

## Order Management

Three scaled limit orders, each placed at a Fibonacci level beyond the box edge:

### SET 1 (Level 1.0 — Box Edge)

| Parameter | Value |
|-----------|-------|
| **Entry** | Box edge (Fib 1.0) |
| **TP** | Fib 0.618 (TP 1 — inside the box) |

### SET 2 (Level 1.272 — First Extension)

| Parameter | Value |
|-----------|-------|
| **Entry** | Fib 1.272 |
| **TP** | Fib 0.618 (TP 1) |

> **To investigate:** Does SET 2 more reliably reach a TP equal in pip distance to SET 1's TP (i.e., the same absolute distance rather than the same price level)? This needs backtesting to determine the optimal TP for SET 2.

### SET 3 (Level 1.618 — Deep Extension)

| Parameter | Value |
|-----------|-------|
| **Entry** | Fib 1.618 |
| **TP** | Fib 1.0 (SET 1 level — the box edge) |

**Fast spike rule:** If price reaches SET 3 very quickly (sharp, impulsive move), apply special TP logic:
- SET 2 and SET 3 both get **TP at Fib 1.0** (SET 1 level)
- SET 1 moves to **breakeven**

The rationale: a fast spike to SET 3 suggests strong momentum that may not fully revert to the box interior — taking profit at the box edge is safer.

---

## Risk Management

### Position Sizing

**All three positions combined must not exceed 1% account risk.**

This means each individual position's risk is a fraction of 1% — divide the total risk budget across the three SETs based on your lot sizing model.

### Stop Loss

The stop loss is **not fixed** at a static pip distance. Instead:

1. Review the **previous day's highs and lows** — these levels indicate where price has already found S/R
2. Identify relevant S/R zones from:
   - Previous session structure (swings, wicks)
   - Battle zones or clusters from PAC analysis (see `PAC/strategy.md`)
   - MMD Cloud boundaries
3. Place the SL **beyond** the nearest relevant S/R level that would invalidate the mean-reversion thesis

> The SL must be at a level where, if reached, the box reversion is clearly no longer valid. Placing it arbitrarily risks either getting stopped out by noise (too tight) or taking excessive loss (too wide).

### Multi-Position Management

When multiple positions are open and price reverts toward the box:

- When price reaches the **entry level of the lower SET** (closer to the box), move the **higher SET to breakeven**
- Example: SET 1 and SET 2 are both open. Price reverts to SET 1's entry level → move SET 2 to breakeven

This locks in risk reduction as the trade moves in your favor.

---

## Minimum Box Width

The box must have a minimum width to be tradeable — too narrow a range means the Fibonacci extensions will be too close together and the setup lacks structure.

| Instrument Category | Minimum Width |
|---------------------|---------------|
| **Majors** (EURUSD, GBPUSD) | 25 pips |
| **Others** (USDCHF, USDJPY) | 20 pips |

> If the box is narrower than the minimum, skip the day. A narrow box suggests extremely low overnight volatility — the Fibonacci levels will be too compressed to produce meaningful entries with adequate R:R.

---

## Execution Checklist

Before placing orders:

1. [ ] Box is defined (00:00-07:59 Polish time, High and Low marked)
2. [ ] Box width meets minimum threshold (25 pips majors / 20 pips others)
3. [ ] Market is in **consolidation** — confirmed via MMD Clouds (no clear trend stacking)
4. [ ] Fibonacci levels are drawn from box High to Low (or vice versa depending on trade direction)
5. [ ] SET 1, SET 2, SET 3 limit orders are placed at correct Fib levels
6. [ ] TPs are set per the rules above
7. [ ] SL is placed beyond relevant S/R (previous day structure, clusters, clouds) — not a fixed distance
8. [ ] Total risk across all three positions does not exceed 1%
9. [ ] Time is before the 12:00-14:00 deadline — if no trigger by then, cancel pending orders

---

## Open Questions

1. **Exact deadline:** 12:00 or 14:00 Polish time? Needs per-instrument backtesting to find the cutoff where win rate drops.
2. **SET 2 TP optimization:** Same price level (TP 1) vs. same pip distance as SET 1? Backtest both.
3. **Directional filter:** Can both sides (buy and sell) be traded equally, or does one direction have a statistical edge? Needs validation.
4. **API report as catalyst:** Is this strategy best deployed specifically on Tuesdays (API day) or is it a daily setup? The box logic is general — determine whether Tuesday performance differs meaningfully.
