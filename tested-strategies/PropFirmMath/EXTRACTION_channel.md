# PropFirmMath — Full JJ Simon Channel Sweep (19 videos)

Swept all of `@itsjjsimon` (21 videos; 1 vlog had no subs, 1 pure-hype). Transcripts in
`transcript/channel/<id>.txt`; per-batch detail in `transcript/channel/_extract_{signal,wrapper,news,journey}.md`.
All below = **JJ's own claims** (self-reported, in-sample, no costs) unless tagged. Quote refs `[id Lxx]`.

---

## A. SIGNAL — the two open questions, now ANSWERED

### A1. Fair-price RESET rule (was the #1 blocker — resolved)
Fair value is **dynamic**, not a static 9:30/2pm line. *"9:29 is not always going to be the fair price"* `[8lbkj0PF1uM L274]`.
- **Default anchor = the 9:29 ET candle BODY** (rectangle, ignore wicks) `[7UXiI2arAlQ; MVP7X-3v8xk]`.
- **Resets on three things only:** *"Fair prices only ever changed by news and by session opens"* `[UVKVSWKFlvo L42]` **plus**
  an intraday **volume-spike consolidation**: if an unfair move spikes on volume and **consolidates at a new level instead
  of reverting → redraw fair price to that consolidation** (*"most recent consolidation = fair price"*) `[MVP7X-3v8xk L62]`.
- Two candidate consolidations → **mark the middle** `[MVP7X-3v8xk L358]`. Confirmed bias → expect the anchor to **migrate**
  that direction. **Does NOT reset on "fake"/no-impact news.**

### A2. Continuation cycle (resolves your chart observation)
- Continuation = the **first ~10–15 min after a session open**, then fade `[UVKVSWKFlvo L281]`. **It RECURS per session open**:
  *"each session I trade one continuation and one reversal"* `[GMDUiamqgig L14]`. Session opens: 9:30, 2pm, 6pm, 8pm. So a
  continuation after the 9:30 window is the **2pm/6pm/8pm session's** continuation — **not** the reversion phase.
- Within a single session it does **not** re-fire on a later break-away (those are the next reversion).
- The only "with-the-trend later" mode = **news-drift** (separate): hold the drift with a huge stop/target to the 2pm/4pm
  prop cutoff `[MVP7X-3v8xk L800]`. Asian continuation is taken **toward the 6pm open/gap**, not the Asian candle.

### A3. News mechanics (his highest-WR trade)
- News anchor = **8:29 candle body**. Red-folder US, 8:30 ET, via Forex Factory; **no sentiment needed** — only *did it happen*
  and *was it planned* `[8lbkj0PF1uM]`.
- **Expected (actual≈forecast) → fade back to pre-news price** (*"highest win rate trade out of all"* `[L367]`).
- **Unexpected / tweet / regime-change → CONTINUATION in the news direction; reset fair price to the post-news consolidation.**
- News **SL/TP is arbitrary** (per firm risk), NOT the 25/38 bracket. 8:30 entry pre-open is dangerous (open wicks you) →
  widen stop / go BE / wait for the open.

### A4. Sizing — TWO independent rules beyond ATR (touches your point #3)
- Base bracket **25 SL / 38 TP** (TP = his rounding of 1.5×25; 50k accounts). **150k → 50 SL / 75–76 TP.**
- **Candle-size switch (hard rule):** signal candle **body > 25 pts → HALVE contracts, use 50/76** instead of 25/38
  `[UVKVSWKFlvo L64]`. ⇒ so size varies by BOTH ATR bucket AND signal-candle size.
- **Confidence-scaled:** *"I risk higher when my chance of winning is higher"* `[8lbkj0PF1uM L376]`; more points-to-fair →
  size down + bigger runway → higher WR. Reconcile with his "standardize size, never deviate" as **fixed base × A+/A/B grade**, not free discretion.

### A5. Other signal corrections to our core
- BoS needs a **close** beyond the level (never a wick). Structure = a wick **lower/higher than the two beside it**. At
  extremes he **requires BoS, refuses displacement**, wants ~no counter-wick.
- Funded = **wait for BoS** (stricter); evals = **allow displacement** (more aggressive).
- Trade mgmt = none **except** move to **BE if a session open hits mid-trade**; re-enter on next BoS if wicked out.
- Windows: NY-AM 9:30→**11:00 cutoff**, dead 11–13h, **2pm**, **6pm** reopen, **8pm** Asian (~done 9:30pm). Stop after **3 trades** (4th only if A+).
- **Trade pace:** single clean account ≈ **2.7 trades/day**; the "~20/day" is **multi-account** live pace.

### A6. Self-reported results (UNVERIFIED, in-sample, manual marking, no costs)
- May backtest `[MVP7X-3v8xk]`: **67% WR (37/56)**, 2.67 trades/day, 6 red days, avg win $750 / loss $500, tuned for low DD.
- Reverts **"95–99.9%"** of the time; **$1.3M/12mo**, ~$160k/mo. **Edge self-admitted ≈ "1–2%, can't build a strategy around it"** — money = prop-firm asymmetry. **No aggregate live win rate ever given.**

