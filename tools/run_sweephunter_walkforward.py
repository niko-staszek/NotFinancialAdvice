"""SweepHunter walk-forward: rolling IS/OOS, select best-IS-Sharpe candidate, blind OOS,
stitch OOS ledgers, apply orb_gate, write an audit report dir. Pass timestamp via --stamp
(scripts cannot call Date.now)."""
from __future__ import annotations
import argparse, csv, hashlib, os, sys
from datetime import date
from dateutil.relativedelta import relativedelta
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path: sys.path.insert(0, _HERE)
import orb_gate
from run_sweephunter_backtest import run

CANDIDATES = [  # (label, set_file)
    ("rr",          "SweepHunter_rr.set"),
    ("dol",         "SweepHunter_dol.set"),
    ("rr_combined", "SweepHunter_rr_combined.set"),
    ("dol_combined","SweepHunter_dol_combined.set"),
]

def _d(s): y,m,d = map(int, s.replace(".","-").split("-")); return date(y,m,d)
def _s(d): return f"{d.year:04d}.{d.month:02d}.{d.day:02d}"

def rolling_windows(start, end, is_months=12, oos_months=3):
    s, e = _d(start), _d(end); out=[]; is_from=s
    while True:
        oos_from = is_from + relativedelta(months=is_months)
        oos_to   = oos_from + relativedelta(months=oos_months)
        if oos_to > e: break
        out.append(dict(is_from=_s(is_from), is_to=_s(oos_from), oos_from=_s(oos_from), oos_to=_s(oos_to)))
        is_from = is_from + relativedelta(months=oos_months)
    return out

def select_on_is(symbol, win):
    best=None
    for label,setf in CANDIDATES:
        ledg = run(symbol, win["is_from"], win["is_to"], setf, f"is_{symbol}_{label}_{win['oos_from']}")
        rows = orb_gate.read_ledger(ledg)
        sh = orb_gate.sharpe([float(r["net_pnl"]) for r in rows])
        if best is None or sh>best[0]: best=(sh,setf,label)
    return best[1], best[2], best[0]

def walk(symbol, start, end, stamp, is_months=12, oos_months=3):
    repo = os.path.dirname(_HERE)
    rep = os.path.join(repo, "tested-strategies", "SweepHunter", "reports", f"SweepHunter-wf-{symbol}-{stamp}")
    os.makedirs(rep, exist_ok=True)
    wins = rolling_windows(start, end, is_months, oos_months)
    oos_rows=[]; is_sharpes=[]
    for win in wins:
        setf, label, is_sh = select_on_is(symbol, win)
        is_sharpes.append(is_sh)
        ledg = run(symbol, win["oos_from"], win["oos_to"], setf, f"oos_{symbol}_{label}_{win['oos_from']}")
        rows = orb_gate.read_ledger(ledg); oos_rows.extend(rows)
        # copy each OOS window ledger into the report dir
        with open(os.path.join(rep, f"ledger_oos_{label}_{win['oos_from']}.csv"),"w",newline="",encoding="utf-8") as f:
            if rows:
                w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    m = orb_gate.metrics_from_rows(oos_rows)
    oos_sh = orb_gate.sharpe([float(r["net_pnl"]) for r in oos_rows])
    is_sh_avg = sum(is_sharpes)/len(is_sharpes) if is_sharpes else 0.0
    verdict = orb_gate.apply_gate(m, oos_sharpe=oos_sh, is_sharpe=is_sh_avg)
    if oos_rows:
        with open(os.path.join(rep,"oos_stitched.csv"),"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(oos_rows[0].keys())); w.writeheader(); w.writerows(oos_rows)
    summary = [f"SweepHunter walk-forward {symbol} ({start}..{end})",
               f"OOS trades={m['trades']} net={m['net']:.0f} PF={m['pf']:.2f} maxDD={m['max_dd']:.1%} "
               f"OOS_Sharpe={oos_sh:.2f} IS_Sharpe(avg)={is_sh_avg:.2f} PASS={verdict['passed']}"]
    summary += [f"- {r}" for r in verdict["reasons"]]
    with open(os.path.join(rep,"gate.txt"),"w",encoding="utf-8") as f: f.write("\n".join(summary)+"\n")
    # manifest
    man=[]
    for fn in sorted(os.listdir(rep)):
        p=os.path.join(rep,fn)
        if os.path.isfile(p):
            man.append(f"{hashlib.sha256(open(p,'rb').read()).hexdigest()}  {fn}")
    with open(os.path.join(rep,"manifest.sha256"),"w",encoding="utf-8") as f: f.write("\n".join(man)+"\n")
    print("\n".join(summary)); print("report:", rep)
    return verdict, rep

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol"); ap.add_argument("start"); ap.add_argument("end")
    ap.add_argument("--stamp", required=True, help="UTC stamp, e.g. 20260622-1700Z")
    ap.add_argument("--is-months", type=int, default=12); ap.add_argument("--oos-months", type=int, default=3)
    a = ap.parse_args()
    v,_ = walk(a.symbol, a.start, a.end, a.stamp, a.is_months, a.oos_months)
    sys.exit(0 if v["passed"] else 2)
