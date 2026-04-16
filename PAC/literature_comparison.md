# PAC Strategy — Comparison with Established Trading Literature

## Overview

PAC (Price Action Cycle) is an intraday M5/tick-chart strategy taught by a Polish instructor named Paweł (community: "Cykl Rotacyjny Ceny"). It combines candlestick signal recognition, a simplified Elliott Wave count, Fibonacci extensions/expansions, session-based bias filtering, measured moves (AB=CD), and five named setups (Trap, Fail, To-Try Pullback Trap, Range Trap, Range Fail). The strategy is presented as a self-contained system for forex, gold, indices, and crypto.

PAC draws — sometimes explicitly, sometimes without attribution — from Wyckoff's accumulation/distribution phases, Elliott Wave Theory, classical Fibonacci analysis, harmonic pattern concepts (AB=CD), ICT's session-based dealing range framework, and Al Brooks's price-action methodology. The question is how faithfully it represents these sources, what it simplifies, and whether the simplifications help or hurt.

---

## Component-by-Component Comparison

### 1. Signal Candle & Gap Candle

**Closest established concept:** Japanese candlestick patterns (Steve Nison, 1991). The signal candle is a pin bar / hammer / shooting star. The gap candle maps loosely to a marubozu or strong-bodied candle with directional conviction.

**Alignment:** The signal candle definition — prominent wick rejecting one direction, small wick on the other — is a textbook pin bar. Requiring confluence (MA, Fibonacci, trendline) before acting on it is standard practice in Nison's work and Al Brooks's methodology.

**Simplification / Loss:** Classical candlestick analysis specifies wick-to-body ratios (pin bar wick typically ≥ 2× body), minimum candle size relative to recent range, and context requirements (prior trend direction matters). PAC explicitly rejects fixed ratios — Paweł says assessment is "optical." This makes the signal candle unfalsifiable: any candle with a noticeable wick qualifies, which on M5 or tick charts is 30–40% of all candles (as the Opus review notes). The established literature's ratio rules exist precisely to filter noise that visual assessment lets through.

**Gap candle lines** (horizontal S/R from wick tips of strong directional candles) resemble Wyckoff's reaction levels drawn from swing points, but without Wyckoff's requirement that the level be validated by subsequent volume behaviour. PAC provides no invalidation criteria for these lines — a gap the literature would address through concepts like "level expiry after N failed tests."

**PAC addition:** The directional EMA filter (bullish signal candle must close above EMA 21) is not part of classical candlestick analysis — it is a sensible addition that reduces noise.

### 2. Trendlines (3-Type System)

**Closest established concept:** Classical trendline analysis (Edwards & Magee, *Technical Analysis of Stock Trends*, 1948). The major/minor distinction maps to Edwards & Magee's primary vs. secondary trends (itself derived from Dow Theory).

**Alignment:** Drawing trendlines from swing-point wicks, distinguishing between primary and secondary trends, and using channel parallels are all textbook technique. The frequency guidance (major: 1–2/day, minor: 3–5/day, micro: 15–20+/day) is a useful operational heuristic not typically spelled out in classical texts.

**Simplification / Loss:** Classical analysis provides explicit break rules (e.g., a close beyond the trendline by a filter percentage, or a break confirmed by volume). PAC provides none — no rule for when a trendline is broken vs. merely penetrated. Al Brooks dedicates entire chapters to the distinction between a trendline break (momentum shift) and a trendline overshoot (trapped traders). PAC's silence on this point is a significant gap.

**Contradiction:** Paweł says "don't skip intermediate swings" when connecting trendline points — this is good practice but not always possible in fast markets, and classical analysts regularly anchor trendlines to non-adjacent significant swings.

### 3. Moving Averages (EMA 21 / SMA 61)

**Closest established concept:** Dual-MA crossover systems are as old as computerized trading. The 21 EMA is widely used (approximates one trading month). The 61 SMA is less standard — more commonly 50 SMA or 55 EMA (Fibonacci-adjacent) in established literature.

**Alignment:** The sentiment rules (price above both = bullish, below both = bearish, between = transitional) are a clean codification of how most MA-based traders operate. The "dynamic cross" concept (sharp cross creates a retestable zone) is well-documented in moving average theory.

