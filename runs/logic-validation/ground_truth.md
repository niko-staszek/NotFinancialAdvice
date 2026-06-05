# Track B — Behavioral Sanity Look (NON-GATING)

> **Status: exploratory, no pass/fail authority.** After a devil's-advocate review, the
> original Track B goal ("verify the engine fires where documented human traders fired")
> was found to be **unachievable as a correctness validator**, and its pass criterion was
> **removed from the LV15 merge gate**. Logic correctness for this phase rests entirely on
> **Track A** (the 14-unit component audit + the 6 reviewed Python fixes) and the
> **Python ↔ MQL5 parity re-port**. This document records what the Strategy-Tester runs
> actually showed, and why they cannot validate correctness.

## Why Track B cannot validate correctness (devil's-advocate findings)

1. **The ground truth is fabricated.** The pointer set is sourced from a Discord chat
   catalog whose numeric `entry`/`sl`/`tps` fields are extraction artifacts — e.g. the
   C.1 row's `entry` was parsed as `7` from a `prnt.sc/7fvE…` URL fragment, not a price.
   There is no real numeric fire-point to match the engine against.
2. **The one strong case is self-admittedly assumed.** `strategy_ea.md` Appendix C.1
   states its `entry≈2466 / sl≈2472 / tp≈2451` were *resolved from the linked chart image*
   and lists nearly every §7.5 gate value as "unknown." You cannot verify a fire against
   inputs the spec itself confesses it invented.
3. **The match window is operator-chosen.** The EA needs ~1490 M5 bars of warm-up *inside*
   the test window (see mechanism below), so windows must be long and are sized by us — any
   "hit" is a tuned degree of freedom, not a prediction.
4. **Three mismatched bar sources.** The Strategy Tester replays MetaQuotes-Demo bars; the
   mentor traded a different broker/chart; the Python reference engine reads yet another
   dumped CSV. Different bars → different swings / measured-moves / signal-candles, so both
   a "hit" and a "miss" are noise.
5. **n = 1 checkable positive.** Of the pointer set, exactly one 2024 mentor case (C.1) is
   runnable; the other mentor case (C.2 EURUSD) is unrunnable (broker history floor); the
   2025 mentor post (M1) is retrospective; the five student posts have `expect_fire=unknown`
   (no expectation). "Majority of checkable `expect_fire=yes`" over n=1 is a coin flip.
6. **Scope excludes what would make a pass meaningful.** Logic Validation explicitly does
   not test profitability nor whether the spec captures the real strategy — so even a clean
   Track B pass would certify only "the EA emits a trade near a timestamp we chose, on bars
   we chose, against prices we made up."

**Verdict:** kill Track B as a behavioral validator → downgraded to this non-gating note.

## What the Strategy-Tester runs DID establish (the honest, narrow claim)

The runs are still useful as an end-to-end integration sanity check on the production EA
against real broker history:

- **The EA runs end-to-end on real history, fires plausible PAC setups, and writes a
  schema-correct ledger.** The C.1 long window (XAUUSD M5, `2024.07.01 → 2024.08.20`,
  9907 bars, "Test passed") produced two trades:

  | ts_signal (UTC) | dir | entry | sl | tp | exit | setup | mmd | result |
  |---|---|---|---|---|---|---|---|---|
  | 2024-08-07T17:35 | BUY | 2402.68 | 2400.51 | 2406.58 | sl_hit | none | weakened | −1.00R |
  | 2024-08-19T16:10 | SELL | 2490.16 | 2492.29 | 2479.12 | sl_hit | trap | weakened | −1.00R |

  (Both losers — but Track B never judged profitability; the point is the entry→ledger→exit
  lifecycle fires and logs correctly on real bars, which the prior Strategy-Tester smoke
  (Task 21) had not yet exercised with an actual trade.)

- **The C.1 mentor SELL (2024-08-14T17:03) produced NO trade at that bar.** This is an
  expected non-match, not a defect: the mentor's entry depended on chart-image levels and
  discretionary reads the EA's deterministic gates cannot see, the catalog has no real
  numeric entry for it, and the broker bars differ. The EA did fire a SELL nearby (Aug-19),
  consistent with the same regime, just not at the discretionary bar.

## Strategy-Tester mechanism finding (worth carrying to Phase 3)

The cause of the "EA loads but nothing triggers" symptom on short windows:

- **Warm-up must accrue inside the test window.** The MT5 Strategy Tester does **not** feed
  the EA pre-`FromDate` history through its `CopyClosedBars`/bar-window path, so the EA's
  1490-bar signal warm-up (max(SmaPeriod, MMD-1440) + 50) is only satisfied after ~1490 M5
  bars have elapsed *within* the test window. Short windows (a few days) → 0 trades; long
  windows (`FromDate` pushed back ≥ ~25–30 calendar days before the region of interest) →
  the EA evaluates and trades. This differs from the Python engine, which consumes the
  first 1490 bars of the *provided CSV* as warm-up. **Parity-relevant for Phase 3.**

- **History availability differs by access path** (also Phase-3 relevant): the MT5 Strategy
  Tester has XAUUSD M5 history back to ~2023 and EURUSD back to 2025-01, whereas the live
  Python `MetaTrader5.copy_rates_range` attach only returns XAUUSD from 2024-12-24 / EURUSD
  from 2025-01-23 on this broker. The 2024 Appendix-C examples are therefore runnable only
  via the Strategy Tester, not via the Python `dump-bars` path.

## Pointer set

See `ground_truth_pointers.csv`. C.1 (XAUUSD SELL 2024-08-14) is the only runnable
documented-mentor positive; it is a non-match for the reasons above. C.2 (EURUSD 2024-08)
is unrunnable (EURUSD Strategy-Tester history floors at 2025-01). The 2025 mentor (M1) and
five student anchors carry no verifiable numeric ground truth.

## Bearing on the merge

Track B is **informational only**. The LV15 merge gate is: Track A audit complete (every
unit `correct` or `accepted-deviation`); the 6 Python correctness fixes reviewed
spec-compliant; the MQL5 parity re-port landed and compiling 0/0; the full Python suite
green; indicator + EA + MQL5 test scripts compiling 0 errors / 0 warnings.
