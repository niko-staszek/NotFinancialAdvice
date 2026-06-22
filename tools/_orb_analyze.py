"""Scratch: analyze ORB walk-forward OOS exits + per-day diag reject reasons."""
import csv, collections, glob, os

st = list(csv.DictReader(open(r'tested-strategies/ORB/reports/ORB-sl-20260622-103849Z/oos_stitched.csv')))
print('OOS trades', len(st))
print('exit_reason', dict(collections.Counter(r['exit_reason'] for r in st)))
print('dir', dict(collections.Counter(r['dir'] for r in st)))
print('stop_arm', dict(collections.Counter(r['stop_arm'] for r in st)))

byr = collections.defaultdict(lambda: [0, 0.0])
for r in st:
    k = r['exit_reason']; byr[k][0] += 1; byr[k][1] += float(r['net_pnl'])
print('net by exit', {k: (c, round(n, 1)) for k, (c, n) in byr.items()})

# scan OOS diag files for arm/reject tally (order_fail = gap-and-go rejection)
common = os.path.join(os.environ['APPDATA'], 'MetaQuotes', 'Terminal', 'Common', 'Files', 'ORB')
tally = collections.Counter()
for f in glob.glob(os.path.join(common, 'diag_oos_*.csv')):
    for line in open(f, encoding='ansi', errors='ignore'):
        last = line.strip().rsplit(',', 1)[-1]
        if last in ('armed', 'warmup', 'rvol_low', 'range_guard', 'bias_flat', 'lots_zero', 'order_fail'):
            tally[last] += 1
print('OOS diag reasons', dict(tally))
