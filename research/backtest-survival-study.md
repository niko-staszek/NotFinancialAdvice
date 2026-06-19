# Backtest Survival Study — What Survives Rigorous Testing

> Knowhow extracted from a video. **Not a tradeable strategy** — it is a
> methodology + empirical map of which *strategy families* actually hold up
> out-of-sample. Treat it as a backtesting-rigor playbook and a prior on where
> edge tends to live.

**Source:** "I Tested 100,000 Trading Strategies." — Algovibes (YouTube)
`https://www.youtube.com/watch?v=XFocx6K4Ers` · uploaded 2026-05-19 · 16:14
Full transcript saved alongside: [`backtest-survival-study.transcript.txt`](backtest-survival-study.transcript.txt)

---

## TL;DR

- **131,441** individual backtest runs · **62** strategies · **31** assets · up
  to **100 Bayesian-optimized** parameter combos per strategy per asset.
- Funnel: **917** promising in-sample → **358** survived walk-forward → **65**
  survived all six filters. **65 / 131,441 ≈ 0.05%.**
- **Mean reversion dominates** the verified set. Trend-following and
  candlestick-pattern strategies had the **lowest** survival rates.
- Real verified edge on **daily bars** produces **OOS Sharpe ≈ 0.5–1.5**.
  Anything claiming Sharpe 3 / 200% annual is an overfit backtest.
