"""CBS CLI: run the reverse analysis over fetched data and write an audit run.

Usage:
  python -m CBS.cbs.cli --run pilot --utcstamp 20260609T0000Z
  Optional: --data CBS/data --out CBS/reports --instruments EURUSD XAUUSD \
            --anchors 0 7 12  --blocks 1 4 24
"""
from __future__ import annotations

import argparse
import glob
from pathlib import Path

import pandas as pd

from . import config as C
from .bars import load_m5_csv
from .pipeline import run_instrument, split_in_out_sample
from .report import write_audit_run


def _find_csv(data_dir: Path, symbol: str) -> Path | None:
    hits = sorted(glob.glob(str(data_dir / f"{symbol}_M5_*.csv")))
    return Path(hits[-1]) if hits else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="CBS/data")
    ap.add_argument("--out", default="CBS/reports")
    ap.add_argument("--run", default="pilot")
    ap.add_argument("--utcstamp", required=True, help="UTC stamp string for the run folder")
    ap.add_argument("--instruments", nargs="*", default=list(C.INSTRUMENTS))
    ap.add_argument("--anchors", nargs="*", type=int, default=list(C.ANCHORS))
    ap.add_argument("--blocks", nargs="*", type=int, default=list(C.BLOCKS))
    args = ap.parse_args()

    data_dir = Path(args.data)
    all_timing, all_entries = [], []
    log_lines = []
    for sym in args.instruments:
        csv = _find_csv(data_dir, sym)
        if csv is None:
            log_lines.append(f"SKIP {sym}: no data file")
            continue
        df = load_m5_csv(csv)
        timing, entries = run_instrument(
            df, symbol=sym, pip_size=C.PIP_SIZE[sym], base_tol_pips=C.BASE_TOLERANCE_PIPS[sym],
            anchors=tuple(args.anchors), blocks=tuple(args.blocks),
            tol_mults=C.TOLERANCE_MULTIPLIERS, cap_hours=C.CLOCK_CAP_HOURS,
            atr_period=C.ATR_PERIOD_M5, atr_k=C.ATR_SL_K, lookback_hours=C.ENTRY_LOOKBACK_HOURS,
        )
        all_timing += timing
        all_entries += entries
        log_lines.append(f"OK {sym}: {len(timing)} timing, {len(entries)} entries from {csv.name}")

    cfg = {"instruments": args.instruments, "anchors": args.anchors, "blocks": args.blocks,
           "tol_mults": C.TOLERANCE_MULTIPLIERS, "cap_hours": C.CLOCK_CAP_HOURS,
           "atr_k": C.ATR_SL_K, "atr_period": C.ATR_PERIOD_M5}
    out = write_audit_run(Path(args.out), run_name=args.run, config=cfg,
                          timing=all_timing, entries=all_entries,
                          log_text="\n".join(log_lines), utcstamp=args.utcstamp)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
