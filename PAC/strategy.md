# Price Action Cycle (PAC)

An intraday price action strategy combining candlestick signals, trend structure, Fibonacci levels, and session context to identify high-probability trade entries with defined targets.

---

## Instruments

### CFDs
| Symbol | Notes |
|--------|-------|
| XAUUSD | Gold |
| USOIL (WTIUSD / WTI.fs) | Monitor geopolitical events — supply disruptions, OPEC decisions, sanctions |
| US500 | S&P 500 |
| US30 | Dow Jones |
| USTECH | Nasdaq 100 |
| GBPUSD | Cable |
| EURUSD | Fiber |
| BTCUSD | Bitcoin |

### Futures
| Symbol | Underlying |
|--------|------------|
| ES | S&P 500 E-mini |
| NQ / NAS100 | Nasdaq 100 E-mini |
| YM | Dow Jones E-mini |
| GC | Gold |
| CL | Crude Oil WTI |
| 6E | Euro FX |

> **Note:** Track which macro events move which instruments. Gold and BTC often react differently to the same catalyst (e.g., rate decisions favor gold, risk-on sentiment favors BTC). Consider parsing a news source (e.g., markets.news) on a schedule for event awareness.

---

## Timeframe & Chart Type

**Primary chart:** M5

**Preferred chart:** Tick chart (generated dynamically).

Tick chart calibration target: **150-160 candles from midnight to ~13:00-14:00 Polish time**. Adjust tick size per instrument to hit this density. This gives enough structure to read intraday price action without excessive noise.

> There is a tick chart generator for MT4 — evaluate performance impact on EA before committing to live use. If tick chart generation introduces unacceptable latency, fall back to M5.

---

## Signal Candle

A signal candle indicates directional intent through its wick-to-body relationship.

**Bullish signal candle:**
- Prominent wick **below** the body (rejection of lower prices)
- Small or no wick above

**Bearish signal candle:**
- Prominent wick **above** the body (rejection of higher prices)
- Small or no wick below

**Impulse-Pullback Signal:**
- An impulse move followed by a shallow pullback, ending with a signal candle in the direction of the impulse
- The pullback should not exceed the origin of the impulse

**Validation — a signal candle gains strength when it aligns with:**
- EMA 21 or SMA 61 (touch/bounce)
- A support/resistance zone or cluster
- A Fibonacci level (retracement or expansion)
- A trendline (major or minor)
- Volume confirmation (above-average volume on the signal candle)

A signal candle alone is not a trade entry. It is a **trigger** that must occur within the correct **context** (trend, sentiment, S/R confluence).

---

## Gap Candle

The inverse of a signal candle — the prominent wick points **in the direction** of the body (wick above body on a bullish candle, wick below body on a bearish candle).

Gap candles create **horizontal reference lines** (drawn from the wick tip or body edge) that price tends to retest. These lines act as magnets — treat them as potential S/R until invalidated.

---

## Trendlines

Trendlines determine the **direction of trend** and define dynamic **S/R levels**.

### How to Draw
1. Identify the first two swing lows (for uptrend) or swing highs (for downtrend)
2. Connect the **wicks** — not the bodies — to capture the true extremes
3. Parallel lines from opposite swings can form a **channel**
4. Adjust when the market shifts to consolidation or reverses direction

### Three Types

| Type | Frequency | Scope |
|------|-----------|-------|
| **Major** | 1-2 per day | Defines the primary trend of the session |
| **Minor** | 3-5 per day | Defines sub-trends and swing structure |
| **Micro** | 15-20+ per day | Short-lived, used for very precise entries |

> Major and minor trendlines are used for trade decisions. Micro trendlines are for fine-tuning entries only — do not base trade direction on them.

---

## Moving Averages

| MA | Type | Period | Purpose |
|----|------|--------|---------|
| EMA | Exponential | 21 | Intraday trend and entry timing |
| SMA | Simple | 61 | Swing-level trend and sentiment filter |

### Sentiment Rules

| Price Position | Sentiment |
|----------------|-----------|
| Above both EMA 21 and SMA 61 | **Bullish** — look for bullish signal candles |
| Below both EMA 21 and SMA 61 | **Bearish** — look for bearish signal candles |
| Between EMA 21 and SMA 61 | **Transitional** — sentiment is weakening, increase caution |
| EMA 21 crosses SMA 61 | **Sentiment switch** — potential trend reversal |

### Price Interaction with MAs

Observe **how** price interacts with the averages:
- **Bounce:** Price touches the MA and reverses — MA is acting as S/R. Look for a signal candle at the touch.
- **Cross and return:** Price briefly crosses the MA then snaps back — false break, MA still holds.
- **Dynamic cross:** Price cuts through both MAs within 1-5 M5 candles. The zone between the EMA 21 and SMA 61 values at the moment of crossing becomes a **S/R range** that is likely to be retested before the trend continues.

