"""CSV bar reader for backtest inputs.

The CSV format is the canonical interchange format between MT5 history dumps
(produced by `tools/mt5_data.py dump-bars`) and the Python engine. Reading
through this module gives schema validation + UTC datetime parsing + typed
metadata so engine.py can rely on consistent input.

Schema (header row required):
    time_utc, open, high, low, close, tick_volume, real_volume, spread
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = ("time_utc", "open", "high", "low", "close", "tick_volume", "real_volume", "spread")


@dataclass
class BarsMetadata:
    symbol: str
    timeframe: str          # e.g., "M5"
    start_utc: datetime
    end_utc: datetime
    rows: int


def read_bars_csv(path: Path, symbol: str, timeframe: str) -> tuple[pd.DataFrame, BarsMetadata]:
    """Read a CSV produced by mt5_data.py dump-bars and return (DataFrame, metadata).

    Validates that all REQUIRED_COLUMNS are present and that types parse as expected.

    Raises:
        ValueError: if the file is empty or missing required columns.
    """
    path = Path(path)
    if path.stat().st_size == 0:
        raise ValueError(f"CSV file is empty: {path}")

    df = pd.read_csv(path)
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"CSV missing required column: {col!r}")

    # Parse time_utc as UTC datetime.
    df["time_utc"] = pd.to_datetime(df["time_utc"], utc=True)
    # Coerce volume + spread to int (CSV may have parsed as int already).
    for col in ("tick_volume", "real_volume", "spread"):
        df[col] = df[col].astype("int64")
    # Ensure prices are floats.
    for col in ("open", "high", "low", "close"):
        df[col] = df[col].astype("float64")

    # Compute metadata.
    if len(df) == 0:
        # Empty dataset (header only) — use a sentinel UTC datetime.
        start = end = datetime(1970, 1, 1, tzinfo=timezone.utc)
    else:
        start = df["time_utc"].iloc[0].to_pydatetime().astimezone(timezone.utc)
        end = df["time_utc"].iloc[-1].to_pydatetime().astimezone(timezone.utc)

    meta = BarsMetadata(symbol=symbol, timeframe=timeframe, start_utc=start, end_utc=end, rows=len(df))
    return df, meta
