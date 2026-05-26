"""Tests for the mentor-trade audit step."""
from __future__ import annotations

import csv
from pathlib import Path

from hedgehog.proposer.pac.audit import audit_mentor_trades


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


def test_filters_to_mentors_and_classifies(tmp_out: Path) -> None:
    catalog = tmp_out / "trades_catalog.csv"
    _write_catalog(catalog, [
        {"message_id": "100", "timestamp": "2024-03-04T11:00:00+01:00",
         "author_nickname": "ALLin Paweł", "is_mentor": "true",
         "symbol": "EURUSD", "direction": "BUY", "entry": "1.085",
         "sl": "1.082", "tps": "1.092", "confidence": "high",
         "content_pl": "measured move", "attachment_count": "1"},
        {"message_id": "101", "timestamp": "2024-03-04T11:30:00+01:00",
         "author_nickname": "Karol", "is_mentor": "false",
         "symbol": "XAUUSD", "confidence": "high",
         "content_pl": "trap", "attachment_count": "0"},
        {"message_id": "102", "timestamp": "2024-03-04T14:00:00+01:00",
         "author_nickname": "ALLin Michał", "is_mentor": "true",
         "symbol": "GBPUSD", "direction": "SELL", "entry": "1.268",
         "confidence": "high",
         "content_pl": "fail po 61.8", "attachment_count": "1"},
    ])
    report_path = tmp_out / "mentor_audit.md"
    summary = audit_mentor_trades(catalog_csv=catalog, report_path=report_path)

    assert summary["mentor_rows"] == 2
    assert report_path.exists()
    text = report_path.read_text(encoding="utf-8")
    # First mentor row classified as measured_move setup, has direction + SL + TP
    assert "measured_move" in text
    assert "EURUSD" in text
    # Second mentor row: SELL GBPUSD with FAIL_SETUP component, no SL field → flagged
    assert "fail" in text
    assert "missing_sl" in text or "missing_tp" in text
