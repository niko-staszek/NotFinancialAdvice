"""Engine B — evaluate one entry signal against the measured move.

Holds from entry to target, walking M5 bars from entry_time to completion. Computes
R-multiple, MFE/MAE in R units, win/loss (target vs invalidation, whichever first),
and spread cost. Lookahead-safe: only bars at/after entry_time are walked, and the
target/invalidation are known at entry.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from .entries import EntryContext, EntrySignal


@dataclass(frozen=True)
class EntryResult:
    symbol: str
    date: str
    anchor: int
    block: int
    name: str
    entry_price: float
    invalidation_price: float
    target: float
    r_multiple: float
    mfe_r: float
    mae_r: float
    realized_r: float
    win: bool
    cost_spread_price: float
    entry_lead_hours: float


def evaluate_entry(ctx: EntryContext, sig: EntrySignal, *, date: str,
                   anchor: int, block: int, min_risk: float = 0.0) -> EntryResult:
    side_up = ctx.approach_side == "up"
    raw_risk = (sig.entry_price - sig.invalidation_price) if side_up else (sig.invalidation_price - sig.entry_price)
    # A structural stop that sits a hair from entry makes planned R explode toward
    # infinity (tiny denominator). Enforce a minimum stop distance: when the raw
    # stop is tighter than `min_risk`, widen the invalidation to that floor so R
    # stays a realistic, comparable number.
    invalidation = sig.invalidation_price
    risk = raw_risk
    if min_risk > 0 and 0 < raw_risk < min_risk:
        risk = min_risk
        invalidation = sig.entry_price - min_risk if side_up else sig.entry_price + min_risk
    reward = (ctx.target - sig.entry_price) if side_up else (sig.entry_price - ctx.target)
    r_mult = math.nan if risk <= 0 else reward / risk

    i = int(ctx.m5["time_utc"].searchsorted(sig.entry_time, side="left"))
    path = ctx.m5.iloc[i:]
    spread_price = 0.0
    if len(path):
        spread_price = float(path["spread"].iloc[0]) * ctx.pip_size

    if len(path) == 0:
        return EntryResult(
            symbol=ctx.symbol, date=date, anchor=anchor, block=block, name=sig.name,
            entry_price=sig.entry_price, invalidation_price=invalidation,
            target=ctx.target, r_multiple=r_mult, mfe_r=math.nan, mae_r=math.nan,
            realized_r=math.nan, win=False, cost_spread_price=spread_price,
            entry_lead_hours=(ctx.completion_ts - sig.entry_time).total_seconds() / 3600.0,
        )

    # Vectorized hold-to-target walk. SL is checked first on a bar that spans both
    # levels (conservative loss). MFE/MAE accumulate up to and including the first
    # event bar (or the whole path if neither level is hit).
    lows = path["low"].to_numpy()
    highs = path["high"].to_numpy()
    if side_up:
        hit_sl = lows <= invalidation
        hit_tp = highs >= ctx.target
        fav = highs - sig.entry_price
        adv = lows - sig.entry_price
    else:
        hit_sl = highs >= invalidation
        hit_tp = lows <= ctx.target
        fav = sig.entry_price - lows
        adv = sig.entry_price - highs

    event = hit_sl | hit_tp
    if event.any():
        k = int(event.argmax())
        win = bool(hit_tp[k] and not hit_sl[k])
        end = k + 1
    else:
        win = False
        end = len(path)
    mfe = max(0.0, float(fav[:end].max()))
    mae = min(0.0, float(adv[:end].min()))

    mfe_r = math.nan if risk <= 0 else mfe / risk
    mae_r = math.nan if risk <= 0 else mae / risk
    realized_r = math.nan if risk <= 0 else (r_mult if win else -1.0)
    lead = (ctx.completion_ts - sig.entry_time).total_seconds() / 3600.0

    return EntryResult(
        symbol=ctx.symbol, date=date, anchor=anchor, block=block, name=sig.name,
        entry_price=sig.entry_price, invalidation_price=invalidation,
        target=ctx.target, r_multiple=r_mult, mfe_r=mfe_r, mae_r=mae_r,
        realized_r=realized_r, win=win,
        cost_spread_price=spread_price, entry_lead_hours=lead,
    )
