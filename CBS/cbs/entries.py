"""Candidate entry detectors for CBS Engine B.

Each detector is a pure function (EntryContext) -> EntrySignal | None. A detector
abstains (returns None) when its pattern is not present. All detectors may only
read bars at/before ctx.completion_ts (no lookahead — enforced by build_context).

This module starts with the framework + baseline (control-group) detectors.
Structure, liquidity, and time detectors are appended in later tasks and
registered in DETECTORS.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Callable, Optional

import pandas as pd

from .bars import slice_window, resample_h1, atr_m5


@dataclass(frozen=True)
class EntrySignal:
    name: str
    entry_price: float
    invalidation_price: float
    entry_time: pd.Timestamp


@dataclass(frozen=True)
class EntryContext:
    symbol: str
    m5: pd.DataFrame
    h1: pd.DataFrame
    window_close_ts: pd.Timestamp
    completion_ts: pd.Timestamp
    target: float
    approach_side: str
    pip_size: float
    atr_m5: float
    atr_k: float


def build_context(df: pd.DataFrame, *, symbol: str, window_close_ts: pd.Timestamp,
                  completion_ts: pd.Timestamp, target: float, approach_side: str,
                  pip_size: float, lookback_hours: int, atr_period: int,
                  atr_k: float) -> EntryContext:
    """Clip `df` to [window_close_ts - lookback, completion_ts] and assemble context."""
    lo = window_close_ts - timedelta(hours=lookback_hours)
    m5 = df.loc[(df["time_utc"] >= lo) & (df["time_utc"] <= completion_ts)].reset_index(drop=True)
    h1 = resample_h1(m5)
    atr = atr_m5(m5, period=atr_period)
    return EntryContext(symbol=symbol, m5=m5, h1=h1, window_close_ts=window_close_ts,
                        completion_ts=completion_ts, target=target,
                        approach_side=approach_side, pip_size=pip_size,
                        atr_m5=atr, atr_k=atr_k)


def _atr_sl(ctx: EntryContext, entry: float) -> float:
    """Fallback invalidation: entry -/+ k*ATR on the side opposite the target."""
    dist = ctx.atr_k * ctx.atr_m5
    return entry - dist if ctx.approach_side == "up" else entry + dist


def _post_window(ctx: EntryContext) -> pd.DataFrame:
    return ctx.m5.loc[ctx.m5["time_utc"] >= ctx.window_close_ts].reset_index(drop=True)


def _window_close_bar(ctx: EntryContext) -> pd.Series:
    """Last bar at/before window_close_ts (the bar whose close defines window close price)."""
    pre = ctx.m5.loc[ctx.m5["time_utc"] < ctx.window_close_ts]
    return pre.iloc[-1]


# --- Baseline detectors (control group) -------------------------------------

def enter_at_window_close(ctx: EntryContext) -> Optional[EntrySignal]:
    bar = _window_close_bar(ctx)
    entry = float(bar["close"])
    return EntrySignal("enter_at_window_close", entry, _atr_sl(ctx, entry),
                       ctx.window_close_ts)


def first_m5_close(ctx: EntryContext) -> Optional[EntrySignal]:
    fwd = _post_window(ctx)
    for row in fwd.itertuples(index=False):
        in_dir = (row.close > row.open) if ctx.approach_side == "up" else (row.close < row.open)
        if in_dir:
            entry = float(row.close)
            return EntrySignal("first_m5_close", entry, _atr_sl(ctx, entry), row.time_utc)
    return None


def first_pullback_pct(ctx: EntryContext, pct: float = 0.3) -> Optional[EntrySignal]:
    """Enter after price retraces `pct` of the move's initial extension back toward start."""
    fwd = _post_window(ctx)
    if len(fwd) < 2:
        return None
    start = float(_window_close_bar(ctx)["close"])
    if ctx.approach_side == "up":
        ext = start
        for row in fwd.itertuples(index=False):
            pull_level = ext - pct * (ext - start)
            if ext > start and row.low <= pull_level:
                return EntrySignal("first_pullback_pct", pull_level, _atr_sl(ctx, pull_level), row.time_utc)
            ext = max(ext, row.high)
    else:
        ext = start
        for row in fwd.itertuples(index=False):
            pull_level = ext + pct * (start - ext)
            if ext < start and row.high >= pull_level:
                return EntrySignal("first_pullback_pct", pull_level, _atr_sl(ctx, pull_level), row.time_utc)
            ext = min(ext, row.low)
    return None


