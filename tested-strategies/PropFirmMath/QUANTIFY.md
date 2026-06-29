# PropFirmMath — Quantification

Sources: (v1) JJ Simon interview, Titans of Tomorrow → [`EXTRACTION.md`](EXTRACTION.md).
(v2) JJ's OWN explainer "$1.2M in 12 months" → [`EXTRACTION_v2.md`](EXTRACTION_v2.md) —
**authoritative, supersedes v1 paraphrase on conflict.** This doc converts the method into
**codeable rules + EV math**. Params tagged `[STATED]` / `[ASSUMED]` / `[v2]` (filled or
corrected by video 2).

---

## v2 RECONCILIATION (read first — corrections + gap fills)
Video 2 is JJ's own step-by-step + a real week of trades. It moves the signal from ~50% to
**~80% codable** and fixes v1 errors:

**Corrections (v2 wins):**
- Fair price = **9:30 ET open CANDLE**, not 9:29 tick. On news, fair price = candle *before* release.
- **11:00 ET = stop-trading cutoff, NOT a session.** The v1 "11:00–14:00 longer hold" does **not exist** (v1 misread) — drop entirely.
- Headline = **$1.2M / 12mo** (his own), not $1.5M/<18mo.
- **Live edge stated as "1–5%", breaks even on live** → confirms Layer A edge is thin and cost-sensitive (the crux).

**Gaps FILLED by v2:**
- **BoS now defined** — two close-confirmed entry triggers (see A4). Load-bearing gap largely resolved.
- **Direction** — two biases must agree: medium-TF reversion toward 9:30 open + low-TF momentum; first trade = open-candle COLOR (red→short, green→long), first 10 min.
- **Exact exits** — R:R **1:1.5, SL 25 pt / TP 38 pt**; sizing = **contract count, points held constant** (resolves how per-firm $ risk varies).
- **Win rate** — first number ever: **A+ ≈ 70–80%**; narrated week ≈ 12W/4L. A/B grades still unmeasured.
- **Session clock corrected** (A6); adds 3:00 ET London.
- **His own backtest-wrapper recipe** — 1 trade/day sim; EOD trailing DD ratchets up on wins, locks at start balance; output = pass rate → `avg_cost_to_funded = eval/pass`.

**Still-open coding blockers (only 2 left):** (1) swing/structure detection threshold (no
bar-count/fractal given); (2) displacement-candle size cutoff (qualitative "bigger + no wicks").
Plus minor: min "points-in-favor" to take a reversion, fair-price-zone width, A/B win rates.

---

## 0. The core reframe — this is TWO bets, not one

The video sells one "loophole" but it is mechanically two separable layers. Keeping them
separate is the whole point of an honest quantification.

> **Current mechanical ruleset → [`STRATEGY_RULES.md`](STRATEGY_RULES.md)** (consolidates v1/v2/v3
> FX Replay; the triggers below are now fully mechanized there). This doc keeps the analysis + EV math.

| Layer | Question | Codeable? | Proven? |
|-------|----------|-----------|------------------|
| **A. Signal** | Does fading NQ 1-min back to the 9:30 open-candle "fair price" have positive expectancy after costs? | Yes | **FX Replay measured 54% WR / +0.35R gross, in-sample** (158 trades) → positive GROSS; **costs + OOS untested** |
| **B. Wrapper** | Given a per-trade edge E, do prop-firm rules + portfolio sizing convert it into the claimed return? | Yes (almost as-is) | Internally consistent |

**The "genius/loophole" is Layer B** — cheap eval = a call option on a $2k–5k payout,
bought in bulk, sized by Kelly, with `(P_fail)^N` risk of ruin. Layer B is real math.
**But Layer B is worthless if Layer A's edge ≤ 0.** After commissions + spread on 20–40
NQ trades/day, Layer A must clear a real hurdle. **That hurdle is THE thing to test.**

> Headline falsifier: if the signal's after-cost per-trade expectancy is ≤ 0, the entire
> $1.5M story is survivorship + selling courses, and no wrapper math saves it.

---

## LAYER A — Per-trade signal engine

### A1. Instrument & data
- **Market:** Nasdaq-100 futures. `[STATED]` Backtest on **MNQ** (micro) or **NQ** continuous. `[ASSUMED: MNQ for cost realism]`
- **Bars:** 1-minute. `[STATED]`
- **Hours:** RTH + extended, ~08:00–20:00 ET (sessions below). `[STATED]`
- **Costs (must model):** commission + spread per round trip. `[ASSUMED: MNQ ≈ $0.50/tick, ~$1.20 commission RT, 1-tick spread]` — he picked Nasdaq *specifically* for best commission+spread, so costs are first-class, not a footnote.

