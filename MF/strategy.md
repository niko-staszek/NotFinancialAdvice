# Money Flow (MF)

A swing-trading strategy that aligns entries with institutional positioning. Large-speculator flow from COT reports sets the directional bias; the Money Flow indicator confirms capital direction per currency; technical analysis (price action, EMAs, Fibonacci, volume levels) times the entry.

**Instructor:** Paweł (same community / methodology family as PAC and PSND)

**Source material:** [3-part video series](links.md) — Money Flow 1 (technicals), Money Flow 2 (indicators), Money Flow 3 (COT reports + news filter).

**Primary timeframe:** H4 for analysis. D1 for context (major S/R, HTF targets). H1 for precise entries.

**Trade tempo:** 1–3 trades per week. Holding period: several days to 1–2 weeks. Low position sizing, wide stops, hands-off.

---

## Instruments

### Pairs to trade

The strategy is built for **exotic / minor cross pairs** where COT divergences between base and quote currencies produce the cleanest swing setups.

| Pair type | Examples | Notes |
|-----------|----------|-------|
| Minors (primary) | EURJPY, EURNZD, GBPNZD, AUDJPY, EURAUD, NZDJPY | Most pronounced COT spread; cleanest swing moves |
| Majors (secondary) | EURUSD, GBPUSD, USDJPY, USDCAD, AUDUSD | Tradable but COT edge thinner; **only** pairs where Volume Edge levels work |
| Commodity currencies | USDMXN (Mexican peso), USDZAR | High COT activity; watch for risk-on/off sensitivity |

### Other instruments

| Symbol | Use |
|--------|-----|
| XAUUSD (Gold) | Risk-off hedge during geopolitical stress; volume levels work |
| USOIL / WTI | Volume levels work; COT available for CL futures |
| Indices (US500, US30, NAS100) | Volume Edge levels work; COT via ES/YM/NQ futures |

### Instruments that don't work

- **Minor cross pairs do NOT have Volume Edge data** (institutional limit orders). Those levels only populate on majors + indices + gold + oil.
- Crypto: not part of the strategy (no COT report coverage for retail FX brokers).

---

## Timeframe & Charts

**D1 (context):** major S/R, HTF targets, higher-timeframe trend. Used for sanity: if we'd be entering long near a D1 resistance, reduce size or skip.

**H4 (primary analysis):** trendlines, S/R zones, EMA/SMA cross, Fibonacci pullback zone, market structure, Point of Control (daily). All setups are identified here.

**H1 (entry precision):** refine entry timing. Swing marking, signal candle, lower-fractal structure shift confirming the H4 setup.

No tick or range charts required (unlike PAC).

---

## Data Sources

### COT (Commitment of Traders) reports

Published weekly by the U.S. CFTC (Friday release, covering positioning as of Tuesday close). **Data is ~1 week delayed** — acceptable because we trade swings that persist for weeks.

**Three groups in each report:**

| Group | Who | Use |
|-------|-----|-----|
| Commercials (Hedgers) | Goldman Sachs, JPM, Morgan Stanley, Citi, Bank of America, producers | Ignore — hedging flow, not directional |
| **Non-Commercials (Large Speculators)** | Bridgewater, Man Group, Elliott Management, Citadel, hedge funds, prop firms | **Primary signal** — these create the trends we follow |
| Small Speculators | Retail via broker aggregation (including us) | Ignore, or use as contrarian indicator |