DETECTORS: dict[str, Callable[[EntryContext], Optional[EntrySignal]]] = {
    "enter_at_window_close": enter_at_window_close,
    "first_m5_close": first_m5_close,
    "first_pullback_pct": first_pullback_pct,
}


# --- Structure detectors ----------------------------------------------------

def _ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def _prior_extreme(ctx: EntryContext, kind: str) -> float:
    """PDH/PDL proxy: extreme of the lookback bars strictly before window close."""
    pre = ctx.m5.loc[ctx.m5["time_utc"] < ctx.window_close_ts]
    return float(pre["high"].max()) if kind == "high" else float(pre["low"].min())


def sr_retest(ctx: EntryContext) -> Optional[EntrySignal]:
    fwd = _post_window(ctx)
    tol = 0.5 * ctx.atr_m5
    if ctx.approach_side == "up":
        level = _prior_extreme(ctx, "high")
        broken = False
        for row in fwd.itertuples(index=False):
            if not broken and row.high > level:
                broken = True
                continue
            if broken and row.low <= level and row.close >= level:
                return EntrySignal("sr_retest", level, level - tol, row.time_utc)
    else:
        level = _prior_extreme(ctx, "low")
        broken = False
        for row in fwd.itertuples(index=False):
            if not broken and row.low < level:
                broken = True
                continue
            if broken and row.high >= level and row.close <= level:
                return EntrySignal("sr_retest", level, level + tol, row.time_utc)
    return None


def fvg_fill(ctx: EntryContext) -> Optional[EntrySignal]:
    fwd = _post_window(ctx).reset_index(drop=True)
    min_gap = 20 * ctx.pip_size
    n = len(fwd)
    for i in range(n - 2):
        if ctx.approach_side == "up":
            gap_lo, gap_hi = float(fwd.loc[i, "high"]), float(fwd.loc[i + 2, "low"])
            if gap_hi - gap_lo >= min_gap:
                for j in range(i + 3, n):
                    if fwd.loc[j, "low"] <= gap_hi:
                        return EntrySignal("fvg_fill", gap_hi, gap_lo, fwd.loc[j, "time_utc"])
        else:
            gap_hi, gap_lo = float(fwd.loc[i, "low"]), float(fwd.loc[i + 2, "high"])
            if gap_hi - gap_lo >= min_gap:
                for j in range(i + 3, n):
                    if fwd.loc[j, "high"] >= gap_lo:
                        return EntrySignal("fvg_fill", gap_lo, gap_hi, fwd.loc[j, "time_utc"])
    return None


def swing_retest(ctx: EntryContext) -> Optional[EntrySignal]:
    pre = ctx.m5.loc[ctx.m5["time_utc"] < ctx.window_close_ts].reset_index(drop=True)
    if len(pre) < 5:
        return None
    fwd = _post_window(ctx)
    if ctx.approach_side == "up":
        highs = pre["high"].values
        swing = None
        for k in range(2, len(highs) - 2):
            if highs[k] >= max(highs[k-2], highs[k-1], highs[k+1], highs[k+2]):
                swing = float(highs[k])
        if swing is None:
            return None
        broken = False
        for row in fwd.itertuples(index=False):
            if not broken and row.high > swing:
                broken = True
                continue
            if broken and row.low <= swing:
                return EntrySignal("swing_retest", swing, swing - 0.5 * ctx.atr_m5, row.time_utc)
    else:
        lows = pre["low"].values
        swing = None
        for k in range(2, len(lows) - 2):
            if lows[k] <= min(lows[k-2], lows[k-1], lows[k+1], lows[k+2]):
                swing = float(lows[k])
        if swing is None:
            return None
        broken = False
        for row in fwd.itertuples(index=False):
            if not broken and row.low < swing:
                broken = True
                continue
            if broken and row.high >= swing:
                return EntrySignal("swing_retest", swing, swing + 0.5 * ctx.atr_m5, row.time_utc)
    return None


