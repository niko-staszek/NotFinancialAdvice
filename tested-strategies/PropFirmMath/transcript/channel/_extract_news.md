# JJ Simon — News Trading, Fair-Price Reset & Continuation extract

Source transcripts (channel/):
- `8lbkj0PF1uM.txt` — "Copy My News Trading Strategy" (PRIORITY — news mechanics)
- `2hwd27aqD30.txt` — "Trading psychology is fake"
- `vJuwbKibN1E.txt` — "What They're Hiding From You" (mostly Layer-B account EV)

Extracting only NEW / more-precise detail vs known method (fade NQ to fair value on close-confirmed BoS/displacement, 25/37.5 SL/TP @ 1.5R, no management).

---

## 1. NEWS TRADING MECHANICS (priority) — `8lbkj0PF1uM.txt`

### Which news
- **Red-folder US-impact news only.** "red folder US impact news. That's going to be 8:30 a.m. EST, usually Tuesday, Thursday, sometimes Friday, Monday, whatever." (L41-44)
- Source = **Forex Factory** news calendar. (L45-47)
- **US only**, because trading Nasdaq futures: "Remember, only US because we're trading Nasdaq futures." (L337-338)
- Named examples he walks through: **CPI** (Tue May 12), and two unnamed red-folder 8:30 prints (Wed May 13, Thu May 14). (L106-116, L178-186, L228-229)

### The KEY split: expected vs unexpected news → different fair price + direction
This is the central new rule. Two regimes:

**(A) EXPECTED news (actual ≈ forecast) → REVERSION to PRE-NEWS price.**
- "the fair price of news is going to be **the price before the news came out.** This is because this news is planned... they already have a forecast for it. Most of the time it's pretty much exactly on the forecast... that means the news has already been priced in." (L53-64)
- So the spike on release is **unfair**; trade reversion back to pre-news price. "this entire move down is unfair, and I want to trade it coming right back to this price here." (L121-124)
- **Fair-price marker = the BODY of the 8:29 a.m. candle** (the candle immediately before the 8:30 release). "mark out here the body of the candle before the news. So this would be 8:29 a.m. EST." (L111-114); "I just do the body of the candle." (L182-183); CPI example "Treating the 8:30 8:29 a.m. candle as fair." (L233-238)
- **Reversion is the main / highest-win-rate trade:** "Reversion is the main way to make money off of expected news." (L79-80); "I would say it is my highest win rate trade out of literally all of the trades that I take is the reversion to pre-news price." (L367-370)

**(B) UNEXPECTED news (actual far from forecast, OR random/tweets) → CONTINUATION in the news direction; fair price RESETS.**
- "if the news is **very far away from the forecast**... then... in a way it's sort of unexpected." (L188-206)
- For unexpected: **the move is FAIR**, do NOT revert to pre-news. Instead **the most-recent consolidation AFTER the news becomes the new fair price.** "instead of trading back to the pre-news price, because the move is fair, I would treat the most recent consolidation after the news to be the new fair price." (L307-312)
- Trade a **continuation** in the direction of the move: "you want to trade, first of all, a continuation. So entering anywhere throughout this candle as it's forming is very good. You don't even need to know the sentiment." (L299-306)
- **News drift** is the named rationale — surprise news keeps drifting same direction: "financial asset prices continue moving in the direction of a surprise piece of news." (L84-92); "they're not able to price in the effects instantly, which is why I love doing continuations of unexpected news." (L353-356)

### No-sentiment rule (important simplification)
- You never need to know if news is good/bad: "you don't have to analyze the sentiment of the news... You just have to know if it occurred and if it was planned. Forex Factory will tell you all of that." (L93-99). Price action tells you direction: "Okay, the institution has thought that this was bad for Nasdaq futures, and hence the dump." (L195-197)

