"""Scratch: cross-instrument edge-vs-exposure — OOS-filtered gate + long/short split."""
import sys, os, calendar, datetime as dt, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orb_gate import read_ledger, metrics_from_rows, sharpe, apply_gate

lo = calendar.timegm(dt.datetime(2022, 10, 1).timetuple())
hi = calendar.timegm(dt.datetime(2026, 4, 1).timetuple())
common = os.path.join(os.environ['APPDATA'], 'MetaQuotes', 'Terminal', 'Common', 'Files', 'ORB')

labels = ['full_e0', 'full_e3', 'us500_e0', 'us500_e3', 'us30_e0', 'us30_e3']
print(f"{'label':10} {'inst':6} {'exit':4}  n   win%   PF    Sharpe   net    DD%    long    short   PASS")
for lab in labels:
    p = os.path.join(common, f'ledger_{lab}.csv')
    if not os.path.exists(p):
        print(lab, 'MISSING'); continue
    rows = [r for r in read_ledger(p) if lo <= int(r['ts_open_utc']) < hi]
    if not rows:
        print(lab, 'no OOS rows'); continue
    m = metrics_from_rows(rows); nets = [float(r['net_pnl']) for r in rows]; sh = sharpe(nets)
    v = apply_gate(m, oos_sharpe=sh, is_sharpe=sh)
    bd = collections.defaultdict(float)
    for r in rows: bd[r['dir']] += float(r['net_pnl'])
    inst = 'US100' if lab.startswith('full') else lab.split('_')[0].upper()
    ex = lab.split('_')[-1].upper()
    print(f"{lab:10} {inst:6} {ex:4} {m['trades']:3} {100*m['wins']/m['trades']:5.1f} "
          f"{m['pf']:5.2f} {sh:+6.2f} {m['net']:+7.0f} {m['max_dd']*100:5.1f} "
          f"{bd['long']:+7.0f} {bd['short']:+7.0f}  {v['passed']}")
