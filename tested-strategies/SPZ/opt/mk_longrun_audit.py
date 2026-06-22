"""Snapshot the 2.5-year MT5 backtest of the 3 winners into an audit folder."""
import os, sys, glob, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
import audit

COMMON = os.path.join(os.environ["APPDATA"], "MetaQuotes", "Terminal", "Common", "Files", "SPZ")
EA = os.path.join(os.path.dirname(__file__), "..", "mt5", "ScalperProReconEA.mq5")
WINNERS = ["XAUUSD", "BTCUSD", "US100.cash"]   # these result files now hold the 2024-2026 run

rpt = audit.new_report("spz-mt5-longrun")
rows = []
for sym in WINNERS:
    p = os.path.join(COMMON, f"result_{sym}.txt")
    if not os.path.exists(p):
        continue
    txt = open(p, encoding="utf-16").read().strip()
    audit.add(rpt, p)
    g = dict(re.findall(r"(\w+)=([-\d.A-Za-z_]+)", txt))
    rows.append({"sym": sym, "tf": g.get("tf", "").replace("PERIOD_", ""),
                 "pf": float(g.get("pf", "nan")), "ddpct": float(g.get("ddpct", "nan")),
                 "trades": int(float(g.get("trades", "0"))), "net": float(g.get("net", "0"))})
audit.add(rpt, EA)

audit.write_manifest(
    rpt, "SPZ recon EA — 2.5-year MT5 backtest (FTMO real-tick, 2024-01..2026-06)",
    summary_lines=[
        "RECON EA, FTMO feed, real ticks, 100k, risk 0.625%/trade, Intraday 13/34; n now significant",
        "XAUUSD H1: PF 1.23, maxDD 15.1% (BREACHES 10% prop cap at this sizing), n265, +23%",
        "BTCUSD H4: PF 1.27, maxDD 7.4%, n98, +9%",
        "US100 H4:  PF 0.86 -> LOSES over the long window (6-month win was regime luck), n83",
        "VERDICT: 6-month numbers were optimistic; long-sample edge is MARGINAL (PF ~1.2-1.3, gross of",
        "commission) and gold DD breaches prop limits at the assumed size. Does NOT clear the gate.",
    ],
    kind="backtest",
    metrics={f"{r['sym']}_pf": round(r["pf"], 2) for r in rows}
          | {f"{r['sym']}_ddpct": round(r["ddpct"], 2) for r in rows},
    preview=["| symbol | TF | PF | maxDD% | trades | net |", "|---|---|---:|---:|---:|---:|"]
          + [f"| {r['sym']} | {r['tf']} | {r['pf']:.2f} | {r['ddpct']:.2f} | {r['trades']} | {r['net']:+.0f} |" for r in rows],
)
print("audit folder:", rpt)
for r in rows:
    print(f"{r['sym']:14s} pf={r['pf']:.2f} dd={r['ddpct']:.2f}% n={r['trades']} net={r['net']:+.0f}")
