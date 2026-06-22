"""Scratch: filter the full-period ledgers to the walk-forward OOS span and gate.
OOS segments (is=12/oos=3, 2021-10..2026-06) are contiguous 2022-10-01 .. 2026-04-01."""
import sys, os, calendar, datetime as dt, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orb_gate import read_ledger, metrics_from_rows, sharpe, apply_gate

lo = calendar.timegm(dt.datetime(2022, 10, 1).timetuple())
hi = calendar.timegm(dt.datetime(2026, 4, 1).timetuple())
common = os.path.join(os.environ['APPDATA'], 'MetaQuotes', 'Terminal', 'Common', 'Files', 'ORB')

for lab in ('full_e0', 'full_e3', 'full_e1_2r'):
    rows = read_ledger(os.path.join(common, f'ledger_{lab}.csv'))
    oos = [r for r in rows if lo <= int(r['ts_open_utc']) < hi]
    if not oos:
        print(lab, 'no OOS rows'); continue
    m = metrics_from_rows(oos)
    nets = [float(r['net_pnl']) for r in oos]
    sh = sharpe(nets)
    v = apply_gate(m, oos_sharpe=sh, is_sharpe=sh)
    bydir = collections.defaultdict(float)
    for r in oos:
        bydir[r['dir']] += float(r['net_pnl'])
    wr = round(100 * m['wins'] / m['trades'], 1)
    print(f"{lab:12} OOS-only n={m['trades']:4} win%={wr:5} PF={m['pf']:.3f} Sharpe={sh:+.2f} "
          f"net={m['net']:+.0f} DD={m['max_dd']*100:+.1f}% long={bydir['long']:+.0f} short={bydir['short']:+.0f} "
          f"PASS={v['passed']}")
