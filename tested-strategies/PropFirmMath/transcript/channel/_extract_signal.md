# JJ Simon — SIGNAL-CORE extraction (4 transcripts)

Source files (channel/):
- `MVP7X-3v8xk.txt` — "Watch Me Backtest My $1.5M Strategy" (May, day-by-day, FX Replay) — **richest source**
- `UVKVSWKFlvo.txt` — "Strategy Explained in 10 Minutes" (5 days)
- `7UXiI2arAlQ.txt` — "This ONE Candle" (9:29 candle = fair price, 7 days)
- `GMDUiamqgig.txt` — "6PM & 8PM Session, Fair Price Theory" (Asian/evening sessions)

---

## ★ TOP PRIORITY Q1 — FAIR-PRICE RESET RULE (how/when fair value updates mid-session)

**This is explicitly addressed, mostly in `MVP7X-3v8xk`. He DOES move the fair-price line during the day.** Reset triggers, quoted:

1. **Volume spike + price continues AWAY instead of reverting → new fair price at the new consolidation.**
   - `MVP7X-3v8xk` L62-69: "Now, I'm going to bring my fair price back up to here because we had a **volume spike and it continued up instead of coming back to the fair price**. So, I can change fair price a little bit throughout the day if you did not know that. I change fair price throughout the day **based on most recent consolidation**."
   - `MVP7X-3v8xk` L358-361: "Okay, new fair price would be up here because there's a **volume spike and it went away from what I thought was the fair price**."
   - `MVP7X-3v8xk` L534-537: "Okay, I'm moving fair price up to here. I have a green [candle/consolidation] with this area here. So, it's either here or here. So, I put it **in the middle of them**."

2. **The rule of thumb: most-recent CONSOLIDATION = fair price.** Recurs constantly.
   - `MVP7X-3v8xk` L68-69: "I change fair price throughout the day **based on most recent consolidation**."
   - `MVP7X-3v8xk` L92-95: "I don't think it will just because there's **a bunch of consolidation here and then it moved up farther. So I would think this is the new fair price.**"
   - `MVP7X-3v8xk` L233-234: "lots of consolidation in there. So, **100% fair price there**."
   - `7UXiI2arAlQ` L112-114: consolidation around a level "proving that this was indeed the fair price throughout the day."

3. **News / a "session-open-like" event resets it.** Fair price "only ever changed by news and by session opens."
   - `UVKVSWKFlvo` L42-49: "**Fair prices only ever changed by news and by session opens.** Now, session open's not going to actually change the fair price, but it'll change the **real** price... So, just be aware did news cause this move or was it like a session open?"
   - News = "basically like another session open." After 8:30 news, the reference becomes the **pre-NEWS price**, not pre-open. `UVKVSWKFlvo` L134-144; `7UXiI2arAlQ` L205-213.
   - A **Trump tweet** creates a new fair price at the post-tweet consolidation. `MVP7X-3v8xk` L787-795: "the volume increased out of nowhere at a random time and then it just started consolidating after. So, **this is a new fair price.**" Also L905-909.

4. **A new SESSION open = new fair-price line** (2pm, 6pm, 8pm Asian). `7UXiI2arAlQ` L89-97 (2pm); `GMDUiamqgig` whole video (6pm open + 8pm Asian open each become their own fair line).

5. **Directional bias on the reset:** he will shade the new fair-price line in the direction of confirmed bias (green news + green open → expects fair price to migrate UP over time).
   - `MVP7X-3v8xk` L1136-1143: "if I think this is a fair price then from here over time **fair price changes**... and I feel like it's going to change in the **positive direction because news was green and open was green**."
   - `MVP7X-3v8xk` L218-234: after open reversed up + 2 green news, "instead of the opening being the fair price, I honestly think the [fair] price is now up here or here. Like, it's one of these two, **not the open**."

6. **What does NOT reset it:** "fake news" — pretend it never happened, keep the prior fair line. `MVP7X-3v8xk` L1040-1048: "Fake news is very weird... basically just pretend it didn't happen... pretend that the chart kept going like this."

**Operational summary of the reset rule:** Start fair price = 9:30 open candle (he also calls it the **9:29 candle** body — see Q-misc). During the session, IF price makes an unfair move on a volume spike and then **consolidates at a new level instead of reverting**, redraw fair price to that newest consolidation. News, tweets, and new session opens (2pm/6pm/8pm) also redraw it (to the pre-news price or the post-event consolidation). Fake news does not. Ambiguity between two candidate consolidations → put the line in the middle.

---

## ★ TOP PRIORITY Q2 — CONTINUATION CYCLE (when continuation trades are valid)

