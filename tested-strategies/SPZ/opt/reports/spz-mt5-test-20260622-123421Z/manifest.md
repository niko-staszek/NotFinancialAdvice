---
title: "SPZ recon EA — MT5 Strategy Tester (FTMO real-tick, 2025-12..2026-06)"
date: 2026-06-22
run: spz-mt5-test-20260622-123421Z
kind: backtest
status: complete
tags: [audit, backtest]
metrics:
  XAU_pf: 1.65
  XAU_ddpct: 4.21
  XAU_trades: 56
  BTC_pf: 2.33
  BTC_ddpct: 3.55
  BTC_trades: 17
---

# SPZ recon EA — MT5 Strategy Tester (FTMO real-tick, 2025-12..2026-06)

Generated: 20260622-123422Z (UTC)

> [!summary] Verdict
> self-contained MQL5 EA of the recon, FTMO feed, real ticks, 100k deposit, risk 0.625%/trade, Intraday 13/34
> XAUUSD H1: PF 1.65, maxDD 4.21%, 56 trades, +12.5% (n>=30 OK)
> BTCUSD H4: PF 2.33, maxDD 3.55%, 17 trades, +5.95% (n<30 NOT significant)
> matches the Python recon (XAU ~1.5, BTC ~2.0) -> port verified; DD well inside 10% cap
> single 6-month window (in-sample-ish); spread via real ticks, commission per account; NOT OOS-validated; demo-forward-test before live

## Key results

| symbol | TF | PF | maxDD% | trades | net% |
|---|---|---:|---:|---:|---:|
| XAUUSD | H1 | 1.65 | 4.21 | 56 | +12.5 |
| BTCUSD | H4 | 2.33 | 3.55 | 17 | +5.95 |

## Files (size bytes, sha256)

| file | bytes | sha256 |
|------|------:|--------|
| [[SPZ.set]] | 73 | `09c22ed2f8753dc4874c7d2b740fe99242036743b47b44f896132bd497a643e1` |
| [[ScalperProReconEA.mq5]] | 10564 | `7db6a917c29eeda1e1d6fb99f3630e543509e232d75cb93d010120aa5af5dddf` |
| [[result_BTCUSD.txt]] | 238 | `9b4e377d3f86d3bc64b87c4aed48d5fa28e2f7e19995943d0a8ebf822db1b3e8` |
| [[result_XAUUSD.txt]] | 244 | `968aaa969972eadc49d0952406fbe2523a73a1c4bd2f241f4f8845d868d13c63` |
| [[spz_btc.ini]] | 670 | `68d9c981632261104bd85253131b1af80b30d83dd3b7d2d5e6cd5ce0217ef60b` |
| [[spz_xau.ini]] | 670 | `ab3718b9ab929fe2f025d1a7cc02262a45d3d934ee5330000154edf00c3d57e4` |
| [[tester_result_lines.txt]] | 2 | `7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6` |

---
[[_index|← all audit runs]]
