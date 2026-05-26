"""Mentor-trade audit.

Reads the trades catalog, keeps mentor rows, infers setup type from the
content, and flags deviations (missing SL, missing TP, no direction, no
attachment). Output is a markdown table the user reviews to arbitrate
auto-classifications.
"""
from __future__ import annotations

import csv
from pathlib import Path

from .components import setup_for


def _flags(row: dict, setup: str) -> list[str]:
    f: list[str] = []
    if not row.get("direction"):
        f.append("missing_direction")
    if not row.get("sl"):
        f.append("missing_sl")
    if not row.get("tps"):
        f.append("missing_tp")
    if not row.get("attachment_count") or row.get("attachment_count") == "0":
        f.append("no_screenshot")
    if setup == "unclassified":
        f.append("unclassified_setup")
    return f


def audit_mentor_trades(catalog_csv: Path, report_path: Path) -> dict:
    rows_out: list[dict] = []
    with Path(catalog_csv).open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("is_mentor") != "true":
                continue
            content = row.get("content_pl") or ""
            setup = setup_for(content)
            rows_out.append({**row, "setup": setup, "flags": "|".join(_flags(row, setup))})

    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_md(rows_out), encoding="utf-8")
    return {"mentor_rows": len(rows_out)}


def _render_md(rows: list[dict]) -> str:
    lines = [
        "# Mentor-trade audit",
        "",
        f"Mentor rows: **{len(rows)}**",
        "",
        "| ts | author | symbol | dir | entry | sl | tps | setup | flags | msg_id |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            "| {ts} | {auth} | {sym} | {dir} | {entry} | {sl} | {tps} | {setup} | {flags} | {mid} |".format(
                ts=r.get("timestamp", ""),
                auth=r.get("author_nickname", "") or r.get("author_name", ""),
                sym=r.get("symbol", ""),
                dir=r.get("direction", ""),
                entry=r.get("entry", ""),
                sl=r.get("sl", ""),
                tps=r.get("tps", ""),
                setup=r.get("setup", ""),
                flags=r.get("flags", ""),
                mid=r.get("message_id", ""),
            )
        )
    return "\n".join(lines) + "\n"
