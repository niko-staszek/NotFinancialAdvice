"""
Max drawdown of the SPZ reconstruction at RECOMMENDED settings (v3.2 defaults: Swing 21/50,
minScore 60, SL 2.8xATR, R:R 1/2/3, cooldown 25, session 07-18) on the user's best combos:
  XAUUSD H1, BTCUSD H4, EURUSD H1  (HTF = 4h for H1 base, 1D for H4 base).
NOTE: this is the RECONSTRUCTION's drawdown, not the original Scalper Pro's (whose DD is not
exposed). Fixed settings => no parameter selection here; still one in-sample period, GROSS of costs.
"""
import os, sys, json
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
import recon, audit

DATA = os.path.join(os.path.dirname(__file__), "..", "..", "..", "CBS", "data")
INSTR = [
    ("XAUUSD", "XAUUSD_M5_2024-06-10_2026-06-10.csv", "1h", "4h"),
    ("BTCUSD", "BTCUSD_M5_2024-06-10_2026-06-10.csv", "4h", "1D"),
    ("EURUSD", "EURUSD_M5_2024-06-10_2026-06-10.csv", "1h", "4h"),
]


def run():
    rpt = audit.new_report("spz-drawdown")
    log = ["config applied: recommended = " + json.dumps(recon.DEFAULTS)]
    rows = []
    for name, fn, tf, htf in INSTR:
        bars = recon.load_tf(os.path.join(DATA, fn), tf)
        f = recon.add_regime_score(recon.build_base(bars, recon.DEFAULTS, htf_rule=htf), recon.DEFAULTS)
        t = recon.simulate(f, recon.DEFAULTS)
        s = recon.stats(t)
        dd1 = recon.equity_dd(t, 1.0)
        dd2 = recon.equity_dd(t, 2.0)
        bh = float(bars["close"].iloc[-1] / bars["close"].iloc[0] - 1.0)
        row = {
            "instrument": name, "tf": tf, "bars": len(bars),
            "from": str(bars.index[0].date()), "to": str(bars.index[-1].date()),
            "trades": s["n"], "pf": round(s["pf"], 2) if s["pf"] == s["pf"] else None,
            "exp_R": round(s["exp"], 3) if s["exp"] == s["exp"] else None,
            "win_pct": round(s["win_rate"] * 100, 1) if s["win_rate"] == s["win_rate"] else None,
            "maxdd_R": round(dd1["maxdd_R"], 1),
            "maxdd_pct_at_1pct": round(dd1["maxdd_pct"], 1),
            "maxdd_pct_at_2pct": round(dd2["maxdd_pct"], 1),
            "net_R": round(dd1["final_R"], 1),
            "buyhold_pct": round(bh * 100, 1),
        }
        rows.append(row)
        if len(t):
            t.to_csv(os.path.join(rpt, f"trades_{name}_{tf}.csv"), index=False)
        line = (f"{name} {tf}: n={s['n']} pf={row['pf']} exp={row['exp_R']}R win={row['win_pct']}% "
                f"| MAX DD = {row['maxdd_R']}R  ({row['maxdd_pct_at_1pct']}% @1%/trade, "
                f"{row['maxdd_pct_at_2pct']}% @2%/trade)  net={row['net_R']}R  B&H={row['buyhold_pct']}%")
        log.append(line); print(line)

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(rpt, "drawdown_summary.csv"), index=False)
    with open(os.path.join(rpt, "config.json"), "w") as fh:
        json.dump({"settings": recon.DEFAULTS, "instruments": INSTR}, fh, indent=2)
    with open(os.path.join(rpt, "runlog.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(log) + "\nrun complete\n")
    audit.add(rpt, os.path.join(os.path.dirname(__file__), "run_dd.py"))
    audit.add(rpt, os.path.join(os.path.dirname(__file__), "recon.py"))

    # auto-reject-gate notes (per docs/strategy-validation): DD worse than -35% (tighter for FX)
    gate = []
    for r in rows:
        flags = []
        if r["trades"] < 30:
            flags.append(f"n={r['trades']}<30 not significant")
        if r["maxdd_pct_at_2pct"] is not None and r["maxdd_pct_at_2pct"] > 35:
            flags.append(f"DD@2% {r['maxdd_pct_at_2pct']}% breaches -35% gate")
        gate.append(f"{r['instrument']}: " + ("; ".join(flags) if flags else "within gate (gross of costs)"))

    audit.write_manifest(
        rpt, "SPZ reconstruction — max drawdown at recommended settings",
        summary_lines=[
            "RECON (not original) drawdown, v3.2 defaults, GROSS of costs, single in-sample period",
        ] + [
            f"{r['instrument']} {r['tf']}: max DD {r['maxdd_R']}R = {r['maxdd_pct_at_1pct']}%/{r['maxdd_pct_at_2pct']}% "
            f"@1%/2% risk; PF {r['pf']}, {r['trades']} trades; B&H {r['buyhold_pct']}%"
            for r in rows
        ] + gate,
        kind="backtest",
        metrics={f"{r['instrument']}_maxdd_R": r["maxdd_R"] for r in rows}
              | {f"{r['instrument']}_pf": r["pf"] for r in rows},
        preview=["| instrument | TF | trades | PF | max DD (R) | DD% @1% | DD% @2% |",
                 "|---|---|---:|---:|---:|---:|---:|"]
              + [f"| {r['instrument']} | {r['tf']} | {r['trades']} | {r['pf']} | {r['maxdd_R']} | {r['maxdd_pct_at_1pct']} | {r['maxdd_pct_at_2pct']} |" for r in rows],
    )
    print("audit folder:", rpt)
    return rpt


if __name__ == "__main__":
    run()
