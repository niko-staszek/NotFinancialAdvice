from __future__ import annotations

import math

import pandas as pd

from CBS.cbs.entries import EntrySignal, build_context
from CBS.cbs.evaluate import evaluate_entry


def _ctx(m5_factory):
    window = [(1.0, 1.5, 0.9, 1.1)] * 12
    fwd = [(1.1, 1.2, 1.05, 1.15)] * 5 + [(1.15, 1.45, 1.15, 1.40)]
    df = m5_factory("2024-01-01T00:00:00", window + fwd)
    return build_context(
        df, symbol="EURUSD",
        window_close_ts=pd.Timestamp("2024-01-01T01:00:00", tz="UTC"),
        completion_ts=pd.Timestamp("2024-01-01T01:30:00", tz="UTC"),
        target=1.4, approach_side="up", pip_size=0.0001,
        lookback_hours=12, atr_period=14, atr_k=1.5,
    )


def test_r_multiple_long_win(m5_factory) -> None:
    ctx = _ctx(m5_factory)
    sig = EntrySignal("x", entry_price=1.10, invalidation_price=1.00,
                      entry_time=pd.Timestamp("2024-01-01T01:00:00", tz="UTC"))
    res = evaluate_entry(ctx, sig, date="2024-01-01", anchor=0, block=1)
    assert math.isclose(res.r_multiple, 3.0, rel_tol=1e-9)
    assert res.win is True
    assert res.mae_r <= 0


def test_loss_when_invalidation_hit_before_target(m5_factory) -> None:
    ctx = _ctx(m5_factory)
    sig = EntrySignal("x", entry_price=1.10, invalidation_price=1.06,
                      entry_time=pd.Timestamp("2024-01-01T01:00:00", tz="UTC"))
    res = evaluate_entry(ctx, sig, date="2024-01-01", anchor=0, block=1)
    assert res.win is False


def test_no_sl_room_returns_nan_r(m5_factory) -> None:
    ctx = _ctx(m5_factory)
    sig = EntrySignal("x", entry_price=1.10, invalidation_price=1.10,
                      entry_time=pd.Timestamp("2024-01-01T01:00:00", tz="UTC"))
    res = evaluate_entry(ctx, sig, date="2024-01-01", anchor=0, block=1)
    assert math.isnan(res.r_multiple)
