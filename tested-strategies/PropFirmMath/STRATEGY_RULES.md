# PropFirmMath — Consolidated Strategy Rules (Layer A signal)

Single mechanical source of truth for the JJ Simon "Fair Value Theory" NQ signal, integrating
all sources. Supersedes the scattered rule fragments in QUANTIFY §A. Provenance tags:
`[v1]` interview, `[v2]` JJ's own video, `[fx-pdf]` FX Replay strategy deck, `[fx-test]` FX Replay
backtest video, `[assume]` my fill (sweep/validate), `[user]` your proposal.

Sources: [`EXTRACTION.md`](EXTRACTION.md) · [`EXTRACTION_v2.md`](EXTRACTION_v2.md) ·
[`EXTRACTION_v3_fxreplay.md`](EXTRACTION_v3_fxreplay.md) · PDF text in `transcript/pdf_fairvalue_text.txt`.

---

## 0. Empirical status — FIRST real win-rate data (verified)

Until now Layer A had no measured win rate. FX Replay ran an **independent manual backtest** in
their replay tool. Numbers below are **verified against `transcript3_clean.txt`** (line refs).

| Slice | Trades | Win rate | Profit factor | Total R | Source |
|---|---|---|---|---|---|
| **Aggregate (all windows)** | **158** | **54%** | **1.76** | — | L1328, L1347–48 |
| Continuations (trigger 1) | — | higher | **>2.0** | **36R** | L1352–56, L1555 |
| Mean reversions (trigger 2) | ~67 | **49%** | **1.46** | **15R** | L1410–18, L1463 |
| Feb 2026 (~half month) | 43 | 58% | — | 19R | L1230–45 |
| Apr–May 2025 uptrend | — | 56% | 1.93 | — | L1264–69 |
| **Before time-filter opt** | 150 | 52% | 1.66 | 46R | L1595–96 |
| **After time-filter opt** (in-sample) | — | **62%** | **2.46** | — | L1600–02 |

**Gross expectancy at 54% WR / 1.5R = `0.54·1.5 − 0.46·1 = +0.35R/trade`** (before costs).
→ Layer A shows **positive GROSS in-sample expectancy** — the first evidence the signal clears the
40% break-even hurdle (§7). **This does NOT mean it works.** Per repo validation rules, treat as
**provisional / in-sample only.** Missing checks: **no walk-forward / OOS**, **no costs deducted**
(commission+spread+slippage on 1-min NQ scalping — host flags live execution as "hard"), dataset is
a **hand-picked stitch of regime windows** (not continuous), and the 62%/2.46 came from **in-sample
time-of-day filtering on the same data** (overfit risk). Host's own caveat: "I'm sure there's also
periods that you have 30% win rates" (L1651–54).

---

## 1. Instrument & timeframe
- **NQ futures, 1-minute bars.** `[v1][v2][fx]` Backtest on NQ/MNQ. Costs MUST be modelled `[assume]`.

## 2. Fair value (the reference price)
- **Two anchors** `[fx-pdf]`: the **09:30 ET open candle** price AND the **14:00 ET (2pm) open** price.
  Drawn as a horizontal line; "what price opens" at each session `[fx-test L256–264]`.
