# Price Action Cycle (PAC)

An intraday price action strategy combining candlestick signals, trend structure, Fibonacci levels, and session context to identify high-probability trade entries with defined targets.

**Instructor:** Paweł (community: "Cykl Rotacyjny Ceny" / Price Action Cycle)

**Primary timeframe:** M5 for initial analysis; tick chart and range chart for entry timing and pattern identification.

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

> **Note:** Track which macro events move which instruments. Gold and BTC often react differently to the same catalyst (e.g., rate decisions favor gold, risk-on sentiment favors BTC).

---

## Timeframe & Chart Type

**Primary analysis chart:** M5

**Mandatory execution chart:** Tick chart or range chart. The following components **require** tick or range charts and fail on time-based charts:

| Component | Requirement |
|-----------|-------------|
| Reversal zone identification | Tick/range mandatory — M1/M3/M5 produce weak, unreliable zones |
| Double Top/Bottom entries | Tick/range mandatory — dynamic reactions are not visible on time-based charts |
| Double Up/Down entries | Tick charts mandatory — M5/M15 explicitly excluded |
| Measured move entry timing | Tick charts for precision — small marking errors cascade into large targeting errors |

If tick chart is unavailable, use M5 as a fallback **only for initial analysis**, not for entry timing.

**Tick chart calibration target:** 150–160 candles from midnight to ~13:00–14:00 Polish time. Adjust tick size per instrument to hit this density.

> **Warning (range charts):** On range charts, signal candles appear almost non-stop due to candle construction. Filter signal candles strictly by context on range charts — not every one is significant.

---

## Signal Candle

A signal candle indicates directional intent through its wick-to-body relationship.

**Bullish signal candle:**
- Prominent wick **below** the body (rejection of lower prices)
- Small or no wick above (a tiny wick at the top is acceptable)

**Bearish signal candle:**
- Prominent wick **above** the body (rejection of higher prices)
- Small or no wick below

**Wick-to-body assessment:** There is no fixed numerical ratio — assess **optically/visually**. The wick must be visually dominant:
- At minimum, the wick should be roughly **2× the body length**
- If the wick is nearly the **same size** as the body → not a signal candle
- If the **body is larger** than the wick → not a signal candle

**EMA 21 directional filter (hard rule):**
- A **bullish** signal candle is only valid when price is **above EMA 21**
- A **bearish** signal candle is only valid when price is **below EMA 21**
- A signal candle on the wrong side of EMA 21 does not qualify

**Impulse-Pullback Signal:**
- An impulse move followed by a shallow pullback, ending with a signal candle in the direction of the impulse
- The pullback should not exceed the origin of the impulse

**Validation — a signal candle gains strength when it aligns with:**
- EMA 21 or SMA 61 (touch/bounce)
- A support/resistance zone or cluster
- A Fibonacci level (retracement or expansion)
- A trendline (major or minor)

A signal candle alone is not a trade entry. It is a **trigger** that must occur within the correct **context** (trend, sentiment, S/R confluence).

---

## Gap Candle

The inverse of a signal candle — the prominent wick points **in the direction** of the body (wick above body on a bullish candle, wick below body on a bearish candle). Sometimes no wick on either side — still a gap candle.

Gap candles represent situations where price opened and immediately fled without hesitation. They often occur around **news events**.

Gap candles create **horizontal reference lines** (drawn from the wick tip or body edge) that price tends to retest. These lines act as magnets — treat them as potential S/R until invalidated.

**Return timing:** Price should return to the gap candle level within **1–2 swings** of formation. On tick charts, returns happen very quickly. If the gap candle forms in the morning and price only returns at 22:00, that is technically a return but not the desired situation.

---

## Trendlines

Trendlines determine the **direction of trend** and define dynamic **S/R levels**.

### How to Draw
1. Identify two swing lows (for uptrend) or swing highs (for downtrend) that are **close to each other** and that **caused volatility** / had a visible reaction on price. Not just any swings — the swings must have had meaningful price impact.
2. **Primary method:** Connect **wick to wick** to capture the true extremes.
   - **Permitted alternative:** One wick + one body from one of the two swings. At least one connection point **must** be a wick.
   - Body-to-body connections are forbidden.
