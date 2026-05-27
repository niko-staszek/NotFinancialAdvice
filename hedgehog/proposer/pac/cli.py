"""Unified CLI for Phase 0 chatdump analysis.

Usage:
    python -m hedgehog.proposer.pac.cli <subcommand> [args]

Subcommands:
    parse-chatdump      Build trades_catalog.csv + trades_unparsed.csv
    analyze-components  Build component_frequency.md
    analyze-setups     Build setup_distribution.md
    audit-mentors       Build mentor_audit.md
    all                 Run every subcommand in order, writing outputs into one dir
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .audit import audit_mentor_trades
from .catalog import build_catalog
from .freq import analyze_component_frequency
from .setup_distribution import analyze_setup_distribution
from .bars import read_bars_csv
from .config import Config
from .engine import run_backtest
from .ledger import TradeLedger


def _add_parse_chatdump(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("parse-chatdump", help="Build trades_catalog.csv + trades_unparsed.csv")
    p.add_argument("--chatdump", required=True)
    p.add_argument("--catalog", required=True)
    p.add_argument("--unparsed", required=True)
    p.add_argument("--cache", required=True)
    p.add_argument("--offline", action="store_true",
                   help="Skip the translator on cache miss (pass through Polish text).")


def _add_analyze_components(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("analyze-components", help="Build component_frequency.md")
    p.add_argument("--chatdump", required=True)
    p.add_argument("--report", required=True)


def _add_analyze_setups(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("analyze-setups", help="Build setup_distribution.md")
    p.add_argument("--catalog", required=True)
    p.add_argument("--report", required=True)


def _add_audit_mentors(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("audit-mentors", help="Build mentor_audit.md")
    p.add_argument("--catalog", required=True)
    p.add_argument("--report", required=True)


def _add_all(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("all", help="Run the full Phase 0 pipeline.")
    p.add_argument("--chatdump", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--offline", action="store_true")


def _add_backtest(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("backtest", help="Run a Plan 4 vectorized backtest on a CSV bar history")
    p.add_argument("--bars", required=True, help="Path to CSV of M5 bars (mt5_data.py dump-bars output)")
    p.add_argument("--symbol", required=True, help="Symbol being traded (e.g., EURUSD, XAUUSD)")
    p.add_argument("--output", required=True, help="Path to write trade ledger CSV")
    p.add_argument("--report", help="Optional path to write a summary markdown report")
    p.add_argument("--initial-equity", type=float, default=10000.0, help="Starting account equity for the simulation")
    p.add_argument(
        "--d1-bars",
        type=str,
        default=None,
        help=(
            "Optional path to a D1 OHLC CSV. When supplied, the engine "
            "resolves the §3.3 D1 promo zone against the previous UTC "
            "calendar day's D1 bar per signal bar instead of always "
            "returning 'neutral'."
        ),
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pac")
    sub = parser.add_subparsers(dest="cmd", required=True)
    _add_parse_chatdump(sub)
    _add_analyze_components(sub)
    _add_analyze_setups(sub)
    _add_audit_mentors(sub)
    _add_all(sub)
    _add_backtest(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "parse-chatdump":
        build_catalog(
            chatdump_path=Path(args.chatdump),
            catalog_csv=Path(args.catalog),
            unparsed_csv=Path(args.unparsed),
            translation_cache_path=Path(args.cache),
            offline=args.offline,
        )
        return 0

    if args.cmd == "analyze-components":
        analyze_component_frequency(
            chatdump_path=Path(args.chatdump),
            report_path=Path(args.report),
        )
        return 0

    if args.cmd == "analyze-setups":
        analyze_setup_distribution(
            catalog_csv=Path(args.catalog),
            report_path=Path(args.report),
        )
        return 0

    if args.cmd == "audit-mentors":
        audit_mentor_trades(
            catalog_csv=Path(args.catalog),
            report_path=Path(args.report),
        )
        return 0

    if args.cmd == "all":
        out = Path(args.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        catalog = out / "trades_catalog.csv"
        unparsed = out / "trades_unparsed.csv"
        cache = out / "translation_cache.json"
        comp = out / "component_frequency.md"
        setups = out / "setup_distribution.md"
        audit = out / "mentor_audit.md"
        build_catalog(
            chatdump_path=Path(args.chatdump),
            catalog_csv=catalog,
            unparsed_csv=unparsed,
            translation_cache_path=cache,
            offline=args.offline,
        )
        analyze_component_frequency(
            chatdump_path=Path(args.chatdump),
            report_path=comp,
        )
        analyze_setup_distribution(catalog_csv=catalog, report_path=setups)
        audit_mentor_trades(catalog_csv=catalog, report_path=audit)
        return 0

    if args.cmd == "backtest":
        bars, meta = read_bars_csv(Path(args.bars), symbol=args.symbol, timeframe="M5")
        cfg = Config()
        d1_bars = None
        if args.d1_bars:
            d1_bars = pd.read_csv(args.d1_bars, parse_dates=["time_utc"])
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        with TradeLedger(out) as ledger:
            summary = run_backtest(
                bars,
                symbol=args.symbol,
                cfg=cfg,
                ledger=ledger,
                initial_equity=args.initial_equity,
                d1_bars=d1_bars,
            )
        print(f"Backtest complete: {summary}")
        if args.report:
            report_path = Path(args.report)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(
                f"# Backtest report\n\n"
                f"- Symbol: {args.symbol}\n"
                f"- Bars: {meta.rows} ({meta.start_utc} → {meta.end_utc})\n"
                f"- Trades opened: {summary['trades_opened']}\n"
                f"- Trades closed: {summary['trades_closed']}\n"
                f"- Final equity: ${summary['final_equity']:.2f}\n"
                f"- Final PnL: ${summary['final_pnl']:.2f}\n",
                encoding="utf-8",
            )
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
