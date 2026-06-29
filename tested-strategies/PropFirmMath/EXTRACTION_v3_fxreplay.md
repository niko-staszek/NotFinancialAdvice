# EXTRACTION v3 — FX Replay: "Backtesting JJ Simon's NQ Strategy | Fair Value Theory"

Source: `transcript/transcript3_clean.txt` (~11,000 words). Independent manual backtest of JJ Simon's strategy performed in the FX Replay tool. Extracted faithfully — only what is stated. Line numbers refer to the cleaned transcript.

**Caveat on number provenance:** Several of the most important aggregate metrics are spoken from on-screen FX Replay analytics dashboards while the host reads them aloud. They are transcribed exactly as spoken below. The host explicitly flags hedging ("I'm pretty sure", "if I remember") on a couple — those are tagged inline.

---

## 1. Backtest results / metrics (HIGHEST PRIORITY)

All quotes verbatim. Sample-type tags noted where the host distinguishes (this study is essentially a single multi-pass manual backtest over several hand-picked historical windows; the host does NOT do formal walk-forward — see §2).

### 1a. The live random-day demo (March 4, 2025 onward)

Random start date chosen live from chat:
- L504: "March 4th, 2025. All right."
- The demo ran across multiple days starting there. Final demo tally:
- L1211: "But obviously it's only eight trades."
- L1206–1209: "So far just no trades this day. So let's look at the analytics. Like I said, this is going to be above average. Like I will show you guys the other sessions I tested. It is not this high of a win rate, but thank you for whoever suggested March of 2025 cuz yeah, this strategy crushed during the period we tested."

So the live-demo window = **8 trades**, described as "crushed" / above-average win rate, but win rate number for just those 8 is NOT STATED as a figure.

### 1b. "February 2026" window (partial month)

- L1230–1232: "So I tested 43 trades over that period. And in the month of February I was able to get 19R."
- L1233–1234: "Actually this is this is only like half of February. So this is very good. You know, 19R in"
- L1243–1245: "But higher frequency with a lower time frame. 58% win rate. performed very very well during this period this recent period that I tested."

→ **43 trades, +19R, 58% win rate** (≈ half of February 2026).

### 1c. Late-April 2025 → early-May 2025 (uptrend window)

- L1247–1249: "I tested this like pretty strict uptrend here from like April of 2025 like late April 2025 to like early May."
- L1259–1260: "For for a while we were having around like you know, plus or minus 5R with a little bit of drawdown."
- L1264–1269: "And so also profitable. 56% win rate. I think it's a much more reasonable compared to like 85% win rate or something like that. But that's a solid profit factor. Like 1.93 profit factor is really good."

→ **56% win rate, 1.93 profit factor** (uptrend window). (R total for this window NOT STATED; only "plus or minus 5R" intra-window described.)

### 1d. ~April 2023 (ranging / choppy window)

- L1273–1276: "This is like April of 2023 through April yeah, basically April of 2023."
- L1280–1284: "So, I'll filter on those real quick. Ranging markets. Not as good."
- L1285–1288: "it was, you know, I I think most strategy Even with the mean reversion, you probably the mean reversions were okay here. Um, but overall, it was still a little bit worse in this condition."

→ Qualitatively "Not as good" / "a little bit worse." No hard numbers stated for the 2023 ranging window.

### 1e. AGGREGATE across all tested windows — the headline strategy stats

Total combined dataset:
- L1328: "So, 158 trades."
- L1343–1344: "but I, you know, jumped down and did 158 trades for you guys, so you're welcome."
- L1347–1348: "but over all the period we tested, 54% win rates, 1.76 profit factor. Honestly very solid."

→ **AGGREGATE: 158 trades, 54% win rate, 1.76 profit factor.**

### 1f. Aggregate broken down by tag — Continuations (entry trigger 1) vs Mean reversions (entry trigger 2)