def ema21_retest(ctx: EntryContext) -> Optional[EntrySignal]:
    h1 = ctx.h1.copy()
    if len(h1) < 21:
        return None
    h1["ema"] = _ema(h1["close"], 21)
    post = h1.loc[h1["time_utc"] >= ctx.window_close_ts].reset_index(drop=True)
    reclaimed = False
    for row in post.itertuples(index=False):
        if ctx.approach_side == "up":
            if not reclaimed and row.close > row.ema:
                reclaimed = True
                continue
            if reclaimed and row.low <= row.ema and row.close >= row.ema:
                return EntrySignal("ema21_retest", float(row.ema), float(row.ema) - 0.5 * ctx.atr_m5, row.time_utc)
        else:
            if not reclaimed and row.close < row.ema:
                reclaimed = True
                continue
            if reclaimed and row.high >= row.ema and row.close <= row.ema:
                return EntrySignal("ema21_retest", float(row.ema), float(row.ema) + 0.5 * ctx.atr_m5, row.time_utc)
    return None


def fib_cluster(ctx: EntryContext) -> Optional[EntrySignal]:
    fwd = _post_window(ctx).reset_index(drop=True)
    if len(fwd) < 3:
        return None
    start = float(_window_close_bar(ctx)["close"])
    if ctx.approach_side == "up":
        ext = start
        for row in fwd.itertuples(index=False):
            level = ext - 0.618 * (ext - start)
            if ext > start and row.low <= level:
                return EntrySignal("fib_cluster", level, level - 0.5 * ctx.atr_m5, row.time_utc)
            ext = max(ext, row.high)
    else:
        ext = start
        for row in fwd.itertuples(index=False):
            level = ext + 0.618 * (start - ext)
            if ext < start and row.high >= level:
                return EntrySignal("fib_cluster", level, level + 0.5 * ctx.atr_m5, row.time_utc)
            ext = min(ext, row.low)
    return None


DETECTORS.update({
    "ema21_retest": ema21_retest,
    "swing_retest": swing_retest,
    "sr_retest": sr_retest,
    "fvg_fill": fvg_fill,
    "fib_cluster": fib_cluster,
})


# --- Liquidity / ICT detectors ----------------------------------------------

def order_block(ctx: EntryContext) -> Optional[EntrySignal]:
    """Last opposing-close bar before the impulse; enter on return into its range."""
    fwd = _post_window(ctx)
    ob = None      # (low, high)
    armed = False  # impulse confirmed: price closed beyond the OB
    if ctx.approach_side == "up":
        for row in fwd.itertuples(index=False):
            if ob is not None and armed and row.low <= ob[1]:
                return EntrySignal("order_block", ob[1], ob[0], row.time_utc)
            if ob is not None and not armed and row.close > ob[1]:
                armed = True
            if row.close < row.open:
                ob = (float(row.low), float(row.high)); armed = False
    else:
        for row in fwd.itertuples(index=False):
            if ob is not None and armed and row.high >= ob[0]:
                return EntrySignal("order_block", ob[0], ob[1], row.time_utc)
            if ob is not None and not armed and row.close < ob[0]:
                armed = True
            if row.close > row.open:
                ob = (float(row.low), float(row.high)); armed = False
    return None