---

## B. LAYER B (wrapper) — refinements + CORRECTIONS to our model

### B1. Corrections (important — our QUANTIFY over-formalized)
- **He NEVER states Kelly or `(1−p·p)^N` risk-of-ruin** — those are OUR modeling, not his. His RoR is qualitative
  (blow 2/20 accounts → payout rate drops "exponentially"). Stated target = **"3x the investment."**
- **~30 accounts** (one trade each), not 40. Phase-3 ≈ 25–50.
- **"$10k→withdraw $5k" → actual mechanic:** per account **+$3k → withdraw 50% → leave half → recursion** extracts the rest.
  Payout trigger = **5 winning days ≥$150**. The **50%-withdraw** rule is the universal lever.
- **Copy-trading:** don't until **~$50k/mo**, hard floor **never under $10k invested**; **his own method = NO copy-trading,
  one account at a time** (LLN smooths variance). "8 & 9 paid, 10 & 11 didn't — fine, I wasn't copy trading."
- **Eval ≠ funded:** eval optimizes **pass-rate ONLY** (ignore win rate/RR); funded optimizes **payout_rate × payout_size**
  (run 1:1.5 eval, **1:2–1:5 funded** → "that's why I don't have a win rate"). Funded ≈ **3× an eval's value**.

### B2. The structural ceiling (the real risk, not signal RoR)
Nearly every firm: **make ~50–100k → banned or force-moved to a tiny live account that deletes the sim balance.**
This is the ceiling behind his "~100k/mo max." Mitigate: **rotate firms before ban thresholds** (~20k Trade Day, ~50–100k
most, 75k Alpha); **max 3 accounts/firm** (the "$30k loss" = Tradeify/Blue-Guardian deleting profit, NOT a trading loss).

### B3. Firm tiers (ranked by actual payouts/denials `[5RzMu2B2E_0]`)
- **S:** TradiFy (monthly salary live; >$120k), **Topstep** ("best of all time"; ~$275k; 5k cap; $49→$149 activation; best for stacking), **Lucid** (Flex; pays instantly).
- **A:** Apex (hold **20 accounts**, 100% split post-ban), Funded Next (daily payouts, bolt), E8 (~$220k, no live-yank), MyFunded.
- **C/avoid:** **Alpha** ("worst EV"; yanks at 75k) — *but he lists it in his $10k cluster → treat cluster as sponsor-driven.* Scams: DayTraders, Blue Guardian, Tick Tick Trader, "Topstep Futures" imitator.
- **Add-a-firm heuristic:** start **Lucid + Topstep + TradiFy**; add an A-tier only **for a capability you lack**.

### B4. Eval economics (concrete)
- 1-firm $10k/mo: Lucid 50K Flex, **33% pass**, 3 attempts/eval, $3k spend → ~$9k out → **net ~$5.1k**, ~**3x/cycle**
  (`$500→1.5k→4.5k→13.5k`); **5 firms ≈ $27k/mo**.
- Business calc `[XhsbfEdJBAc]`: EV ≈ **1.17×**; cost-to-funded **$300**; break-even **1 payout / 20 evals**;
  **months-to-payout is the biggest lever** (he runs ~3wk on 50ks); **+2% pass&payout ≈ +$5.5k/mo**; don't model >~50% pass.

### B5. Drawdown + the 5 rules
- **EOD trailing** (trails up, **locks at 4pm ET**) = predictable, preferred. **Intraday trailing = DANGER** (ratchets to peak
  unrealized → spike-then-fall can kill the account). 50K DD **$2,000**; 150K **$4,500**. Consistency rules (20–50%) → why he keeps daily wins small/uniform.
- **5 rules:** (1) one strategy only; (2) attack evals aggressively (capped risk); (3) many accounts across many firms;
  (4) daily target AND hard daily-loss limit per account; (5) "$3,000 must feel like $3" (risk units, not dollars).

---

## C. What to fold into our build
1. **STRATEGY_RULES (signal):** dynamic fair-price reset (§A1), per-session continuation + news-drift mode (§A2/A3), the
   candle-size + confidence sizing rules (§A4), 9:29-body anchor, BoS-needs-close, BE-on-session-open. → §6b/7 updated.
2. **QUANTIFY (Layer B):** drop the implication that Kelly/RoR are JJ's; mark them OUR model. Fix ~30 accounts, the
   +$3k→50%-withdraw recursion, and add the **firm-ban ceiling** as the dominant real-world risk (bigger than signal RoR).
3. **Backtest implications:** the model is now materially more complex (dynamic anchor, 4 sessions, news split, two sizing
   switches) → strongly favors a **flexible Python engine** over Pine/NinjaScript. The eval/funded split means the wrapper
   sim only needs **pass-rate** from the signal backtest (eval) and **payout_rate × size** (funded) — two separate measurements.
</content>
