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
    cols = ["time_utc", "open", "high", "low", "close", "tick_volume", "real_volume", "spread"]
    df = pd.DataFrame(recs, columns=cols)
    if not df.empty:
        df["time_utc"] = pd.to_datetime(df["time_utc"], utc=True)
    return df


@pytest.fixture
def m5_factory():
    return make_m5
