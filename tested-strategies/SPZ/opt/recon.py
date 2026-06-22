"""
Python reconstruction of the "Scalper Pro v4.1 [ZynAlgo]" recovered indicator (SPZ/recovered_indicator.pine v3.2),
for disciplined parameter search against real XAUUSD H1 data. Indicator math mirrors Pine v6:
  ta.ema  -> ewm(span, adjust=False)
  ta.rma  -> ewm(alpha=1/n, adjust=False)   (Wilder)
  ta.rsi/ta.atr/ta.dmi use rma.
Trade model = v3.2: SL fixed -1R, target TP3 +3R, hold >= cooldown ignoring opposite signals,
reverse on cooled opposite signal; no-trade in SIDEWAY regime.
"""
import numpy as np
import pandas as pd


# ----------------------------- indicator primitives -----------------------------
def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()

def rma(s, n):
    return s.ewm(alpha=1.0 / n, adjust=False).mean()

def rsi(c, n=14):
    d = c.diff()
    up = d.clip(lower=0.0)
    dn = (-d).clip(lower=0.0)
    rs = rma(up, n) / rma(dn, n)
    return 100.0 - 100.0 / (1.0 + rs)

def true_range(h, l, c):
    pc = c.shift()
    return pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)

def atr(h, l, c, n=14):
    return rma(true_range(h, l, c), n)

def adx(h, l, c, n=14):
    up = h.diff()
    dn = -l.diff()
    plus_dm = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), index=h.index)
    minus_dm = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), index=h.index)
    tr_rma = rma(true_range(h, l, c), n)
    plus_di = 100.0 * rma(plus_dm, n) / tr_rma
    minus_di = 100.0 * rma(minus_dm, n) / tr_rma
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    return rma(dx, n)


# ----------------------------- data -----------------------------
def load_tf(csv_path, rule="1h"):
    df = pd.read_csv(csv_path, parse_dates=["time_utc"]).set_index("time_utc").sort_index()
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "tick_volume": "sum"}
    bars = df.resample(rule).agg(agg).dropna()
    return bars.rename(columns={"tick_volume": "volume"})

def load_h1(csv_path):
    return load_tf(csv_path, "1h")

def htf_ema_on_h1(h1, span, htf="4h"):
    """H4 EMA aligned to H1 using only completed H4 bars (no lookahead)."""
    c4 = h1["close"].resample(htf).last().dropna()
    e4 = ema(c4, span)
    e4_end = e4.copy()
    e4_end.index = e4_end.index + pd.Timedelta(htf)          # value known only after the H4 bar closes
    left = h1.index.to_frame(name="t").reset_index(drop=True)
    right = e4_end.rename("htfema").reset_index().rename(columns={"index": "t4", "time_utc": "t4"})
    right.columns = ["t4", "htfema"]
    m = pd.merge_asof(left.sort_values("t"), right.sort_values("t4"),
                      left_on="t", right_on="t4", direction="backward")
    return pd.Series(m["htfema"].values, index=h1.index)


# ----------------------------- features -----------------------------
def build_base(h1, p, htf_rule="4h"):
    """Heavy indicators that depend only on EMA lengths / session — compute ONCE per grid.
    htf_rule = the higher timeframe used for the HTF trend (H1 base -> 4h; H4 base -> 1D)."""
    f = pd.DataFrame(index=h1.index)
    f["close"] = h1["close"]; f["high"] = h1["high"]; f["low"] = h1["low"]; f["volume"] = h1["volume"]
    f["emaSlow"] = ema(h1["close"], p["emaSlow"])
    f["htfEma"] = htf_ema_on_h1(h1, p["emaSlow"], htf=htf_rule)
    f["htfUp"] = f["close"] > f["htfEma"]
    f["adx"] = adx(h1["high"], h1["low"], h1["close"], 14)
    f["rsi"] = rsi(h1["close"], 14)
    f["atr"] = atr(h1["high"], h1["low"], h1["close"], 14)
    f["rsiBull"] = f["rsi"] > 50
    hour = f.index.hour
    f["inSession"] = (hour >= p["sessStart"]) & (hour < p["sessEnd"]) if p["useSession"] else True
    return f

def add_regime_score(base, p):
    """Cheap per-combo layer: regime (slopeLen, flatBand), score (adxStrongTh)."""
    f = base.copy()
    f["adxStrong"] = f["adx"] >= p["adxStrongTh"]
    f["emaSlope"] = (f["emaSlow"] - f["emaSlow"].shift(p["slopeLen"])) / f["atr"]
    f["marketBull"] = f["emaSlope"] > p["flatBand"]
    f["marketBear"] = f["emaSlope"] < -p["flatBand"]
    bull = f["marketBull"].astype(int) + f["htfUp"].astype(int) + f["rsiBull"].astype(int)
    bear = f["marketBear"].astype(int) + (~f["htfUp"]).astype(int) + (~f["rsiBull"]).astype(int)
    f["bullVotes"] = bull; f["bearVotes"] = bear
    f["score"] = np.minimum(100, np.maximum(bull, bear) * 25 + f["adxStrong"].astype(int) * 25)
    return f

def build_features(h1, p):
    return add_regime_score(build_base(h1, p), p)


