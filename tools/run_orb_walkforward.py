"""ORB walk-forward: rolling IS/OOS windows, sequential arm/grid selection on IS,
blind OOS, stitch OOS ledgers, apply the gate, write an audit report."""
from __future__ import annotations
import csv, os, sys
from datetime import date
from dateutil.relativedelta import relativedelta   # python-dateutil
# repo's tools/ is NOT a package — add this dir to sys.path and import siblings directly
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path: sys.path.insert(0, _HERE)
import orb_gate, audit
from run_orb_backtest import run

def _d(s): y,m,d = map(int, s.replace(".","-").split("-")); return date(y,m,d)
def _s(d): return f"{d.year:04d}.{d.month:02d}.{d.day:02d}"

def rolling_windows(start, end, is_months=12, oos_months=3):
    s, e = _d(start), _d(end); out=[]
    is_from = s
    while True:
        oos_from = is_from + relativedelta(months=is_months)
        oos_to   = oos_from + relativedelta(months=oos_months)
        if oos_to > e: break
        out.append(dict(is_from=_s(is_from), is_to=_s(oos_from),
                        oos_from=_s(oos_from), oos_to=_s(oos_to)))
        is_from = is_from + relativedelta(months=oos_months)
    return out

def stitch_oos(ledger_row_lists):
    out=[]
    for x in ledger_row_lists: out.extend(x)
    return out

def select_on_is(symbol, win, candidates):
    """candidates: list of (label, set_file). Return (set_file, label) with best IS Sharpe."""
    best=None
    for label,setf in candidates:
        ledg = run(symbol, win["is_from"], win["is_to"], setf, f"is_{label}_{win['oos_from']}")
        rows = orb_gate.read_ledger(ledg)
        sh = orb_gate.sharpe([float(r["net_pnl"]) for r in rows])
        if best is None or sh>best[0]: best=(sh,setf,label)
    return best[1], best[2]

def walk(symbol, start, end, candidates, is_months=12, oos_months=3, run_name="ORB"):
    rep = audit.new_report(run_name)
    wins = rolling_windows(start, end, is_months, oos_months)
    oos_lists=[]
    for win in wins:
        winner_set, winner_label = select_on_is(symbol, win, candidates)
        ledg = run(symbol, win["oos_from"], win["oos_to"], winner_set, f"oos_{winner_label}_{win['oos_from']}")
        rows = orb_gate.read_ledger(ledg); oos_lists.append(rows)
        audit.add(rep, ledg)
    stitched = stitch_oos(oos_lists)
    m = orb_gate.metrics_from_rows(stitched)
    oos_sh = orb_gate.sharpe([float(r["net_pnl"]) for r in stitched])
    verdict = orb_gate.apply_gate(m, oos_sharpe=oos_sh, is_sharpe=oos_sh)
    stitched_path=os.path.join(rep,"oos_stitched.csv")
    if stitched:
        with open(stitched_path,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(stitched[0].keys())); w.writeheader(); w.writerows(stitched)
    # stitched_path already lives inside the report dir — do NOT audit.add it (that self-copies -> WinError 32)
    audit.write_manifest(rep, title=f"{run_name} walk-forward {symbol}",
        summary_lines=[f"OOS trades={m['trades']} net={m['net']:.0f} PF={m['pf']:.2f} "
                       f"maxDD={m['max_dd']:.1%} Sharpe={oos_sh:.2f} "
                       f"PASS={verdict['passed']}", *(f"- {r}" for r in verdict['reasons'])],
        metrics=dict(trades=m["trades"], net=round(m["net"],2), pf=round(m["pf"],2),
                     max_dd=round(m["max_dd"],4), oos_sharpe=round(oos_sh,2), passed=verdict["passed"]),
        kind="backtest")
    return verdict, rep
