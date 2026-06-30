# PropFirmMath — Extraction v2 (JJ Simon's own explainer video)

Source: `transcript/transcript2_clean.txt` — "The EXACT Trading Strategy That Made Me $1.2M in 12 Months." JJ Simon's solo step-by-step walkthrough + a real prior-week trade review. Recorded Saturday the 28th; trades reviewed are Mon–Fri of that week. Extracted ONLY from what the video states. Cross-referenced against video-1 gaps (`EXTRACTION.md` §14, `QUANTIFY.md` §A4).

This video is FAR more mechanically explicit than video 1. Several load-bearing gaps now close.

---

## PART 1 — GAP RESOLUTION (priority)

### Gap 1 — "Fair price / fair pricing theory" — **[FILLED]**

The full theory, precisely:

- **Definition (corrected from v1):** fair price = **the 9:30 a.m. ET session-open candle / the candle at open**, NOT 9:29. He repeatedly marks "the candle pre-open" / "the opening candle" as fair price. `[CONTRADICTS v1]` — v1 said "9:29 ET"; v2 explicitly says **9:30 a.m.** is the fair price. (On news, fair price = "the candle before news," e.g. "the 29 candle" — i.e. the bar immediately preceding the news release.)
- **Why it's fair:** "the New York session open acts as the first major intraday reference point for fair auction." Nasdaq = 100 real companies with an actual long-term fair value (contrast Bitcoin "where the value is unknown… determined by an auction place of people agreeing"). So NQ has a real fair price; the open anchors it intraday.
- **Why moves away are "unfair":** "Early moves away from that price are often driven by opening flow, liquidity imbalances, stops, hedging, momentum, participation, not necessarily by a true, long-lasting repricing of the index." At 9:30 "all the overnight orders come in, all the banks start doing their trading" — an influx of participants creates a short-term auction-marketplace dislocation, not a true revaluation.
- **The trade thesis:** "I believe the 9:30 a.m. is the fair price. Any move away from that is unfair. So I would trade a reversion back to the opening price." That reversion = the "high time frame reversion."
- **Liquidity caveat (his own):** "I don't really believe liquidity is a very important part of Nasdaq just because it's so liquid." He explicitly does NOT believe stop-losses are hunted: "I don't believe stop losses are truly hunted. That's not really a thing." The edge instead = funds "taking advantage of uninformed participants."
- **News changes fair price; session open does NOT.** "News changes the inherent value of Nasdaq futures… News changes fair price, but opening session does not." On news, the average outcome is "already priced in" (insiders, quant funds, Polymarket), so the news volume spike is the unfair move to fade back to the pre-news candle.

> Evidence: "I believe the 9:30 a.m. is the fair price. Any move away from that is unfair. So I would trade a reversion back to the opening price."

Note: the deeper fair-pricing detail is gated to his paid one-on-one ("I do a lot more of that one-on-one, so it's like too complicated to explain here"). The public version is the above.

---

### Gap 2 — Break of structure / entry trigger — **[FILLED]** (this is the big one)

There are **two distinct entry triggers**, and he names exactly when each applies:

1. **Break of structure + close** (his A+ trigger): price **breaks a prior structure level and a candle CLOSES beyond it** ("break of structure and a close"; "as long as it closes below the structure that it broke"). "Structure" = a prior swing level — he points to a level that is "lower than these two points" as "a really important piece of structure." So a structure = a local swing high/low formed by adjacent candles. Entry fires on the **close of the candle that closes past that level**.

2. **Displacement candle** (his A trigger, used when there is no clean structure to close beyond): a **displacement candle** is defined mechanically and verbatim:
   > "a candle that's larger than the previous one and it doesn't really have any wicks."
   He enters on the **close of the first qualifying displacement candle** ("It is the first displacement that occurs"). Disqualifiers he states by example: too-large a wick relative to body → not displacement; not clearly larger than the prior candle → not displacement; must "close consistently above/below" the previous candle (a body that closes "way above" the prior, not just marginally).

**Decision rule between the two:** if there is a structure level available to close beyond, the break-of-structure-and-close is the higher-grade entry (A+). If "there's no structure here to close below, so you can enter on a displacement" (A). He trades **both** every day: "I am trading pretty much every displacement I see just because there's a slight bit of edge that I want to capture every single day."

