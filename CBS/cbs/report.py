"""T1/T2 table builders + audit-trail run writer (design §5).

build_t1: per (symbol, anchor, block, tol_mult) — completion_rate, instant_rate, and
hours percentiles. Hours stats are computed over COMPLETED, NON-INSTANT moves only,
so 'already-settled' instant touches (hours=0) and never-completed (NaN) do not
distort the speed picture. n / completion_rate / instant_rate cover the full group.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

import pandas as pd

from .timing import TimingRecord
from .evaluate import EntryResult

_KEYS = ["symbol", "anchor", "block", "tol_mult"]


def build_t1(records: Sequence[TimingRecord]) -> pd.DataFrame:
    df = pd.DataFrame([asdict(r) for r in records])
    base = df.groupby(_KEYS, as_index=False).agg(
        n=("completed", "size"),
        completion_rate=("completed", "mean"),
        instant_rate=("instant", "mean"),
    )
    speed_src = df[df["completed"] & ~df["instant"]]
    if len(speed_src):
        speed = speed_src.groupby(_KEYS, as_index=False).agg(
            completed_n=("hours_to_complete", "size"),
            median_hours=("hours_to_complete", "median"),
            p25_hours=("hours_to_complete", lambda s: s.quantile(0.25)),
            p75_hours=("hours_to_complete", lambda s: s.quantile(0.75)),
        )
        out = base.merge(speed, on=_KEYS, how="left")
    else:
        out = base.assign(completed_n=0, median_hours=float("nan"),
                          p25_hours=float("nan"), p75_hours=float("nan"))
    return out


def build_t2(records: Sequence[EntryResult]) -> pd.DataFrame:
    df = pd.DataFrame([asdict(r) for r in records])
    df = df[df["realized_r"].notna()].copy()
    grp = df.groupby(["symbol", "name"], as_index=False)
    out = grp.agg(
        n=("win", "size"),
        expectancy_r=("realized_r", "mean"),
        win_rate=("win", "mean"),
        avg_planned_rr=("r_multiple", "mean"),
        median_mae_r=("mae_r", "median"),
        median_lead_hours=("entry_lead_hours", "median"),
    )
    out = out.sort_values(["symbol", "expectancy_r"], ascending=[True, False]).reset_index(drop=True)
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

    lines = []
    for p in sorted(out.glob("*")):
        if p.name == "manifest.sha256":
            continue
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        lines.append(f"{digest}  {p.name}")
    (out / "manifest.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