**PAC addition:** The specific requirement that a dynamic cross must be impulsive (1–2 candles, not a 5-candle meander) is a useful operational filter not typically codified in MA literature. The Opus review correctly notes this is the best-defined component of PAC.

### 4. Fibonacci (Extensions, Expansions, Clusters, Spike 50% Rule)

**Closest established concept:** Classical Fibonacci retracement/extension analysis, widely codified by traders like Joe DiNapoli (*Trading with DiNapoli Levels*, 1998) and Carolyn Boroden (*Fibonacci Trading*, 2008).

**Alignment:** PAC's use of 38.2%, 61.8%, 100%, 138.2%, and 161.8% is broadly standard. The cluster concept (multiple Fib levels converging within ~5 pips) is well-established — Boroden calls these "clusters" using the same term, and DiNapoli calls them "confluence." The Spike 50% invalidation rule (even a wick past 50% kills the setup) mirrors the AB=CD pattern's 50% rule used in harmonic trading.

**Simplification / Loss:** PAC drops 23.6% and 78.6% — both are significant in classical analysis. The 78.6% level (square root of 61.8%) is central to Scott Carney's harmonic patterns (the Bat pattern's D-point). By omitting it, PAC loses the ability to distinguish between shallow corrections (23.6–38.2%) and deep corrections (61.8–78.6%). Everything outside 38.2–61.8% is simply "not a valid correction" — a coarser filter than the literature supports.

**Note:** The gap analysis found that 127.2% was erroneously added to strategy.md and never appears in Paweł's teaching. The established literature does use 127.2% extensively (it's key in Gartley and Butterfly patterns). Its absence from PAC is consistent with PAC's simpler Fibonacci toolkit.

### 5. Elliott Wave (PAC's Simplified Counting)

**Closest established concept:** Elliott Wave Theory (R.N. Elliott, 1938; expanded by Robert Prechter and A.J. Frost in *Elliott Wave Principle*, 1978).

**Where PAC departs radically:** Classical Elliott Wave has three inviolable rules: (1) Wave 2 never retraces beyond Wave 1's origin, (2) Wave 3 is never the shortest impulse wave, (3) Wave 4 never enters Wave 1's price territory. These rules make wave counts falsifiable — if a proposed count violates them, it is wrong.

PAC removes all three rules. Paweł counts "3 to 8 impulses" without labelling corrective waves (A-B-C), without a degree hierarchy, and without any formal invalidation criteria. This is not simplified Elliott Wave — it is a different tool that borrows Elliott's vocabulary. Classical Elliott practitioners would not recognize PAC's wave count as valid Elliott analysis.

**What is lost:** The entire falsifiability framework. In classical Elliott, a failed Wave 3 projection forces a recount — this discipline prevents confirmation bias. In PAC, you can always recount impulses to fit the current narrative because there are no rules to violate.

**What is gained:** Usability. Classical Elliott Wave on M5 is extremely difficult — academic studies (e.g., Poser, *Technical Analysis — The Complete Resource for Financial Market Technicians*) note that Elliott counts below daily timeframes are unreliable due to noise. PAC's approach of simply asking "how many impulse moves have occurred?" is pragmatically useful as a trend-age gauge even if it is not Elliott Wave.

**Honest assessment:** PAC uses Elliott's name for credibility but practices a different, simpler form of momentum counting.

### 6. Measured Move + Double Up/Down

**Closest established concept:** The AB=CD pattern (H.M. Gartley, 1932; formalized by Scott Carney in harmonic pattern theory). Also classical "measured move" from Edwards & Magee — a flag/pennant target projection equal to the prior impulse.

**Alignment:** PAC's measured move is structurally identical to AB=CD at 100% expansion. The EMA cross requirement for point A (price begins on one side of EMA 21, ends on the other) adds a concrete filter that the classical AB=CD does not require — this is a reasonable addition.

**Simplification / Loss:** Harmonic trading specifies the Fibonacci ratio at which point C must form (e.g., Bat pattern: C at 38.2–50%). PAC requires C to be "clearly back on the same side of EMA as A" — a looser constraint. The three-leg maximum rule ("after the 3rd leg, stop trading this structure") is PAC-specific and not present in harmonic theory, which allows unlimited AB=CD extensions within a trend. This is arguably a sensible risk-management addition.

