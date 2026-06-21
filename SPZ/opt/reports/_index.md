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
