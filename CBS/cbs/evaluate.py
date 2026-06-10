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
                   anchor: int, block: int) -> EntryResult:
    side_up = ctx.approach_side == "up"
    risk = (sig.entry_price - sig.invalidation_price) if side_up else (sig.invalidation_price - sig.entry_price)
    reward = (ctx.target - sig.entry_price) if side_up else (sig.entry_price - ctx.target)
    r_mult = math.nan if risk <= 0 else reward / risk

    path = ctx.m5.loc[ctx.m5["time_utc"] >= sig.entry_time].reset_index(drop=True)
    spread_price = 0.0
    if len(path):
        spread_price = float(path["spread"].iloc[0]) * ctx.pip_size

    if len(path) == 0:
        return EntryResult(
            symbol=ctx.symbol, date=date, anchor=anchor, block=block, name=sig.name,
            entry_price=sig.entry_price, invalidation_price=sig.invalidation_price,
            target=ctx.target, r_multiple=r_mult, mfe_r=math.nan, mae_r=math.nan,
            realized_r=math.nan, win=False, cost_spread_price=spread_price,
            entry_lead_hours=(ctx.completion_ts - sig.entry_time).total_seconds() / 3600.0,
        )

    win = False
    mfe = 0.0
    mae = 0.0
    for row in path.itertuples(index=False):
        if side_up:
            mfe = max(mfe, row.high - sig.entry_price)
            mae = min(mae, row.low - sig.entry_price)
            hit_sl = row.low <= sig.invalidation_price
            hit_tp = row.high >= ctx.target
        else:
            mfe = max(mfe, sig.entry_price - row.low)
            mae = min(mae, sig.entry_price - row.high)
            hit_sl = row.high >= sig.invalidation_price
            hit_tp = row.low <= ctx.target
        if hit_sl:
            win = False
            break
        if hit_tp:
            win = True
            break

    mfe_r = math.nan if risk <= 0 else mfe / risk
    mae_r = math.nan if risk <= 0 else mae / risk
    realized_r = math.nan if risk <= 0 else (r_mult if win else -1.0)
    lead = (ctx.completion_ts - sig.entry_time).total_seconds() / 3600.0

    return EntryResult(
        symbol=ctx.symbol, date=date, anchor=anchor, block=block, name=sig.name,
        entry_price=sig.entry_price, invalidation_price=sig.invalidation_price,
        target=ctx.target, r_multiple=r_mult, mfe_r=mfe_r, mae_r=mae_r,
        realized_r=realized_r, win=win,
        cost_spread_price=spread_price, entry_lead_hours=lead,
    )
