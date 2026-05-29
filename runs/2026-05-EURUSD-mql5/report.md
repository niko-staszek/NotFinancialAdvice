# Plan 5 MQL5 EA — Strategy Tester Smoke

**EA:** `PAC_EA` (Plan 5, branch `plan-5-mql5-ea`)
**Terminal:** MetaQuotes-Demo, data dir `D0E8209F77C8CF37AD8BF550E51FF075`
**Symbol / TF:** EURUSD / M5
**Model:** 1 (1-minute OHLC)
**Compile pass:** indicator + EA + all 15 test scripts compiled **0 errors / 0 warnings**.

## Runs

| Range | Bars | Result | Trades | Final balance |
|---|---|---|---|---|
| 2024.05.01 → 2024.05.31 | 6,336 | Test passed in 1.9s | 0 | $10,000.00 |
| 2026.05.01 → 2026.05.15 | 2,880 | Test passed in 0.86s | 0 | $10,000.00 |

Both runs:
- `PAC_EA: initialized for EURUSD` — OnInit succeeded.
- MMD indicator loaded via `iCustom` (`PAC_MMD_Clouds.ex5`, 12,630 bytes).
- No runtime errors, no failed asserts, clean shutdown.
- Ledger written to the tester agent sandbox at
  `…/Tester/<id>/Agent-127.0.0.1-3000/MQL5/Files/PAC/ledger.csv`.

## Ledger schema verification

The produced `ledger.csv` (committed here, from the 2026-05 run) is **header-only,
221 bytes**, and the 21-column header is **byte-identical** to Plan 4's `ledger.py`
output:

```
trade_id,ts_signal,ts_open,ts_close,symbol,direction,entry_price,sl_price,tp_price,
exit_price,exit_reason,pnl_pips,pnl_money,r_multiple,setup_type,direction_strict,
mmd_alignment,d1_zone,confluence_type,lot_size,risk_pct
```

- Line ending: `\r\n` (CRLF) — matches Plan 4.
- No BOM — matches Plan 4.

This confirms `PAC_Logger.mqh` produces the triangulation-contract schema correctly.

## What this smoke proves (Task 21 goal)

✅ The EA compiles, loads its `iCustom` indicator, runs a full month of M5 bars in
the Strategy Tester without runtime errors, and emits a schema-correct ledger.

## What it does NOT yet prove (deferred to Phase 3)

⚠️ **0 trades vs Plan 4's 1 trade on the identical 2026-05-01→15 range.** This is the
first triangulation divergence and is expected — it has at least two well-understood
candidate causes that Phase 3 must reconcile on matched inputs:

1. **D1-zone computation differs.** Plan 4's committed smoke ran `run_backtest(d1_bars=None)`,
   so its §3.3 `d1_zone` was always `neutral` (permissive in the composite-direction
   rule). The MQL5 EA computes the *real* previous-day D1 promo zone via
   `iOpen/iHigh/iLow/iClose(PERIOD_D1, 1)`, which can gate out a trade that Plan 4
   took. Phase 3 should re-run Plan 4 *with* D1 bars supplied for apples-to-apples.
2. **Bar source differs.** The tester replays MetaQuotes-Demo broker history (Model 1,
   1-min OHLC sub-bar modeling); Plan 4 read a specific dumped CSV. Different
   broker/source bars shift swings, MMs, and signal candles.

Other parity factors flagged during implementation (for Phase 3): MMD midpoint
classification vs count heuristic (resolved in favour of Python), rolling 1500-bar
window vs full-series, EMA-from-iMA vs `ewm`, and slippage/fill model (≤2-pip
tolerance per the contract).

**Because the full trade lifecycle (entry → ledger data row → exit row) did not fire
in either smoke window, the data-row path of `PAC_Logger.mqh` / `Orders_Submit` /
closure logging is exercised only by the MQL5 unit tests, not yet by an end-to-end
ST trade.** Finding a trade-firing range (or aligning inputs with Plan 4) is the first
concrete Phase 3 task.
