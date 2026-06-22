"""ORB acceptance gate — the repo validation rules, codified. Pure functions."""
from __future__ import annotations
import csv, math
from typing import Iterable

GATE = dict(
    sharpe_floor=0.5, sharpe_ceiling=2.5, max_dd_limit=-0.30,
    min_trades=30, max_single_frac=0.30, oos_over_is_max=1.30,
)

def read_ledger(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def metrics_from_rows(rows: Iterable[dict]) -> dict:
    nets = [float(r["net_pnl"]) for r in rows]
    n = len(nets); net = sum(nets)
    gross_win = sum(x for x in nets if x > 0); gross_loss = -sum(x for x in nets if x < 0)
    pf = (gross_win / gross_loss) if gross_loss > 0 else float("inf")
    eq, peak, max_dd = 0.0, 0.0, 0.0
    for x in nets:
        eq += x; peak = max(peak, eq)
        if peak > 0: max_dd = min(max_dd, (eq - peak) / peak)
    max_single = max((abs(x) for x in nets), default=0.0)
    return dict(trades=n, net=net, pf=pf, max_dd=max_dd,
                max_single_frac=(max_single/abs(net) if net else 0.0),
                wins=sum(1 for x in nets if x > 0))

def apply_gate(m: dict, oos_sharpe: float, is_sharpe: float) -> dict:
    reasons = []
    if m["trades"] < GATE["min_trades"]: reasons.append(f"trade count {m['trades']} < {GATE['min_trades']}")
    if oos_sharpe < GATE["sharpe_floor"]: reasons.append(f"OOS Sharpe {oos_sharpe:.2f} < {GATE['sharpe_floor']} (noise)")
    if oos_sharpe > GATE["sharpe_ceiling"]: reasons.append(f"OOS Sharpe {oos_sharpe:.2f} > {GATE['sharpe_ceiling']} (asset did it)")
    if is_sharpe > 0 and oos_sharpe > is_sharpe*GATE["oos_over_is_max"]:
        reasons.append(f"OOS Sharpe beats IS by >30% (luck)")
    if m["max_dd"] < GATE["max_dd_limit"]: reasons.append(f"max DD {m['max_dd']:.1%} worse than {GATE['max_dd_limit']:.0%}")
    if m["max_single_frac"] > GATE["max_single_frac"]:
        reasons.append(f"profit concentration {m['max_single_frac']:.0%} > {GATE['max_single_frac']:.0%}")
    return dict(passed=(len(reasons) == 0), reasons=reasons, metrics=m,
                oos_sharpe=oos_sharpe, is_sharpe=is_sharpe)

def sharpe(nets: list[float]) -> float:
    if len(nets) < 2: return 0.0
    mu = sum(nets)/len(nets); var = sum((x-mu)**2 for x in nets)/(len(nets)-1)
    sd = math.sqrt(var); return (mu/sd*math.sqrt(len(nets))) if sd > 0 else 0.0
