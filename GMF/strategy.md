# GMF Strategy — Quantified Spec

**GMF = "Global Macro Flow"** — a global-macro / intermarket swing methodology: derive a
directional bias from the macro regime, confirm that big money is positioned that way (COT +
volume), then time entries with auction-market-theory (volume-profile) signals. "Follow the flow
of smart money," not technical chart patterns.

Source: YouTube — **"How to SWING Trade like a Pro"** by **Andrea Cimi**
([2MBKUuyCQ_o](https://www.youtube.com/watch?v=2MBKUuyCQ_o), 2026-06-18, 1:44:26). Machine
transcript in [transcripts/](transcripts/how-to-swing-trade-like-a-pro-2MBKUuyCQ_o.txt). See
[links.md](links.md).

**Status:** SPEC ONLY — **UNVALIDATED**. No backtest has been run; no number in this document is
evidence of edge. The system as taught is **discretionary** (macro judgment + manual COT/volume
reading); only one sub-component (the volume-profile entry, §6) is mechanically backtestable.
Creator's trade "calls" (§11) are unverified, after-the-fact TradingView posts. Do not size risk
against this document.

---

## §1 Core thesis

Big institutions cannot fill billion-dollar orders at once, so they split them and feed them into
the market over days/weeks via algorithms. This creates **order-flow autocorrelation** (more buys
beget more buys) → persistent **drifts** = what retail calls trends. Because the orders are slow,
the resulting moves are **long-term and swing-tradeable**, and the best predictor of their
direction is **macroeconomics**, not price patterns.

Therefore: predict where capital is *flowing* (macro), confirm *who* is positioned (COT + volume),
and *time* the entry with auction-market-theory. Price is the consequence; the driver is the cause.

---

## §2 The pipeline (4 steps)

```
STEP 1  MACRO BIAS      Macro data -> Fed reaction function -> intermarket regime -> per-asset bias
STEP 2  MARKET SELECT   Pick the asset(s) whose driver is most cleanly aligned with the regime
STEP 3  PARTICIPATION   Confirm with COT (non-commercials) + volume-profile value-area shift
STEP 4  TIMING          Enter on an auction-market-theory signal (trend-follow OR mean-revert)
```

Every step must agree before a trade is taken: *"the macro driver has to happen first, the money
needs to flow second, then I time the entry."*

---

## §3 Step 1 — Macro regime → directional bias

**Engine = the central-bank reaction function.** A central bank (Fed) has a dual mandate: stable
prices (PCE inflation ≈ 2%) and maximum employment. It moves one joystick — the policy rate —
plus open-market operations (QE/QT, i.e. balance sheet `WALCL`).

| Macro reading | Fed response | Cycle phase |
|---|---|---|
| Inflation rising & > 2%, unemployment low | **HIKE** (restrictive) | Top → contraction |
| Unemployment rising, recession risk | **CUT** (expansive) | Trough → recovery |

**Data watched (the inputs):**
- Inflation: CPI, PCE (the Fed's target), PPI.
- Employment: NFP, unemployment rate, ADP, JOLTS job openings, weekly jobless claims.
- Activity/sentiment: GDP, ISM/PMI, consumer & business sentiment.

**Key timing fact:** markets *anticipate* the economy by ~**6–9 months**, and price moves on the
*expectation* of the next FOMC action, not the action itself. So the trade is on where the data is
*aiming* (toward a hike vs a cut), classified into one of four states `{+ , +/- , -/+ , -}`
(continue stronger / stay / slightly worse / reverse).

**Regime → per-asset bias matrix** (the quantifiable core of Step 1):

| Regime | Yields | USD | Gold | Stocks/Crypto | VIX |
|---|---|---|---|---|---|
| **Expansion / dovish** (low rates, QE, gov spending↑) | low | weak | **up** | **up** | low |
| **Peak → expecting hikes** (inflation↑, hawkish) | up | strong | flat/down | up then down | rising |
| **Recession onset / crash** (risk-off) | spike (price↑) | short-term strong | early weak | **down** | **spikes** |
| **Recovery** (rates still low, QE, post-crash) | low | reverses weak | **pumps** | bottom → up | falling |

---

## §4 Step 2 — Intermarket driver rules

What *causes* each market to move (so the bias above is mechanistic, not vibes):

| Market | Primary driver | Quantified rule |
|---|---|---|
| **Bonds** | safe haven + inflation hedge | Price ↑ (yields ↓) on risk-off / cuts; the "destination" of money fleeing stocks |
| **Forex** | **bond-yield differential** | Long the currency whose CB is *hawkish* vs the *dovish* one (rate/yield spread). Carry trade amplifies (borrow low-yield ccy, buy high-yield). e.g. USDJPY up while BoJ ~0%; AUDCAD up when RBA hawkish & BoC flat |
| **Gold** | **inverse to real yields** | `real yield = nominal yield (US05Y/US10Y) − inflation expectations (T5YIE/breakevens)`. Real yield ↓ → gold ↑; real yield ↑ → gold flat/down. Gold competes with bonds as the inflation hedge |
| **Stocks** | risk appetite + **liquidity** | Up when Fed balance sheet `WALCL` expands (QE), rates low, gov spending up. Structural up-skew → favor longs |
| **VIX** | implied vol / fear | **Mean-reverting** with a hard floor (almost never < 10; practical low ~16). Buy low as cheap downside hedge; reverts up on stress |

---

## §5 Step 3 — Participation (who is positioned, and is volume confirming)

**COT (Commitment of Traders, CFTC, weekly).** Three actor classes:
- **Commercials** — producers/hedgers (take the opposite side).
- **Non-commercials = large speculators = "smart money"** (banks, hedge funds) → **this is the
  group GMF follows.** Read whether non-commercials are net buying/selling and the week-over-week
  *change* for the dollar, gold, the FX pair, etc.
- **Non-reportables** — retail.

**Volume profile / auction market theory.** Build a volume profile; the high-volume node = the
**value area** (fair value). Trend is assessed by the **value area *shifting*** (migrating up =
bullish, down = bearish) — explicitly **not** by higher-highs/higher-lows. A bullish setup wants the
value area shifting up *and* non-commercials buying.

---

## §6 Step 4 — Entry models (auction-market-theory) — the mechanizable kernel

Price alternates between **balance** (consolidation around fair value = the value area, where most
volume transacts) and **price discovery / imbalance** (a directional "auction" seeking liquidity).
Two trend-following models + one range model. All are variations on *trade relative to the value
area*. (Long versions shown; shorts are symmetric.)

**Value area (VA)** = volume-profile band around the POC capturing ~1σ of volume (≈68–70%): `POC`,
`VAH` (value-area high), `VAL` (value-area low).

| Model | Context | Trigger | Entry | Target | Stop |
|---|---|---|---|---|---|
| **M1 — break-in (failed auction)** | bias UP; established VA | price expands **below VAL** (sellers attempt new discovery), then a **Daily or H4 candle closes back inside the VA** = failed/initiative auction rejected | long on that close-back-inside | opposite side of VA (`VAH`) and beyond | beyond the excursion extreme (the failed-auction low) |
| **M2 — breakout retest** | bias UP; price has broken **above VA** and built **new VA above** | **retest of the old VAH** (now support) | long on the retest, expecting drift to continue | higher / new VA / extension | below old VAH / new VAL |
| **MR — range mean-reversion** | rangebound market (typical of FX); one large long-term VA | price expands **beyond the VA** then **reverts back inside** | fade back toward the **other side** of the range | opposite side of the range | beyond the expansion extreme |

This is the primary, repeatable signal. M1 and MR are **mean-reversion-to-value**; M2 is
**trend-continuation**. The creator favors the **failed-auction (M1/MR)** entry.

---

## §7 Per-market application

| Market | Default model | Notes from source |
|---|---|---|
| **Forex** | **MR (range)** | FX mostly stays in CB-defended ranges; use M1/M2 trend models *only* during big monetary-policy regime shifts (~every 5–7 yrs, e.g. COVID) |
| **Gold** | M1/M2 trend-follow when rates low / QE; **MR from highs** when flat/reversing | Bias entirely from real yields |
| **Stocks (SPX/NDX)** | **LONG-ONLY, buy the dip** | Buy when index drops ~2–3% **and VIX spikes to ~20**; breakout (M2) also works but long-only is "statistically better." Short only via puts / VIX, never outright |
| **VIX** | buy low (~16–17 → target ~23); floor ~10 | Substitute for shorting stocks — easier to time the VIX low than the stock-market top |
| **Single stocks** | as index, but pick the **strongest** name (upward skew) | Close **before earnings** (event risk). e.g. demo bought Nvidia at the failed auction below its year-long VA |

---

## §8 Risk / trade construction (as described)

- **Asymmetry first** — sizing/selection driven by R-multiple skew (1:2, 1:4, 1:5 quoted).
- **Options to dodge stop risk** on hard-to-time tops or illiquid pairs: long puts, bull call
  spreads, VIX futures (defined risk, no stop-out needed).
- **FX uses hard stops** above/below the failed-auction extreme; re-enter if the setup re-forms
  after a stop (this re-entry behavior must be modeled — see §11, it inflates apparent win rate).
- **Diversify uncorrelated** — do not stack correlated pairs (e.g. short-CHF via both USDCHF and
  EURCHF = one bet); spread risk across genuinely uncorrelated macro themes.
- **Scale into VA lows** — "gradually entered bit by bit on the low of the value area."

---

## §9 Parameters

| # | Parameter | Step | Default / value | Status |
|---|---|---|---|---|
| P1 | Macro regime classification | 1 | 4-state `{+,+/-,-/+,-}` from data | **FREE** — judgment; no rule given |
| P2 | Data set & thresholds (CPI/PCE/NFP/…) | 1 | listed in §3 | **FREE** — no trigger levels |
| P3 | Anticipation lead | 1 | ~6–9 months | **FREE** — loose |
| P4 | Gold real-yield inputs | 2 | `US05Y − T5YIE` | semi-FIXED (series named); threshold FREE |
| P5 | FX yield-differential rule | 2 | hawkish-vs-dovish CB | semi-FIXED; threshold FREE |
| P6 | Liquidity gauge (stocks) | 2 | Fed `WALCL` direction | semi-FIXED |
| P7 | COT actor | 3 | **non-commercials** | FIXED |
| P8 | COT net/Δ threshold & lookback | 3 | "are they buying/selling" | **FREE** — no level/window |
| P9 | Volume-profile window | 3/4 | daily / session / range | **FREE** — must define |
| P10 | Value area width | 4 | POC ± ~1σ (~68–70%) | FIXED (standard VA) once P9 set |
| P11 | "Failed auction" definition | 4 | expand beyond VA, close back inside | **FREE** — excursion size, # bars |
| P12 | Entry trigger TF | 4 | Daily or H4 close | semi-FIXED (pick one) |
| P13 | Entry model selection | 4 | M1 / M2 / MR per regime | **FREE** — regime-dependent, discretionary |
| P14 | Value-area-shift detector | 3 | VA migrates up/down | **FREE** — how much = a shift |
| P15 | Stop placement | 8 | beyond excursion extreme | semi-FIXED |
| P16 | Target | 8 | VAH / opposite VA / extension | **FREE** — pick one |
| P17 | Stock dip / VIX trigger | 7 | drop ~2–3%, VIX ~20 | **FREE** — examples, not rules |
| P18 | VIX buy / target levels | 7 | buy ~16–17, target ~23, floor ~10 | **FREE** — examples |
| P19 | Re-entry after stop | 8 | yes (FX) | **FREE** — must bound (else inflates win rate) |

---

## §10 Testability gaps & the mechanizable kernel

**As a whole system, GMF is not backtestable** — Steps 1–3 require macro judgment, manual COT
reading, and discretionary model selection (P1, P8, P13). Those are exactly the degrees of freedom
that let any winning chart be drawn in hindsight.

**The one mechanically testable kernel is the §6 entry** — a **volume-profile mean-reversion system
(M1 / MR)**, which happens to be in the family the repo's survival study *favors*. Proposed
deterministic build:

| Gap | Algorithmic proxy |
|---|---|
| Volume profile (P9) | Rolling session/`N`-day profile; compute `POC, VAH, VAL` at the ~70% band |
| Failed auction (P11) | Bar `low < VAL − k·tick` (or `< VAL`) then a Daily/H4 close back `> VAL` within `m` bars → long signal |
| Target (P16) | `POC` (conservative) or `VAH` (range) — pick one per run |
| Stop (P15) | Beyond the excursion extreme (failed-auction low); fallback `j·ATR` |
| Macro/COT gate (P1/P8) | Treat as **optional filters**: test (a) entry alone, (b) entry + COT-direction filter, (c) entry + regime filter — measure whether the gate adds OOS Sharpe or just cuts trades |
| Re-entry (P19) | Cap at `≤ N` re-entries per signal; count each scratch as a trade (no hiding losses) |

Backtest the kernel first; only layer the macro/COT gate if it *measurably* improves blind OOS
results.

---

## §11 Validation status & claim check

Per [docs/strategy-validation.md](../docs/strategy-validation.md) — the standing rule of this repo:

- **The "calls" are unverified, after-the-fact anecdotes.** Gold +86% (bought Sep-2023), GBPUSD
  −26% (2021 short), and the "1 to 5" oil/AUDCAD/EURCHF/Nvidia/VIX trades are screenshots of
  TradingView ideas / community posts shown *after* the outcome — textbook survivorship & hindsight
  selection. The creator himself admits losers ("this one went to stop-loss", FX "stop-loss was
  triggered first… I re-entered"), so this is **not** a clean log; no losing series, no equity
  curve, no sample size.
- **Sound reasoning ≠ edge.** The macro/intermarket teaching is genuinely correct textbook material
  (Fed reaction function, yield curve → recession, real yields → gold, carry trade → FX). But
  *being right about the economy* does not imply a *tradeable, cost-surviving edge* — the 6–9-month
  lead is loose, and regime calls are discretionary (P1).
- **Win-rate-inflation risk.** "Buy the dip / scale in / re-enter after a stop" + options-to-avoid-
  stops can manufacture a high hit rate while carrying negative skew. High win rate ≠ positive
  expectancy.
- **The Tesla trap.** Stocks (and gold) trended *up* across the demo window. Long-only-stock and
  long-gold results must be checked against **buy-and-hold** — otherwise it is exposure, not edge.
- **Priors (survival study):** the §6 volume-profile mean-reversion kernel is in the **favored**
  family; the discretionary macro overlay is **unfalsifiable as stated**. Realistic surviving edge
  ≈ OOS Sharpe 0.5–1.5, not the "mathematical" certainty implied.

**To move SPEC → evidence:**
1. Pin every **FREE** parameter in §9/§10 to deterministic proxies; backtest the **kernel** alone.
2. **Walk-forward** (optimize ~70%, blind ~30%, stitch OOS), **net of spread/commission/slippage**.
3. Clear the **auto-reject gate**: OOS DD > −35% → reject; OOS Sharpe < 0.5 or > 2.5 → reject; OOS
   beats in-sample by > 30% → reject; < 30 trades → not significant; any single trade > ~25–30% of
   net P&L → reject.
4. **Buy-and-hold sanity** on every long-biased market (stocks, gold).
5. Only then test whether the macro/COT gate *adds* OOS Sharpe.

Until then: **provisional / unvalidated / spec only.**

---

## §12 Audit trail (when backtested)

Any run that produces a reported number must leave an audit folder
(`GMF/reports/<run>-<utcstamp>/`): raw signals/trades, aggregated metrics, `config.json`, the
driver script, `run.log`, `manifest.sha256`. No metric may be stated unless it traces to a file in
that folder (enforced by the `audit-trail` skill).
