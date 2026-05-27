"""Tests for bars.py — CSV bar reader."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from hedgehog.proposer.pac.bars import BarsMetadata, read_bars_csv


_VALID_CSV = """time_utc,open,high,low,close,tick_volume,real_volume,spread
2024-01-01T00:00:00,1.10500,1.10510,1.10495,1.10505,42,0,1
2024-01-01T00:05:00,1.10505,1.10520,1.10502,1.10518,38,0,1
2024-01-01T00:10:00,1.10518,1.10525,1.10510,1.10512,45,0,2
"""


def test_read_bars_csv_returns_dataframe_and_metadata(tmp_path: Path) -> None:
    p = tmp_path / "bars.csv"
    p.write_text(_VALID_CSV, encoding="utf-8")
    df, meta = read_bars_csv(p, symbol="EURUSD", timeframe="M5")
    assert isinstance(df, pd.DataFrame)
    assert isinstance(meta, BarsMetadata)
    assert len(df) == 3
    assert list(df.columns) == ["time_utc", "open", "high", "low", "close", "tick_volume", "real_volume", "spread"]


def test_read_bars_metadata_fields(tmp_path: Path) -> None:
    p = tmp_path / "bars.csv"
    p.write_text(_VALID_CSV, encoding="utf-8")
    _, meta = read_bars_csv(p, symbol="EURUSD", timeframe="M5")
    assert meta.symbol == "EURUSD"
    assert meta.timeframe == "M5"
    assert meta.rows == 3
    assert meta.start_utc == datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc)
    assert meta.end_utc == datetime(2024, 1, 1, 0, 10, tzinfo=timezone.utc)


def test_read_bars_csv_missing_required_column_raises(tmp_path: Path) -> None:
    # Missing 'high' column
    bad = """time_utc,open,low,close,tick_volume,real_volume,spread
2024-01-01T00:00:00,1.105,1.104,1.105,42,0,1
"""
    p = tmp_path / "bad.csv"
    p.write_text(bad, encoding="utf-8")
    with pytest.raises(ValueError, match="missing required column"):
        read_bars_csv(p, symbol="EURUSD", timeframe="M5")


def test_read_bars_csv_empty_file_raises(tmp_path: Path) -> None:
    p = tmp_path / "empty.csv"
    p.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        read_bars_csv(p, symbol="EURUSD", timeframe="M5")


def test_read_bars_csv_header_only_returns_empty_df(tmp_path: Path) -> None:
    """A file with header but no data rows is valid (empty dataset)."""
    p = tmp_path / "header_only.csv"
    p.write_text("time_utc,open,high,low,close,tick_volume,real_volume,spread\n", encoding="utf-8")
    df, meta = read_bars_csv(p, symbol="EURUSD", timeframe="M5")
    assert len(df) == 0
    assert meta.rows == 0


def test_read_bars_csv_dtypes_correct(tmp_path: Path) -> None:
    p = tmp_path / "bars.csv"
    p.write_text(_VALID_CSV, encoding="utf-8")
    df, _ = read_bars_csv(p, symbol="EURUSD", timeframe="M5")
    # time_utc parsed as datetime
    assert pd.api.types.is_datetime64_any_dtype(df["time_utc"])
    # Prices floats
    for col in ("open", "high", "low", "close"):
        assert pd.api.types.is_float_dtype(df[col])
    # Volumes ints
    for col in ("tick_volume", "real_volume", "spread"):
        assert pd.api.types.is_integer_dtype(df[col])