3. **Do not skip intermediate swings.** If an important swing lies between your two connection points, the trendline is invalid. Always use the **closest two relevant swings**.
4. Parallel lines from opposite swings can form a **channel**.
5. Adjust when the market shifts to consolidation or reverses direction. Updating with two newer swings is permitted, but the original line may still hold value.

### Three Types

| Type | Frequency | Scope |
|------|-----------|-------|
| **Major** | 1–2 per day | Defines the primary trend of the session |
| **Minor** | 3–5 per day | Defines sub-trends and swing structure |
| **Micro** | 15–20+ per day | Short-lived, used for very precise entries |

> Major and minor trendlines are used for trade decisions. Micro trendlines are for fine-tuning entries only — do not base trade direction on them. Reversal lines can only be validated against major and minor trendlines — micro trendlines are explicitly excluded.

---

## Moving Averages

| MA | Type | Period | Purpose |
|----|------|--------|---------|
| EMA | Exponential | 21 | Intraday trend, entry timing, and measured move reference |
| SMA | Simple | 61 | Swing-level trend and sentiment filter |

> **Practical note:** The SMA 61 is primarily a background context filter. For active intraday work — especially measured moves — EMA 21 is the sole reference. SMA 61 does not help for measured move construction.

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
- **Dynamic cross:** Price cuts through both MAs within **~1–2 candles**. The cross must be **impulsive and fluid** — not a sideways meander. If price is wandering sideways through the MAs in a range, ignore it — that is not a dynamic cross.
  - The zone between the **EMA 21 and SMA 61 values** (the MA lines themselves, not candle bodies) at the moment of crossing becomes a **S/R range**.
  - Price should return to this zone before continuing in the new direction.
  - This works on all chart types (minute, tick, range).

---

## Fibonacci Levels

Used to identify pullback zones, targets, and S/R clusters.

**Key ratios:** 0.382 (38.2%), 0.618 (61.8%), 1.0 (100%), 1.382 (138.2%), 1.618 (161.8%)

> **Note on terminology:** "Extension" and "Expansion" naming varies across platforms (MT4/MT5, TradingView label them differently). This document uses: **Extension = 2-point (AB)**, **Expansion = 3-point (ABC)**.

### Extensions (2-Point: A-B)

Used to project how far price may travel beyond an impulse.

- **A** = Beginning of the impulse (must be a "visible" move — not a minor fluctuation)
- **B** = End of the impulse

| Level | Zone | Interpretation |
|-------|------|----------------|
| 38.2% – 61.8% | Pullback / Support | After the impulse, price corrects into this zone. The correction must be **visible** — if it's only a gentle retracement, expect a deeper dip. If price action in this zone is choppy/random, skip the setup. |
| 138.2% – 161.8% | Target / Resistance | Profit-taking zone for trades entered at the pullback. |

**Shallow correction rule:** If the correction is shallower than 38.2%, expect price to move slightly further in the impulse direction but then make a much deeper correction.

### Expansions (3-Point: A-B-C)

Used to project targets after a correction completes.

- **A** = Beginning of the impulse
- **B** = End of the impulse
- **C** = Deepest point of the correction

| Level | Role |
|-------|------|
| 38.2% | Conservative target (intermediate S/R) |
| 61.8% | Moderate target (intermediate S/R) |
| 100% (Measured Move) | Primary target — price frequently reaches this level |
| 138.2% | Extended target |
| 161.8% | Aggressive target |

**Correction point (C) adjustment rule:**
- If the correction deepens **while staying within** the Fibo zone (38.2–61.8%), update point C to the deepest point.
- **Exception:** If the impulse has **already renewed** in the trend direction before the deeper correction, you **must stick with the original C**. Do not move C after the impulse has resumed.

### Impulse Identification

An impulse is a directional move that is:
- Visually distinct from surrounding price action
- Composed of candles predominantly in one direction
- Larger in magnitude than recent swings
- Not a minor fluctuation or noise — if you have to squint to see it, it is not an impulse
- When multiple potential impulses exist, select the one that is **most significant on the chart** — assessed against previous visible moves

### Clusters

When multiple Fibonacci levels from different measurements land within **~5 pips** of each other, they form a **cluster**. Clusters are high-probability S/R zones.

When price reaches a cluster → **realize profit**. Do not extend the position. The cluster is a destination point — price achieved what it was supposed to achieve.

