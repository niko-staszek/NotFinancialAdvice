from __future__ import annotations

import pandas as pd

from CBS.cbs.target import Target, compute_target


def test_target_is_high_plus_low_minus_open(m5_factory) -> None:
    df = m5_factory("2024-01-01T00:00:00", [
        (1.0, 1.2, 0.9, 1.1),
        (1.1, 1.8, 0.5, 1.3),
        (1.3, 1.4, 1.0, 1.2),
    ])
    t = compute_target(df)
    assert t.value == 1.8 + 0.5 - 1.0
    assert t.window_open == 1.0
    assert t.window_close_price == 1.2


def test_approach_side_up_when_target_above_close(m5_factory) -> None:
    df = m5_factory("2024-01-01T00:00:00", [(1.0, 2.0, 1.0, 1.2)])
    t = compute_target(df)
    assert t.approach_side == "up"


def test_approach_side_down_when_target_below_close(m5_factory) -> None:
    df = m5_factory("2024-01-01T00:00:00", [(2.0, 2.1, 1.0, 1.9)])
    t = compute_target(df)
    assert t.approach_side == "down"


def test_empty_window_raises(m5_factory) -> None:
    import pytest
    df = m5_factory("2024-01-01T00:00:00", [])
    with pytest.raises(ValueError):
        compute_target(df)
