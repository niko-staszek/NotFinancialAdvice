# NotFinancialAdvice

Trading strategy research, backtesting, and automation across forex, crypto, indices, and commodities.

---

## Strategies

| Strategy | Description | Instruments | Timeframe |
|----------|-------------|-------------|-----------|
| [PAC](PAC/strategy.md) | **Price Action Cycle** — Intraday price action combining candlestick signals, trend structure, Fibonacci, Elliott Waves, and session context | XAUUSD, USOIL, US500, US30, USTECH, GBPUSD, EURUSD, BTCUSD + futures | M5 / Tick |
| [MRD](MRD/strategy.md) | **Midweek Range Division** — Weekly-cycle strategy using Mon-Tue range as a box, trading the Wednesday directional breakout | EURUSD, US500, US100 | H1 |
| [API](API/strategy.md) | **API Box** — Session-range mean-reversion using Fibonacci scaled limit orders off the overnight box | EURUSD, GBPUSD, USDCHF, USDJPY | M5 |
| [MMD](MMD/MMD_CLOUDS.md) | **Magic Moving Averages** — Multi-layer cloud system (standalone strategy + indicator/filter for other strategies) | Any | H1 (primary) |
| [CBS](CBS/strategy.md) | **"Can't Be Simpler"** — Target-driven strategy using H+L-O pivot with Fibonacci clusters, three sub-strategies (Reaction, Coming, Averaging) | Forex majors, XAUUSD, XTIUSD, BTCUSD, ETHUSD | H1 (exec), H4 (trend) |
| [MF](MF/strategy.md) | **Money Flow** — Swing strategy aligning entries with COT large-speculator positioning, the Money Flow indicator, and technical confluence (EMA/SMA cross, Fibonacci, POC) | Minor crosses (primary), majors, XAUUSD, USOIL, indices | H4 / H1 |

## How Strategies Connect

```
MMD Clouds (trend / regime filter)
 |
 +-- PAC uses MMD for trend-or-range-day classification
 +-- MRD uses MMD for extended R:R confirmation
 +-- API uses MMD for consolidation regime filter
```

## Validation & Research

- [**Strategy validation rules**](docs/strategy-validation.md) — standing rulebook for building/backtesting/judging any strategy here (walk-forward, auto-reject gate, red flags, pre-claim checklist). Enforced for AI sessions via [CLAUDE.md](CLAUDE.md).
- [Backtest survival study](research/backtest-survival-study.md) — knowhow from a 131,441-run meta-study on what survives rigorous testing (mean reversion dominates; real edge ≈ OOS Sharpe 0.5–1.5).

## Reference Links

Each strategy folder may contain a `links.md` with video references:

- [PAC reference videos](PAC/links.md) — 16 videos covering each PAC component
- [API reference videos](API/links.md)
- [CBS reference videos](CBS/links.md) — PSND series (6 parts)
- [MF reference videos](MF/links.md) — Money Flow series (3 parts)

## Repo Structure

```
NotFinancialAdvice/
  PAC/          Price Action Cycle
  MRD/          Midweek Range Division
  API/          API Box (session range mean-reversion)
  MMD/          Magic Moving Averages (clouds, diamonds, ribbons, schemas)
  CBS/          "Can't Be Simpler" (target-driven, 3 sub-strategies)
  MF/           Money Flow (COT + flow-based swing)
  docs/         Cross-cutting rules & specs (see strategy-validation.md)
  research/     General research & notes
```