Continuations:
- L1352–1356: "the continuations have slightly higher win rate, which is very common. Continuations generally tend to be a little higher probability over two profit factor."
- → Continuations: "over two profit factor" (>2.0 PF). Exact PF/WR not given as a single number here.

Streaks (aggregate / continuations context):
- L1357–1359: "Max win streak of eight, max loss streak of five. Um, we had more buys than sells in the period."

Continuations monthly R:
- L1377–1379: "and again, looking at performance by month, anywhere between um sorry. Anywhere between like 2% uh sorry, 2R and 15R just trading the continuations."

Continuations total R (host hedges):
- L1476–1478: "we got 15R here versus entry trigger one. Um, I think it was like 40R if I remember. Um, I'm pretty sure it's like 40R."
- → Continuations total ≈ **40R** (host explicitly unsure: "if I remember", "pretty sure").

Mean reversions (entry trigger 2):
- L1410–1418: "now let's look at the entry trigger two. Um, cuz that's going to be the mean reversions ... So, little lower win rate, 59 or 49% win rate. Still 15R over the period, 1.46 profit factor, still not quite as good"
- → Mean reversions: **49% win rate, +15R, 1.46 profit factor.** (Host misspeaks "59 or 49%" then settles on 49%.)

AM vs PM session:
- L1362–1366: "and then yeah, pretty similar results between the AM session and PM session. Probably slightly higher win rate in the PM session, it looks like, um but still profitable in in the performance session."
- → PM session "slightly higher win rate" than AM; both profitable. No hard split numbers.

Performance by day (aggregate / continuations):
- L1367–1368: "performance by day, um Tuesdays, Wednesdays seems a little lower"

Mean-reversion day breakdown sample size:
- L1463–1464: "Again, these are I have decent sample size here. This is 67 trades."
- → Mean-reversion (entry trigger 2) ≈ **67 trades** in that day-breakdown view.

### 1g. The "few simple optimizations" before/after comparison (time-of-day filters only)

This is the host's optimized variant — drop first 3 minutes, drop 10–11am hour for mean-reversions, drop 3–4pm hour for mean-reversions. He compares his pre-existing dataset before vs after.

BEFORE (his earlier testing dataset, excludes the most recent demo data):
- L1596–1600: "So, this is all the testing I did before. Um, hunt still 150 trades, 46R, uh 52% win rate, 1.66 profit factor."
- → BEFORE: **150 trades, +46R, 52% win rate, 1.66 profit factor.**

AFTER (same data, time-of-day filters applied):
- L1600–1605: "And then after I removed a few of those um I removed those first three minutes. I removed the 10 and 11 hour versions. I removed the 3 to 4 p.m. hour versions. Now we have a 2.46 profit factor with a 62% win rate. So, very simple optimization. No new rules or whatsoever. Just literally like using the time."
- → AFTER: **2.46 profit factor, 62% win rate.** (Trade count / R after filtering NOT STATED.)

### 1h. Excel "first 3 minutes are bad" evidence (continuations)

- L1554–1558: "And then if I just literally filter on the first like three minutes, uh we made like 40R um across all these, I'm pretty sure. Where's the P&L right here? 36R. Over these and then this is like the testing I did before."
- → ALL continuations (pre-recent data) = **36R** (host first says "like 40R ... pretty sure" then corrects to on-screen **36R**).
- L1562–1572: "But if we filter just the first three minutes, uh we've only made 2R um in that ... Let's see the count. 28 trades, you're only making 2R. Um, so it's going to be a super low win rates. Um, I don't know if I counted it, probably like 40 40% win rate something like that."
- → FIRST-3-MINUTES continuations only = **28 trades, +2R, ~40% win rate** (win rate is a guess: "probably like 40 40% ... something like that").

### 1i. Risk-reward simulator (optimal R:R)

Continuations:
- L1384–1394: "1.5 is optimal um for this strategy the the way we traded it. It doesn't say that any other risk reward level is going to drastically improve our results... 1.6R is slightly better. So, if you want to get a little bit more out of the edge, um you maybe you can go 1.6R instead of uh just 1.5."
- → 1.5R optimal; 1.6R "slightly better."

