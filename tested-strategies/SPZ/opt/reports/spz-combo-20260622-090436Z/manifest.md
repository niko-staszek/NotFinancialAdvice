---
title: SPZ recon — combined XAU+BTC prop-safe sizing
date: 2026-06-22
run: spz-combo-20260622-090436Z
kind: backtest
status: complete
tags: [audit, backtest]
metrics:
  combined_maxdd_R: 8.0
  risk_per_trade_pct: 0.625
  overlap_frac: 0.497
  XAU_lots100k: 0.167
  BTC_lots100k: 0.208
---

# SPZ recon — combined XAU+BTC prop-safe sizing

Generated: 20260622-090436Z (UTC)

> [!summary] Verdict
> XAU H1 + BTC H4, Intraday, ms75; limits 5%d/10%m, 2x buffer, $100,000
> combined maxDD 8.0R vs sum-of-solo 13.0R (diversification saves 5.0R); both-open 50% of time
> -> risk 0.625%/trade each, binding max-DD; proj combined maxDD 5.0% / daily 1.2%
> RECON DD not original; gross of costs; ~1y window; closed-trade DD (floating could be worse)

## Key results

| | combined | sum of solo |
|---|---:|---:|
| max DD (R) | 8.0 | 13.0 |

| instrument | risk/trade | lots/$100k |
|---|---:|---:|
| XAUUSD | 0.625% | 0.167 |
| BTCUSD | 0.625% | 0.208 |

## Files (size bytes, sha256)

| file | bytes | sha256 |
|------|------:|--------|
| [[combo_sizing.csv]] | 126 | `3d0292eaba687c0ea16c018b5302f95db023ad18600fe19d248e801aca357836` |
| [[config.json]] | 206 | `33750a2affbd015bf87e6fdedb77b5e934067ed95317b977667b1dc82508fc4e` |
| [[merged_trades.csv]] | 9968 | `9459e8dadbab82bffa827a0e33c5e8b0b565f3f687a21fc37efa455e1b6af18a` |
| [[recon.py]] | 8987 | `9326f820780a12bc980e37d155e37304080a910e501deb902c21a71b6388198a` |
| [[run_combo.py]] | 7693 | `7ea11414db7efcb5af3bbb0e9c85a481dfb1b12c60ff0e1c651ec5b28294db4f` |
| [[runlog.txt]] | 372 | `8f7478c9516a64bd00ae50025163e8d857bda6ac52eac6cba801b4f600997ff9` |
| [[summary.json]] | 285 | `ffddc5817073697c017091b103d671220b3859b20322037af0e4ef173269bddd` |

---
[[_index|← all audit runs]]
