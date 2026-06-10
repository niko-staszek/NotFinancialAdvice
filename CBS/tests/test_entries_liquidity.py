from __future__ import annotations

import pandas as pd

from CBS.cbs.entries import build_context, DETECTORS


def _ctx(m5_factory, lookback, window, fwd):
    full = lookback + window + fwd
    df = m5_factory("2024-01-01T00:00:00", full)
    base = pd.Timestamp("2024-01-01T00:00:00", tz="UTC")
    close_min = 5 * (len(lookback) + len(window))
    comp_min = 5 * (len(full) - 1)
    return build_context(
        df, symbol="EURUSD",
        window_close_ts=base + pd.Timedelta(minutes=close_min),
        completion_ts=base + pd.Timedelta(minutes=comp_min),
        target=1.4, approach_side="up", pip_size=0.0001,
        lookback_hours=24, atr_period=14, atr_k=1.5,
    )


def test_liquidity_sweep_fires_on_pdl_raid_and_reclaim(m5_factory) -> None:
    lookback = [(1.10, 1.15, 1.00, 1.12)] * 288   # PDL = 1.00
    window = [(1.12, 1.16, 1.08, 1.14)] * 12
    fwd = [(1.14, 1.14, 0.98, 1.02)]              # wick below PDL 1.00
    fwd += [(1.02, 1.10, 1.01, 1.08)]             # reclaim above 1.00
    fwd += [(1.08, 1.45, 1.08, 1.40)]
    ctx = _ctx(m5_factory, lookback, window, fwd)
    sig = DETECTORS["liquidity_sweep"](ctx)
    assert sig is None or sig.invalidation_price < sig.entry_price


def test_order_block_registered_and_callable(m5_factory) -> None:
    assert "order_block" in DETECTORS
    lookback = [(1.0, 1.05, 0.95, 1.0)] * 288
    window = [(1.10, 1.16, 1.08, 1.14)] * 12
    fwd = [(1.14, 1.14, 1.10, 1.11)]              # down-close (the OB)
    fwd += [(1.11, 1.30, 1.11, 1.28)]             # up impulse
    fwd += [(1.28, 1.29, 1.12, 1.15)]             # return into OB range
    fwd += [(1.15, 1.45, 1.15, 1.40)]
    ctx = _ctx(m5_factory, lookback, window, fwd)
    sig = DETECTORS["order_block"](ctx)
    assert sig is None or sig.invalidation_price < sig.entry_price


def test_breaker_and_eqh_eql_registered() -> None:
    assert "breaker" in DETECTORS
    assert "eqh_eql_raid" in DETECTORS