Mean reversions:
- L1485–1494: "Um, if you are ex- if you can accept a 27% win rate, um it seems like holding the mean reversion a little better. Um, could improve your results a little bit. Um, I usually don't recommend people go for a 27% win rate strategy"
- → For mean reversions, sim suggests holding longer (down to a **27% win rate**) could improve results; host does not recommend actually running at 27% WR.

### 1j. Numbers NOT STATED
- Max drawdown (%): NOT STATED as a number anywhere (only qualitative "a little bit of drawdown", "we did come into a little bit of drawdown").
- Total $ / dollar profit figure: NOT STATED (only R and PF).
- Largest single win / largest single loss: NOT STATED.
- Expectancy per trade (R): NOT STATED directly (derivable but not spoken).
- Sharpe: NOT STATED.
- Exact date span of the full 158-trade dataset: NOT STATED as a single range (it is a stitch of hand-picked windows: ~Apr 2023, Apr–May 2025, Mar 2025, ~half of Feb 2026).

---

## 2. Test methodology

- Instrument: **NQ futures, 1-minute timeframe.** L183–188: "Obviously, this is NQ 1-minute timeframe... he's trading 1-minute NQ timeframe, NQ futures. Um, so, this is obviously a futures specific strategy."
- Tool: **FX Replay** (manual bar-replay backtester). Trades tagged by type; analytics dashboards, risk-reward simulator, and CSV export used.
- Manual, discretionary, human-executed bar replay — NOT automated. Host eyeballs structure breaks and applies a fib tool to check candle decisiveness (see §3).
- Sample construction: NOT a formal walk-forward. The host hand-picks several historical windows chosen deliberately to span market regimes:
  - L1222–1225: "So I tested 2020 February of this year cuz obviously he's been trading this pretty recently."  (he means Feb 2026 — see L1229)
  - L1247–1249: late-April 2025 → early May 2025 — "pretty strict uptrend."
  - L1271–1275: ~April 2023 — "I tried to find like the rangiest conditions I could find."
  - Live demo: March 4, 2025 random start.
  - L1294–1296: "to give you guys I've jumped around a few different market conditions and we have like a really good sample size for this."
- Each window appears to be a single forward pass through the replay (one pass over a fixed window per regime), tagged, then all sessions tied to one FX Replay "strategy" object for combined analytics. L1300–1304: "I've created a strategy for this and all these sessions that I've traded, I'm going to link up to this specific strategy... So we can look at all the analytics together."
- Tagging scheme:
  - L683–687 / L897–898: "entry trigger one for the continuations" (= continuations away from fair value).
  - L750–751 / L913–916: "entry trigger two for the uh meaner versions" (= mean reversions back to fair value).
  - Suggests **entry trigger three** for second-move continuations (not actually recorded — see §4).
- Sessions traded: **New York open (9:30, ~first 90 min)** and **New York PM (14:00 / 2pm)**. Asia NOT tested by host. London not traded (JJ US-based). L348–349: "I didn't personally test Asia session. I just focused on New York session for my testing so far."
- Discretionary parts handled by converting to mechanical proxies: decisiveness via fib counter-wick %, stop size via ATR bucket (see §3, §5). Host repeatedly says size of candle and live news-context were left out as too discretionary (see §3, §6).
- Sample-size honesty caveat stated explicitly:
  - L1212–1219: "If you test a strategy for 10 trades and it's amazing, it doesn't guarantee that it's going to do well over a large sample size. You need to make sure to validate with a proper sample size."
  - L1651–1654: "But yeah, the period we tested today obviously crushed. But I'm sure there's also periods that you have 30% win rates."

---

## 3. "Decisive candle" / displacement candle — how THEY defined & identified it

Host adopts a **mechanical counter-wick rule** and explicitly DROPS the size threshold as too discretionary.