### A2. Direction / bias rule `[v2 corrected]`
- **Fair price** `P_fair` = the **09:30 ET session-open candle** (open-candle level). `[v2]` On news, `P_fair` = candle *before* the release. Early post-open moves = "opening flow / liquidity imbalances / hedging", not true repricing → fade them.
- **Two biases must AGREE** `[v2]`: (a) medium-TF **reversion** toward `P_fair` (price above open→short, below→long); (b) low-TF **continuation** = direction of recent momentum. Aligned = A+.
- **First trade of a session = open-candle COLOR** (red open→short, green→long), first 10 min only.
- `[ASSUMED]` Fair-price-zone width (how close to `P_fair` to stop fading) — JJ skips entries "inside the zone" but never sizes it. Sweep.

### A3. Two trade types per session

**(1) Continuation** — at session open / news spike, trade *with* the opening move (first trade only).
- Trigger: first 1-min candle of the session (or the news candle) closes directional → enter its direction. `[STATED, no confirmation rule given]`
- `[ASSUMED]` Enter at close of bar 1; this is the only "with-trend" trade of the block.

**(2) Mean reversion** — the bread-and-butter, ~3–4 per block, fading back to `P_fair`.
- Trigger: after the continuation extends and **volume dies → consolidation**, price makes a **1-min break of structure (BoS) back toward `P_fair`**, confirmed on close. `[STATED]`
- Confirmation (the one concrete rule): **"closes below the structure it broke"** (mirror for longs). `[STATED]`
- Gate: reversion entries only **before 11:00 ET** for the morning block. `[STATED]`

### A4. Entry trigger — DEFINED by v2 (was the load-bearing gap)
Two co-equal triggers, **both confirmed on candle CLOSE** `[v2]`:
1. **Break of structure + close** — candle closes beyond a prior swing level ("closes below the structure it broke"; mirror for longs). Use when a structure level exists.
2. **Displacement candle** — "a candle larger than the previous one with (almost) no wicks", closing *clearly* past the prior candle. Use when no clean structure level.
- **Setup grading** `[v2]`: **A+** = both biases aligned + BoS-close; **A** = displacement only; **B/B+** = biases opposed → skip. He takes nearly every A/A+.
- **Remaining free params (sweep)** `[ASSUMED]`: swing detection = pivot H/L over `L` bars (`L∈{3,5,8}`); displacement size cutoff = body ≥ `m`× prior body AND wick ≤ `w`% of range (`m,w` swept). These two thresholds are the **only undefined edges left** — JJ states them qualitatively.

