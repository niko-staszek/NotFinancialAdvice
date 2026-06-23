# Strategy Validation — Rules & Findings

**Audience: future Claude (and the human) working in this repo.** This is the
standing rulebook for *building, backtesting, and judging any strategy here* —
PAC, MRD, API, MMD, CBS, MF, IVB, ETR, hedgehog, and anything new.

It exists because most trading strategies are curve-fits that look real and get
trusted. The default stance is **skeptical**, and the burden of proof is always
**out-of-sample**.

Distilled from two sources:
1. A 131,441-run meta-study on what survives rigorous testing — see
   [research/backtest-survival-study.md](../research/backtest-survival-study.md).
2. This repo's own results (IVB, ETR) — see [Findings log](#findings-log).

---

## 0. The one rule

> **No strategy is "working" until it holds up on data the optimizer never saw.**

In-sample profit factor, in-sample equity curves, and "looks good on the chart"
prove nothing. If a claim of edge is not backed by an out-of-sample (OOS)
number, treat it as unverified and say so.

---

## 1. The validation method (mandatory)

**Walk-forward, not single-shot backtest:**

1. Split history into sequential windows.
2. Optimize parameters on the **first ~70%** of each window.
3. Run **blind** on the remaining **~30%** (optimizer never saw it).
4. Slide window forward, repeat.
5. Stitch all OOS segments into one combined result. **Report that.**

A plain backtest over all history with tuned parameters is **not evidence** and
must not be presented as such.

---

## 2. The acceptance gate (auto-reject filters)

Apply after walk-forward. Any failure = reject (or flag loudly), don't quietly
keep it. Thresholds below are the daily-bar study's; see §5 for intraday
adaptation.

| # | Gate | Threshold | Rationale |
|---|------|-----------|-----------|
| 1 | OOS max drawdown | better than **−35%** | Nobody holds through −70% live. |
| 2 | OOS Sharpe (floor) | **> 0.5** | Below ≈ noise. |
| 3 | OOS Sharpe (ceiling) | **< 2.5** | Above (on daily bars) = the *asset* did the work, not the strategy. |
| 4 | OOS vs in-sample Sharpe | OOS ≤ IS **+30%** | Doing much better on unseen data = luck/variance. |
| 5 | Trade count | **≥ 30** | Fewer → statistics meaningless. |
| 6 | In-sample Sharpe | **> 0** | Sanity. |

Two more this repo learned the hard way (see Findings log):

| 7 | **Profit concentration** | No single trade > ~25–30% of net P&L | One lucky trade ≠ edge (ETR: 1 trade = 90% of net). |
| 8 | **Net of costs** | Sharpe/PF computed *after* spread + commission + slippage | Pre-cost survivors thin out fast, especially intraday. |

---

## 3. Red flags — reject or investigate before trusting

