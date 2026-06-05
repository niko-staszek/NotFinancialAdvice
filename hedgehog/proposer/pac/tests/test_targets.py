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
    """Construct bars + swings that form a clean bull A→B→C, expect 1 MM.

    NOTE (Defect-1 fix): the EMA-cross anchor now uses the bar CLOSE at each
    pivot, not the swing wick price (§5.1). The original fixture started flat
    at 95.0 so the EMA equalled the close exactly at bar A (close == EMA, which
    is NOT "begun on one side of EMA") — it only passed under the old wick-based
    check. The price path below is reshaped so the bar at A genuinely CLOSES
    below EMA, B CLOSES above EMA, and C CLOSES back below EMA, while keeping the
    same swing pivots (94 / 116 / 105) and hence the same d_target (127). The
    post-C path resumes upward (never dips below C, reaches D) so the MM is
    cleanly valid.
    """
    closes = (
        [100.0 - 0.2 * i for i in range(30)]      # bars 0..29: decline into A (low)
        + [94.0 + 0.55 * i for i in range(40)]    # bars 30..69: rise to B (high)
        + [115.5 - 0.55 * i for i in range(10)]   # bars 70..79: pull back to C (low)
        + [110.0 + 2.0 * i for i in range(20)]    # bars 80..99: resume up, reach D
    )
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
    assert mm.validity == "valid"


def test_detect_measured_moves_empty_swings() -> None:
    bars = pd.DataFrame({"open": [100.0], "high": [101.0], "low": [99.0], "close": [100.0]})
    ema = bars["close"].ewm(span=21, adjust=False).mean()
    cfg = Config()
    assert detect_measured_moves(bars, [], ema, cfg) == []


# ---------------------------------------------------------------------------
# Defect 1 — §5.1 EMA-cross must use the bar CLOSE, not the swing wick.
# "Wicks that merely touch the EMA do not count — the bar at point B must
#  close on the opposite side from where the impulse started at point A."
# ---------------------------------------------------------------------------

def _flat_ema_bars(n: int, ema_level: float) -> tuple[pd.DataFrame, pd.Series]:
    """Helper: build n bars with a flat EMA at `ema_level`.

    Bars are placeholders (overwritten per-test for the A/B/C pivots). ATR is
    derived from the bar ranges, so each test sets generous ranges at the
    pivots to clear impulse_atr_multiple_min.
    """
    closes = [ema_level] * n
    bars = pd.DataFrame({
        "open": list(closes),
        "high": [c + 0.5 for c in closes],
        "low": [c - 0.5 for c in closes],
        "close": list(closes),
    })
    ema = pd.Series([ema_level] * n, dtype="float64")
    return bars, ema


def test_detect_measured_moves_wick_only_cross_rejected() -> None:
    """B's wick pierces above EMA but its CLOSE stays below → NOT a valid MM.

    SPEC-correct behavior (§5.1): the EMA-cross anchor is on the bar close,
    so a wick-only cross at B must NOT produce a measured move.
    """
    n = 90
    ema_level = 100.0
    bars, ema = _flat_ema_bars(n, ema_level)

    # A pivot (bar 30): a clear low — close BELOW EMA (correct side for bull A).
    a_idx = 30
    bars.loc[a_idx, ["open", "high", "low", "close"]] = [90.0, 91.0, 88.0, 90.0]
    # B pivot (bar 60): swing wick HIGH = 116 (above EMA) but CLOSE = 99 (BELOW EMA).
    #   Old buggy code used the wick (116 > 100) → admitted the cross.
    #   Spec-correct code uses close (99 < 100) → rejects the cross.
    b_idx = 60
    bars.loc[b_idx, ["open", "high", "low", "close"]] = [99.0, 116.0, 98.0, 99.0]
    # C pivot (bar 75): a low close below EMA, above A.
    c_idx = 75
    bars.loc[c_idx, ["open", "high", "low", "close"]] = [95.0, 96.0, 94.0, 95.0]

    swings = [
        Swing(bar_idx=a_idx, price=88.0, kind="low"),   # wick low
        Swing(bar_idx=b_idx, price=116.0, kind="high"),  # wick high (touches above EMA)
        Swing(bar_idx=c_idx, price=94.0, kind="low"),
    ]
    cfg = Config()
    mms = detect_measured_moves(bars, swings, ema, cfg)
    bull_mms = [m for m in mms if m.direction == "bull"]
    assert bull_mms == [], (
        "wick-only EMA cross at B must not produce an MM "
        "(close stayed on A's side of EMA)"
    )


