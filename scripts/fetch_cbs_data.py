"""Fetch ~2yr M5 bars for the 11 PSND instruments from the running MT5 terminal.

Writes CBS/data/<SYMBOL>_M5_<from>_<to>.csv per available instrument and a
_fetch_report.json documenting which symbols were found/missing. Operational
glue around tools/mt5_data.py — no analysis logic here.

Usage:  python scripts/fetch_cbs_data.py [--years 2]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import MetaTrader5 as mt5

from CBS.cbs.config import INSTRUMENTS

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "CBS" / "data"


def available_symbols() -> set[str]:
    if not mt5.initialize():
        print(f"MT5 init failed: {mt5.last_error()}", file=sys.stderr)
        sys.exit(1)
    syms = {s.name for s in mt5.symbols_get()}
    mt5.shutdown()
    return syms


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, default=2)
    args = ap.parse_args()

    DATA.mkdir(parents=True, exist_ok=True)
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=365 * args.years)
    syms = available_symbols()

    report = {"requested": list(INSTRUMENTS), "found": [], "missing": [], "files": {}}
    for sym in INSTRUMENTS:
        match = sym if sym in syms else next((s for s in syms if s.upper().startswith(sym)), None)
        if match is None:
            report["missing"].append(sym)
            continue
        out = DATA / f"{sym}_M5_{start}_{end}.csv"
        cmd = [sys.executable, str(REPO / "tools" / "mt5_data.py"), "dump-bars",
               match, "M5", str(start), str(end), str(out)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and out.exists():
            report["found"].append(sym)
            report["files"][sym] = str(out.relative_to(REPO))
        else:
            report["missing"].append(sym)
            print(f"dump failed for {sym} ({match}): {res.stdout}{res.stderr}", file=sys.stderr)

    (DATA / "_fetch_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
