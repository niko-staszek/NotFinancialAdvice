"""
Disciplined walk-forward parameter search for the SPZ reconstruction.

Anchored walk-forward, 3 folds: optimise regime+score params on the in-sample (IS) span,
select by IS expectancy (require IS n>=20), apply BLIND to the next out-of-sample (OOS) span,
stitch all OOS trades -> honest blind result. Compares to baseline (v3.2 defaults) and to
gold buy-and-hold over the period (Tesla-trap check). Writes a full audit folder.
"""
import os, sys, json, itertools, io, contextlib
import pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "tools"))
import recon
import audit

CSV = os.path.join(os.path.dirname(__file__), "..", "..", "CBS", "data", "XAUUSD_M5_2024-06-10_2026-06-10.csv")

GRID = dict(
    flatBand=[0.3, 0.5, 0.7, 1.0, 1.5],
    slopeLen=[5, 10, 20],
    adxStrongTh=[20, 25],
    minScore=[50, 60, 75],
    cooldown=[10, 25, 50],
)
MIN_IS_TRADES = 20


def run():
    log = io.StringIO()
    def out(*a):
        s = " ".join(str(x) for x in a); print(s); log.write(s + "\n")

    rpt = audit.new_report("spz-walkforward")
    h1 = recon.load_h1(CSV)
    out("config applied: EMA 21/50 fixed (confirmed); grid =", json.dumps(GRID))
    out("H1 bars:", len(h1), "| range:", h1.index[0], "->", h1.index[-1])

    base = recon.build_base(h1, recon.DEFAULTS)

    # feature cache keyed by (slopeLen, flatBand, adxStrongTh) — minScore/cooldown are sim-only
    feat = {}
    for sl in GRID["slopeLen"]:
        for fb in GRID["flatBand"]:
            for ax in GRID["adxStrongTh"]:
                p = dict(recon.DEFAULTS); p.update(slopeLen=sl, flatBand=fb, adxStrongTh=ax)
                feat[(sl, fb, ax)] = recon.add_regime_score(base, p)

    # fold boundaries (4 equal blocks -> 3 anchored OOS folds covering the last 75% blind)
    idx = h1.index; n = len(idx)
    b = [idx[0], idx[n // 4], idx[n // 2], idx[3 * n // 4], idx[-1] + pd.Timedelta("1h")]
    folds = [(b[0], b[1], b[1], b[2]), (b[0], b[2], b[2], b[3]), (b[0], b[3], b[3], b[4])]

    combos = [dict(zip(GRID, v)) for v in itertools.product(*GRID.values())]
    out("combos per fold:", len(combos), "| folds:", len(folds))

    all_rows = []          # every combo, every fold, IS stats (raw result file)
    selected = []          # per-fold winner + its OOS
    oos_trades = []

    for fi, (is0, is1, oo0, oo1) in enumerate(folds):
        best = None
        for c in combos:
            p = dict(recon.DEFAULTS); p.update(c)
            f = feat[(c["slopeLen"], c["flatBand"], c["adxStrongTh"])]
            s_is = recon.stats(recon.simulate(f, p, win=(is0, is1)))
            row = {"fold": fi, **c, **{f"is_{k}": v for k, v in s_is.items()}}
            all_rows.append(row)
            if s_is["n"] >= MIN_IS_TRADES and (best is None or s_is["exp"] > best["is_exp"]):
                best = {"fold": fi, **c, "is_exp": s_is["exp"], "is_pf": s_is["pf"], "is_n": s_is["n"]}
        if best is None:
            out(f"fold {fi}: NO combo cleared IS n>={MIN_IS_TRADES}; skipping")
            continue
        p = dict(recon.DEFAULTS); p.update({k: best[k] for k in GRID})
        f = feat[(best["slopeLen"], best["flatBand"], best["adxStrongTh"])]
        t_oos = recon.simulate(f, p, win=(oo0, oo1))
        s_oos = recon.stats(t_oos)
        t_oos = t_oos.assign(fold=fi)
        oos_trades.append(t_oos)
        sel = {**best, "oos_window": f"{oo0.date()}..{oo1.date()}",
               **{f"oos_{k}": v for k, v in s_oos.items()}}
        selected.append(sel)
        out(f"fold {fi} IS[{is0.date()}..{is1.date()}] -> best {{flatBand:{best['flatBand']}, "
            f"slopeLen:{best['slopeLen']}, adxTh:{best['adxStrongTh']}, minScore:{best['minScore']}, "
            f"cooldown:{best['cooldown']}}} IS exp={best['is_exp']:.3f} pf={best['is_pf']:.2f} n={best['is_n']} "
            f"|| OOS exp={s_oos['exp']:.3f} pf={s_oos['pf']:.2f} n={s_oos['n']}")

    # stitched blind OOS (the honest headline)
    stitched = pd.concat(oos_trades, ignore_index=True) if oos_trades else pd.DataFrame()
    s_stitch = recon.stats(stitched)
    out("STITCHED OOS:", json.dumps(s_stitch))

    # baseline (v3.2 defaults) over the same stitched OOS span for comparison
    fdef = recon.add_regime_score(base, recon.DEFAULTS)
    base_oos = recon.simulate(fdef, recon.DEFAULTS, win=(b[1], b[4]))
    s_base = recon.stats(base_oos)
    out("BASELINE defaults over OOS span:", json.dumps(s_base))

    # gold buy-and-hold over full period (Tesla-trap check)
    bh = float(h1["close"].iloc[-1] / h1["close"].iloc[0] - 1.0)
    out("gold buy&hold over period: %.1f%%" % (bh * 100))
    out("run complete")

    # ---- write audit artifacts ----
    pd.DataFrame(all_rows).to_csv(os.path.join(rpt, "is_grid_all_combos.csv"), index=False)
    pd.DataFrame(selected).to_csv(os.path.join(rpt, "selected_per_fold.csv"), index=False)
    if len(stitched):
        stitched.to_csv(os.path.join(rpt, "stitched_oos_trades.csv"), index=False)
    with open(os.path.join(rpt, "config.json"), "w") as fh:
        json.dump({"grid": GRID, "defaults": recon.DEFAULTS, "min_is_trades": MIN_IS_TRADES,
                   "folds": [[str(x) for x in fo] for fo in folds], "data": os.path.basename(CSV)}, fh, indent=2)
    with open(os.path.join(rpt, "runlog.txt"), "w", encoding="utf-8") as fh:
        fh.write(log.getvalue())
    audit.add(rpt, os.path.join(os.path.dirname(__file__), "run_search.py"))
    audit.add(rpt, os.path.join(os.path.dirname(__file__), "recon.py"))

    audit.write_manifest(
        rpt, "SPZ reconstruction — walk-forward param search",
        summary_lines=[
            f"data {h1.index[0].date()}..{h1.index[-1].date()} XAUUSD H1 ({len(h1)} bars), 3 anchored folds",
            f"STITCHED blind OOS: pf={s_stitch['pf']:.2f} exp={s_stitch['exp']:.3f}R n={s_stitch['n']} win%={s_stitch['win_rate']*100:.0f}",
            f"baseline v3.2 over OOS span: pf={s_base['pf']:.2f} exp={s_base['exp']:.3f}R n={s_base['n']}",
            f"gold buy&hold over period: {bh*100:.0f}% (Tesla-trap: long-biased PF rides this)",
        ],
        kind="backtest",
        metrics={"oos_pf": round(s_stitch["pf"], 3), "oos_exp_R": round(s_stitch["exp"], 3),
                 "oos_n": s_stitch["n"], "baseline_oos_pf": round(s_base["pf"], 3),
                 "gold_bh_pct": round(bh * 100, 1)},
        preview=["| metric | stitched OOS | baseline OOS |", "|---|---:|---:|",
                 f"| PF | {s_stitch['pf']:.2f} | {s_base['pf']:.2f} |",
                 f"| exp (R) | {s_stitch['exp']:.3f} | {s_base['exp']:.3f} |",
                 f"| trades | {s_stitch['n']} | {s_base['n']} |"],
    )
    out("audit folder:", rpt)
    return rpt


if __name__ == "__main__":
    run()
