# PropFirmMath

Quantification + backtest study of the **JJ Simon prop-firm method**, reverse-engineered
from two YouTube videos (v1 interview `aCOgfvL6lK8`; v2 his own explainer `3L8xdh3oPm4`,
"$1.2M in 12 months" — authoritative). The method is **two separable bets**:

- **Layer A — signal.** Fade Nasdaq (NQ/MNQ) 1-min back to the **09:30 ET open-candle**
  "fair price" on a close-confirmed **break-of-structure or displacement candle** (displacement
  = body bigger than prior, ~no wicks). Fixed **25 pt SL / 38 pt TP (1:1.5)**, sized by
  contract count (points held constant), ~20 trades/day across session opens (08:30/09:30/
  14:00/18:00/20:00 ET), hard **11:00 cutoff** on the morning block, no break-even/partials.
  Setups graded A+/A/B; only A+ has a stated win rate (~70–80%).
- **Layer B — wrapper (the "loophole").** Treat each cheap evaluation as a call-option on a
  $2–5k payout. Buy many, Kelly-sized; risk-of-ruin `(1 − p_pass·p_payout)^N`; grow a funded
  account to $10k balance → withdraw $5k → repeat; target ~3× eval spend. This is the real
  insight — but it is **worthless if Layer A's after-cost expectancy ≤ 0.**

**Status: SPEC'D, NOT YET TESTED.** Build not started. No metric claimed — JJ himself states
the live edge is only "1–5% and breaks even on live", so the whole system leans on prop-firm
leverage amplifying a razor-thin, cost-sensitive edge. **Gate 1 = does the 9:30-fade clear
40% WR after NQ costs?** is the make-or-break test (test A+-only vs the full blend).

- Quantified rules + EV math + falsifiers: [`QUANTIFY.md`](QUANTIFY.md)
- Phased TDD build plan with kill-gates: [`PLAN.md`](PLAN.md)
- Raw transcript extractions: [`EXTRACTION.md`](EXTRACTION.md) (v1), [`EXTRACTION_v2.md`](EXTRACTION_v2.md) (v2)
- Cross-chat working notes: [`NOTES.md`](NOTES.md)
- Validation: walk-forward IS/OOS per [`../../docs/strategy-validation.md`](../../docs/strategy-validation.md); audit trail in `reports/`. `VERDICT.md` written at the end.

**Related:** `../../../PropDDSim/` (sibling, non-git) is a prop-firm drawdown simulator that
likely overlaps Layer B (Phase 2/3) and should be reviewed for reuse before building the wrapper.

## Two remaining coding blockers (only ones left after v2)
1. Swing/structure detection threshold (pivot lookback `L`) — JJ never gives a bar count → sweep.
2. Displacement-candle size cutoff (`m`× prior body, wick ≤ `w`% of range) — qualitative → sweep.

## Next
Data-source decision (real NQ/MNQ futures 1-min vs MT5 NAS100 CFD proxy — cost fidelity
drives the verdict) → TDD `core/` → Phase 1 signal → **Gate 1**.
