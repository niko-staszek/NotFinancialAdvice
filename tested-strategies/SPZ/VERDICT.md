# SPZ — Verdict

**Strategy:** reconstruction of the protected TradingView indicator **"Scalper Pro v4.1 [ZynAlgo]"**.
**Outcome:** 🔴 **TESTED → REJECTED for live trading.** Faithful *shell*, marginal/unproven *edge*.

## What was built
- `recovered_indicator.pine` — Pine v6 reconstruction (dashboard, regime, score, SL/TP, labels).
  Dashboard values, sub-indicator lengths and SL/TP geometry match the original **exactly**; the
  entry **selectivity** (its proprietary score) could not be recovered from a black box.
- `mt5/ScalperProReconEA.mq5` — self-contained MQL5 EA of the recon (no TradingView/bridge).
  Compiles clean; runs natively; dynamic prop-safe sizing; REAL-account guard.
- `opt/` — Python harness (mirrors the Pine logic) + walk-forward, drawdown, sizing, style sweeps.

## The numbers (audit trail in `opt/reports/`)
MT5 Strategy Tester, FTMO real-tick feed, $100k, 0.625%/trade, Intraday 13/34:

| | 6-month window | **2.5-year (significant)** |
|---|---|---|
| XAUUSD H1 | PF 1.65, DD 4.2%, n56 | **PF 1.23, DD 15.1%, n265** |
| BTCUSD H4 | PF 2.33, DD 3.6%, n17 | **PF 1.27, DD 7.4%, n98** |
| US100 H4 | PF 1.79, n15 | **PF 0.86 (loses), n83** |
| US500 / GER40 / US30 | 0.73 / 0.63 / 0.93 (all lose) | — |

## Why rejected
1. **The short window was a mirage.** On a significant sample the edge collapses to PF ~1.2–1.3,
   and that is **gross of FTMO commission** → realistically near breakeven.
2. **Gold's real drawdown is 15%**, which **breaches the 10% prop max** at 0.625% risk. Sizing down
   to stay safe (~0.2%) shrinks gold to ~3%/yr — not worth a prop fee.
3. **Does not generalize** — only gold/BTC/Nasdaq ever profit; S&P/DAX/Dow/EURUSD lose.
4. Consistent with the original's self-reported **PF 6 being in-sample, not real edge**.

## If revisited
XAU + BTC only, size to the *real* DD (~0.2% / ~0.4%), demo-only, accept tiny returns. Otherwise
treat as a research artifact. Full derivation + comparison log in [NOTES.md](NOTES.md).