# ----------------------------- trade simulator (v3.2 state machine) -----------------------------
def simulate(f, p, win=None):
    """win = (start_ts, end_ts): restrict trade ENTRIES to this window (warm-up uses all prior bars)."""
    sig_long = (f["score"] >= p["minScore"]) & (f["bullVotes"] >= 2) & f["marketBull"] & f["inSession"]
    sig_short = (f["score"] >= p["minScore"]) & (f["bearVotes"] >= 2) & f["marketBear"] & f["inSession"]
    score = f["score"].values; high = f["high"].values; low = f["low"].values; close = f["close"].values
    atrv = f["atr"].values; sigL = sig_long.values; sigS = sig_short.values
    if win is None:
        in_win = np.ones(len(f), dtype=bool)
    else:
        idx = f.index
        in_win = (idx >= win[0]) & (idx < win[1])
    n = len(f)
    pos = 0; entry = np.nan; entry_i = -1; curSL = np.nan; tp3 = np.nan; risk = np.nan; lastSig = -10**9
    trades = []
    for i in range(n):
        if np.isnan(atrv[i]):
            continue
        cooldown_ok = (i - lastSig) >= p["cooldown"]
        rev_long = pos == 1 and sigS[i] and cooldown_ok
        rev_short = pos == -1 and sigL[i] and cooldown_ok
        exited = False; exitR = 0.0; exitTxt = ""
        # A) hard exits
        if pos == 1 and not rev_long:
            if low[i] <= curSL:
                exited = True; exitR = -1.0; exitTxt = "SL"
            elif high[i] >= tp3:
                exited = True; exitR = 3.0; exitTxt = "WIN"
        elif pos == -1 and not rev_short:
            if high[i] >= curSL:
                exited = True; exitR = -1.0; exitTxt = "SL"
            elif low[i] <= tp3:
                exited = True; exitR = 3.0; exitTxt = "WIN"
        # B) reversal
        if rev_long:
            rr = (close[i] - entry) / risk
            exited = True; exitR = 1.0 if rr >= 0 else -1.0; exitTxt = "TP" if rr >= 0 else "SL"
        elif rev_short:
            rr = (entry - close[i]) / risk
            exited = True; exitR = 1.0 if rr >= 0 else -1.0; exitTxt = "TP" if rr >= 0 else "SL"
        if exited:
            trades.append({"entry_i": entry_i, "exit_i": i, "dir": pos, "R": exitR,
                           "bars": i - entry_i, "entry": entry, "outcome": exitTxt,
                           "entry_t": f.index[entry_i], "exit_t": f.index[i]})
            pos = 0
        # C) entries (only inside the active window)
        if pos == 0 and cooldown_ok and in_win[i]:
            if sigL[i]:
                pos = 1; entry = close[i]; entry_i = i; lastSig = i; risk = p["slMult"] * atrv[i]
                curSL = close[i] - risk; tp3 = close[i] + p["rr3"] * risk
            elif sigS[i]:
                pos = -1; entry = close[i]; entry_i = i; lastSig = i; risk = p["slMult"] * atrv[i]
                curSL = close[i] + risk; tp3 = close[i] - p["rr3"] * risk
    return pd.DataFrame(trades)


def stats(trades):
    if len(trades) == 0:
        return {"n": 0, "pf": float("nan"), "exp": float("nan"), "win_rate": float("nan"),
                "wins": 0, "losses": 0, "win3R": 0, "tp1R": 0, "sl": 0}
    gW = trades.loc[trades["R"] > 0, "R"].sum()
    gL = -trades.loc[trades["R"] < 0, "R"].sum()
    return {
        "n": int(len(trades)),
        "pf": float(gW / gL) if gL > 0 else float("inf"),
        "exp": float(trades["R"].mean()),
        "win_rate": float((trades["R"] > 0).mean()),
        "wins": int((trades["R"] > 0).sum()),
        "losses": int((trades["R"] < 0).sum()),
        "win3R": int((trades["outcome"] == "WIN").sum()),
        "tp1R": int((trades["outcome"] == "TP").sum()),
        "sl": int((trades["outcome"] == "SL").sum()),
    }


def equity_dd(trades, risk_pct):
    """Max drawdown from the R-multiple trade sequence.
    Returns max DD in R units, and max DD % under fixed-fractional sizing at risk_pct per trade."""
    if len(trades) == 0:
        return {"maxdd_R": float("nan"), "maxdd_pct": float("nan"), "final_R": 0.0}
    R = trades["R"].values
    eqR = np.cumsum(R)
    ddR = np.maximum.accumulate(eqR) - eqR
    maxdd_R = float(np.max(ddR)) if len(ddR) else 0.0
    eq = 1.0; peak = 1.0; maxdd = 0.0
    for r in R:
        eq *= (1.0 + r * risk_pct / 100.0)
        peak = max(peak, eq)
        maxdd = max(maxdd, (peak - eq) / peak)
    return {"maxdd_R": maxdd_R, "maxdd_pct": maxdd * 100.0, "final_R": float(eqR[-1])}


DEFAULTS = dict(emaFast=21, emaSlow=50, slopeLen=10, flatBand=0.6, adxStrongTh=20,
                minScore=60, cooldown=25, slMult=2.8, rr3=3.0, rr1=1.0,
                useSession=True, sessStart=7, sessEnd=18)
