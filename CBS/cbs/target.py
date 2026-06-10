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