def test_detect_measured_moves_close_cross_accepted() -> None:
    """B's CLOSE crosses above EMA → valid MM (close-anchored, sanity guard)."""
    n = 90
    ema_level = 100.0
    bars, ema = _flat_ema_bars(n, ema_level)

    a_idx = 30
    bars.loc[a_idx, ["open", "high", "low", "close"]] = [90.0, 91.0, 88.0, 90.0]
    # B: close = 112 ABOVE EMA (genuine cross).
    b_idx = 60
    bars.loc[b_idx, ["open", "high", "low", "close"]] = [111.0, 116.0, 110.0, 112.0]
    # C: close = 95 back below EMA, above A.
    c_idx = 75
    bars.loc[c_idx, ["open", "high", "low", "close"]] = [95.0, 96.0, 94.0, 95.0]

    swings = [
        Swing(bar_idx=a_idx, price=88.0, kind="low"),
        Swing(bar_idx=b_idx, price=116.0, kind="high"),
        Swing(bar_idx=c_idx, price=94.0, kind="low"),
    ]
    cfg = Config()
    mms = detect_measured_moves(bars, swings, ema, cfg)
    bull_mms = [m for m in mms if m.direction == "bull"]
    assert len(bull_mms) >= 1, "genuine close-cross at B should produce an MM"


# ---------------------------------------------------------------------------
# Defect 2 — §5.1 C-breach invalidation must fire from history.
# "The measured move is INVALID if price retraces beyond C before reaching D."
# ---------------------------------------------------------------------------

def test_detect_measured_moves_c_breach_marks_invalid() -> None:
    """Bull MM: price prints a low below C before reaching D → validity='invalid'."""
    n = 90
    ema_level = 100.0
    bars, ema = _flat_ema_bars(n, ema_level)

    a_idx = 30
    bars.loc[a_idx, ["open", "high", "low", "close"]] = [90.0, 91.0, 88.0, 90.0]
    b_idx = 60
    bars.loc[b_idx, ["open", "high", "low", "close"]] = [111.0, 116.0, 110.0, 112.0]
    c_idx = 75
    bars.loc[c_idx, ["open", "high", "low", "close"]] = [95.0, 96.0, 94.0, 95.0]
    # d_target = c_price(95) + (b_price 116 - a_price 88) = 95 + 28 = 123.

    # After C (bars 76..89): price retraces BELOW C (low < 95) BEFORE any bar
    # reaches D (high >= 123). Put a deep low at bar 80.
    breach_idx = 80
    bars.loc[breach_idx, ["open", "high", "low", "close"]] = [93.0, 93.5, 90.0, 91.0]

    swings = [
        Swing(bar_idx=a_idx, price=88.0, kind="low"),
        Swing(bar_idx=b_idx, price=116.0, kind="high"),
        Swing(bar_idx=c_idx, price=94.0, kind="low"),
    ]
    cfg = Config()
    mms = detect_measured_moves(bars, swings, ema, cfg)
    bull_mms = [m for m in mms if m.direction == "bull"]
    assert len(bull_mms) == 1
    assert bull_mms[0].validity == "invalid", (
        "price breached below C before reaching D → MM must be invalid"
    )


def test_detect_measured_moves_no_c_breach_stays_valid() -> None:
    """Bull MM: price never retraces below C after C → validity stays 'valid'."""
    n = 90
    ema_level = 100.0
    bars, ema = _flat_ema_bars(n, ema_level)

    a_idx = 30
    bars.loc[a_idx, ["open", "high", "low", "close"]] = [90.0, 91.0, 88.0, 90.0]
    b_idx = 60
    bars.loc[b_idx, ["open", "high", "low", "close"]] = [111.0, 116.0, 110.0, 112.0]
    c_idx = 75
    bars.loc[c_idx, ["open", "high", "low", "close"]] = [95.0, 96.0, 94.0, 95.0]

    # After C: price drifts up toward D, never dips below C (low >= 95).
    for k in range(c_idx + 1, n):
        bars.loc[k, ["open", "high", "low", "close"]] = [100.0, 101.0, 99.0, 100.0]

    swings = [
        Swing(bar_idx=a_idx, price=88.0, kind="low"),
        Swing(bar_idx=b_idx, price=116.0, kind="high"),
        Swing(bar_idx=c_idx, price=94.0, kind="low"),
    ]
    cfg = Config()
    mms = detect_measured_moves(bars, swings, ema, cfg)
    bull_mms = [m for m in mms if m.direction == "bull"]
    assert len(bull_mms) == 1
    assert bull_mms[0].validity == "valid"


