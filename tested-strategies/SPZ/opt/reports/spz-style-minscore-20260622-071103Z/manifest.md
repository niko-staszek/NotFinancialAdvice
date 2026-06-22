---
title: SPZ recon — Trading Style x minScore sensitivity
date: 2026-06-22
run: spz-style-minscore-20260622-071103Z
kind: sweep
status: complete
tags: [audit, sweep]
metrics:
  runs: 27
---

# SPZ recon — Trading Style x minScore sensitivity

Generated: 20260622-071104Z (UTC)

> [!summary] Verdict
> per-instrument style + minScore sweep; RECON DD, gross of costs, single ~1-1.5y period
> score is coarse (steps of 25) so minScore <=75 behaves alike; >75 needs all-aligned+ADX
> XAUUSD Scalp ms50: n=182 pf=1.29 maxDD=13.0R
> XAUUSD Scalp ms75: n=176 pf=1.3 maxDD=12.0R
> XAUUSD Scalp ms100: n=142 pf=1.4 maxDD=10.0R
> XAUUSD Intraday ms50: n=154 pf=1.5 maxDD=8.0R
> XAUUSD Intraday ms75: n=155 pf=1.46 maxDD=9.0R
> XAUUSD Intraday ms100: n=126 pf=1.51 maxDD=9.0R
> BTCUSD Swing ms50: n=31 pf=1.68 maxDD=5.0R
> BTCUSD Swing ms75: n=31 pf=1.68 maxDD=5.0R
> BTCUSD Swing ms100: n=25 pf=1.56 maxDD=4.0R
> EURUSD Swing ms50: n=132 pf=1.04 maxDD=11.0R
> EURUSD Swing ms75: n=129 pf=1.03 maxDD=13.0R
> EURUSD Swing ms100: n=118 pf=1.07 maxDD=10.0R

## Key results

| instrument | style | EMAs | minScore | trades | PF | exp R | win% | maxDD R |
|---|---|---|---:|---:|---:|---:|---:|---:|
| XAUUSD | Scalp | 9/21 | 50 | 182 | 1.29 | 0.187 | 34.6 | 13.0 |
| XAUUSD | Scalp | 9/21 | 75 | 176 | 1.3 | 0.193 | 35.2 | 12.0 |
| XAUUSD | Scalp | 9/21 | 100 | 142 | 1.4 | 0.254 | 35.9 | 10.0 |
| XAUUSD | Intraday | 13/34 | 50 | 154 | 1.5 | 0.312 | 37.7 | 8.0 |
| XAUUSD | Intraday | 13/34 | 75 | 155 | 1.46 | 0.29 | 36.8 | 9.0 |
| XAUUSD | Intraday | 13/34 | 100 | 126 | 1.51 | 0.317 | 37.3 | 9.0 |
| XAUUSD | Swing | 21/50 | 50 | 118 | 1.93 | 0.542 | 41.5 | 13.0 |
| XAUUSD | Swing | 21/50 | 75 | 118 | 1.89 | 0.525 | 40.7 | 13.0 |
| XAUUSD | Swing | 21/50 | 100 | 109 | 1.55 | 0.358 | 34.9 | 14.0 |
| BTCUSD | Scalp | 9/21 | 50 | 47 | 1.5 | 0.277 | 44.7 | 8.0 |
| BTCUSD | Scalp | 9/21 | 75 | 44 | 1.15 | 0.091 | 38.6 | 8.0 |
| BTCUSD | Scalp | 9/21 | 100 | 32 | 1.74 | 0.438 | 40.6 | 6.0 |
| BTCUSD | Intraday | 13/34 | 50 | 34 | 2.18 | 0.588 | 50.0 | 4.0 |
| BTCUSD | Intraday | 13/34 | 75 | 34 | 2.0 | 0.529 | 47.1 | 4.0 |
| BTCUSD | Intraday | 13/34 | 100 | 29 | 2.06 | 0.586 | 44.8 | 4.0 |
| BTCUSD | Swing | 21/50 | 50 | 31 | 1.68 | 0.419 | 38.7 | 5.0 |
| BTCUSD | Swing | 21/50 | 75 | 31 | 1.68 | 0.419 | 38.7 | 5.0 |
| BTCUSD | Swing | 21/50 | 100 | 25 | 1.56 | 0.36 | 36.0 | 4.0 |
| EURUSD | Scalp | 9/21 | 50 | 179 | 1.01 | 0.006 | 30.2 | 18.0 |
| EURUSD | Scalp | 9/21 | 75 | 175 | 1.07 | 0.051 | 30.9 | 15.0 |
| EURUSD | Scalp | 9/21 | 100 | 148 | 1.2 | 0.135 | 33.1 | 15.0 |
| EURUSD | Intraday | 13/34 | 50 | 158 | 1.04 | 0.025 | 29.7 | 13.0 |
| EURUSD | Intraday | 13/34 | 75 | 156 | 0.98 | -0.013 | 28.8 | 16.0 |
| EURUSD | Intraday | 13/34 | 100 | 137 | 1.2 | 0.139 | 32.1 | 13.0 |
| EURUSD | Swing | 21/50 | 50 | 132 | 1.04 | 0.03 | 29.5 | 11.0 |
| EURUSD | Swing | 21/50 | 75 | 129 | 1.03 | 0.023 | 28.7 | 13.0 |
| EURUSD | Swing | 21/50 | 100 | 118 | 1.07 | 0.051 | 28.8 | 10.0 |

## Files (size bytes, sha256)

| file | bytes | sha256 |
|------|------:|--------|
| [[config.json]] | 716 | `6ede15d2d3b57e6d3e6a27e3803aadbd02d4390c9ce8a00919e43440aae9ab93` |
| [[recon.py]] | 8987 | `9326f820780a12bc980e37d155e37304080a910e501deb902c21a71b6388198a` |
| [[run_styles.py]] | 4604 | `d81ee1d986036ea39f343e03de1e4ca42c7dcc2a026c169be213fbf3032fc219` |
| [[runlog.txt]] | 2460 | `433a737c3659a8110e6b475ace22aae71fc9ba82b1530b57b29b708caa469d69` |
| [[style_minscore_grid.csv]] | 2101 | `6ab687f7a0f9e11c0eadbf0c6d58d18f4c0c0a0347f834f3996cc2e970088b6b` |

---
[[_index|← all audit runs]]