### A5. Exits — fully static (no price-based exits) `[v2 exact]`
- **SL = 25 pt, TP = 38 pt → R:R 1:1.5**, applied on every example trade. `[v2]`
- **Sizing = contract count; points held CONSTANT.** `[v2]` Per-firm $ risk varies only via contracts (Layer B), the point distances never move. (Resolves v1's "static $1000/$500".)
- **No break-even / no partials / no runners** on eval. `[STATED]`
- **Funded variant:** may extend TP past 38 / let it run past 1:1 to capture the full reversion; pick account by **points-available that day** (50 pt some days, 20 others). `[v2]`
- **Re-entry rule** `[v2]`: after a stop-out caused by an unfair displacement, re-enter immediately (the reversion thesis is unchanged).
- Avoid holding into **9:45 / 10:00 ET** news. `[v2]`

### A6. Session schedule (ET) — the clock that fires trades `[v2 corrected]`
| Time | Action | Trades |
|------|--------|--------|
| 03:00 | London open `[v2 new]` | 1 continuation + reversions |
| 08:30 | News (red-folder) | 1 continuation + ≤3–4 reversion |
| 09:30 | **NY a.m. open — set `P_fair`** (primary) | 1 continuation (0–10 min) + ≤3–4 reversion (10–90 min) |
| 11:00 | **STOP-TRADING CUTOFF** (not a session) | — |
| 14:00 | NY p.m. open | 1 continuation + ≤3–4 reversion |
| 18:00 | Reopen | 1 continuation + ≤3–4 reversion |
| 20:00 | Asian | 1 continuation + reversions |
- Continuation window = **first 0–10 min**; reversions fire **10–90 min**. `[v2]` 11:00–14:00 "longer hold" from v1 **does not exist** — dropped.
- ~20 trades/day typical, "30+" headline. `[STATED]` Rationale: 20 trades ≈ 1/day for a month → 20× edge. `[STATED]`
- Dead-volume fallback: drop to **5-min chart**, fewer trades. `[v2]`

### A7. What Layer A MEASURES (outputs, not inputs)
The backtest must **discover** these — measure, don't assume:
- Per-trade **win rate** by **grade (A+/A/B)** and setup (continuation vs reversion). v2 gives only **A+ ≈ 70–80%** `[v2]`; A/B unmeasured.
- After-cost **per-trade expectancy** (R) at the fixed **1:1.5**.
- **Daily P&L distribution** (claims ~98% winning days; narrated week ≈ 12W/4L). `[v2]`
- Max adverse excursion vs the static **25 pt** SL.

**Break-even win-rate anchor — strategy is fixed at R:R 1:1.5:**
| R:R | Break-even WR (pre-cost) |
|---|---|
| **1:1.5 (the strategy)** | **40.0%** |
| 1:1 / 1:2 / 1:4 (funded variants) | 50.0% / 33.3% / 20.0% |
Costs push the hurdle **up**. The empirical question: does the 9:30-fade clear **40% WR
after costs** on NQ at 20 trades/day? If A+ really runs 70–80% but A/B drag the blend below
40%, the answer is grade-selection — so **measure WR per grade**, and test trading A+ only.

---

## LAYER B — Prop-firm EV / portfolio wrapper

This layer is codeable almost verbatim. It consumes Layer A's trade distribution and the
firm's rule set; it outputs pass rate, payout probability, EV, and risk of ruin.

### B1. Firm rule model (parameterize per firm)
- `target` — profit target to pass eval (e.g. $3000 on a tier). `[STATED example]`
- `max_loss` / **trailing drawdown** — the binding constraint; on futures it **trails up and locks at end of day**. `[STATED]` Must model intraday-trailing vs EOD-lock exactly — the whole static-risk + matched-R:R design exists to exploit this.
- `daily_loss_limit` — `[ASSUMED — firm-specific]`
- `consistency_rule` — no single day > X% of total profit; the reason runners/large-R:R are banned. `[STATED, X unspecified → ASSUMED]`
- `min_trading_days` — `[ASSUMED]`
- `eval_cost`, `account_size`, `payout_split`, `payout_cadence`. `[STATED examples: $50–$215 eval, 50k/100k/150k, 90–95% split]`

### B2. Eval simulation → `p_pass`, `time_to_pass`
Monte-Carlo: draw trade sequences from Layer A's empirical distribution; apply firm rules
bar-by-bar; account **passes** if `equity` hits `target` before tripping trailing-DD /
daily-loss / consistency.
- Objective he optimizes here: **P(hit target before max loss).** `[STATED]`
- Matched R:R claim to validate: setting R:R = target/max_loss ratio (1:1.5 for 3k/2k) **raises `p_pass`** given how trailing DD moves. `[STATED — test it]`
- Self-reported `p_pass ≈ 25–33%`. `[STATED]` Treat as an **output to reproduce**, not an input.

### B3. Funded simulation → `p_payout`, `payout_size`
- Objective shifts to **EV = P(payout) × payout_size.** `[STATED]`
- Payout cycle: grow funded balance to **$10k**, withdraw **$5k** (half / the max), repeat. `[STATED]` Small-scale variant: to $4k, take $2k.
- `p_payout` = P(reach $10k balance before blowing the funded account). `[STATED as separate from p_pass]`
- `payout_size` cap **$5k**; biggest-ever $45k, all others ≤ $5k. `[STATED]`
- Funded R:R **varied** to match what the market offers per account. `[STATED]`

### B4. Portfolio EV + risk of ruin (the "loophole" math)
Per-eval economics (his own numbers, formalized):
```
avg_cost_to_funded = eval_cost / p_pass
P(eval → payout)    = p_pass × p_payout
EV_per_eval         = p_pass × p_payout × payout_size  +  E[residual balance]  −  eval_cost
return_multiple     = (p_payout × payout_size) / avg_cost_to_funded
```
His worked instances (to reproduce):
- `0.33 × 0.33 ≈ 1/9`; payout $2000; eval $100 → spend $900 / withdraw $2000 ≈ **2x**, plus $2000 residual. `[STATED]`
- `avg_cost_to_funded $333`, EV payout $1000 → **3x**. `[STATED]` Target 3x spend (good runs 4–6x, bad ~2.7x).

Risk of ruin — **JJ's formula, which assumes `N` independent evals** (real accounts are
block-correlated → this understates RoR; see §2.4 and [`STRATEGY_RULES.md`](STRATEGY_RULES.md) §8b):
```
P(zero payouts) = (1 − p_pass·p_payout)^N
```
- `0.9^50 ≈ 0.005` → <1% RoR on 50 accounts. `[STATED, reproduces]` (independence-optimistic)
- Target RoR **≤5% starting, ~0.5% now.** `[STATED]`

Bankroll sizing:
- **Kelly** (or ¼–½ Kelly while building) sets how many evals a bankroll affords. `[STATED]`
- Heuristic: total exposure ≈ **5% of net worth** (×10 → 0.5% RoR). `[STATED]`
- Portfolio > concentration: many small accounts beats few large (5×150k ≈ $5k/mo vs the goal). `[STATED]`