**Double Up/Down** (continuation double top/bottom within a correction) maps directly to Al Brooks's concept of a double bottom bull flag or double top bear flag — a two-legged pullback that signals correction exhaustion. Brooks explicitly teaches this as a continuation pattern. PAC's presentation is faithful to this concept, though the "only works on tick charts" requirement is PAC-specific.

### 7. Battle Zones

**Closest established concept:** Wyckoff trading ranges (accumulation/distribution zones). Also classical congestion/consolidation areas from Edwards & Magee.

**Alignment:** A zone where "multiple alternating swing reactions" occur with buyers and sellers fighting for control is a textbook description of a Wyckoff trading range. The requirement that reactions be "roughly balanced" top and bottom parallels Wyckoff's concept of supply and demand reaching equilibrium.

**Simplification / Loss:** Wyckoff's trading range analysis is volume-dependent: accumulation is confirmed when volume dries up on tests of the range low, distribution when volume dries up on tests of the range high. PAC's Battle Zones have zero volume component — they are identified purely by price swing structure. This removes Wyckoff's primary analytical tool.

**PAC addition:** The "never carry Battle Zones across days" rule and the "typical location: 50% or ⅓ of a move" heuristic are PAC-specific operational rules not found in Wyckoff.

### 8. OHLC D1 Bias

**Closest established concept:** ICT's (Inner Circle Trader) "dealing range" concept — using the prior day's OHLC to define intraday bias. Also related to classical pivot-point analysis.

**Alignment:** PAC's promo zones (above body = one side's promotion zone, below body = the other's) are functionally identical to ICT's approach of using the prior day's high/low/open/close as intraday S/R. The "first reach of a promo zone = highest probability reaction" teaching matches ICT's "first presentation" concept.

**Simplification / Loss:** ICT layers additional context — the weekly range, monthly bias, and the concept of "premium" vs. "discount" relative to equilibrium (the 50% of the dealing range). PAC uses D1 only, without multi-timeframe OHLC stacking. This is simpler but loses the higher-timeframe framing.

### 9. Session Boxes

**Closest established concept:** ICT kill zones and session-based analysis. Also the Asian Range Breakout strategy (widely taught in forex education since the 2000s).

**Alignment:** Asia session high/low defining the overnight range, with London and New York sessions breaking out of it, is a direct match to ICT's session framework and the Asian Range Breakout concept. The buyer/seller promo zone labeling is ICT-adjacent terminology.

**PAC addition:** The formalized box structure (Asia Box → London Box → US session) is a clean operational framework. ICT teaches similar concepts but less systematically.

### 10. Spike & Channel / Flag / Range

**Closest established concept:** Classical bull/bear flag (Spike & Flag), channel trading (Spike & Channel), and congestion/rectangle patterns (Spike & Range). Al Brooks extensively covers these as "spike and channel" trends.

**Alignment:** Nearly 1:1 with Al Brooks's spike-and-channel framework. A strong initial impulse (spike) followed by a measured pullback in a channel, with the channel's breakout as the continuation entry. Brooks even uses the term "spike and channel." PAC's Spike & Flag is a classical flag pattern. The measured-move target from the spike is standard.

**PAC's framing:** Making the measured move the "primary" framework for trading Spike & Channel (rather than simply a target) is a useful emphasis not always explicit in Brooks's work.

### 11. Hidden Channel

**Closest established concept:** Parallel channel / equidistant channel trading. A measured move contained within a drawn channel is classical channel analysis.

**Alignment:** This is standard channel trading with a different name. The anti-adjustment rule ("don't change the channel to make it fit") is excellent practice — it directly addresses the confirmation bias that classical texts warn about but rarely codify as a rule.

### 12. Reversal Lines

**Closest established concept:** Wyckoff's reaction highs/lows as S/R. Also classical swing-point S/R mapping.

**Alignment:** Drawing horizontal S/R from swing points where price has previously reacted is among the oldest techniques in technical analysis. The validation process (wait for a retest → mark as S/R only if price reacts) is Wyckoff's approach.

