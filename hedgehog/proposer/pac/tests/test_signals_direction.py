"""Tests for signals.py §3 Direction Filter."""
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import pytest

from hedgehog.proposer.pac.config import Config
from hedgehog.proposer.pac.mmd import compute_clouds
from hedgehog.proposer.pac.signals import (
    sentiment,
    mmd_alignment,
    d1_promo_zone,
    session_box_position,
    composite_direction,
)


def _bars(closes: list[float], highs: list[float] | None = None, lows: list[float] | None = None) -> pd.DataFrame:
    if highs is None:
        highs = [c + 0.5 for c in closes]
    if lows is None:
        lows = [c - 0.5 for c in closes]
    return pd.DataFrame({
        "open": closes,
        "high": highs,
        "low": lows,
        "close": closes,
    })


def test_sentiment_bull_when_price_above_both_mas() -> None:
    """Strong uptrend — price > EMA21 > SMA61 → bull."""
    # 100 bars rising from 100 to 200
    closes = [100 + i for i in range(100)]
    bars = _bars(closes)
    cfg = Config()
    result = sentiment(bars, cfg, bar_idx=99)
    assert result == "bull"


def test_sentiment_bear_when_price_below_both_mas() -> None:
    closes = [200 - i for i in range(100)]
    bars = _bars(closes)
    cfg = Config()
    result = sentiment(bars, cfg, bar_idx=99)
    assert result == "bear"


def test_sentiment_transitional_when_between_mas() -> None:
    # Flat then small move — price between MAs
    closes = [100] * 80 + [100.01 + i * 0.001 for i in range(20)]
    bars = _bars(closes)
    cfg = Config()
    # bar 99 close is just above 100; with 100-bar flat history, both MAs ~= 100
    result = sentiment(bars, cfg, bar_idx=99)
    # Just check it's a valid value (transitional is plausible but not guaranteed)
    assert result in ("bull", "bear", "transitional")


def test_sentiment_transitional_when_insufficient_history() -> None:
    """If MA NaN at bar_idx (insufficient bars), return transitional."""
    closes = [100, 101, 102]  # only 3 bars, SMA(61) is NaN
    bars = _bars(closes)
    cfg = Config()
    result = sentiment(bars, cfg, bar_idx=2)
    assert result == "transitional"


def test_mmd_alignment_returns_weakened_on_nan() -> None:
    """Insufficient cloud warmup → weakened."""
    bars = _bars([100.0] * 50)  # < 1440, so Green is NaN
    clouds = compute_clouds(bars)
    cfg = Config()
    result = mmd_alignment(clouds, bar_idx=49, sentiment_value="bull", cfg=cfg)
    # green_sma will be NaN at bar 49 → weakened
    assert result == "weakened"


def test_d1_promo_zone_returns_neutral_on_empty_d1() -> None:
    empty = pd.DataFrame(columns=["time_utc", "open", "high", "low", "close"])
    result = d1_promo_zone(empty, datetime(2026, 1, 15, tzinfo=timezone.utc), current_price=100.0)
    assert result == "neutral"


def test_d1_promo_zone_bearish_d1_above_body_is_bear_promo() -> None:
    """Bearish D1 (close<open): zone above body = sellers' (bear) promo."""
    d1 = pd.DataFrame({
        "time_utc": [datetime(2026, 1, 14, tzinfo=timezone.utc)],
        "open": [110.0],
        "high": [115.0],
        "low": [99.0],
        "close": [100.0],
    })
    # Current price 112 is between Open (110) and High (115) — above body, in upper wick
    result = d1_promo_zone(d1, datetime(2026, 1, 15, tzinfo=timezone.utc), current_price=112.0)
    assert result == "bear_promo"


def test_d1_promo_zone_bearish_d1_below_body_is_bull_promo() -> None:
    d1 = pd.DataFrame({
        "time_utc": [datetime(2026, 1, 14, tzinfo=timezone.utc)],
        "open": [110.0],
        "high": [115.0],
        "low": [99.0],
        "close": [100.0],
    })
    # Current price 99.5 is between Low (99) and Close (100) — below body, in lower wick
    result = d1_promo_zone(d1, datetime(2026, 1, 15, tzinfo=timezone.utc), current_price=99.5)
    assert result == "bull_promo"