### B5. Scale ladder (validation checkpoints)
`$5k → $17k` on 50 × 50k accounts (~3.3x, ~1mo, 2 firms) → `$10k → 34k tier, 4 firms` →
now **10 firms × 150k, 5 funded each, ~40 accounts.** `[STATED]`
$100k/mo math: 150k/5k = **30 payouts/mo** (~1/day) → **30×150k = $4.5M** allocation. `[STATED — reproduce]`

---

## 1. Quantified parameter table (single source of truth for the build)

| Param | Value | Tag |
|---|---|---|
| Instrument | MNQ/NQ 1-min (5-min dead-vol fallback) | STATED / ASSUMED(MNQ) |
| Fair price | **09:30 ET open candle**; on news = pre-release candle | v2 |
| Bias | two must agree: reversion→open + low-TF momentum | v2 |
| First trade | open-candle COLOR, first 0–10 min | v2 |
| Entry trigger | **BoS+close OR displacement candle** (both close-confirmed) | v2 |
| Setup grade | A+ (aligned+BoS) / A (displacement) / skip B | v2 |
| BoS free params | pivot `L∈{3,5,8}`; displacement body≥`m`×prev, wick≤`w`% | **ASSUMED — sweep (only 2 left)** |
| Reversion window | 10–90 min; **hard stop 11:00 ET** | v2 |
| SL / TP | **25 pt / 38 pt → 1:1.5** (points fixed) | v2 |
| Sizing | **contract count** (per-firm $; points never move) | v2 |
| Funded variant | extend TP past 1:1; pick acct by points-available | v2 |
| Re-entry | immediate after unfair-displacement stop-out | v2 |
| BE / partials | none on eval; avoid holding into 9:45/10:00 news | v2 |
| Trades/day | ~20 (30+ headline) | STATED |
| Sessions ET | 03:00, 08:30, 09:30, 14:00, 18:00, 20:00 | v2 |
| Per-trade WR | A+ ≈70–80%; A/B **measure** | v2 / OUTPUT |
| p_pass | ~33% — reproduce | OUTPUT |
| p_payout | ~33% — reproduce | OUTPUT |
| Payout cycle | →$10k bal, take $5k | STATED |
| RoR formula | (1 − p_pass·p_payout)^N | STATED |
| Target return | 3x eval spend | STATED |

---

## 2. Falsification criteria (what kills this)
1. **Layer A after-cost expectancy ≤ 0** → whole thesis dead, regardless of wrapper. *Primary test.*
2. Reproduced `p_pass` ≪ 25% under realistic firm rules → eval economics negative.
3. Matched-R:R claim false (1:1.5 does **not** beat other R:R on pass rate) → core "loophole" mechanic is folklore.
4. `(P_fail)^N` assumes **independent** accounts. JJ avoids the catastrophic case (one setup copied onto all ~40) but DOES copy-trade in **~5-account clusters** across several setups/day, layering same-direction evals into winners → outcomes are **block-correlated** (within-cluster ≈ correlated; across-cluster positive via same strategy/instrument/day), not independent → real RoR > stated (less than a naive all-40 copy, but independence still flatters it). Model block/effective-ρ. **Likely the biggest hidden flaw.**
5. Costs alone (20–40 trades/day × spread+commission) exceed the thin reversion edge.

## 3. Honest read (post-v2)
- **Layer B is genuine, codeable, correct math** — bulk cheap optionality + Kelly + variance shaping. The real insight.
- **Layer B's independence assumption is its weak point**: JJ does NOT copy one setup onto all ~40 accounts (the catastrophic case he rejects); he copy-trades in **~5-account clusters**, spreads different setups across the day, and layers same-direction evals into already-winning trades. So accounts are **block-correlated, not independent** — `(P_fail)^N` still flatters RoR, just less than a full copy. Model cluster/effective-ρ (Phase 3.3).
- **Layer A is now fully mechanical** (v3/FX Replay defined the triggers — see [`STRATEGY_RULES.md`](STRATEGY_RULES.md)) and has its **first measured win rate: 54% aggregate over 158 trades at 1.5R → +0.35R gross expectancy, in-sample** (FX Replay manual backtest, verified). This clears the 40% break-even hurdle **gross**.
- **But "gross in-sample" ≠ works.** No OOS/walk-forward, **no costs deducted** (the killer for a 1.5R/25-pt-stop 1-min NQ scalp), dataset is hand-picked regime windows, and the optimized 62%/2.46PF is in-sample time-of-day fitting. JJ separately says live edge is only "1–5%" / breaks even live `[v2]`.
- The make-or-break is unchanged, just sharper: **does the ≥54% gross survive realistic costs and hold OOS?** That is PLAN.md Gate 1.
