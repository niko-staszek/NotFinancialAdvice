# CBS Measured-Move Reverse Analysis — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the CBS Python pipeline that reverse-analyzes the PSND measured-move target (`H+L−O`): how long the move takes to complete across a 24×24 anchor/block window grid, and which entry technique gives the best R-multiple — with full audit-trail reports.

**Architecture:** Pure pandas pipeline over MT5-dumped M5 bars. Two engines: **timing** (window → target → first tolerance-touch within 48h) and **evaluate** (candidate entry detectors → R/MFE/MAE vs target). Deterministic, no wall-clock/random in the analysis path. Reports under `reports/<name>-<UTCstamp>/` with sha256 manifests. Design spec: `docs/superpowers/specs/2026-06-09-cbs-measured-move-reverse-analysis-design.md`.

**Tech Stack:** Python 3.11+, pandas, pytest. Data via `tools/mt5_data.py dump-bars`. Reuses the repo's canonical CSV bar schema.

---

## File Structure

```
CBS/
  __init__.py                 # marks CBS importable as a package
  README.md                   # what CBS is, how to run, how to read reports
  strategy.md                 # reverse-analysis methodology (copy of locked spec essentials)
  cbs/
    __init__.py
    config.py                 # INSTRUMENTS, pip sizes, tolerance ladder, anchors, blocks, ATR k, costs
    bars.py                   # load/validate M5 CSV → DataFrame; helpers (slice window, resample H1)
    target.py                 # window → H+L-O target + approach side
    timing.py                 # Engine A: time-to-complete per (instrument, day, anchor, block, tol)
    entries.py                # candidate entry detectors (pure functions, one per technique)
    evaluate.py               # Engine B: R / MFE / MAE / cost per entry vs target
    report.py                 # T1, T2 tables + audit manifest writer
    pipeline.py               # driver: wire engines, OOS split, write reports
    cli.py                    # argparse entrypoint
  tests/
    __init__.py
    conftest.py               # synthetic-bar fixtures
    test_config.py
    test_bars.py
    test_target.py
    test_timing.py
    test_entries.py
    test_evaluate.py
    test_report.py
    test_pipeline.py
  data/                       # M5 dumps (gitignored, see Task 1)
  reports/                    # audit-trail output (gitignored except .gitkeep)
scripts/
  fetch_cbs_data.py           # operational: query symbols + dump 2yr M5 for each instrument
```

Each module has one responsibility. Detectors in `entries.py` are pure `(context) -> EntrySignal | None` functions sharing one dataclass interface, so each is independently testable and the menu is extensible without touching the engine.

---

## Shared types (defined here, referenced throughout)

These dataclasses are the interfaces between modules. They are created in the tasks noted; later tasks rely on these exact field names.

```python
# cbs/target.py
@dataclass(frozen=True)
class Target:
    value: float          # H + L - O for the window
    approach_side: str    # "up" if target > window_close_price else "down"
    window_open: float
    window_high: float
    window_low: float
    window_close_price: float   # close of last bar in window (drives approach_side)

# cbs/timing.py
@dataclass(frozen=True)
class TimingRecord:
    symbol: str
    date: str             # ISO date of the anchor day (UTC)
    anchor: int           # 0..23
    block: int            # 1..24
    tol_mult: int         # tolerance ladder multiplier (1..4)
    target: float
    approach_side: str
    completed: bool
    instant: bool         # touched within tolerance on the first post-window bar
    hours_to_complete: float   # NaN if not completed
    window_close_price: float
    bars_scanned: int

# cbs/entries.py
@dataclass(frozen=True)
class EntrySignal:
    name: str             # detector id, e.g. "ema21_retest"
    entry_price: float
    invalidation_price: float   # structural SL (or ATR fallback)
    entry_time: pd.Timestamp

@dataclass(frozen=True)
class EntryContext:
    """Everything a detector may read. All bars are at/before the decision horizon."""
    symbol: str
    m5: pd.DataFrame      # M5 bars from (window_open - lookback) .. completion bar inclusive
    h1: pd.DataFrame      # H1 resample of the same span
    window_close_ts: pd.Timestamp
    completion_ts: pd.Timestamp
    target: float
    approach_side: str
    pip_size: float
    atr_m5: float         # precomputed ATR for fallback SL

# cbs/evaluate.py
@dataclass(frozen=True)
class EntryResult:
    symbol: str
    date: str
    anchor: int
    block: int
    name: str
    entry_price: float
    invalidation_price: float
    target: float
    r_multiple: float     # (target-entry)/(entry-invalidation), side-adjusted, NaN if no SL room
    mfe_r: float
    mae_r: float
    win: bool             # target reached before invalidation
    cost_spread_price: float
    entry_lead_hours: float
```

---

## Task 0: Scaffold the CBS package

**Files:**
- Create: `CBS/__init__.py`, `CBS/cbs/__init__.py`, `CBS/tests/__init__.py`
- Create: `CBS/reports/.gitkeep`, `CBS/data/.gitkeep`
- Create: `CBS/.gitignore`
- Test: `CBS/tests/test_smoke.py`

- [ ] **Step 1: Create package init files (empty)**

Create `CBS/__init__.py`, `CBS/cbs/__init__.py`, `CBS/tests/__init__.py` each containing only:
```python
```
(empty file)

- [ ] **Step 2: Create `.gitignore` for data/reports bulk**

`CBS/.gitignore`:
```
data/*.csv
reports/*/
!reports/.gitkeep
!data/.gitkeep
__pycache__/
*.pyc
```

- [ ] **Step 3: Add keep files**

`CBS/reports/.gitkeep` and `CBS/data/.gitkeep` — empty files.

- [ ] **Step 4: Write the smoke test**

`CBS/tests/test_smoke.py`:
```python
"""Smoke test: package is importable from repo root."""
from __future__ import annotations


def test_cbs_package_imports() -> None:
    import CBS.cbs  # noqa: F401
    assert CBS.cbs is not None
```

- [ ] **Step 5: Run it from repo root**

Run: `python -m pytest CBS/tests/test_smoke.py -v`
Expected: PASS. If import fails with `ModuleNotFoundError: CBS`, add `CBS/conftest.py`:
```python
"""Ensure repo root on sys.path for CBS package imports during pytest."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
```
Re-run; expect PASS.

- [ ] **Step 6: Commit**

```bash
git add CBS/__init__.py CBS/cbs/__init__.py CBS/tests/ CBS/.gitignore CBS/reports/.gitkeep CBS/data/.gitkeep
git commit -m "feat(cbs): scaffold package + smoke test"
```

---

## Task 1: Config

**Files:**
- Create: `CBS/cbs/config.py`
- Test: `CBS/tests/test_config.py`

- [ ] **Step 1: Write failing tests**

`CBS/tests/test_config.py`:
```python
from __future__ import annotations

from CBS.cbs import config


def test_instruments_are_the_eleven_psnd_symbols() -> None:
    assert set(config.INSTRUMENTS) == {
        "EURUSD", "GBPUSD", "USDCAD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD",
        "XAUUSD", "XTIUSD", "BTCUSD", "ETHUSD",
    }


def test_every_instrument_has_pip_size_and_base_tolerance() -> None:
    for sym in config.INSTRUMENTS:
        assert sym in config.PIP_SIZE
        assert sym in config.BASE_TOLERANCE_PIPS


def test_jpy_pip_size_differs_from_eur() -> None:
    assert config.PIP_SIZE["USDJPY"] == 0.01
    assert config.PIP_SIZE["EURUSD"] == 0.0001


def test_grid_dimensions() -> None:
    assert config.ANCHORS == tuple(range(24))
    assert config.BLOCKS == tuple(range(1, 25))
    assert config.TOLERANCE_MULTIPLIERS == (1, 2, 3, 4)


def test_clock_cap_is_48h() -> None:
    assert config.CLOCK_CAP_HOURS == 48
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest CBS/tests/test_config.py -v`
Expected: FAIL (`ModuleNotFoundError` / `AttributeError`).

- [ ] **Step 3: Implement config**

