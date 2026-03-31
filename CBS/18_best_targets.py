"""
18_best_targets.py -- CBS Best Target Finder
==============================================
Single script that runs the full analysis and outputs two clean tables:
  1. OFFSET TARGETS -- best config per instrument (24h windows, hourly offsets)
  2. INTRADAY TARGETS -- best config per instrument (2-8h session windows)

For each instrument, tests all combinations of:
  - 13 offset windows (00:00-12:00 UTC)
  - 21 intraday windows (session-based)
  - 16 filter combos (EMA/H4/CLU/LLR on/off)
  - 4 SL modes (tier, 1:1, 1:1.5, 1:2)

Usage:
  python 18_best_targets.py
  python 18_best_targets.py --symbols EURUSD,XAUUSD
  python 18_best_targets.py --data-path "C:/.../MQL5/Files/CBS_DATA"
  python 18_best_targets.py --symbols EURUSD --validate   # walk-forward OOS test
"""

import argparse
import logging
import os
import sys
import time
import datetime as dt
from pathlib import Path
from dataclasses import dataclass
from itertools import product
from collections import defaultdict

import numpy as np
import pandas as pd

# ─── Logging ──────────────────────────────────────────────────────────────────

log = logging.getLogger("cbs_targets")

# ─── Paths ────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "research" / "output"


def auto_detect_data_dirs():
    """Scan %APPDATA%/MetaQuotes/Terminal/*/MQL{4,5}/Files/CBS_DATA for existing dirs."""
    appdata = os.environ.get("APPDATA", "")
    if not appdata:
        return []
    base = Path(appdata) / "MetaQuotes" / "Terminal"
    if not base.exists():
        return []
    found = []
    for terminal in base.iterdir():
        if not terminal.is_dir():
            continue
        for mql in ["MQL5", "MQL4"]:
            candidate = terminal / mql / "Files" / "CBS_DATA"
            if candidate.exists():
                found.append(candidate)
    return found


# ─── Instrument Definitions ──────────────────────────────────────────────────

INSTRUMENTS = {
    "EURUSD":  (0.0001, 5,  1.5,  "forex"),
    "GBPUSD":  (0.0001, 5,  1.5,  "forex"),
    "USDCAD":  (0.0001, 5,  2.0,  "forex"),
    "USDJPY":  (0.01,   5,  1.5,  "forex"),
    "USDCHF":  (0.0001, 5,  1.5,  "forex"),
    "AUDUSD":  (0.0001, 5,  1.5,  "forex"),
    "NZDUSD":  (0.0001, 5,  1.5,  "forex"),
    "XAUUSD":  (0.1,    15, 25.0, "standard"),
    "BTCUSD":  (1.0,    10, 50.0, "standard"),
    "ETHUSD":  (1.0,    5,  15.0, "standard"),
}

INSTRUMENT_MIN_DISTANCE = {
    "EURUSD": 15, "GBPUSD": 15, "USDCAD": 15, "USDJPY": 15,
    "USDCHF": 15, "AUDUSD": 15, "NZDUSD": 15,
    "XAUUSD": 50, "BTCUSD": 50, "ETHUSD": 30,
}

CLUSTER_SIZE_PIPS = {"forex": 5, "XAUUSD": 15, "BTCUSD": 10, "ETHUSD": 5}
FIB_LEVELS = [0.382, 0.618, -0.382, -0.618, 1.382, 1.618, 2.618]

OFFSETS_UTC = list(range(0, 13))
INTRADAY_WINDOWS = [
    (7, 3), (7, 4), (7, 6), (12, 4), (12, 6),
    (13, 4), (14, 4), (14, 6), (8, 2), (8, 3),
    (9, 3), (10, 3), (15, 3), (16, 3), (18, 3),
    (0, 6), (5, 8), (7, 8), (18, 6), (20, 4), (22, 6),
]

MAX_HOLD_HOURS = 18
SL_MODES = ["tier", "1:1", "1:1.5", "1:2"]


# ─── Data Loading ────────────────────────────────────────────────────────────

