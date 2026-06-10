from __future__ import annotations

import math
from datetime import timedelta

import pandas as pd

from CBS.cbs.timing import TimingRecord, measure_move


def _window(m5_factory):
    pre = [(1.0, 1.5, 0.9, 1.1)] * 12
    return pre


def test_completes_when_price_touches_target_within_tolerance(m5_factory) -> None:
    rows = _window(m5_factory)
    rows += [(1.1, 1.2, 1.05, 1.15)] * 6
    rows += [(1.15, 1.399, 1.15, 1.30)]
    df = m5_factory("2024-01-01T00:00:00", rows)
    rec = measure_move(df, symbol="EURUSD", anchor=0, block=1, tol_price=0.05,
                       cap_hours=48, date="2024-01-01")
    assert rec.completed is True
    assert rec.instant is False
    assert math.isclose(rec.hours_to_complete, 35 / 60, rel_tol=1e-6)


def test_instant_when_first_post_window_bar_already_within_tolerance(m5_factory) -> None:
    rows = _window(m5_factory)
    rows += [(1.38, 1.41, 1.38, 1.40)]
    df = m5_factory("2024-01-01T00:00:00", rows)
    rec = measure_move(df, symbol="EURUSD", anchor=0, block=1, tol_price=0.05,
                       cap_hours=48, date="2024-01-01")
    assert rec.completed is True
    assert rec.instant is True
    assert rec.hours_to_complete == 0.0


def test_not_completed_when_target_never_reached_within_cap(m5_factory) -> None:
    rows = _window(m5_factory)
    rows += [(1.1, 1.2, 1.05, 1.15)] * 6
    df = m5_factory("2024-01-01T00:00:00", rows)
    rec = measure_move(df, symbol="EURUSD", anchor=0, block=1, tol_price=0.05,
                       cap_hours=48, date="2024-01-01")
    assert rec.completed is False
    assert math.isnan(rec.hours_to_complete)
