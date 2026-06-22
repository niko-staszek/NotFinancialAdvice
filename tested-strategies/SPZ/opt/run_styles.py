"""
Sensitivity of the SPZ reconstruction to Trading Style and minScore, per instrument,
at otherwise-recommended settings. Style sets EMAs: Scalp 9/21, Intraday 13/34, Swing 21/50.
Reports trades / PF / expectancy / win% / max DD (R and % at 1%&2% risk) for each combo.

NOTE: my recon's score is coarse (votes x25 + adx x25, steps of 25), so minScore only has a
few effective levels: <=75 admits score>=75 (2 aligned+ADX, or 3 aligned); >75 requires score
100 (3 aligned + ADX strong). 50 also admits the weak 2-aligned-no-ADX case. So sweep 50/75/100.
"""
import os, sys, json, itertools
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
import recon, audit

DATA = os.path.join(os.path.dirname(__file__), "..", "..", "..", "CBS", "data")
INSTR = [   # name, file, tf, htf, recommended style (from user's combos)
    ("XAUUSD", "XAUUSD_M5_2024-06-10_2026-06-10.csv", "1h", "4h", "Scalp/Intraday"),
    ("BTCUSD", "BTCUSD_M5_2024-06-10_2026-06-10.csv", "4h", "1D", "Swing"),
    ("EURUSD", "EURUSD_M5_2024-06-10_2026-06-10.csv", "1h", "4h", "Swing"),
]
STYLE_EMA = {"Scalp": (9, 21), "Intraday": (13, 34), "Swing": (21, 50)}
MINSCORES = [50, 75, 100]


def run():
    rpt = audit.new_report("spz-style-minscore")
    rows, log = [], []
    for (name, fn, tf, htf, rec) in INSTR:
        bars = recon.load_tf(os.path.join(DATA, fn), tf)
        for style, (ef, es) in STYLE_EMA.items():
            base = recon.build_base(bars, {**recon.DEFAULTS, "emaFast": ef, "emaSlow": es}, htf_rule=htf)
            for ms in MINSCORES:
                p = {**recon.DEFAULTS, "emaFast": ef, "emaSlow": es, "minScore": ms}
                t = recon.simulate(recon.add_regime_score(base, p), p)
                s = recon.stats(t)
                dd1 = recon.equity_dd(t, 1.0); dd2 = recon.equity_dd(t, 2.0)
                row = {"instrument": name, "tf": tf, "rec_style": rec, "style": style, "emas": f"{ef}/{es}",
                       "minScore": ms, "trades": s["n"],
                       "pf": round(s["pf"], 2) if s["pf"] == s["pf"] else None,
                       "exp_R": round(s["exp"], 3) if s["exp"] == s["exp"] else None,
                       "win_pct": round(s["win_rate"] * 100, 1) if s["win_rate"] == s["win_rate"] else None,
                       "maxdd_R": round(dd1["maxdd_R"], 1),
                       "maxdd_pct_1": round(dd1["maxdd_pct"], 1), "maxdd_pct_2": round(dd2["maxdd_pct"], 1),
                       "net_R": round(dd1["final_R"], 1)}
                rows.append(row)
                log.append(f"{name} {tf} {style:8s}({ef}/{es}) ms={ms:3d}: n={s['n']:3d} pf={row['pf']} "
                           f"exp={row['exp_R']}R win={row['win_pct']}% maxDD={row['maxdd_R']}R net={row['net_R']}R")
    for l in log:
        print(l)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(rpt, "style_minscore_grid.csv"), index=False)
    with open(os.path.join(rpt, "config.json"), "w") as fh:
        json.dump({"defaults": recon.DEFAULTS, "styles": STYLE_EMA, "minScores": MINSCORES,
                   "instruments": [[i[0], i[2], i[4]] for i in INSTR]}, fh, indent=2)
    with open(os.path.join(rpt, "runlog.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(log) + "\nrun complete\n")
    audit.add(rpt, os.path.join(os.path.dirname(__file__), "run_styles.py"))
    audit.add(rpt, os.path.join(os.path.dirname(__file__), "recon.py"))
    # recommended-style rows for the manifest preview
    recmask = df.apply(lambda r: r["style"] in r["rec_style"], axis=1)
    recdf = df[recmask]
    audit.write_manifest(
        rpt, "SPZ recon — Trading Style x minScore sensitivity",
        summary_lines=["per-instrument style + minScore sweep; RECON DD, gross of costs, single ~1-1.5y period",
                       "score is coarse (steps of 25) so minScore <=75 behaves alike; >75 needs all-aligned+ADX"]
        + [f"{r['instrument']} {r['style']} ms{r['minScore']}: n={r['trades']} pf={r['pf']} maxDD={r['maxdd_R']}R"
           for _, r in recdf.iterrows()],
        kind="sweep",
        metrics={"runs": len(rows)},
        preview=["| instrument | style | EMAs | minScore | trades | PF | exp R | win% | maxDD R |",
                 "|---|---|---|---:|---:|---:|---:|---:|---:|"]
        + [f"| {r['instrument']} | {r['style']} | {r['emas']} | {r['minScore']} | {r['trades']} | {r['pf']} | {r['exp_R']} | {r['win_pct']} | {r['maxdd_R']} |"
           for _, r in df.iterrows()],
    )
    print("audit folder:", rpt)
    return rpt


if __name__ == "__main__":
    run()
