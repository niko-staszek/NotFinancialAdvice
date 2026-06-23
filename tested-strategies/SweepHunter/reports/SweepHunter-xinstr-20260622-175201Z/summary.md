# SweepHunter — cross-instrument walk-forward (quick pass)

**Stamp:** 20260622-175201Z
**Method:** walk-forward, IS 12mo / OOS 3mo / slide 3mo, span 2023.01.01–2026.06.01. Per window, the best-IS-Sharpe candidate among {rr, dol, rr_combined, dol_combined} is run blind on OOS; OOS segments stitched; `tools/orb_gate.py` applied.
**Model:** `Period=M1`, real ticks; metrics net of spread + commission + swap (EA `net_pnl`).

## Results (all numbers from each symbol's `gate.txt` + `oos_stitched.csv`, this stamp)

| Instrument | OOS n | win% | net ($/10k) | PF | OOS Sharpe | IS Sharpe(avg) | maxDD | concentration | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| XAUUSD | 438 | 28.5 | −6619 | 0.78 | −1.94 | −0.99 | −86.6% | — | 🔴 FAIL |
| EURUSD | 439 | 36.2 | +3087 | 1.10 | 0.72 | −0.03 | −20.7% | 57% | 🔴 FAIL |
| US100.cash | 488 | 30.1 | −918 | 0.97 | −0.19 | −0.65 | −42.2% | 228% | 🔴 FAIL |

Sources:
- `SweepHunter-wf-XAUUSD-20260622-175201Z/gate.txt`
- `SweepHunter-wf-EURUSD-20260622-175201Z/gate.txt`
- `SweepHunter-wf-US100.cash-20260622-175201Z/gate.txt`

## Per-window candidate selection (which variant won IS)

| Instrument | dol | dol_combined | rr_combined | rr |
|---|---:|---:|---:|---:|
| XAUUSD | 2 | 3 | 4 | 0 |
| EURUSD | 2 | 6 | 1 | 0 |
| US100.cash | 0 | 9 | 0 | 0 |

The draw-on-liquidity targets (`dol` / `dol_combined`) — the preferred exit — won most windows, so DOL is *not* the bottleneck; the entry edge itself is absent.

## Gate failures (per `orb_gate.py`)
- **XAUUSD:** OOS Sharpe −1.94 < 0.5; maxDD −86.6% worse than −30%. Loses in-sample too (IS −0.99).
- **EURUSD:** profit concentration 57% > 30% (one trade carries the net); IS Sharpe −0.03 → the +OOS is variance, not edge.
- **US100.cash:** OOS Sharpe −0.19 < 0.5; maxDD −42.2% worse than −30%; concentration 228% (net is negative, so a single winner exceeds |net|). IS −0.65.

## Buy-and-hold sanity
Over 2023–2026 XAUUSD and US100 both trended strongly upward; SweepHunter *lost* on both (−66% on XAUUSD/10k, negative on US100). It does not even capture exposure — it underperforms doing nothing. Not a Tesla-trap false-positive; an outright loser.

## Decision
3/3 instruments fail, **negative in-sample Sharpe on all three** → no edge to overfit, let alone generalize. Quick pass is decisive; the full 9-instrument sweep was not run (would not change the verdict). See `../../VERDICT.md`.
