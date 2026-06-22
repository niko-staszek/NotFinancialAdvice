"""
Portfolio (combined) prop-safe sizing for trading XAUUSD + BTCUSD together with the SPZ
reconstruction (Intraday style 13/34, recommended minScore). Builds one combined equity curve
from BOTH strategies' trades (same risk % per trade on each), so the COMBINED max DD / worst day
account for overlap when both draw down at once. Sizes so the PORTFOLIO stays inside 5% daily /
10% max, with a 2x buffer (target 2.5% daily / 5% max). Also reports how often both are open
simultaneously (the overlap the user expects) and the diversification vs summing the two DDs.

Caveats: reconstruction's DD (not original); gross of costs; single ~1y window (BTC data starts
2025-06); combined DD here is from CLOSED trades — concurrent FLOATING DD could be worse, which
the 2x buffer partly covers.
"""
import os, sys, json
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "tools"))
import recon, audit

DATA = os.path.join(os.path.dirname(__file__), "..", "..", "..", "CBS", "data")
CFG = [   # name, file, tf, htf, $per point per lot
    ("XAUUSD", "XAUUSD_M5_2024-06-10_2026-06-10.csv", "1h", "4h", 100.0),
    ("BTCUSD", "BTCUSD_M5_2024-06-10_2026-06-10.csv", "4h", "1D", 1.0),
]
STYLE = (13, 34)      # Intraday
MINSCORE = 75
ACCOUNT = 100_000.0
TGT_MAX = 5.0         # 10% limit, 2x buffer
TGT_DAILY = 2.5       # 5% limit, 2x buffer


def maxdd_R(R):
    eq = np.cumsum(R)
    return float(np.max(np.maximum.accumulate(eq) - eq)) if len(eq) else 0.0


def overlap_seconds(a, b):
    """total seconds both instruments hold a position simultaneously (a,b = lists of (start,end))."""
    tot = 0.0
    for s1, e1 in a:
        for s2, e2 in b:
            lo = max(s1, s2); hi = min(e1, e2)
            if hi > lo:
                tot += (hi - lo)
    return tot


def union_seconds(intervals):
    iv = sorted(intervals)
    tot = 0.0; cs = ce = None
    for s, e in iv:
        if cs is None:
            cs, ce = s, e
        elif s <= ce:
            ce = max(ce, e)
        else:
            tot += ce - cs; cs, ce = s, e
    if cs is not None:
        tot += ce - cs
    return tot


