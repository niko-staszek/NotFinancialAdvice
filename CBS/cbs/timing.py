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
    scanned = len(fwd)
    if len(fwd):
        # Vectorized first-touch: band overlap (low-tol <= target <= high+tol).
        lows = fwd["low"].to_numpy()
        highs = fwd["high"].to_numpy()
        touch = (lows - tol_price <= tgt.value) & (tgt.value <= highs + tol_price)
        if touch.any():
            idx = int(touch.argmax())
            completed = True
            instant = (idx == 0)
            scanned = idx + 1
            if instant:
                hours = 0.0
            else:
                bar_close_ts = fwd["time_utc"].iloc[idx] + timedelta(minutes=5)
                hours = (bar_close_ts - close_ts).total_seconds() / 3600.0

    return TimingRecord(
        symbol=symbol, date=date, anchor=anchor, block=block, tol_mult=tol_mult,
        target=tgt.value, approach_side=tgt.approach_side, completed=completed,
        instant=instant, hours_to_complete=hours,
        window_close_price=tgt.window_close_price, bars_scanned=scanned,
    )