**Default: continuation only in the first ~10-15 min after a session open. He says this explicitly.**
- `UVKVSWKFlvo` L281-285: "I only take continuations in like the **first 10-15 minutes** because when the unfair initial opening move stops, I definitely want to be **shorting for reversion**."
- `UVKVSWKFlvo` L100-105: "I only like to take continuation longs **right when session opens**, because that is when the unfair moves happen. After that, I'm just looking for reverses."
- `7UXiI2arAlQ` L82-83 / L156-158: trade only the **first 90 minutes** (a.m. window) + the 2pm session; 11:00–13:00 volume is dead, don't trade.

**BUT continuation recurs PER SESSION OPEN, not just the 9:30 open.** Each session open gets its own one continuation + one reversion:
- `GMDUiamqgig` L14-20: "**each session I would trade one continuation and one reversal.**" He does continuation+reversion for the 6pm open, then again for the 8pm Asian open ("four extra trades").
- New-York 2pm session: a move away from the 2pm open is "unfair," traded with the **same entry model as 9:30**. `7UXiI2arAlQ` L89-98.
- Asian-session continuation is taken **in the direction of the 6pm open / unfilled gap**, not the direction of the Asian opening candle. `GMDUiamqgig` L49-58, L379-384: "**Asian trades in the direction of the 6:00 p.m. open most of the time. 6:00 p.m. trades in the direction of the gap and then back to the 6:00 p.m. price.**" If Asian opens already at the 6pm/fair price (gap filled), he skips the Asian continuation. `GMDUiamqgig` L52-59.

**Does a continuation recur LATER within the same session (after a revert + break-away again)?**
- Within a single session, **no** — once the initial unfair opening move ends, subsequent away-moves are treated as the next *reversion* setup, not new continuations. The repeated intra-session pattern he narrates is drop→revert→jump→revert, all faded (`7UXiI2arAlQ` L84-98, L110-118).
- The ONLY exception to "trade with the trend later" is **news-drift / tweet trades** (a separate model): after a green tweet + green open + green news at all-time highs, he holds a long *with* the drift, huge stop/target, until 2pm or the 4pm prop cutoff. He repeatedly calls this "a news drift trade... ride the green" and flags it as **not the core scalp model**. `MVP7X-3v8xk` L800-837, L1150-1178. (Each one finished ~1 point from TP.)

**Continuation entry/sizing specifics (NEW/precise):**
- Continuation = trade **the direction of the opening candle** (green open → long bias, red open → short bias). Bias can be overruled by a huge counter-wick on the opening candle (then wait a candle, or flip). `MVP7X-3v8xk` L142-153, L963-981.
- If opening candle ≤ ~25 pts and no break/close yet, he may wait for a **break + close above/below structure** to confirm before taking the continuation. `MVP7X-3v8xk` L147-153, L744-755.
- Opening-candle SIZE gates contract size (see Sizing below): candle >25 pts → half size + wider stop.

---

## Entry trigger details (NEW or more precise than core)

- **Two entry models, both used:** (a) **break of structure** (BoS) close-confirmed; (b) **displacement** candle. He grades displacement as lower quality and at all-time highs / extremes he REQUIRES BoS, refusing displacement.
  - `MVP7X-3v8xk` L38-43: "I want to wait for a break of structure... I don't want to short off displacement."
  - `MVP7X-3v8xk` L70-75: "wait for a break of structure with **no wick** because we're at all time highs... I really want a very strong short."
- **Structure defined (his words):** "it's basically whenever there's a wick just like that, and it's **lower than these two**. So, it's structure. Just wait for a **close below** it." `MVP7X-3v8xk` L271-277. For longs: a structure is a swing the candle "**breaks and closes above**." `UVKVSWKFlvo` L60-62, L76-79.
- **BoS requires close beyond the level, not just a wick through it.** Repeatedly rejects wick-through-no-close. `MVP7X-3v8xk` L122-124 ("Wick, but no break. I want to close below"); L540-541; L682-683; L1000-1001 ("This is no breaker structure... since this is not a structure").
- **"No wick" displacement / strong-break preference at extremes:** counter-wick should be minimal; large counter-wick → wait one confirming candle or skip. `MVP7X-3v8xk` L278-279, L547-551 ("If there's a large wick, you can wait for the next candle to confirm"), L932-933.
- **Grading (A+/A/B):** only loosely verbalized. "A+ setup" = clean BoS, no wick, high-time-frame bias aligned, many points to fair price. `MVP7X-3v8xk` L701-702 ("A+ setup for sure"), L511-514 (everything lines up except opening candle). On his own accounts he ALSO takes displacements (lower grade) → more trades, lower win rate. `MVP7X-3v8xk` L1276-1284.
- **First-BoS rule:** for reversion he enters on the **first** break of structure he sees in the fair-price direction. `UVKVSWKFlvo` L85-88, L237-239, L248-251; `7UXiI2arAlQ` L263-271.

