---
title: SPZ reconstruction — max drawdown at recommended settings
date: 2026-06-22
run: spz-drawdown-20260622-045911Z
kind: backtest
status: complete
tags: [audit, backtest]
metrics:
  XAUUSD_maxdd_R: 13.0
  BTCUSD_maxdd_R: 5.0
  EURUSD_maxdd_R: 13.0
  XAUUSD_pf: 1.89
  BTCUSD_pf: 1.68
  EURUSD_pf: 1.03
---

# SPZ reconstruction — max drawdown at recommended settings

Generated: 20260622-045911Z (UTC)

> [!summary] Verdict
> RECON (not original) drawdown, v3.2 defaults, GROSS of costs, single in-sample period
> XAUUSD 1h: max DD 13.0R = 12.3%/23.1% @1%/2% risk; PF 1.89, 118 trades; B&H 60.9%
> BTCUSD 4h: max DD 5.0R = 4.9%/9.6% @1%/2% risk; PF 1.68, 31 trades; B&H -42.1%
> EURUSD 1h: max DD 13.0R = 12.4%/23.6% @1%/2% risk; PF 1.03, 129 trades; B&H 12.9%
> XAUUSD: within gate (gross of costs)
> BTCUSD: within gate (gross of costs)
> EURUSD: within gate (gross of costs)

## Key results

| instrument | TF | trades | PF | max DD (R) | DD% @1% | DD% @2% |
|---|---|---:|---:|---:|---:|---:|
| XAUUSD | 1h | 118 | 1.89 | 13.0 | 12.3 | 23.1 |
| BTCUSD | 4h | 31 | 1.68 | 5.0 | 4.9 | 9.6 |
| EURUSD | 1h | 129 | 1.03 | 13.0 | 12.4 | 23.6 |

## Files (size bytes, sha256)

| file | bytes | sha256 |
|------|------:|--------|
| [[config.json]] | 628 | `1369a92b204eba7393d74a558f4770fd94a050252cada3235825bc654cb967fb` |
| [[drawdown_summary.csv]] | 359 | `f7b7693fff211e56ab58e4f204dd2e7159b7315253b2f3a1ff04f238540733e0` |
| [[recon.py]] | 8987 | `9326f820780a12bc980e37d155e37304080a910e501deb902c21a71b6388198a` |
| [[run_dd.py]] | 4749 | `4f3dfda711114b8ca87b07484069351239591630918ff569e37796c356658465` |
| [[runlog.txt]] | 612 | `e52071b73802cae2e18fcef5ba01e6dbb80df944b994978e534894aeee81bc06` |
| [[trades_BTCUSD_4h.csv]] | 2305 | `faedd84e841aeb955120bcbd234ece9730487702714aeb4a0003665acad5af03` |
| [[trades_EURUSD_1h.csv]] | 9319 | `691535675e1c153004bd539dc585acac73a292b825f9a00e48665fa47db0d2fc` |
| [[trades_XAUUSD_1h.csv]] | 8541 | `617fd7194842a3b2617dedbcbc1a2328b706033eb05d5e46f746f95e3ae02d04` |

---
[[_index|← all audit runs]]
