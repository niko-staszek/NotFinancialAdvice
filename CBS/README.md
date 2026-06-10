# CBS — Measured-Move Reverse Analysis

CBS is a historical characterization tool for the PSND measured-move target. Instead of trading the
move forward, it reverse-analyzes M5 bar history to answer two questions:

**T1 — How long does the full move take to complete?**
For every instrument, CBS scans a 24×24 grid of anchor-hour × block-size windows (576 cells per
day per instrument). For each window `W`, the target is:

```
target = high(W) + low(W) − open(W)
```

CBS measures how many hours elapse from window close until price first touches within settle
tolerance of that target. Completion rates, median hours, and p25/p75 hours are reported per cell
across the full tolerance ladder (×1–4).

**T2 — What entry technique gives the best R into that move?**
For every completing, non-instant move, CBS evaluates 16 candidate entry detectors (structure,
liquidity/ICT, time/level, and baseline controls) and ranks them by median R-multiple
`R = (target − entry) / (entry − SL)`.

The output is two auditable tables — T1 and T2 — with full audit-trail proof for every reported
number.

---

## Locked definitions (summary)

- **Target:** `High(W) + Low(W) − Open(W)` over the window.
- **Window grid:** anchor ∈ {0..23} × block ∈ {1..24} = 576 cells per instrument per day.
- **Completion:** first M5 bar whose `[low, high]` range falls within settle tolerance of the
  target. Tolerance ladder: FX majors 5/10/15/20 pips; XAUUSD/XTIUSD 15/30/45/60 pips;
  BTCUSD $10/20/30/40; ETHUSD $5/10/15/20.
- **Clock:** starts at window close; capped at 48h. Never-completed → `completed=False, hours=NaN`.
  Moves already within tolerance at the first post-window bar → `instant=True`, reported separately.
- **Approach side:** if target is above window-close price the move is up (long opportunity);
  if below, down (short). Drives entry-side logic in all detectors.

Full locked spec: `docs/superpowers/specs/2026-06-09-cbs-measured-move-reverse-analysis-design.md`
PSND video links: `PSND/links.md`

---

## Getting data

Data is M5 bars exported from a running MT5 terminal. The fetch script is not yet committed under
`scripts/`; the canonical invocation once it exists will be:

```
python scripts/fetch_cbs_data.py --years 2
```

This writes files to `CBS/data/<SYMBOL>_M5_<YYYYMMDD>.csv` (large files — gitignored). The
canonical CSV schema is `time_utc, open, high, low, close, tick_volume, real_volume, spread`.

The CLI picks up the most-recently dated file per symbol automatically.

---

## Running the analysis

```
python -m CBS.cbs.cli --run <name> --utcstamp <UTCSTAMP> [options]
```

| Argument | Default | Notes |
|---|---|---|
| `--run` | `pilot` | Label for the run folder |
| `--utcstamp` | required | Arbitrary stamp string, e.g. `20260609T0000Z` |
| `--data` | `CBS/data` | Directory containing M5 CSV files |
| `--out` | `CBS/reports` | Output root; run folder created inside |
| `--instruments` | all 11 | Space-separated subset, e.g. `EURUSD XAUUSD` |
| `--anchors` | 0–23 | Subset of anchor hours to scan |
| `--blocks` | 1–24 | Subset of block sizes to scan |

**Pilot run (fast).** The full 24×24 grid across 11 instruments × 2 years of M5 data is heavy.
For a pilot, restrict the grid to a few representative cells:

```
python -m CBS.cbs.cli \
    --run pilot \
    --utcstamp 20260609T0000Z \
    --instruments EURUSD XAUUSD \
    --anchors 0 7 12 \
    --blocks 1 4 8 24
```

**Full run.**

```
python -m CBS.cbs.cli --run full --utcstamp 20260609T0000Z
```

---

## Reading the outputs

Each run writes to `CBS/reports/<run>-<utcstamp>/`:

| File | Contents |
|---|---|
| `timing_raw.csv` | One row per (symbol, date, anchor, block, tol_mult). Raw timing events. |
| `entries_raw.csv` | One row per (symbol, date, anchor, block, detector). Raw entry evaluations. |
| `t1_time_to_complete.csv` | Aggregated T1 table: completion and speed stats per cell. |
| `t2_best_entry.csv` | Aggregated T2 table: entry ranking per (symbol, detector). |
| `config.json` | Exact parameters used for this run (instruments, anchors, blocks, tolerances, ATR k). |
| `run.log` | Per-instrument load/skip log. |
| `manifest.sha256` | SHA-256 digest of every other file in the folder. |

**T1 columns:** `symbol, anchor, block, tol_mult, n, completion_rate, instant_rate, completed_n,
median_hours, p25_hours, p75_hours`.

- `n` — total windows in this cell (one per trading day in the dataset).
- `completion_rate` — fraction of windows where price touched within tolerance within 48h.
- `instant_rate` — fraction flagged instant (already settled at first post-window bar).
- `completed_n` — count used for hours stats (completed, non-instant moves only).
- `median_hours`, `p25_hours`, `p75_hours` — time-to-completion distribution over `completed_n`.

**T2 columns:** `symbol, name, n, median_r, win_rate, median_mae_r, median_lead_hours`.

- `name` — detector identifier (e.g. `ema21_retest`, `order_block`, `enter_at_window_close`).
- `n` — number of moves where this detector fired.
- `median_r` — median R-multiple `(target−entry)/(entry−SL)` across all fires.
- `win_rate` — fraction where target was reached before SL.
- `median_mae_r` — median maximum adverse excursion in R units (drawdown before entry works).
- `median_lead_hours` — how early in the move the entry typically fires.

---

## Audit

Every number in T1 and T2 traces back to a row in `timing_raw.csv` or `entries_raw.csv`. The
`manifest.sha256` covers all artifacts in the run folder; re-computing any table from the raw CSV
with the same config must reproduce the same result exactly (no wall-clock or random in the
pipeline).