**Simplification / Loss:** Classical S/R analysis weighs the number of tests, the time elapsed since the level formed, and the volume at the level. PAC's reversal lines have no such weighting — every confirmed reaction level is equal.

### 13. The Five Named Setups

**Closest established concepts:**
- **Trap Setup** → Al Brooks's two-legged pullback / failed breakout trap. ICT's liquidity sweep (trapped counter-trend traders).
- **Fail Setup** → Deep pullback / Wyckoff spring or upthrust (false break beyond S/R that reverses).
- **To-Try Pullback Trap** → AB=CD extension with correction re-entry. Harmonic pattern continuation after target overshoot.
- **Range Trap** → Classical false breakout of a consolidation range. Wyckoff's spring/upthrust within a trading range.
- **Range Fail** → Failed breakout reversal at range boundary. Directly matches the "failed breakout" concept from nearly every TA textbook.

**Assessment:** These five setups are not novel patterns — they are well-established price action archetypes (false breakout, two-legged pullback, deep correction reversal, range failure) given branded names. The value PAC adds is the specific packaging: each setup has defined Fibonacci zones, Two-Try Rule requirements, and EMA/trendline confluence filters. This codification is genuinely useful — most classical texts describe these patterns descriptively rather than as checklistable setups.

### 14. Tick Chart Requirement

**Closest established concept:** Tick charts are well-established in futures day trading (popularized by traders like John Carter, Ken Calhoun). Eliminates time distortion, each bar represents equal market activity.

**Unusual aspect:** PAC mandates tick charts for several components (Reversal Zones, Double Top/Bottom, Double Up/Down) while being a retail forex/CFD strategy. Tick chart data quality in retail forex depends entirely on the broker's data feed — it varies dramatically between brokers. In futures (where tick data comes from centralized exchanges), tick charts are reliable. In retail forex, they are broker-dependent and non-standardized — a significant practical concern that PAC does not acknowledge.

---

## What Is Original vs. What Is Rebranded

### Genuinely novel (or at least uncommon)

1. **The Five Named Setups as a closed taxonomy** — the specific packaging of Trap/Fail/Range Trap/Range Fail as the exhaustive list of tradeable setups, each with defined entry criteria. Classical texts describe these patterns but rarely organize them into a finite menu.
2. **The EMA directional filter on signal candles** — requiring a bullish signal candle to close above EMA 21 is a simple, effective noise filter not standard in candlestick literature.
3. **The "never carry Battle Zones across days" rule** — a practical discipline for intraday S/R freshness.
4. **The 3-leg maximum rule on measured moves** — not found in harmonic or AB=CD literature.
5. **The tick chart mandate for specific components** — unusual in retail forex, though standard in futures trading.

### Classical theory with new names

| PAC Term | Established Term |
|----------|-----------------|
| Signal Candle | Pin bar / hammer / shooting star |
| Gap Candle lines | Reaction level S/R (Wyckoff) |
| Battle Zone | Trading range / congestion zone (Wyckoff, Edwards & Magee) |
| Hidden Channel | Equidistant / parallel channel |
| Reversal Lines | Swing-point S/R |
| Spike & Flag/Channel | Bull/bear flag, spike-and-channel trend (Al Brooks) |
| Promo Zones (OHLC D1) | Dealing range / prior-day OHLC bias (ICT) |
| Session Boxes | Asian Range Breakout / ICT kill zones |
| Measured Move | AB=CD pattern (Gartley/Carney) |
| Trap Setup | Two-legged pullback + failed breakout (Brooks) |
| Range Trap/Fail | False breakout of range (Wyckoff spring/upthrust) |

### Adapted/simplified from established methods

- **Elliott Wave** → stripped of all rules, becomes impulse counting. Loses falsifiability.
- **Fibonacci** → trimmed to five levels, drops 23.6% and 78.6%. Loses harmonic pattern precision.
- **Wyckoff trading ranges** → price-only, no volume analysis. Loses Wyckoff's core diagnostic tool.

### Does simplification improve usability?

**Yes, for the MA system, the five named setups, and the measured move rules.** These are more actionable than the original frameworks they draw from.