Clusters, combined with other confluences (trendlines, MAs, gap candle lines, battle zones), form the **context** of a trade. An entry requires a signal candle appearing at or near a cluster/confluence zone.

---

## Elliott Wave Structure

Applied on M5 to count the momentum within a trend. Assessed **within a single day** — every day is different.

### Practical Wave Counting

- After identifying a **sentiment change**, count the impulse waves in the trend direction
- A trend typically produces **3–5 impulse waves**, though **up to 8 can be counted** in practice
- Between impulses there are **corrective pauses** (counter-trend pullbacks or sideways moves)
- PAC does not use formal 1-2-3-4-5 labeling — simply count the impulses as they occur

### Usage Rules
- **Impulses 1–3:** Highest probability — trade aggressively with the trend
- **Impulse 4–5:** Momentum fading — reduce position size or skip
- **After the 4th–5th impulse:** Do not force it. Expect a pause or stop. Do not enter expecting further continuation.
- If wave count becomes ambiguous, defer to other PAC tools (MAs, trendlines, Fibonacci) for direction

> Elliott Waves are a **supporting tool** in PAC, not the primary decision driver. Use them to gauge where you are in the trend cycle, not to predict exact turning points. Do not extend into harmonic patterns (sharks, butterflies, bats) — they have been tested extensively and provide zero edge.

---

## Reversal Lines (S/R from Swing Reactions)

A method for building S/R zones from observed price reactions at swing points. **Requires tick or range charts.**

### Process
1. Mark the latest **swing high or swing low** — mark the **entire wick** of the swing candle as the reversal zone (narrow the zone if the body is centered within the candle range)
2. Wait for price to return to that level
3. **If price reacts** (a clear, decisive move away) at the swing level — mark it as a **reversal line** (S/R)
4. **If price ignores the level** — discard it; do not force zones
5. Build S/R zones from confirmed reversal lines
6. After price breaks through a reversal zone and establishes a new swing, draw **new trendlines** — do not recycle old ones past the break

### Validation
- Reversal lines must align with **major or minor trendlines** — not micro trendlines (micro trendlines are explicitly excluded)
- Zones where multiple reversal lines and trendlines converge are high-conviction S/R
- EMA confluence can be added as extra confirmation

---

## Double Top & Bottom

Used as a **trend continuation** signal, not a reversal signal. **Requires tick or range charts** — dynamic reactions are not visible on time-based charts.

### Setup
1. During a correction within a trend, two swing highs (double top) or swing lows (double bottom) form
2. The two swings must have **visible separation** — not consecutive candles (candle-to-candle is a common error)
3. If the candle **bodies** (open/close) are at the same price level, wick differences do not matter — bodies take priority over wicks
4. Precision is not critical — recognize the pattern and confirm body alignment

### Entry
- After the second touch, look for a **dynamic reaction**: consecutive same-color candles flowing away from the double top/bottom
- If the reaction is choppy (alternating red/green candles) → discard the setup
- The dynamic move signals that the correction has ended and the trend is resuming

### Restrictions
- **Do NOT use at daily extremes.** Using double top/bottom at the absolute high or low of the day as a reversal signal does not lead to success. DT/DB is strictly a continuation pattern within corrections.
- Gold: double top/bottom is a rare element — do not expect frequent setups

---

## OHLC Analysis (D1)

Use the previous day's D1 candle (Open, High, Low, Close) to define **intraday bias zones**. Use M15 for a quick visual assessment of which zone price is in — but make **no trading decisions** from M15.

### For a Bearish D1 Candle (Close < Open)

| Price Zone | Location | Bias |
|------------|----------|------|
| Within the candle body | Between Open and Close | Neutral / "Maybe" zone — no clear edge |
| Between Open and wick high | Above body, within upper wick | **Sellers' promotion zone** — favorable for shorts |
| Between Close and wick low | Below body, within lower wick | **Buyers' promotion zone** — favorable for longs |

### For a Bullish D1 Candle (Close > Open)
Reverse the logic: above the body (within upper wick) = buyers' promo zone, below the body (within lower wick) = sellers' promo zone.

**First-touch rule:** The **first time** price reaches a promo zone in the day has the **highest reaction probability**. Subsequent visits to the same promo zone within the same session have decreasing reliability.

> These zones provide a **daily directional filter**. If your intraday signal aligns with the D1 promo zone bias, the trade has higher conviction.

---

## Session Objective & Session Boxes

