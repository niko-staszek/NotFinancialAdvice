# ORB US100 — full-period exit sweep + walk-forward bug correction (2026-06-22)

## Why this exists
The selection walk-forward (`reports/ORB-sl-20260622-103849Z/`) reported PF 0.97 / OOS
Sharpe −0.20 → "REJECTED". That verdict was **wrong** — a harness bug, not a result.

## The bug
`run_orb_walkforward.walk()` runs each OOS window as a **fresh** EA. The EA's RVOL filter
needs a 14-session warmup to fill its ring buffer, so **every 3-month OOS window is
trade-free for its first ~1 month** (confirmed: window 2024-01-01's first trade is
2024-02-01). ~30% of each OOS window is silently dropped. Plus per-window SL *selection*
(S0/S1/S2 by IS Sharpe) overfit — fixed structural S0 beats it.

## Correct method (fixed config → no parameter selection → a single continuous backtest
## IS a valid OOS test; warmup happens once)
Run the fixed spec default continuously 2021-10→2026-06, then filter to the OOS span
2022-10→2026-04. Configs: S0 opposite-end SL, RVOL ≥ 1.0; exit varied.

| config (OOS-filtered) | trades | win% | PF | Sharpe(t) | net$ | maxDD | long$ | short$ | gate |
|--|--|--|--|--|--|--|--|--|--|
| E0 (1:1)        | 255 | 53.3 | 1.14 | +1.04 | +1575 | −11.0% | +1906 | −331 | PASS |
| E3 (EMA8 runner)| 255 | 55.7 | 1.54 | +2.14 | +3630 | −6.3%  | +2940 | +691 | PASS |
| E1 (2R target)  | 255 | 44.3 | 1.15 | +0.99 | +2155 | −9.7%  | +3044 | −890 | PASS |

(Full-period, un-filtered, in `gate_fullperiod.txt`; OOS-filtered in `gate_oos_filtered.txt`.)

## Status: PROVISIONAL, not "edge"
- The **un-cherry-picked baseline** (E0) passes — this is not a tuned result.
- BUT US100 buy&hold was **+106%** over the period; bias-gated ORB is a bidirectional
  trend-follower → this may be trend **exposure**, not a distinct edge.
- E3's short side is positive (+691), which argues slightly against pure long exposure.
- `sharpe()` is a per-trade t-statistic, not annualized equity Sharpe.

## Next (decisive)
Cross-instrument (US500 / US30 / GER40, same fixed config, continuous + OOS-filter): a real
edge should generalize; pure US100-bull exposure will not. Then fix the WF warmup bug
(pre-roll each window) before any selection-based sweep is trusted.