- **The Tesla trap / asset drift.** A long-biased system on a strongly trending
  asset (TSLA +14,000%, XAUUSD's run, BTC) looks like genius — it is exposure,
  not edge. Filters 3 & 4 exist to catch this. Always ask: *would a dumb
  buy-and-hold have done as well?*
- **Profit concentration.** Net P&L carried by 1–2 trades. (ETR.)
- **Catastrophic drawdown.** −70%/−99% DD means it doesn't work in practice
  regardless of end return. (IVB.)
- **Over-optimization.** Many parameters, finely tuned. The more knobs, the more
  room to fit noise. Prefer fewer parameters.
- **In-sample-only metrics.** PF/return/Sharpe quoted without an OOS counterpart.
- **Survivorship bias.** "This strategy from a video/forum works" — it's
  published *because* it had one good run; the failures aren't published.

---

## 4. Where edge actually tends to live (priors, not guarantees)

From the meta-study's survival rates:

- **Mean reversion** and **volume** strategies survived most (~38%).
- **Trend-following MA crossovers** and **candlestick patterns** survived least
  (~18–22%) — despite being the most popular.
- **Simple beats complex.** Fewer parameters → less overfitting.
- A survivor has a **logical market-microstructure reason** to work, not just
  past evidence that it did.
- **Realistic verified edge on daily bars = OOS Sharpe 0.5–1.5.** Anything
  pitching Sharpe 3 / 200% annual is an overfit backtest. Modest is normal.

Use these to prioritise *what to test*, not as a substitute for testing.

---

## 5. Adapting to this repo's universe

The meta-study was **daily bars on US equities / sector ETFs / crypto**. This
repo trades **intraday FX / gold / indices (M5–H4)**. So:

- **Method transfers as-is** (walk-forward + gate). Bake §2 into every backtest
  harness as automatic rejects rather than eyeballing.
- **Survivor *list* is a prior, not a transplant.** Mean-reversion dominance on
  XLU/ETH daily does not imply the same edge on XAUUSD M5 — re-verify locally.
- **Costs dominate intraday.** Spread + slippage + commission must be modelled;
  an M5 strategy with positive gross and negative net is a reject, not a "close."
- **Drawdown threshold may need to be tighter** for leveraged FX than −35%.
- **Sample size is easier intraday** (more bars) — no excuse for < 30 trades, and
  prefer hundreds for significance.

---

## 6. Pre-claim checklist

Before stating that any strategy "works," "has edge," or reporting its numbers,
confirm every box (per the repo's audit-trail discipline — results must trace to
a file inspected this session):

- [ ] Walk-forward (70/30 sliding) run; combined OOS result reported.
- [ ] OOS max DD better than threshold (−35% daily; tighter for leveraged FX).
- [ ] OOS Sharpe in [0.5, 2.5].
- [ ] OOS Sharpe does not exceed in-sample by > 30%.
- [ ] ≥ 30 trades (prefer ≫ for intraday).
- [ ] No single trade > ~25–30% of net P&L.
- [ ] Metrics are **net of** spread/commission/slippage.
- [ ] Sanity: would buy-and-hold of the asset have matched it? If yes → not edge.
- [ ] Numbers trace to a saved result file, not memory or a tuned single run.

If any box is unchecked, report the result as **provisional / in-sample only**
and say which checks are missing. Do not round up "promising" to "works."

---

## Findings log

Concrete evidence from this repo — extend as runs complete.

| Date | Strategy | Finding | Rule it illustrates |
|------|----------|---------|---------------------|
| 2026-06-19 | **IVB** (Initial-Balance Breakout, XAUUSD 2024 in-sample) | No edge: PF 0.79–0.88, DD 74–99%. Sizing bug fixed; still no edge. | Gate #1 (catastrophic DD), §3 catastrophic drawdown. |
| 2026-06-19 | **ETR** (EMA Trend Rider, XAUUSD) | +34%, PF 1.36 — but **1 trade = ~90% of net**. | Gate #7 (profit concentration), §3 Tesla-trap-adjacent. |
| 2026-05-19 | **Meta-study** (Algovibes, 131,441 runs) | 65/131,441 survived. Mean reversion dominates; trend/pattern worst. | §1 method, §2 gate, §4 priors. |
| 2026-06-22 | **ORB** (bias-gated breakout, US indices) | **No generalizable edge.** US100 default (S0/E0/RVOL1.0, continuous OOS 2022-10→2026-04) passes (PF 1.14, Sharpe(t) +1.04; runner E3 +2.14) — BUT same config FAILS on US500 (−1.06/−0.04) and US30 (−1.30/+0.42). Positive on the one most-volatile index only → Nasdaq trend/vol exposure, not robust edge. (Initial −0.20 "reject" was a separate harness bug: per-window RVOL-warmup restart dropped ~30% of each OOS window — a real WF pitfall now logged.) | §3 Tesla-trap / instrument cherry-pick (cf. ETR gold/BTC-only); §4 breakout family weakest; **new pitfall: WF per-window warmup fragmentation.** |
| 2026-06-22 | **SweepHunter** (ICT Asia/London sweep → NY M1 FVG reversal, FTMO) | **No edge.** WF OOS (12/3mo, 2023–2026, net of costs) FAILs 3/3 primary instruments: XAUUSD Sharpe −1.94 / DD −86.6% / PF 0.78; EURUSD +net but **57% in one trade** & IS≈0; US100.cash −0.19 / DD −42% / 228% concentration. **Negative IS Sharpe on all three** → no signal to even overfit. Lost on XAUUSD & US100 while both rallied (worse than buy-and-hold). Draw-on-liquidity targets won most windows yet still lose → the *entry* has no edge. | §2 gate (#1 DD, #2 Sharpe, #7 concentration), §3 worse-than-B&H, §4 sweep/pattern family weakest. **New: negative IS Sharpe = reject before OOS — nothing to generalize.** |

---

*Keep this doc current.* When a backtest teaches a new rule, add it to the
Findings log and (if general) to the gate or red-flags section.
