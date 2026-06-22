# SweepHunter

ICT session-liquidity model. At 09:00 ET mark the prior **Asia** (20:00–00:00 ET)
and **London** (02:00–05:00 ET) session highs/lows. During the NY AM hunt window
(09:00–11:30 ET) wait for one of those four levels to be **swept**, then drop to
M1 and enter a **fair-value-gap reversal** the other way. Stop at the sweep swing;
target either fixed **1:2 RR** or the next **draw on liquidity** (nearest un-swept
session level) — both modes carried and compared on identical entries.

- Engine: MQL5 EA, MT5 Strategy Tester (FTMO), `Period=M1`, real ticks.
- Spec: `docs/superpowers/specs/2026-06-22-sweephunter-design.md`
- Plan: `docs/superpowers/plans/2026-06-22-sweephunter.md`
- Validation: walk-forward IS/OOS + `tools/orb_gate.py` + cross-instrument table. See `VERDICT.md` (written at the end).
