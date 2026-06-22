---
title: ORB-sl walk-forward US100.cash
date: 2026-06-22
run: ORB-sl-20260622-103849Z
kind: backtest
status: complete
tags: [audit, backtest]
metrics:
  trades: 195
  net: -271.81
  pf: 0.97
  max_dd: -28.1618
  oos_sharpe: -0.2
  passed: false
---

# ORB-sl walk-forward US100.cash

Generated: 20260622-105452Z (UTC)

> [!summary] Verdict
> OOS trades=195 net=-272 PF=0.97 maxDD=-2816.2% Sharpe=-0.20 PASS=False
> - OOS Sharpe -0.20 < 0.5 (noise)
> - max DD -2816.2% worse than -30%
> - profit concentration 39% > 30%

## Files (size bytes, sha256)

| file | bytes | sha256 |
|------|------:|--------|
| [[ledger_oos_S0_2022.10.01.csv]] | 2358 | `e02ad6efb4b22814888064335034ebf95dfbb252f3722fd068c10e9ce9799960` |
| [[ledger_oos_S0_2023.01.01.csv]] | 2622 | `6c8d99839ba0e239b143de3f9797c789ebefc1edc7ffebe552db535b760fd454` |
| [[ledger_oos_S0_2024.01.01.csv]] | 1802 | `9bbf44be611ebba68364c3876f4b84dfac7698348b0fb400a3426ccd8cb434ea` |
| [[ledger_oos_S0_2024.04.01.csv]] | 2896 | `847afdd60c5c0b7e239ae19718045a59ef534de546e176f39700c1a61ce5446c` |
| [[ledger_oos_S0_2024.10.01.csv]] | 1844 | `9d3970b25193cad24c73e2385e1561ebcded0de3936b7bc1f441f3145cd65ef3` |
| [[ledger_oos_S0_2025.01.01.csv]] | 2067 | `07082a4004f779e06510a05cac2f6d64ef0bb0292c15a58a6a8d07de58fa829e` |
| [[ledger_oos_S0_2026.01.01.csv]] | 2365 | `46e6084aa5bf9345f5843cd1816c67851d57c6825cdedf21016e2ee9d8c62b3d` |
| [[ledger_oos_S2_2023.04.01.csv]] | 2698 | `87859b0e4f6bbc37663453dc8cd0101beb77b941d43d62ddcec52add501c6de9` |
| [[ledger_oos_S2_2023.07.01.csv]] | 2836 | `d61dc7569a09debf78681962b1faf369371257775d8e7cf58582b1a69340468a` |
| [[ledger_oos_S2_2023.10.01.csv]] | 2824 | `fd8d7ce9d7339090feee9938846eeb43072a20a8b6d5f7bd5aae56e140978e1c` |
| [[ledger_oos_S2_2024.07.01.csv]] | 2840 | `45d2a9c3ebb9952bc8af6855ead39d0e2deb8923b728f18785719f9c302dd221` |
| [[ledger_oos_S2_2025.04.01.csv]] | 2230 | `7f4f3a8a7cc6336d27c8944f1e65d33f52c1861e3fa83c5b26f7e8a91141c29b` |
| [[ledger_oos_S2_2025.07.01.csv]] | 3129 | `10788b82e5d32cc95ef71bdc5019e1f42f5cce45f23cbf1302a4b7cee6c3c495` |
| [[ledger_oos_S2_2025.10.01.csv]] | 2518 | `8615e82ead3a148f15602c28b0aceda7ff977b6defca955a8e467db46092340b` |
| [[oos_stitched.csv]] | 32936 | `0e48c2de2bd79221b62a65950c8b3c5e6e91969fd49f6da903e68f024f085ba7` |

---
[[_index|← all audit runs]]
