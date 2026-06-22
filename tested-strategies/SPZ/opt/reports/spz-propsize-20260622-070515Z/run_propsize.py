"""
Prop-safe position sizing for the SPZ reconstruction at recommended settings.
Prop limits: daily DD <= 5%, max DD <= 10%.

For risk f% per trade (1R = f% of account):
  account max DD  ~= maxDD_R   * f
  worst daily DD  ~= worstDay_R * f       (worst sum of closed-trade R in one calendar day)
=> f must satisfy  f <= 10/maxDD_R  AND  f <= 5/worstDay_R.
History is short (~1-1.5y), so the observed DD is optimistic -> apply a 2x safety buffer
(size as if a future DD could be twice the worst seen). Example lots for a $100k account use
median SL distance (2.8 x median ATR) and standard contract sizes.
NOTE: reconstruction's DD, not the original's; gross of costs; single recent period.
"""
import os, sys, json
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
import recon, audit

DATA = os.path.join(os.path.dirname(__file__), "..", "..", "CBS", "data")
# instrument, file, tf, htf, $ per 1.0 price move per 1.0 lot (standard contract)
INSTR = [
    ("XAUUSD", "XAUUSD_M5_2024-06-10_2026-06-10.csv", "1h", "4h", 100.0),     # 1 lot = 100 oz
    ("BTCUSD", "BTCUSD_M5_2024-06-10_2026-06-10.csv", "4h", "1D", 1.0),       # 1 lot = 1 BTC
    ("EURUSD", "EURUSD_M5_2024-06-10_2026-06-10.csv", "1h", "4h", 100000.0),  # 1 lot = 100k
]
ACCOUNT = 100_000.0
DAILY_LIMIT = 5.0
MAX_LIMIT = 10.0
BUFFER = 2.0   # size for 2x the worst historical DD


def run():
    rpt = audit.new_report("spz-propsize")
    log = [f"limits: daily {DAILY_LIMIT}% / max {MAX_LIMIT}% ; buffer x{BUFFER} ; account ${ACCOUNT:,.0f}"]
    rows = []
    for name, fn, tf, htf, dollar_per_pt in INSTR:
        bars = recon.load_tf(os.path.join(DATA, fn), tf)
        f = recon.add_regime_score(recon.build_base(bars, recon.DEFAULTS, htf_rule=htf), recon.DEFAULTS)
        t = recon.simulate(f, recon.DEFAULTS)
        s = recon.stats(t)
        maxdd_R = recon.equity_dd(t, 1.0)["maxdd_R"]
        # worst single calendar day (sum of closed-trade R), as a positive loss magnitude
        day = t.assign(d=pd.to_datetime(t["exit_t"]).dt.date).groupby("d")["R"].sum()
        worstday_R = float(-day.min()) if len(day) else float("nan")
        med_atr = float(f["atr"].median())
        med_sl_px = recon.DEFAULTS["slMult"] * med_atr     # price distance of 1R

        f_max = MAX_LIMIT / maxdd_R if maxdd_R > 0 else float("inf")
        f_daily = DAILY_LIMIT / worstday_R if worstday_R > 0 else float("inf")
        f_bind = min(f_max, f_daily)
        binding = "max-DD" if f_max <= f_daily else "daily-DD"
        f_safe = f_bind / BUFFER
        # lots for $100k at f_safe
        risk_usd = ACCOUNT * f_safe / 100.0
        lots = risk_usd / (med_sl_px * dollar_per_pt)
        # resulting DDs at f_safe (sanity: should be <= limits/buffer)
        res_maxdd = maxdd_R * f_safe
        res_daily = worstday_R * f_safe

        row = {
            "instrument": name, "tf": tf, "trades": s["n"], "pf": round(s["pf"], 2) if s["pf"] == s["pf"] else None,
            "maxdd_R": round(maxdd_R, 1), "worstday_R": round(worstday_R, 1),
            "med_SL_px": round(med_sl_px, 4), "binding": binding,
            "risk_per_trade_pct": round(f_safe, 3),
            "lots_100k": round(lots, 3),
            "risk_usd_100k": round(risk_usd, 0),
            "result_maxdd_pct": round(res_maxdd, 1), "result_daily_pct": round(res_daily, 1),
        }
        rows.append(row)
        if len(t):
            t.to_csv(os.path.join(rpt, f"trades_{name}_{tf}.csv"), index=False)
        line = (f"{name} {tf}: maxDD={row['maxdd_R']}R worstDay={row['worstday_R']}R "
                f"binding={binding} -> risk/trade {row['risk_per_trade_pct']}%  "
                f"(~{row['lots_100k']} lots/$100k, SL~{row['med_SL_px']})  "
                f"=> proj maxDD {row['result_maxdd_pct']}% / daily {row['result_daily_pct']}%")
        log.append(line); print(line)

    pd.DataFrame(rows).to_csv(os.path.join(rpt, "propsize.csv"), index=False)
    with open(os.path.join(rpt, "config.json"), "w") as fh:
        json.dump({"settings": recon.DEFAULTS, "limits": {"daily": DAILY_LIMIT, "max": MAX_LIMIT},
                   "buffer": BUFFER, "account": ACCOUNT, "instruments": [i[0] + " " + i[2] for i in INSTR]}, fh, indent=2)
    with open(os.path.join(rpt, "runlog.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(log) + "\nrun complete\n")
    audit.add(rpt, os.path.join(os.path.dirname(__file__), "run_propsize.py"))
    audit.add(rpt, os.path.join(os.path.dirname(__file__), "recon.py"))
    audit.write_manifest(
        rpt, "SPZ reconstruction — prop-safe sizing (5% daily / 10% max)",
        summary_lines=[
            f"limits daily {DAILY_LIMIT}% / max {MAX_LIMIT}%, {BUFFER}x safety buffer, ${ACCOUNT:,.0f} account",
            "RECON DD (not original), GROSS of costs, ~1-1.5y single period -> buffer is essential",
        ] + [f"{r['instrument']} {r['tf']}: risk {r['risk_per_trade_pct']}%/trade (~{r['lots_100k']} lots/$100k), "
             f"binding={r['binding']}, proj maxDD {r['result_maxdd_pct']}%/daily {r['result_daily_pct']}%" for r in rows],
        kind="backtest",
        metrics={f"{r['instrument']}_risk_pct": r["risk_per_trade_pct"] for r in rows}
              | {f"{r['instrument']}_lots100k": r["lots_100k"] for r in rows},
        preview=["| instrument | TF | maxDD R | worstDay R | binding | risk/trade % | lots/$100k |",
                 "|---|---|---:|---:|---|---:|---:|"]
              + [f"| {r['instrument']} | {r['tf']} | {r['maxdd_R']} | {r['worstday_R']} | {r['binding']} | {r['risk_per_trade_pct']} | {r['lots_100k']} |" for r in rows],
    )
    print("audit folder:", rpt)
    return rpt


if __name__ == "__main__":
    run()
