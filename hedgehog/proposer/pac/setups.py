"""Setup-distribution analyzer.

Pivots the trades catalog by symbol × session × day-of-week × setup_type.
Sessions are bucketed in Polish local time (chatdump timestamps are
already in +01:00 / +02:00 with DST applied by DiscordChatExporter).

Setup type comes from the components present in the row:
- if TRAP_SETUP / FAIL_SETUP / RANGE_TRAP / RANGE_FAIL / SPIKE_FLAG /
  SPIKE_CHANNEL / DOUBLE_TOP_BOTTOM hits, use that name;
- else if MEASURED_MOVE hits → "measured_move";
- else "unclassified".
"""
from __future__ import annotations

import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

from .components import Component, classify_components


_SETUP_PRIORITY: list[Component] = [
    Component.TRAP_SETUP,
    Component.FAIL_SETUP,
    Component.RANGE_TRAP,
    Component.RANGE_FAIL,
    Component.SPIKE_FLAG,
    Component.SPIKE_CHANNEL,
    Component.DOUBLE_TOP_BOTTOM,
    Component.MEASURED_MOVE,
]

_SESSION_BOUNDS_LOCAL = [
    # (name, start_hour_inclusive, end_hour_exclusive) in Polish local time.
    ("asia",    23, 24), ("asia",     0,  8),    # 23:00-07:59 wraps midnight
    ("london",   8, 14),
    ("america", 14, 22),
    ("dead",    22, 23),
]


def _session_for(hour: int) -> str:
    for name, start, end in _SESSION_BOUNDS_LOCAL:
        if start <= hour < end:
            return name
    return "dead"


def _setup_type(text: str) -> str:
    comps = classify_components(text or "")
    for c in _SETUP_PRIORITY:
        if c in comps:
            return c.value
    return "unclassified"


def analyze_setup_distribution(
    catalog_csv: Path,
    report_path: Path,
) -> dict:
    pivot: Counter[tuple[str, str, str, str]] = Counter()
    rows_analyzed = 0

    with Path(catalog_csv).open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ts = row.get("timestamp", "")
            symbol = (row.get("symbol") or "").upper()
            content = row.get("content_pl") or ""
            if not ts or not symbol:
                continue
            try:
                dt = datetime.fromisoformat(ts)
            except ValueError:
                continue
            session = _session_for(dt.hour)
            dow = dt.strftime("%a")  # Mon, Tue, ...
            setup = _setup_type(content)
            pivot[(symbol, session, dow, setup)] += 1
            rows_analyzed += 1

    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_md(pivot, rows_analyzed), encoding="utf-8")

    return {"rows_analyzed": rows_analyzed, "buckets": len(pivot)}


def _render_md(pivot: Counter, rows_analyzed: int) -> str:
    lines = [
        "# Setup distribution",
        "",
        f"Rows analyzed: **{rows_analyzed}**  ·  Distinct buckets: **{len(pivot)}**",
        "",
        "Columns: symbol · session · day-of-week · setup_type · count",
        "",
        "| Symbol | Session | DOW | Setup | Count |",
        "|---|---|---|---|---:|",
    ]
    for (symbol, session, dow, setup), count in pivot.most_common():
        lines.append(f"| {symbol} | {session} | {dow} | {setup} | {count} |")
    return "\n".join(lines) + "\n"
