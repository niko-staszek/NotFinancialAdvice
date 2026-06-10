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
    assert abs(row["median_hours"] - 3.0) < 1e-9


def test_build_t1_excludes_instant_from_speed_stats() -> None:
    # one instant (0.0) + one real (4.0): median must be 4.0, not 2.0
    recs = [_timing(instant=True, hours_to_complete=0.0),
            _timing(instant=False, hours_to_complete=4.0)]
    t1 = build_t1(recs)
    row = t1.iloc[0]
    assert abs(row["median_hours"] - 4.0) < 1e-9
    assert abs(row["instant_rate"] - 0.5) < 1e-9


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
    for line in manifest.read_text().splitlines():
        digest, name = line.split("  ", 1)
        data = (Path(out) / name).read_bytes()
        assert hashlib.sha256(data).hexdigest() == digest