### Entry trigger for news — SAME as regular method
- "Personally, I just use a **break and close above previous structure.** It's what's worked best for me." (L124-127)
- Repeated: "Same entry criteria as usual for the strategy, pretty much off of any break of structure." (L223-224); "just get in on a break of structure. The first one we see is right here." (L242-245)
- So news reversion = **wait for break-and-close of structure back toward the pre-news (8:29 body) price**, same BoS trigger as the open-candle method.

### SL / TP for news — ARBITRARY, not the 25/37.5 fixed rule
- **Explicit:** "Stop loss and take profit are arbitrary, up to your prop firm risk management, whatever you are doing. There are statistically optimal ways to do this, but in general, just trading in the direction of the news is always good." (L348-353)
- So for news he does NOT assert the fixed 25/37.5 @1.5R; sizing/targets deferred to prop-firm risk rules. Target is effectively the fair-price level (points back to 8:29 body). He eyeballs points-in-favor: "very easily able to see how many points I'm getting in my favor back to what I believe to be the fair price." (L127-130); cites "70 points in your favor" on the CPI trade (L245-246).

### Pre-open news timing hazard (NEW, concrete)
8:30 news fires ~1 hour before the 9:30 RTH open. He flags entering *before* the open as dangerous:
- "You can also enter before the market open, such as off this break of structure... Just know it is very, very dangerous if the market is opening while you're in a trade. Because the open has a ton of overnight orders... totally possible that you're in a winning trade, and the open just wicks you out before continuing back up." (L140-151)
- Overnight order imbalance carries into the first seconds of the open: "pretty likely that the opening trend for at least the **first 10 to 15 seconds** is going to have a lot of selling orders because the overnight trend was mostly bearish." (L155-159)
- Mitigation: "you want to **widen your stop** if you're in a trade. Sometimes go break even, but it is up to you and your back testing." (L160-163)
- Safer alternative: wait for the open, let it print its first green candle, then enter on the BoS: "just wait until the market opens and prints its first green candle and just enter here off this break of structure back to this pre-news price." (L163-168)

### Stacking multiple reversions (continuation cycle within news)
- After price reverts to fair, an over-extension *past* fair is itself unfair → another reversion: "this continuation up here would also be unfair, and you could trade another reversion back to the news price." (L169-172); CPI "you could even double down and get a second trade in." (L254-258)
- **But capped by volume/time:** "I would recommend don't look for too many reversions throughout the day. I'm usually done trading by 11:00 a.m. just because the volume sort of dies out, and the edge dies as well." (L173-177)

### How fair value BEHAVES around news (summary)
- Expected news: fair value is **sticky to pre-news (8:29 body)**; the release spike is noise to fade.
- Unexpected news: fair value **jumps** to the post-news consolidation; old pre-news level is abandoned.
- Confirmation that a level was fair = price returns and **consolidates/chops** there. CPI: "comes all the way back down to the pre-news price... and then consolidates, so pretty much proving that this was indeed a fair price." (L261-266). Iran-tweet example: market opened, "instantly came back to this consolidation... and just chopped around in here, proving that this is the new fair price." (L319-325)

---

## 2. FAIR-PRICE RESET (mid-session) — NEW, the biggest cross-cutting finding

The known method anchors fair value at the 9:30 open candle / 2pm. These transcripts show fair value **is dynamic and resets intraday**:

- **Reset trigger = a fair move (real displacement), after which a NEW consolidation defines the new fair price.** General statement: "I would just treat **the most recent consolidation** and the market open price as fair, instead of this news candle." (L197-200)
- On the Wed May 13 example (actual far from forecast), he abandons the 8:29 candle and re-anchors: "I'll just treat this consolidation and the 9:29 a.m. candle as the fair price." (L207-209)
- Explicit caveat that 9:29/open is NOT always fair: "Just understand that **9:29 is not always going to be the fair price** because there can be unfair moves pre-market open." (L274-277)
- Mechanism for picking the new anchor: after an unexpected/fair move, **wait for consolidation, treat that consolidation as the new fair reference**, and fade subsequent breakouts back into it: "Sometimes... it will break out of this consolidation and I'll trade on it coming back to the consolidation." (L316-318)

