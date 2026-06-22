# ORB — Verdict

**Strategy:** Opening Range Breakout — bias-gated index breakout (M15 opening range at the NY
09:30 open, D1 EMA(50) bias gate, RVOL ≥ 1.0, opposite-end SL, exits E0 1:1 / E1 2R / E3 EMA8-runner).
Built as a tested MQL5 EA on the FTMO feed (US100.cash dev).
**Outcome:** 🔴 **TESTED → REJECTED.** Passes on Nasdaq only; does **not generalize** → trend
exposure, not a distinct edge.

## The numbers (cross-instrument, fixed config, OOS-filtered 2022-10→2026-04)
Source: `reports/ORB-fullperiod-20260622/gate_cross_instrument.txt`.

| Instrument | exit | n | win% | PF | Sharpe(t) | maxDD | gate |
|---|---|---:|---:|---:|---:|---:|---|
| **US100** (Nasdaq) | E0 1:1 | 255 | 53.3 | **1.14** | +1.04 | −11.0% | PASS |
| **US100** | E3 EMA8 | 255 | 55.7 | **1.54** | +2.14 | −6.3% | PASS |
| US500 (S&P) | E0 | 247 | 46.6 | **0.87** | −1.06 | −20.1% | **FAIL** |
| US500 | E3 | 247 | 48.6 | 0.99 | −0.04 | −10.0% | **FAIL** |
| US30 (Dow) | E0 | 245 | 45.7 | **0.84** | −1.30 | −19.5% | **FAIL** |
| US30 | E3 | 245 | 49.0 | 1.09 | +0.42 | −12.8% | **FAIL** |

## Why rejected
1. **Only US100 passes.** US500 and US30 lose with the *same* fixed config. A real breakout edge
   would generalize across index futures; this doesn't.
2. **US100 buy-and-hold was +106%** over the period. A bias-gated bidirectional trend-follower on a
   parabolic index is most likely capturing **exposure**, not a distinct edge (the Tesla trap).
3. A walk-forward warmup bug (RVOL ring-buffer dropping ~1 month of each OOS window) had earlier
   produced a *false* "no edge", then a *false* "provisional pass" — corrected to a single
   continuous fixed-config backtest. Even corrected, the cross-instrument test is decisive: no edge.

## Note
The build + harness are sound (codified validation gate, headless MT5 tester, OnTradeTransaction
ledger). The *strategy* is what failed. Plan/spec live in `docs/superpowers/`.
