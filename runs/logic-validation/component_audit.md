# Component Correctness Audit (Track A)

Method: define (canonical PAC) → read (impl) → trace (hand-computed example) → verdict.
verdict ∈ {correct, suspect, wrong}; action ∈ {none, fix-code, amend-spec}.

| unit | verdict | evidence | action |
|---|---|---|---|
| atr | correct | hand Wilder ATR(3) on 8-bar series = 2.08025, compute_atr returned 2.08025 (full chain matches); confirmed Wilder recursion not simple mean (simple-roll would give 2.0), idx0/1 NaN seed=simple-avg, and prefix-of-6 ATR[5] == full ATR[5] proving no look-ahead. Bar-0 exclusion is a documented caller contract (fn takes only closed bars). | none |
| swing | correct | synthetic rise→drop≥thresh→rise (atr_period=3, mult=1.0): hand expected HIGH@bar6 price14.0 then LOW@bar8 price9.5; detect_swings returned exactly that. Swing-HIGH confirmed only after the ≥(ATR×mult) drop, pivot recorded at the true peak idx not the confirmation bar, swings alternate high/low. | none |
| timeutil | correct | Ran real code: Jan-2026→+1 (PLT 13:00), Jul-2026→+2 (PLT 14:00). Spring-forward computed at last-Sun-Mar=29: 00:59 UTC→+1 (PLT 01:59), 01:00 UTC→+2 (PLT jumps 01:59→03:00) — matches §2.3 "02:00 CET→03:00 CEST". Fall-back at last-Sun-Oct=25 flips +2→+1 at 01:00 UTC (PLT 02:59→02:00). `_last_sunday` is calendar-derived: 2027 returns Mar-28/Oct-31, 2025 Mar-30 (not 2026's dates). All session labels match §2.3 incl. midnight-wrap Asia (02:00/23:00/07:00 PLT→asia), London 08:00/13:59, America 14:00/21:59, Dead 22:00/22:59. | none |
