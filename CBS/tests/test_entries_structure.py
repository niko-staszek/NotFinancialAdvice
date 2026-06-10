from __future__ import annotations

import pandas as pd

from CBS.cbs.entries import build_context, DETECTORS


def _df_ctx(m5_factory, window, fwd, lookback=None):
    lookback = lookback or []
    full = lookback + window + fwd
    df = m5_factory("2024-01-01T00:00:00", full)
    n_pre = len(lookback)
    close_min = 5 * (n_pre + len(window))
    comp_min = 5 * (len(full) - 1)
    base = pd.Timestamp("2024-01-01T00:00:00", tz="UTC")
    return build_context(
        df, symbol="EURUSD",
        window_close_ts=base + pd.Timedelta(minutes=close_min),
        completion_ts=base + pd.Timedelta(minutes=comp_min),
        target=1.4, approach_side="up", pip_size=0.0001,
        lookback_hours=24, atr_period=14, atr_k=1.5,
    )


def test_sr_retest_fires_on_pdh_break_and_retest(m5_factory) -> None:
    lookback = [(1.0, 1.20, 0.95, 1.10)] * 288       # 24h prior, PDH=1.20
    window = [(1.10, 1.15, 1.05, 1.12)] * 12
    fwd = [(1.12, 1.25, 1.12, 1.22)]                  # break above 1.20
    fwd += [(1.22, 1.23, 1.20, 1.21)]                 # retest 1.20
    fwd += [(1.21, 1.45, 1.21, 1.40)]                 # to target
    ctx = _df_ctx(m5_factory, window, fwd, lookback)
    sig = DETECTORS["sr_retest"](ctx)
    assert sig is not None
    assert abs(sig.entry_price - 1.20) < 1e-9
    assert sig.invalidation_price < sig.entry_price


def test_fvg_fill_fires_when_gap_revisited(m5_factory) -> None:
    window = [(1.10, 1.15, 1.05, 1.12)] * 12
    fwd = [(1.12, 1.20, 1.12, 1.19)]
    fwd += [(1.19, 1.30, 1.19, 1.28)]
    fwd += [(1.28, 1.32, 1.25, 1.27)]
    fwd += [(1.27, 1.27, 1.22, 1.24)]   # trades back into gap (<=1.25)
    fwd += [(1.24, 1.45, 1.24, 1.40)]
    ctx = _df_ctx(m5_factory, window, fwd, [(1.0, 1.05, 0.95, 1.0)] * 288)
    sig = DETECTORS["fvg_fill"](ctx)
    assert sig is not None
    assert sig.invalidation_price < sig.entry_price


def test_swing_retest_registered_and_callable(m5_factory) -> None:
    assert "swing_retest" in DETECTORS
    window = [(1.10, 1.15, 1.05, 1.12)] * 12
    fwd = [(1.12, 1.30, 1.12, 1.28)] + [(1.28, 1.29, 1.18, 1.20)] + [(1.20, 1.45, 1.20, 1.40)]
    ctx = _df_ctx(m5_factory, window, fwd, [(1.0, 1.18, 0.95, 1.0)] * 288)
    sig = DETECTORS["swing_retest"](ctx)
    assert sig is None or sig.invalidation_price < sig.entry_price


def test_ema21_retest_and_fib_cluster_registered() -> None:
    assert "ema21_retest" in DETECTORS
    assert "fib_cluster" in DETECTORS
