"""Fetch ~2yr M5 bars for the 11 PSND instruments from the running MT5 terminal.

Writes CBS/data/<SYMBOL>_M5_<from>_<to>.csv per available instrument and a
_fetch_report.json documenting which symbols were found/missing. Operational
glue — no analysis logic here.

MT5 returns "(-2, 'Invalid params')" when a single copy_rates_range spans too many
M5 bars, so history is pulled in monthly chunks, deduplicated, and concatenated.
The CSV schema matches CBS/cbs/bars.py:
    time_utc, open, high, low, close, tick_volume, real_volume, spread

Usage:  python scripts/fetch_cbs_data.py [--years 2]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import MetaTrader5 as mt5

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from CBS.cbs.config import INSTRUMENTS

DATA = REPO / "CBS" / "data"

# PSND instrument name -> broker symbol where they differ (e.g. oil is WTI here).
SYMBOL_ALIASES = {"XTIUSD": "WTI"}

CHUNK_DAYS = 28  # monthly chunks stay under MT5's per-call M5 limit


def _ts(unix: int) -> str:
    return datetime.fromtimestamp(unix, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _resolve(sym: str, syms: set[str]) -> str | None:
    alias = SYMBOL_ALIASES.get(sym)
    if sym in syms:
        return sym
    if alias and alias in syms:
        return alias
    return next((s for s in syms if s.upper().startswith(sym)), None)


def _fetch_chunked(symbol: str, start: datetime, end: datetime) -> list:
    """Pull M5 bars in CHUNK_DAYS windows; dedup by bar time, sorted ascending."""
    mt5.symbol_select(symbol, True)
    seen: dict[int, tuple] = {}
    cursor = start
    step = timedelta(days=CHUNK_DAYS)
    while cursor < end:
        nxt = min(cursor + step, end)
        rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M5, cursor, nxt)
        if rates is not None:
            for r in rates:
                seen[int(r["time"])] = r
        cursor = nxt
    return [seen[t] for t in sorted(seen)]


def _write_csv(path: Path, rates: list) -> int:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time_utc", "open", "high", "low", "close", "tick_volume", "real_volume", "spread"])
        for r in rates:
            w.writerow([
                _ts(int(r["time"])),
                float(r["open"]), float(r["high"]), float(r["low"]), float(r["close"]),
                int(r["tick_volume"]), int(r["real_volume"]), int(r["spread"]),
            ])
    return len(rates)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, default=2)
    args = ap.parse_args()

    DATA.mkdir(parents=True, exist_ok=True)
    if not mt5.initialize():
        print(f"MT5 init failed: {mt5.last_error()}", file=sys.stderr)
        sys.exit(1)

    end = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=365 * args.years)
    syms = {s.name for s in mt5.symbols_get()}

    report = {"requested": list(INSTRUMENTS), "found": [], "missing": [], "files": {}, "rows": {}}
    for sym in INSTRUMENTS:
        match = _resolve(sym, syms)
        if match is None:
            report["missing"].append(sym)
            print(f"MISSING {sym}: no broker symbol", file=sys.stderr)
            continue
        rates = _fetch_chunked(match, start, end)
        if not rates:
            report["missing"].append(sym)
            print(f"NO DATA {sym} ({match}): {mt5.last_error()}", file=sys.stderr)
            continue
        out = DATA / f"{sym}_M5_{start.date()}_{end.date()}.csv"
        n = _write_csv(out, rates)
        report["found"].append(sym)
        report["files"][sym] = str(out.relative_to(REPO))
        report["rows"][sym] = n
        print(f"OK {sym} ({match}): {n} bars -> {out.name}")

    mt5.shutdown()
    (DATA / "_fetch_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("found", "missing", "rows")}, indent=2))


if __name__ == "__main__":
    main()
