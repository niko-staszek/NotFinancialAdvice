from __future__ import annotations

import pandas as pd

from CBS.cbs.pipeline import run_instrument, split_in_out_sample


def test_split_in_out_sample_tags_last_6mo() -> None:
    dates = pd.to_datetime(["2024-01-01", "2024-04-01", "2024-09-01", "2024-12-01"])
    df = pd.DataFrame({"date": dates})
    tagged = split_in_out_sample(df, oos_months=6, date_col="date")
    assert set(tagged["split"]) == {"in_sample", "oos"}
    oos_dates = set(tagged.loc[tagged["split"] == "oos", "date"].dt.strftime("%Y-%m-%d"))
    assert oos_dates == {"2024-09-01", "2024-12-01"}


def test_run_instrument_smoke(m5_factory) -> None:
    rows = []
    for d in range(2):
        day = [(1.0 + 0.001 * (i % 10), 1.0 + 0.001 * (i % 10) + 0.005,
                1.0 + 0.001 * (i % 10) - 0.005, 1.0 + 0.001 * (i % 10)) for i in range(288)]
        rows += day
    df = m5_factory("2024-01-01T00:00:00", rows)
    timing, entries = run_instrument(
        df, symbol="EURUSD", pip_size=0.0001, base_tol_pips=5,
        anchors=(0,), blocks=(1,), tol_mults=(1, 2), cap_hours=48,
        atr_period=14, atr_k=1.5, lookback_hours=12,
    )
    assert isinstance(timing, list)
    assert isinstance(entries, list)
    assert all(t.symbol == "EURUSD" for t in timing)


def test_run_instrument_skips_window_with_gapped_context(m5_factory) -> None:
    # A 2h window [00:00,02:00) has bars only in its first hour, then a market gap
    # (no 01:00-01:55 bars), then completion bars after 02:00. With lookback=1h the
    # entry context [01:00, completion] has no pre-window bar — the window must be
    # skipped, not crash _window_close_bar with an empty .iloc[-1].
    window_first_hour = m5_factory("2025-01-01T00:00:00", [(2000.0, 2010.0, 1995.0, 2000.0)] * 12)
    # target = 2010 + 1995 - 2000 = 2005 (> close 2000 -> approach up)
    fwd = m5_factory("2025-01-01T02:00:00",
                     [(2000.0, 2001.0, 1999.0, 2000.0)] * 3      # below target -> not instant
                     + [(2000.0, 2006.0, 2000.0, 2005.0)] * 3)   # touches 2005
    df = pd.concat([window_first_hour, fwd], ignore_index=True)
    timing, entries = run_instrument(
        df, symbol="XAUUSD", pip_size=0.1, base_tol_pips=15,
        anchors=(0,), blocks=(2,), tol_mults=(1,), cap_hours=48,
        atr_period=14, atr_k=1.5, lookback_hours=1,
    )
    # Must complete without raising; the gapped window yields no evaluable entries.
    assert entries == []
    assert any(t.completed for t in timing)
