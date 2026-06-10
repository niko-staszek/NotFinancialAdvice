"""Driver wiring timing + entry evaluation across the window grid, per instrument."""
from __future__ import annotations

from datetime import timedelta

import pandas as pd

from .timing import measure_move, TimingRecord
from .entries import build_context, DETECTORS
from .evaluate import evaluate_entry, EntryResult, evaluate_entry_rr


def _trading_days(df: pd.DataFrame) -> list[str]:
    return sorted(df["time_utc"].dt.strftime("%Y-%m-%d").unique().tolist())


def split_in_out_sample(df: pd.DataFrame, *, oos_months: int = 6,
                        date_col: str = "date") -> pd.DataFrame:
    """Tag rows 'in_sample'/'oos': oos = strictly after (latest_date - oos_months)."""
    d = df.copy()
    d[date_col] = pd.to_datetime(d[date_col])
    cutoff = d[date_col].max() - pd.DateOffset(months=oos_months)
    d["split"] = "in_sample"
    d.loc[d[date_col] > cutoff, "split"] = "oos"
    return d


def run_instrument(df: pd.DataFrame, *, symbol: str, pip_size: float, base_tol_pips: float,
                   anchors, blocks, tol_mults, cap_hours: int, atr_period: int,
                   atr_k: float, lookback_hours: int,
                   entry_tol_mult: int = 1,
                   min_risk_atr_k: float = 0.5,
                   rr_list=(1.0, 2.0, 3.0),
                   settle_tol: float = 0.0) -> tuple[list[TimingRecord], list[EntryResult], list]:
    """Run the full grid for one instrument. Returns (timing_records, entry_results, rr_rows).

    Timing is recorded for every tolerance tier (feeds T1 sensitivity). Entries are
    evaluated only at `entry_tol_mult` (default 1, the PSND baseline) so the same
    move is not counted into T2 once per tier.
    """
    timing: list[TimingRecord] = []
    entries: list[EntryResult] = []
    rr_rows: list = []
    days = _trading_days(df)

    for date in days:
        for anchor in anchors:
            for block in blocks:
                for tol_mult in tol_mults:
                    tol_price = base_tol_pips * pip_size * tol_mult
                    try:
                        rec = measure_move(df, symbol=symbol, anchor=anchor, block=block,
                                           tol_price=tol_price, cap_hours=cap_hours,
                                           date=date, tol_mult=tol_mult)
                    except ValueError:
                        continue
                    timing.append(rec)

                    if tol_mult != entry_tol_mult:
                        continue
                    if not rec.completed or rec.instant:
                        continue
                    close_ts = pd.Timestamp(f"{date}T00:00:00", tz="UTC") + timedelta(hours=anchor + block)
                    comp_ts = close_ts + timedelta(hours=rec.hours_to_complete)
                    ctx = build_context(df, symbol=symbol, window_close_ts=close_ts,
                                        completion_ts=comp_ts, target=rec.target,
                                        approach_side=rec.approach_side, pip_size=pip_size,
                                        lookback_hours=lookback_hours, atr_period=atr_period,
                                        atr_k=atr_k)
                    # A market gap (weekend/session break) can leave the clipped context
                    # with no bar before or after window close — detectors that reference
                    # the window-close bar can't be evaluated, so skip the window.
                    has_pre = bool((ctx.m5["time_utc"] < close_ts).any())
                    has_post = bool((ctx.m5["time_utc"] >= close_ts).any())
                    if not has_pre or not has_post:
                        continue
                    min_risk = min_risk_atr_k * ctx.atr_m5
                    for name, fn in DETECTORS.items():
                        sig = fn(ctx)
                        if sig is None:
                            continue
                        entries.append(evaluate_entry(ctx, sig, date=date,
                                                      anchor=anchor, block=block,
                                                      min_risk=min_risk))
                        rr_rows.extend(evaluate_entry_rr(ctx, sig, date=date,
                                                         anchor=anchor, block=block,
                                                         rr_list=rr_list,
                                                         settle_tol=settle_tol))
    return timing, entries, rr_rows