Trading session focus windows (Polish time — CET/CEST):

| Session | Hours (Polish) | Role |
|---------|----------------|------|
| **Asia** | 23:00 – 07:59 | Establishes the overnight range |
| **London** | 09:00 – 13:00 | European session; primary trading window before US |
| **America** | 14:00 – 21:00 | US session; highest volatility, trend continuation or reversal |

> These are **focus windows** for this strategy, not full exchange hours. The London session is intentionally limited to isolate the period without US participation.

### Session Box Logic

**Asia Box** (High/Low of Asia session):
- The zone **above** the Asia box = European buyers' promo zone (potential long setups or profit-taking by shorts)
- The zone **below** the Asia box = European sellers' promo zone

**London Box** (High/Low of London session):
- The zone **above** the London box = US buyers' promo zone
- The zone **below** the London box = US sellers' promo zone

**Session objective concept:** Each session's participants arrive and seek promotion zones — where is it cheap? Where is it expensive? Their first goal is to reach a promotion zone and either take profits or establish positions there.

> Trades where price has **clearly broken out** of the session box are preferred. If price is wandering inside the box, the setup lacks conviction — wait.

---

## Measured Move (AB=CD)

A pattern that projects the target for the current momentum leg. This is one of the most important and most difficult aspects of PAC.

> Signal and gap candles are **not relevant** for identifying the measured move structure — only the swing points matter. Use **EMA 21 exclusively** as the reference MA for measured moves.

### Structure

- **A → B (Impulse):** Price begins on one side of EMA 21 and clearly ends on the opposite side. Wicks merely "touching" the EMA do not count — the move must be a **clean cross** with price clearly closing on the opposite side. Select the **largest/most significant impulse** visible on the chart.
- **B → C (Pullback):** Point C must be **clearly back on the same side of EMA as point A**. This must be a visible, significant return — a barely-grazing touch of the EMA does not qualify.
- **C → D (Measured Move):** D is the target where AB = CD in price distance (100% expansion).

### Drawing
Use the Fibonacci expansion tool: mark A, B, C — the 100% level gives you D.

### Rules
- The movement must be **clean** — clear impulse, clear pullback, no choppy/ambiguous price action
- Keep all other PAC context in mind (Fibonacci clusters, S/R, trendlines) — the measured move target should ideally align with other levels
- **Invalidation:** If price, after moving from C toward D, retraces back beyond C (deeper correction than C), the measured move is void — identify a new impulse and new ABC

### 3-Leg Rules

After the measured move completes (D reached), if a correction occurs, a 3rd leg can be projected:

1. **3rd leg sizing:** The 3rd leg equals the **1st leg** in size — not the 2nd leg, even if the 2nd leg was much larger. The 1st leg sets the template.
2. **EMA contact required:** Before projecting the 3rd leg, the correction after the 2nd leg **must contact EMA 21** (at minimum a touch, ideally a cross and return). If the pullback does not touch the EMA, the 3rd leg projection is not yet valid — **wait** for EMA contact.
3. **Maximum 3 legs.** After the 3rd leg completes, stop. Do not project a 4th leg. Wait for a new situation.
4. The correction after D should ideally reach the 38.2–61.8% Fibonacci retracement zone.

### Extended Measured Move

When price **overshoots** the standard measured move target (100%) by several candles without returning (not a slight one-candle overshoot), the move may continue:

1. Calculate an **extended target** using external Fibonacci: same A-B-C points, project to **138.2%** or **161.8%** of the original A-B range
2. Only project the extended target **after** the standard 100% target has been exceeded by a meaningful margin
3. Price should stop within the 138.2–161.8% range
4. After the extended move completes, calculate the correction from the **entire move** (not just the original MM)
5. Apply a Trap Setup at ~38.2% correction and target the **3rd leg of the original measured move**

This pattern is frequent on **Gold and Oil**.

### Double Up & Double Down

An alternative measurement of the same impulse using **Fibonacci retracement** instead of expansion. **Requires tick charts.**

- **A → B:** Same impulse as the traditional measured move (starts one side of EMA, ends opposite side)
- Apply Fibonacci retracement to A-B
- **Double Up (bullish) / Double Down (bearish):** The retracement levels project continuation targets
- A **triple** (3rd occurrence) creates a strong S/R line