**No, for Elliott Wave counting and Fibonacci analysis.** The simplification removes the guardrails that prevent self-deception. A trader using PAC's "count the impulses" approach has no way to know when their count is wrong.

---

## Where Established Literature Warns Against PAC's Approach

### Elliott Wave on M5

Academic analysis (Poser, 2003; Prechter & Frost, 1978 — who themselves focused on daily+ timeframes) consistently warns that sub-hourly Elliott counts are dominated by noise. Applying wave counting on M5 tick charts produces an overwhelming number of possible counts with no way to discriminate. PAC sidesteps this by abandoning formal wave rules, but the underlying signal-to-noise problem remains.

### Fibonacci level validity

Statistical studies on Fibonacci retracements in financial markets (e.g., Gaucan, 2011 — "How to use Fibonacci retracement to predict forex market") find weak statistical significance for individual Fibonacci levels. The levels "work" primarily through self-fulfilling prophecy (enough traders watch them) rather than any intrinsic market property. The cluster concept mitigates this — convergence of multiple levels is stronger than any single level — but PAC does not acknowledge the base-rate weakness of individual Fibonacci levels.

### Confluence and confirmation bias

Adding more tools (Fib + MA + trendline + Battle Zone + session box + OHLC bias) can create an illusion of robustness. The Opus review makes this point sharply: with 15+ tools, you can almost always find a "confluence" to justify a trade. The established literature (Kahneman & Tversky's work on cognitive biases; Taleb's *Fooled by Randomness*) warns that increasing the number of flexible indicators increases the risk of curve-fitting and narrative construction. A smaller set of rigid rules typically outperforms a larger set of flexible ones.

### The five setups — validated patterns or named heuristics?

The Trap and Fail setups are variants of false-breakout and two-legged-pullback patterns, which have empirical support in the price action literature (Brooks, 2012; Bulkowski's *Encyclopedia of Chart Patterns*). However, they have been validated in the context of daily/hourly timeframes with specific sample sizes and win rates. PAC applies them on M5/tick with no published performance data. The patterns are plausible but unvalidated at PAC's operating timeframe.

---

## Verdict

**Is PAC a coherent synthesis or a hodgepodge?**

It is closer to a coherent synthesis than a random collection — the five named setups provide a decision framework, and the tools are logically connected (MAs define sentiment → Fibonacci defines zones → signal candle triggers entry → measured move defines target). The problem is that the toolbox is too large relative to the filtering rules. With 15+ tools and a 7-point checklist that most setups can pass, the strategy's actual selectivity depends on trader discretion, not on the system's rules.

**Does it add value over classical S/R with measured moves?**

Marginally. The specific value of PAC over "trade pullbacks to support in a trend with a measured-move target" lies in: (1) the five-setup taxonomy, which gives names and checklists to common discretionary patterns; (2) the session-box framework, which provides intraday structure; and (3) the EMA-based filters, which are concrete and automatable. These three elements could stand alone as a tighter strategy.

**What would a Brooks/Wyckoff practitioner say?**

An Al Brooks practitioner would recognize most of PAC's setups as standard price action patterns with rebranded terminology. They would likely appreciate the measured-move emphasis and the Two-Try Rule but criticize the absence of volume analysis (Wyckoff), the lack of explicit risk-reward requirements, the removal of Elliott Wave's falsification rules, and the over-reliance on visual/discretionary assessment. A Wyckoff analyst would specifically object to calling anything a "trading range" analysis without volume — in Wyckoff's framework, that is fundamentally incomplete.

**What should the repo owner take from this?**

PAC is approximately 80% established theory with new terminology, 15% useful operational simplification, and 5% genuinely distinctive packaging (the five-setup taxonomy, the EMA signal-candle filter, the 3-leg rule). It is not a scam or pure rebranding — the codification of the five setups into a tradeable checklist format is genuinely valuable work. But the repo owner should understand that studying Brooks, Wyckoff, and ICT directly would provide deeper understanding of the same patterns, with the added benefit of falsification rules and volume analysis that PAC strips away. The strongest path forward would be to extract PAC's best operational innovations (the five setups, the EMA filters, the 3-leg measured-move discipline) and combine them with the rigour that the source traditions provide — especially Wyckoff's volume analysis and Brooks's explicit risk-reward requirements.
