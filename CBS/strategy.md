# CBS Strategy — Locked Methodology

**Status:** Locked (approved design). No edits without a new design document.
**Full spec:** `docs/superpowers/specs/2026-06-09-cbs-measured-move-reverse-analysis-design.md`
**Parent strategy:** PSND (`PSND/strategy.md`)

---

## §2 Definitions

### §2.1 Target formula

For measurement window `W`:

```
target = high(W) + low(W) − open(W)
```

`open(W)` = open of the first M5 bar in the window. `high(W)` / `low(W)` = extremes over all M5
bars in the window (wicks included). One target per window; direction-agnostic (PSND semantics).

### §2.2 Window grid

- **Anchor hour** `A ∈ {0, 1, …, 23}` — 24 values (broker/server time UTC).
- **Block size** `N ∈ {1, 2, …, 24}` hours — 24 values.
- Total: **576 windows** per instrument per day.
- Window span: `[A, A+N)` on the same UTC calendar day.

### §2.3 Completion within tolerance

Price has **touched within settle tolerance** of the target when an M5 bar's `[low, high]` range
comes within `tolerance_price` of the target:

```
|bar_extreme − target| ≤ tolerance_price
```

**Baseline tolerance and ladder:**

| Instrument | Baseline (×1) | ×2 | ×3 | ×4 |
|---|---|---|---|---|
| FX majors (6 pairs) | 5 pips | 10 | 15 | 20 |
| XAUUSD, XTIUSD | 15 pips | 30 | 45 | 60 |
| BTCUSD | $10 | $20 | $30 | $40 |
| ETHUSD | $5 | $10 | $15 | $20 |

T1 is computed at all four tiers. If completion rate jumps sharply when tolerance loosens, the
looser tier is flagged as the operative one for that instrument. T2 is computed at the operative
tolerance; the R trade-off (tighter tolerance → larger R headroom) is shown explicitly.

Pip sizes: FX 0.0001; USDJPY 0.01; XAUUSD 0.1; XTIUSD 0.01; BTC/ETH pip=1.0 (tolerance in $).

### §2.4 Completion clock

- Clock **starts** at window close: `anchor + block` hours past midnight UTC.
- Clock **cap:** 48 hours.
- No touch within 48h → `completed = False`, `hours_to_complete = NaN`.
- `hours_to_complete` = (timestamp of first touching M5 bar − window close) in hours, float.
- If the first post-window bar already touches → `instant = True`, `hours ≈ 0`. Instant moves are
  reported separately and excluded from speed statistics.

### §2.5 Approach side

At window close, `approach_side` is determined by comparing the target to the window-close price:

- `target > window_close_price` → approach side = **up** (long opportunity).
- `target < window_close_price` → approach side = **down** (short opportunity).

Approach side drives entry-side logic (which direction to enter, which extreme is invalidation).

---

## §4 Entry detectors

Runs on completing, non-instant moves only. Each detector is offered the M5 bar path from
`window_close` to `completion_ts` plus a look-back of `ENTRY_LOOKBACK_HOURS` (config, default 12h)
for structure. A detector fires by returning `(entry_price, invalidation_price, entry_time)` or
abstains (returns `None`).

**Invalidation / SL rule (all detectors):** each detector defines its own structural invalidation
(e.g. swing low beyond the retest for longs, far side of the FVG, beyond swept liquidity). If no
clean structural level is available, the fallback is `SL = entry ± k × ATR_M5` where `k =
ATR_SL_K` (config, default 1.5) and ATR is Wilder-style over `ATR_PERIOD_M5` (config, default 14)
M5 bars ending at entry time.

**R-multiple definition:**

```
R = (target − entry_price) / (entry_price − invalidation_price)   [sign-adjusted by side]
```

Spread at the entry bar is netted into entry price before computing R.

### Structure set

| Detector | Signal |
|---|---|
| `ema21_retest` | Price reclaims EMA21 (H1) then retests it from the correct side. PSND's own entry. |
| `swing_retest` | Break of a recent swing high/low, then retest of the broken level. |
| `sr_retest` | Retest of a prior horizontal S/R level: PDH, PDL, PWH, PWL. |
| `fvg_fill` | Entry on fill of a ≥20-pip H1/M5 imbalance in the move direction. |
| `fib_cluster` | Touch of a fib cluster zone (38.2/61.8/161.8 across multiple periods, PSND rules). |

### Liquidity / ICT set

| Detector | Signal |
|---|---|
| `order_block` | Tap of the last opposing candle before the impulse (ICT order block). |
| `liquidity_sweep` | Stop-run beyond PDH/PDL or local extreme, then reclaim. |
| `breaker` | Failed order block flipped to support/resistance (ICT breaker). |
| `eqh_eql_raid` | Raid of equal highs/equal lows then reversal. |

### Time / level set

| Detector | Signal |
|---|---|
| `session_open_retrace` | Retrace to the session open price after the move has started. |
| `prior_level_react` | Reaction off PDH/PDL/PWH (level-based; distinct from `sr_retest` trigger). |
| `opening_range_break` | Break + retest of the first-hour range. |
| `round_number` | Tap of the nearest round number in the path to target. |

### Baselines (control group)

Must be beaten to claim edge. Baseline detectors always fire (never abstain) on a completing move.

| Detector | Signal |
|---|---|
| `enter_at_window_close` | Naive: enter at window-close price. |
| `first_pullback_pct` | Enter after price pulls back a fixed % of the distance toward start. |
| `first_m5_close` | Enter on first M5 close in the move direction after window close. |

---

## §5 Outputs

### T1 — Time-to-complete

Aggregated per `(symbol, anchor, block, tol_mult)`:

| Column | Description |
|---|---|
| `n` | Total windows (one per trading day) |
| `completion_rate` | Fraction completed within 48h and tolerance |
| `instant_rate` | Fraction flagged instant |
| `completed_n` | Count for hours stats (completed, non-instant only) |
| `median_hours` | Median time-to-completion over `completed_n` |
| `p25_hours` | 25th percentile hours |
| `p75_hours` | 75th percentile hours |

### T2 — Best entry

Aggregated per `(symbol, name)`:

| Column | Description |
|---|---|
| `n` | Number of moves where detector fired |
| `median_r` | Median R-multiple (target−entry)/(entry−SL) |
| `win_rate` | Fraction where target reached before SL hit |
| `median_mae_r` | Median max adverse excursion in R units |
| `median_lead_hours` | Median hours before completion that the entry fired |

Detectors are ranked by `median_r` descending per symbol. A detector beats the baselines only if
its `median_r` and `win_rate` exceed all three baseline values on the same instrument.

### Audit trail

Every run folder (`CBS/reports/<run>-<utcstamp>/`) contains:
- `timing_raw.csv`, `entries_raw.csv` — raw events underlying T1 and T2.
- `t1_time_to_complete.csv`, `t2_best_entry.csv` — aggregated tables.
- `config.json` — exact parameters (instruments, anchors, blocks, tol_mults, cap_hours, atr_k, atr_period).
- `run.log` — per-instrument load/skip log.
- `manifest.sha256` — SHA-256 over all other artifacts.

No metric is reported unless it traces to a row in the raw CSVs in the same run folder.