## Exit / stop / target / ATR (NEW or precise)

- **Base bracket: 25 pt SL / 38 pt TP (1:1.5).** "I always do 25 and 38 for these take profits." `UVKVSWKFlvo` L93-94, L196 ("Usual target 38 points").
- **ATR / candle-size bucket rule (the size→bracket switch):** if the opening/signal candle **> 25 points**, he does NOT use 25/38 — he **halves contract size and uses 50 SL / 76 TP** instead. Direct quote:
  - `UVKVSWKFlvo` L64-70: "The candle is 29 points, so I would do a 50 point stop and a 76 point take profit. My usual rule for that is **if the candle's over 25 points, then I don't do my 25 stop 38 profit. I would divide size by two and I'll do 50 and 76.**"
  - Confirmed again `UVKVSWKFlvo` L173-177 (50-pt candle → 50 stop / 76 TP). `MVP7X-3v8xk` L766-768 (50-pt candle → 50 stop / 75 TP).
  - **Note:** TP here is **38** (and 76 at double size), i.e. exactly 1.5× the 25 (resp. 50) stop. Earlier core note said TP=37.5; **his stated number is 38 / 76.** Backtest video mostly uses "$500 risk / $750 target" as the dollar equivalent (1:1.5), occasionally drifting to "750" loosely.
- **Targets are sometimes extended past 38** when far from fair price (esp. at all-time highs, on funded/live accounts without consistency rule): he'll target the full distance to fair price, "infinite profit," or fixed 1000/1500. `MVP7X-3v8xk` L300-308, L1019-1035, L1206-1217.
- **Trade management = essentially none, EXCEPT break-even when a session open will hit mid-trade.** Not a profit-trail.
  - `UVKVSWKFlvo` L155-159: "I **do recommend going break even if the market's going to open while you're in a trade**, just because you have crazy wicks like this."
  - `MVP7X-3v8xk` L167-169: "I would move stop to break even, but I'm in drawdown, so I don't need to" (only moves to BE once price is past entry).
- **Re-entry after a wick-out:** if wicked out of a pre-open reversion by the open candle, re-enter on the next BoS in the same direction. `UVKVSWKFlvo` L164-168.

## Sessions, windows, cutoffs (NEW or precise)

- **NY a.m.:** trade 9:30 → **11:00 cutoff** (volume dies; "I really don't want to trade after 11 because it always just drifts straight up"). `MVP7X-3v8xk` L552-558; `UVKVSWKFlvo` L207-208; `7UXiI2arAlQ` L156-158, L201, L322-325.
- **Dead zone 11:00–13:00:** don't trade. `7UXiI2arAlQ` L77-82, L258-260.
- **2:00 pm session:** new fair-price line at the 2pm open; fade moves away from it, same entry model. `7UXiI2arAlQ` L82-98, L254-272.
- **6:00 pm futures reopen** = a fair price (1hr closed → "priced at a good price"). Continuation in direction of opening candle / gap, then reversion to 6pm open. `GMDUiamqgig` L1-11, L24-44.
- **8:00 pm Asian open** = another fair line; opens fairly "**unless it's very far away from the 6pm**," in which case trade back toward 6pm. Asian continuation = toward 6pm open / unfilled gap. Done ~9:30 pm. `GMDUiamqgig` L45-64, L129-131.
- **Sunday 6pm opens are MORE fair** (48 hrs to price in vs 1 hr on weekdays). `GMDUiamqgig` L223-229.
- **8:30 am news** treated as a session open; reversion target becomes **pre-news** price; red-folder 8:30 news "is always priced in." `UVKVSWKFlvo` L131-153; `7UXiI2arAlQ` L205-213.
- **4:00 pm** = prop-firm forced exit (relevant to news-drift holds). `MVP7X-3v8xk` L824-829.

## Follow-up trades / 2nd attempts (NEW)

- **Pattern per session = 1 continuation + 1 reversion as the baseline**, but he takes MULTIPLE reversion attempts if price keeps making fresh unfair moves back away from fair price, each off a new BoS, until 11:00. `MVP7X-3v8xk` throughout (e.g. L676-680, L704-711 takes a 2nd/3rd short same morning).
- "I do take a lot of trades just because I feel like I know it's going to revert... if I get stopped out, **I'm ready to go on another account. That's how I'm getting through so many trades per day.**" `MVP7X-3v8xk` L728-735. (Implies running many prop accounts in parallel, re-firing the same setup.)
- After a losing continuation he immediately looks for the reversion ("continuation was not a win... now we'll just look for a reversion"). `MVP7X-3v8xk` L112-114.