def liquidity_sweep(ctx: EntryContext) -> Optional[EntrySignal]:
    """Raid beyond the prior-day extreme then reclaim within 3 bars."""
    fwd = _post_window(ctx).reset_index(drop=True)
    if ctx.approach_side == "up":
        pdl = _prior_extreme(ctx, "low")
        swept_i = None; sweep_low = None
        for i, row in enumerate(fwd.itertuples(index=False)):
            if swept_i is None:
                if row.low < pdl:
                    swept_i = i; sweep_low = float(row.low)
            else:
                if i - swept_i > 3:
                    swept_i = None; continue
                sweep_low = min(sweep_low, float(row.low))
                if row.close > pdl:
                    return EntrySignal("liquidity_sweep", float(row.close), sweep_low, row.time_utc)
    else:
        pdh = _prior_extreme(ctx, "high")
        swept_i = None; sweep_high = None
        for i, row in enumerate(fwd.itertuples(index=False)):
            if swept_i is None:
                if row.high > pdh:
                    swept_i = i; sweep_high = float(row.high)
            else:
                if i - swept_i > 3:
                    swept_i = None; continue
                sweep_high = max(sweep_high, float(row.high))
                if row.close < pdh:
                    return EntrySignal("liquidity_sweep", float(row.close), sweep_high, row.time_utc)
    return None


def breaker(ctx: EntryContext) -> Optional[EntrySignal]:
    """Failed order block: OB extreme broken, then price reclaims the OB → flip."""
    fwd = _post_window(ctx)
    ob = None; broken_ext = None
    if ctx.approach_side == "up":
        for row in fwd.itertuples(index=False):
            if ob is not None:
                if broken_ext is None and row.low < ob[0]:
                    broken_ext = float(row.low)
                elif broken_ext is not None:
                    broken_ext = min(broken_ext, float(row.low))
                    if row.close > ob[1]:
                        return EntrySignal("breaker", ob[1], broken_ext, row.time_utc)
            if row.close < row.open:
                ob = (float(row.low), float(row.high)); broken_ext = None
    else:
        for row in fwd.itertuples(index=False):
            if ob is not None:
                if broken_ext is None and row.high > ob[1]:
                    broken_ext = float(row.high)
                elif broken_ext is not None:
                    broken_ext = max(broken_ext, float(row.high))
                    if row.close < ob[0]:
                        return EntrySignal("breaker", ob[0], broken_ext, row.time_utc)
            if row.close > row.open:
                ob = (float(row.low), float(row.high)); broken_ext = None
    return None


def _equal_level(values, band: float, side: str):
    """Cluster values into `band`-width buckets; return the level of a >=2-member
    cluster on the given side ('low' -> lowest such cluster min, 'high' -> highest max)."""
    if band <= 0 or len(values) < 2:
        return None
    buckets: dict = {}
    for v in values:
        key = round(float(v) / band)
        buckets.setdefault(key, []).append(float(v))
    cands = [vals for vals in buckets.values() if len(vals) >= 2]
    if not cands:
        return None
    if side == "low":
        return min(min(v) for v in cands)
    return max(max(v) for v in cands)


def eqh_eql_raid(ctx: EntryContext) -> Optional[EntrySignal]:
    """Raid of equal lows (up) / equal highs (down) then reversal back through them."""
    pre = ctx.m5.loc[ctx.m5["time_utc"] < ctx.window_close_ts]
    band = 0.25 * ctx.atr_m5
    fwd = _post_window(ctx)
    if ctx.approach_side == "up":
        level = _equal_level(pre["low"].values, band, "low")
        if level is None:
            return None
        raided = False; raid_low = None
        for row in fwd.itertuples(index=False):
            if not raided and row.low < level:
                raided = True; raid_low = float(row.low)
            elif raided:
                raid_low = min(raid_low, float(row.low))
                if row.close > level:
                    return EntrySignal("eqh_eql_raid", level, raid_low, row.time_utc)
    else:
        level = _equal_level(pre["high"].values, band, "high")
        if level is None:
            return None
        raided = False; raid_high = None
        for row in fwd.itertuples(index=False):
            if not raided and row.high > level:
                raided = True; raid_high = float(row.high)
            elif raided:
                raid_high = max(raid_high, float(row.high))
                if row.close < level:
                    return EntrySignal("eqh_eql_raid", level, raid_high, row.time_utc)
    return None


DETECTORS.update({
    "order_block": order_block,
    "liquidity_sweep": liquidity_sweep,
    "breaker": breaker,
    "eqh_eql_raid": eqh_eql_raid,
})
