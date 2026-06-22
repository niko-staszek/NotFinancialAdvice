---
title: ORB-wf-validate walk-forward US100.cash
date: 2026-06-22
run: ORB-wf-validate-20260622-103653Z
kind: backtest
status: complete
tags: [audit, backtest]
metrics:
  trades: 3
  net: -99.97
  pf: 0.5
  max_dd: 0.0
  oos_sharpe: -0.51
  passed: false
---

# ORB-wf-validate walk-forward US100.cash

Generated: 20260622-103758Z (UTC)

> [!summary] Verdict
> OOS trades=3 net=-100 PF=0.50 maxDD=0.0% Sharpe=-0.51 PASS=False
> - trade count 3 < 30
> - OOS Sharpe -0.51 < 0.5 (noise)
> - profit concentration 99% > 30%

## Files (size bytes, sha256)

| file | bytes | sha256 |
|------|------:|--------|
| [[ledger_oos_S2_2026.04.01.csv]] | 504 | `97f692c31ef7a359788bda75a29de6665a6b5bc08b2b3b85d7e0f73273d541db` |
| [[ledger_oos_S2_2026.05.01.csv]] | 328 | `032370feb9b0348687eddf4240b3a0d07eb9680d1f3b554a959156d53de37dba` |
| [[oos_stitched.csv]] | 671 | `7d8ed3265929a12a10a6bd4aaf2c0e20aefd01bf99cc5cc8c666e68674d3d395` |

---
[[_index|← all audit runs]]