def _normalize(df):
    if "Date" in df.columns and "Timestamp" in df.columns:
        df["datetime"] = pd.to_datetime(df["Date"].astype(str) + " " + df["Timestamp"].astype(str))
    elif "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"])
    elif "time" in df.columns:
        df["datetime"] = pd.to_datetime(df["time"])
    else:
        raise ValueError(f"Cannot detect datetime column. Found columns: {list(df.columns)}")
    renames = {}
    for c in ["open", "high", "low", "close", "volume"]:
        if c in df.columns and c.capitalize() not in df.columns:
            renames[c] = c.capitalize()
    if renames:
        df.rename(columns=renames, inplace=True)
    df = df[["datetime", "Open", "High", "Low", "Close"]].copy()
    df.sort_values("datetime", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def load_csv(symbol, tf, data_dir):
    for p in [data_dir / symbol / f"{symbol}_{tf}.csv",
              data_dir / symbol / f"{symbol}_{tf}.pro.csv",
              data_dir / f"{symbol}_{tf}.csv"]:
        if p.exists():
            try:
                return _normalize(pd.read_csv(p))
            except Exception as e:
                log.warning(f"Failed to load {p}: {e}")
    return pd.DataFrame()


def load_spreads(data_dir):
    p = data_dir / "spreads.csv"
    if not p.exists():
        return {}
    try:
        df = pd.read_csv(p, header=None, names=["symbol", "spread"])
        return dict(zip(df["symbol"].str.strip().str.upper(), df["spread"]))
    except Exception as e:
        log.warning(f"Failed to load spreads.csv: {e}")
        return {}


# ─── Indicators ──────────────────────────────────────────────────────────────

def ema(series, period=21):
    out = np.empty_like(series, dtype=float)
    out[0] = series[0]
    m = 2.0 / (period + 1)
    for i in range(1, len(series)):
        out[i] = series[i] * m + out[i - 1] * (1 - m)
    return out


def compute_h4_trend(h4):
    h4 = h4.copy()
    h4["ema21"] = ema(h4["Close"].values, 21)
    h4["h4_trend"] = np.where(h4["Close"] > h4["ema21"], 1,
                               np.where(h4["Close"] < h4["ema21"], -1, 0))
    return h4


def map_h4_to_m15(m15_dts, h4):
    h4s = h4.set_index("datetime")["h4_trend"].sort_index()
    idx = h4s.index.searchsorted(m15_dts, side="right") - 1
    return h4s.values[idx.clip(0, len(h4s) - 1)]


def compute_llr_flags(highs, lows, closes, n):
    buy_ok = np.zeros(n, dtype=bool)
    sell_ok = np.zeros(n, dtype=bool)
    sl_prev = sl_last = sh_prev = sh_last = None
    for i in range(2, n):
        c = i - 1
        if lows[c] < lows[c - 1] and lows[c] < lows[i]:
            if sl_last is None or sl_last[0] != c:
                sl_prev, sl_last = sl_last, (c, lows[c])
        if highs[c] > highs[c - 1] and highs[c] > highs[i]:
            if sh_last is None or sh_last[0] != c:
                sh_prev, sh_last = sh_last, (c, highs[c])
        if sl_prev and sl_last and sl_prev[0] != sl_last[0]:
            slope = (sl_last[1] - sl_prev[1]) / (sl_last[0] - sl_prev[0])
            buy_ok[i] = closes[i] > sl_last[1] + slope * (i - sl_last[0])
        if sh_prev and sh_last and sh_prev[0] != sh_last[0]:
            slope = (sh_last[1] - sh_prev[1]) / (sh_last[0] - sh_prev[0])
            sell_ok[i] = closes[i] < sh_last[1] + slope * (i - sh_last[0])
    return buy_ok, sell_ok


def compute_fib_clusters(pd_h, pd_l, pw_h, pw_l, pm_h, pm_l, pip_size, cluster_pips):
    """Build Fibonacci retracement clusters from PD/PW/PM levels.
    Clusters form when retracement levels from different periods land close together,
    creating S/R confluence zones (see strategy.md 'Clusters' section)."""
    all_levels = []
    for label, h, l in [("PD", pd_h, pd_l), ("PW", pw_h, pw_l), ("PM", pm_h, pm_l)]:
        rng = h - l
        if rng <= 0:
            continue
        for fib in FIB_LEVELS:
            all_levels.append((l + rng * fib, label))
    if len(all_levels) < 2:
        return []
    all_levels.sort(key=lambda x: x[0])
    cdist = cluster_pips * pip_size
    clusters = []
    i = 0
    while i < len(all_levels):
        group = [all_levels[i]]
        j = i + 1
        while j < len(all_levels) and (all_levels[j][0] - all_levels[i][0]) <= cdist:
            group.append(all_levels[j])
            j += 1
        periods = set(lbl for _, lbl in group)
        if len(periods) >= 2:
            prices = [p for p, _ in group]
            clusters.append((np.mean(prices), (max(prices) - min(prices)) / pip_size))
        i = j if j > i + 1 else i + 1
    return clusters


def find_blockers(entry, target, clusters, pip_size, cluster_pips):
    """Find cluster zones between entry and target that act as obstacles.
    Per strategy.md: if a cluster sits between entry and target, trade waits
    for price to clear it before entering."""
    blockers = []
    for center, width in clusters:
        hz = max(cluster_pips, width / 2 + cluster_pips) * pip_size
        zlo, zhi = center - hz, center + hz
        if entry < target:
            if zlo > entry and zhi < target:
                blockers.append((center, zhi))
        else:
            if zlo > target and zhi < entry:
                blockers.append((center, zlo))
    blockers.sort(key=lambda x: abs(x[0] - entry))
    return blockers


def compute_prev_period_levels(d1):
    if d1.empty:
        return {}
    d1 = d1.copy()
    d1["date"] = d1["datetime"].dt.date
    levels = {}
    dates = sorted(d1["date"].unique())
    for i, date in enumerate(dates):
        rec = {}
        if i >= 1:
            prev = d1[d1["date"] == dates[i - 1]]
            rec["pd_h"], rec["pd_l"] = prev["High"].max(), prev["Low"].min()
        else:
            rec["pd_h"] = rec["pd_l"] = np.nan
        if i >= 5:
            wk = d1[d1["date"].isin(dates[max(0, i - 5):i])]
            rec["pw_h"], rec["pw_l"] = wk["High"].max(), wk["Low"].min()
        else:
            rec["pw_h"] = rec["pw_l"] = np.nan
        if i >= 22:
            mo = d1[d1["date"].isin(dates[max(0, i - 22):i])]
            rec["pm_h"], rec["pm_l"] = mo["High"].max(), mo["Low"].min()
        else:
            rec["pm_h"] = rec["pm_l"] = np.nan
        levels[date] = rec
    return levels


# ─── Window Target Computation ───────────────────────────────────────────────

def compute_window_targets(m15, start_hour, duration_hours):
    """Compute CBS targets for each day/session.
    Target = High + Low - Open  (Fibonacci expansion level 1.0, see strategy.md)."""
    if m15.empty:
        return {}
    m15 = m15.copy()
    m15["hour"] = m15["datetime"].dt.hour
    m15["date"] = m15["datetime"].dt.date
    end_hour = (start_hour + duration_hours) % 24
    wraps = (start_hour + duration_hours) >= 24
    targets = {}

    if duration_hours == 24:
        m15["wday"] = m15["datetime"].apply(
            lambda x: (x - pd.Timedelta(hours=start_hour)).date())
        for wday, grp in m15.groupby("wday"):
            if len(grp) < 4:
                continue
            o, h, l = grp["Open"].iloc[0], grp["High"].max(), grp["Low"].min()
            targets[wday + dt.timedelta(days=1)] = {"open": o, "high": h, "low": l, "target": h + l - o}
    else:
        if not wraps:
            mask = (m15["hour"] >= start_hour) & (m15["hour"] < end_hour)
        else:
            mask = (m15["hour"] >= start_hour) | (m15["hour"] < end_hour)
        wb = m15[mask].copy()
        if not wraps:
            wb["wdate"] = wb["date"]
        else:
            wb["wdate"] = wb.apply(
                lambda r: r["date"] - dt.timedelta(days=1) if r["hour"] < end_hour else r["date"], axis=1)
        for wdate, grp in wb.groupby("wdate"):
            if len(grp) < 2:
                continue
            o, h, l = grp["Open"].iloc[0], grp["High"].max(), grp["Low"].min()
            targets[wdate] = {"open": o, "high": h, "low": l, "target": h + l - o}
    return targets


# ─── Filter Config ────────────────────────────────────────────────────────────

@dataclass
class FC:
    use_ema: bool = False
    use_h4: bool = False
    use_clu: bool = False
    use_llr: bool = False
    sl_mode: str = "tier"

    @property
    def label(self):
        parts = []
        if self.use_ema: parts.append("EMA")
        if self.use_h4:  parts.append("H4")
        if self.use_clu: parts.append("CLU")
        if self.use_llr: parts.append("LLR")
        base = "+".join(parts) if parts else "RAW"
        return f"{base}|{self.sl_mode}"

    @property
    def sl_ratio_fixed(self):
        return {"1:1": 1.0, "1:1.5": 1.5, "1:2": 2.0, "1:3": 3.0}.get(self.sl_mode, 0)


ALL_COMBOS = [FC(e, h, c, l, sl)
              for e, h, c, l in product([False, True], repeat=4)
              for sl in SL_MODES]


# ─── Trade Simulation (vectorized backward approach) ─────────────────────────

def simulate(symbol, targets, m15, fwd_bars, fc, pip_size, settle_tol, spread,
             tier_mode, m15_ema=None, h4_trend=None, llr_buy=None,
             llr_sell=None, period_levels=None, window_label=""):
    """Simulate trades using vectorized settlement detection.

    Uses M5 (or M15 fallback) bars for forward simulation, giving fine-grained
    SL/TP resolution that eliminates intra-bar ambiguity.

    Settlement offset = (settle_tol + spread) * pip_size per strategy.md:
    'Target is considered reached within the settle tolerance PLUS spread.'

    Spread is baked into entry price (BUY at ask, SELL at bid) rather than
    flat deducted from PnL.
    """

    fwd_idx = fwd_bars.set_index("datetime")
    cpips = CLUSTER_SIZE_PIPS.get(symbol, CLUSTER_SIZE_PIPS.get(tier_mode, 5))
    min_dist = max(INSTRUMENT_MIN_DISTANCE.get(symbol, 15), spread + 1) if fc.use_clu else 0
    m15_dts = m15["datetime"].values

    # Settlement offset per strategy.md: settle_tol + spread
    settle_offset = (settle_tol + spread) * pip_size
    # Half-spread for entry price adjustment
    half_spread_price = (spread / 2) * pip_size

    n_trades = 0
    n_settled = 0
    n_winners = 0
    n_sl = 0
    n_timeout = 0
    total_pips = 0.0
    gross_profit = 0.0
    gross_loss = 0.0
    sum_settle_h = 0.0
    settle_hours_list = []
    rr_list = []
    sum_rr = 0.0
    sum_dist = 0.0

    for tdate in sorted(targets.keys()):
        tgt = targets[tdate]["target"]
        day_start = pd.Timestamp(tdate)
        day_end = day_start + pd.Timedelta(hours=23, minutes=59)

        # Get M15 bars for the day (for entry + filter checks)
        try:
            day_m15 = m15[(m15["datetime"] >= day_start) & (m15["datetime"] <= day_end)]
        except Exception:
            continue
        if day_m15.empty:
            continue

        first_ts = day_m15["datetime"].iloc[0]
        raw_entry = day_m15["Close"].iloc[0]

        # Direction from raw close (before spread adjustment)
        d = "buy" if tgt > raw_entry else ("sell" if tgt < raw_entry else None)
        if d is None:
            continue

        # Entry price with spread: BUY at ask, SELL at bid
        entry = raw_entry + half_spread_price if d == "buy" else raw_entry - half_spread_price

        bar_pos = np.searchsorted(m15_dts, first_ts.to_datetime64(), side="left")
        if bar_pos >= len(m15_dts):
            continue

        # ── Filters ──
        if fc.use_ema and m15_ema is not None:
            ev = m15_ema[bar_pos]
            if (d == "buy" and raw_entry <= ev) or (d == "sell" and raw_entry >= ev):
                continue

        if fc.use_h4 and h4_trend is not None:
            h4d = h4_trend[bar_pos]
            if (d == "buy" and h4d < 0) or (d == "sell" and h4d > 0):
                continue

        if fc.use_llr and llr_buy is not None:
            if (d == "buy" and not llr_buy[bar_pos]) or (d == "sell" and not llr_sell[bar_pos]):
                continue

        dist = abs(tgt - entry) / pip_size
        if min_dist > 0 and dist < min_dist:
            continue

        # ── Clusters (wait for price to clear obstacle before entry) ──
        clu_delay = 0.0
        if fc.use_clu and period_levels and tdate in period_levels:
            lvl = period_levels[tdate]
            if not np.isnan(lvl.get("pd_h", np.nan)):
                clusters = compute_fib_clusters(
                    lvl["pd_h"], lvl["pd_l"],
                    lvl.get("pw_h", lvl["pd_h"]), lvl.get("pw_l", lvl["pd_l"]),
                    lvl.get("pm_h", lvl["pd_h"]), lvl.get("pm_l", lvl["pd_l"]),
                    pip_size, cpips)
                blockers = find_blockers(entry, tgt, clusters, pip_size, cpips)
                if blockers:
                    clear_price = max(e for _, e in blockers) if d == "buy" else min(e for _, e in blockers)
                    cleared = False

                    # Use fwd_bars for cluster clearing scan
                    try:
                        clu_scan_end = first_ts + pd.Timedelta(hours=MAX_HOLD_HOURS)
                        clu_bars = fwd_idx.loc[first_ts:clu_scan_end]
                    except KeyError:
                        continue

                    for bts, bar in clu_bars.iterrows():
                        waited = (bts - first_ts).total_seconds() / 3600
                        if waited > MAX_HOLD_HOURS:
                            break
                        if (d == "buy" and bar["Close"] > clear_price) or \
                           (d == "sell" and bar["Close"] < clear_price):
                            # Re-enter at new close with spread
                            raw_entry = bar["Close"]
                            entry = raw_entry + half_spread_price if d == "buy" else raw_entry - half_spread_price
                            clu_delay = waited
                            cleared = True
                            if fc.use_ema and m15_ema is not None:
                                bp2 = np.searchsorted(m15_dts, bts.to_datetime64(), side="left")
                                if bp2 < len(m15_ema):
                                    if (d == "buy" and raw_entry <= m15_ema[bp2]) or \
                                       (d == "sell" and raw_entry >= m15_ema[bp2]):
                                        cleared = False
                            break
                    if not cleared:
                        continue
                    dist = abs(tgt - entry) / pip_size
                    if min_dist > 0 and dist < min_dist:
                        continue

        # ── SL calculation ──
        if fc.sl_ratio_fixed > 0:
            sl_ratio = fc.sl_ratio_fixed
        elif tier_mode == "forex":
            sl_ratio = 3.0 if dist <= 35 else (1.5 if dist <= 100 else 1.0)
        else:
            sl_ratio = 1.0
        sl_pips = dist * sl_ratio
        sl_price = (entry - sl_pips * pip_size) if d == "buy" else (entry + sl_pips * pip_size)

        # ── Forward simulation on M5/M15 bars (vectorized where possible) ──
        actual_ts = first_ts + pd.Timedelta(hours=clu_delay)
        remain = MAX_HOLD_HOURS - clu_delay
        if remain <= 0:
            continue
        end_ts = actual_ts + pd.Timedelta(hours=remain)

        try:
            fwd = fwd_idx.loc[actual_ts:end_ts]
        except KeyError:
            continue

        if fwd.empty:
            continue

        # Vectorized SL/TP detection using cumulative extremes
        highs = fwd["High"].values
        lows = fwd["Low"].values
        closes = fwd["Close"].values
        timestamps = fwd.index
        n_bars = len(fwd)

        pnl = 0.0
        settled = False
        hit_sl = False
        timed_out = False
        settle_h = remain

        if d == "buy":
            # TP: high reaches target (with settlement offset)
            tp_threshold = tgt - settle_offset
            tp_hits = np.where(highs >= tp_threshold)[0]
            # SL: low breaches SL price
            sl_hits = np.where(lows <= sl_price)[0]
        else:
            # TP: low reaches target (with settlement offset)
            tp_threshold = tgt + settle_offset
            tp_hits = np.where(lows <= tp_threshold)[0]
            # SL: high breaches SL price
            sl_hits = np.where(highs >= sl_price)[0]

        tp_bar = tp_hits[0] if len(tp_hits) > 0 else n_bars
        sl_bar = sl_hits[0] if len(sl_hits) > 0 else n_bars

        if sl_bar < tp_bar and sl_bar < n_bars:
            # SL hit first
            hit_sl = True
            settle_h = (timestamps[sl_bar] - actual_ts).total_seconds() / 3600
            pnl = -sl_pips
        elif tp_bar < sl_bar and tp_bar < n_bars:
            # TP hit first
            settled = True
            settle_h = (timestamps[tp_bar] - actual_ts).total_seconds() / 3600
            pnl = dist
        elif tp_bar == sl_bar and tp_bar < n_bars:
            # Same bar — ambiguous. With M5 bars this is rare.
            # Conservative: assume SL hit (worst case)
            hit_sl = True
            settle_h = (timestamps[sl_bar] - actual_ts).total_seconds() / 3600
            pnl = -sl_pips
        else:
            # Timeout — neither hit within hold period
            timed_out = True
            if n_bars > 0:
                lc = closes[-1]
                pnl = (lc - entry) / pip_size if d == "buy" else (entry - lc) / pip_size

        rr = max(-10.0, min(10.0, pnl / sl_pips)) if sl_pips else 0

        n_trades += 1
        total_pips += pnl
        sum_dist += dist
        sum_rr += rr
        rr_list.append(rr)
        if settled:
            n_settled += 1
            settle_hours_list.append(settle_h)
            sum_settle_h += settle_h
        if pnl > 0:
            n_winners += 1
            gross_profit += pnl
        elif pnl < 0:
            gross_loss += abs(pnl)
        if hit_sl:
            n_sl += 1
        if timed_out:
            n_timeout += 1

        log.debug(
            f"  {symbol} {window_label} {tdate} {d.upper()} "
            f"entry={entry:.5f} tgt={tgt:.5f} sl={sl_price:.5f} "
            f"dist={dist:.1f} pnl={pnl:.1f} rr={rr:.2f} "
            f"{'SETTLED' if settled else 'SL' if hit_sl else 'TIMEOUT'} {settle_h:.1f}h"
        )

    if n_trades == 0:
        return None

    return {
        "symbol": symbol,
        "window": window_label,
        "flags": fc.label,
        "n": n_trades,
        "settle_rate": round(n_settled / n_trades * 100, 1),
        "win_rate": round(n_winners / n_trades * 100, 1),
        "pf": round(gross_profit / max(gross_loss, 0.001), 2),
        "total_pips": round(total_pips, 0),
        "avg_pips": round(total_pips / n_trades, 1),
        "avg_settle_h": round(sum_settle_h / max(n_settled, 1), 1),
        "med_settle_h": round(np.median(settle_hours_list), 1) if settle_hours_list else 0,
        "avg_rr": round(sum_rr / n_trades, 2),
        "med_rr": round(np.median(rr_list), 2) if rr_list else 0,
        "avg_dist": round(sum_dist / n_trades, 1),
        "pct_timeout": round(n_timeout / n_trades * 100, 1),
    }


# ─── Stats Helpers ───────────────────────────────────────────────────────────

def pick_best(rows, min_n=30, min_wr=50, min_pf=1.0):
    """Pick the best row by PF, with minimum trade count and WR."""
    valid = [r for r in rows if r and r["n"] >= min_n
             and r["win_rate"] >= min_wr and r["pf"] >= min_pf]
    if not valid:
        # Relax: just pick best PF with enough trades
        valid = [r for r in rows if r and r["n"] >= min_n and r["pf"] >= 1.0]
    if not valid:
        valid = [r for r in rows if r and r["n"] >= 15]
    if not valid:
        return None
    return max(valid, key=lambda x: x["pf"])


# ─── Walk-Forward Validation ─────────────────────────────────────────────────

def walk_forward_validate(symbol, m15, fwd_bars, h4, d1, fc_list,
                          pip_size, settle_tol, spread, tier_mode,
                          from_date, to_date, block_months=6):
    """Run walk-forward validation: train on N blocks, test on block N+1.

    Returns list of OOS results per block for the best IS config.
    This catches overfitting: if IS PF is 5.0 but OOS PF is 0.8, the config is overfit.
    """
    from_dt = pd.Timestamp(from_date)
    to_dt = pd.Timestamp(to_date)

    # Build block boundaries
    blocks = []
    current = from_dt
    while current < to_dt:
        block_end = current + pd.DateOffset(months=block_months)
        if block_end > to_dt:
            block_end = to_dt
        blocks.append((current, block_end))
        current = block_end

    if len(blocks) < 3:
        log.warning(f"  {symbol}: Not enough data for walk-forward ({len(blocks)} blocks, need >= 3)")
        return []

    # Precompute indicators on full dataset
    m15_ema_arr = ema(m15["Close"].values, 21)
    h4_trend_arr = map_h4_to_m15(m15["datetime"], compute_h4_trend(h4)) if not h4.empty else None
    llr_b, llr_s = compute_llr_flags(m15["High"].values, m15["Low"].values, m15["Close"].values, len(m15))
    period_levels = compute_prev_period_levels(d1) if not d1.empty else {}

    oos_results = []

    for test_idx in range(2, len(blocks)):
        # Train on blocks 0..test_idx-1
        train_start = blocks[0][0]
        train_end = blocks[test_idx - 1][1]
        test_start = blocks[test_idx][0]
        test_end = blocks[test_idx][1]

        # Filter data for train period
        train_m15 = m15[(m15["datetime"] >= train_start) & (m15["datetime"] < train_end)].reset_index(drop=True)
        train_fwd = fwd_bars[(fwd_bars["datetime"] >= train_start) & (fwd_bars["datetime"] < train_end)].reset_index(drop=True)

        if train_m15.empty or train_fwd.empty:
            continue

        # Find best config on training data (simplified: test all offsets + all combos)
        best_is = None
        best_is_config = None
        for offset in OFFSETS_UTC:
            label = f"offset_{offset:02d}:00"
            targets = compute_window_targets(train_m15, start_hour=offset, duration_hours=24)
            if not targets:
                continue
            for fc in fc_list:
                r = simulate(symbol, targets, train_m15, train_fwd, fc, pip_size,
                             settle_tol, spread, tier_mode, m15_ema_arr, h4_trend_arr,
                             llr_b, llr_s, period_levels, label)
                if r and r["n"] >= 15 and r["pf"] >= 1.0:
                    if best_is is None or r["pf"] > best_is["pf"]:
                        best_is = r
                        best_is_config = (offset, fc, label)

        if best_is_config is None:
            continue

        # Test that same config on OOS block
        offset, fc, label = best_is_config
        test_m15 = m15[(m15["datetime"] >= test_start) & (m15["datetime"] < test_end)].reset_index(drop=True)
        test_fwd = fwd_bars[(fwd_bars["datetime"] >= test_start) & (fwd_bars["datetime"] < test_end)].reset_index(drop=True)

        if test_m15.empty or test_fwd.empty:
            continue

        targets = compute_window_targets(test_m15, start_hour=offset, duration_hours=24)
        if not targets:
            continue

        oos = simulate(symbol, targets, test_m15, test_fwd, fc, pip_size,
                       settle_tol, spread, tier_mode, m15_ema_arr, h4_trend_arr,
                       llr_b, llr_s, period_levels, label)

        oos_results.append({
            "block": f"{test_start.strftime('%Y-%m')}->{test_end.strftime('%Y-%m')}",
            "is_pf": best_is["pf"],
            "is_wr": best_is["win_rate"],
            "is_n": best_is["n"],
            "oos_pf": oos["pf"] if oos else 0,
            "oos_wr": oos["win_rate"] if oos else 0,
            "oos_n": oos["n"] if oos else 0,
            "config": best_is_config[2] + " " + fc.label,
        })

    return oos_results


# ─── Main Runner ─────────────────────────────────────────────────────────────

def run(symbols, data_dir, from_date, to_date, source_label, validate=False):

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    from_dt = pd.Timestamp(from_date)
    to_dt = pd.Timestamp(to_date)
    spread_overrides = load_spreads(data_dir)

    offset_best = []    # one row per symbol
    intraday_best = []  # one row per symbol
    all_rows = []       # everything for CSV
    wf_results = {}     # walk-forward results per symbol

    t0 = time.time()

    for symbol in symbols:
        if symbol not in INSTRUMENTS:
            log.info(f"  [SKIP] Unknown: {symbol}")
            continue

        pip_size, settle_tol, default_spread, tier_mode = INSTRUMENTS[symbol]
        spread = spread_overrides.get(symbol, default_spread)

        log.info(f"\n  {symbol} (spread={spread})...")

        m15 = load_csv(symbol, "M15", data_dir)
        h4 = load_csv(symbol, "H4", data_dir)
        d1 = load_csv(symbol, "D1", data_dir)

        # Load M5 for forward simulation, fall back to M15
        m5 = load_csv(symbol, "M5", data_dir)
        if not m5.empty:
            fwd_bars = m5
            log.info(f"    Using M5 bars for forward simulation ({len(m5)} bars)")
        else:
            fwd_bars = m15
            log.info(f"    M5 not available, falling back to M15 for forward simulation")

        if m15.empty:
            log.warning(f"    NO M15 DATA")
            continue

        # Filter date range (clean reassignment, no in-place mutation)
        m15 = m15[(m15["datetime"] >= from_dt) & (m15["datetime"] <= to_dt)].reset_index(drop=True)
        fwd_bars = fwd_bars[(fwd_bars["datetime"] >= from_dt) & (fwd_bars["datetime"] <= to_dt)].reset_index(drop=True)
        if not h4.empty:
            h4 = h4[(h4["datetime"] >= from_dt) & (h4["datetime"] <= to_dt)].reset_index(drop=True)
        if not d1.empty:
            d1 = d1[(d1["datetime"] >= from_dt) & (d1["datetime"] <= to_dt)].reset_index(drop=True)

        if m15.empty or fwd_bars.empty:
            log.warning(f"    NO DATA after date filter")
            continue

        # Precompute indicators
        m15_ema_arr = ema(m15["Close"].values, 21)
        h4_trend_arr = map_h4_to_m15(m15["datetime"], compute_h4_trend(h4)) if not h4.empty else None
        llr_b, llr_s = compute_llr_flags(m15["High"].values, m15["Low"].values, m15["Close"].values, len(m15))
        period_levels = compute_prev_period_levels(d1) if not d1.empty else {}

        sym_offset_rows = []
        sym_intra_rows = []

        # Offset windows
        for offset in OFFSETS_UTC:
            label = f"offset_{offset:02d}:00"
            targets = compute_window_targets(m15, start_hour=offset, duration_hours=24)
            if not targets:
                continue
            for fc in ALL_COMBOS:
                r = simulate(symbol, targets, m15, fwd_bars, fc, pip_size, settle_tol,
                             spread, tier_mode, m15_ema_arr, h4_trend_arr,
                             llr_b, llr_s, period_levels, label)
                if r:
                    r["target_type"] = "offset"
                    sym_offset_rows.append(r)
                    all_rows.append(r)
            log.info(".")

        # Intraday windows
        for sh, dur in INTRADAY_WINDOWS:
            eh = (sh + dur) % 24
            label = f"intra_{sh:02d}-{eh:02d}_{dur}h"
            targets = compute_window_targets(m15, start_hour=sh, duration_hours=dur)
            if not targets:
                continue
            for fc in ALL_COMBOS:
                r = simulate(symbol, targets, m15, fwd_bars, fc, pip_size, settle_tol,
                             spread, tier_mode, m15_ema_arr, h4_trend_arr,
                             llr_b, llr_s, period_levels, label)
                if r:
                    r["target_type"] = "intraday"
                    sym_intra_rows.append(r)
                    all_rows.append(r)
            log.info(".")

        # Pick best
        best_off = pick_best(sym_offset_rows)
        best_intra = pick_best(sym_intra_rows)
        if best_off:
            offset_best.append(best_off)
        if best_intra:
            intraday_best.append(best_intra)

        # Walk-forward validation
        if validate:
            log.info(f"  Running walk-forward validation for {symbol}...")
            wf = walk_forward_validate(
                symbol, m15, fwd_bars, h4, d1, ALL_COMBOS,
                pip_size, settle_tol, spread, tier_mode,
                from_date, to_date)
            if wf:
                wf_results[symbol] = wf

        elapsed = time.time() - t0
        log.info(f"  {symbol} done ({len(sym_offset_rows)}+{len(sym_intra_rows)} combos, {elapsed:.0f}s)")

    # ─── Print Tables ─────────────────────────────────────────────────────────

    hdr = (f"  {'Symbol':<8} {'Window':<24} {'Filters':<20} {'SL':<6} "
           f"{'N':>5} {'WR%':>6} {'PF':>7} {'Pips':>10} "
           f"{'Settle':>7} {'AvgRR':>6} {'MedRR':>6}")
    sep = "  " + "-" * 110

    def fmt(r):
        flags = r["flags"]
        sl = flags.split("|")[-1] if "|" in flags else "tier"
        filt = flags.split("|")[0] if "|" in flags else flags
        pf_str = "  inf " if r['pf'] > 999 else f"{r['pf']:>6.2f}"
        return (f"  {r['symbol']:<8} {r['window']:<24} {filt:<20} {sl:<6} "
                f"{r['n']:>5} {r['win_rate']:>5.1f}% {pf_str} "
                f"{r['total_pips']:>9.0f} {r['avg_settle_h']:>5.1f}h "
                f"{r['avg_rr']:>5.2f} {r['med_rr']:>5.2f}")

    print("\n")
    print("=" * 114)
    print("  OFFSET TARGETS -- Best config per instrument (24h windows)")
    print("=" * 114)
    print(hdr)
    print(sep)
    for r in offset_best:
        print(fmt(r))
    print("=" * 114)

    print("\n")
    print("=" * 114)
    print("  INTRADAY TARGETS -- Best config per instrument (session windows)")
    print("=" * 114)
    print(hdr)
    print(sep)
    for r in intraday_best:
        print(fmt(r))
    print("=" * 114)

    # ─── Walk-Forward Table ──────────────────────────────────────────────────

    if wf_results:
        print("\n")
        print("=" * 114)
        print("  WALK-FORWARD VALIDATION -- In-Sample vs Out-of-Sample")
        print("=" * 114)
        wf_hdr = (f"  {'Symbol':<8} {'Block':<22} {'Config':<30} "
                  f"{'IS_N':>5} {'IS_WR':>6} {'IS_PF':>7} "
                  f"{'OOS_N':>6} {'OOS_WR':>7} {'OOS_PF':>8}")
        print(wf_hdr)
        print(sep)
        for sym, blocks in wf_results.items():
            for b in blocks:
                is_pf = "  inf " if b['is_pf'] > 999 else f"{b['is_pf']:>6.2f}"
                oos_pf = "  inf " if b['oos_pf'] > 999 else f"{b['oos_pf']:>7.2f}"
                print(f"  {sym:<8} {b['block']:<22} {b['config']:<30} "
                      f"{b['is_n']:>5} {b['is_wr']:>5.1f}% {is_pf} "
                      f"{b['oos_n']:>6} {b['oos_wr']:>6.1f}% {oos_pf}")
        print("=" * 114)

    # ─── Save CSV ─────────────────────────────────────────────────────────────

    if all_rows:
        df = pd.DataFrame(all_rows)
        cols = ["symbol", "target_type", "window", "flags",
                "n", "settle_rate", "win_rate", "pf", "total_pips", "avg_pips",
                "avg_settle_h", "med_settle_h", "avg_rr", "med_rr",
                "avg_dist", "pct_timeout"]
        df = df[[c for c in cols if c in df.columns]]
        df.sort_values(["symbol", "target_type", "pf"], ascending=[True, True, False], inplace=True)

        out = OUTPUT_DIR / f"18_best_targets_{source_label}.csv"
        df.to_csv(out, index=False)
        log.info(f"\n  Full CSV: {out} ({len(df)} rows)")

    elapsed = time.time() - t0
    log.info(f"  Total time: {elapsed:.0f}s ({elapsed/60:.1f}min)")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CBS Best Target Finder")
    parser.add_argument("--symbols", default="all", help="Comma-separated or 'all'")
    parser.add_argument("--from-date", default="2023-03-27")
    parser.add_argument("--to-date", default="2026-12-31")
    parser.add_argument("--data-path", type=str, default=None,
                        help="Path to CBS_DATA directory. Auto-detected if not provided.")
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Logging level (DEBUG shows per-trade details)")
    parser.add_argument("--validate", action="store_true",
                        help="Run walk-forward validation (slower, tests for overfitting)")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)-5s %(message)s",
        datefmt="%H:%M:%S",
    )

    # Resolve data path
    if args.data_path:
        data_dir = Path(args.data_path)
        source = "custom"
    else:
        candidates = auto_detect_data_dirs()
        if len(candidates) == 1:
            data_dir = candidates[0]
            source = "auto"
        elif len(candidates) > 1:
            log.error("Multiple CBS_DATA directories found:")
            for c in candidates:
                log.error(f"  {c}")
            log.error("Please specify one with --data-path")
            sys.exit(1)
        else:
            log.error("No CBS_DATA directory found. Provide --data-path.")
            sys.exit(1)

    if not data_dir.exists():
        log.error(f"Data path not found: {data_dir}")
        sys.exit(1)

    if args.symbols.lower() == "all":
        symbols = [s for s in INSTRUMENTS if (data_dir / s).exists()]
    else:
        symbols = [s.strip().upper() for s in args.symbols.split(",")]

    log.info("CBS Best Target Finder")
    log.info(f"  Source:  {source} ({data_dir})")
    log.info(f"  Symbols: {symbols}")
    log.info(f"  Range:   {args.from_date} -> {args.to_date}")
    log.info(f"  Combos:  {len(ALL_COMBOS)} per window (16 filters x {len(SL_MODES)} SL modes)")
    log.info(f"  Windows: {len(OFFSETS_UTC)} offsets + {len(INTRADAY_WINDOWS)} intraday = {len(OFFSETS_UTC) + len(INTRADAY_WINDOWS)}")
    if args.validate:
        log.info(f"  Walk-forward validation: ENABLED (6-month blocks)")

    run(symbols, data_dir, args.from_date, args.to_date, source, validate=args.validate)


if __name__ == "__main__":
    main()
