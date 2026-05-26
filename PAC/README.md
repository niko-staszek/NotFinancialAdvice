# PAC — Price Action Cycle

Polish-language trading curriculum by Paweł Krynicki, taught in the *ALLinTraders x MFA Traders* Discord community. Implementable EA subset documented in `strategy_ea.md`.

## Documents in this folder

| File | Purpose | Audience |
|---|---|---|
| [strategy.md](strategy.md) | Full PAC curriculum reference (40 KB, 15+ components). | Anyone studying the strategy. |
| [strategy_ea.md](strategy_ea.md) | Implementable EA spec — the 10 components automated in v1 with quantitative thresholds + risk rules. | EA implementer (MQL5 + Python ref impl + Pine indicators). |
| [review.md](review.md) | Critical assessment of PAC as a tradeable system. Recommends "PAC Lite" and flags missing risk management. | Anyone deciding what to implement; cited heavily by strategy_ea.md. |
| [literature_comparison.md](literature_comparison.md) | PAC components mapped to Wyckoff / Brooks / ICT / Carney / Elliott / Nison. | Anyone wanting external context or alternative names for PAC concepts. |
| [links.md](links.md) | 16 YouTube videos by Paweł — the source curriculum. | Anyone wanting to verify a rule's origin. |
| [chatdump_analysis/](chatdump_analysis/) | Phase 0 data-mining outputs from the Discord chatdump (15,231 messages). Grounds the inclusion + threshold decisions in strategy_ea.md. | EA implementer; the spec author. |

## Code subfolders (future)

| Folder | Status | Purpose |
|---|---|---|
| `mt5/` | not yet built | MQL5 EA + indicators (Phase 2). |
| `pine/` | not yet built | TradingView Pine Script indicators for visual prototyping (Phase 2). |

## Workflow

Plan and execution history lives in the parent scratch workspace at `C:\Users\nikof\Documents\GitHub\PAC\docs\superpowers\` — specs, plans, brainstorm artifacts. Eventually migrated here per the original design doc.

## Status

- Phase 0 — Chatdump cleanup + mining: **DONE** (merged into main).
- Phase 1a — Data-quality fixes + pipeline refresh: **DONE** (merged into main).
- Phase 1b — `strategy_ea.md` authoring: **DONE** (this branch's deliverable).
- Phase 2 — Implementation (MQL5 EA + Python ref impl + Pine): not started.
- Phase 3 — Triangulation: not started.
- Phase 4 — Strategy Tester campaign: not started.
- Phase 5 — Migration / public push to NFA: not started.