## Sizing / contracts / risk (NEW or precise)

- **Default 1 contract; HALF size (0.5) when opening candle is large (>25 pts) OR when very close to fair price** so the fixed-$ target still fits. `MVP7X-3v8xk` L18-23 (33-pt open → half), L160-166 (exactly 750 to fair → 0.5), L430-433 (open >25 → 0.5).
- **More points to fair price → can size down and still profit** (small stop, big runway). Explicitly framed as a **win-rate optimization** he wasn't sure he'd reveal. `MVP7X-3v8xk` L77-87: "you can change the amount of contracts you use based on how many points to the fair price... a little optimization you can do to help increase your win rate." Also L1219-1226 ("such small stops like 25 points... win a little bit more than 20% to be profitable").
- **Fixed dollar bracket in backtest: −$500 / +$750 per trade** (= the 1:1.5). `MVP7X-3v8xk` L26-27, L108, repeated.
- **Risk tuned for prop DD rules:** props are "−2,000 to +3,000" → 1:1.5 to pass. `UVKVSWKFlvo` L178-182. 50k account loss limit = $2,000 = 4%. `MVP7X-3v8xk` L1239-1257.
- **Consistency rule** caps daily win at ≤ half the target on eval accounts → he caps targets (e.g. 1500). `MVP7X-3v8xk` L1028-1035, L1206-1217.

## Concrete numbers

- `MVP7X-3v8xk` May backtest stats (FX Replay, his own marking — **in-sample, no costs, manual**):
  - "**67% win rate**" (L1258); later restated "**56 trades and I won 37**" (≈66%) (L1300-1301); also "2.67 trades per day" / "**56 trades**" / "6 red days" (L1270-1301).
  - Avg win 750 / avg loss 500 used for EV (L1302-1305). Optimized for **low max drawdown**; never hit −$2k intraday except on consecutive red days (L1240-1257, L1296-1298).
- `UVKVSWKFlvo`: claims **$1.3M from prop firms in 12 months** (L1-3). One reversion example gave **181 points** to fair price (~$3.6k/contract) (L252-258).
- `7UXiI2arAlQ`: claims **~$160k/month** in payouts ($83k props + $38k Topstep + $46k live) (L1-15). Pattern reverts "**95%**"/"**99.9%**" of the time (L116-118, L331-333).
- His own accounts: more aggressive (takes displacements) → **lower win rate, more trades, more $**. `MVP7X-3v8xk` L1276-1284.

## Contradictions / corrections vs our core notes

1. **TP number:** he says **38 / 76**, not 37.5. (38 = 1.5×25 exactly.) Keep 38.
2. **Fair-price anchor name:** core says "9:30 open candle"; in `7UXiI2arAlQ` he names it the **9:29 a.m. (EST) candle body** — "I can tell you for certain the candle is the 9:29 a.m. candle every single day" (L17-18), mark the **body** with a rectangle (L36-39, L107). Same idea (the candle straddling the open) but the precise anchor he states is the 9:29 candle, body-only (ignore wicks).
3. **"~20 trades/day"** is his LIVE multi-account pace; the clean single-account backtest was **~2.7 trades/day / ~56 in a month**. The 20/day comes from re-firing across many accounts. `MVP7X-3v8xk` L728-735, L1275.
4. **Continuation is per-session-open, not only the 9:30 open** — there are up to 4 session opens/evening (9:30, 2pm, 6pm, 8pm), each with its own continuation. Slightly broadens the core's "first 10-15 min" framing.
5. **No-trade-management** is *almost* right, but there IS a conditional **break-even-on-session-open** rule. Add it.

## Per-video novelty check

- `MVP7X-3v8xk` — **most novel.** Sole source for the mid-session fair-price RESET rule, the size↔bracket switch in practice, news-drift/tweet model, multi-account trade volume, May stats.
- `UVKVSWKFlvo` — confirms 25/38 & the >25pt→50/76 rule (clearest statement), 10-15min continuation window, pre-news reversion, 1:1.5 rationale, first-BoS.
- `7UXiI2arAlQ` — sole clear source for **9:29 candle body** as the anchor, 90-min window, 11-13h dead zone, 2pm session, "95-99.9% reverts."
- `GMDUiamqgig` — sole source for **6pm + 8pm Asian** sessions, "one continuation + one reversal per session," Asian-trades-toward-6pm-open rule, Sunday-open-more-fair.
