"""Component-frequency analyzer.

Streams the chatdump, classifies each message's PAC components, splits
counts by mentor vs. student, and renders a ranked markdown table.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from .authors import is_mentor
from .components import Component, classify_components
from .reader import iter_messages


def analyze_component_frequency(
    chatdump_path: Path,
    report_path: Path,
) -> dict:
    mentor_counts: Counter[str] = Counter()
    student_counts: Counter[str] = Counter()
    mentor_msgs = 0
    student_msgs = 0

    for msg in iter_messages(chatdump_path):
        author = msg.get("author") or {}
        mentor = is_mentor(author)
        if mentor:
            mentor_msgs += 1
        else:
            student_msgs += 1
        comps = classify_components(msg.get("content") or "")
        target = mentor_counts if mentor else student_counts
        for c in comps:
            target[c.value] += 1

    counts: dict[str, dict[str, int]] = {}
    for c in Component:
        counts[c.value] = {
            "mentor": mentor_counts.get(c.value, 0),
            "student": student_counts.get(c.value, 0),
        }

    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _render_md(counts, mentor_msgs, student_msgs),
        encoding="utf-8",
    )

    return {
        "mentor_message_count": mentor_msgs,
        "student_message_count": student_msgs,
        "counts": counts,
    }


def _render_md(
    counts: dict[str, dict[str, int]],
    mentor_msgs: int,
    student_msgs: int,
) -> str:
    rows = sorted(counts.items(), key=lambda kv: kv[1]["mentor"], reverse=True)
    lines = [
        "# Component frequency",
        "",
        f"Mentor messages scanned: **{mentor_msgs}**  ·  Student messages scanned: **{student_msgs}**",
        "",
        "Components are ranked by mentor reference count (descending).",
        "",
        "| Component | Mentor | Student | Mentor share |",
        "|---|---:|---:|---:|",
    ]
    for name, c in rows:
        m, s = c["mentor"], c["student"]
        total = m + s
        share = f"{(m / total * 100):.1f}%" if total else "—"
        lines.append(f"| `{name}` | {m} | {s} | {share} |")
    return "\n".join(lines) + "\n"
