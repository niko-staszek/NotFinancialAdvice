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

from .audit import audit_mentor_trades
from .catalog import build_catalog
from .freq import analyze_component_frequency
from .setups import analyze_setup_distribution


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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pac")
    sub = parser.add_subparsers(dest="cmd", required=True)
    _add_parse_chatdump(sub)
    _add_analyze_components(sub)
    _add_analyze_setups(sub)
    _add_audit_mentors(sub)
    _add_all(sub)
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

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