- Concept (JJ's): L115–118: "this concept of a displacement candle. And in his... video, he talks about it being like a large candle and kind of like a decisive candle."
- Decisiveness is mechanized via counter-wick %:
  - L121–132: "we can use this like counter wick definition where basically for a bullish candle that top wick, if you measure from like the open to that kind of the high, how much of that... range does the wick make up? And like a decisive close you could say, 'Okay, I don't want that counter wick to be more than 20% of that range.' That can indicate that that's a really strong close."
  - **Counter-wick < 20% of range = decisive.** Confirmed again L161 ("more than 20%... would like not meet our criteria"), L168 ("very small counter wicks that are less than 20%"), L892–894 ("the counter wick is less than 20% so we got everything we need").
- SIZE threshold: explicitly NOT mechanized.
  - L133–138: "The size of the candle is a little more discretionary. That's something that's a little harder to make a mechanical rule set around. So, for my testing specifically, I've tried to focus mostly on like the decisiveness of the candle."
  - L172–175: "it's it's discretionary enough that I think it's better it's going to be better to focus on the decisiveness versus the size, um, when testing."
  - No "bigger than prior N candles" / no multiple-of-average-range rule was used. He comments on size visually only (e.g. L142–149 "decisive but it's not very large", "kind of the best where it's both decisive and large").
- Practical identification in FX Replay — fib retracement tool:
  - L573–584: "I use this fib retracement tool... So, you're using 0, 2, and 1 for the fib retracement... you can apply this fib level from basically the open of the candle to the low and see like did it close decisively or not."
  - I.e. fib levels set at **0, 0.2, 1**; the **0.2 level** is the threshold price the close must clear. L1129–1141: "the level is 19732.5. So it did not quite. It was like one point off. And so I'm basically like looking at the price level on the 0.2 to see like okay, price needed to close at or above this level."
  - Worked examples of reading it: L668–676 (2606.25 "literally right at that"), L1087–1090 ("We would need 830.5 and it's 820. Actually this is. Yeah, it was decisive enough"), L1015–1017 ("20 at 152... we're definitely below that level we needed for the decisiveness").
- Discretion flagged at the threshold (equality / "exactly at level"):
  - L668–677: "and it's literally right at that. So um I'll let you guys decide if we want to allow it to be exactly equal amount. We'll go ahead and take it. Um I think in the PDF I said it it can't be more than."
- **CRITICAL combined-criteria refinement:** decisive candle AND the structure break must be on the SAME candle:
  - L591–599: "However, we haven't really broken structure with this candle. You want to see the break of the candle and the decisive decisive candle in the same instance, whereas the break kind of happened this first candle and now we're in a decisive candle."
  - L995–997: "it is specific criteria that you need the break and the decisive candle on the same candle."
  - L808–813: "even though we had the the kind of strong displacement candle since there wasn't a structure break it didn't work out. Um so that's why the combination of the two is going to be higher probability for sure."
- Possible future automation noted: L698–704 host suggests coding a custom indicator to flag decisive candles (white body etc.), but for the test he just uses the fib tool.

---

## 4. Follow-up / 2nd-attempt / additional trades that JJ takes but FX Replay did NOT trade

This is the caller's flagged claim. There are TWO distinct "extra trade" categories JJ reportedly takes that the host deliberately EXCLUDED:

### 4a. Second ATTEMPTS (re-entries after a loss)
- L356–366: "Same thing with second attempts. If you he he in his video, he showed second attempts pretty frequently. You know, I had a loss here, took another try, had a loss here, took another try. With FX Replay, the great thing is you can use tags to see... like is it worth taking the second attempts or not. So, you can collect the data and confirm if you should try it or not."
- → JJ re-enters after losses; host did not systematically include these — flags them as a taggable test.

### 4b. Additional / second-move CONTINUATIONS & mean reversions (after price already reverted)
- L388–409: "He'll trade like additional continuations after price comes back. Um... So, price has already moved away from the and already kind of reverted back and now he's taking subsequent continuations and mean reversion. So, in my testing, I tried to focus mostly on like kind of this first move, the initial move away and the move back. But, you could also test... these like kind of second moves... I just try to focus on just that first move to keep it simple so far today."
- Re-confirmed with a concrete on-chart example (large green candle ~10:00–10:05, ~33–34 min after open):
  - L854–869: "this is where um I'd mentioned in the PDF um specifically you could take additional continuations after price returns to fair value... he said specifically in his video he really tries to look for um continuations the first like 10 minutes or so. Um so this is like... 34 33 minutes after open. It's... definitely after the period that he started. Um so you could you could test these and see... maybe I use entry trigger three for those like kind of second move continuations."
  - Also second-move mean reversions: L873–882: "say you were in the session we saw this meaner version short and you saw like... an opportunity for a meaner version long like still in your session you could also take these kind of second move meaner versions and see if those are worth taking too."
- Host explicitly did NOT record these: L976–984: "this super strong candle. Definitely broke a lot of of structure right here. Decent chance that it has continuation. I'm not going to specifically record it because I haven't been recording these testing. So I just don't really have the data on them, but this is definitely something if you want to increase the trade frequency even more, you could also test these kind of second move continuations and mean reversions."

### 4c. How it might change the results
- Host suggests the excluded second-move mean reversions could fill in the weaker "second hour" window:
  - L1438–1447: "I didn't personally take those like second mover versions. Um, so if you added those to the mix... Maybe if you added more of these, it would maybe offset and improve that second hour window or whatever, but for my testing, I was mostly focused on kind of that first move."
- Net: JJ's live trade frequency / results include re-entries and second-move setups that are **absent** from this backtest. The host's 158-trade dataset is therefore a *subset* (first-move-only, decisive+break-same-candle) of what JJ actually trades. Direction of effect on results is left open (could add frequency, could offset the weak windows; "worth taking or not" is presented as an untested question).

---

## 5. Rule deviations / refinements vs the written spec

The host states he made the strategy MORE mechanical than JJ's video ("slightly different than maybe the video he showed", L1620–1623). Specifics:

### 5a. Stop-loss / take-profit — ATR-bucketed (host's mechanization)
JJ's stated raw rule:
- L268–274: "he basically uses like most often a 25 tick stop loss and like a 38.5... tick tick profit for 1.5 R. Um, but he did mention there's like more of maybe if it's more volatile, then he'll do like a 50 tick stop loss and 75 ticks."

Host's ATR mechanization (1-minute ATR value on the lower pane):
- L282–298: "if it's over 20, like, price is really moving, um 50 tick stop loss... And obviously, 1.5 R would be 75. 7 to 20 was kind of the range that I was... testing... for that 25 tick stop loss, um in the 38 and 1/2 tick tick profit. And then if it's below 7 ATR... it's probably better to tighten it up a little further and use like a 16 and 1/2 versus 24.75."

→ **ATR buckets (host's invention):**
- ATR > 20 → 50-tick SL / 75-tick TP.
- ATR 7–20 → 25-tick SL / 38.5-tick TP.
- ATR < 7 → 16.5-tick SL / 24.75-tick TP.
- All at fixed **1.5 R**, **no trade management**. L437–439: "Using the ATR to determine our stop loss and just going for a fixed 1.5 R no trade management." L840–842: "He doesn't do any trade management as far as I know. He just lets it play out um win or loss."

ATR threshold applied live at the 20 boundary:
- L908–913: "It's 20.25 so it's just over the 20 threshold. If it's under 20 then we would drop it um to the 25 tick but we'll stick with our 50 tick."
- L1093–1094: "we finally have an ATR below 20. Barely. 19.7." → used 25-tick.

### 5b. Contract sizing rationale (prop-firm $1,000 risk design)
- L304–319: "If you have a pretty wide stop loss with 50 ticks, one contract on NQ is going to equate to a $1,000 risk per trade... Two contracts with a 25 tick equates to $1,000 risk per trade, or three contracts with a 16.5 tick stop loss. 1,000. So, like it's very easy to adjust the quantity based on the stop loss levels."
- → The three SL distances (50 / 25 / 16.5 tick) are designed so 1 / 2 / 3 NQ contracts each = ~$1,000 risk.

### 5c. "Avoid first 3 minutes" (host refinement, NOT in JJ's video)
- L324–337: "it may be best to avoid the first three minutes after the 9:30 open... from my testing so far that seems like it may be best to wait like the first three minutes before taking these continuations."
- Validated in Excel (§1h): first-3-min continuations only +2R over 28 trades vs +36R for all.
- Applies to NY open only — PM session timing didn't matter: L654–658: "the afternoon session from my testing didn't matter as much if you waited a few candles or not... even if it's like the first candle of the PM session that seemed to was fine uh to take if it met the criteria."

### 5d. Combined criteria tightening (displacement + break same candle)
- Host chose JJ's "best combination" only, not displacement-only. L230–245: "he said the best combination is when it's displacement plus a break in structure... So, I decided to stick with the best." See §3 for same-candle rule.

### 5e. Fair-value reference price (9:30 and 2pm)
- The reference is the **market-open price / first candle**, drawn as a line. L256–264: "It's basically market open. So... what price opens... He usually... highlights like the first candle... it's basically that the what price opens... kind of at market open."
- Two fair-value times tested: **9:30 (NY open)** and **14:00 / 2pm (NY PM)**. L216–218: "he's found that the 9:30 open and the 2:00 p.m. New York afternoon often act as fair value." PM session in FX Replay set to 1400 (L549–551).
- Continuation-then-reversion timing: L219–225: "he generally looks for continuations kind of away from the fair value the first 10-15 minutes... after the open and then look for mean reversions... back to that fair value the rest of the trade window."

### 5f. "Don't take mean reversion if take-profit is far beyond fair value"
- Host's added discretionary filter: a mean-reversion whose TP sits well past the fair-value price is lower probability.
- L724–745: "now we're pretty we're already like pretty close to the meaner version level. So in cases like this I... was really like not trying to take the trade if we're already pretty much like at our target..."
- L1056–1068 / L1076–1079: "this is a example where like the take profit is quite a bit of ways beyond the fair value level. So either you would probably want to pass on this or... if it taps the fair value price, maybe at least go break even at that point... the fact that our take profit was kind of beyond the fair value price just made this one a little lower probability."
- Break-even-at-fair-value idea: L752–754: "if it comes back to the fair value price you could um go break even at that point." (JJ-attributed randomness after tag: L1066–1068 "I think he said like it's pretty random after it comes back to the fair value levels.")

### 5g. VWAP confluence (mentioned, NOT tested)
- L339–346: "he didn't mention it specifically in his video, but looking at some some other examples that I found, he often will have like the VWAP on his chart as well, so that could potentially be another confluence to test."

### 5h. Session-window optimization (host's data-driven cuts)
- L412–423: "It may be best to just stop trading that second hour after the window. So, maybe only the first 30 minutes of New York open and maybe only the first hour in that in the afternoon window."
- Mean reversions specifically: L1424–1431: "you may not want to take mean reversions if they happen after the first 30 minutes of New York open... only take mean reversions if they happen within that first 30 minutes of open."
- PM mean reversions: L1454–1460: "you probably only only want to trade mean reversions the first hour of that PM window and just don't worry about trading the last... 3:00 p.m. to 4:00 p.m. of New York session."
- Day-of-week tweaks (low confidence, small sample): L1462–1464: "Performance by day, maybe drop Wednesdays... and maybe increase risk Fridays."

### 5i. Asia session (host did NOT test; JJ's condition)
- L350–354: "if you're going to trade Asia, he says he really only likes to trade it if there's like a surge in volume and volatility. Otherwise, he doesn't like to trade it cuz it's generally like pretty flat and choppy."

### 5j. News trading (mentioned, NOT tested)
- L368–376: "he also mentioned you can trade news with this strategy. The 8:30 a.m. red folder news. You could trade mean reversion back to the price before news... I didn't specifically test those."

### 5k. Live discretion the host deliberately stripped out
- L1159–1199: JJ in his videos checks Trump tweets / live news to validate moves and draws *additional* fair-value levels at random-looking consolidations. Host simplified to time + price + scheduled news only:
  - L1176–1179: "I think it's something better to focus on the data that you do have consistently, which is obviously time and price and like expected news."
  - L1193–1199: "there are additional fair value levels you could trade as well, but you would probably need a little bit more insights on how exactly he does that. I think it's fine to just stick to these opens. It works well enough it seems."

### 5l. Stop-loss philosophy (host's positive note)
- L920–946: praises the non-precise ATR stop — "He's just like trying to say okay I think in general price is going to go this way so as long as I give myself enough wiggle room... It may be better to use a little more general... numbers based... stop loss instead of always using structure."

---

## 6. Their verdict / sum-up

Bottom line: **cautiously positive — "promising," "solid," possibly legit, but heavily hedged on sample size and live executability.**

- Opening + closing framing (same lines, bookended): L1–8 / L1610–1631:
  - L1–8: "I'm honestly going to say, like, this JJ guy might be legit. I hope he doesn't come out like in a week on JJ's a fraud. But, we put his strategy to the test with no bias, no, um, expectations. Definitely a promising strategy that if you love 1-minute timeframe NQ scalping, um, could be a strategy for you."
  - L1610–1613: "I'm honestly going to say like this JJ guy might be legit. Um, I hope he doesn't come out like in a week on JJ's a fraud."
- L1624–1631: "honestly, yeah, this is a super solid um, data set that we have so far. Definitely a promising strategy that if you love 1-minute time frame NQ scalping, um, could be a strategy for you."
- Verification caveat on JJ's claims: L17–26 (the $1.2M payout claim "not fully verified on our end"; hopes he keeps showing live logins). L106–112: "it's really important to validate any of these strategies and see if it's actually legit instead of just trusting what everybody says."
- Executability hedge (the recurring "but..."):
  - L480–484: "but the timing of it and... is it something realistic for you to execute is probably the bigger question that you need to ask."
  - L948–954: "it's obviously going to be hard like hard to execute in a live market for sure. Um, but... price often you know does give you a little bit of time to execute this. Like even though it entered here you had like seven whole minutes to enter."
  - L960–968: suggests limit orders at the same price to still catch trades if late.
- "It's not for everyone" hedge: L1322–1326: "yeah, a lot of profit in two weeks, but also a lot of chart time and probably a lot of gray hairs from trading one minute charts. So, if it's for you, then great, but it's definitely not for everyone."
- Regime honesty: L1651–1657: "the period we tested today obviously crushed. But I'm sure there's also periods that you have 30% win rates... but does seem like a promising NQ scalping strategy."
- Recommends viewers validate themselves in FX Replay rather than trust him (L1645–1651).

No claim of formal walk-forward / OOS validation, no drawdown figure, no Sharpe. The verdict rests on aggregate WR/PF/R across hand-picked regime windows.

---

## 7. Things that would change a backtest implementation (params, gotchas, definitions)

Concrete engine spec distilled from the above:

**Instrument / TF:** NQ futures, 1-minute bars.

**Sessions (NY timezone):**
- NY open: 9:30; trade window first ~90 min (through ~11:00). JJ's stated continuation hunt = first ~10–15 min; mean reversions rest of window.
- NY PM: 14:00 (2pm); host cuts off ~15:00 (3:00). L196–198: "I think it's probably best to cut off around 3:00 if you're trading that afternoon window."
- Asia / London / news windows exist in spec but were NOT tested.

**Fair-value reference price:** the open price of the first 1-min candle of the session (9:30 or 14:00). Drawn as a horizontal line.

**Entry — continuation (trigger 1):** after price moves away from fair value, enter on a candle that is BOTH (a) a break of structure (close beyond prior swing point, not just a wick) AND (b) a decisive candle, **on the same candle.**

**Entry — mean reversion (trigger 2):** same break+decisive-same-candle signature, but oriented back toward the fair-value price, after price has extended away.

**Decisive-candle definition (mechanical):** counter-wick ≤ 20% of the candle's open→extreme range. (Bullish: top wick from open to high ≤ 20% of that range. Bearish symmetric.) Implemented in FX Replay via fib at 0 / 0.2 / 1, close must clear the 0.2 level. Equality at the level = host's discretion (he allowed "exactly at").
- SIZE of candle: deliberately NOT thresholded. Do not require a min size / multiple-of-average. (This is a key divergence from any "displacement = X× ATR/range" reading.)

**Structure-break definition:** close beyond a prior swing high/low (wick alone insufficient). BOS (continuation) and MSB (reversal) used interchangeably. L95–100. Host applies an "eye test" for a clear swing point (L708–723: rejected a setup with no clear wick low).

**Stop / target (ATR-bucketed, host's mechanization), fixed 1.5R, no management:**
| 1-min ATR | SL (ticks) | TP (ticks) | NQ contracts for ~$1,000 risk |
|---|---|---|---|
| > 20 | 50 | 75 | 1 |
| 7–20 | 25 | 38.5 | 2 |
| < 7 | 16.5 | 24.75 | 3 |
- ATR is the standard Average True Range indicator on the 1-min chart, current value read off the right edge. (Length not stated — NOT STATED; assume default.)

**Timing filters that materially changed results (host's optimizations):**
- Skip first 3 minutes after 9:30 (continuations). Evidence: first-3-min continuations = +2R/28 trades vs +36R all.
- Mean reversions: take only within first 30 min of NY open; skip 10:00–11:00.
- PM mean reversions: first hour only (skip 15:00–16:00).
- Applying just these time filters moved the host's 150-trade dataset from 52% WR / 1.66 PF → 62% WR / 2.46 PF (no new rules).
- Optimal R:R ≈ 1.5 (1.6 marginally better for continuations).

**Excluded-from-backtest behaviours (would increase frequency / change results if added) — see §4:**
- Re-entries after a loss ("second attempts").
- Second-move continuations and second-move mean reversions after price has already reverted (host suggested tagging as "entry trigger three").
- Live news/tweet validation and extra hand-drawn fair-value levels at consolidations (discretionary; not modellable from time+price alone).

**Discretionary judgment calls an engine must approximate:**
- "Clear swing point" eye test for the break.
- Skip mean reversions whose TP lands far beyond the fair-value price (lower probability); optionally move to break-even if price taps fair value.
- Equality handling at the decisive-fib 0.2 level.

**Gotchas / honesty flags for whoever consumes these numbers:**
- Dataset is a STITCH of hand-picked regime windows (~Apr 2023 ranging, Apr–May 2025 uptrend, Mar 2025, ~half Feb 2026), NOT a continuous period and NOT a walk-forward. Selection is regime-deliberate, which cuts both ways for representativeness.
- Several headline numbers are read aloud off-screen; two are explicitly uncertain ("~40R continuations… if I remember / pretty sure"; first-3-min "~40% win rate… something like that"; "36R" corrected down from a first "like 40R").
- The "before vs after optimization" 62%/2.46 figures come from in-sample time-of-day filtering on the *same* data — textbook over-fit risk; no out-of-sample confirmation given.
- Costs: results are in R / tick terms; commission, spread, and slippage are NOT mentioned as deducted. Live executability on 1-min NQ explicitly flagged as hard.
- No drawdown %, no Sharpe, no $ figure stated.
