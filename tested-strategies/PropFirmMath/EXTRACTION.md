# PropFirmMath — Extraction from JJ Simon Interview

Source: `transcript/transcript_clean.txt` (Titans of Tomorrow interview with "JJ Simon", quant-finance graduate, prop-firm trader). Claims ~$1.5M in payouts in <18 months, 20–30+ trades/day. All content below is extracted ONLY from what the transcript states. "NOT STATED" marks gaps. Trading knowledge of my own is not added.

---

## 1. Core thesis / the "loophole"

The edge is NOT a market edge — it is a **prop-firm-rule edge**. He optimizes his trade parameters (risk, profit target, R:R, account selection) against each prop firm's specific rule set so that he extracts more total payout dollars than the cost of evaluations, treating the whole thing as a positive-EV slot machine.

One-sentence summary (his framing): take a tiny mean-reversion bias, trade it many times per day at small static R:R across many cheap evaluation accounts, sized so that the math (pass rate × payout chance × payout size, vs. eval cost) guarantees positive return in the long run with capped downside.

Key statements:
- "I found that my returns were not going to be incredibly high. The reason for that is the prop firms don't want you to make money... you have to do something against the norm if you want to stand out and be extremely profitable on prop firms."
- "He instead found a mathematical loophole that is completely mechanical, removes all psychology."
- "I was able to use that very strong background in math and stats in order to create positive expected value in all of my trades based on my win rate, based on my risk reward... exactly which prop firm challenge to trade on, exactly how much to risk, exactly how much to go for in terms of profit target every single trade."
- "Your goal was not actually find an edge in the market... It was rather have an edge in the prop firm arena." → "Yeah, 100%."

Critical distinction he repeats: **evaluation and funded phases are optimized for DIFFERENT objectives, and he trades different strategies on each.**

---

## 2. Why common approaches fail on prop firms

- "The prop firms don't want you to make money. So they obviously have to structure their rules in a way where the most common trading approaches is not going to work."
- He modeled level-2 order flow + specific TP/SL on live and found returns "were not going to be incredibly high" because prop firm rules are structured against common live-trading approaches.
- The binding constraint is the **trailing drawdown** (on futures accounts, the trailing drawdown moves up at the end of the day). Strategies must be built around max-drawdown in the equity curve, not around finding the best live equity curve.
- Live accounts given by prop firms are "getting more and more strict because they want to try their best to limit the profitable traders." This is the one decay risk he names.
- Leaving runners/partials is "probably one of the worst things you can do on prop firms" because of (a) the consistency rule and (b) how the trailing drawdown moves.

---

## 3. Evaluation phase approach

