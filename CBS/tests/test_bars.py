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


def test_slice_window_matches_boolean_mask(m5_factory) -> None:
    # searchsorted slice must equal the naive boolean-mask result, including for
    # start/end that fall strictly between bar timestamps.
    df = m5_factory("2024-01-01T00:00:00", [(i, i + 1, i - 1, i) for i in range(100)])
    for start_min, end_min in [(0, 60), (12, 47), (3, 3), (95, 200), (-10, 5)]:
        base = pd.Timestamp("2024-01-01T00:00:00", tz="UTC")
        start = base + timedelta(minutes=start_min) + timedelta(seconds=30)  # off-grid
        end = base + timedelta(minutes=end_min) + timedelta(seconds=30)
        got = slice_window(df, start, end)
        ref = df.loc[(df["time_utc"] >= start) & (df["time_utc"] < end)].reset_index(drop=True)
        pd.testing.assert_frame_equal(got, ref)