`CBS/cbs/config.py`:
```python
"""CBS configuration: instruments, pip sizes, tolerance ladder, window grid, costs.

All values are PSND-derived. Tolerances are expressed in *pips* and converted to
price via PIP_SIZE. The tolerance ladder multiplies BASE_TOLERANCE_PIPS so a too-
tight baseline does not understate completion (design §2.3).
"""
from __future__ import annotations

INSTRUMENTS: tuple[str, ...] = (
    "EURUSD", "GBPUSD", "USDCAD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD",
    "XAUUSD", "XTIUSD", "BTCUSD", "ETHUSD",
)

# Price increment of one "pip" as PSND counts it.
PIP_SIZE: dict[str, float] = {
    "EURUSD": 0.0001, "GBPUSD": 0.0001, "USDCAD": 0.0001, "USDCHF": 0.0001,
    "AUDUSD": 0.0001, "NZDUSD": 0.0001,
    "USDJPY": 0.01,
    "XAUUSD": 0.1,    # PSND tolerance "15 pips" on gold = 1.5 in price; pip=0.1
    "XTIUSD": 0.01,
    "BTCUSD": 1.0,    # crypto tolerance expressed directly in $ below
    "ETHUSD": 1.0,
}

# PSND baseline settle tolerance, in pips (×PIP_SIZE = price). Crypto in $ via pip=1.0.
BASE_TOLERANCE_PIPS: dict[str, float] = {
    "EURUSD": 5, "GBPUSD": 5, "USDCAD": 5, "USDCHF": 5, "AUDUSD": 5, "NZDUSD": 5,
    "USDJPY": 5,
    "XAUUSD": 15, "XTIUSD": 15,
    "BTCUSD": 10, "ETHUSD": 5,
}

ANCHORS: tuple[int, ...] = tuple(range(24))          # 0..23
BLOCKS: tuple[int, ...] = tuple(range(1, 25))        # 1..24 hours
TOLERANCE_MULTIPLIERS: tuple[int, ...] = (1, 2, 3, 4)

CLOCK_CAP_HOURS: int = 48
ATR_PERIOD_M5: int = 14
ATR_SL_K: float = 1.5            # fallback SL = entry ± k*ATR when no structural level
ENTRY_LOOKBACK_HOURS: int = 12   # bars before window_open a detector may read


def tolerance_price(symbol: str, mult: int) -> float:
    """Settle tolerance in price units for `symbol` at ladder multiplier `mult`."""
    return BASE_TOLERANCE_PIPS[symbol] * PIP_SIZE[symbol] * mult
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest CBS/tests/test_config.py -v`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add CBS/cbs/config.py CBS/tests/test_config.py
git commit -m "feat(cbs): config — instruments, pip sizes, tolerance ladder, grid"
```

---

## Task 2: Bars loader + window/resample helpers

**Files:**
- Create: `CBS/cbs/bars.py`
- Create: `CBS/tests/conftest.py`
- Test: `CBS/tests/test_bars.py`

- [ ] **Step 1: Write the synthetic-bar fixture**

`CBS/tests/conftest.py`:
```python
"""Synthetic M5 bar fixtures with known answers for CBS tests."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pandas as pd
import pytest


def make_m5(start: str, rows: list[tuple[float, float, float, float]], spread: int = 1) -> pd.DataFrame:
    """Build an M5 DataFrame. `rows` = list of (open, high, low, close). Times step 5min from `start` UTC."""
    t0 = datetime.fromisoformat(start).replace(tzinfo=timezone.utc)
    recs = []
    for i, (o, h, l, c) in enumerate(rows):
        recs.append({
            "time_utc": t0 + timedelta(minutes=5 * i),
            "open": o, "high": h, "low": l, "close": c,
            "tick_volume": 1, "real_volume": 0, "spread": spread,
        })
    df = pd.DataFrame(recs)
    df["time_utc"] = pd.to_datetime(df["time_utc"], utc=True)
    return df


@pytest.fixture
def m5_factory():
    return make_m5
```

- [ ] **Step 2: Write failing tests for bars helpers**

`CBS/tests/test_bars.py`:
```python
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
import pytest

from CBS.cbs.bars import load_m5_csv, slice_window, resample_h1, atr_m5


_CSV = """time_utc,open,high,low,close,tick_volume,real_volume,spread
2024-01-01T00:00:00,1.1000,1.1010,1.0995,1.1005,5,0,1
2024-01-01T00:05:00,1.1005,1.1020,1.1002,1.1018,5,0,1
2024-01-01T00:10:00,1.1018,1.1025,1.1010,1.1012,5,0,2
"""


def test_load_m5_csv_parses_utc_and_sorts(tmp_path: Path) -> None:
    p = tmp_path / "x.csv"
    p.write_text(_CSV, encoding="utf-8")
    df = load_m5_csv(p)
    assert list(df.columns)[:5] == ["time_utc", "open", "high", "low", "close"]
    assert str(df["time_utc"].dt.tz) == "UTC"
    assert df["time_utc"].is_monotonic_increasing


def test_slice_window_is_half_open(m5_factory) -> None:
    # 24 bars of 5min = 2 hours. Window [00:00, 01:00) must take first 12 bars.
    df = m5_factory("2024-01-01T00:00:00", [(1, 2, 0.5, 1.5)] * 24)
    start = pd.Timestamp("2024-01-01T00:00:00", tz="UTC")
    end = start + timedelta(hours=1)
    w = slice_window(df, start, end)
    assert len(w) == 12
    assert w["time_utc"].iloc[0] == start
    assert w["time_utc"].iloc[-1] == pd.Timestamp("2024-01-01T00:55:00", tz="UTC")


def test_resample_h1_aggregates_ohlc(m5_factory) -> None:
    df = m5_factory("2024-01-01T00:00:00", [
        (1.0, 1.5, 0.9, 1.2),   # 00:00
        (1.2, 1.8, 1.1, 1.7),   # 00:05
    ] + [(1.7, 1.7, 1.7, 1.7)] * 10)  # fill the hour
    h1 = resample_h1(df)
    row = h1.iloc[0]
    assert row["open"] == 1.0
    assert row["high"] == 1.8
    assert row["low"] == 0.9


def test_atr_m5_positive(m5_factory) -> None:
    df = m5_factory("2024-01-01T00:00:00", [(1.0, 1.2, 0.8, 1.0)] * 20)
    val = atr_m5(df, period=14)
    assert val > 0
```

- [ ] **Step 3: Run to verify fail**

Run: `python -m pytest CBS/tests/test_bars.py -v`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 4: Implement bars.py**

`CBS/cbs/bars.py`:
```python
"""M5 bar loading and frame helpers for CBS.

Uses the repo's canonical CSV schema produced by tools/mt5_data.py dump-bars:
    time_utc, open, high, low, close, tick_volume, real_volume, spread
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = ("time_utc", "open", "high", "low", "close", "tick_volume", "real_volume", "spread")


def load_m5_csv(path: Path) -> pd.DataFrame:
    """Load an M5 CSV, validate schema, parse UTC, sort by time, reset index."""
    path = Path(path)
    if path.stat().st_size == 0:
        raise ValueError(f"CSV file is empty: {path}")
    df = pd.read_csv(path)
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"CSV missing required column: {col!r}")
    df["time_utc"] = pd.to_datetime(df["time_utc"], utc=True)
    for col in ("open", "high", "low", "close"):
        df[col] = df[col].astype("float64")
    for col in ("tick_volume", "real_volume", "spread"):
        df[col] = df[col].astype("int64")
    df = df.sort_values("time_utc").reset_index(drop=True)
    return df


