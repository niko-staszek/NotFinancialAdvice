"""Scratch: Tesla-trap check — long/short P&L split + buy-and-hold benchmark."""
import sys, os, csv, collections, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from orb_gate import read_ledger

common = os.path.join(os.environ['APPDATA'], 'MetaQuotes', 'Terminal', 'Common', 'Files', 'ORB')
for lab in ('full_e0', 'full_e3', 'full_e1_2r'):
    rows = read_ledger(os.path.join(common, f'ledger_{lab}.csv'))
    bydir = collections.defaultdict(lambda: [0, 0.0])
    for r in rows:
        bydir[r['dir']][0] += 1; bydir[r['dir']][1] += float(r['net_pnl'])
    print(f"{lab:12} by dir:", {d: (c, round(n, 1)) for d, (c, n) in bydir.items()})

import MetaTrader5 as mt5
mt5.initialize(path=r"C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe")
r = mt5.copy_rates_range('US100.cash', mt5.TIMEFRAME_D1, dt.datetime(2021, 10, 1), dt.datetime(2026, 6, 2))
if r is not None and len(r):
    c0, c1 = float(r[0]['close']), float(r[-1]['close'])
    print(f"US100 buy&hold {c0:.0f} -> {c1:.0f} = {100*(c1/c0-1):+.0f}% over the period "
          f"(strategy risks 1%/trade on $10k, so B&H% and strategy% are NOT directly comparable "
          f"in $ but the DIRECTION/exposure question stands)")
mt5.shutdown()