---

## Fibonacci Levels

Used to identify pullback zones, targets, and S/R clusters.

**Key ratios:** 0.382 (38.2%), 0.618 (61.8%), 1.0 (100%), 1.272 (127.2%), 1.382 (138.2%), 1.618 (161.8%)

> **Note on terminology:** "Extension" and "Expansion" naming varies across platforms (MT4/MT5, TradingView label them differently). This document uses: **Extension = 2-point (AB)**, **Expansion = 3-point (ABC)**.

### Extensions (2-Point: A-B)

Used to project how far price may travel beyond an impulse.

- **A** = Beginning of the impulse (must be a "visible" move — not a minor fluctuation)
- **B** = End of the impulse

| Level | Zone | Interpretation |
|-------|------|----------------|
| 38.2% - 61.8% | Pullback / Support | After the impulse, price corrects into this zone. The correction must be **visible** — if it's only a gentle retracement, expect a deeper dip. If price action in this zone is choppy/random, skip the setup. |
| 127.2% - 161.8% | Target / Resistance | Profit-taking zone for trades entered at the pullback. |

### Expansions (3-Point: A-B-C)

Used to project targets after a correction completes.

- **A** = Beginning of the impulse
- **B** = End of the impulse
- **C** = Deepest point of the correction (if the next correction goes deeper than C, recalculate)

| Level | Role |
|-------|------|
| 38.2% | Conservative target |
| 61.8% | Moderate target |
| 100% (Measured Move) | Primary target — price frequently reaches this level |
| 138.2% | Extended target |
| 161.8% | Aggressive target |

### Impulse Identification

An impulse is a directional move that is:
- Visually distinct from surrounding price action
- Composed of candles predominantly in one direction
- Larger in magnitude than recent swings
- Not a minor fluctuation or noise — if you have to squint to see it, it's not an impulse

### Clusters

When multiple Fibonacci levels from different measurements land within **~5 pips** of each other, they form a **cluster**. Clusters are high-probability S/R zones.

Clusters, combined with other confluences (trendlines, MAs, gap candle lines, battle zones), form the **context** of a trade. An entry requires a signal candle appearing at or near a cluster/confluence zone.

---

## Elliott Wave Structure

Applied on M5 to count the momentum within a trend.

### Basic Structure
- A full trend typically consists of **5 impulse waves** (labeled 1-2-3-4-5)
- Waves 2 and 4 are **corrective** (counter-trend pullbacks)
- Waves 1, 3, and 5 move in the trend direction
- Wave 3 is usually the longest and strongest

### Practical Rules
- After identifying a sentiment change, count the impulse waves
- **Waves 1-3:** Highest probability — trade aggressively with the trend
- **Wave 4-5:** Momentum fading — reduce position size or skip
- **2-3 consecutive moves in one direction after the 5th wave** = likely a larger pullback/reversal forming
- If wave count becomes ambiguous, defer to other PAC tools (MAs, trendlines, Fibonacci) for direction

> Elliott Waves are a **supporting tool** in PAC, not the primary decision driver. Use them to gauge where you are in the trend cycle, not to predict exact turning points.

---

## Reversal Lines (S/R from Swing Reactions)

A method for building S/R zones from observed price reactions at swing points.

### Process
1. Mark the latest **swing high or swing low** (use the wick, not the body)
2. Wait for price to return to that level
3. **If price reacts** (bounce, stall, or reversal) at the swing level — mark it as a **reversal line** (S/R)
4. **If price ignores the level** — discard it; do not force zones
5. Build S/R zones from confirmed reversal lines

### Validation
- Reversal lines should align with **major or minor trendlines** — not micro trendlines
- Zones where multiple reversal lines and trendlines converge are high-conviction S/R

---

## Double Top & Bottom (M5)

Used as a **trend continuation** signal, not a reversal signal in this context.

### Setup
1. During a correction within a trend, two swing highs (double top) or swing lows (double bottom) form
2. The two swings must have **visible separation** — not consecutive candles
3. The wicks do not need to align perfectly — find the **center** of the two swing points
4. If the candle bodies (open/close) are in the same price area, wick differences are less important

### Entry
- After the second touch, look for a **dynamic reaction**: 3+ consecutive candles of the same color moving away from the double top/bottom
- This works best on tick or range charts where noise is filtered
- The dynamic move signals that the correction has ended and the trend is resuming

---

## OHLC Analysis (D1)

Use the previous day's D1 candle (Open, High, Low, Close) to define **intraday bias zones**.

