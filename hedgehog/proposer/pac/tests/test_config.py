"""Tests for the central Config dataclass holding all §1-§7 thresholds."""
from __future__ import annotations

import pytest

from hedgehog.proposer.pac.config import Config


def test_defaults_match_strategy_ea_section_1() -> None:
    cfg = Config()
    assert cfg.risk_percent == 1.0
    assert cfg.min_rr == 1.5
    assert cfg.max_trades_per_session == 3
    assert cfg.daily_dd_stop_pct == -3.0
    assert cfg.weekly_dd_stop_pct == -5.0
    assert cfg.news_filter_enabled is False


def test_defaults_match_strategy_ea_section_3() -> None:
    cfg = Config()
    assert cfg.ema_period == 21
    assert cfg.sma_period == 61
    assert cfg.dynamic_cross_max_bars == 2
    assert cfg.direction_strict is True
    assert cfg.mmd_strict is False


def test_defaults_match_strategy_ea_section_4() -> None:
    cfg = Config()
    assert cfg.wick_to_body_ratio_min == 2.0
    assert cfg.candle_range_atr_multiple_min == 0.5
    assert cfg.close_position_within_wick_pct == 33
    assert cfg.confluence_pips_threshold_atr_multiple == 0.3
    assert cfg.confluence_required_levels == 1


def test_defaults_match_strategy_ea_section_5() -> None:
    cfg = Config()
    assert cfg.impulse_atr_multiple_min == 1.5
    assert cfg.fib_levels_retracement == (0.382, 0.5, 0.618)
    assert cfg.fib_levels_extension == (1.382, 1.618, 2.618)
    assert cfg.cluster_pips_threshold_atr_multiple == 0.3
    assert cfg.cluster_member_min == 2
    assert cfg.overshoot_bars_min == 3
    assert cfg.settle_buffer_atr_multiple == 0.5
    assert cfg.max_active_measured_moves == 5


def test_defaults_match_strategy_ea_section_6() -> None:
    cfg = Config()
    assert cfg.trap_first_try_level == 0.382
    assert cfg.trap_failure_threshold_atr_multiple == 0.2
    assert cfg.trap_max_bars_between_tries == 20
    assert cfg.trap_max_first_try_penetration_fib == 0.20
    assert cfg.fail_min_first_attempt_depth_fib == 0.382
    assert cfg.fail_max_first_attempt_depth_fib == 1.0
    assert cfg.fail_second_attempt_shortfall_atr_multiple == 0.3
    assert cfg.fail_max_bars_between_attempts == 30
    assert cfg.spike_min_bars == 3
    assert cfg.spike_min_magnitude_atr == 3.0
    assert cfg.spike_max_counter_bars == 1
    assert cfg.pullback_invalidation_fib == 0.5
    assert cfg.exhaustion_fib == 1.382
    assert cfg.channel_min_bars == 5


def test_defaults_match_strategy_ea_section_7() -> None:
    cfg = Config()
    assert cfg.wick_buffer_in_spreads == 1
    assert cfg.min_sl_distance_atr_multiple == 0.3
    assert cfg.max_slippage_pips == 3
    assert cfg.partials_enabled is False
    assert cfg.partials_trigger_r == 1.0
    assert cfg.partials_close_fraction == 0.5
    assert cfg.partials_breakeven_after is True
    assert cfg.trailing_enabled is False
    assert cfg.trailing_activation_r == 1.5
    assert cfg.trailing_distance_atr_multiple == 1.0
    assert cfg.trailing_freeze_atr_at_activation is True


def test_frozen_immutable() -> None:
    cfg = Config()
    with pytest.raises((AttributeError, TypeError)):
        cfg.risk_percent = 5.0


def test_correlation_groups_default() -> None:
    cfg = Config()
    assert ("XAUUSD", "US500") in cfg.correlation_groups
    assert any({"US500", "US30", "USTECH"} <= set(g) for g in cfg.correlation_groups)


def test_to_dict_round_trip() -> None:
    cfg = Config()
    d = cfg.to_dict()
    # Round-trip — all keys preserved
    cfg2 = Config.from_dict(d)
    assert cfg2 == cfg