**Implication for the model:** fair value = "most recent consolidation following a fair move" (default = 9:30 open candle / 2pm, but re-anchored after any displacement-grade move). This generalizes the static 9:30/2pm anchor.

---

## 3. CONTINUATION CYCLE (with-trend, beyond first 10-15 min) — NEW

- He confirms a **continuation leg of the open-candle method**, separate from reversion: "In my other strategy, I also trade continuation of an opening candle." (L131-133) On a red open candle that snaps back up: "we make a quick continuation back up towards the fair price. So you could pretty much enter anywhere along this stretch of green candles." (L133-139)
- **When to prefer continuation over reversion:** when the move is large/unexpected (actual far from forecast). "if it is very far away, as it is here, it is **better to take continuations** of these sort of trades, and you can just enter anywhere throughout the first candle as it's printing." (L213-218)
- For pure expected news he generally **skips** continuation: "I probably wouldn't trade a continuation because it came out as expected." (L268-271)
- Continuation entry is looser than reversion — **enter anywhere through the forming candle / stretch**, not a strict BoS: (L300-306, L213-218). Reversion still uses the BoS-and-close trigger.
- Continuation is gated as advanced/risky: "You can also trade a continuation of the news if you're able to get in early enough. It's a lot more dangerous though. You would have to test that for yourself. It's only something I would add **once you're trading multiple accounts at a time.**" (L72-78)

**Summary of the decision tree he describes:**
1. Red-folder 8:30 news → check actual vs forecast on Forex Factory.
2. Actual ≈ forecast (expected) → **REVERSION** to 8:29-candle body, BoS-and-close entry, no sentiment needed. (Main edge, highest WR.)
3. Actual far from forecast OR random/tweet (unexpected) → **CONTINUATION** in move direction (enter anywhere in forming candle), then re-anchor fair value to the post-news consolidation and fade breakouts back to it.
4. Over-extensions past fair = re-fade (stack reversions), but stop ~11:00 a.m.

---

## 4. OTHER CONCRETE RULES / NUMBERS

### Session cutoff (confirms known)
- "I'm usually done trading by 11:00 a.m. just because the volume sort of dies out, and the edge dies as well." (L173-177, `8lbkj0PF1uM`).

### Sizing — risk MORE when win-prob is higher (NEW, explicit)
- "I always risk higher when my chance of winning is expected to be higher. It's something that you should apply to your trading as well." (L376-379, `8lbkj0PF1uM`). Supports the user's "size-gate on A+ setups" idea — confidence-scaled sizing is his stated practice.

### A "statistically optimal" SL/TP exists but isn't given
- He twice alludes to optimal SL/TP without specifying: news SL/TP "arbitrary... There are statistically optimal ways to do this" (L348-353). Leaves the fixed 25/37.5 as a *regular-session* convention, not a news rule.

### From `2hwd27aqD30.txt` (psychology — mostly filler, but concrete sizing/risk bits):
- **Standardized fixed sizing is the whole point** — most "psychology" failures are really sizing inconsistency: "most traditional psychology problems are pretty much sizing problems... using too many contracts, too little contracts." (L74-82) Fix = a step-by-step plan you never deviate from. (L92-96) Supports a *fixed-fraction / fixed-contract* model, not discretionary sizing — mild tension with the "risk higher on A+" line above (reconcile: fixed base, scaled only by graded confidence).
- **Tilt-routing rule (Layer-B):** if tilting, blow a cheap eval bundle instead of a funded account — same dollar risk, lower variance. "$1,000 to get [a 150k account]... I will fullport the entire thing... it's only $1,000 worth of risk." vs blowing a 10K-profit funded acct = "10 times as worse." (L196-219); "buy 10 evaluations for $100 each, you could fullport 10 evaluations straight... exact same risk as doing that 1:1 plus or minus thousand trade." (L233-237)
- Claim: random/tilted trades are "**worst case break even** with higher risk" (no negative-EV penalty beyond variance). (L166-178, L280-281). NOTE: this is his assertion, not validated — assumes the underlying signal is zero-EV, which contradicts a real edge existing; treat skeptically.
- No new *signal* mechanics in this video. Otherwise motivational.

