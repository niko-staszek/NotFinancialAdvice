---
title: SPZ reconstruction — walk-forward param search
date: 2026-06-21
run: spz-walkforward-20260621-204751Z
kind: backtest
status: complete
tags: [audit, backtest]
metrics:
  oos_pf: 2.235
  oos_exp_R: 0.7
  oos_n: 60
  baseline_oos_pf: 1.712
  gold_bh_pct: 60.9
---

# SPZ reconstruction — walk-forward param search

Generated: 20260621-204800Z (UTC)

> [!summary] Verdict
> data 2025-01-07..2026-06-09 XAUUSD H1 (8360 bars), 3 anchored folds
> STITCHED blind OOS: pf=2.24 exp=0.700R n=60 win%=43
> baseline v3.2 over OOS span: pf=1.71 exp=0.435R n=85
> gold buy&hold over period: 61% (Tesla-trap: long-biased PF rides this)

## Key results

| metric | stitched OOS | baseline OOS |
|---|---:|---:|
| PF | 2.24 | 1.71 |
| exp (R) | 0.700 | 0.435 |
| trades | 60 | 85 |

## Files (size bytes, sha256)

| file | bytes | sha256 |
|------|------:|--------|
| [[config.json]] | 1120 | `c458d216b4db31426819aaa6ee75a2e2120ae5dcd4cf6c9b1dff8f8edaad5b6d` |
| [[is_grid_all_combos.csv]] | 65379 | `e43bfb289661dd6e9521bbc63e2a8b047c8eb99b732b86bc9de4a45be0abb7c2` |
| [[recon.py]] | 8098 | `952a8beea4848267c1cb7167ea171f34ae2801518d79d8e065b4988ea2e05509` |
| [[run_search.py]] | 6742 | `811eeeb4f2da15af4d1646523016c743e676b868bb5dcac8aedd0512c19f8505` |
| [[runlog.txt]] | 1175 | `3dde39da6151270e76db69a80326428e27d830cbc6488105f38e5fafc301400f` |
| [[selected_per_fold.csv]] | 525 | `d07abe8594814f645e384f4c630eebf0123e7138e404b449c6f1d62f678c66f0` |
| [[stitched_oos_trades.csv]] | 4519 | `fece4f96a26c46711480247dc0591249be70cc7f7770614b1ee5ee0c11630cd4` |

---
[[_index|← all audit runs]]
