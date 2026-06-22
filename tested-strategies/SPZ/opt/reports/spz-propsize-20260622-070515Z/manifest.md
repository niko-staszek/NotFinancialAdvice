---
title: "SPZ reconstruction — prop-safe sizing (5% daily / 10% max)"
date: 2026-06-22
run: spz-propsize-20260622-070515Z
kind: backtest
status: complete
tags: [audit, backtest]
metrics:
  XAUUSD_risk_pct: 0.385
  BTCUSD_risk_pct: 1.0
  EURUSD_risk_pct: 0.385
  XAUUSD_lots100k: 0.103
  BTCUSD_lots100k: 0.333
  EURUSD_lots100k: 1.039
---

# SPZ reconstruction — prop-safe sizing (5% daily / 10% max)

Generated: 20260622-070516Z (UTC)

> [!summary] Verdict
> limits daily 5.0% / max 10.0%, 2.0x safety buffer, $100,000 account
> RECON DD (not original), GROSS of costs, ~1-1.5y single period -> buffer is essential
> XAUUSD 1h: risk 0.385%/trade (~0.103 lots/$100k), binding=max-DD, proj maxDD 5.0%/daily 0.8%
> BTCUSD 4h: risk 1.0%/trade (~0.333 lots/$100k), binding=max-DD, proj maxDD 5.0%/daily 1.0%
> EURUSD 1h: risk 0.385%/trade (~1.039 lots/$100k), binding=max-DD, proj maxDD 5.0%/daily 0.8%

## Key results

| instrument | TF | maxDD R | worstDay R | binding | risk/trade % | lots/$100k |
|---|---|---:|---:|---|---:|---:|
| XAUUSD | 1h | 13.0 | 2.0 | max-DD | 0.385 | 0.103 |
| BTCUSD | 4h | 5.0 | 1.0 | max-DD | 1.0 | 0.333 |
| EURUSD | 1h | 13.0 | 2.0 | max-DD | 0.385 | 1.039 |

## Files (size bytes, sha256)

| file | bytes | sha256 |
|------|------:|--------|
| [[config.json]] | 472 | `b02f5d852d7f9c11be456bcff4afb93484ba2f46c37855c77305cf5b49da333e` |
| [[propsize.csv]] | 347 | `f2a7dabea24309926f30ed889935f8323099d82bddbfa9098970e02dacc5ed87` |
| [[recon.py]] | 8987 | `9326f820780a12bc980e37d155e37304080a910e501deb902c21a71b6388198a` |
| [[run_propsize.py]] | 5753 | `6dd74a13e9ab8c8115ceff0ad0b7a178c1fae012576145aebe6270bed7ab54b5` |
| [[runlog.txt]] | 497 | `6f48fd3a1bb6629e56e5acab376da19ee257b3f032099886bdd9220c276247c1` |
| [[trades_BTCUSD_4h.csv]] | 2305 | `faedd84e841aeb955120bcbd234ece9730487702714aeb4a0003665acad5af03` |
| [[trades_EURUSD_1h.csv]] | 9319 | `691535675e1c153004bd539dc585acac73a292b825f9a00e48665fa47db0d2fc` |
| [[trades_XAUUSD_1h.csv]] | 8541 | `617fd7194842a3b2617dedbcbc1a2328b706033eb05d5e46f746f95e3ae02d04` |

---
[[_index|← all audit runs]]
