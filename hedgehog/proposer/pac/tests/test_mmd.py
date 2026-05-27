"""Tests for MMD cloud computation and alignment classification."""
from __future__ import annotations

import pandas as pd
import pytest

from hedgehog.proposer.pac.mmd import (
    CloudValues,
    compute_clouds,
    classify_alignment,
)


def _flat_bars(n: int, price: float = 1000.0) -> pd.DataFrame:
    return pd.DataFrame({
        "open": [price] * n,
        "high": [price] * n,
        "low": [price] * n,
        "close": [price] * n,
    })


def test_compute_clouds_on_flat_bars() -> None:
    """All MA-based clouds collapse to the constant price on a flat-price series."""
    bars = _flat_bars(2000)  # > 1440 to fully warm up Green
    clouds = compute_clouds(bars)
    assert isinstance(clouds, CloudValues)
    # Last bar — all three midpoints equal price
    assert clouds.orange_mid.iloc[-1] == pytest.approx(1000.0)
    assert clouds.blue_mid.iloc[-1] == pytest.approx(1000.0)
    assert clouds.green_mid.iloc[-1] == pytest.approx(1000.0)


def test_classify_alignment_confirmed_bull() -> None:
    """Orange > Blue > Green AND sentiment=bull → confirmed."""
    align = classify_alignment(
        orange_mid=1050.0,
        blue_mid=1040.0,
        green_mid=1030.0,
        sentiment="bull",
    )
    assert align == "confirmed"


def test_classify_alignment_confirmed_bear() -> None:
    """Green > Blue > Orange AND sentiment=bear → confirmed."""
    align = classify_alignment(
        orange_mid=1030.0,
        blue_mid=1040.0,
        green_mid=1050.0,
        sentiment="bear",
    )
    assert align == "confirmed"


def test_classify_alignment_vetoed_when_fully_opposite() -> None:
    """Orange < Blue < Green BUT sentiment=bull → vetoed."""
    align = classify_alignment(
        orange_mid=1030.0,
        blue_mid=1040.0,
        green_mid=1050.0,
        sentiment="bull",
    )
    assert align == "vetoed"


def test_classify_alignment_weakened_when_partial() -> None:
    """One cloud out of order → weakened."""
    align = classify_alignment(
        orange_mid=1050.0,
        blue_mid=1030.0,
        green_mid=1040.0,
        sentiment="bull",
    )
    assert align == "weakened"


def test_classify_alignment_transitional_returns_weakened() -> None:
    """Transitional sentiment is treated as weakened (safe default)."""
    align = classify_alignment(
        orange_mid=1050.0, blue_mid=1040.0, green_mid=1030.0,
        sentiment="transitional",
    )
    assert align == "weakened"


def test_compute_clouds_has_required_attributes() -> None:
    """CloudValues exposes orange/blue/green ema/sma/mid as pd.Series."""
    bars = _flat_bars(50)
    clouds = compute_clouds(bars)
    for attr in ("orange_ema", "orange_sma", "orange_mid", "blue_ema", "blue_sma", "blue_mid", "green_ema", "green_sma", "green_mid"):
        series = getattr(clouds, attr)
        assert isinstance(series, pd.Series)