def test_detect_measured_moves_d_reached_before_breach_stays_valid() -> None:
    """Bull MM: D reached first, THEN a dip below C → stays valid (breach is moot)."""
    n = 90
    ema_level = 100.0
    bars, ema = _flat_ema_bars(n, ema_level)

    a_idx = 30
    bars.loc[a_idx, ["open", "high", "low", "close"]] = [90.0, 91.0, 88.0, 90.0]
    b_idx = 60
    bars.loc[b_idx, ["open", "high", "low", "close"]] = [111.0, 116.0, 110.0, 112.0]
    c_idx = 75
    bars.loc[c_idx, ["open", "high", "low", "close"]] = [95.0, 96.0, 94.0, 95.0]
    # d_target = 123.

    # Bar 78: reaches D (high >= 123).
    bars.loc[78, ["open", "high", "low", "close"]] = [120.0, 124.0, 119.0, 123.0]
    # Bar 82: dips below C — but D was already reached, so no invalidation.
    bars.loc[82, ["open", "high", "low", "close"]] = [93.0, 93.5, 90.0, 91.0]

    swings = [
        Swing(bar_idx=a_idx, price=88.0, kind="low"),
        Swing(bar_idx=b_idx, price=116.0, kind="high"),
        Swing(bar_idx=c_idx, price=94.0, kind="low"),
    ]
    cfg = Config()
    mms = detect_measured_moves(bars, swings, ema, cfg)
    bull_mms = [m for m in mms if m.direction == "bull"]
    assert len(bull_mms) == 1
    assert bull_mms[0].validity == "valid", (
        "breach below C AFTER D was reached must not invalidate the MM"
    )


# ---------------------------------------------------------------------------
# Defect 3 — §5.3 overshoot_bars must be derived from history so the
# extended target can actually fire in production.
# ---------------------------------------------------------------------------

def test_detect_measured_moves_sets_overshoot_bars() -> None:
    """Bull MM: price overshoots D for >= overshoot_bars_min consecutive bars."""
    n = 95
    ema_level = 100.0
    bars, ema = _flat_ema_bars(n, ema_level)

    a_idx = 30
    bars.loc[a_idx, ["open", "high", "low", "close"]] = [90.0, 91.0, 88.0, 90.0]
    b_idx = 60
    bars.loc[b_idx, ["open", "high", "low", "close"]] = [111.0, 116.0, 110.0, 112.0]
    c_idx = 75
    bars.loc[c_idx, ["open", "high", "low", "close"]] = [95.0, 96.0, 94.0, 95.0]
    # d_target = 123.

    # Bar 80 reaches D; bars 81..85 stay beyond D (low >= 123) — 5 overshoot bars.
    bars.loc[80, ["open", "high", "low", "close"]] = [120.0, 124.0, 119.0, 123.5]
    for k in range(81, 86):
        bars.loc[k, ["open", "high", "low", "close"]] = [125.0, 126.0, 124.0, 125.0]
    # Remaining bars stay above D too.
    for k in range(86, n):
        bars.loc[k, ["open", "high", "low", "close"]] = [125.0, 126.0, 124.0, 125.0]

    swings = [
        Swing(bar_idx=a_idx, price=88.0, kind="low"),
        Swing(bar_idx=b_idx, price=116.0, kind="high"),
        Swing(bar_idx=c_idx, price=94.0, kind="low"),
    ]
    cfg = Config()
    mms = detect_measured_moves(bars, swings, ema, cfg)
    bull_mms = [m for m in mms if m.direction == "bull"]
    assert len(bull_mms) == 1
    mm = bull_mms[0]
    assert mm.overshoot_bars >= cfg.overshoot_bars_min, (
        f"expected overshoot_bars >= {cfg.overshoot_bars_min}, got {mm.overshoot_bars}"
    )
    # And the extended target must now fire.
    # Geometry uses the swing pivot prices: a=88, b=116, c=94 (unchanged).
    ext = extended_mm_target(mm, bars, cfg)
    assert ext is not None
    assert ext == pytest.approx(94.0 + 1.382 * (116.0 - 88.0), abs=0.01)


def test_detect_measured_moves_no_overshoot_when_d_not_held() -> None:
    """Bull MM: D touched once but price retraces back through D → overshoot 0."""
    n = 90
    ema_level = 100.0
    bars, ema = _flat_ema_bars(n, ema_level)

    a_idx = 30
    bars.loc[a_idx, ["open", "high", "low", "close"]] = [90.0, 91.0, 88.0, 90.0]
    b_idx = 60
    bars.loc[b_idx, ["open", "high", "low", "close"]] = [111.0, 116.0, 110.0, 112.0]
    c_idx = 75
    bars.loc[c_idx, ["open", "high", "low", "close"]] = [95.0, 96.0, 94.0, 95.0]
    # d_target = 123.

    # Bar 80 touches D (high 124) but immediately retraces below D thereafter.
    bars.loc[80, ["open", "high", "low", "close"]] = [122.0, 124.0, 118.0, 119.0]
    for k in range(81, n):
        bars.loc[k, ["open", "high", "low", "close"]] = [110.0, 111.0, 109.0, 110.0]

    swings = [
        Swing(bar_idx=a_idx, price=88.0, kind="low"),
        Swing(bar_idx=b_idx, price=116.0, kind="high"),
        Swing(bar_idx=c_idx, price=94.0, kind="low"),
    ]
    cfg = Config()
    mms = detect_measured_moves(bars, swings, ema, cfg)
    bull_mms = [m for m in mms if m.direction == "bull"]
    assert len(bull_mms) == 1
    assert bull_mms[0].overshoot_bars == 0, (
        "price retraced back through D → no sustained overshoot"
    )


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
