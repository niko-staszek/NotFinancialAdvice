# SweepHunter — Verdict

**Strategy:** ICT Asia/London session-liquidity sweep → NY M1 fair-value-gap reversal. At 09:00 ET
mark prior Asia (20:00–00:00 ET) and London (02:00–05:00 ET) session highs/lows; during the NY hunt
window (09:00–11:30 ET) wait for a level sweep; drop to M1 and enter an FVG reversal the other way;
stop at the sweep swing; target fixed 1:2 RR or the next draw-on-liquidity (both carried as
candidates). Built as a tested MQL5 EA on the FTMO feed.

**Outcome:** 🔴 **TESTED → REJECTED.** No edge. Fails the acceptance gate on all three primary
instruments, with **negative in-sample Sharpe everywhere** — the optimizer could not find profitable
parameters even on the training data, so there is nothing to generalize.

## The numbers (walk-forward OOS, IS 12mo/OOS 3mo/slide 3mo, 2023.01–2026.06, net of costs)
Source: `reports/SweepHunter-xinstr-20260622-175201Z/summary.md` and each
`reports/SweepHunter-wf-<sym>-20260622-175201Z/gate.txt`.

| Instrument | OOS n | win% | net /10k | PF | OOS Sharpe | IS Sharpe | maxDD | gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| XAUUSD | 438 | 28.5 | −6619 | 0.78 | **−1.94** | −0.99 | **−86.6%** | FAIL |
| EURUSD | 439 | 36.2 | +3087 | 1.10 | 0.72 | −0.03 | −20.7% | FAIL |
| US100.cash | 488 | 30.1 | −918 | 0.97 | −0.19 | −0.65 | −42.2% | FAIL |

## Why rejected
1. **No in-sample edge.** IS Sharpe is negative on all three instruments (−0.99 / −0.03 / −0.65). A
   strategy that cannot be made profitable on the data the optimizer *sees* has no signal to begin
   with — this is a stronger rejection than mere overfitting.
2. **XAUUSD is a blow-up:** −86.6% max drawdown, PF 0.78, Sharpe negative in and out of sample.
3. **EURUSD's positive net is a mirage:** one trade carries 57% of net P&L (gate #7) and IS Sharpe is
   ≈0, so the +0.72 OOS Sharpe is variance, not edge.
4. **US100.cash loses** (−42.2% DD, PF 0.97, concentration 228%).
5. **Worse than buy-and-hold.** XAUUSD and US100 both trended strongly up over 2023–2026; SweepHunter
   lost money on both. It does not even capture exposure (not the Tesla trap — an outright loser).
6. **The preferred exit doesn't save it.** Draw-on-liquidity targets (`dol`/`dol_combined`) won most
   walk-forward windows yet still failed — the deficiency is the entry, not the target.

Consistent with this repo's priors (§4 of `docs/strategy-validation.md`): breakout/sweep and
candlestick-pattern families survive least; ORB, SPZ, IVB, ETR were likewise rejected.

## Scope note
Quick primary pass (XAUUSD, EURUSD, US100.cash) was decisive, so the full 9-instrument sweep
(GBPUSD, USDJPY, USDCHF, US30.cash, US500.cash, BTCUSD) was not run — it would not change the
verdict. The harness supports it (`tools/run_sweephunter_walkforward.py <sym> <start> <end> --stamp <s>`)
should anyone want the complete table.

## Note
The build and harness are sound: 8 unit-tested pure modules (53 assertions), headless MT5 tester,
`OnTradeTransaction` ledger with context derived from the closing position, codified acceptance gate,
walk-forward driver. A real lifecycle bug (phantom second positions when a limit filled and stopped
out within one M1 bar) was caught by behavioral testing and root-cause-fixed. The *strategy* is what
failed, not the implementation. Spec/plan live in `docs/superpowers/`.