### From `vJuwbKibN1E.txt` ("What They're Hiding" — Layer-B account EV; overlaps PropDDSim):
Mostly the account-as-option math already captured in Layer B. New/precise numbers worth logging:
- **Account EV = what you paid for it, until it's in profit.** New funded acct: pass rate 33%, eval $100 → "average cost to achieve the funded account is $300... your real expected value of this account is $300." (L120-133)
- **Real risk = ½ of acquisition cost on a fresh funded account.** "Say I want to risk $1,000... your real risk is $150 because that is half of what you paid to get there." (L278-294) i.e. risking $X of simulated money on a fresh account costs you ≈ (½ × eval-acquisition-cost), not $X.
- **In-profit account EV ≈ its profit** and real risk ≈ full dollar risk: "$2,000 funded account is pretty much $2,000... if I risk that same $1,000... my actual risk is $1,000." (L296-304)
- **Recursion / payout cadence:** "if you're able to take a payout every five winning days and you are a break even trader... on average you take out half of it, you take out another half... about $2,000 expected value." (L143-159) — payout-every-5-winning-days cadence + break-even assumption underpin the EV.
- **EV formula in his tool:** "cost of the eval, the cost to get the funded account, which is that formula... basically **eval cost divided by pass rate plus activation fee** if there is one, and the expected payout." (L521-530)
- **Different R:R per firm AND per account stage** (eval vs funded vs funded-in-profit), because rules differ (consistency, min winning days, payout caps): "I do take a different risk-to-reward on each firm and on each account." (L230-235); eval → "optimize your pass rate," funded → "optimize your chance of a payout multiplied by size of the payout." (L225-229)
- **His own scale (proof):** ~$250k payouts Topstep, $136k Tradeify, $220k E8, $100k Lucid, $108k FundedNext, $75k Alpha Futures over 12 mo (L5-24). Monthly model: spend ~$20-30k on evals → withdraw ~$130k. (L327-346)
- **Live accounts are bad** (both prop-live and real-live): Topstep deletes profit via bonus-unlock (must make 9k×4 = 36k to unlock 40k reserve) (L400-421); Lucid/Tradeify give $0 live accounts, 1 per funded acct that took a payout, capped at 5, $4,500 max-loss with $4,500 bonus on hitting target (L452-478). Real-live needs $5M to match the prop approach at 2%/mo. (L354-365)
- **8 losses in a row at $500 = $4,000 (blows a 150k trailing account)** — Monte Carlo stress reference. (L595-598)

---

## 5. CONTRADICTIONS / TENSIONS vs known method

1. **SL/TP for news is explicitly "arbitrary," NOT 25/37.5 @1.5R.** (L348-353, `8lbkj0PF1uM`). The fixed 25/37.5 is a regular-session convention; news targets the fair-price level by points. Do not assume the fixed bracket for news trades.
2. **Fair value is NOT statically 9:30/2pm — it resets to the most-recent consolidation after any fair move.** Explicit: "9:29 is not always going to be the fair price." (L274-277). The static-anchor assumption is a simplification of a dynamic anchor.
3. **Continuation trading is real and core to his book**, not just reversion — but only on unexpected/large moves, entered loosely (anywhere in the forming candle), and gated to multi-account/advanced. The known "fade-only" framing is incomplete.
4. **Sizing:** "risk higher when chance of winning is higher" (`8lbkj0PF1uM` L376) vs "standardized system, never deviate, sizing problems cause losses" (`2hwd27aqD30` L74-96). Reconcile as: fixed base size, confidence-graded scaling on A+/A/B — not free discretion. Supports the user's size-gate idea but warns against ad-hoc sizing.
5. Psychology video's "tilted trades are worst-case break-even" claim assumes zero-EV signal — internally inconsistent with claiming a real edge, and unvalidated. Flag, don't adopt.
