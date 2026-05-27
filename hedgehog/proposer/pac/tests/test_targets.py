"""Tests for targets.py §5 Target Engine."""
from __future__ import annotations

import pandas as pd
import pytest

from hedgehog.proposer.pac.config import Config
from hedgehog.proposer.pac.helpers.swing import Swing
from hedgehog.proposer.pac.targets import (
    MeasuredMove,
    detect_measured_moves,
    fibonacci_levels,
    find_clusters,
    extended_mm_target,
    apply_settle_buffer,
)


def test_measured_move_dataclass_fields() -> None:
    mm = MeasuredMove(
        id=1, direction="bull",
        a_bar=10, a_price=100.0,
        b_bar=20, b_price=110.0,
        c_bar=25, c_price=104.0,
        d_target=114.0, validity="valid",
    )
    assert mm.id == 1
    assert mm.direction == "bull"
    assert mm.overshoot_bars == 0


def test_detect_measured_moves_bull_pattern() -> None:
    """Construct bars + swings that form a clean bull A→B→C, expect 1 MM."""
    # 100 bars with EMA computable (close 95 first 50, rising to 115 by bar 70, dropping to 105 by bar 80)
    closes = [95.0] * 30 + [95.0 + 0.5 * i for i in range(40)] + [115.0 - 0.5 * i for i in range(20)] + [105.0] * 10
    bars = pd.DataFrame({
        "open": closes, "high": [c + 1 for c in closes],
        "low": [c - 1 for c in closes], "close": closes,
    })
    ema_series = bars["close"].ewm(span=21, adjust=False).mean()
    # Pre-construct swings: low at idx 29, high at idx 69, low at idx 79
    swings = [
        Swing(bar_idx=29, price=94.0, kind="low"),
        Swing(bar_idx=69, price=116.0, kind="high"),
        Swing(bar_idx=79, price=105.0, kind="low"),
    ]
    cfg = Config()
    mms = detect_measured_moves(bars, swings, ema_series, cfg)
    # Should detect at least one bull MM with A=29, B=69, C=79
    bull_mms = [m for m in mms if m.direction == "bull"]
    assert len(bull_mms) >= 1
    mm = bull_mms[0]
    assert mm.d_target == pytest.approx(105.0 + (116.0 - 94.0))  # = 127


def test_detect_measured_moves_empty_swings() -> None:
    bars = pd.DataFrame({"open": [100.0], "high": [101.0], "low": [99.0], "close": [100.0]})
    ema = bars["close"].ewm(span=21, adjust=False).mean()
    cfg = Config()
    assert detect_measured_moves(bars, [], ema, cfg) == []


def test_fibonacci_levels_bull_mm() -> None:
    mm = MeasuredMove(
        id=1, direction="bull",
        a_bar=10, a_price=100.0, b_bar=20, b_price=110.0,
        c_bar=25, c_price=104.0, d_target=114.0, validity="valid",
    )
    bars = pd.DataFrame({"open": [100.0], "high": [101.0], "low": [99.0], "close": [100.0]})
    cfg = Config()
    levels = fibonacci_levels(bars, [mm], cfg)
    # AB span = 10 (100→110). Retracement levels at 0.382, 0.5, 0.618:
    # 100 + 0.382*10 = 103.82, 100 + 0.5*10 = 105.0, 100 + 0.618*10 = 106.18
    prices = [lev[0] for lev in levels]
    assert any(abs(p - 103.82) < 0.01 for p in prices)
    assert any(abs(p - 105.0) < 0.01 for p in prices)
    assert any(abs(p - 106.18) < 0.01 for p in prices)


def test_fibonacci_levels_no_active_mms() -> None:
    bars = pd.DataFrame({"open": [100.0], "high": [101.0], "low": [99.0], "close": [100.0]})
    cfg = Config()
    assert fibonacci_levels(bars, [], cfg) == []


def test_find_clusters_groups_nearby_levels() -> None:
    # 3 levels: 100.0, 100.2, 105.0. ATR=10, threshold=0.3*10=3.
    # 100.0 and 100.2 are within 3 → cluster. 105.0 is alone.
    levels = [(100.0, "fib_R_0.5"), (100.2, "fib_R_0.618"), (105.0, "fib_E_1.382")]
    cfg = Config()
    clusters = find_clusters(levels, atr_value=10.0, cfg=cfg)
    assert len(clusters) == 1
    # Cluster price ≈ 100.1, has 2 members
    cluster_price, members = clusters[0]
    assert cluster_price == pytest.approx(100.1, abs=0.01)
    assert len(members) == 2


def test_find_clusters_below_min_members_no_cluster() -> None:
    # cluster_member_min=2; only one level → no cluster
    levels = [(100.0, "fib_R_0.5")]
    cfg = Config()
    clusters = find_clusters(levels, atr_value=10.0, cfg=cfg)
    assert clusters == []


def test_extended_mm_target_returns_none_before_overshoot() -> None:
    mm = MeasuredMove(
        id=1, direction="bull",
        a_bar=10, a_price=100.0, b_bar=20, b_price=110.0,
        c_bar=25, c_price=104.0, d_target=114.0, validity="valid",
        overshoot_bars=0,
    )
    bars = pd.DataFrame({"open": [100.0], "high": [101.0], "low": [99.0], "close": [100.0]})
    cfg = Config()
    assert extended_mm_target(mm, bars, cfg) is None


def test_extended_mm_target_returns_138_after_overshoot() -> None:
    mm = MeasuredMove(
        id=1, direction="bull",
        a_bar=10, a_price=100.0, b_bar=20, b_price=110.0,
        c_bar=25, c_price=104.0, d_target=114.0, validity="valid",
        overshoot_bars=5,  # >= cfg.overshoot_bars_min (3)
    )
    bars = pd.DataFrame({"open": [100.0], "high": [101.0], "low": [99.0], "close": [100.0]})
    cfg = Config()
    target = extended_mm_target(mm, bars, cfg)
    # Extended target = c_price + 1.382 * (b_price - a_price) = 104 + 1.382*10 = 117.82
    assert target == pytest.approx(117.82, abs=0.01)


def test_apply_settle_buffer_bull_pulls_target_down() -> None:
    cfg = Config()
    # settle_buffer = 0.5 * 10 = 5; bull target 100 → 100 - 5 = 95
    assert apply_settle_buffer(100.0, "bull", atr_value=10.0, cfg=cfg) == 95.0


def test_apply_settle_buffer_bear_pushes_target_up() -> None:
    cfg = Config()
    # bear target 100 → 100 + 5 = 105
    assert apply_settle_buffer(100.0, "bear", atr_value=10.0, cfg=cfg) == 105.0
