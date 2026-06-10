from __future__ import annotations

import pandas as pd

from CBS.cbs.entries import build_context, DETECTORS


def _ctx(m5_factory, window, fwd, lookback):
    full = lookback + window + fwd
    df = m5_factory("2024-01-01T00:00:00", full)
    base = pd.Timestamp("2024-01-01T00:00:00", tz="UTC")
    return build_context(
        df, symbol="EURUSD",
        window_close_ts=base + pd.Timedelta(minutes=5 * (len(lookback) + len(window))),
        completion_ts=base + pd.Timedelta(minutes=5 * (len(full) - 1)),
        target=1.4, approach_side="up", pip_size=0.0001,
        lookback_hours=24, atr_period=14, atr_k=1.5,
    )


def test_opening_range_break_registered(m5_factory) -> None:
    assert "opening_range_break" in DETECTORS
    window = [(1.10, 1.16, 1.08, 1.14)] * 12
    fwd = [(1.14, 1.18, 1.12, 1.16)] * 12
    fwd += [(1.16, 1.25, 1.16, 1.22)]
    fwd += [(1.22, 1.23, 1.17, 1.19)]
    fwd += [(1.19, 1.45, 1.19, 1.40)]
    ctx = _ctx(m5_factory, window, fwd, [(1.0, 1.05, 0.95, 1.0)] * 288)
    sig = DETECTORS["opening_range_break"](ctx)
    assert sig is None or sig.invalidation_price < sig.entry_price


def test_session_open_retrace_registered(m5_factory) -> None:
    assert "session_open_retrace" in DETECTORS


def test_prior_level_and_round_number_registered() -> None:
    assert "prior_level_react" in DETECTORS
    assert "round_number" in DETECTORS
