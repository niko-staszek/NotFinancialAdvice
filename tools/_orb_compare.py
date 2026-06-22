"""Scratch: gate the full-period exit-sweep ledgers."""
import sys, os, csv, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from orb_gate import read_ledger, metrics_from_rows, sharpe, apply_gate

common = os.path.join(os.environ['APPDATA'], 'MetaQuotes', 'Terminal', 'Common', 'Files', 'ORB')
for lab in ('full_e0', 'full_e3', 'full_e1_2r'):
    rows = read_ledger(os.path.join(common, f'ledger_{lab}.csv'))
    if not rows:
        print(lab, 'EMPTY'); continue
    m = metrics_from_rows(rows)
    nets = [float(r['net_pnl']) for r in rows]
    sh = sharpe(nets)
    v = apply_gate(m, oos_sharpe=sh, is_sharpe=sh)
    ex = dict(collections.Counter(r['exit_reason'] for r in rows))
    wr = round(100 * m['wins'] / m['trades'], 1)
    print(f"{lab:12} trades={m['trades']:4} win%={wr:5} PF={m['pf']:.3f} Sharpe={sh:+.2f} "
          f"net={m['net']:+.0f} DD={m['max_dd']*100:+.1f}% conc={m['max_single_frac']*100:.0f}% "
          f"PASS={v['passed']}")
    print(f"             exits={ex}")
