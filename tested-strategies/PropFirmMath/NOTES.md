# PropFirmMath

## Goal
Quantify + backtest the JJ Simon prop-firm method (YouTube `aCOgfvL6lK8`, Titans of
Tomorrow, claims $1.5M payouts/18mo). "Done" = a VERDICT traced to `reports/` files:
is there a real after-cost edge, or is it survivorship + course-selling? Pipeline so far:
transcribe → quantify → plan. **Build not started.**

## The method in one line
TWO layers: **(A) signal** = fade NQ 1-min back to the **09:30 ET open-candle** "fair price"
on a close-confirmed **BoS or displacement candle**, fixed **25pt SL / 38pt TP (1:1.5)**,
sizing via contract count, ~20 trades/day, no BE/partials; **(B) wrapper** = buy many cheap
evals as call-options on $2k–5k payouts, Kelly-sized, RoR=(1−p_pass·p_payout)^N, grow funded
to $10k → withdraw $5k → repeat, target 3x eval spend. The "genius" is Layer B.

## Two source videos
- **v1** interview (Titans of Tomorrow) → `EXTRACTION.md`. Paraphrase; some errors.
- **v2** JJ's OWN explainer "$1.2M/12mo" (`3L8xdh3oPm4`) → `EXTRACTION_v2.md`. **Authoritative.**
  Corrected v1: fair price **9:30** (not 9:29); **11:00 = cutoff** (no "longer hold"); $1.2M/12mo
  (not $1.5M/18mo); **live edge only "1–5%", breaks even live**. Defined BoS/displacement, exact
  25/38 1:1.5, contract sizing, A+/A/B grading, A+ WR ≈70–80%, session clock, his own backtest recipe.

## Decisions
- Treat as 2 separable bets — the loophole (B) is real math but worthless if (A)'s after-cost
  expectancy ≤ 0. → **Gate 1 = test Layer A first, cheapest kill.**
- Python TDD engine + `reports/<name>-<UTCstamp>/` audit trail; verify-before-reporting (no
  metric without a traced result file — per GoldCore fabrication incident).
- v1 drops the undefined 11:00–14:00 hold; models funded = same engine w/ varied R:R.

## State / done
- 2026-06-26 — **v1** transcript fetched+cleaned (16.5k w) → `transcript/`, `EXTRACTION.md`;
  QUANTIFY.md + PLAN.md (TDD, kill-gates) written.
- 2026-06-26 — **v2** (JJ's own explainer `3L8xdh3oPm4`, 7.4k w) fetched+cleaned →
  `EXTRACTION_v2.md`; reconciled into QUANTIFY.md (v2 RECONCILIATION block + patched §A2/A4/A5/A6/A7
  + param table) and PLAN.md. Signal now **~80% codable** (triggers defined).

## Rejected / dead ends
- v1's "11:00–14:00 longer hold" trade — v2 confirms it **does not exist** (11:00 = hard cutoff).

## Open threads / next
1. **Phase 0.1 — data source decision (NEEDS USER):** real NQ/MNQ futures 1-min vs MT5
   NAS100 CFD proxy. Cost fidelity drives the whole verdict; proxy spread ≠ futures.
2. TDD core/ (sessions + **9:30** fair price + 11:00 cutoff, structure=BoS+displacement, costs)
   → Phase 1 signal → **Gate 1**. Test all-setups vs **A+-only** (v2: A+≈70–80%, blend unknown).
3. **Biggest analytical risk to test:** Layer B's `(P_fail)^N` assumes independent accounts,
   but 40 accounts on same NQ signal same day are correlated → real RoR ≫ stated. Phase 3.3 → ρ.

## Load-bearing gaps — 2 left after v2 (must sweep — see QUANTIFY §A4)
- Swing/structure detection threshold (pivot lookback `L`) — JJ never gives bar count.
- Displacement-candle cutoff (`m`× body, `w`% wick) — JJ qualitative ("bigger + no wicks").
- (Resolved by v2: fair price, direction, triggers, R:R, sizing, sessions. WR A+≈70–80%; A/B still measure.)
