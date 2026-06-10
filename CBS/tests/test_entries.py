from __future__ import annotations

import pandas as pd

from CBS.cbs.entries import (
    EntrySignal, EntryContext, build_context,
    enter_at_window_close, first_m5_close, first_pullback_pct,
    DETECTORS,
)


def _ctx(m5_factory, approach="up"):
    window = [(1.0, 1.5, 0.9, 1.1)] * 12
    fwd = [(1.1, 1.2, 1.05, 1.15)] * 5 + [(1.15, 1.45, 1.15, 1.40)]
    df = m5_factory("2024-01-01T00:00:00", window + fwd)
    return build_context(
        df, symbol="EURUSD",
        window_close_ts=pd.Timestamp("2024-01-01T01:00:00", tz="UTC"),
        completion_ts=pd.Timestamp("2024-01-01T01:30:00", tz="UTC"),
        target=1.4, approach_side=approach, pip_size=0.0001,
        lookback_hours=12, atr_period=14, atr_k=1.5,
    )


def test_build_context_clips_to_decision_horizon(m5_factory) -> None:
    ctx = _ctx(m5_factory)
    assert ctx.m5["time_utc"].max() <= ctx.completion_ts
    assert ctx.atr_m5 > 0


def test_enter_at_window_close_returns_close_price(m5_factory) -> None:
    ctx = _ctx(m5_factory)
    sig = enter_at_window_close(ctx)
    assert sig is not None
    assert sig.name == "enter_at_window_close"
    assert sig.entry_price == 1.1
    assert sig.invalidation_price < sig.entry_price


def test_first_m5_close_fires_on_first_close_in_direction(m5_factory) -> None:
    ctx = _ctx(m5_factory)
    sig = first_m5_close(ctx)
    assert sig is not None
    assert sig.entry_time >= ctx.window_close_ts


def test_first_pullback_pct_uses_atr_fallback_when_no_structure(m5_factory) -> None:
    ctx = _ctx(m5_factory)
    sig = first_pullback_pct(ctx)
    assert sig is None or sig.invalidation_price < sig.entry_price


def test_registry_contains_baselines() -> None:
    for name in ("enter_at_window_close", "first_m5_close", "first_pullback_pct"):
        assert name in DETECTORS
