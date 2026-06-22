"""Snapshot the MT5 Strategy-Tester run (FTMO feed) into an audit folder."""
import os, sys, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
import audit

APPDATA = os.environ["APPDATA"]
DATA = os.path.join(APPDATA, "MetaQuotes", "Terminal", "81A933A9AFC5DE3C23B15CAB19C63850")
COMMON = os.path.join(APPDATA, "MetaQuotes", "Terminal", "Common", "Files", "SPZ")
EA = os.path.join(os.path.dirname(__file__), "..", "mt5", "ScalperProReconEA.mq5")

import re
rpt = audit.new_report("spz-mt5-test")

# every result_<symbol>.txt the EA emitted (verbatim)
results = {}
parsed = []
for p in sorted(glob.glob(os.path.join(COMMON, "result_*.txt"))):
    txt = open(p, encoding="utf-16").read().strip()
    sym = os.path.basename(p)[len("result_"):-len(".txt")]
    results[sym] = txt
    audit.add(rpt, p)
    g = dict(re.findall(r"(\w+)=([-\d.A-Za-z_]+)", txt))
    parsed.append({"sym": sym, "tf": g.get("tf", "").replace("PERIOD_", ""),
                   "pf": float(g.get("pf", "nan")), "ddpct": float(g.get("ddpct", "nan")),
                   "trades": int(float(g.get("trades", "0"))), "net": float(g.get("net", "0"))})
parsed.sort(key=lambda r: -r["pf"])

# pull the RESULT + balance lines straight from the latest tester log as execution proof
tlogs = sorted(glob.glob(os.path.join(DATA, "Tester", "logs", "*.log")), key=os.path.getmtime)
loglines = []
if tlogs:
    for ln in open(tlogs[-1], encoding="utf-8", errors="ignore"):
        if "RESULT symbol=" in ln or "final balance" in ln:
            loglines.append(ln.rstrip())
open(os.path.join(rpt, "tester_result_lines.txt"), "w", encoding="utf-8").write("\n".join(loglines) + "\n")

# snapshot EA + presets + inis
audit.add(rpt, EA)
for f in glob.glob(os.path.join(DATA, "spz_*.ini")):
    audit.add(rpt, f)
sset = os.path.join(DATA, "MQL5", "Profiles", "Tester", "SPZ.set")
if os.path.exists(sset):
    audit.add(rpt, sset)

audit.write_manifest(
    rpt, "SPZ recon EA — MT5 Strategy Tester (FTMO real-tick, 2025-12..2026-06)",
    summary_lines=[
        "self-contained MQL5 EA of the recon, FTMO feed, real ticks, 100k deposit, risk 0.625%/trade, Intraday 13/34",
        "WINNERS: XAUUSD H1 (PF 1.65, n56), BTCUSD H4 (2.33, n17), US100 H4 (1.79, n15)",
        "LOSERS:  US500 (0.73), GER40 (0.63), US30 (0.93) -> do NOT trade these with this EA",
        "instrument-specific edge (gold/BTC/Nasdaq = the user's stated combos); does NOT generalize to S&P/DAX/Dow",
        "ALL non-gold n<30 -> NOT significant; single 6-month window; gross of commission; NOT OOS-validated; demo-forward-test before live",
    ],
    kind="backtest",
    metrics={f"{r['sym']}_pf": round(r["pf"], 2) for r in parsed}
          | {f"{r['sym']}_ddpct": round(r["ddpct"], 2) for r in parsed},
    preview=["| symbol | TF | PF | maxDD% | trades | net |", "|---|---|---:|---:|---:|---:|"]
          + [f"| {r['sym']} | {r['tf']} | {r['pf']:.2f} | {r['ddpct']:.2f} | {r['trades']} | {r['net']:+.0f} |" for r in parsed],
)
print("audit folder:", rpt)
for r in parsed:
    print(f"{r['sym']:14s} pf={r['pf']:.2f} dd={r['ddpct']:.2f}% n={r['trades']} net={r['net']:+.0f}")
