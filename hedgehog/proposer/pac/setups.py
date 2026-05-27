"""§6 Setup Recognition — trap, fail, spike & channel state machines.

Design notes:
    - v1 setups are state machines for JOURNALING only, NOT trade gates.
      The engine (Task 16) checks *_triggered() predicates to log conviction;
      §3-§5-§7 agreement still drives actual trade decisions.
    - Only basic state transitions are implemented here. Timeout/expiry edge
      cases, mid-state invalidation, and fail-vs-trap nuance are marked # v2.
    - Each step_* function returns an immutable new state via
      dataclasses.replace() — the input state is never mutated.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

import pandas as pd

from hedgehog.proposer.pac.config import Config
from hedgehog.proposer.pac.targets import MeasuredMove


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TrapState:
    mm_id: int
    state: Literal["idle", "first_try_failed", "second_try_failed", "triggered"]
    first_try_extreme: float | None = None
    first_try_bar: int | None = None
    second_try_extreme: float | None = None
    second_try_bar: int | None = None


@dataclass(frozen=True)
class FailState:
    mm_id: int
    state: Literal["idle", "first_attempt_done", "second_attempt_done", "triggered"]
    first_attempt_extreme: float | None = None
    first_attempt_bar: int | None = None
    second_attempt_extreme: float | None = None
    second_attempt_bar: int | None = None


@dataclass(frozen=True)
class SpikeChannelState:
    state: Literal[
        "idle", "spike_detected", "channel_active",
        "pullback_active", "triggered", "invalidated",
    ]
    a_bar: int | None = None
    a_price: float | None = None
    a_prime_bar: int | None = None
    a_prime_price: float | None = None
    b_bar: int | None = None
    b_price: float | None = None
    c_price: float | None = None      # 50% Fib of A-B
    direction: Literal["bull", "bear", "none"] = "none"


# ---------------------------------------------------------------------------
# §6.1 Trap setup
# ---------------------------------------------------------------------------

def step_trap(
    state: TrapState,
    bar: pd.Series,
    bar_idx: int,
    mm: MeasuredMove,
    atr: float,
    cfg: Config,
) -> TrapState:
    """Advance the trap state machine one bar; return new immutable state.

    Trap logic (§6.1):
        The 38.2% Fib retracement level of A→B is the "trap zone".
        For a bull MM, two successive failed breaks of that zone (price dips in
        then snaps back) signal trapped shorts and trigger a long setup.

    State flow:
        idle
          → first_try_failed   when bar touches the trap zone within threshold
                                and penetration is shallow
          (timeout to idle: # v2)
        first_try_failed
          → second_try_failed  when a later bar again touches near the same extreme
          (timeout to idle: # v2)
        second_try_failed
          → triggered          when price reacts up by at least the failure threshold
    """
    ab_span = mm.b_price - mm.a_price  # positive for bull, negative for bear

    if mm.direction == "bull":
        trap_level = mm.a_price + cfg.trap_first_try_level * ab_span
        failure_threshold = cfg.trap_failure_threshold_atr_multiple * atr
        max_penetration = cfg.trap_max_first_try_penetration_fib * abs(ab_span)

        if state.state == "idle":
            # Bar low must touch close to trap_level (within failure_threshold)
            # and penetration past trap_level must be shallow.
            low = bar["low"]
            distance_to_trap = abs(low - trap_level)
            penetration = trap_level - low  # positive if low broke below trap_level
            if distance_to_trap <= failure_threshold and penetration <= max_penetration:
                return replace(
                    state,
                    state="first_try_failed",
                    first_try_extreme=float(low),
                    first_try_bar=bar_idx,
                )

        elif state.state == "first_try_failed":
            assert state.first_try_bar is not None
            assert state.first_try_extreme is not None
            # Must occur within cfg.trap_max_bars_between_tries bars of first try.
            # v2: hard-expire to idle; v1 just gate on the window.
            bars_since_first = bar_idx - state.first_try_bar
            if bars_since_first <= cfg.trap_max_bars_between_tries:
                low = bar["low"]
                distance_to_extreme = abs(low - state.first_try_extreme)
                if distance_to_extreme <= failure_threshold:
                    return replace(
                        state,
                        state="second_try_failed",
                        second_try_extreme=float(low),
                        second_try_bar=bar_idx,
                    )
            # v2: else reset to idle

        elif state.state == "second_try_failed":
            # Subsequent bar shows price moving up by at least the failure threshold.
            close = bar["close"]
            assert state.second_try_extreme is not None
            reaction_up = close - state.second_try_extreme
            if reaction_up >= failure_threshold:
                return replace(state, state="triggered")

    else:
        # Bear MM: mirror of bull.
        trap_level = mm.a_price + cfg.trap_first_try_level * ab_span  # ab_span negative
        failure_threshold = cfg.trap_failure_threshold_atr_multiple * atr
        max_penetration = cfg.trap_max_first_try_penetration_fib * abs(ab_span)

        if state.state == "idle":
            high = bar["high"]
            distance_to_trap = abs(high - trap_level)
            penetration = high - trap_level  # positive if high broke above trap_level
            if distance_to_trap <= failure_threshold and penetration <= max_penetration:
                return replace(
                    state,
                    state="first_try_failed",
                    first_try_extreme=float(high),
                    first_try_bar=bar_idx,
                )

        elif state.state == "first_try_failed":
            assert state.first_try_bar is not None
            assert state.first_try_extreme is not None
            bars_since_first = bar_idx - state.first_try_bar
            if bars_since_first <= cfg.trap_max_bars_between_tries:
                high = bar["high"]
                distance_to_extreme = abs(high - state.first_try_extreme)
                if distance_to_extreme <= failure_threshold:
                    return replace(
                        state,
                        state="second_try_failed",
                        second_try_extreme=float(high),
                        second_try_bar=bar_idx,
                    )

        elif state.state == "second_try_failed":
            close = bar["close"]
            assert state.second_try_extreme is not None
            reaction_down = state.second_try_extreme - close
            failure_threshold = cfg.trap_failure_threshold_atr_multiple * atr
            if reaction_down >= failure_threshold:
                return replace(state, state="triggered")

    return state


# ---------------------------------------------------------------------------
# §6.2 Fail setup
# ---------------------------------------------------------------------------

def step_fail(
    state: FailState,
    bar: pd.Series,
    bar_idx: int,
    mm: MeasuredMove,
    atr: float,
    cfg: Config,
) -> FailState:
    """Advance the fail state machine one bar.

    Fail logic (§6.2):
        Similar to trap but with DEPTH requirements.
        First attempt must PIERCE >= cfg.fail_min_first_attempt_depth_fib (0.382) of AB.
        Second attempt must fall short of first attempt depth by >=
            cfg.fail_second_attempt_shortfall_atr_multiple × atr.

    State flow:
        idle
          → first_attempt_done   when bar pierces the min-depth level
          (timeout: # v2)
        first_attempt_done
          → second_attempt_done  when a later bar pierces again but falls short
          (timeout: # v2)
        second_attempt_done
          → triggered            when price reacts in the original direction
    """
    ab_span = mm.b_price - mm.a_price  # positive for bull, negative for bear
    ab_abs = abs(ab_span)
    min_depth_level = cfg.fail_min_first_attempt_depth_fib * ab_abs
    shortfall_threshold = cfg.fail_second_attempt_shortfall_atr_multiple * atr

    if mm.direction == "bull":
        # "Fail" for bull = deep downward correction.
        # First attempt low must be at or below (a_price + min_depth - ab_span_abs)
        # i.e. low pierces below the 38.2% retracement from B toward A.
        depth_threshold = mm.b_price - min_depth_level  # e.g. 110 - 3.82 = 106.18 → actually A+(1-0.382)*AB

        # More precisely: the 38.2% retracement of AB is a_price + 0.382*ab_span.
        # "Pierce >= 0.382" means the low went at or below that level.
        fib_382 = mm.a_price + cfg.fail_min_first_attempt_depth_fib * ab_span

        if state.state == "idle":
            low = bar["low"]
            if low <= fib_382:
                return replace(
                    state,
                    state="first_attempt_done",
                    first_attempt_extreme=float(low),
                    first_attempt_bar=bar_idx,
                )

        elif state.state == "first_attempt_done":
            assert state.first_attempt_bar is not None
            assert state.first_attempt_extreme is not None
            bars_since_first = bar_idx - state.first_attempt_bar
            if bars_since_first <= cfg.fail_max_bars_between_attempts:
                low = bar["low"]
                # Second attempt also must pierce 38.2%, but not go as deep —
                # falls short by >= shortfall_threshold (less extreme than first).
                if low <= fib_382:
                    shortfall = state.first_attempt_extreme - low
                    # If shortfall is negative it means second went deeper → not a fail setup
                    # If shortfall >= threshold, second attempt was shallower → valid
                    if shortfall >= shortfall_threshold:
                        return replace(
                            state,
                            state="second_attempt_done",
                            second_attempt_extreme=float(low),
                            second_attempt_bar=bar_idx,
                        )
            # v2: expire to idle after timeout

        elif state.state == "second_attempt_done":
            # Price reacts back up (bullish close confirms fail of bears).
            close = bar["close"]
            assert state.second_attempt_extreme is not None
            if close > fib_382:
                return replace(state, state="triggered")

    else:
        # Bear MM: mirror
        fib_382 = mm.a_price + cfg.fail_min_first_attempt_depth_fib * ab_span
        # For bear, ab_span is negative, so fib_382 < a_price (lower).
        # "Fail" = deep upward correction, high pierces fib_382.

        if state.state == "idle":
            high = bar["high"]
            if high >= fib_382:
                return replace(
                    state,
                    state="first_attempt_done",
                    first_attempt_extreme=float(high),
                    first_attempt_bar=bar_idx,
                )

        elif state.state == "first_attempt_done":
            assert state.first_attempt_bar is not None
            assert state.first_attempt_extreme is not None
            bars_since_first = bar_idx - state.first_attempt_bar
            if bars_since_first <= cfg.fail_max_bars_between_attempts:
                high = bar["high"]
                if high >= fib_382:
                    shortfall = high - state.first_attempt_extreme
                    if shortfall >= shortfall_threshold:
                        return replace(
                            state,
                            state="second_attempt_done",
                            second_attempt_extreme=float(high),
                            second_attempt_bar=bar_idx,
                        )

        elif state.state == "second_attempt_done":
            close = bar["close"]
            assert state.second_attempt_extreme is not None
            if close < fib_382:
                return replace(state, state="triggered")

    return state


# ---------------------------------------------------------------------------
# §6.3 Spike & channel
# ---------------------------------------------------------------------------

def step_spike_channel(
    state: SpikeChannelState,
    bar: pd.Series,
    bar_idx: int,
    bars_window: pd.DataFrame,
    atr: float,
    cfg: Config,
) -> SpikeChannelState:
    """Advance the spike & channel state machine one bar.

    `bars_window` is the recent slice of bars (last cfg.spike_min_bars bars)
    used to detect a spike on the current evaluation.

    Spike & Channel logic (§6.3):
        idle
          → spike_detected  when last spike_min_bars bars are all same-direction
                            (<=spike_max_counter_bars counter bars allowed)
                            AND cumulative magnitude >= spike_min_magnitude_atr × atr
        spike_detected
          → channel_active  after at least 1 bar beyond the spike
                            (tracking the channel's high/low as B)
        channel_active (after >= channel_min_bars)
          → pullback_active when price retraces toward 50% Fib of A→B
        pullback_active
          → triggered       when price reacts at C (50% Fib), close in spike direction
          → invalidated     if pullback wick pierces beyond pullback_invalidation_fib
                            before triggering (v1: same fib = 50% as c_price, # v2 refine)
    """
    if state.state == "idle":
        n = cfg.spike_min_bars
        if len(bars_window) < n:
            return state

        window = bars_window.iloc[-n:]
        closes = window["close"].tolist()
        opens = window["open"].tolist()

        # Determine direction from net close-to-close move.
        net_move = closes[-1] - closes[0]
        if abs(net_move) < cfg.spike_min_magnitude_atr * atr:
            return state

        is_bull = net_move > 0
        direction: Literal["bull", "bear"] = "bull" if is_bull else "bear"

        # Count counter-direction bars.
        counter_bars = 0
        for i in range(len(closes)):
            bar_move = closes[i] - opens[i]
            if is_bull and bar_move < 0:
                counter_bars += 1
            elif not is_bull and bar_move > 0:
                counter_bars += 1

        if counter_bars > cfg.spike_max_counter_bars:
            return state

        # Spike confirmed.
        a_bar = bar_idx - n + 1
        a_price = float(window["close"].iloc[0])
        a_prime_bar = bar_idx
        a_prime_price = float(window["close"].iloc[-1])

        return replace(
            state,
            state="spike_detected",
            a_bar=a_bar,
            a_price=a_price,
            a_prime_bar=a_prime_bar,
            a_prime_price=a_prime_price,
            direction=direction,
        )

    elif state.state == "spike_detected":
        # After at least 1 bar beyond the spike, move to channel_active.
        # (a_prime_bar is the last spike bar; if bar_idx > a_prime_bar we're past the spike.)
        if state.a_prime_bar is not None and bar_idx > state.a_prime_bar:
            # Initialize B as the current bar's extreme.
            assert state.a_price is not None
            if state.direction == "bull":
                b_price = float(bar["high"])
            else:
                b_price = float(bar["low"])
            c_price = (state.a_price + b_price) / 2.0  # 50% Fib
            return replace(
                state,
                state="channel_active",
                b_bar=bar_idx,
                b_price=b_price,
                c_price=c_price,
            )

    elif state.state == "channel_active":
        assert state.b_bar is not None
        assert state.b_price is not None
        assert state.a_price is not None
        assert state.c_price is not None

        # Update B continuously (track the furthest extreme).
        if state.direction == "bull":
            new_b = max(state.b_price, float(bar["high"]))
        else:
            new_b = min(state.b_price, float(bar["low"]))

        new_c = (state.a_price + new_b) / 2.0

        bars_in_channel = bar_idx - state.b_bar
        updated_state = replace(state, b_price=new_b, c_price=new_c)

        # Only start looking for pullback after channel_min_bars.
        if bars_in_channel < cfg.channel_min_bars:
            return updated_state

        # Check for pullback toward C.
        if state.direction == "bull":
            if bar["low"] <= new_c:
                return replace(updated_state, state="pullback_active")
        else:
            if bar["high"] >= new_c:
                return replace(updated_state, state="pullback_active")

        return updated_state

    elif state.state == "pullback_active":
        assert state.c_price is not None
        assert state.a_price is not None

        # Invalidation: wick pierces beyond pullback_invalidation_fib.
        # v1: use c_price as the invalidation line (same as 50% Fib).
        # v2: use a separate cfg.pullback_invalidation_fib level.
        if state.direction == "bull":
            # Invalidate if low goes below a_price (full retracement).
            if bar["low"] < state.a_price:
                return replace(state, state="invalidated")
            # Trigger: close above c_price (reaction off the 50% level).
            if bar["close"] >= state.c_price:
                return replace(state, state="triggered")
        else:
            if bar["high"] > state.a_price:
                return replace(state, state="invalidated")
            if bar["close"] <= state.c_price:
                return replace(state, state="triggered")

    # triggered / invalidated are terminal; no further transitions.
    return state


# ---------------------------------------------------------------------------
# Predicate helpers
# ---------------------------------------------------------------------------

def trap_setup_triggered(state: TrapState) -> bool:
    return state.state == "triggered"


def fail_setup_triggered(state: FailState) -> bool:
    return state.state == "triggered"


def spike_channel_triggered(state: SpikeChannelState) -> bool:
    return state.state == "triggered"
