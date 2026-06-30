# Tested strategies

Strategies that have been through **backtesting / validation** (not just spec'd), each with a
recorded verdict. Pass or fail, the work + audit trail lives here so a result is never re-litigated
from scratch. Validation rules: [docs/strategy-validation.md](../docs/strategy-validation.md).

| Strategy | What | Status | Verdict |
|---|---|---|---|
| [SPZ](SPZ/VERDICT.md) | Reverse-engineered "Scalper Pro v4.1 [ZynAlgo]" TradingView indicator → Pine v6 recon → self-contained MT5 EA | **Tested** | 🔴 **Rejected for live** — marginal edge (PF ~1.2–1.3 over 2.5y, gross of costs), gold DD breaches the 10% prop cap at usable sizing, indices/EURUSD lose. Faithful reconstruction; no robust edge. |
| [ORB](ORB/VERDICT.md) | Bias-gated Opening Range Breakout index EA (M15 OR @ NY open, D1 EMA bias, RVOL), MQL5 on FTMO | **Tested** | 🔴 **Rejected** — passes on US100/Nasdaq only (PF 1.14–1.54); US500 & US30 fail with the same config → trend exposure, not a generalizable edge. |
Each strategy folder holds its source, the test harness, and `reports/` audit folders (raw results
+ config + driver + sha256 manifest per run). See the strategy's `VERDICT.md` for the bottom line.
