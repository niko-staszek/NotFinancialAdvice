"""Central configuration for the PAC ref impl.

All thresholds from strategy_ea.md §1-§7 live here. Defaults match the spec.
The Config is frozen — pass a new instance to override (or use .replace()).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class Config:
    # §1 Risk Management
    risk_percent: float = 1.0
    min_rr: float = 1.5
    max_trades_per_session: int = 3
    daily_dd_stop_pct: float = -3.0
    weekly_dd_stop_pct: float = -5.0
    correlation_groups: tuple[tuple[str, ...], ...] = field(default_factory=lambda: (
        ("XAUUSD", "US500"),
        ("US500", "US30", "USTECH"),
        ("USOIL", "US500"),
    ))
    news_filter_enabled: bool = False
    news_filter_window_min: int = 15

    # §3.1 EMA/SMA Sentiment
    ema_period: int = 21
    sma_period: int = 61
    dynamic_cross_max_bars: int = 2

    # §3.2 MMD
    mmd_strict: bool = False

    # §3.5 Composite direction rule
    direction_strict: bool = True

    # §4.1 Signal candle
    wick_to_body_ratio_min: float = 2.0
    candle_range_atr_multiple_min: float = 0.5
    close_position_within_wick_pct: int = 33

    # §4.3 Confluence
    confluence_pips_threshold_atr_multiple: float = 0.3
    confluence_required_levels: int = 1

    # §5.1 Measured move
    impulse_atr_multiple_min: float = 1.5
    max_active_measured_moves: int = 5

    # §5.2 Fibonacci
    fib_levels_retracement: tuple[float, ...] = (0.382, 0.5, 0.618)
    fib_levels_extension: tuple[float, ...] = (1.382, 1.618, 2.618)
    cluster_pips_threshold_atr_multiple: float = 0.3
    cluster_member_min: int = 2

    # §5.3 Extended MM
    overshoot_bars_min: int = 3

    # §5.4 Settle buffer
    settle_buffer_atr_multiple: float = 0.5

    # §6.1 Trap setup
    trap_first_try_level: float = 0.382
    trap_failure_threshold_atr_multiple: float = 0.2
    trap_max_bars_between_tries: int = 20
    trap_max_first_try_penetration_fib: float = 0.20

    # §6.2 Fail setup
    fail_min_first_attempt_depth_fib: float = 0.382
    fail_max_first_attempt_depth_fib: float = 1.0
    fail_second_attempt_shortfall_atr_multiple: float = 0.3
    fail_max_bars_between_attempts: int = 30

    # §6.3 Spike & channel
    spike_min_bars: int = 3
    spike_min_magnitude_atr: float = 3.0
    spike_max_counter_bars: int = 1
    pullback_invalidation_fib: float = 0.5
    exhaustion_fib: float = 1.382
    channel_min_bars: int = 5

    # §7.1 SL placement
    wick_buffer_in_spreads: int = 1
    min_sl_distance_atr_multiple: float = 0.3

    # §7.2 Order type
    max_slippage_pips: int = 3

    # §7.3 Partials
    partials_enabled: bool = False
    partials_trigger_r: float = 1.0
    partials_close_fraction: float = 0.5
    partials_breakeven_after: bool = True

    # §7.4 Trailing
    trailing_enabled: bool = False
    trailing_activation_r: float = 1.5
    trailing_distance_atr_multiple: float = 1.0
    trailing_freeze_atr_at_activation: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Config":
        # Restore tuples from lists if JSON-deserialized.
        d = dict(d)  # copy so we don't mutate caller's dict
        if isinstance(d.get("correlation_groups"), list):
            d["correlation_groups"] = tuple(tuple(g) for g in d["correlation_groups"])
        if isinstance(d.get("fib_levels_retracement"), list):
            d["fib_levels_retracement"] = tuple(d["fib_levels_retracement"])
        if isinstance(d.get("fib_levels_extension"), list):
            d["fib_levels_extension"] = tuple(d["fib_levels_extension"])
        return cls(**d)

    def replace(self, **overrides: Any) -> "Config":
        return replace(self, **overrides)