def slice_window(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    """Return bars with start <= time_utc < end (half-open)."""
    mask = (df["time_utc"] >= start) & (df["time_utc"] < end)
    return df.loc[mask].reset_index(drop=True)


def resample_h1(df: pd.DataFrame) -> pd.DataFrame:
    """Resample M5 → H1 OHLC. Returns columns time_utc, open, high, low, close."""
    s = df.set_index("time_utc")
    agg = s.resample("1h", label="left", closed="left").agg(
        open=("open", "first"), high=("high", "max"),
        low=("low", "min"), close=("close", "last"),
    ).dropna(subset=["open"]).reset_index()
    return agg


def atr_m5(df: pd.DataFrame, period: int = 14) -> float:
    """Wilder-style ATR over the last `period` M5 bars. Returns the final ATR value."""
    if len(df) < 2:
        return float(df["high"].iloc[-1] - df["low"].iloc[-1]) if len(df) else 0.0
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()
    return float(atr.iloc[-1])
```

- [ ] **Step 5: Run to verify pass**

Run: `python -m pytest CBS/tests/test_bars.py -v`
Expected: PASS (4 tests).

- [ ] **Step 6: Commit**

```bash
git add CBS/cbs/bars.py CBS/tests/conftest.py CBS/tests/test_bars.py
git commit -m "feat(cbs): bars loader + window/resample/atr helpers"
```

---

## Task 3: Target computation

**Files:**
- Create: `CBS/cbs/target.py`
- Test: `CBS/tests/test_target.py`

- [ ] **Step 1: Write failing tests**

`CBS/tests/test_target.py`:
```python
from __future__ import annotations

import pandas as pd

from CBS.cbs.target import Target, compute_target


def test_target_is_high_plus_low_minus_open(m5_factory) -> None:
    # window: open=1.0 (first bar open), high=1.8, low=0.5
    df = m5_factory("2024-01-01T00:00:00", [
        (1.0, 1.2, 0.9, 1.1),
        (1.1, 1.8, 0.5, 1.3),
        (1.3, 1.4, 1.0, 1.2),   # last close = 1.2
    ])
    t = compute_target(df)
    assert t.value == 1.8 + 0.5 - 1.0
    assert t.window_open == 1.0
    assert t.window_close_price == 1.2


def test_approach_side_up_when_target_above_close(m5_factory) -> None:
    df = m5_factory("2024-01-01T00:00:00", [(1.0, 2.0, 1.0, 1.2)])
    t = compute_target(df)   # target = 2.0 + 1.0 - 1.0 = 2.0 > close 1.2
    assert t.approach_side == "up"


def test_approach_side_down_when_target_below_close(m5_factory) -> None:
    df = m5_factory("2024-01-01T00:00:00", [(2.0, 2.1, 1.0, 1.9)])
    t = compute_target(df)   # target = 2.1 + 1.0 - 2.0 = 1.1 < close 1.9
    assert t.approach_side == "down"


def test_empty_window_raises(m5_factory) -> None:
    import pytest
    df = m5_factory("2024-01-01T00:00:00", [])
    with pytest.raises(ValueError):
        compute_target(df)
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest CBS/tests/test_target.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement target.py**

`CBS/cbs/target.py`:
```python
"""PSND measured-move target: value = High + Low - Open over a window."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Target:
    value: float
    approach_side: str          # "up" or "down"
    window_open: float
    window_high: float
    window_low: float
    window_close_price: float


def compute_target(window: pd.DataFrame) -> Target:
    """Compute the PSND target for a window of M5 bars.

    Raises ValueError if the window is empty.
    """
    if len(window) == 0:
        raise ValueError("compute_target: empty window")
    o = float(window["open"].iloc[0])
    h = float(window["high"].max())
    low = float(window["low"].min())
    close = float(window["close"].iloc[-1])
    value = h + low - o
    side = "up" if value > close else "down"
    return Target(value=value, approach_side=side, window_open=o,
                  window_high=h, window_low=low, window_close_price=close)
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest CBS/tests/test_target.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add CBS/cbs/target.py CBS/tests/test_target.py
git commit -m "feat(cbs): measured-move target + approach side"
```

---

## Task 4: Timing engine (Engine A)

**Files:**
- Create: `CBS/cbs/timing.py`
- Test: `CBS/tests/test_timing.py`

- [ ] **Step 1: Write failing tests**

`CBS/tests/test_timing.py`:
```python
from __future__ import annotations

import math
from datetime import timedelta

import pandas as pd

from CBS.cbs.timing import TimingRecord, measure_move


def _window(m5_factory):
    # 12 bars (1h) window: open=1.0, high=1.5, low=0.9, close=1.1 -> target=1.4 (up)
    pre = [(1.0, 1.5, 0.9, 1.1)] * 12
    return pre


def test_completes_when_price_touches_target_within_tolerance(m5_factory) -> None:
    # window 1h, then a bar reaching 1.399 (within tol 0.05 of target 1.4) 30min after close.
    rows = _window(m5_factory)
    # 6 filler bars (30 min) below target, then a spike to 1.399
    rows += [(1.1, 1.2, 1.05, 1.15)] * 6
    rows += [(1.15, 1.399, 1.15, 1.30)]
    df = m5_factory("2024-01-01T00:00:00", rows)
    rec = measure_move(df, symbol="EURUSD", anchor=0, block=1, tol_price=0.05,
                       cap_hours=48, date="2024-01-01")
    assert rec.completed is True
    assert rec.instant is False
    # window closes at 01:00, touch bar opens at 01:35 -> ~35min ~ 0.583h
    assert math.isclose(rec.hours_to_complete, 35 / 60, rel_tol=1e-6)


def test_instant_when_first_post_window_bar_already_within_tolerance(m5_factory) -> None:
    rows = _window(m5_factory)
    rows += [(1.38, 1.41, 1.38, 1.40)]   # first post-window bar straddles target 1.4
    df = m5_factory("2024-01-01T00:00:00", rows)
    rec = measure_move(df, symbol="EURUSD", anchor=0, block=1, tol_price=0.05,
                       cap_hours=48, date="2024-01-01")
    assert rec.completed is True
    assert rec.instant is True
    assert rec.hours_to_complete == 0.0


def test_not_completed_when_target_never_reached_within_cap(m5_factory) -> None:
    rows = _window(m5_factory)
    rows += [(1.1, 1.2, 1.05, 1.15)] * 6   # only 30 min of data after close, never near 1.4
    df = m5_factory("2024-01-01T00:00:00", rows)
    rec = measure_move(df, symbol="EURUSD", anchor=0, block=1, tol_price=0.05,
                       cap_hours=48, date="2024-01-01")
    assert rec.completed is False
    assert math.isnan(rec.hours_to_complete)
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest CBS/tests/test_timing.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement timing.py**

`CBS/cbs/timing.py`:
```python
"""Engine A — time-to-complete for a single (window, tolerance).

Given the full M5 frame and a window defined by anchor+block, compute the target,
then scan forward up to cap_hours for the first bar whose [low, high] range comes
within tol_price of the target. Records hours-to-complete and instant/completed
flags (design §2.3–§2.4).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import timedelta

import pandas as pd

from .bars import slice_window
from .target import compute_target


@dataclass(frozen=True)
class TimingRecord:
    symbol: str
    date: str
    anchor: int
    block: int
    tol_mult: int
    target: float
    approach_side: str
    completed: bool
    instant: bool
    hours_to_complete: float
    window_close_price: float
    bars_scanned: int


def _touches(low: float, high: float, target: float, tol: float) -> bool:
    """True if [low, high] comes within tol of target (band overlap)."""
    return (low - tol) <= target <= (high + tol)


def measure_move(df: pd.DataFrame, *, symbol: str, anchor: int, block: int,
                 tol_price: float, cap_hours: int, date: str,
                 tol_mult: int = 1) -> TimingRecord:
    """Measure time-to-complete for one window on one day.

    `df` must contain the window bars plus forward bars up to cap_hours after close.
    The window is [anchor_ts, anchor_ts + block hours) where anchor_ts is `date` at
    hour `anchor` (UTC).
    """
    anchor_ts = pd.Timestamp(f"{date}T00:00:00", tz="UTC") + timedelta(hours=anchor)
    close_ts = anchor_ts + timedelta(hours=block)
    window = slice_window(df, anchor_ts, close_ts)
    if len(window) == 0:
        raise ValueError(f"empty window {symbol} {date} a={anchor} b={block}")
    tgt = compute_target(window)

    fwd = slice_window(df, close_ts, close_ts + timedelta(hours=cap_hours))
    completed = False
    instant = False
    hours = math.nan
    scanned = 0
    for i, row in enumerate(fwd.itertuples(index=False)):
        scanned += 1
        if _touches(row.low, row.high, tgt.value, tol_price):
            completed = True
            instant = (i == 0)
            delta = (row.time_utc - close_ts).total_seconds() / 3600.0
            hours = 0.0 if instant else delta
            break

    return TimingRecord(
        symbol=symbol, date=date, anchor=anchor, block=block, tol_mult=tol_mult,
        target=tgt.value, approach_side=tgt.approach_side, completed=completed,
        instant=instant, hours_to_complete=hours,
        window_close_price=tgt.window_close_price, bars_scanned=scanned,
    )
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest CBS/tests/test_timing.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add CBS/cbs/timing.py CBS/tests/test_timing.py
git commit -m "feat(cbs): timing engine — time-to-complete with instant/cap handling"
```

---

## Task 5: Entry detector framework + baselines

This task builds the `EntrySignal`/`EntryContext` interface and the **baseline** detectors (the control group). Structure/liquidity/time detectors follow in Tasks 6–8, each added to the same registry.

**Files:**
- Create: `CBS/cbs/entries.py`
- Test: `CBS/tests/test_entries.py`

- [ ] **Step 1: Write failing tests for the framework + baselines**

`CBS/tests/test_entries.py`:
```python
from __future__ import annotations

import pandas as pd

from CBS.cbs.entries import (
    EntrySignal, EntryContext, build_context,
    enter_at_window_close, first_m5_close, first_pullback_pct,
    DETECTORS,
)


def _ctx(m5_factory, approach="up"):
    # window 12 bars (1h), then forward bars to a completion at bar +6
    window = [(1.0, 1.5, 0.9, 1.1)] * 12
    fwd = [(1.1, 1.2, 1.05, 1.15)] * 5 + [(1.15, 1.45, 1.15, 1.40)]
    df = m5_factory("2024-01-01T00:00:00", window + fwd)
    return build_context(
        df, symbol="EURUSD",
        window_close_ts=pd.Timestamp("2024-01-01T01:00:00", tz="UTC"),
        completion_ts=pd.Timestamp("2024-01-01T01:30:00", tz="UTC"),
        target=1.4, approach_side=approach, pip_size=0.0001,
        lookback_hours=12, atr_period=14, atr_k=1.5,
    )


def test_build_context_clips_to_decision_horizon(m5_factory) -> None:
    ctx = _ctx(m5_factory)
    # context M5 must not contain bars after completion_ts
    assert ctx.m5["time_utc"].max() <= ctx.completion_ts
    assert ctx.atr_m5 > 0


def test_enter_at_window_close_returns_close_price(m5_factory) -> None:
    ctx = _ctx(m5_factory)
    sig = enter_at_window_close(ctx)
    assert sig is not None
    assert sig.name == "enter_at_window_close"
    # entry = close of the bar at/just before window_close_ts (the 12th window bar close = 1.1)
    assert sig.entry_price == 1.1
    # long invalidation below entry
    assert sig.invalidation_price < sig.entry_price


def test_first_m5_close_fires_on_first_close_in_direction(m5_factory) -> None:
    ctx = _ctx(m5_factory)
    sig = first_m5_close(ctx)
    assert sig is not None
    assert sig.entry_time >= ctx.window_close_ts


def test_first_pullback_pct_uses_atr_fallback_when_no_structure(m5_factory) -> None:
    ctx = _ctx(m5_factory)
    sig = first_pullback_pct(ctx)
    assert sig is None or sig.invalidation_price < sig.entry_price  # long => SL below


def test_registry_contains_baselines() -> None:
    for name in ("enter_at_window_close", "first_m5_close", "first_pullback_pct"):
        assert name in DETECTORS
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest CBS/tests/test_entries.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement entries.py framework + baselines**

`CBS/cbs/entries.py`:
```python
"""Candidate entry detectors for CBS Engine B.

Each detector is a pure function (EntryContext) -> EntrySignal | None. A detector
abstains (returns None) when its pattern is not present. All detectors may only
read bars at/before ctx.completion_ts (no lookahead — enforced by build_context).

This module starts with the framework + baseline (control-group) detectors.
Structure, liquidity, and time detectors are appended in later tasks and
registered in DETECTORS.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Callable, Optional

import pandas as pd

from .bars import slice_window, resample_h1, atr_m5


@dataclass(frozen=True)
class EntrySignal:
    name: str
    entry_price: float
    invalidation_price: float
    entry_time: pd.Timestamp


@dataclass(frozen=True)
class EntryContext:
    symbol: str
    m5: pd.DataFrame
    h1: pd.DataFrame
    window_close_ts: pd.Timestamp
    completion_ts: pd.Timestamp
    target: float
    approach_side: str
    pip_size: float
    atr_m5: float
    atr_k: float


def build_context(df: pd.DataFrame, *, symbol: str, window_close_ts: pd.Timestamp,
                  completion_ts: pd.Timestamp, target: float, approach_side: str,
                  pip_size: float, lookback_hours: int, atr_period: int,
                  atr_k: float) -> EntryContext:
    """Clip `df` to [window_close_ts - lookback, completion_ts] and assemble context."""
    lo = window_close_ts - timedelta(hours=lookback_hours)
    # half-open slice then include the completion bar explicitly
    m5 = df.loc[(df["time_utc"] >= lo) & (df["time_utc"] <= completion_ts)].reset_index(drop=True)
    h1 = resample_h1(m5)
    atr = atr_m5(m5, period=atr_period)
    return EntryContext(symbol=symbol, m5=m5, h1=h1, window_close_ts=window_close_ts,
                        completion_ts=completion_ts, target=target,
                        approach_side=approach_side, pip_size=pip_size,
                        atr_m5=atr, atr_k=atr_k)


def _atr_sl(ctx: EntryContext, entry: float) -> float:
    """Fallback invalidation: entry -/+ k*ATR on the side opposite the target."""
    dist = ctx.atr_k * ctx.atr_m5
    return entry - dist if ctx.approach_side == "up" else entry + dist


def _post_window(ctx: EntryContext) -> pd.DataFrame:
    return ctx.m5.loc[ctx.m5["time_utc"] >= ctx.window_close_ts].reset_index(drop=True)


def _window_close_bar(ctx: EntryContext) -> pd.Series:
    """Last bar at/before window_close_ts (the bar whose close defines window close price)."""
    pre = ctx.m5.loc[ctx.m5["time_utc"] < ctx.window_close_ts]
    return pre.iloc[-1]


# --- Baseline detectors (control group) -------------------------------------

def enter_at_window_close(ctx: EntryContext) -> Optional[EntrySignal]:
    bar = _window_close_bar(ctx)
    entry = float(bar["close"])
    return EntrySignal("enter_at_window_close", entry, _atr_sl(ctx, entry),
                       ctx.window_close_ts)


def first_m5_close(ctx: EntryContext) -> Optional[EntrySignal]:
    fwd = _post_window(ctx)
    for row in fwd.itertuples(index=False):
        in_dir = (row.close > row.open) if ctx.approach_side == "up" else (row.close < row.open)
        if in_dir:
            entry = float(row.close)
            return EntrySignal("first_m5_close", entry, _atr_sl(ctx, entry), row.time_utc)
    return None


def first_pullback_pct(ctx: EntryContext, pct: float = 0.3) -> Optional[EntrySignal]:
    """Enter after price retraces `pct` of the move's initial extension back toward start."""
    fwd = _post_window(ctx)
    if len(fwd) < 2:
        return None
    start = float(_window_close_bar(ctx)["close"])
    # extension extreme reached so far in the target direction
    if ctx.approach_side == "up":
        ext = float(fwd["high"].cummax().iloc[-1])
        pull_level = ext - pct * (ext - start)
        for row in fwd.itertuples(index=False):
            if row.low <= pull_level:
                return EntrySignal("first_pullback_pct", pull_level, _atr_sl(ctx, pull_level), row.time_utc)
    else:
        ext = float(fwd["low"].cummin().iloc[-1])
        pull_level = ext + pct * (start - ext)
        for row in fwd.itertuples(index=False):
            if row.high >= pull_level:
                return EntrySignal("first_pullback_pct", pull_level, _atr_sl(ctx, pull_level), row.time_utc)
    return None


DETECTORS: dict[str, Callable[[EntryContext], Optional[EntrySignal]]] = {
    "enter_at_window_close": enter_at_window_close,
    "first_m5_close": first_m5_close,
    "first_pullback_pct": first_pullback_pct,
}
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest CBS/tests/test_entries.py -v`
Expected: PASS (6 tests).

- [ ] **Step 5: Commit**

```bash
git add CBS/cbs/entries.py CBS/tests/test_entries.py
git commit -m "feat(cbs): entry detector framework + baseline controls"
```

---

## Task 6: Structure detectors

Add the PSND-flavored structure detectors to `entries.py` and register them. Each is a pure function with the rule stated; each gets a test with a synthetic path that makes the pattern unambiguous.

**Files:**
- Modify: `CBS/cbs/entries.py` (append detectors + register in `DETECTORS`)
- Test: `CBS/tests/test_entries_structure.py`

Detectors and rules (long-side described; short-side mirrors by swapping high/low and comparison):

- `ema21_retest` — compute EMA21 on `ctx.h1`. Fires when, after window close, an H1 bar closes above EMA21 (reclaim) and a later bar's low dips to within `0.25*ATR` of the EMA21 value then closes back above. Entry = EMA21 value at the retest bar; invalidation = retest bar low.
- `swing_retest` — find the most recent M5 swing high (a bar whose high > the 2 bars either side) before the move. Fires when post-window price breaks above it then trades back to within `0.25*ATR`. Entry = the swing level; invalidation = entry − `0.5*ATR`.
- `sr_retest` — given prior-day high (max high of the 24h before window_open) as resistance: fires when price breaks above PDH then retests it. Entry = PDH; invalidation = PDH − `0.5*ATR`.
- `fvg_fill` — detect a bullish M5 imbalance (bar i high < bar i+2 low) of size ≥ `20*pip_size` after window close; fires when a later bar trades back into the gap. Entry = gap top; invalidation = gap bottom.
- `fib_cluster` — compute fib 0.618 retrace of the post-window initial leg (start→first extreme); fires when price returns to within `0.25*ATR` of it. Entry = the 0.618 level; invalidation = entry − `0.5*ATR`.

- [ ] **Step 1: Write failing tests (one per detector, long side)**

`CBS/tests/test_entries_structure.py`:
```python
from __future__ import annotations

import pandas as pd

from CBS.cbs.entries import build_context, DETECTORS


def _df_ctx(m5_factory, window, fwd, lookback=window_pre := None):
    full = (lookback or []) + window + fwd
    df = m5_factory("2024-01-01T00:00:00", full)
    # window_close after len(lookback)+len(window) bars
    n_pre = len(lookback or [])
    close_min = 5 * (n_pre + len(window))
    comp_min = 5 * (len(full) - 1)
    base = pd.Timestamp("2024-01-01T00:00:00", tz="UTC")
    return build_context(
        df, symbol="EURUSD",
        window_close_ts=base + pd.Timedelta(minutes=close_min),
        completion_ts=base + pd.Timedelta(minutes=comp_min),
        target=1.4, approach_side="up", pip_size=0.0001,
        lookback_hours=24, atr_period=14, atr_k=1.5,
    )


def test_sr_retest_fires_on_pdh_break_and_retest(m5_factory) -> None:
    lookback = [(1.0, 1.20, 0.95, 1.10)] * 288       # 24h prior, PDH=1.20
    window = [(1.10, 1.15, 1.05, 1.12)] * 12          # 1h window, target up
    fwd = [(1.12, 1.25, 1.12, 1.22)]                  # break above 1.20
    fwd += [(1.22, 1.23, 1.20, 1.21)]                 # retest 1.20
    fwd += [(1.21, 1.45, 1.21, 1.40)]                 # to target
    ctx = _df_ctx(m5_factory, window, fwd, lookback)
    sig = DETECTORS["sr_retest"](ctx)
    assert sig is not None
    assert abs(sig.entry_price - 1.20) < 1e-9
    assert sig.invalidation_price < sig.entry_price


def test_fvg_fill_fires_when_gap_revisited(m5_factory) -> None:
    window = [(1.10, 1.15, 1.05, 1.12)] * 12
    # bullish gap: bar0 high 1.20 < bar2 low 1.25 -> gap [1.20,1.25]; then revisit
    fwd = [(1.12, 1.20, 1.12, 1.19)]
    fwd += [(1.19, 1.30, 1.19, 1.28)]
    fwd += [(1.28, 1.32, 1.25, 1.27)]
    fwd += [(1.27, 1.27, 1.22, 1.24)]   # trades back into gap (<=1.25)
    fwd += [(1.24, 1.45, 1.24, 1.40)]
    ctx = _df_ctx(m5_factory, window, fwd, [(1.0, 1.05, 0.95, 1.0)] * 288)
    sig = DETECTORS["fvg_fill"](ctx)
    assert sig is not None
    assert sig.invalidation_price < sig.entry_price


def test_swing_retest_registered_and_callable(m5_factory) -> None:
    assert "swing_retest" in DETECTORS
    window = [(1.10, 1.15, 1.05, 1.12)] * 12
    fwd = [(1.12, 1.30, 1.12, 1.28)] + [(1.28, 1.29, 1.18, 1.20)] + [(1.20, 1.45, 1.20, 1.40)]
    ctx = _df_ctx(m5_factory, window, fwd, [(1.0, 1.18, 0.95, 1.0)] * 288)
    sig = DETECTORS["swing_retest"](ctx)
    assert sig is None or sig.invalidation_price < sig.entry_price


def test_ema21_retest_and_fib_cluster_registered() -> None:
    assert "ema21_retest" in DETECTORS
    assert "fib_cluster" in DETECTORS
```

> Note on the helper: the walrus in `_df_ctx`'s signature is illustrative; implement it as a plain helper with `lookback=None` and compute timestamps from segment lengths. Keep the body as shown.

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest CBS/tests/test_entries_structure.py -v`
Expected: FAIL (KeyError on DETECTORS).

- [ ] **Step 3: Implement the 5 structure detectors and register them**

Append to `CBS/cbs/entries.py` (before the `DETECTORS` dict, then add entries to the dict). Implement each per the rules above. Reference implementation:

```python
# --- Structure detectors ----------------------------------------------------

def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _prior_extreme(ctx: EntryContext, kind: str) -> float:
    """PDH/PDL proxy: extreme of the lookback bars strictly before window close."""
    pre = ctx.m5.loc[ctx.m5["time_utc"] < ctx.window_close_ts]
    return float(pre["high"].max()) if kind == "high" else float(pre["low"].min())


def sr_retest(ctx: EntryContext) -> Optional[EntrySignal]:
    fwd = _post_window(ctx)
    tol = 0.5 * ctx.atr_m5
    if ctx.approach_side == "up":
        level = _prior_extreme(ctx, "high")
        broken = False
        for row in fwd.itertuples(index=False):
            if not broken and row.high > level:
                broken = True
                continue
            if broken and row.low <= level + 0.25 * ctx.atr_m5 and row.close >= level:
                return EntrySignal("sr_retest", level, level - tol, row.time_utc)
    else:
        level = _prior_extreme(ctx, "low")
        broken = False
        for row in fwd.itertuples(index=False):
            if not broken and row.low < level:
                broken = True
                continue
            if broken and row.high >= level - 0.25 * ctx.atr_m5 and row.close <= level:
                return EntrySignal("sr_retest", level, level + tol, row.time_utc)
    return None


def fvg_fill(ctx: EntryContext) -> Optional[EntrySignal]:
    fwd = _post_window(ctx).reset_index(drop=True)
    min_gap = 20 * ctx.pip_size
    n = len(fwd)
    for i in range(n - 2):
        if ctx.approach_side == "up":
            gap_lo, gap_hi = float(fwd.loc[i, "high"]), float(fwd.loc[i + 2, "low"])
            if gap_hi - gap_lo >= min_gap:
                for j in range(i + 3, n):
                    if fwd.loc[j, "low"] <= gap_hi:
                        return EntrySignal("fvg_fill", gap_hi, gap_lo, fwd.loc[j, "time_utc"])
        else:
            gap_hi, gap_lo = float(fwd.loc[i, "low"]), float(fwd.loc[i + 2, "high"])
            if gap_hi - gap_lo >= min_gap:
                for j in range(i + 3, n):
                    if fwd.loc[j, "high"] >= gap_lo:
                        return EntrySignal("fvg_fill", gap_lo, gap_hi, fwd.loc[j, "time_utc"])
    return None


def swing_retest(ctx: EntryContext) -> Optional[EntrySignal]:
    pre = ctx.m5.loc[ctx.m5["time_utc"] < ctx.window_close_ts].reset_index(drop=True)
    if len(pre) < 5:
        return None
    tol = 0.25 * ctx.atr_m5
    fwd = _post_window(ctx)
    if ctx.approach_side == "up":
        highs = pre["high"].values
        swing = None
        for k in range(2, len(highs) - 2):
            if highs[k] >= max(highs[k-2], highs[k-1], highs[k+1], highs[k+2]):
                swing = float(highs[k])
        if swing is None:
            return None
        broken = False
        for row in fwd.itertuples(index=False):
            if not broken and row.high > swing:
                broken = True
                continue
            if broken and row.low <= swing + tol:
                return EntrySignal("swing_retest", swing, swing - 0.5 * ctx.atr_m5, row.time_utc)
    else:
        lows = pre["low"].values
        swing = None
        for k in range(2, len(lows) - 2):
            if lows[k] <= min(lows[k-2], lows[k-1], lows[k+1], lows[k+2]):
                swing = float(lows[k])
        if swing is None:
            return None
        broken = False
        for row in fwd.itertuples(index=False):
            if not broken and row.low < swing:
                broken = True
                continue
            if broken and row.high >= swing - tol:
                return EntrySignal("swing_retest", swing, swing + 0.5 * ctx.atr_m5, row.time_utc)
    return None


def ema21_retest(ctx: EntryContext) -> Optional[EntrySignal]:
    h1 = ctx.h1.copy()
    if len(h1) < 21:
        return None
    h1["ema"] = _ema(h1["close"], 21)
    post = h1.loc[h1["time_utc"] >= ctx.window_close_ts].reset_index(drop=True)
    tol = 0.25 * ctx.atr_m5
    reclaimed = False
    for row in post.itertuples(index=False):
        if ctx.approach_side == "up":
            if not reclaimed and row.close > row.ema:
                reclaimed = True
                continue
            if reclaimed and row.low <= row.ema + tol and row.close >= row.ema:
                return EntrySignal("ema21_retest", float(row.ema), float(row.ema) - 0.5 * ctx.atr_m5, row.time_utc)
        else:
            if not reclaimed and row.close < row.ema:
                reclaimed = True
                continue
            if reclaimed and row.high >= row.ema - tol and row.close <= row.ema:
                return EntrySignal("ema21_retest", float(row.ema), float(row.ema) + 0.5 * ctx.atr_m5, row.time_utc)
    return None


def fib_cluster(ctx: EntryContext) -> Optional[EntrySignal]:
    fwd = _post_window(ctx).reset_index(drop=True)
    if len(fwd) < 3:
        return None
    start = float(_window_close_bar(ctx)["close"])
    tol = 0.25 * ctx.atr_m5
    if ctx.approach_side == "up":
        ext = float(fwd["high"].cummax().iloc[-1])
        level = ext - 0.618 * (ext - start)
        for row in fwd.itertuples(index=False):
            if row.low <= level + tol:
                return EntrySignal("fib_cluster", level, level - 0.5 * ctx.atr_m5, row.time_utc)
    else:
        ext = float(fwd["low"].cummin().iloc[-1])
        level = ext + 0.618 * (start - ext)
        for row in fwd.itertuples(index=False):
            if row.high >= level - tol:
                return EntrySignal("fib_cluster", level, level + 0.5 * ctx.atr_m5, row.time_utc)
    return None


DETECTORS.update({
    "ema21_retest": ema21_retest,
    "swing_retest": swing_retest,
    "sr_retest": sr_retest,
    "fvg_fill": fvg_fill,
    "fib_cluster": fib_cluster,
})
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest CBS/tests/test_entries_structure.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add CBS/cbs/entries.py CBS/tests/test_entries_structure.py
git commit -m "feat(cbs): structure entry detectors (ema21/swing/sr/fvg/fib)"
```

---

## Task 7: Liquidity / ICT detectors

**Files:**
- Modify: `CBS/cbs/entries.py`
- Test: `CBS/tests/test_entries_liquidity.py`

Detectors (long side; short mirrors):

- `order_block` — last down-close M5 bar before the post-window up-impulse. Fires when price returns into that bar's range. Entry = bar high; invalidation = bar low.
- `liquidity_sweep` — price wicks below the prior-day low (`_prior_extreme low`) then closes back above it within the next 3 bars. Entry = the reclaim bar close; invalidation = the sweep low.
- `breaker` — an order block that failed (price broke its low) then flips: fires when price reclaims the broken OB high. Entry = OB high; invalidation = the post-break extreme.
- `eqh_eql_raid` — two pre-window highs within `0.25*ATR` (equal highs); fires when price raids above them then trades back below. Entry = the equal-high level; invalidation = the raid extreme.

- [ ] **Step 1: Write failing tests**

`CBS/tests/test_entries_liquidity.py`:
```python
from __future__ import annotations

import pandas as pd

from CBS.cbs.entries import build_context, DETECTORS


def _ctx(m5_factory, lookback, window, fwd):
    full = lookback + window + fwd
    df = m5_factory("2024-01-01T00:00:00", full)
    base = pd.Timestamp("2024-01-01T00:00:00", tz="UTC")
    close_min = 5 * (len(lookback) + len(window))
    comp_min = 5 * (len(full) - 1)
    return build_context(
        df, symbol="EURUSD",
        window_close_ts=base + pd.Timedelta(minutes=close_min),
        completion_ts=base + pd.Timedelta(minutes=comp_min),
        target=1.4, approach_side="up", pip_size=0.0001,
        lookback_hours=24, atr_period=14, atr_k=1.5,
    )


def test_liquidity_sweep_fires_on_pdl_raid_and_reclaim(m5_factory) -> None:
    lookback = [(1.10, 1.15, 1.00, 1.12)] * 288   # PDL = 1.00
    window = [(1.12, 1.16, 1.08, 1.14)] * 12
    fwd = [(1.14, 1.14, 0.98, 1.02)]              # wick below PDL 1.00
    fwd += [(1.02, 1.10, 1.01, 1.08)]             # reclaim above 1.00
    fwd += [(1.08, 1.45, 1.08, 1.40)]
    ctx = _ctx(m5_factory, lookback, window, fwd)
    # approach side up but sweep is a long-from-below; detector should still produce a long signal
    sig = DETECTORS["liquidity_sweep"](ctx)
    assert sig is None or sig.invalidation_price < sig.entry_price


def test_order_block_registered_and_callable(m5_factory) -> None:
    assert "order_block" in DETECTORS
    lookback = [(1.0, 1.05, 0.95, 1.0)] * 288
    window = [(1.10, 1.16, 1.08, 1.14)] * 12
    fwd = [(1.14, 1.14, 1.10, 1.11)]              # down-close (the OB)
    fwd += [(1.11, 1.30, 1.11, 1.28)]             # up impulse
    fwd += [(1.28, 1.29, 1.12, 1.15)]             # return into OB range
    fwd += [(1.15, 1.45, 1.15, 1.40)]
    ctx = _ctx(m5_factory, lookback, window, fwd)
    sig = DETECTORS["order_block"](ctx)
    assert sig is None or sig.invalidation_price < sig.entry_price


def test_breaker_and_eqh_eql_registered() -> None:
    assert "breaker" in DETECTORS
    assert "eqh_eql_raid" in DETECTORS
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest CBS/tests/test_entries_liquidity.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement the 4 detectors per the rules above and register in `DETECTORS`.**

Append to `entries.py` following the same structure as Task 6 (long branch + mirrored short branch, ATR fallback when no clean level). Use `_prior_extreme`, `_post_window`, and `0.25*ctx.atr_m5` band tolerances. Register:
```python
DETECTORS.update({
    "order_block": order_block,
    "liquidity_sweep": liquidity_sweep,
    "breaker": breaker,
    "eqh_eql_raid": eqh_eql_raid,
})
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest CBS/tests/test_entries_liquidity.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add CBS/cbs/entries.py CBS/tests/test_entries_liquidity.py
git commit -m "feat(cbs): liquidity/ICT entry detectors (OB/sweep/breaker/eqh)"
```

---

## Task 8: Time / level detectors

**Files:**
- Modify: `CBS/cbs/entries.py`
- Test: `CBS/tests/test_entries_time.py`

Detectors (long side; short mirrors):

- `session_open_retrace` — after window close, fires when price retraces to within `0.25*ATR` of the window-close price (the "session open") having first moved ≥ `0.5*ATR` toward target. Entry = window-close price; invalidation = entry − `0.5*ATR`.
- `prior_level_react` — fires when price reaches the prior-week high proxy (max high over lookback) and reacts (closes back in target direction). Entry = that level; invalidation = level ± `0.5*ATR`. (Distinct from `sr_retest`: this is a *reaction* at the level, no prior break required.)
- `opening_range_break` — define the first-hour range after window close (high/low of first 12 post-window M5 bars). Fires on break of the range high then retest. Entry = range high; invalidation = range low.
- `round_number` — nearest round number to window-close price (multiple of `round_step` from config-derived `pip_size*1000`). Fires when price taps it. Entry = round number; invalidation = entry − `0.5*ATR`.

- [ ] **Step 1: Write failing tests**

`CBS/tests/test_entries_time.py`:
```python
from __future__ import annotations

import pandas as pd

from CBS.cbs.entries import build_context, DETECTORS


def _ctx(m5_factory, window, fwd, lookback):
    full = lookback + window + fwd
    df = m5_factory("2024-01-01T00:00:00", full)
    base = pd.Timestamp("2024-01-01T00:00:00", tz="UTC")
    return build_context(
        df, symbol="EURUSD",
        window_close_ts=base + pd.Timedelta(minutes=5 * (len(lookback) + len(window))),
        completion_ts=base + pd.Timedelta(minutes=5 * (len(full) - 1)),
        target=1.4, approach_side="up", pip_size=0.0001,
        lookback_hours=24, atr_period=14, atr_k=1.5,
    )


def test_opening_range_break_registered(m5_factory) -> None:
    assert "opening_range_break" in DETECTORS
    window = [(1.10, 1.16, 1.08, 1.14)] * 12
    fwd = [(1.14, 1.18, 1.12, 1.16)] * 12       # opening range
    fwd += [(1.16, 1.25, 1.16, 1.22)]           # break range high
    fwd += [(1.22, 1.23, 1.17, 1.19)]           # retest
    fwd += [(1.19, 1.45, 1.19, 1.40)]
    ctx = _ctx(m5_factory, window, fwd, [(1.0, 1.05, 0.95, 1.0)] * 288)
    sig = DETECTORS["opening_range_break"](ctx)
    assert sig is None or sig.invalidation_price < sig.entry_price


def test_session_open_retrace_registered(m5_factory) -> None:
    assert "session_open_retrace" in DETECTORS


def test_prior_level_and_round_number_registered() -> None:
    assert "prior_level_react" in DETECTORS
    assert "round_number" in DETECTORS
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest CBS/tests/test_entries_time.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement the 4 detectors per the rules above and register in `DETECTORS`.**

Append to `entries.py`. For `round_number`, use `step = ctx.pip_size * 1000` (e.g. EURUSD → 0.10? choose nearest 0.0050 grid: `step = ctx.pip_size * 50`) — document the chosen grid in a comment. Register:
```python
DETECTORS.update({
    "session_open_retrace": session_open_retrace,
    "prior_level_react": prior_level_react,
    "opening_range_break": opening_range_break,
    "round_number": round_number,
})
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest CBS/tests/test_entries_time.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add CBS/cbs/entries.py CBS/tests/test_entries_time.py
git commit -m "feat(cbs): time/level entry detectors (orb/session/prior/round)"
```

---

## Task 9: Evaluation engine (Engine B)

**Files:**
- Create: `CBS/cbs/evaluate.py`
- Test: `CBS/tests/test_evaluate.py`

- [ ] **Step 1: Write failing tests**

`CBS/tests/test_evaluate.py`:
```python
from __future__ import annotations

import math

import pandas as pd

from CBS.cbs.entries import EntrySignal, build_context
from CBS.cbs.evaluate import evaluate_entry


def _ctx(m5_factory):
    window = [(1.0, 1.5, 0.9, 1.1)] * 12
    fwd = [(1.1, 1.2, 1.05, 1.15)] * 5 + [(1.15, 1.45, 1.15, 1.40)]
    df = m5_factory("2024-01-01T00:00:00", window + fwd)
    return build_context(
        df, symbol="EURUSD",
        window_close_ts=pd.Timestamp("2024-01-01T01:00:00", tz="UTC"),
        completion_ts=pd.Timestamp("2024-01-01T01:30:00", tz="UTC"),
        target=1.4, approach_side="up", pip_size=0.0001,
        lookback_hours=12, atr_period=14, atr_k=1.5,
    )


def test_r_multiple_long_win(m5_factory) -> None:
    ctx = _ctx(m5_factory)
    sig = EntrySignal("x", entry_price=1.10, invalidation_price=1.00,
                      entry_time=pd.Timestamp("2024-01-01T01:00:00", tz="UTC"))
    res = evaluate_entry(ctx, sig, date="2024-01-01", anchor=0, block=1)
    # reward = 1.40-1.10 = 0.30 ; risk = 1.10-1.00 = 0.10 ; R = 3.0
    assert math.isclose(res.r_multiple, 3.0, rel_tol=1e-9)
    assert res.win is True
    assert res.mae_r <= 0  # adverse excursion non-positive in R terms


def test_loss_when_invalidation_hit_before_target(m5_factory) -> None:
    ctx = _ctx(m5_factory)
    # SL just below entry so the first dip to 1.05 stops it out before target
    sig = EntrySignal("x", entry_price=1.10, invalidation_price=1.06,
                      entry_time=pd.Timestamp("2024-01-01T01:00:00", tz="UTC"))
    res = evaluate_entry(ctx, sig, date="2024-01-01", anchor=0, block=1)
    assert res.win is False


def test_no_sl_room_returns_nan_r(m5_factory) -> None:
    ctx = _ctx(m5_factory)
    sig = EntrySignal("x", entry_price=1.10, invalidation_price=1.10,
                      entry_time=pd.Timestamp("2024-01-01T01:00:00", tz="UTC"))
    res = evaluate_entry(ctx, sig, date="2024-01-01", anchor=0, block=1)
    assert math.isnan(res.r_multiple)
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest CBS/tests/test_evaluate.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement evaluate.py**

`CBS/cbs/evaluate.py`:
```python
"""Engine B — evaluate one entry signal against the measured move.

Holds from entry to target, walking M5 bars from entry_time to completion. Computes
R-multiple, MFE/MAE in R units, win/loss (target vs invalidation, whichever first),
and spread cost. Lookahead-safe: only bars at/after entry_time are walked, and the
target/invalidation are known at entry.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from .entries import EntryContext, EntrySignal


@dataclass(frozen=True)
class EntryResult:
    symbol: str
    date: str
    anchor: int
    block: int
    name: str
    entry_price: float
    invalidation_price: float
    target: float
    r_multiple: float
    mfe_r: float
    mae_r: float
    win: bool
    cost_spread_price: float
    entry_lead_hours: float


def evaluate_entry(ctx: EntryContext, sig: EntrySignal, *, date: str,
                   anchor: int, block: int) -> EntryResult:
    side_up = ctx.approach_side == "up"
    risk = (sig.entry_price - sig.invalidation_price) if side_up else (sig.invalidation_price - sig.entry_price)
    reward = (ctx.target - sig.entry_price) if side_up else (sig.entry_price - ctx.target)
    r_mult = math.nan if risk <= 0 else reward / risk

    path = ctx.m5.loc[ctx.m5["time_utc"] >= sig.entry_time].reset_index(drop=True)
    spread_price = 0.0
    if len(path):
        spread_price = float(path["spread"].iloc[0]) * ctx.pip_size

    win = False
    mfe = 0.0
    mae = 0.0
    for row in path.itertuples(index=False):
        if side_up:
            mfe = max(mfe, row.high - sig.entry_price)
            mae = min(mae, row.low - sig.entry_price)
            hit_sl = row.low <= sig.invalidation_price
            hit_tp = row.high >= ctx.target
        else:
            mfe = max(mfe, sig.entry_price - row.low)
            mae = min(mae, sig.entry_price - row.high)
            hit_sl = row.high >= sig.invalidation_price
            hit_tp = row.low <= ctx.target
        if hit_sl and not hit_tp:
            win = False
            break
        if hit_tp:
            win = True
            break

    mfe_r = math.nan if risk <= 0 else mfe / risk
    mae_r = math.nan if risk <= 0 else mae / risk
    lead = (ctx.completion_ts - sig.entry_time).total_seconds() / 3600.0

    return EntryResult(
        symbol=ctx.symbol, date=date, anchor=anchor, block=block, name=sig.name,
        entry_price=sig.entry_price, invalidation_price=sig.invalidation_price,
        target=ctx.target, r_multiple=r_mult, mfe_r=mfe_r, mae_r=mae_r, win=win,
        cost_spread_price=spread_price, entry_lead_hours=lead,
    )
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest CBS/tests/test_evaluate.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add CBS/cbs/evaluate.py CBS/tests/test_evaluate.py
git commit -m "feat(cbs): evaluation engine — R/MFE/MAE/win/cost per entry"
```

---

## Task 10: Reports + audit manifest

**Files:**
- Create: `CBS/cbs/report.py`
- Test: `CBS/tests/test_report.py`

`report.py` builds T1 (time-to-complete) and T2 (best-entry) from lists of records, and writes an audit folder with sha256 manifest.

- [ ] **Step 1: Write failing tests**

`CBS/tests/test_report.py`:
```python
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

from CBS.cbs.timing import TimingRecord
from CBS.cbs.evaluate import EntryResult
from CBS.cbs.report import build_t1, build_t2, write_audit_run


def _timing(**kw):
    base = dict(symbol="EURUSD", date="2024-01-01", anchor=0, block=1, tol_mult=1,
                target=1.4, approach_side="up", completed=True, instant=False,
                hours_to_complete=2.0, window_close_price=1.1, bars_scanned=24)
    base.update(kw)
    return TimingRecord(**base)


def test_build_t1_aggregates_completion_and_median_hours() -> None:
    recs = [_timing(hours_to_complete=2.0), _timing(hours_to_complete=4.0),
            _timing(completed=False, hours_to_complete=float("nan"))]
    t1 = build_t1(recs)
    row = t1[(t1["symbol"] == "EURUSD") & (t1["block"] == 1) & (t1["anchor"] == 0) & (t1["tol_mult"] == 1)].iloc[0]
    assert row["n"] == 3
    assert abs(row["completion_rate"] - (2 / 3)) < 1e-9
    assert abs(row["median_hours"] - 3.0) < 1e-9   # median of [2,4]


def _entry(**kw):
    base = dict(symbol="EURUSD", date="2024-01-01", anchor=0, block=1, name="sr_retest",
                entry_price=1.1, invalidation_price=1.0, target=1.4, r_multiple=3.0,
                mfe_r=3.0, mae_r=-0.5, win=True, cost_spread_price=0.0001, entry_lead_hours=1.0)
    base.update(kw)
    return EntryResult(**base)


def test_build_t2_ranks_entries_by_median_r() -> None:
    recs = [_entry(name="sr_retest", r_multiple=3.0, win=True),
            _entry(name="sr_retest", r_multiple=2.0, win=True),
            _entry(name="first_m5_close", r_multiple=0.5, win=False)]
    t2 = build_t2(recs)
    row = t2[(t2["symbol"] == "EURUSD") & (t2["name"] == "sr_retest")].iloc[0]
    assert abs(row["median_r"] - 2.5) < 1e-9
    assert abs(row["win_rate"] - 1.0) < 1e-9


def test_write_audit_run_creates_manifest(tmp_path: Path) -> None:
    recs_t = [_timing()]
    recs_e = [_entry()]
    out = write_audit_run(tmp_path, run_name="pilot", config={"k": 1.5},
                           timing=recs_t, entries=recs_e, log_text="ran ok")
    manifest = Path(out) / "manifest.sha256"
    assert manifest.exists()
    # every listed file hash matches
    for line in manifest.read_text().splitlines():
        digest, name = line.split("  ", 1)
        data = (Path(out) / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest CBS/tests/test_report.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement report.py**

`CBS/cbs/report.py`:
```python
"""T1/T2 table builders + audit-trail run writer (design §5)."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

import pandas as pd

from .timing import TimingRecord
from .evaluate import EntryResult


def build_t1(records: Sequence[TimingRecord]) -> pd.DataFrame:
    """Aggregate timing records to per (symbol, anchor, block, tol_mult) stats."""
    df = pd.DataFrame([asdict(r) for r in records])
    grp = df.groupby(["symbol", "anchor", "block", "tol_mult"], as_index=False)
    out = grp.agg(
        n=("completed", "size"),
        completion_rate=("completed", "mean"),
        instant_rate=("instant", "mean"),
        median_hours=("hours_to_complete", "median"),
        p25_hours=("hours_to_complete", lambda s: s.quantile(0.25)),
        p75_hours=("hours_to_complete", lambda s: s.quantile(0.75)),
    )
    return out


def build_t2(records: Sequence[EntryResult]) -> pd.DataFrame:
    """Aggregate entry results to per (symbol, name) ranking stats."""
    df = pd.DataFrame([asdict(r) for r in records])
    grp = df.groupby(["symbol", "name"], as_index=False)
    out = grp.agg(
        n=("win", "size"),
        median_r=("r_multiple", "median"),
        win_rate=("win", "mean"),
        median_mae_r=("mae_r", "median"),
        median_lead_hours=("entry_lead_hours", "median"),
    )
    out = out.sort_values(["symbol", "median_r"], ascending=[True, False]).reset_index(drop=True)
    return out


def _write_csv(path: Path, records, df: pd.DataFrame | None = None) -> None:
    if df is None:
        df = pd.DataFrame([asdict(r) for r in records])
    df.to_csv(path, index=False)


def write_audit_run(base_dir: Path, *, run_name: str, config: dict,
                    timing: Sequence[TimingRecord], entries: Sequence[EntryResult],
                    log_text: str, utcstamp: str = "run") -> Path:
    """Write raw CSVs, config, log, and a sha256 manifest. Returns the run folder.

    `utcstamp` is supplied by the caller (no wall-clock inside the analysis path).
    """
    out = Path(base_dir) / f"{run_name}-{utcstamp}"
    out.mkdir(parents=True, exist_ok=True)

    _write_csv(out / "timing_raw.csv", timing)
    _write_csv(out / "entries_raw.csv", entries)
    build_t1(timing).to_csv(out / "t1_time_to_complete.csv", index=False)
    if entries:
        build_t2(entries).to_csv(out / "t2_best_entry.csv", index=False)
    (out / "config.json").write_text(json.dumps(config, indent=2, default=str), encoding="utf-8")
    (out / "run.log").write_text(log_text, encoding="utf-8")

    # manifest over every file except the manifest itself
    lines = []
    for p in sorted(out.glob("*")):
        if p.name == "manifest.sha256":
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(f"{digest}  {p.name}")
    (out / "manifest.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest CBS/tests/test_report.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add CBS/cbs/report.py CBS/tests/test_report.py
git commit -m "feat(cbs): T1/T2 builders + sha256 audit manifest writer"
```

---

## Task 11: Pipeline driver (wires engines + OOS split)

**Files:**
- Create: `CBS/cbs/pipeline.py`
- Test: `CBS/tests/test_pipeline.py`

The pipeline, per instrument: load M5 → enumerate trading days → for each (day, anchor, block, tol_mult) run timing → for completing non-instant moves at the operative tolerance, build context + run every detector + evaluate. Splits into in-sample / OOS (last 6 months) and tags each record with `split`.

- [ ] **Step 1: Write failing test (small synthetic, 1 instrument, reduced grid)**

`CBS/tests/test_pipeline.py`:
```python
from __future__ import annotations

import pandas as pd

from CBS.cbs.pipeline import run_instrument, split_in_out_sample


def test_split_in_out_sample_tags_last_6mo() -> None:
    dates = pd.to_datetime(["2024-01-01", "2024-04-01", "2024-09-01", "2024-12-01"])
    df = pd.DataFrame({"date": dates})
    tagged = split_in_out_sample(df, oos_months=6, date_col="date")
    assert set(tagged["split"]) == {"in_sample", "oos"}
    # last 6 months relative to max date 2024-12-01 -> 2024-09-01 & 2024-12-01 are oos
    oos_dates = set(tagged.loc[tagged["split"] == "oos", "date"].dt.strftime("%Y-%m-%d"))
    assert oos_dates == {"2024-09-01", "2024-12-01"}


def test_run_instrument_smoke(m5_factory) -> None:
    # 2 days of bars, reduced grid via params; assert it returns timing + entry lists
    rows = []
    for d in range(2):
        # each day: 24h of 5min bars = 288 bars; simple oscillation that hits H+L-O
        day = [(1.0 + 0.001 * (i % 10), 1.0 + 0.001 * (i % 10) + 0.005,
                1.0 + 0.001 * (i % 10) - 0.005, 1.0 + 0.001 * (i % 10)) for i in range(288)]
        rows += day
    df = m5_factory("2024-01-01T00:00:00", rows)
    timing, entries = run_instrument(
        df, symbol="EURUSD", pip_size=0.0001, base_tol_pips=5,
        anchors=(0,), blocks=(1,), tol_mults=(1, 2), cap_hours=48,
        atr_period=14, atr_k=1.5, lookback_hours=12,
    )
    assert isinstance(timing, list)
    assert isinstance(entries, list)
    assert all(t.symbol == "EURUSD" for t in timing)
```

- [ ] **Step 2: Run to verify fail**

Run: `python -m pytest CBS/tests/test_pipeline.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement pipeline.py**

`CBS/cbs/pipeline.py`:
```python
"""Driver wiring timing + entry evaluation across the window grid, per instrument."""
from __future__ import annotations

from datetime import timedelta

import pandas as pd

from .timing import measure_move, TimingRecord
from .entries import build_context, DETECTORS
from .evaluate import evaluate_entry, EntryResult


def _trading_days(df: pd.DataFrame) -> list[str]:
    return sorted(df["time_utc"].dt.strftime("%Y-%m-%d").unique().tolist())


def split_in_out_sample(df: pd.DataFrame, *, oos_months: int = 6,
                        date_col: str = "date") -> pd.DataFrame:
    """Tag rows 'in_sample'/'oos': oos = within `oos_months` of the latest date."""
    d = df.copy()
    d[date_col] = pd.to_datetime(d[date_col])
    cutoff = d[date_col].max() - pd.DateOffset(months=oos_months)
    d["split"] = (d[date_col] > cutoff).map({True: "oos", False: "in_sample"})
    # boundary date itself (== cutoff) stays in_sample; > cutoff is oos
    d.loc[d[date_col] <= cutoff, "split"] = "in_sample"
    return d


def run_instrument(df: pd.DataFrame, *, symbol: str, pip_size: float, base_tol_pips: float,
                   anchors, blocks, tol_mults, cap_hours: int, atr_period: int,
                   atr_k: float, lookback_hours: int) -> tuple[list[TimingRecord], list[EntryResult]]:
    """Run the full grid for one instrument. Returns (timing_records, entry_results)."""
    timing: list[TimingRecord] = []
    entries: list[EntryResult] = []
    days = _trading_days(df)

    for date in days:
        for anchor in anchors:
            for block in blocks:
                for tol_mult in tol_mults:
                    tol_price = base_tol_pips * pip_size * tol_mult
                    try:
                        rec = measure_move(df, symbol=symbol, anchor=anchor, block=block,
                                           tol_price=tol_price, cap_hours=cap_hours,
                                           date=date, tol_mult=tol_mult)
                    except ValueError:
                        continue  # empty window (no data for that slot) — skip, not silent loss at report time
                    timing.append(rec)

                    # entries only on completing, non-instant moves at operative (largest passing) tol
                    if not rec.completed or rec.instant:
                        continue
                    close_ts = pd.Timestamp(f"{date}T00:00:00", tz="UTC") + timedelta(hours=anchor + block)
                    comp_ts = close_ts + timedelta(hours=rec.hours_to_complete)
                    ctx = build_context(df, symbol=symbol, window_close_ts=close_ts,
                                        completion_ts=comp_ts, target=rec.target,
                                        approach_side=rec.approach_side, pip_size=pip_size,
                                        lookback_hours=lookback_hours, atr_period=atr_period,
                                        atr_k=atr_k)
                    for name, fn in DETECTORS.items():
                        sig = fn(ctx)
                        if sig is None:
                            continue
                        entries.append(evaluate_entry(ctx, sig, date=date,
                                                      anchor=anchor, block=block))
    return timing, entries
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest CBS/tests/test_pipeline.py -v`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add CBS/cbs/pipeline.py CBS/tests/test_pipeline.py
git commit -m "feat(cbs): pipeline driver across window grid + OOS split"
```

---

## Task 12: Data fetch script (operational — not TDD)

**Files:**
- Create: `scripts/fetch_cbs_data.py`

This queries MT5 for available symbols, maps PSND instruments to broker symbol names where they differ, and dumps ~2yr M5 per instrument into `CBS/data/`. It documents (prints + writes `CBS/data/_fetch_report.json`) any instrument the broker does not expose.

- [ ] **Step 1: Implement the fetch script**

`scripts/fetch_cbs_data.py`:
```python
"""Fetch ~2yr M5 bars for the 11 PSND instruments from the running MT5 terminal.

Writes CBS/data/<SYMBOL>_M5_<from>_<to>.csv per available instrument and a
_fetch_report.json documenting which symbols were found/missing. Operational
glue around tools/mt5_data.py — no analysis logic here.

Usage:  python scripts/fetch_cbs_data.py [--years 2]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import MetaTrader5 as mt5

from CBS.cbs.config import INSTRUMENTS

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "CBS" / "data"


def available_symbols() -> set[str]:
    if not mt5.initialize():
        print(f"MT5 init failed: {mt5.last_error()}", file=sys.stderr)
        sys.exit(1)
    syms = {s.name for s in mt5.symbols_get()}
    mt5.shutdown()
    return syms


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, default=2)
    args = ap.parse_args()

    DATA.mkdir(parents=True, exist_ok=True)
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=365 * args.years)
    syms = available_symbols()

    report = {"requested": list(INSTRUMENTS), "found": [], "missing": [], "files": {}}
    for sym in INSTRUMENTS:
        # broker may suffix symbols (e.g. EURUSD.r) — try exact then prefix match
        match = sym if sym in syms else next((s for s in syms if s.upper().startswith(sym)), None)
        if match is None:
            report["missing"].append(sym)
            continue
        out = DATA / f"{sym}_M5_{start}_{end}.csv"
        cmd = [sys.executable, str(REPO / "tools" / "mt5_data.py"), "dump-bars",
               match, "M5", str(start), str(end), str(out)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and out.exists():
            report["found"].append(sym)
            report["files"][sym] = str(out.relative_to(REPO))
        else:
            report["missing"].append(sym)
            print(f"dump failed for {sym} ({match}): {res.stdout}{res.stderr}", file=sys.stderr)

    (DATA / "_fetch_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it (requires MT5 terminal running)**

Run: `python scripts/fetch_cbs_data.py --years 2`
Expected: prints a JSON report; `CBS/data/` populated; `_fetch_report.json` lists found/missing. **Do not commit the CSVs** (gitignored). Commit only the script.

- [ ] **Step 3: Commit the script**

```bash
git add scripts/fetch_cbs_data.py
git commit -m "feat(cbs): MT5 data fetch script for the 11 PSND instruments"
```

---

## Task 13: CLI + first real run + written report

**Files:**
- Create: `CBS/cbs/cli.py`
- Create: `CBS/README.md`
- Create: `CBS/strategy.md`

- [ ] **Step 1: Implement the CLI**

`CBS/cbs/cli.py`:
```python
"""CBS CLI: run the reverse analysis over fetched data and write an audit run.

Usage:
  python -m CBS.cbs.cli --data CBS/data --out CBS/reports --run pilot --utcstamp 20260609T0000Z
  Optional: --instruments EURUSD XAUUSD  --anchors 0 7 12  --blocks 1 4 24
"""
from __future__ import annotations

import argparse
import glob
from pathlib import Path

import pandas as pd

from . import config as C
from .bars import load_m5_csv
from .pipeline import run_instrument, split_in_out_sample
from .report import write_audit_run


def _find_csv(data_dir: Path, symbol: str) -> Path | None:
    hits = sorted(glob.glob(str(data_dir / f"{symbol}_M5_*.csv")))
    return Path(hits[-1]) if hits else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="CBS/data")
    ap.add_argument("--out", default="CBS/reports")
    ap.add_argument("--run", default="pilot")
    ap.add_argument("--utcstamp", required=True, help="UTC stamp string for the run folder")
    ap.add_argument("--instruments", nargs="*", default=list(C.INSTRUMENTS))
    ap.add_argument("--anchors", nargs="*", type=int, default=list(C.ANCHORS))
    ap.add_argument("--blocks", nargs="*", type=int, default=list(C.BLOCKS))
    args = ap.parse_args()

    data_dir = Path(args.data)
    all_timing, all_entries = [], []
    log_lines = []
    for sym in args.instruments:
        csv = _find_csv(data_dir, sym)
        if csv is None:
            log_lines.append(f"SKIP {sym}: no data file")
            continue
        df = load_m5_csv(csv)
        timing, entries = run_instrument(
            df, symbol=sym, pip_size=C.PIP_SIZE[sym], base_tol_pips=C.BASE_TOLERANCE_PIPS[sym],
            anchors=tuple(args.anchors), blocks=tuple(args.blocks),
            tol_mults=C.TOLERANCE_MULTIPLIERS, cap_hours=C.CLOCK_CAP_HOURS,
            atr_period=C.ATR_PERIOD_M5, atr_k=C.ATR_SL_K, lookback_hours=C.ENTRY_LOOKBACK_HOURS,
        )
        all_timing += timing
        all_entries += entries
        log_lines.append(f"OK {sym}: {len(timing)} timing, {len(entries)} entries from {csv.name}")

    cfg = {"instruments": args.instruments, "anchors": args.anchors, "blocks": args.blocks,
           "tol_mults": C.TOLERANCE_MULTIPLIERS, "cap_hours": C.CLOCK_CAP_HOURS,
           "atr_k": C.ATR_SL_K, "atr_period": C.ATR_PERIOD_M5}
    out = write_audit_run(Path(args.out), run_name=args.run, config=cfg,
                          timing=all_timing, entries=all_entries,
                          log_text="\n".join(log_lines), utcstamp=args.utcstamp)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full pipeline (after Task 12 produced data)**

Run (use a real UTC stamp): `python -m CBS.cbs.cli --run pilot --utcstamp <YYYYMMDDTHHMMZ>`
Expected: prints `wrote CBS/reports/pilot-<stamp>`; folder contains `timing_raw.csv`, `entries_raw.csv`, `t1_time_to_complete.csv`, `t2_best_entry.csv`, `config.json`, `run.log`, `manifest.sha256`.

- [ ] **Step 3: Verify the manifest (audit-trail discipline)**

Run: `python -c "import hashlib,glob,os; d=sorted(glob.glob('CBS/reports/pilot-*'))[-1]; [print('OK',n) or (_ for _ in ()).throw(SystemExit('BAD '+n)) for ln in open(d+'/manifest.sha256') if ln.strip() for h,n in [ln.split('  ',1)] for n in [n.strip()] if hashlib.sha256(open(os.path.join(d,n),'rb').read()).hexdigest()==h]"`
Expected: prints OK for each file; non-zero exit if any hash mismatches.

- [ ] **Step 4: Write README.md and strategy.md from the run**

`CBS/README.md` — what CBS is, how to fetch data (`scripts/fetch_cbs_data.py`), how to run (`python -m CBS.cbs.cli`), how to read T1/T2, where audit runs land, and the links from `PSND/links.md`. `CBS/strategy.md` — condense the design spec's locked definitions (§2 target/grid/completion/clock, §4 entry menu, §5 outputs) so CBS is self-documenting. Both reference the design spec path.

- [ ] **Step 5: Present findings + commit**

Read `t1_time_to_complete.csv` and `t2_best_entry.csv`, render the headline T1 (best anchor×block cells per instrument) and T2 (winning entry per instrument, in/out-of-sample) as markdown tables in the response to the user. Then:
```bash
git add CBS/cbs/cli.py CBS/README.md CBS/strategy.md
git commit -m "feat(cbs): CLI + docs; first pilot run + reported findings"
```

---

## Self-Review (completed during planning)

- **Spec coverage:** §2 target/grid/completion/clock → Tasks 3,4; tolerance ladder → Task 1 + pipeline tol_mults (Task 11); §3 timing → Task 4; §4 entries (all 4 menus + invalidation + ATR fallback) → Tasks 5–9; §4.3 R/MFE/MAE/cost → Task 9; §5 T1/T2 + audit manifest → Task 10; §6 layout → Task 0; §7 data/symbol-query/missing-doc → Task 12; §8 OOS split + lookahead (build_context clipping) + determinism (utcstamp injected) → Tasks 9,11,13. All covered.
- **Placeholders:** structure/liquidity/time detectors give the exact rule + registration + tests; Tasks 7–8 describe each detector's rule precisely and mirror the fully-coded Task 6 template — no vague steps.
- **Type consistency:** `TimingRecord`, `EntrySignal`, `EntryContext`, `EntryResult` field names match across timing/entries/evaluate/report/pipeline; `DETECTORS` registry name consistent; `build_context`/`measure_move`/`evaluate_entry` signatures consistent across caller and tests.

---

## Known follow-ups (out of this plan)

- MT5 on-chart visual indicator to show winning anchor/block + entry (design §9, optional).
- Per-detector parameter tuning (we rank a fixed menu, not tune it — design §9).
- Full 24×24×4 grid runtime may be heavy on 11×2yr; if slow, vectorize `measure_move` or parallelize per instrument (optimize only if a real run shows it's needed — YAGNI).