**Sources:**
- [barchart.com](https://www.barchart.com) → Currencies → Commitment of Traders → Non-Commercials → "View Summary" (pre-built currency pairs available)
- Futures COT → pair currencies manually (base currency long + quote currency short → go long the pair)
- Community tool "Kintel" — aggregated view (currently being rebuilt)

### Money Flow indicator

A proprietary indicator in the community's tooling. Displays **7 colored lines**, one per G7 currency:

| Currency | Color |
|----------|-------|
| EUR | Blue |
| USD | White |
| GBP | Magenta / Pink |
| JPY | Yellow |
| CHF | Green |
| AUD | Red |
| NZD | Orange |

**Reading the indicator:**
- **Zero line** divides inflow from outflow. Above zero = capital flowing INTO that currency. Below zero = capital flowing OUT.
- **Pair interpretation:** base-currency line above zero + quote-currency line below zero → pair should rise.
- **Crossover between two currency lines** = primary regime-change signal (more important than zero-line crossings alone).
- **Extreme highs / extreme lows** of a currency's line = reversal candidate.

Observed on **H1 or H4** (not lower — too noisy).

### Volume Edge (institutional pending-order levels)

Another proprietary indicator. Horizontal price levels representing pending orders of one major institution (~5% of total FX market capital).

- Levels appear as colored horizontal lines; color indicates the session hour when the order was placed.
- Lines that extend to the right = still active (not yet filled).
- Lines that stop being drawn = filled / cancelled.
- **Works ONLY on:** majors + indices + gold + oil. Does NOT populate for minor crosses.

Alternative (free): on TradingView use "Fixed Range Volume Profile" or "Session Volume Profile" built-ins. Or third-party: clusterdelta.com (paid).

---

## Technical Components

### 1. Swings

A swing high / swing low is the reference point for S/R, structure, and line-drawing.

**Classical rule (strong swing):**
- Impulse move → **two candles** in the opposite direction
- Body sizes roughly equal
- Mark the extreme wick as the swing point

**Weak swing (single-candle reversal):**
- Impulse move → single candle in opposite direction, but with visibly larger body than the preceding move
- If the next candle goes back with the original trend, mark as a swing anyway — the rejection was decisive

**Marking rule:** Alternate swing highs and swing lows. If two candidate swing highs occur without a swing low between them, keep only the highest. Never mark two consecutive swings of the same type.

### 2. Trendlines

**First-two-swings rule:** Draw the trendline through the first two swings of the move. Use wicks OR bodies — whichever gives more touch points. Mixing (wick on one, body on another) is acceptable.

**Rotational channel:** Once trendline exists, draw a parallel on the opposite side. Channel adds context — price rejects both sides similarly.

**Overshoot / undershoot:** A candle wick piercing the channel without body close outside is not a breach. Symmetric overshoots (one side → expect similar on the other).

**Break of trendline = first warning.** Retest of the broken line from the other side → trend-change confirmation.

### 3. Support / Resistance zones

Drawn from swing wicks + bodies (the range between swing body and swing wick top/bottom).

**Validity grows with retests.** A fresh zone with one reaction is "potential." After 2–3 reactions it's "strong." After a break, it flips polarity (resistance becomes support and vice versa) — retest of the broken zone from the new side is a high-probability entry.

**Staircase pattern:** price steps from one zone to the next — reaction → break → retest → continuation. Very common on H4 uptrends/downtrends.

### 4. EMA 21 + SMA 66

Both on the same chart. H4 is the main timeframe for this pair; D1 also informative.

**Regime-change signal:** when EMA 21 crosses SMA 66 → first warning that trend may be shifting.
- EMA 21 crossing SMA 66 upward (after a downtrend) → potential bullish reversal
- EMA 21 crossing SMA 66 downward (after an uptrend) → potential bearish reversal

**Reactive zone:** the **zone between EMA 21 and SMA 66** (widen with a small buffer) acts as S/R after a cross. Price that broke out of the cross zone often returns to retest it → reaction → continuation.

**Caveat:** the cross is an early warning, not a standalone entry trigger. Large impulse moves sometimes make the cross lag the actual reversal by bars.

### 5. Fibonacci pullback zone

**The 38.2% – 61.8% retracement** of the prior impulse is the entry zone (same as PAC).

- Draw Fib from swing low to swing high (for an uptrend; reverse for downtrend)
- **61.8% is the preferred entry level** (reactions are often pinpoint)
- Confluent with EMA/SMA cross zone, trendline, S/R, or POC → high-probability entry

### 6. Market structure (BoS / CHoCH)

**Break of Structure (BoS):** in an uptrend, price breaks the prior swing high. In a downtrend, breaks the prior swing low. Confirms trend continuation.

**Change of Character (CHoCH):** in an uptrend, price breaks the prior swing LOW (first higher-low that fails). Confirms trend reversal — or at least meaningful pause.

Mark these as vertical annotations on H4. A CHoCH against your COT bias = reduce size or skip; a BoS with COT bias = confidence boost.

### 7. Point of Control (POC) — daily volume profile

The price level at which the most volume traded during a given session (typically D1).

**Usable POC (trade-relevant):**
- Must be preceded by a **strong impulse** (trending day). If the day was a range, the POC reflects only consolidation and is useless.
- Draw a small zone around the POC (not a single line — wick reactions often overshoot).
- Use as a reaction level on retest.

**Timeframe weighting:**
- D1 POC: most useful (primary).
- W1 POC: useful on retests.
- H1 POC: noise — ignore.
- Monthly POC: rarely useful.

### 8. Volume Edge levels

Institutional pending-order levels (covered above). Reaction levels — not entries themselves, but confluence.

Active line (drawn right) that confluents with POC, a Fib level, or the EMA/SMA cross zone → strong reaction candidate.

**Only on majors + indices + gold + oil.** Skip for minor crosses.

---

## Entry Rules (composition)

A Money Flow entry requires **alignment across three axes**: flow (COT + MF indicator), price (technical confluence), and macro (no imminent tier-1 event).

### Step 1 — Flow bias (required)

1. Pull latest COT Non-Commercials report.
2. Identify a currency with **net position ≥ ±70,000 contracts** (≥50k acceptable as a looser screen; <50k → skip, likely range-bound).
3. Identify a second currency on the opposite side (≤ −50k while the first is ≥ +50k, or vice versa).
4. Form the pair. Base currency (first in the cross) determines direction: base long + quote short → buy the pair.
5. Confirm on the Money Flow indicator: base currency line above zero, quote currency line below zero. Ideally the two lines have recently crossed (crossover = regime-change signal).

**If COT or MF disagrees → no trade.** Both must confirm.

### Step 2 — Technical confluence (required)

On H4:

1. Determine trend direction on the pair (market structure, EMA/SMA slope).
2. Price must be pulling back into a **confluence zone** that includes at least 2 of:
   - 38.2%–61.8% Fibonacci retracement of the current impulse (preferred: 61.8%)
   - EMA 21 / SMA 66 cross zone
   - A respected S/R zone
   - A D1 POC (with strong impulse origin)
   - A trendline touchpoint
   - A Volume Edge active level (majors / indices / metals / oil only)
3. Structure must not have just put in a CHoCH against the intended direction.

### Step 3 — Precise entry on H1

1. Drop to H1.
2. Wait for a rejection signal at the confluence zone: signal candle (wick rejection), H1 BoS in trade direction, or H1 CHoCH confirming the reversal from the pullback.
3. Enter on candle close.

### Step 4 — News filter (required)

1. Check the macro calendar for both currencies in the pair.
2. If **high-impact news** is due within 24 hours (interest rate decision, CPI, PPI, NFP, GDP, PMI, major geopolitical announcement) → skip or reduce size to ¼ normal.
3. Special case — central bank decision within 24h: always skip.

---

## Stop Loss & Targets

### Stop loss

Swing-based, not ATR-based:

- **Long entry:** stop below the most recent H4 swing low that structurally supports the setup, plus a small buffer (0.1–0.3 × ATR).
- **Short entry:** mirror — above recent H4 swing high.
- **Wider than intraday strategies by design.** Typical SL distance: 50–200 pips for FX majors, 300–600 for exotics, 1000+ pips for gold.

### Targets

Two-tier:

- **T1 (partial close, ~50%):** next major H4 S/R zone in trade direction, OR 1R, whichever comes first.
- **T2 (runner, remainder):** D1 target — next major D1 S/R, OR PDH/PDL, OR opposite end of a well-defined range. Move stop to breakeven after T1.

**Expected R:R at full target:** 3–5R on average. Individual trades may reach 8–10R on strong trend extensions.

### Exit triggers (pre-target)

Exit the full position, or at least the runner, if any of the following fires:

- H4 **EMA 21 crosses SMA 66 against** your position
- H4 **CHoCH against** your position (after a BoS in your favor first)
- Weekly COT shows **net position change ≥ 50,000 contracts against** your bias on either currency
- Money Flow indicator shows **line-cross against** your position on H1/H4
- Approaching tier-1 news within 24h — close or tighten stop

---

## Position Sizing & Risk

- **Risk per trade:** ≤ 1% of account equity on the initial stop distance.
- **Max concurrent open positions:** 3. Keep portfolio heat ≤ 3% total risk.
- **Correlation cap:** no two positions in the same base or quote currency in the same direction (avoid doubling effective exposure). Example: long EURUSD + long EURJPY = both long EUR → count as one, use half size on each.
- **Weekly cadence:** 1–3 trades per week target. If no clean COT+MF+technical alignment is found, no trade. Do not force.

---

## Key Assumptions (for falsification)

The strategy is load-bearing on five hypotheses. Any of these failing invalidates a substantial part of the approach:

1. **COT non-commercials' positioning leads price by days to weeks.** Testable: correlation between weekly COT net-position changes and subsequent 1-week and 2-week returns on the corresponding pair.
2. **The 70k contract threshold separates tradeable trends from range regimes.** Testable: split COT-history into buckets (<30k, 30-70k, >70k) and compare subsequent-week realized volatility and directional persistence.
3. **EMA 21 / SMA 66 cross zone reacts as S/R.** Testable: measure mean forward return conditional on price revisiting the cross zone after a cross.
4. **D1 POC reacts as S/R only when preceded by a strong impulse day.** Testable: classify each D1 POC as (impulse / range) and compare reaction rates on H4 retests.
5. **Fibonacci 61.8% retracement has higher reaction probability than 38.2% / 50%.** Testable: for each swing on H4, measure reaction magnitude at each Fib level.

Each hypothesis can be walk-forward tested on 10 years of D1 + H4 data independently, and the composite strategy can be tested by enforcing all rules and measuring out-of-sample PF and drawdown.

---

## Differences from PAC

| Aspect | PAC | MF |
|--------|-----|-----|
| Style | Intraday (M5 + tick/range) | Swing (D1 / H4 / H1) |
| Hold time | Minutes to hours | Days to 1–2 weeks |
| Primary bias source | Price action (pattern + session) | COT + Money Flow indicator |
| Chart type | Tick / range mandatory for entries | Time-based only |
| Trade frequency | Multiple per day | 1–3 per week |
| Stop distance | Tight (structure-based, minutes) | Wide (swing-based, days) |
| News filter | Intraday avoidance (kill zones) | 24h window around tier-1 |
| Pairs | Majors + metals + indices | Minors preferred; majors secondary |

**Overlap:** Fibonacci 38.2–61.8% pullback zone is identical. Swing definition and market structure (BoS/CHoCH) shared. EMA 21 used in both (PAC as signal-candle filter; MF paired with SMA 66 as cross zone).

---

## Not Covered (out of scope for v1)

- The exact construction of the proprietary Money Flow indicator (community tooling). For testing from scratch, the closest public analogue is a currency-strength meter combining relative performance of each G7 currency vs. a basket.
- The exact construction of Volume Edge (institutional order data). For testing, skip this component or substitute with TradingView's Session Volume Profile for POC purposes (covers point 7 but not point 8).
- Kintel (the community's COT + news dashboard). Use barchart.com directly for COT ingestion.
- Manual fundamental analysis beyond the tier-1-news filter.
