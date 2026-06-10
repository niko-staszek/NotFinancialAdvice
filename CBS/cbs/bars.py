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
    """Return bars with start <= time_utc < end (half-open).

    Uses searchsorted on the time-sorted frame (O(log n)) instead of a full
    boolean mask (O(n)) — this is the hot path, called once per grid cell.
    Requires df sorted ascending by time_utc (load_m5_csv guarantees this).
    """
    s = df["time_utc"]
    lo = int(s.searchsorted(start, side="left"))
    hi = int(s.searchsorted(end, side="left"))
    return df.iloc[lo:hi].reset_index(drop=True)


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
