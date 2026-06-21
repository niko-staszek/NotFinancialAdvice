"""Baseline + harness-validity check for the SPZ reconstruction model. No optimization yet."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import recon

CSV = os.path.join(os.path.dirname(__file__), "..", "..", "CBS", "data", "XAUUSD_M5_2024-06-10_2026-06-10.csv")


def regime_counts(f):
    bull = int(f["marketBull"].sum())
    bear = int(f["marketBear"].sum())
    side = int((~f["marketBull"] & ~f["marketBear"]).sum())
    return {"BULL": bull, "BEAR": bear, "SIDEWAY": side}


def main():
    h1 = recon.load_h1(CSV)
    print("config applied: DEFAULTS =", recon.DEFAULTS)
    print("H1 bars:", len(h1), "| range:", h1.index[0], "->", h1.index[-1])

    f = recon.build_features(h1, recon.DEFAULTS)
    print("rsi  min/max: %.1f / %.1f" % (f["rsi"].min(), f["rsi"].max()))
    print("adx  min/max: %.1f / %.1f" % (f["adx"].min(), f["adx"].max()))
    print("regime bar counts:", regime_counts(f))

    t = recon.simulate(f, recon.DEFAULTS)
    print("BASELINE stats:", recon.stats(t))

    # discriminator: a very high flatBand makes the regime ~never trend -> trades must drop
    p2 = dict(recon.DEFAULTS); p2["flatBand"] = 5.0
    f2 = recon.build_features(h1, p2)
    t2 = recon.simulate(f2, p2)
    print("DISCRIMINATOR flatBand=5.0 stats:", recon.stats(t2))
    print("discriminator_ok:", len(t) != len(t2))
    print("run complete")


if __name__ == "__main__":
    main()