- On 08:30 news: fair value = candle *before* the release `[v2]` (news block — not tested by FX Replay).
- Theory: with no new info, price reverts to fair value `[fx-pdf]`. (v1's "9:29" was imprecise → 9:30.)

## 3. Session windows & timing (ET)
- **NY AM:** 09:30, trade window first **~90 min** (→ ~11:00). `[fx-pdf]`
- **NY PM:** 14:00, cut off ~**15:00** `[fx-test L196–198]`.
- Continuation hunt = **first ~10–15 min** after each open (away from FV); mean reversions =
  **rest of the window** (back to FV). `[v2][fx-pdf]`
- Optional/untested: 03:00 London, 20:00 Asia (Asia only on volume/volatility surge), 08:30 news. `[fx-pdf]`

## 4. Structure break — BOS vs MSB `[fx-pdf]`
- **Break = a candle CLOSE past the wick high/low of the recent price leg** (a wick alone is NOT
  enough; needs a clear swing point — host eye-test L708–723).
- **BOS** (break of structure) = continuation direction → used for **continuation** entries.
- **MSB** (market structure break) = close past recent leg H/L signalling **reversal** → used for
  **mean-reversion** entries.
- Used roughly interchangeably mechanically; the distinction is which direction the trade faces.

## 5. Decisive / displacement candle — THE entry-trigger candle
This was the load-bearing undefined rule. FX Replay mechanized it. **Two independent gates:**

**Gate 1 — decisive close (CORE, mechanical):** the **counter-wick** (the wick *against* the close
direction) must be **≤ ~20%** of the candle. `[fx-pdf][fx-test L121–132, L573–84, L892–94]`
```
direction = sign(close - open)
range = high - low                       # guard > 0
bullish: counter_wick = open - low       # rejection below an up-close
bearish: counter_wick = high - open      # rejection above a down-close
DECISIVE  ⇔  counter_wick / range ≤ 0.20     # 0.20 = sweepable; FX Replay fib 0/0.2/1
```
Exact fib anchor (open→extreme vs full range) is slightly ambiguous in the source — **confirm
against FX Replay video frames during P1**; intent is unambiguous (small rejection = decisive close).
Equality at the 0.2 level was allowed at host discretion (L668–77).

**Gate 2 — size (OPTIONAL, explicitly NOT used by FX Replay):** JJ says "ideally larger than the
candles before it," but FX Replay **deliberately dropped size** as "too discretionary" and still got
54% WR. `[fx-test L133–138, L172–175]`
- **Your proposal** `[user]` is a clean way to mechanize this optional gate IF we want to test it:
```
SIZE_OK  ⇔  range ≥ m · mean(range, last L bars)     # m ∈ {1.2, 1.5}, L ∈ {4,5,6}
```
- **Implement as a togglable confluence, default OFF.** The backtest then *measures* whether the
  size filter adds edge — which is the open question FX Replay left (they got their result with
  **no** size gate, so size is unproven, not required).

**Gate 3 — SAME-CANDLE requirement (CRITICAL refinement):** the structure break AND the decisive
candle must occur on the **same candle**. `[fx-test L591–599, L995–97, L808–13]` Displacement
without a same-bar break (or vice-versa) is a lower-probability/skip. This is the "A+ combination."

## 6. Entry triggers
- **Trigger 1 — continuation:** after price moves away from FV in the first ~10–15 min, enter on a
  same-candle **BOS + decisive candle** in the move's direction. `[fx-pdf]`
- **Trigger 2 — mean reversion:** after price has extended away, enter on a same-candle **MSB +
  decisive candle** oriented **back toward FV**, for the rest of the window. `[fx-pdf]` Trade either
  side of FV. Skip if TP would land far **beyond** FV (low probability; optional BE if price taps FV). `[fx-test L724–45, L1056–79]`
- **Trigger 3 — follow-ups (YOUR point — EXCLUDED from the FX Replay 158-trade test):** `[fx-test §4]`
  - **(a) 2nd attempts / re-entries after a loss** — JJ does these frequently `[fx-test L356–66]`.
  - **(b) second-move continuations & mean reversions** after price has already reverted (e.g. a
    continuation ~33 min post-open, past the first-move window) `[fx-test L388–409, L854–82, L976–84]`.
  - FX Replay's 158 trades are **first-move-only** → JJ's real frequency/results are a **superset**.
    Direction of effect unknown (host: could add frequency, could offset weak 2nd-hour windows).
  - **Engine: tag follow-ups separately ("trigger 3") so we measure base vs base+followups** — exactly
    as FX Replay advise ("collect the data to confirm"). Resolves your observation directly.

### 6b. JJ's ACTUAL continuation logic (his own words — corrects the "2 setups/day" simplification) `[v2]`
The "continuation 3–15 min then reversion = 2 setups" model is FX Replay's **base simplification**.
JJ's own video shows continuations recur all session. Verified quotes (transcript2):
- **"high time frame mean reversion, low time frame continuation"** (L83–84). "Continuation" = TWO things:
  - (a) the **opening** continuation of the first unfair (overnight-order) move — early only: *"you don't
    want to look for continuations too far after the open"* (L548–552).
  - (b) a **low-timeframe ENTRY style** used on EVERY trade (incl. reversions): *"by continuation I just
    mean like this series of green candles"* (L592–606). Bias = HTF reversion to fair; entry = LTF momentum.
- It is a **repeating cycle**, not one continuation + one reversion: unfair move → continuation away →
  reversion to fair → *"this move up was unfair, so I was going to trade another reversion"* (L611–614) →
  and when price breaks away again (fair price having reset on consolidation) a **fresh continuation** is
  valid → "continuation with the trend after the reversion period" (user's chart obs, JJ video ~14:05).
- **Implication for our model:** continuation = a displacement/BOS away from the **current (dynamic)
  fair price**, **per-session-open** (9:30/2pm/6pm/8pm — "one continuation + one reversal per session"),
  each gated to that session's first ~10–15 min; NOT recurring within a session. "With-the-trend later" =
  the separate **news-drift** mode. `[channel sweep]`

### 6c. Fair-price RESET rule — RESOLVED by the 19-video channel sweep (was the #1 open question)
Full detail + quotes: [`EXTRACTION_channel.md`](EXTRACTION_channel.md) §A1–A4. Fair value is **dynamic**:
- Default anchor = **9:29 ET candle BODY** (ignore wicks). *"9:29 is not always the fair price."*
- **Resets only on: news, session opens, AND an intraday volume-spike consolidation** — if an unfair move
  spikes on volume and **consolidates at a new level instead of reverting, redraw FV to that consolidation**
  ("most recent consolidation = fair price"). Two candidates → mark the middle. No reset on fake news.
- **News split:** expected news → fade to the **8:29 candle body** (his highest-WR trade); unexpected/tweet/
  regime → **continuation + reset** FV to the post-news consolidation; news SL/TP arbitrary (not 25/38).
- **Sizing beyond ATR:** signal-candle body **>25 pts → halve contracts, 50/76**; confidence-scaled
  ("risk higher when win-chance higher"); closer to FV → size down + bigger runway. TP **38** = his round of 1.5×25.

## 7. Exits — ATR-bucketed, fixed 1.5R, NO management `[fx-pdf][fx-test L282–98]`
| 1-min ATR | SL (pts) | TP (pts) | NQ contracts for ~$1k risk |
|---|---|---|---|
| > 20 | 50 | 75 | 1 |
| 7–20 | 25 | **37.5** | 2 |
| < 7 | 16.5 | 24.75 | 3 |
- **R:R fixed 1.5** (1 pt = $1 NQ). v2's "38 TP" was JJ rounding 37.5. No break-even, no partials,
  no runners — "lets it play out win or loss" `[fx-test L840–42]`.
- Optimal R:R confirmed ≈1.5 (1.6 marginally better for continuations) `[fx-test L1384–94]`.
- ATR length NOT STATED → assume default 14 `[assume]`.

## 8. Position sizing
- SL distance × {1,2,3} contracts engineered so each ≈ **$1,000 risk/trade** `[fx-pdf][fx-test L304–19]`.
  This is the link into Layer B (per-account $ risk = contracts; point distances fixed).

## 8b. Multi-account orchestration (how the portfolio actually trades) `[v1][v2]`
NOT copy-trading one setup onto all accounts — JJ calls copying all accounts at once "one of the
worst things you can do ever while trading" (variance / correlated lump risk). `[v1 L1690–1697]` The
real mechanic:
- **Each account ~once per day, on a DIFFERENT setup.** "trade each account once per day instead of
  copy trading all of them once… if you have five accounts, you want to trade five different setups." `[v2 L249–254]`
- **Copy-trade only in small clusters (~5 at once), never all 40.** "I have 40 accounts, I'm copy
  trading five at once… maximum exposure to the edge before it dies." `[v2 L273–276]` → ~40 accounts
  worked across several setups/day, ~5 per setup, so any single trade risks only the cluster, not the fleet.
- **Layer same-direction evals into a WINNER ("follow the good trades").** Once a funded account is
  in profit, add evals in the same direction at staggered entries — "unique positions," what one
  trader does as a single scaled position spread across ~5 accounts. Evals only join trades already
  proving good → tilts pass-hungry accounts toward winners. `[v1 L344–348, L389–393]`
- **Layer-B RoR consequence:** block-correlated, not independent and not fully copied — `(P_fail)^N`
  overstates safety (less than a naive all-40 copy). Model cluster/effective-ρ.
- Copy-trading only advised once you KNOW pass rate / payout chance / avg payout AND RoR<5% (≳$10k
  bankroll); else trade one account, bank payouts, then scale. `[v2 L214–239]`

## 9. Filters / optimizations (materially changed results — but IN-SAMPLE)
- **Skip first 3 min after 09:30** (continuations): first-3-min = +2R/28 trades vs +36R all `[fx-test L1554–72]`. PM session: timing didn't matter `[fx-test L654–58]`.
- **Mean reversions: only first 30 min of NY open**; skip 10:00–11:00 `[fx-test L1424–31]`.
- **PM mean reversions: first hour only** (skip 15:00–16:00) `[fx-test L1454–60]`.
- Applying just these time filters: 52%/1.66PF → **62%/2.46PF** (no new rules) `[fx-test L1600–02]` — **in-sample, overfit risk, needs OOS**.
- Optional/untested confluences: **session VWAP** `[fx-test L339–46]`; day-of-week tilt (drop Wed, +risk Fri — low confidence) `[fx-test L1462–64]`.

## 10. Discretionary items an engine must approximate (remaining judgment calls)
1. "Clear swing point" for the break (eye test) → formalize via pivot lookback `L`. `[assume]`
2. Exact decisive-candle fib anchor + equality handling → pin from frames. `[fx-test]`
3. Size gate on/off + `m,L` → sweep (your proposal). `[user]`
4. Skip mean-reversion when TP is far beyond FV → threshold in points/ATR. `[assume]`
5. Extra hand-drawn FV levels at consolidations + live news/tweet reads → **dropped** (not modellable from time+price); FX Replay dropped them too and it "works well enough". `[fx-test L1159–99]`

## 11. What's still unproven (gates for our own build)
- **OOS / walk-forward** never done (FX Replay = hand-picked in-sample windows).
- **Costs** never deducted — the make-or-break for a 1.5R / 25-pt-stop 1-min scalp.
- **Follow-up trades (trigger 3)** never measured.
- **Size gate** (your idea) never tested.
- Our PLAN.md Gate 1 stands, but the bar is now: **reproduce ≥~54% gross then survive costs + OOS.**
