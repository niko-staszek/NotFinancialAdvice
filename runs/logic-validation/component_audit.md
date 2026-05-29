# Component Correctness Audit (Track A)

Method: define (canonical PAC) → read (impl) → trace (hand-computed example) → verdict.
verdict ∈ {correct, suspect, wrong}; action ∈ {none, fix-code, amend-spec}.

| unit | verdict | evidence | action |
|---|---|---|---|
| atr | correct | hand Wilder ATR(3) on 8-bar series = 2.08025, compute_atr returned 2.08025 (full chain matches); confirmed Wilder recursion not simple mean (simple-roll would give 2.0), idx0/1 NaN seed=simple-avg, and prefix-of-6 ATR[5] == full ATR[5] proving no look-ahead. Bar-0 exclusion is a documented caller contract (fn takes only closed bars). | none |
| swing | correct | synthetic rise→drop≥thresh→rise (atr_period=3, mult=1.0): hand expected HIGH@bar6 price14.0 then LOW@bar8 price9.5; detect_swings returned exactly that. Swing-HIGH confirmed only after the ≥(ATR×mult) drop, pivot recorded at the true peak idx not the confirmation bar, swings alternate high/low. | none |