### Combining Measured Move + Double Up/Down
~**70%** of the time, the 3rd leg target of the measured move and the Double Up/Down level will coincide (cluster). This confluence is a strong target confirmation. When they align, the level is high-conviction.

---

## Hidden Channel (Rotation Channel)

A channel pattern that forms after a target is hit and new momentum begins.

### Context
Price has reached a significant level: a measured move target, double top/bottom, a daily target, a cluster, or another key level. A reaction occurs and price begins rotating within two parallel lines.

### Structure
- Two **parallel** lines containing the price rotation (precision required — lines must not be skewed)
- The channel is "hidden" because it is **unconfirmed** until both sides are tested
- Look for a clean impulse within the channel to define the boundaries

### Trading Rules

1. **Wait for both sides to be tested.** If only one side of the channel is tested, do not enter — the channel is still hidden/unconfirmed.
2. **Entry:** Look for a signal candle with proper EMA context:
   - The signal candle must **cross the EMA** and react to the channel boundary — being merely "close to" the edge without EMA relationship is insufficient
   - For bearish setups: signal candle below EMA or price strongly crossing EMA downward
   - For bullish setups: signal candle above EMA or price strongly crossing EMA upward
3. **Target:** Use the measured move projected from the channel. Settle the trade **a few pips/ticks before** the projected target — other participants with similar analysis will exit earlier.
4. Ideal case: the measured move target aligns exactly with the opposite channel boundary — this confirms analysis quality.
5. **Do not adjust channel lines after the fact** to fit the narrative. If the channel does not work, accept it — do not fabricate the story.

---

## Battle Zones

A swing-based S/R classification system. **Never carry Battle Zones across days** — each trading day starts fresh.

### Zone Types

| Type | Definition |
|------|------------|
| **Resistance** | Range where counter-trend traders gained control (e.g., sellers pushed price down from this zone in an uptrend) |
| **Support** | Range where trend-direction traders defended (e.g., buyers held price at this zone in an uptrend) |
| **Untested** | A swing that produced a strong reaction but has **not been retested** — strongest conviction |
| **Verified** | A zone retested by price **at least once** — confirmed but slightly weaker |
| **Turncoat** | A zone where the character is changing — former support becoming resistance, or vice versa |
| **Battle Zone** | A range where **multiple alternating swings** cluster (buyers and sellers trading control back and forth). Must have clear alternating impulses from both sides — buyers push, sellers push, buyers push again, sellers push again. One or two reactions do not qualify — those are simple reversal lines. |

### Battle Zone Identification
- Mark from the **outermost wicks** of the highest to lowest swing in the cluster
- Battle zones typically form at **50%** or **⅓** of a significant move — use these proportions as a rough guide for where to expect them
- Analyze on a **clean chart** — no Fibonacci overlays during BZ identification

### Rules
- If a battle zone is **crossed in the opposite direction** (e.g., market was bearish but buyers push through the zone), the battle zone is **void** — look for opportunities in the new direction
- **Each retest weakens the zone** — untested zones are strongest, zones retested 3+ times are likely to break
- BZ invalidation is **not the same as a structure change** — structure change happens faster/sooner; BZ invalidation is a separate, bigger-picture concept
- Do not slide the Battle Zone lower/higher as price makes new extremes — a single reaction at a new level does not create a new BZ
- Battle zones interact with all other PAC tools — a signal candle at a battle zone boundary, aligned with trend and Fibonacci levels, is a high-probability setup

---

## Spike & Move Patterns

Patterns that form after a sudden, sharp price movement (spike). The spike is a set of candles — **3, 4, 5, 8, 10, 12 or more** — what matters is the **speed and magnitude** of the move, not the candle count. Spikes are often tied to news events and occur nearly every day in current markets.

> All examples below are described from the bullish perspective. Mirror for bearish.

### Spike & Channel

A spike followed by a **channel continuing in the spike's direction**. This is the primary framework for "playing the 2nd leg" using measured-move logic.

**Points:**
- **A** = Open/base of the spike
- **A'** = Top of the spike (where the channel begins)
- **B** = Highest point reached in the rotation channel
- **C** = 50% Fibonacci retracement of the full A-B range

