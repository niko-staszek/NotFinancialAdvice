---
title: "SPZ recon EA — 2.5-year MT5 backtest (FTMO real-tick, 2024-01..2026-06)"
date: 2026-06-22
run: spz-mt5-longrun-20260622-124132Z
kind: backtest
status: complete
tags: [audit, backtest]
metrics:
  XAUUSD_pf: 1.23
  BTCUSD_pf: 1.27
  US100.cash_pf: 0.86
  XAUUSD_ddpct: 15.09
  BTCUSD_ddpct: 7.41
  US100.cash_ddpct: 12.59
---

# SPZ recon EA — 2.5-year MT5 backtest (FTMO real-tick, 2024-01..2026-06)

Generated: 20260622-124132Z (UTC)

> [!summary] Verdict
> RECON EA, FTMO feed, real ticks, 100k, risk 0.625%/trade, Intraday 13/34; n now significant
> XAUUSD H1: PF 1.23, maxDD 15.1% (BREACHES 10% prop cap at this sizing), n265, +23%
> BTCUSD H4: PF 1.27, maxDD 7.4%, n98, +9%
> US100 H4:  PF 0.86 -> LOSES over the long window (6-month win was regime luck), n83
> VERDICT: 6-month numbers were optimistic; long-sample edge is MARGINAL (PF ~1.2-1.3, gross of
> commission) and gold DD breaches prop limits at the assumed size. Does NOT clear the gate.

## Key results

| symbol | TF | PF | maxDD% | trades | net |
|---|---|---:|---:|---:|---:|
| XAUUSD | H1 | 1.23 | 15.09 | 265 | +23131 |
| BTCUSD | H4 | 1.27 | 7.41 | 98 | +9411 |
| US100.cash | H4 | 0.86 | 12.59 | 83 | -5058 |

## Files (size bytes, sha256)

| file | bytes | sha256 |
|------|------:|--------|
| [[ScalperProReconEA.mq5]] | 10564 | `7db6a917c29eeda1e1d6fb99f3630e543509e232d75cb93d010120aa5af5dddf` |
| [[result_BTCUSD.txt]] | 240 | `6719249426c24b1dedb357a9e77801ff46d823367dc9e65c553549afd2d7eeb3` |
| [[result_US100.cash.txt]] | 256 | `a461a667fe42fdea3cc2c31fe9f2f529c4d73144c593a1c38ca34435749c3665` |
| [[result_XAUUSD.txt]] | 250 | `706ef3274ed8717d6cdc06740e52e8b6ffa451b6f8d179aa7b70338763bc0f08` |

---
[[_index|← all audit runs]]