def run():
    rpt = audit.new_report("spz-combo")
    log = []
    per = {}
    all_trades = []
    for name, fn, tf, htf, dpp in CFG:
        bars = recon.load_tf(os.path.join(DATA, fn), tf)
        p = {**recon.DEFAULTS, "emaFast": STYLE[0], "emaSlow": STYLE[1], "minScore": MINSCORE}
        f = recon.add_regime_score(recon.build_base(bars, p, htf_rule=htf), p)
        t = recon.simulate(f, p)
        t = t.assign(instr=name)
        med_sl = recon.DEFAULTS["slMult"] * float(f["atr"].median())
        per[name] = {"dd_R": maxdd_R(t["R"].values), "n": len(t), "med_sl": med_sl, "dpp": dpp,
                     "entry": pd.to_datetime(t["entry_t"]), "exit": pd.to_datetime(t["exit_t"])}
        all_trades.append(t[["entry_t", "exit_t", "R", "instr"]])
        line = f"{name} {tf} Intraday ms{MINSCORE}: n={len(t)} solo maxDD={per[name]['dd_R']:.1f}R medSL={med_sl:.2f}"
        log.append(line); print(line)

    merged = pd.concat(all_trades, ignore_index=True)
    merged["exit_t"] = pd.to_datetime(merged["exit_t"])
    merged = merged.sort_values("exit_t").reset_index(drop=True)
    comb_dd = maxdd_R(merged["R"].values)
    sum_solo = sum(per[k]["dd_R"] for k in per)
    worstday = float(-merged.assign(d=merged["exit_t"].dt.date).groupby("d")["R"].sum().min())

    # overlap: seconds both open / union of open time
    iv = {k: list(zip(per[k]["entry"].astype("int64") // 10**9, per[k]["exit"].astype("int64") // 10**9)) for k in per}
    both = overlap_seconds(iv["XAUUSD"], iv["BTCUSD"])
    uni = union_seconds(iv["XAUUSD"] + iv["BTCUSD"])
    overlap_frac = both / uni if uni else 0.0

    r_max = TGT_MAX / comb_dd if comb_dd > 0 else float("inf")
    r_daily = TGT_DAILY / worstday if worstday > 0 else float("inf")
    r_safe = min(r_max, r_daily)
    binding = "max-DD" if r_max <= r_daily else "daily-DD"

    rows = []
    for name in per:
        risk_usd = ACCOUNT * r_safe / 100.0
        lots = risk_usd / (per[name]["med_sl"] * per[name]["dpp"])
        rows.append({"instrument": name, "solo_maxdd_R": round(per[name]["dd_R"], 1),
                     "risk_per_trade_pct": round(r_safe, 3), "lots_100k": round(lots, 3),
                     "med_SL_px": round(per[name]["med_sl"], 2)})

    summary = {
        "combined_maxdd_R": round(comb_dd, 1), "sum_of_solo_R": round(sum_solo, 1),
        "diversification_R_saved": round(sum_solo - comb_dd, 1),
        "combined_worstday_R": round(worstday, 1), "overlap_frac_both_open": round(overlap_frac, 3),
        "binding": binding, "risk_per_trade_pct": round(r_safe, 3),
        "proj_combined_maxdd_pct": round(comb_dd * r_safe, 1),
        "proj_combined_daily_pct": round(worstday * r_safe, 1),
    }
    log.append(f"COMBINED maxDD={comb_dd:.1f}R (vs sum {sum_solo:.1f}R -> div saves {sum_solo-comb_dd:.1f}R) "
               f"worstDay={worstday:.1f}R overlap={overlap_frac*100:.0f}% -> risk {r_safe:.3f}%/trade "
               f"(binding {binding}); proj combined maxDD {summary['proj_combined_maxdd_pct']}% / daily {summary['proj_combined_daily_pct']}%")
    for r in rows:
        log.append(f"  {r['instrument']}: {r['lots_100k']} lots/$100k (SL~{r['med_SL_px']})")
    print("\n".join(log[len(CFG):]))

    pd.DataFrame(rows).to_csv(os.path.join(rpt, "combo_sizing.csv"), index=False)
    merged.to_csv(os.path.join(rpt, "merged_trades.csv"), index=False)
    with open(os.path.join(rpt, "summary.json"), "w") as fh:
        json.dump(summary, fh, indent=2)
    with open(os.path.join(rpt, "config.json"), "w") as fh:
        json.dump({"style": "Intraday 13/34", "minScore": MINSCORE, "limits": {"daily": 5, "max": 10},
                   "buffer": 2, "account": ACCOUNT, "instruments": ["XAUUSD H1", "BTCUSD H4"]}, fh, indent=2)
    with open(os.path.join(rpt, "runlog.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(log) + "\nrun complete\n")
    audit.add(rpt, os.path.join(os.path.dirname(__file__), "run_combo.py"))
    audit.add(rpt, os.path.join(os.path.dirname(__file__), "recon.py"))
    audit.write_manifest(
        rpt, "SPZ recon — combined XAU+BTC prop-safe sizing",
        summary_lines=[
            f"XAU H1 + BTC H4, Intraday, ms{MINSCORE}; limits 5%d/10%m, 2x buffer, ${ACCOUNT:,.0f}",
            f"combined maxDD {summary['combined_maxdd_R']}R vs sum-of-solo {summary['sum_of_solo_R']}R "
            f"(diversification saves {summary['diversification_R_saved']}R); both-open {summary['overlap_frac_both_open']*100:.0f}% of time",
            f"-> risk {r_safe:.3f}%/trade each, binding {binding}; "
            f"proj combined maxDD {summary['proj_combined_maxdd_pct']}% / daily {summary['proj_combined_daily_pct']}%",
            "RECON DD not original; gross of costs; ~1y window; closed-trade DD (floating could be worse)",
        ],
        kind="backtest",
        metrics={"combined_maxdd_R": summary["combined_maxdd_R"], "risk_per_trade_pct": r_safe,
                 "overlap_frac": summary["overlap_frac_both_open"],
                 "XAU_lots100k": rows[0]["lots_100k"], "BTC_lots100k": rows[1]["lots_100k"]},
        preview=["| | combined | sum of solo |", "|---|---:|---:|",
                 f"| max DD (R) | {summary['combined_maxdd_R']} | {summary['sum_of_solo_R']} |",
                 "", "| instrument | risk/trade | lots/$100k |", "|---|---:|---:|"]
              + [f"| {r['instrument']} | {r['risk_per_trade_pct']}% | {r['lots_100k']} |" for r in rows],
    )
    print("audit folder:", rpt)
    return rpt


if __name__ == "__main__":
    run()