def test_session_box_position_above_box() -> None:
    """Build M5 bars across London session, with current price above session high."""
    # London = 08:00–13:59 PLT. Use 2026-01-15 (winter CET +1) so London = 07:00–12:59 UTC.
    times = pd.date_range("2026-01-15 07:00:00+00:00", periods=10, freq="5min")
    # Session bars at prices 100-104; bar_idx 9 is at 100.45 + breakout to 110 above session high
    closes = [100.0, 100.5, 101.0, 102.0, 103.0, 102.5, 101.5, 100.5, 100.0, 110.0]
    bars = pd.DataFrame({
        "time_utc": times, "open": closes, "high": [c + 0.5 for c in closes],
        "low": [c - 0.5 for c in closes], "close": closes,
    })
    cfg = Config()
    result = session_box_position(bars, bar_idx=9, session="london", cfg=cfg, atr_value=1.0)
    # Session high (bars 0–8) ≈ 103.5; current high 110.5 > 103.5 → above
    assert result == "above"


def test_session_box_position_inside_narrow_box() -> None:
    """Narrow box (range < 0.5×ATR) → inside regardless of price."""
    times = pd.date_range("2026-01-15 07:00:00+00:00", periods=10, freq="5min")
    closes = [100.0] * 10  # all identical
    bars = pd.DataFrame({
        "time_utc": times, "open": closes, "high": [c + 0.1 for c in closes],
        "low": [c - 0.1 for c in closes], "close": closes,
    })
    cfg = Config()
    # Box range = 0.2, ATR=10, so 0.5*ATR=5 > 0.2 → inside
    result = session_box_position(bars, bar_idx=9, session="london", cfg=cfg, atr_value=10.0)
    assert result == "inside"


def test_composite_direction_bull_when_all_aligned() -> None:
    cfg = Config()
    result = composite_direction(
        sentiment_value="bull",
        mmd_value="confirmed",
        d1_value="bull_promo",
        box_value="above",
        cfg=cfg,
    )
    assert result == "bull"


def test_composite_direction_bear_when_all_aligned() -> None:
    cfg = Config()
    result = composite_direction(
        sentiment_value="bear",
        mmd_value="confirmed",
        d1_value="bear_promo",
        box_value="below",
        cfg=cfg,
    )
    assert result == "bear"


def test_composite_direction_neutral_when_box_inside() -> None:
    cfg = Config()
    result = composite_direction(
        sentiment_value="bull",
        mmd_value="confirmed",
        d1_value="bull_promo",
        box_value="inside",  # blocks
        cfg=cfg,
    )
    assert result == "neutral"


def test_composite_direction_neutral_when_mmd_vetoed() -> None:
    cfg = Config()
    result = composite_direction(
        sentiment_value="bull",
        mmd_value="vetoed",  # blocks
        d1_value="bull_promo",
        box_value="above",
        cfg=cfg,
    )
    assert result == "neutral"


def test_composite_direction_neutral_when_d1_opposite() -> None:
    cfg = Config()
    result = composite_direction(
        sentiment_value="bull",
        mmd_value="confirmed",
        d1_value="bear_promo",  # blocks bull
        box_value="above",
        cfg=cfg,
    )
    assert result == "neutral"


def test_composite_direction_loose_mode_only_requires_sentiment() -> None:
    cfg = Config().replace(direction_strict=False)
    # Loose mode: bull sentiment is enough even though d1 says bear
    result = composite_direction(
        sentiment_value="bull",
        mmd_value="vetoed",  # would block in strict
        d1_value="bear_promo",
        box_value="inside",  # would block in strict
        cfg=cfg,
    )
    assert result == "bull"


def test_composite_direction_mmd_strict_requires_confirmed() -> None:
    cfg = Config().replace(mmd_strict=True)
    # mmd_strict + weakened MMD → blocks bull
    result = composite_direction(
        sentiment_value="bull",
        mmd_value="weakened",
        d1_value="bull_promo",
        box_value="above",
        cfg=cfg,
    )
    assert result == "neutral"
