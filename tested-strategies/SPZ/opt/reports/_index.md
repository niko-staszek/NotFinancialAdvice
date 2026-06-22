---
title: Audit Runs
tags: [audit, moc]
---

# Audit Runs

Map of content for every audit folder under `reports/`. Each run note carries a verdict callout, the metrics in frontmatter, and a sha256 inventory.

```dataview
table kind, status, date, metrics
from #audit
where file.name = "manifest"
sort date desc
```

## All runs

- [[spz-walkforward-20260621-204751Z/manifest|SPZ reconstruction — walk-forward param search]] <!--run:spz-walkforward-20260621-204751Z--> — `backtest` / complete — data 2025-01-07..2026-06-09 XAUUSD H1 (8360 bars), 3 anchored folds
- [[spz-style-minscore-20260622-071103Z/manifest|SPZ recon — Trading Style x minScore sensitivity]] <!--run:spz-style-minscore-20260622-071103Z--> — `sweep` / complete — per-instrument style + minScore sweep; RECON DD, gross of costs, single ~1-1.5y period
- [[spz-propsize-20260622-070515Z/manifest|SPZ reconstruction — prop-safe sizing (5% daily / 10% max)]] <!--run:spz-propsize-20260622-070515Z--> — `backtest` / complete — limits daily 5.0% / max 10.0%, 2.0x safety buffer, $100,000 account
- [[spz-drawdown-20260622-045911Z/manifest|SPZ reconstruction — max drawdown at recommended settings]] <!--run:spz-drawdown-20260622-045911Z--> — `backtest` / complete — RECON (not original) drawdown, v3.2 defaults, GROSS of costs, single in-sample period
- [[spz-combo-20260622-090436Z/manifest|SPZ recon — combined XAU+BTC prop-safe sizing]] <!--run:spz-combo-20260622-090436Z--> — `backtest` / complete — XAU H1 + BTC H4, Intraday, ms75; limits 5%d/10%m, 2x buffer, $100,000
