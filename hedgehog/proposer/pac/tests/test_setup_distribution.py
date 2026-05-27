"""Tests for setup-distribution analysis (symbol × session × DOW × setup_type)."""
from __future__ import annotations

import csv
from pathlib import Path

from hedgehog.proposer.pac.setup_distribution import analyze_setup_distribution


def _write_catalog(path: Path, rows: list[dict]) -> None:
    fields = [
        "message_id", "timestamp", "author_name", "author_nickname", "is_mentor",
        "symbol", "direction", "entry", "sl", "tps", "confidence",
        "content_pl", "content_en", "attachment_count",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({**{k: "" for k in fields}, **r})


def test_pivot_by_symbol_session_dow_setup(tmp_out: Path) -> None:
    catalog = tmp_out / "trades_catalog.csv"
    _write_catalog(catalog, [
        # London session (Polish CET ~11:00) Monday
        {"timestamp": "2024-03-04T11:00:00.000+01:00",
         "symbol": "EURUSD", "is_mentor": "true",
         "content_pl": "BUY EURUSD measured move", "confidence": "high"},
        # America session (Polish CET ~17:00) Friday
        {"timestamp": "2024-03-08T17:00:00.000+01:00",
         "symbol": "XAUUSD", "is_mentor": "true",
         "content_pl": "trap setup XAUUSD", "confidence": "high"},
    ])
    report_path = tmp_out / "setup_distribution.md"
    summary = analyze_setup_distribution(catalog_csv=catalog, report_path=report_path)

    assert report_path.exists()
    # Two rows -> two distinct setup types tagged.
    assert summary["rows_analyzed"] == 2
    text = report_path.read_text(encoding="utf-8")
    assert "EURUSD" in text
    assert "XAUUSD" in text