Objective: **maximize chance of hitting the profit target BEFORE hitting the max loss.** (Not EV — that's the funded objective.)

Mechanics stated:
- **Static risk per trade** (fixed dollar amount per account).
- **Fixed R:R / fixed profit target** on evaluation ("It is for evaluation. It's fixed.").
- **No runners, no partials, no break-even** (with rare exceptions — see §7).
- He solves for **max drawdown in his equity curve**, framed as **total evaluation fees vs. total payouts** (the "slot machine, keep rolling the dice, let the math play out" framing — he confirmed it's this, not a per-trade profit-target-vs-drawdown frame).
- Targets ~**3x return on evaluation spend**; good runs 4–6x, bad runs ~2.7x; "the downside is extremely capped."
- **Match R:R to the firm's target/drawdown ratio.** Worked example: "$3,000 profit target and a $2,000 max loss, that is a 1 to 1.5. So if you automatically change your risk reward to a 1 to 1.5, then you're just going to pass more challenges because of how the trailing drawdown works."
- He layers multiple evals in the same direction rather than copy-trading one signal: "I'll do one eval here, another, another, another. So I'm getting like five evaluations in the same direction as taking one trade like someone would do on a live account." (Layered after the first/funded one is in profit.)
- Trade-count selling point: "I'm passing like 10 evals in a day. Just by taking so many trades of smaller risk to reward."
- Targets ~**30% eval pass rate** ("I try to pass about 30% of the evaluations"; elsewhere "25-30%", and a 33% figure used in one worked model).

Why small R:R beats large R:R on eval (his reasoning): a 1:10 trader, even with equal expectancy, needs ~3 wins in a row or ~20 trades to clear the profit target given the consistency rule (up 1000, minus, minus, minus...), taking "a week to a month" to pass; he passes many evals per day with small R:R.

---

## 4. Funded phase approach

Objective: **maximize expected value = (chance of a payout) × (size of that payout).** Explicitly different from eval.

How it differs from evaluation:
- He uses **different strategies** on funded vs. eval ("incredibly different").
- R:R is **varied** on funded (he cycles 1:1, 1:1.5, 1:4, "whatever") rather than the single fixed R:R he prefers on eval. He picks which account to trade based on what the market offers: "if I see a one to 1.5 in the market, I know I'm going to choose this account because a one to 1.5 is best for this account specifically."
- Payout mechanics: aims for **max $5,000 per payout**; brings a funded account to **$10,000 balance, then withdraws $5,000 (half), back to $10k, withdraw half**, repeat. (In the smaller-scale worked example: bring to $4k, take $2k.)
- He layers evals in the same direction once a funded account is in profit (§3).
- Forward concern: live/funded accounts get progressively stricter; that's the only thing he can't forecast.

---

## 5. The EV / probability math ("the exact maths before buying a single evaluation")

This is the most important section. Captured as close to verbatim as possible.

### 5a. Two-phase objective split
- Eval: optimize **P(hit profit target before max loss)**.
- Funded: optimize **EV = P(payout) × payout size**.

### 5b. Probability of a payout (from eval)
- "If I'm starting from eval, it's **pass rate multiplied by chance of reaching $10,000 balance**" (because he wants $10k balance, then withdraws $5k max).
- He explicitly separates **eval pass rate** from **chance of getting the payout** (P(payout) is NOT the per-trade win rate).
- Worked illustration he gives: "25% chance to pass and then 25% chance to get the payout, multiply those two together, that's like 6.25%."

### 5c. Risk of ruin
- Wants **risk of ruin ≤ 5%** when starting; later operates at **0.5%**.
- Formula he states: with P(fail / no payout) per account, **P(zero payouts from N accounts) = (P_fail)^N**.
  - Example: "0.95 to the power of maybe like 20 if you're going to buy 20 accounts, and then you'll know my chance of getting zero payouts from 20 accounts is that number."
  - Concrete personal start: $5,000 bankroll, 50k accounts at ~$100 each → can afford ~50 accounts; 90% fail rate → **0.9^50 ≈ <1%** risk of ruin. ("turned 5,000 into 17,000 trading the 50k accounts.")
- To go from a starting bankroll to net-worth requirement, he uses "just do like 5%" (i.e., total exposure ≈ 5% of net worth); for copy-trading 10 accounts at $1k he says you'd need ~$2M net worth (or ~$500k on prop firms), and "sometimes you can multiply it by 10 just for an extremely safe 0.5% risk of ruin."

### 5d. The funded EV formula (built live with host, near end)
Variables he enumerates:
- **Eval phase:** (1) evaluation cost, (2) evaluation pass rate, (3) time to pass [added on prompting].
- **Funded phase:** (1) **average cost to funded** = eval cost ÷ pass rate. Example: "if I buy three evals and I pass one, it cost me $300 to get to funded → $300 average cost to funded." (2) **chance of getting a payout**, (3) **payout size**, (4) time.
- **EV / ratio:** upside = P(payout) × payout size; downside = average cost to funded. Ratio of the two = the return multiple.

Worked example (his numbers):
- Average cost to funded = $333; average payout EV = $1,000 → **3x return** ("very very achievable").
- To make a given payout total, "look on the upside, you need to make about ~$14,000 in payouts, and with that 3x, take a third of that" = total cost; multiply to get funding required.

### 5e. The "1 out of 9" model (his actual early scaling math)
- "I personally modeled it with **33% pass rate and then a 33% chance to get a payout for $2,000**. So I do 0.33 × 0.33. So it's basically **one out of nine evals that I buy, I'm going to get $2,000 out of it.** Each eval costs ~$100. So I'm spending 900 and then I'm withdrawing 2,000 → easy 2x return. Plus you still have $2,000 left in your funded account because you only took out half."
- "I would aim to have **one out of nine eval purchases results in a payout for $2,000. And then you just need to do that 10 times.**" (→ $20k payouts / $10k a month target scale.)

### 5f. Kelly criterion
- Used Kelly early to decide **how many evals he could afford** for a given bankroll and expected return: "if I go in with 5,000, then based on the return that I expect to get, I would bet this specific amount." Buys a mix (e.g., $50, $80, $100 evals) to keep risk of ruin low while realizing EV.
- Notes Kelly recommends higher risk than most are comfortable with; suggests **quarter- or half-Kelly** when building a bankroll. Says he no longer needs it because bankroll is large and "the edge is 100% going to play out... guaranteed in the long run."

### 5g. Memoryless / streak math (mental-model digression)
- Each trade is **memoryless**; after 9 losses the next trade's win prob is unchanged.
- The probability of extending a streak vs. the streak's own probability differ: "your chance exponentially of getting nine versus 10 in a row is nine times 0.4" / "multiply that value at the ninth loss by 0.6." (This is a discussion of a "consecutive losses in a 100-trade sample" table, NOT a trade rule.)
- Decision under a losing streak: **keep risk identical, do not change strategy** "until you realize the numbers are not in your favor."

### 5h. Scaling ladder (portfolio framing)
- Start $5k → 50k accounts (~$100 each), ~3.3–3.4x → $17k.
- Then $10k → 34k across 4 firms (chose this over jumping to 150k accounts), because "treat prop firm accounts like a portfolio" — many accounts at once beats few large accounts (5×150k ≈ only $5k/month vs. target $100k/month).
- Now: **10 firms, all 150k accounts, trying to have all 5 funded active at once on every firm.** "150 is a 3x from 50... I try to go for a 4x so I can spend a little bit less."
- $100k/month target math (built with host): 150k payouts ÷ $5k = **30 payouts** (~1 payout/day/month); running ~**40 accounts** (could do 30, refreshing losers). Funding needed: **30 × 150k = $4.5M** in allocations. $10k/month → ~$450k in allocation.

---

## 6. Entry mechanics

What actually triggers a trade — precise about specified vs. unspecified.

### Bias / direction
- **High-time-frame bias is built from the 1-minute chart only** (looks back up to 6 hours if needed). "Just 1 minute. Market opens, it goes this way, I'm just going to trade back to the open."
- Direction = his view of the **"fair price" of the futures** for the next **30 minutes to 1 hour**.
- **Fair price defined as the 9:29 a.m. Eastern price (pre-open)**; thereafter, "if there's consolidation and then more breakouts, I'll just read the most recent consolidation as a fair price."
- He does NOT use higher-TF charts, points of interest, order blocks, or institutional/order-flow signals. "All I need is a slight edge in a bias in my favor. So I don't care if it's no-man's land... All I'm trading is a specific direction."

### Two trade types per session
1. **Continuation of the open / news** — pure time trigger. At session open (or news), the first trade is a continuation of the opening/news candle. "The minute any session opens, I'm ready to take a continuation." For news: "when news comes out there's a huge candle, I'll just trade a continuation of that candle for my first trade of the day."
2. **Mean reversion back toward the open/fair price** — after the continuation, he takes ~3–4 trades fading the move back toward the opening (or pre-news) price. The reversion entry trigger is a **1-minute break of structure back toward the opening price**, after consolidation: "when volume starts dying out, it will usually start to consolidate... I will trade when it breaks structure back towards the opening price."

### Execution criterion (the one concrete trigger)
- Entry on a **1-minute break of structure**, confirmed by close: "**As long as it closes below the structure that it broke, I'm good with entering.**"
- Fully mechanical, binary: "Either it broke structure it didn't. I try to take the discretion out of it."
- Reversion entries must occur **before 11:00 a.m.** ("As long as it's before 11:00 a.m. I don't care.").
- He explicitly does NOT believe in chart patterns ("most of it is artificial" — institutions placing huge fake/bulk candles balancing inventory). Does NOT use Level 2 / order flow ("I've never, no.").

### Rationale for many trades
- "If I take 20 trades per day it's the exact same as someone who takes one trade a day for a month. And if I'm able to trade 20 times as much with the same edge, I'm going to make 20 times as much."
- Claims ~98% winning DAYS from 20-trade daily sample size with slight positive expectancy.

---

## 7. Exit mechanics

- **Static stop loss** (fixed dollar amount per account), NOT placed at technical levels. "Exactly a thousand, exactly 500." He says he modeled technical SL placement and found static "infinitely better" on prop firms.
- **Static take profit** (fixed dollar/points), NOT based on price action. "Exactly static."
- **R:R per trade (account-specific), examples given:** risk 1,000 / target 2,000 (1:2); risk 1,000 / target 1,500 (1:1.5); risk 500 / target 2,000 (1:4). Eval mostly 1:1.5, some 1:2, some 1:1. Funded ranges 1:1, 1:1.5, 1:4.
- **No break-even, no partials, no runners** ~95% of the time. He lets trades "play out in the long run... I'd rather be in the trade than not in the trade even if it's pretty much random from that point."
- **Break-even exceptions:** (1) a new session opens while he's in a trade (e.g., in a 6pm trade and Asian session opens → go BE), (2) news coming out → go BE. "95% of my trades I'm not going to go break even."
- Reasoning for no-BE on reversion: mean-reversion moves retrace ("market makers balancing inventory... it can't travel so far with only one-sided orders"), so a trade that returns to BE still often reaches TP.
- Profit targets sometimes constrained by firm rules, e.g. "on some accounts a 15-point profit target that I have to take just for the prop firm's specific approach."

---

## 8. Instruments / markets / timeframes / sessions

- **Instrument:** Nasdaq futures only ("Futures for Nasdaq"). Chosen for best commissions + spread for his approach. He has NOT modeled other assets but believes the approach generalizes to any prop-firm instrument with static risk/TP.
- **Chart timeframe:** 1-minute only (with up to 6h lookback for bias).
- **Sessions / daily schedule (Eastern):**
  - **8:30 a.m.** — news; 1 continuation + ~3 reversions.
  - **9:30 a.m. (NY a.m. open)** — 1 continuation + 3–4 reversions.
  - **~11:00 a.m. (into lunch)** — 1 longer trade held from 11:00 to ~2:00.
  - **2:00 p.m. (NY p.m. open)** — 1 continuation + 3–4 reversions.
  - **6:00 p.m. session** — 1 continuation + 3–4 reversions.
  - **8:00 p.m. (Asian session)** — 1 more (one continuation + reversions implied).
  - Fair-price reference = **9:29 a.m. ET** pre-open price.
- Reversion entries gated to **before 11:00 a.m.** for the morning block.
- Trades every day (not only news days); session-open volatility treated the same as news (an "unfair move" to fade).

---

## 9. Position sizing & risk

- **Static dollar risk per trade**, varied per ACCOUNT (not per trade signal) to fit each firm's rule set. Examples: $1,000, $500.
- **Risk varies by account** specifically to optimize SL/TP for that firm's optimal rule set.
- Targets risk of ruin ≤5% at start, ~0.5% now.
- Net-worth / exposure heuristic: total exposure ≈ 5% of net worth (×10 safety for 0.5% RoR).
- Future refinement he'd make: put the profit target where he thinks fair price is AND layer a live-style approach onto the static approach — "changing contract size from like two to like 17 17 micros. Like very small changes to increase your return."
- Rejects copy-trading on variance grounds: 10 accounts × $1k = $10k swing → needs ~$2M net worth (~$500k on props); copy trading at small R:R (e.g., -100/+250 ×10) passes accounts far too slowly for far smaller payouts vs. running one account at a time at -1000/+2500.

---

## 10. Prop firm specifics

- **Firms named as best-paying / used:** Topstep, Lucid, TradeFi ("TradiFi"). Also mentions Apex (historical "golden age" of $1M–$2M payouts), and the rule changes after the silver exploit ("Topstep had to ban silver and increase their prices just because of how exploitable trading silver was").
- **Sponsors mentioned (not necessarily his):** Olap Prime (95% split, 1-hour/"10.1-hour" structured payout), Alpha Capital ($100M payouts), Alpha Futures (Tradovate/NinjaTrader, CME-compliant, largest end-of-day balance drawdown, 90% splits, same-day payouts, accounts from $79), TradeZella, TradeZella/Zella AI (journaling).
- **Account sizes he's used:** 50k → 150k (also references 100k, 34k tier). Currently **all 150k accounts, 10 firms, aiming 5 funded active per firm.**
- **Eval cost examples:** ~$100 (general), $50/$80/$100 (Kelly mix), $79 (Alpha Futures ad), "215 eval... spending a million dollars."
- **Profit target / max loss example:** $3,000 target / $2,000 max loss = 1:1.5 ratio (drives his R:R choice).
- **Drawdown rule exploited:** **trailing/end-of-day drawdown on futures accounts** (moves up at end of day) — his entire static-risk, no-runner, match-R:R-to-ratio approach is built to exploit how this trailing drawdown behaves.
- **Consistency rule:** central reason he avoids large R:R and runners ("you can't make the whole thing in one day").
- **Payout structure he runs:** bring funded to $10k balance → withdraw $5k (half) → repeat; **max $5k per payout**; ~30 payouts/month at scale (~1/day).
- **Payout denials:** "I had about 300,000 denied in payouts" over 18 months. Some firms "are not going to pay you at all... no real arguing with them." His vetting: try ONE account on a new firm; if they pay, scale; check YouTube / public presence; avoid scams. (Bought first Lucid account "September 8th".)
- **Biggest payout ever: $45,000; every other payout is $5,000 or less.** (Consistency over lottery wins.)

---

## 11. Concrete numbers ledger (every hard number stated, tagged)

- **$1.5M** — total payouts claimed, in <18 months.
- **~$100k/month** — current run-rate / target (was stuck at $75k for months).
- **18 months / "year and a half"** — track record length.
- **30+ trades/day** — headline claim; he states **~20 trades/day** as his typical.
- **20 trades/day ≈ one trade/day for a month** — his equivalence; → 20× profit at same edge.
- **~98%** — winning-day rate he claims from 20-trade daily samples.
- **3x** — target return on eval/funded spend; **4–6x** on good runs; **~2.7x** on bad runs; **3.2–3.3x** with his actual strategy edge.
- **R:R values:** 1:1.5 (primary eval), 1:2, 1:1, 1:4. Examples: risk 1000/TP 2000, 1000/1500, 500/2000.
- **$3,000 target / $2,000 max loss = 1:1.5** — firm-ratio example.
- **1:10** — the large-R:R approach he argues against (would need ~3 wins in a row or ~20 trades, ~week-to-month to pass).
- **Pass rate: ~30%** (also "25-30%", and **33%** in one model).
- **Payout chance: ~30%** (also **25%** illustrative, **33%** in model).
- **25% × 25% = 6.25%** — illustrative combined payout probability.
- **33% × 33% ≈ 1 in 9** — his eval-purchase-to-payout rate, for **$2,000** payouts.
- **Risk of ruin: ≤5% at start, 0.5% now.**
- **(P_fail)^N risk-of-ruin formula:** 0.95^20; **0.9^50 ≈ <1%**.
- **Max payout target: $5,000/payout** (bring to $10k balance, take half). Smaller-scale: $2,000/payout (bring to $4k, take $2k).
- **Biggest payout: $45,000;** all others ≤ $5,000.
- **$300,000** — total payouts denied by scam firms.
- **Bankroll ladder:** started with $20k (poker money) but personally deployed **$5,000 → $17,000** (~3.3–3.4x) on 50k accounts (~$100 each, ~50 affordable) in ~1 month on 2 firms; then $10k → 34k on 4 firms.
- **Currently:** 10 firms, 150k accounts, 5 funded targeted each, ~40 accounts running (could run 30).
- **Account sizes:** 50k, 100k, 150k, 34k tier.
- **$100k/month math:** 150k payouts ÷ 5k = **30 payouts**; **30 × 150k = $4.5M** allocation; ~40 accounts.
- **$10k/month math:** ~$450k allocation; ~$14,000 payouts needed at 3x → take a third as cost.
- **Average cost to funded** example: 3 evals, pass 1 → **$300** ($333 used in model); EV payout $1,000 → 3x.
- **Eval costs:** $50, $79, $80, $100, $215.
- **15-point** — a forced profit target on some accounts.
- **Contract size** refinement: "two to 17 micros."
- **Sessions (ET):** 8:30, 9:29 (fair price), 9:30, 11:00, 2:00, 6:00, 8:00.
- **Bias window:** next **30 min to 1 hour**; 1-minute chart; up to **6h** lookback.
- **Reversion gate:** before **11:00 a.m.**
- **0.1% / extra 0.1% on $150k ≈ $500** — value of strategy refinement on props (3.2 vs 3.3x).
- **Sample-size stats (digression, not rules):** 60% WR → 7 losses in a row = 17%; 40% WR → 5 losses in a row = 98%; 40% WR → 9 in a row = 35%, 9→10 = 22%.
- **Loss-aversion anecdote:** people refuse +100/-100; refuse +150/-100; accept around +250/-100 (1:2.5).
- **Counterfactual quant salary:** entry $300k/yr → 1–2M in a few years → 5–10M in 10 years.

---

## 12. Key verbatim quotes (mechanical core + EV math)

1. "The evaluation, you have to optimize for your chance of hitting the profit target before hitting the max loss. And then on funded account, you need to optimize for your expected value, which is basically like your chance of a payout multiplied by how large that payout is."
2. "If you have a $3,000 profit target and a $2,000 max loss, that is a 1 to 1.5. So if you automatically change your risk reward to a 1 to 1.5, then you're just going to pass more challenges because of how the trailing drawdown works."
3. "I'm passing like 10 evals in a day. Just by taking so many trades of smaller risk to reward."
4. "If I take 20 trades per day it's the exact same as someone who takes one trade a day for a month. And if I'm able to trade 20 times as much with the same edge, I'm going to make 20 times as much."
5. "I have a high time frame bias of where the price is going to charge in for the next 30 minutes to an hour... Just 1 minute. Market opens, it goes this way, I'm just going to trade back to the open."
6. "Fair price that I will assume is just 9:29 Eastern before the market opens. And then from there, if there's consolidation and then more breakouts, I'll just read the most recent consolidation as a fair price."
7. "As long as it closes below the structure that it broke, I'm good with entering and then the stop loss take profit are static."
8. "On prop firms it is infinitely better to use static risk in terms of like exactly a thousand, exactly 500."
9. "I never go break even... unless there is a new session opening... Or if we have news coming out... but like 95% of my trades I'm not going to go break even."
10. "If I'm starting from eval, it's pass rate multiplied by chance of reaching $10,000 balance because I want to get to a $10,000 balance on my account and then take out 5,000, which would be the max."
11. "If I have 25% chance to pass and then 25% chance to get the payout, multiply those two together, that's like 6.25%."
12. "You can do like 0.95 to the power of maybe like 20 if you're going to buy 20 accounts, and then you'll know my chance of getting zero payouts from 20 accounts is that number."
13. "I personally modeled it when I first started with 33% pass rate and then a 33% chance to get a payout for $2,000. So I do 0.33 * 0.33. So it's basically one out of nine evals that I buy, I'm going to get $2,000 out of it."
14. "My biggest payout has been 45,000 and then every other payout from that then on is literally 5,000 or less."
15. "Either it broke structure it didn't. I try to take the discretion out of it just because I'm trying to take so many trades, it's easier if I follow a very step-by-step plan for every account."

---

## 13. Vague / hype / unverifiable

- **"Fair price"** is asserted but only loosely defined (9:29 ET, or "most recent consolidation"). The actual numeric reversion target per trade is never given — it collapses into a static dollar/point TP anyway.
- **Win rate is never given as a number** — "Win rate changes a lot." He pivots every win-rate question to R:R and pass-rate. No per-trade win-rate figure exists in the transcript for any setup.
- **What distinguishes a "continuation" entry from a "reversion" entry mechanically** beyond "trade the open candle's direction" vs. "break of structure back toward open" is thin. Continuation has no stated confirmation rule (the only stated confirmation — "closes below the structure it broke" — is described for reversion).
- **"Break of structure" is never defined** (swing size, lookback bars, what counts as "the structure that it broke"). This is the single load-bearing entry rule and it is unquantified.
- **The "longer 11:00–2:00 trade"** has no stated entry/SL/TP logic.
- **Different strategies on eval vs. funded** — he says they're "incredibly different" but the funded strategy is never actually described beyond "varied R:R" and EV optimization. Only the eval/reversion mechanics are spelled out.
- **Pass rate and payout chance (~30%/33%)** are self-reported, sample = "all evals I've done"; not independently verifiable, and he says you need ≥50 samples for an "exact" number (20 for approximation).
- **"98% winning days," "$1.5M payouts," "$300k denied," "10 evals/day," "$45k biggest"** — all unverifiable self-report.
- **"The edge is 100% going to play out... guaranteed in the long run"** — assumes positive expectancy that is never demonstrated with data; the whole EV case rests on an unstated, unproven per-trade edge.
- **Regime adjustments** ("little changes month to month based on the regime") — unspecified, discretionary, contradicts the "fully mechanical" claim.
- Marketing-adjacent: heavy sponsor reads (Olap Prime, Alpha Capital, Alpha Futures, TradeZella) interleaved; the interview is a promotional vehicle (Titans of Tomorrow Inner Circle, "drag-and-drop plug-and-play formulas").

---

## 14. Open questions for quantification (gaps to resolve before backtesting)

1. **Define "break of structure" precisely** — swing-high/low detection method, lookback window, minimum displacement, and "closes below the structure it broke" on the 1-minute chart. Without this there is no codable entry.
2. **Define the bias/direction rule** — how is "fair price for the next 30–60 min" computed from 1-minute data + 6h lookback? Is direction simply "fade the move away from the 9:29 price"? Need an exact rule for which way is long vs. short at each session.
3. **Continuation entry trigger** — what defines "the opening/news candle" and what confirms a continuation entry? Bar close? Time offset from open?
4. **Per-trade R:R and dollar SL/TP** — these are "per account / per firm rule set." For a backtest, pick a representative firm: its target, max (trailing) drawdown, consistency rule, and derive the matched R:R (e.g., 1:1.5 from 3k/2k). Need the exact trailing-drawdown mechanic (intraday vs. end-of-day move, lock-at-profit, etc.).
5. **Win rate is unknown** — must be measured by the backtest, not assumed. The entire EV claim hinges on it being ≥ break-even for the chosen R:R.
6. **Number/timing of trades** — codify the session schedule (8:30, 9:30, 11:00→2:00, 2:00, 6:00, 8:00 ET) with the "1 continuation + 3–4 reversions" pattern and the before-11:00 reversion gate. Need a rule for when the 3–4 reversions fire (after each consolidation break? max per session?).
7. **Break-even exceptions** — encode "go BE if a new session opens while in trade, or if news is imminent" with concrete session/news timestamps.
8. **The "longer 11:00–2:00 trade"** — entry, SL, TP all undefined; must assume or drop.
9. **Eval vs. funded as two strategies** — the funded strategy is underspecified; decide whether to model only the eval/reversion engine, or assume funded = same engine with varied R:R.
10. **Account/portfolio layer** — to reproduce the EV math, the backtest must simulate the prop-firm wrapper: eval cost, pass/fail on target-before-drawdown, $10k→withdraw-$5k payout cycle, account refresh on failure, (P_fail)^N risk-of-ruin, and 3x-spend target. This is a Monte-Carlo over accounts, separate from the per-trade signal backtest.
11. **News data** — "trade continuation of the news candle" and "revert to pre-news price" require an economic-calendar feed and a definition of "the news candle."
12. **Instrument/data** — Nasdaq futures (NQ / MNQ micros), 1-minute bars, RTH + extended sessions through 8:00 p.m. ET; commissions + spread must be modeled (he picked Nasdaq specifically for these).
13. **"Memoryless / keep risk static"** — confirms no martingale/anti-martingale; risk is constant. Simplifies sizing logic.