**Setup grading (NEW, mechanical):**
- **A+** = both biases line up (HTF reversion + LTF continuation) **AND** break-of-structure + close. "Break of structure and a close is an A+ setup. It's a lot more likely to win."
- **A** = displacement only.
- **B / B+** = biases point opposite ways → "you definitely don't want to trade the B setups." (He'll occasionally take a B+ "just cuz I'm trying to trade all my accounts.")

This is the codable entry rule that was the #1 open gap in v1. Displacement = (body > prior body) AND (negligible wicks). BOS+close = candle closes beyond a prior swing level. Confirmation = candle CLOSE in both cases.

---

### Gap 3 — Direction / bias rule — **[FILLED]**

Direction is set by **two biases that must agree**, named "high time frame reversion, low time frame continuation":

- **High-time-frame (really "medium") reversion bias = direction back toward the 9:30 open price.** "By reversion, I just mean coming back to the opening price." If price is ABOVE the open → bias short (revert down); if BELOW → bias long (revert up).
- **Low-time-frame continuation bias = direction of the most recent short-term momentum** (the recent run of candles). "By continuation, I just mean… this series of green candles or the series of gray candles."
- **A+ only when both align.** Example (Monday): "We are getting a high timeframe reversion because it's gone up, and we're getting a low timeframe continuation because it's gone down recently" → both point down → short.

**The opening-candle direction sets the FIRST trade's side specifically:**
- First trade = **continuation of the opening candle's direction.** "The only way you want to look for a continuation is short because the first candle was red, which means the overnight orders were mostly short." Green open → look for longs first; red open → shorts first.
- After the initial unfair move, flip to **reversion back toward the open** (fade). On a green-open day he refused continuation shorts: "the opening candle right here was very green, so I wanted longs to start. And then after this initial displacement up, sort of just trade reversion."

So per setup the long/short decision = (a) first trade follows open-candle color; (b) thereafter, fade toward the open price; (c) only take it when LTF momentum also points that way (A+), else it's a weaker A/B.

---

### Gap 4 — Continuation entry — **[FILLED / PARTIAL]**

- **Trigger:** SAME mechanical trigger as everything else — break of structure + close, or a displacement candle — just in the open-candle's direction. First-trade example: "break of structure and close or displacement… it broke this structure right here… it closed below. So I was predicting on a displacement away from the opening price."
- **Timing window:** continuation is ONLY the **first 0–10 minutes** of the session. "Continuation. I only trade it in the first 5 to 10 minutes or I guess like 0 to 10 minutes. Like I'm looking for my first trade pretty much instantly. After 10 minutes, I'm going to look for mean reversion." `[NEW vs v1]` — v1 never gave the 0–10 min continuation window.
- **Direction:** open-candle color (Gap 3).
- PARTIAL only in that there's still no separate confirmation rule for continuation vs reversion — they share the displacement/BOS+close trigger. That's actually the resolution: there is no different trigger.

---

### Gap 5 — Per-trade win rate — **[PARTIAL]** (first real number ever stated)

Video 1 gave NO per-trade win rate. Video 2 gives **one stated figure, for an A+ setup only**, hedged:

> "It's a displacement, everything A+ setup, like 100% going to win this trade. Maybe not 100, maybe like **70 to 80**, but that's really good cuz it's 1 to 1.5."

So: **A+ setup ≈ 70–80% claimed win rate** (self-reported, single offhand estimate, no sample). No win-rate number is given for plain A (displacement-only) or B setups. He still insists for backtesting that win rate per trade "does not matter" — only pass rate matters (see Gap 8 / Part 3). Treat 70–80% as an unverified ceiling for the best setup, not a measured strategy win rate.

Also a directional data point: the reviewed week's trades net roughly break-even-to-slightly-positive by his own tally (see Part 2): days went 4-0, 3-0, 3-2, 1-2, 1-0 → **12 wins / 4 losses across the week as he narrates them** (≈75%), but small sample and self-selected.

---

### Gap 6 — R:R and static SL/TP — **[FILLED]** (exact point values now given)

- **Primary R:R = 1 : 1.5**, used on every example trade in the video. "for all these trades, I'm just going to be using a 1 to 1.5 risk to reward."
- **Exact static values:** **25 points stop loss, 38 points take profit.** "I'm just going to have all of them be **38 points TP, 25 points stop loss**, and then you can choose your contract sizing based on your risk aversion." (38/25 = 1.52 ≈ 1.5.) On news he rounds: "I'll just set it to 38. .25 is just the average what I do" / "38, 25… 1.5."
- **Why 1:1.5:** matches the firm's target:maxloss ratio. "most evaluations are plus 3,000 before they're minus 2,000… that's three to two, which is 1.5 risk to reward… you can sort of just compact the entire challenge into a 1 to 1.5." Same logic as v1.
- **Sizing is via CONTRACT SIZE, not via changing SL/TP.** SL/TP points are fixed (25/38); the dollar risk per firm is set by how many contracts/micros you trade. "you can choose your contract sizing based on your risk aversion." This resolves the v1 ambiguity about how per-account dollar risk varies: **points constant, contracts variable.** `[NEW vs v1]`
- **Funded exception:** on funded you MAY extend TP beyond 38 to capture the full reversion to the open: "you can move this take profit up to all the way up here… if you want to capture more points on a funded account." On the Thursday reversion he ran a runner past 1:1 ("pretty confident at a 1 to 1 when it got back to here and then just letting it run for the rest") — a funded-style variation. (See Gap 8.)

---

### Gap 7 — Session schedule — **[FILLED / CORRECTED]**

Stated session list (ET), verbatim: "the **6:00 p.m.** when the market reopens, **8:00 p.m.** Asian session, **3:00 a.m.** London session, **8:30 a.m.** when there's news, **9:30 a.m.** Eastern, and then **2:00 p.m.** Eastern for the New York PM session."

vs v1's (08:30 / 09:30 / 11:00 / 14:00 / 18:00 / 20:00):
- **CONFIRMED:** 8:30 (news), 9:30 (NY AM), 2:00 PM (NY PM), 6:00 PM (reopen), 8:00 PM (Asian).
- **NEW:** **3:00 a.m. London session** (not in v1's list). `[NEW vs v1]`
- **CHANGED:** the v1 "11:00 a.m." is NOT a separate session — it's the **cutoff** where he stops trading the morning block. `[CONTRADICTS v1]` — v1 listed 11:00 as a session entry with "1 longer trade." v2: "I usually stop looking for trades at 11:00 or just whenever the volume dies out." See Gap 9.
- **Per-session structure:** **1 continuation (first 0–10 min) + up to 3–4 mean-reversion trades (10–90 min)**, max. "Three to four trades max." Reversion window = **10 min to 90 min** after open. "continuation is the first 10, mean reversion is just after that… from 10 minutes to 90 minutes."
- NY open is the primary session: "what I'm looking for is the New York session open. It's like the main session… to trade for me."

---

### Gap 8 — Funded vs eval difference — **[PARTIAL]** (more than v1, still thin)

v1 said "incredibly different" but never described funded. v2 gives concrete differences but still centers the eval/reversion engine:

- **Same entry engine on both.** The trade triggers (displacement / BOS+close, fair-price reversion) are identical. The difference is risk/target management:
- **Eval = fixed 1:1.5 (25/38 pts), no runners.** "at least on your evaluation, you should be using [1:1.5]."
- **Funded = you may extend TP / let it run to capture more points.** "if you want to capture more points on a funded account… you can move this take profit up to all the way up here." The Thursday trade demonstrates a funded-style runner (take 1:1, "just letting it run for the rest").
- **Funded = pick which account by points available in the market.** "trading a different prop firm account based on what I'm seeing… some days I'll see 50 points on a reversion, some days 20. Based on that, you should trade a different prop firm because each prop firm you should be using a different risk on." More points available → trade the firm/account that needs more points. `[matches v1 funded "pick account by R:R offered"]`
- Still NOT a fully separate "strategy" in this video — funded ≈ same engine, variable TP, account-selection-by-points. The "incredibly different" framing of v1 is softened here to "I have a very different specific risk management approach… it's whatever works best for you."

---

### Gap 9 — The 11:00–14:00 "longer hold" trade — **[STILL UNCLEAR / likely does not exist as v1 described]**

This video gives NO 11:00→2:00 longer-hold trade. Instead **11:00 is the morning stop-trading cutoff**: "I usually stop looking for trades at 11:00 or just whenever the volume dies out." The 2:00 PM NY-PM is its own fresh session (continuation + reversions), not a hold from 11:00. So the v1 "1 longer trade held 11:00→2:00" appears to be a misread of the interview; v2 does not support it. `[CONTRADICTS v1]`

---

### Gap 10 — Break-even / exit-management exceptions — **[PARTIAL / shifted]**

- v2 does NOT re-state the explicit "go BE if a new session opens / if news imminent" rules from v1. Not contradicted, just not repeated.
- v2's stated exit behavior: trades run to the **static 38-pt TP or 25-pt SL**; **no partials/BE** on eval.
- **Re-entry rule (NEW):** if stopped out by an unfair displacement against you, **re-enter immediately.** "Usually, if I get stopped out, it's due to a displacement down, which is unfair, and then I can just reenter instantly, which is what happened here." `[NEW vs v1]`
- **Funded runner (NEW):** on funded, after price reaches the open (≈1:1) he may let the remainder run rather than fixed-TP, because "once it gets back to the opening price… it's pretty much random from there." `[NEW vs v1]`
- News caution: avoid being in a trade when 9:45/10:00 a.m. news prints ("you don't want to be in a trade when 9:45 or 10:00 a.m. news comes out") — a niche timing exception, loosely the analog of v1's "go BE for news." `[PARTIAL]`

---

## PART 2 — THE WEEK-OF-TRADES WALKTHROUGH

Instrument throughout: **Nasdaq futures (NQ/MNQ), 1-minute chart** (5-min only when volume is dead). All trades **1:1.5, 25-pt SL / 38-pt TP** unless noted. Session = 9:30 NY AM unless noted. He states it's his literal prior week, un-cherry-picked.

**FRIDAY (9:30 NY AM) — described first, in most detail**
- T1 — **Short, continuation.** Open candle red → overnight orders short → look short only. Trigger: broke a structure and **closed below** it (open candle had wicked the level so he waited for the clean close-below). Entry on BOS+close. Outcome: **WIN** (implied; "first short, continuation of this move," no loss noted).
- T2 — **Long, mean reversion** back toward open. No structure to close above, so entered on a **displacement candle** ("no wick down here… bigger than this entire previous candle… right when this one closes up here, I'm trading a mean reversion"). Price tapped the opening candle then continued — edge ran from entry up to the open. Outcome: **WIN** (implied).
- T3 — **Short, continuation** (late, unusual). "most perfect short setup," previous structures visible, "incredible displacement down, closed right below the structure," 38 pts ≈ exactly to a prior low. Graded A+→A only because late in the time window. Outcome: **WIN** (implied).
- T4 — **Long, mean reversion.** Waited through a choppy box (no valid displacement — too many wicks), then "volume spike… close above this box," longed. Outcome: **WIN.**
- Friday tally stated: not explicitly summed, but all four read as wins.

**THURSDAY (9:30 NY AM) — "a very good day… four wins" (posted on Instagram)**
- T1 — **Short, continuation.** Closed below structure. "short 25, 38 take profit." "almost stopped me out, but it was a win." Outcome: **WIN.**
- T2 — **Long, mean reversion** back to open. Skipped an early displacement (wick too big), waited for a key structure; "pretty confident we'd come back to at least the top of this opening candle." Ran it as a **funded-style runner** past 1:1 ("confident at a 1 to 1 when it got back to here and then just letting it run"). Entry reason: break of structure, close above. Outcome: **WIN.**
- T3 — **Short, reversion** back to open (graded A→B+ because price was already at fair price). Closed below a bit of structure. Outcome: **WIN.**
- T4 — **Short, reversion off a displacement candle** (first true displacement: bigger body than prior, no wicks, consistent close below). Outcome: **WIN.**
- Thursday tally: **4 wins / 0 losses** (he labels it "another three for three day" mid-narration but explicitly calls the day "four wins").

**WEDNESDAY (9:30 NY AM) — "win, loss, win, loss, win" → 3 and 2**
- T1 — **Long, continuation.** Open candle marked as fair price; "displacement up, close above here, very good for a long." Outcome: **WIN.**
- T2 — **Short, reversion** back to open (~38 pts back to opening price). Good displacement candle. Outcome: **LOSS** ("This one did lose. That is totally okay.").
- T3 — **Short, reversion.** Closed below structure, displacement, "everything A+ setup… maybe like 70 to 80[% to win]." Outcome: **WIN.**
- (Then a green-open segment) — refused continuation shorts because open candle was very green (wanted longs); after initial displacement up, traded reversion.
- T4 — **Long, mean reversion** off a displacement candle (not ideal entry, some points in favor). Outcome: **LOSS** — "This one did get stopped out." Then **re-entered instantly** (stop was caused by an unfair displacement down).
- T5 — **Long** re-entry, displacement close (admits he should have entered a bar earlier; closed almost above prior). Outcome: **WIN.**
- Wednesday tally stated: **"win, loss, win, loss, win… three and two, so three out of five."**

**TUESDAY (9:30 NY AM) — "not the best day" → 1 win / 2 losses**
- T1 — **Long, continuation.** Forced to long at the top of the last 30 min because the opening candle had large wicks (wished it had closed clean). "Not my favorite to long at the all-time high of the last 30 minutes, but… I always follow the strategy." Outcome: **LOSS** ("Unfortunately, it doesn't play out").
- (missed) — notes a textbook mean-reversion short he didn't mark/take (displacement candle, closed below) — possibly skipped for too-few points.
- T2 — **Long, reversion** back to open off a displacement (body larger than prior, no wicks). Outcome: **LOSS** ("This one stopped out").
- T3 — **Long** re-entry, another displacement, close above. Outcome: **WIN.**
- Tuesday tally stated: **"two losses and one win."**

**MONDAY (very low volume — used 5-minute chart) → 1 trade**
- Monday "absolutely no volume," wicky open, so dropped to the **5-minute** and "trade the exact same strategy." Took exactly **one trade.**
- T1 — **Short.** Open = fair price; price went up (HTF reversion = down) and recently went down (LTF continuation = down) → both align → short. Trigger: break of the only real structure + **close below** on the 5-min. Points in favor back to open. Outcome: not explicitly won/lost ("I just took one trade today, and it was just this short" — narrated as the clean textbook example, implied fine). Counted as 1 trade.

**PATTERN across all examples (key for reverse-engineering the mechanical rule):**
1. **Mark the 9:30 open candle = fair price.** Every single day starts here.
2. **First trade = continuation in the open-candle's color, in the first ~10 min,** triggered by displacement OR BOS+close.
3. **All subsequent trades = fade back toward the open** (reversion), each triggered by a fresh displacement candle or a BOS+close, taken after consolidation.
4. **Entry confirmation is always a candle CLOSE** (close beyond structure, or close of a clean displacement candle = body bigger than prior + minimal wicks).
5. **Skip entries that are at/inside the fair-price zone** ("you're already at the session open, so there's no point reverting") and skip entries with too-few points to the open.
6. **Fixed 25/38 pts, 1:1.5**, contract size set per firm.
7. **Stop trading ~11:00 a.m. / when volume dies.** Drop to 5-min when volume is dead.
8. **Stopped out by an unfair displacement → re-enter immediately.**
9. He takes **essentially every A/A+ he sees** (and some B+) to maximize daily exposure across 40 accounts.

---

## PART 3 — NEW / CONTRADICTORY

**NEW (not in v1):**
- **Displacement candle = explicit definition:** body larger than previous candle + (almost) no wicks. This is a second, co-equal entry trigger alongside BOS+close. v1 only had "break of structure."
- **A+ / A / B+ / B setup grading** with explicit criteria (biases-aligned + BOS-close = A+; displacement = A; biases-opposed = B).
- **0–10 min continuation window; 10–90 min reversion window; 3–4 reversion trades max.** Precise timing v1 lacked.
- **3:00 a.m. London session** added to the session list.
- **Exact static points: 25 SL / 38 TP.** v1 only had dollar examples (1000/2000 etc.), never points.
- **Sizing = contract size, points held constant.** Resolves how per-firm dollar risk is set.
- **Re-enter instantly after an unfair-displacement stop-out.**
- **A+ ≈ 70–80% win** (first per-trade win-rate number anywhere).
- **5-minute fallback** when volume is dead (Asian / NY-PM / Monday).
- **Backtesting method (whole new section):** do NOT backtest as a live equity curve; simulate the **prop-firm wrapper** — one trade/day, end-of-day trailing drawdown that ratchets up on winning days and **stops trailing at the starting balance** (50k acct: DD floor climbs 48→49→50 then locks at 50k; pass = hit 53k before DD). Equity "teleports" per day (win or lose, no intraday curve). Output you need = **pass rate**, then average-cost-to-funded = eval cost ÷ pass rate (e.g. $100 ÷ 33% = $300). "You do not need your average profit, your sharp ratio, your expected profit per trade, your win rate. That does not matter. The only thing that matters is [pass rate]." This is a near-complete spec for the Monte-Carlo wrapper in v1 open-question #10.
- **Firm-level payout proof (1099 tax forms):** Topstep $250k + RiseWorks $450k last year; spend on evals **$200–250k**. Per-firm payout screenshots: E8 Futures 172k, Lucid ~75k, TradeFi ~100k, Apex ~60k, FundedNext 67k, Alpha Futures ~75k.
- **Copy-trading caution:** don't copy-trade until you know exact pass rate / payout chance / avg payout AND risk-of-ruin <5%; "if you have more than $10,000, it's fine to start," else avoid. He runs **40 accounts, copy-trading 5 at once.** `[partially NEW — v1 had 40 accounts but framed layering differently]`

**CONTRADICTIONS vs v1:**
- `[CONTRADICTS v1]` **Fair price = 9:30 open candle**, not 9:29. (v1 §6/§8: "9:29 a.m. ET pre-open." v2: "I believe the 9:30 a.m. is the fair price.")
- `[CONTRADICTS v1]` **11:00 a.m. is a stop-trading cutoff, not a session with a longer hold.** (v1 §8: "~11:00 a.m. — 1 longer trade held 11:00 to ~2:00." v2: "I usually stop looking for trades at 11:00.")
- `[CONTRADICTS v1]` **Total payouts = $1.2M in 12 months** here vs **$1.5M in <18 months** in v1. Also reframed: "14k off a million in my first year… started in February or March." Different headline number, different window. (Both self-reported; v2 backs it with 1099s.)
- `[CONTRADICTS v1, mild]` **Live-account edge = "1 to 5%"** and strategy would "probably break even" on live. v1 also said live edge low, but v2 is blunter that the strategy is prop-firm-specific and likely just break-even live.
- `[SOFTENS v1]` Eval-vs-funded "incredibly different" (v1) → in v2 it's the **same entry engine** with different TP/account management. Not a contradiction of mechanics, but a softer framing.
- `[CONTRADICTS v1, mild]` Mean-reversion window now explicitly **medium time frame** ("more of a medium time frame reversion"), and he keeps correcting his own "high time frame" label. v1 took "high time frame bias" more literally.

---

## PART 4 — CONCRETE NUMBERS LEDGER (this video)

Payouts / money:
- **$1.2M** total payouts in **12 months** (headline).
- **$250k** Topstep + **$450k** RiseWorks paid last year (per 1099s).
- Per-firm payout screenshots: **E8 172k**, **Lucid ~75k** (in 1–2 months), **TradeFi ~100k**, **Apex ~60k** (then banned, no reason), **FundedNext 67k**, **Alpha Futures ~75k**.
- **$200k–250k** spent on evals (under "education / business services").
- "**14k off a million**" in first year.

Strategy mechanics:
- **R:R = 1 : 1.5** (every example).
- **SL = 25 points; TP = 38 points** (38.25/25 on news, ≈1.5).
- **Continuation window = 0–10 min** after open.
- **Reversion window = 10–90 min** after open.
- **Max 3–4 reversion trades** per session.
- **Stop-trading cutoff ≈ 11:00 a.m.** (or when volume dies).
- **A+ win rate ≈ 70–80%** (self-estimate, A+ only).
- Setup grades: **A+** (biases aligned + BOS-close), **A** (displacement), **B/B+** (biases opposed — avoid).
- Points-available examples for account selection: **"some days 50 points on a reversion, some days 20."**
- Live-account edge if traded there: **"1 to 5%."**

Accounts / scaling:
- **40 accounts**, **copy-trading 5 at once.**
- Copy-trade safety threshold: **>$10,000** bankroll; **risk of ruin < 5%.**
- Eval cost example: **$100.**
- Pass-rate example: **33%** → average cost to funded **$100 ÷ 0.33 = $300.**
- Backtest account math: **50k account**, DD floor climbs 48→49→50k then **locks at 50k**; **pass = reach 53k** before DD.
- Loss aversion: emotional value of a loss = **2×** the value of a win.

Sessions (ET): **3:00 a.m.** London, **8:30 a.m.** news, **9:30 a.m.** NY AM (primary), **2:00 p.m.** NY PM, **6:00 p.m.** reopen, **8:00 p.m.** Asian.
Niche: avoid open trades into **9:45 / 10:00 a.m.** news. Main news = **8:30 a.m. red-folder.**

Instrument: **Nasdaq futures (NQ)**, **1-minute** chart (**5-minute** fallback when volume dead).

---

## PART 5 — UPDATED OPEN QUESTIONS (what STILL can't be quantified)

Resolved by v2 (were open in v1): break-of-structure trigger (now: close beyond a prior swing level), displacement trigger (body>prior + minimal wicks), direction rule (open-candle color first, then fade to 9:30 open, both biases must agree), exact SL/TP points (25/38), continuation window (0–10 min), reversion window/count (10–90 min, ≤3–4), fair price (= 9:30 open candle), sizing mechanism (contract size, fixed points), backtest wrapper spec (one-trade/day + ratcheting trailing DD locking at start balance), 11:00 cutoff. These are now codable.

**Still unquantified / requires assumptions before a clean backtest:**
1. **"Structure" / swing-level detection threshold.** He points at levels visually ("lower than these two points") but gives no bar-count/fractal lookback or minimum swing size. Need a concrete swing definition (e.g. N-bar fractal) — he never numerically specifies it. This is the last fuzzy edge of the entry rule.
2. **Displacement size threshold is qualitative.** "larger than the previous one" and "no real wicks" — needs a coded cutoff (body ≥ X× prior body? wick ≤ Y% of range?). He even waffles on a "50/50… yes, no, yes" candle. Some discretion remains.
3. **"Points in your favor" minimum.** He skips reversions with too few points to the open (Tuesday missed short) but never states the minimum point distance that makes a reversion tradeable.
4. **Which firm/account per trade** = "based on points available" but the exact mapping (50 pts → which account/contract size) is gated to the paid one-on-one.
5. **Mean-reversion exhaustion / when price "is already at fair price."** He downgrades setups inside the open zone but the zone width (how close = "already there") is eyeballed.
6. **Per-setup win rates for A and B** — only A+ got a (hedged) 70–80%. Real per-grade win rate must be measured, not assumed.
7. **Payout-chance and average-payout** inputs to the funded EV are still self-reported (33% pass × 33% payout from v1), not derived here.
8. **News fair-price shift** ("news changes fair price") is asserted but the magnitude/handling is explicitly withheld ("too complicated to explain here… I do a lot more one-on-one").
9. **Discretion remains despite "mechanical" claim** — he repeatedly says "I should have entered here," "honestly it's whatever works best for you," takes/skips B+ situationally. The rule is more mechanical than v1 suggested but not fully deterministic.

Net: the **per-trade signal is now ~80% codable** (displacement + BOS-close + fade-to-9:30-open + 25/38 pts + session windows). The two remaining coding blockers are the **swing/structure detection rule** and the **displacement-size cutoff** — both left qualitative. The **prop-firm wrapper** (pass-rate Monte-Carlo with ratcheting trailing DD) is now well enough specified to build directly.