### For a Bearish D1 Candle (Close < Open)

| Price Zone | Location | Bias |
|------------|----------|------|
| Within the candle body | Between Open and Close | Neutral / "Maybe" zone — no clear edge |
| Between Open and wick high | Above body, within upper wick | **Sellers' promotion zone** — favorable for shorts |
| Between Close and wick low | Below body, within lower wick | **Buyers' promotion zone** — favorable for longs |

### For a Bullish D1 Candle (Close > Open)
Reverse the logic: above the body (within upper wick) = buyers' promo zone, below the body (within lower wick) = sellers' promo zone.

> These zones provide a **daily directional filter**. If your intraday signal aligns with the D1 promo zone bias, the trade has higher conviction.

---

## Session Objective

Trading session focus windows (Polish time — CET/CEST):

| Session | Hours (Polish) | Role |
|---------|----------------|------|
| **Asia** | 23:00 - 07:59 | Establishes the overnight range |
| **London** | 09:00 - 13:00 | European session; primary trading window before US |
| **America** | 14:00 - 21:00 | US session; highest volatility, trend continuation or reversal |

> These are **focus windows** for this strategy, not full exchange hours.

### Session Box Logic

**Asia Box** (High/Low of Asia session):
- The zone **above** the Asia box = European buyers' promo zone (potential long setups or profit-taking by shorts)
- The zone **below** the Asia box = European sellers' promo zone

**London Box** (High/Low of London session):
- The zone **above** the London box = US buyers' promo zone
- The zone **below** the London box = US sellers' promo zone

> Trades where price has **clearly broken out** of the session box are preferred. If price is wandering inside the box, the setup lacks conviction — wait.

---

## Measured Move (AB=CD)

A pattern that projects the target for the current momentum leg.

> Signal and gap candles are **not relevant** for identifying the measured move structure — only the swing points matter.

### Structure

- **A → B (Impulse):** Price begins on one side of EMA 21 and clearly ends on the opposite side. Wicks merely "touching" the EMA do not count — the move must be a **clean cross**.
- **B → C (Pullback):** Point C must be clearly back on the **same side of EMA as point A**. This confirms the pullback.
- **C → D (Measured Move):** D is the target where AB = CD in price distance.

### Drawing
Use the Fibonacci expansion tool: mark A, B, C — the 100% level gives you D.

### Rules
- The movement must be **clean** — clear impulse, clear pullback, no choppy/ambiguous price action
- Keep all other PAC context in mind (Fibonacci clusters, S/R, trendlines) — the measured move target should ideally align with other levels
- **Invalidation:** If price, after moving from C toward D, retraces back beyond C (deeper correction than C), the measured move is void

### 3rd Leg (Advanced)
After the measured move completes (D reached), if a correction occurs:
- Measure from the deepest point of that correction
- The 3rd leg often terminates at a cluster or when price touches the EMA
- This is a lower-probability setup — treat it as supplementary, not primary

### Double Up & Double Down

An alternative view of the measured move using **Fibonacci retracement** instead of expansion:

- **A → B:** Impulse begins on one side of EMA, clearly ends on the opposite side
- Apply Fibonacci retracement to A-B
- **Double Up (bullish) / Double Down (bearish):** The retracement levels project continuation targets
- A **triple** (3rd occurrence) of this pattern creates a strong S/R line

### Combining Both
The measured move target (D) and the double up/down projection can align, creating a **support/resistance confluence area**. The 3rd leg of the measured move can coincide with the double up/down value — when they align, the level is high-conviction.

---

## Hidden Channel (Rotation Channel)

A channel pattern that forms after a target is hit and new momentum begins.

### Context
Price has reached a significant level: a measured move target, double top/bottom, or other key level. A reaction occurs and price begins moving with new momentum.

### Structure
- Two parallel lines containing the price rotation (a channel)
- Look for a **clean impulse** within the channel to define the boundaries
- The channel represents a pause/rotation before the next directional move

### Trading Rules

1. **Wait for confirmation:** If only one side of the channel is tested ("false retest"), do not enter — wait for both sides to be tested
2. **Entry:** Look for a signal candle within correct context:
   - For bearish setups: signal candle below EMA or price strongly crossing EMA downward
   - For bullish setups: signal candle above EMA or price strongly crossing EMA upward
3. **Target:** Use the measured move projected from the channel. Settle the trade **a few pips before** the projected target
4. At the beginning of the rotation, the measured move provides the initial target framework

---

## Battle Zone

A swing-based S/R classification system.

### Zone Types

