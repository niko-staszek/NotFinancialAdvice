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

## Three sources → consolidated ruleset in `STRATEGY_RULES.md`
- **v1** interview (Titans of Tomorrow) → `EXTRACTION.md`. Paraphrase; some errors.
- **v2** JJ's OWN explainer "$1.2M/12mo" (`3L8xdh3oPm4`) → `EXTRACTION_v2.md`. Corrected v1:
  fair price **9:30**, **11:00 cutoff**, $1.2M/12mo, **live edge only "1–5%"**; defined BoS/displacement.
- **v3** FX Replay backtest (`SNO1wqJTq5A`) + their PDF deck → `EXTRACTION_v3_fxreplay.md`,
  `transcript/pdf_fairvalue_text.txt`, `transcript/pdf_page{2,3}.png`. **Most mechanical + first real
  WR data.** Defined: displacement = **counter-wick ≤20%** (size optional, FX Replay dropped it);
  **decisive + break must be SAME candle**; MSB(reversal) vs BOS(continuation); **ATR-bucketed SL/TP**
  (50/75, 25/37.5, 16.5/24.75; TP=37.5 not 38); fair value = **9:30 AND 2pm**; skip first 3min;
  follow-up trades (re-entries + 2nd-move) **excluded from their test** = trigger-3 tag.

## Decisions
- Treat as 2 separable bets — the loophole (B) is real math but worthless if (A)'s after-cost
  expectancy ≤ 0. → **Gate 1 = test Layer A first, cheapest kill.**
- Python TDD engine + `reports/<name>-<UTCstamp>/` audit trail; verify-before-reporting (no
  metric without a traced result file — per GoldCore fabrication incident).
- v1 drops the undefined 11:00–14:00 hold; models funded = same engine w/ varied R:R.

## State / done
- 2026-06-26 — **v1** transcript fetched+cleaned (16.5k w) → `transcript/`, `EXTRACTION.md`;
  QUANTIFY.md + PLAN.md (TDD, kill-gates) written.
- 2026-06-26 — **v2** reconciled into QUANTIFY/PLAN (fair price 9:30, 11:00 cutoff, triggers defined).
- 2026-06-26 — **v3 FX Replay** (backtest video + PDF deck) ingested → `EXTRACTION_v3_fxreplay.md`;
  wrote consolidated **`STRATEGY_RULES.md`** (now-mechanical Layer-A, all 3 sources); reconciled QUANTIFY.
  **First measured WR: 54% / 158 trades / 1.5R → +0.35R gross, IN-SAMPLE (verified vs transcript).**
- 2026-06-26 — **TradingView indicator** built: `pine/FairValueTheory.pine` (Pine v6) +
  spec `docs/superpowers/specs/2026-06-26-fairvalue-indicator-design.md`. Sessions/FV-lines/
  window-tints/pivot-BOS-MSB/decisive-candle(white)/A+(gold)/ATR-table + live recommendation.
  Grilled design. **COMPILE-VERIFIED clean (zero errors) + renders correctly on NQ 1-min** via
  TradingView MCP — table (ATR→bucket→SL/TP, active session, window, BOS/MSB), session labels,
  window tints, pivot BOS all confirmed live; proof `pine/verification-render.png`. (Launched the
  Store-app TV v3.2.0.7916 manually with --remote-debugging-port=9222 — MCP tv_launch had a stale
  hard-coded 3.0.0.7652 path; needed kill+relaunch to enable CDP.) Timings verified vs FX Replay;
  18:00 reopen (not 18:30). White/gold candle paint compiled but no qualifying bar in the snapshot.
- 2026-06-26 — Indicator **v2** (user feedback): BOS/MSB now drawn as **lines** at the broken
  level (not triangles); removed raw pivot plots (were confusing duplicate of S/R); **open/FV
  lines made prominent** + price label; **integrated S/R zones** by porting the user's SRv2
  (LonesomeTheBlue, MPL-2.0) v5→v6 + removed the standalone dup from chart. Caught+fixed a
  RUNTIME crash (compiled clean but red-!): v6 port of `find_loc` indexed an empty array — v5
  relied on an `na`-bound loop skipping; guarded with size check. Re-verified rendering live
  (proof `pine/verification-render.png`). Minor known nit: S/R right-edge labels overlap the
  top-right table (cosmetic; lower srLabelLoc or move table).
- 2026-06-26 — Indicator **polish**: table → **bottom-right** (configurable input; clears both the
  legend and S/R labels), added **Fair Value price row**, colored Window cell to match its tint,
  softened window tints. Re-verified render live; proof refreshed. Indicator considered DONE for v1.
- Also (prior, parallel sub-project): **EV-app design spec committed** (`docs/superpowers/specs/2026-06-26-propfirm-ev-app-design.md`,
  commit 1581157) — Streamlit+SQLite calculator+tracker; approved, **awaiting user spec review → writing-plans**.

## Rejected / dead ends
- v1's "11:00–14:00 longer hold" trade — v2 confirms it **does not exist** (11:00 = hard cutoff).
- Displacement SIZE threshold as a *required* gate — FX Replay dropped it ("too discretionary"),
  got 54% WR without it → size is **optional/unproven**, not required (test as toggle).

## Open threads / next
1. **Phase 0.1 — data source decision (NEEDS USER):** real NQ/MNQ futures 1-min vs MT5 NAS100 proxy.
   Cost fidelity drives the verdict; proxy spread ≠ futures.
2. TDD core/ → Phase 1 signal → **Gate 1, now sharper: reproduce ≥~54% gross, then SURVIVE COSTS + OOS**
   (FX Replay = in-sample, hand-picked windows, no costs). Costs are the killer for a 1.5R/25-pt scalp.
3. **Measure separately:** base vs +follow-ups (trigger-3); size-gate on/off (user's 1.2–1.5×avg idea).
4. Layer B's `(P_fail)^N` ignores account correlation → Phase 3.3 model ρ.

## Load-bearing gaps — RESOLVED by v3 (only fine-tuning left)
- Displacement = **counter-wick ≤20%** (was the big gap) ✓; size = optional toggle (user's m×avg). 
- Decisive + break **same candle** (new critical refinement). Swing-point still needs pivot `L` formalize.
- Remaining unknowns are now empirical not definitional: **costs, OOS, follow-ups, size-gate value.**
