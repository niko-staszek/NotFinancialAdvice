---
title: "SPZ recon EA — MT5 Strategy Tester (FTMO real-tick, 2025-12..2026-06)"
date: 2026-06-22
run: spz-mt5-test-20260622-123910Z
kind: backtest
status: complete
tags: [audit, backtest]
metrics:
  BTCUSD_pf: 2.33
  US100.cash_pf: 1.79
  XAUUSD_pf: 1.65
  US30.cash_pf: 0.93
  US500.cash_pf: 0.73
  GER40.cash_pf: 0.63
  BTCUSD_ddpct: 3.55
  US100.cash_ddpct: 5.1
  XAUUSD_ddpct: 4.21
  US30.cash_ddpct: 5.88
  US500.cash_ddpct: 7.36
  GER40.cash_ddpct: 4.08
---

# SPZ recon EA — MT5 Strategy Tester (FTMO real-tick, 2025-12..2026-06)

Generated: 20260622-123911Z (UTC)

> [!summary] Verdict
> self-contained MQL5 EA of the recon, FTMO feed, real ticks, 100k deposit, risk 0.625%/trade, Intraday 13/34
> WINNERS: XAUUSD H1 (PF 1.65, n56), BTCUSD H4 (2.33, n17), US100 H4 (1.79, n15)
> LOSERS:  US500 (0.73), GER40 (0.63), US30 (0.93) -> do NOT trade these with this EA
> instrument-specific edge (gold/BTC/Nasdaq = the user's stated combos); does NOT generalize to S&P/DAX/Dow
> ALL non-gold n<30 -> NOT significant; single 6-month window; gross of commission; NOT OOS-validated; demo-forward-test before live

## Key results

| symbol | TF | PF | maxDD% | trades | net |
|---|---|---:|---:|---:|---:|
| BTCUSD | H4 | 2.33 | 3.55 | 17 | +5953 |
| US100.cash | H4 | 1.79 | 5.10 | 15 | +4177 |
| XAUUSD | H1 | 1.65 | 4.21 | 56 | +12465 |
| US30.cash | H4 | 0.93 | 5.88 | 16 | -449 |
| US500.cash | H4 | 0.73 | 7.36 | 16 | -1981 |
| GER40.cash | H4 | 0.63 | 4.08 | 17 | -2783 |

## Files (size bytes, sha256)

| file | bytes | sha256 |
|------|------:|--------|
| [[SPZ.set]] | 73 | `09c22ed2f8753dc4874c7d2b740fe99242036743b47b44f896132bd497a643e1` |
| [[ScalperProReconEA.mq5]] | 10564 | `7db6a917c29eeda1e1d6fb99f3630e543509e232d75cb93d010120aa5af5dddf` |
| [[result_BTCUSD.txt]] | 238 | `9b4e377d3f86d3bc64b87c4aed48d5fa28e2f7e19995943d0a8ebf822db1b3e8` |
| [[result_GER40.cash.txt]] | 252 | `91318e2bcabfbaa441c94ee4484dea7ae4c918f11e86f1c8c2aba8357c69bc2c` |
| [[result_US100.cash.txt]] | 246 | `01ab0b814a954620e0e553e61a5103c8af1951e9ad548f52f70a9be27262ab3e` |
| [[result_US30.cash.txt]] | 246 | `708fd0c5f93ab4543c03cab91cc43842a68d9e97c5cd42f37e2d5825c0e081bb` |
| [[result_US500.cash.txt]] | 252 | `ebbb07da49c535416ac69a0fe5a25f831f96424bbf8f8f0de1d76e6d3471b34f` |
| [[result_XAUUSD.txt]] | 244 | `968aaa969972eadc49d0952406fbe2523a73a1c4bd2f241f4f8845d868d13c63` |
| [[spz_GER40_cash.ini]] | 692 | `aedeb308659049c9ca9b3c1a1ba9281ddecc32b2c1a3b5feb791029ec8ef9912` |
| [[spz_US100_cash.ini]] | 692 | `ea536d37dc6a8b6354f2f84f1b3490f055e134965c291f524e82208b0c7d5fe5` |
| [[spz_US30_cash.ini]] | 688 | `be268eaffa03bc00cbb0837ad10e5c30fe9c882b85056708aabefd0cfc905162` |
| [[spz_US500_cash.ini]] | 692 | `e09487d14f90a5340c8a0abd9ca4c9689487c50d041f7e501f70f1fe56fcd9c0` |
| [[spz_btc.ini]] | 670 | `68d9c981632261104bd85253131b1af80b30d83dd3b7d2d5e6cd5ce0217ef60b` |
| [[spz_xau.ini]] | 670 | `ab3718b9ab929fe2f025d1a7cc02262a45d3d934ee5330000154edf00c3d57e4` |
| [[tester_result_lines.txt]] | 2 | `7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6` |

---
[[_index|← all audit runs]]