| Type | Definition |
|------|------------|
| **Resistance** | Range where counter-trend traders gained control (e.g., sellers pushed price down from this zone in an uptrend) |
| **Support** | Range where trend-direction traders defended (e.g., buyers held price at this zone in an uptrend) |
| **Untested** | A swing that produced a strong reaction but has **not been retested** — strongest conviction |
| **Verified** | A zone retested by price **at least once** — confirmed but slightly weaker |
| **Turncoat** | A zone where the character may be changing — former support becoming resistance, or vice versa |
| **Battle Zone** | A range where multiple swings cluster tightly (buyers and sellers alternating control). Mark from the highest to the lowest swing in the cluster. |

### Rules
- If a battle zone is **crossed in the opposite direction** (e.g., market was bearish but buyers push through the zone), the battle zone is **void** — look for opportunities in the new direction
- **Each retest weakens the zone** — untested zones are strongest, zones retested 3+ times are likely to break
- Battle zones interact with all other PAC tools — a signal candle at a battle zone boundary, aligned with trend and Fibonacci levels, is a high-probability setup

---

## Spike & Move Patterns

Patterns that form after a sudden, sharp price movement (spike). The spike can be a single candle or up to ~10 candles — what matters is the **speed and magnitude** of the move, not the candle count.

> All examples below are described from the bullish perspective. Mirror for bearish.

### Spike & Channel

A spike followed by a **channel continuing in the spike's direction**.

**Points:**
- **A** = Open/base of the spike
- **A'** = Top of the spike (where the channel begins)
- **B** = Highest point reached in the channel
- **C** = 50% Fibonacci retracement of the full A-B range

**Rules:**
1. Wait for a pullback to the **50% Fib of A-B** (point C)
2. Price must **react** at the 50% level — if it breaks through, the entire setup is invalidated
3. **Target (D):** Measured move from A-B-C (100% Fibonacci expansion)
4. If price within the channel reaches the **138.2% Fib of A-A'**, expect exhaustion — the move is likely complete
5. If price begins correcting before 138.2% but does **not break** the 50% level, and buyers reappear:
   - Wait for price to cross back above EMA
   - Draw a trendline from the channel high through the intermediate swing low
   - Entry opportunity with target at 138.2% Fib of A-A'

**Alternative view:** Spike & Channel is essentially a play on the 2nd leg. It can be reframed as a measured move where A'' = base of spike, B'' = top of channel, C'' = deepest correction — making it a waiting game for the 3rd leg.

> This setup is often "ungrateful" — price frequently reaches 138.2% within the channel before a clean pullback entry materializes.

### Spike & Flag

A spike followed by a **channel in the opposite direction** (a flag — price drifts against the spike).

**Points:**
- **A** = Open/base of the spike
- **B** = Highest point before the flag begins
- **C** = 50% Fibonacci retracement of A-B

**Rules:**
1. **Do not** enter during the flag — do not chase the counter-trend drift
2. Wait for a pullback to 50% Fib of A-B (point C). If price breaks through 50%, the setup is invalidated.
3. **Target (D):** Measured move from A-B-C
4. The **trigger** is a clean, sudden break of the flag's upper channel line:
   - The candle **body** must close outside the channel (not just a wick)
   - A signal candle at the breakout adds confidence
   - If you miss the breakout entry, there is often a retest of the broken channel line — enter on the retest
5. If price has not reached the spike high (B), you can either use B as a conservative target or go with the full measured move
6. **Spike & Flag tends to skip corrections**, especially on Oil, US indices, and Gold — once the flag breaks, the move can be fast and one-directional

### Spike & Range

A spike followed by a **sideways range** (no channel, no flag — just consolidation).

> **Do not trade this pattern.** It is very difficult to identify a directional bias from a range after a spike.

---

## Trend or Range Day Classification

Use MMD Clouds (see `MMD/MMD_CLOUDS.md`) to determine whether the current session is trending or ranging. This classification affects which PAC setups to prioritize:
- **Trend day:** Favor measured moves, spike patterns, and trend-continuation setups
- **Range day:** Favor battle zone reactions, session box plays, and double top/bottom setups

---

## Trade Execution Checklist

Before entering any trade, confirm:

1. **Direction:** Trend and sentiment align (MAs, Elliott Wave count, trendlines)
2. **Context:** Entry point sits at a confluence zone (Fibonacci cluster, battle zone, reversal line, session box boundary, trendline, MA)
3. **Trigger:** A valid signal candle has formed at the confluence zone
4. **D1 Bias:** Intraday direction aligns with the OHLC promo zone bias
5. **Session:** Current session supports the trade (not in a dead zone between sessions)
6. **Target:** A clear, measurable target exists (measured move, Fibonacci level, cluster)
7. **Settlement:** Place TP a few pips before the target to account for spread and slippage
