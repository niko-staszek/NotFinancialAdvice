# NotFinancialAdvice — project instructions

Trading strategy research, backtesting, and automation (forex, crypto, indices,
commodities). Each strategy lives in its own folder with `strategy.md` (+ often
`links.md`). See [README.md](README.md) for the strategy map.

## Strategy validation — the standing rule

**Before claiming any strategy "works", "has edge", or reporting its numbers,
follow [docs/strategy-validation.md](docs/strategy-validation.md).** Full rules,
rationale, and the per-claim checklist are there. The non-negotiable core:

- **Out-of-sample or it didn't happen.** A backtest over all history with tuned
  parameters is not evidence. Use **walk-forward** (optimize on ~70% of each
  window, run blind on the remaining ~30%, stitch the OOS segments, report that).
- **Auto-reject gate** (apply to every backtest, don't eyeball):
  - OOS max drawdown worse than −35% (tighter for leveraged FX) → reject.
  - OOS Sharpe < 0.5 (noise) or > 2.5 (the asset did the work) → reject.
  - OOS Sharpe beats in-sample by > 30% → luck, reject.
  - < 30 trades → not significant.
  - Any single trade > ~25–30% of net P&L → concentration, reject.
  - Metrics not net of spread/commission/slippage → recompute, don't report.
- **Sanity:** would buy-and-hold of the asset have matched it? If yes, it's
  exposure, not edge (the "Tesla trap").
- **Priors:** mean-reversion and simple, few-parameter strategies survive far
  more often than trend-following / candlestick patterns. Real edge on daily
  bars ≈ OOS Sharpe 0.5–1.5 — modest, not spectacular.

If a result hasn't cleared the gate, report it as **provisional / in-sample
only** and name the missing checks. Do not round "promising" up to "works".

Log new empirical findings to the Findings table in `docs/strategy-validation.md`.

## Quantitative work

Any backtest / optimization / walk-forward run that produces a reported number
must leave an audit trail (raw result file + config + driver + log + manifest),
and no metric may be stated unless it traces to a file inspected that session.
The `audit-trail` skill enforces this — use it whenever running or reporting a
measurement.