**Rules:**
1. Wait for a pullback to the **50% Fib of A-B** (point C)
2. Price must **react** at the 50% level — if even a **wick** penetrates past 50%, the entire setup is invalidated. A wick past 50% counts as invalidation.
3. **Target (D):** Measured move from A-B-C (100% Fibonacci expansion / 1:1 move)
4. If price within the channel reaches the **138.2% Fib of A-A'** (spike impulse), expect exhaustion — the move is likely complete
5. If price begins correcting before 138.2% but does **not break** the 50% level, and buyers reappear:
   - Wait for price to get **above the EMA** (mandatory)
   - A trendline (line of least resistance) can provide additional confirmation
   - Entry opportunity with target at 138.2% Fib of A-A'

> This setup is often "ungrateful" — price frequently reaches 138.2% within the channel before a clean pullback entry materializes. Do NOT enter at the upper edge of the rotation channel. Best approach: wait patiently for a correction; if it does not come, skip it.

### Spike & Flag ⭐ (Preferred Setup)

A spike followed by a **channel in the opposite direction** (a flag — price drifts against the spike).

**Points:**
- **A** = Open/base of the spike
- **B** = Highest point before the flag begins
- **C** = 50% Fibonacci retracement of A-B

**Rules:**
1. **Do not** enter during the flag — do not chase the counter-trend drift
2. Wait for a pullback to 50% Fib of A-B (point C). If even a **wick** closes past the 50% level, the setup is invalidated — wick penetration counts as invalidation.
3. Ideal: flag ends at or before the 38.2% retracement level
4. **Target (D):** Measured move from A-B-C
5. The **trigger** is an impulsive break of the flag's upper channel line:
   - The candle **body** must close outside the channel (not just a wick)
   - Alternating candles (green-red-green-red) are **NOT** a valid breakout — the breakout must be impulsive, consecutive same-direction candles
   - A signal candle at the breakout adds confidence
   - If you miss the breakout entry, there is often a retest of the broken channel line — enter on the retest
   - **Order type on breakout:** Limit order on candle close (not market order); do not expect a deep pullback after the flag breaks
6. If price has not reached the spike high (B), you can either use B as a conservative target or go with the full measured move
7. **Spike & Flag tends to skip corrections**, especially on Gold, Oil, NASDAQ, and DAX — once the flag breaks, the move can be fast and one-directional. On EUR/USD and currency pairs, corrections are somewhat more likely.

### Spike & Range

A spike followed by a **sideways range** (no channel, no flag — just consolidation).

> **Do not trade this pattern.** Multi-year statistics show only ~+2,200 units of profit over hundreds of trades — the edge is negligible. Do not fabricate a story by trying to see a flag inside a range. If it looks sideways, it is sideways — skip it.

---

## Trend or Range Day Classification

The classification of the current session as a Trend Day or Range Day is the starting point for all trade decisions. **Always start fresh** — never carry analysis from the previous day.

### Classification Method

Draw a **wide rotation channel** across the session's price action:
1. If you **can** identify a clear rotation channel showing a broad price rotation with a trend direction → **Trend Day**
2. If you **cannot** find a clear rotation channel → **Range Day** or mixed-trend day
3. Mixed-trend days exist (down → up → down) — still try to find the trend first
4. Define the measured move → verify it aligns with the wide rotation channel edges
5. If you cannot find a measured move → consider sitting out