- Universe was **daily bars on US equities / sector ETFs / crypto** — NOT the
  intraday FX/metals universe this repo trades. The *method* transfers; the
  *specific survivors* are a prior, not a transplant. See [Transfer to this repo](#transfer-to-this-repo).

---

## The two killers (why ~99.95% failed)

**1. Overfitting.** Take RSI, standard settings, it doesn't quite work. So you
nudge — 28 periods instead of 14, oversold at 35 instead of 30 — until the
backtest looks good. You did not discover working parameters; you searched
combinations until something fit the past. That is finding noise that *looks*
like signal. "A mathematical accident wearing a costume."

**2. Survivorship bias.** Every strategy written about online exists because it
worked at least once. Nobody publishes the thousands that quietly failed. So the
entire retail information environment is pre-filtered to historical winners. Most
retail traders run optimized curve-fits on dead data drawn from a biased sample,
and call it a system.

---

## The test: walk-forward validation

This is the part that separates a meaningful backtest from a worthless one.

1. Split history into sequential windows.
2. Optimize on the **first 70%** of each window.
3. Run the strategy **completely blind** on the remaining **30%** — data the
   optimizer never saw.
4. Slide the window forward, repeat.
5. Stitch all out-of-sample (OOS) periods into one combined result.

**The combined OOS result is the only number that matters.** Genuine edge holds
on unseen data; a curve-fit collapses immediately — and most do.

> Funnel checkpoint: 917 looked promising in-sample → only **358** survived
> walk-forward.

---

## The six filters (applied after walk-forward)

Exact thresholds — reuse these as a rejection gate on any backtest:

| # | Filter | Threshold | Why |
|---|--------|-----------|-----|
| 1 | OOS max drawdown | better than **−35%** | Nobody actually holds through −70%. If a strategy needs that, it doesn't work in practice. |
| 2 | OOS Sharpe | **> 0.5** | Below 0.5 is statistically indistinguishable from noise. |
| 3 | OOS Sharpe | **< 2.5** | Above 2.5 on daily bars almost always means the *asset* did the work, not the strategy. |
| 4 | OOS vs in-sample Sharpe | OOS may not beat IS by **> 30%** | Doing much *better* on unseen data is luck/variance, not skill. |
| 5 | Trade count | **≥ 30** | Fewer and the statistics mean nothing. |
| 6 | In-sample Sharpe | **> 0** | Basic sanity. |

> 358 passed walk-forward → **65** remained after all six.

Distribution context: 57% of all results had positive OOS Sharpe; only 26%
cleared the 0.5 threshold; only 65 cleared everything.

**The Tesla trap (filter rationale):** a strategy showing 1,400% on Tesla isn't
edge — TSLA rose ~14,000%, so any long-biased system looks like a genius. That is
exposure to a rocket, not skill. Filters 3 and 4 exist to kill this.

---

## What survived — category breakdown

Verification rate by category (share of that category's strategies that survived):

| Category | Survival rate |
|----------|--------------|
| Volume strategies | **38.7%** |
| Mean reversion | **38.5%** |
| Momentum | 27.4% |
| Pattern recognition | 22.0% |
| Trend following | **18.2%** (lowest) |

The two categories retail spends the most time on — **trend-following MA
crossovers** and **candlestick patterns** — had the worst out-of-sample survival.
"The things that get the fewest YouTube views held up the best."

---

## Verified survivors (the highlighted table)

| Strategy | Asset | OOS Sharpe | OOS Max DD | Notes |
|----------|-------|-----------|-----------|-------|
| Squeeze Momentum | ETH-USD | 0.84 | −16.4% | 376 trades, +58% over OOS windows. **Top result.** |
| Bollinger Band + RSI combo | XLU (utilities) | **1.28** | **−6.8%** | DD is the standout — genuinely controlled risk. |
| Bollinger Band reversion | XLC (comms) | 1.06 | −11.7% | |
| Chaikin Money Flow | Gold | 0.99 | −9.3% | +62.9% total over test windows. |

**Same signal verified across multiple uncorrelated assets** (this consistency
is the real tell — not one lucky dataset):

- **RSI mean reversion** → XLK, XLF, XLI, IWM (4 different/uncorrelated assets)
- **Bollinger Band reversion** → SPY, XLC, XLE
- **%B reversion** → XLU, AAPL, GOOG, XLE
- **Z-score reversion** → DIA, XLF, GOOG, AMZN, Brazil
- **Pivot bounce** → SPY, DIA
- **Golden / death cross** → Bitcoin

**Pattern is unmistakable: mean reversion dominates.** Not exotic multi-indicator
systems, not pattern recognition — the simple, mathematically grounded idea that
price reverts toward a mean.

---

## What survivors have in common (the actual lesson)

Survivors share:
- A **logical basis in market microstructure** — a *reason* it should work, not
  just evidence that it did.
- **Frequent enough trading** to be statistically significant.
- **No requirement to survive catastrophic drawdowns.**
- **Simplicity** — few parameters → less room to overfit.

Failures share:
- Complexity, many parameters optimized on history.
- Dependence on specific conditions that don't generalize.
- Or (most dangerous) they only "work" because one asset went up a lot.

**Uncomfortable truth:** genuine edge in liquid public markets exists but is
rare, requires rigorous testing to find, and produces **modest, not spectacular**
returns. Realistic verified edge on daily bars → **OOS Sharpe 0.5–1.5**.

---

## Scope tested (for context)

- **62 strategies** across: trend following (MA crossovers, MACD ×3, SuperTrend,
  Parabolic SAR, Ichimoku, Donchian, ADX, linear-regression slope, price-channel
  breakout); momentum (RSI variants, stochastics, CCI, ROC, Williams %R, MFI,
  TSI, dual/absolute momentum, Connors RSI); mean reversion (Bollinger reversion
  & squeeze, Z-score, Keltner, VWAP, %B, RSI-MR, EMA-band, dip buying); volatility
  (ATR breakout, squeeze momentum, HV breakout, range breakout); volume (OBV,
  Chaikin MF, VPT, Force Index, Elder Ray, VWAP momentum, volume-surge breakout);
  pattern (engulfing, three-bar reversal, pivot bounce, HH/HL, gap-and-go);
  composite (triple-screen, trend-quality momentum, MACD+RSI, chandelier exit).
- **31 assets** — daily bars: SPY/QQQ/IWM/DIA; sector ETFs (tech, financials,
  energy, healthcare, industrials, utilities); gold/silver/oil; long bonds, high
  yield; Europe/Brazil/EM; BTC/ETH; AAPL/MSFT/NVDA/TSLA/AMZN/GOOG/META.

---

## Transfer to this repo

This repo trades **intraday FX / gold / indices (M5–H4)**; the study is **daily
bars on US equities / sector ETFs / crypto**. So:

- **Method transfers directly.** Adopt walk-forward (70/30 sliding) + the six
  filters as the acceptance gate for CBS, IVB, ETR, and hedgehog walk-forward.
  Bake the six thresholds into the backtest harness as automatic rejects.
- **Survivor list is a prior, not a transplant.** Mean-reversion dominance is a
  hint about where to spend search effort, but XLU/ETH daily edges do not imply
  the same on XAUUSD M5. Re-verify on this repo's universe before trusting.
- **Sanity anchor.** Any in-house backtest showing OOS Sharpe > 2.5 or huge
  returns on a trending asset (XAUUSD's run, BTC) should be treated as the Tesla
  trap until proven otherwise. This matches the IVB finding (no edge once sizing
  bug fixed) — see the IVB note.
- The video's full notebook/database is **members-only**, not public. Only the
  method + results above are available.

## Open questions / caveats

- Daily bars only — says nothing about intraday microstructure edges.
- "Up to 100 Bayesian combos per strategy/asset" still risks some optimization
  bias even with walk-forward; the 30% beat-cap (filter 4) is the guard.
- No transaction-cost / slippage detail given — survivors' Sharpes are likely
  pre-cost. Net-of-cost would thin the 65 further.
- Long-only vs long/short construction per strategy not specified.