> **Repo note:** This section extends PAC with MMD cloud confirmation — see the [MMD Integration](#mmd-integration) section below for an additional classification layer using MMD clouds. The method above (rotation channels) is Paweł's actual classification method from the source videos.

---

### Trend Day Workflow

1. **Define direction + wide rotation channel** — find a broad rotational channel aligned with price direction
2. **Define the large measured move** — verify it aligns with the rotation channel edges; check for Double Down/Up overlap and 3rd-leg clustering
3. **Define the market target** — always look for a measured move; without one, you cannot define a target
4. **Mark Reversal Lines and Battle Zones** — where did sellers/buyers react? Were reactions strong or weak?
5. **Assess micro-rotation** — is micro-rotation clean and reliable today? If not, use the fallback chain:
   - Check **Two-Try Rule** setups
   - Check **strength setups**
   - Check correction quality (to EMA, with double-attempt, trap/fail patterns)
6. **Look for entry setups** — only after Steps 1–5 are complete

---

### Trend Day Setups

#### 1. Trap Setup (To-Try Trap)

**Context:** Appears during corrections within a trend move, typically after an impulse or strength move.

**Structure:**
- Impulse → correction → **two-legged pullback** (Two-Try Rule applied to corrections)
- **First try:** Counter-trend traders attempt to extend the correction → weak trend-continuation reaction
- **Second try:** Counter-trend traders attempt again → they **fail** → strong trend-continuation reaction follows

**Entry criteria:**
- Correction zone starts from **38.2% Fibonacci** of the preceding impulse
- The first impulsive reaction after the 2nd failed attempt is sufficient for entry (if aligned with micro-rotation)
- If missed: wait for pullback to EMA + signal candle

**Confluence elements:** Rotation channel, trendline, Battle Zone, Reversal Line, EMA

**Target:** Measured move target or 3rd leg target

**Key characteristic:** The trap move typically sweeps a recent swing high/low to collect stops before continuing in the trend direction.

#### 2. Fail Setup

**Context:** Similar to Trap but with a **deeper correction**.

**Structure:**
- Correction **must pass the 38.2% level** — if it does not reach 38.2%, this is NOT a Fail setup; do not force it
- Correction can be very deep — up to **61.8% or even near the impulse origin**
- Counter-trend traders make a deep first attempt → brief trend response → counter-trend traders try a second time → they **fail to reach the same level** as the first attempt → trend traders react

**Entry criteria:**
- Correction must reach at least 38.2% (hard requirement)
- Second attempt must fail to reach the first attempt's level
- Entry on the reaction after the second failure

**Key principle:** Without enough correction depth, there is no "spring" to generate profit. Shallow corrections do not qualify for Fail setups.

**Target:** Measured move from the failure point

#### 3. To-Try Pullback Trap (Extended Measured Move)

**Context:** The standard measured move target (100%) has been **overshot** — price continued past D for several candles without returning. This is NOT a slight overshoot (one candle past = normal MM completion).

**Structure:**
1. Price overshoots the 100% measured move by several candles
2. Calculate **extended measured move** using external Fibonacci: same A-B-C points → target extends to **138.2% or 161.8%**
3. Price should stop within the 138–161.8% range
4. After the extended move completes: calculate correction from the **entire move** (not just original MM)
5. Correction zone at ~**38.2%** — even a slight wick past is acceptable, but not a huge overshoot
6. Wait for a **Trap Setup** (two-legged pullback) within this correction zone
7. Target = **3rd leg of the original measured move** (not the extended one)

**Instrument note:** Frequent on **Gold and Oil**.

---

### Range Day Workflow

1. **Define the trading range:**
   - Find the price level with the **most reactions** (opens, closes, highs, lows, candle crossings)
   - Reactions must be **roughly balanced** top and bottom (not 8 reactions top, 2 bottom)
   - If you see **5+ expansions** (breakouts and returns), your range is drawn too narrow — widen it
   - More than 4 unreactive expansions → range is poorly defined, redraw
2. **Define the non-trade zone** — the center/core of the range where price is attracted; do not trade here
3. **Check expansions** — verify that breakouts from the range react at expansion levels; reactive expansions confirm the range definition
4. **Apply Two-Try Rule to breakouts**
5. **Check micro-rotation** — is a rotational channel forming toward the target?
6. **Trendlines** — in range days, trendlines are blocking lines; wait for price to cross them before entering

**Counting rule:** Count breakout attempts starting from **08:00 AM European session** (Polish time). Overnight Asian session attempts do not count. After **4–5 breakout-and-return cycles** within the day → be very cautious with the next one.

> Markets move sideways over 60% of the time. Range days are the most frequent trading day type.

---

### Range Day Setups

#### 4. Range Trap (Two-Try Breakout Trap)

**Context:** A defined trading range with a non-trade zone at center.

**Setup:**
- Price approaches one boundary and makes a **false breakout** (trap) beyond it, then snaps back inside
- **Two-Try Rule:** First breakout attempt → second breakout attempt → **both fail**
- The "trap" = traders who believed a new trend was starting are now trapped
- After the 2nd failed breakout: price must **cross the trendline** that was containing it

**Entry:** After the false breakout candle closes back inside the range boundary — enter toward the opposite range boundary. Must see clear buyer/seller reaction after the second failed attempt.

**Confluence:** If a micro-rotation channel is forming toward the target → extra confluence (preferred scenario).

**Target:** Opposite range boundary (or slightly before it).

**Stop:** Just beyond the false breakout extreme.

**Note:** Count breakout attempts from 08:00 AM. After multiple failed attempts at a boundary, the trap probability increases.

#### 5. Range Fail

**Context:** Price approaches a range boundary.

**Setup:**
- Breakout from the range must **reach the Fibonacci expansion level** — if it does not reach expansion, do not trade (this confirms the range definition is correct)
- Two-Try at the expansion: buyers/sellers try to extend → fail → **do not reach the same level** on the second try
- Reaction from the opposite side → enter

**Entry:** When reversal signals appear as the second attempt fails at or near the expansion level — enter toward opposite boundary.

**Target:** Return to trading range, then potentially the opposite edge.

**Key rule:** The fail is subtler than the trap — the push may lose momentum and reverse before fully testing the boundary extreme.

---

### SL/TP Framework

- **TP** = the defined measured move target (primary) or 3rd leg projection
- **Ideal SL** = above/below the zone that started the setup
- If R:R does not allow ideal SL → tighter SL is acceptable when timing/precision is good
- **Define the target first**, then fit the SL to maintain acceptable R:R
- Always settle a **few pips/ticks before** the projected target

---

## MMD Integration

> **Repo note:** This section extends PAC with MMD (Magic Moving Averages) cloud analysis. MMD is a separate strategy in this repo — see `MMD/MMD_CLOUDS.md` for the full spec. The integration below is the repo owner's own synthesis, not part of Paweł's original PAC curriculum.

### Day Classification (MMD-Enhanced)

Use Paweł's rotation channel method as the primary classifier. MMD cloud stacking provides objective confirmation:

| Cloud Configuration | Signal |
|---------------------|--------|
| Orange (48) above Blue (288), all aligned | Trend Day confirmed |
| Orange/Blue compressed or interleaved (not clearly stacked) | Range Day signal |
| Correction stacking (CORR BULL / CORR BEAR) | Mixed day — apply highest-conviction setups only |

### Trade Direction Filter

Cloud stacking direction adds a timeframe layer on top of PAC's EMA 21 / SMA 61 filter:

| Cloud Stacking | Implication |
|----------------|-------------|
| Orange above Blue | Bullish signal candles preferred |
| Orange below Blue | Bearish signal candles preferred |
| Clouds and EMA 21 disagree | Reduce conviction or skip the trade |

### Target Obstacle Filter

Before committing to a PAC measured move target, check whether an MMD cloud sits between entry and target:
- **Cloud in the path → conservative:** Target the near edge of the cloud
- **Cloud in the path → patient:** Require a clean cloud break before entering (wait for confirmation)
- **Target aligns with cloud boundary:** High-conviction confluence

### Battle Zone + Cloud Confluence

A PAC battle zone that coincides with an MMD cloud boundary (especially Orange or Blue cloud edge) = highest-conviction S/R. Treat these as priority setups.

### Entry Timing — "Na Maćka" Alignment

When a PAC signal candle forms at a cloud boundary and the Red (12) cloud has just crossed the Orange (48) cloud in the same direction → double trigger. Both systems are firing simultaneously — this is the highest-quality entry combination.

---

## Trade Execution Checklist

Before entering any trade, confirm:

1. **Day Type:** Classify as Trend Day or Range Day using the rotation channel method (MMD confirmation optional)
2. **Direction:** Trend and sentiment align (MAs, Elliott Wave count, trendlines, cloud stacking)
3. **Context:** Entry point sits at a confluence zone (Fibonacci cluster, battle zone, reversal line, session box boundary, trendline, MA)
4. **Signal Candle:** A valid signal candle has formed at the confluence zone — on the correct side of EMA 21 (bullish above, bearish below)
5. **D1 Bias:** Intraday direction aligns with the OHLC promo zone bias
6. **Session:** Current session supports the trade (not in a dead zone between sessions)
7. **Chart Type:** Entry is confirmed on tick or range chart (not M5 alone)
8. **Setup Name:** The trade matches one of the five named setups (Trap, Fail, To-Try Pullback Trap, Range Trap, Range Fail) or a Spike & Flag / Spike & Channel setup
9. **Target:** A clear, measurable target exists (measured move, Fibonacci level, cluster, opposite range boundary)
10. **Settlement:** Place TP a few pips/ticks before the target to account for spread, slippage, and other participants exiting early
