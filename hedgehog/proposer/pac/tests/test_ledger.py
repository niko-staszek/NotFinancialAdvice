"""Tests for ledger.py — 21-column trade ledger CSV writer."""
from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

import pytest

from hedgehog.proposer.pac.ledger import LedgerRow, TradeLedger


def _row(trade_id: str = "T1") -> LedgerRow:
    return LedgerRow(
        trade_id=trade_id,
        ts_signal=datetime(2024, 1, 1, 0, 0, tzinfo=timezone.utc),
        ts_open=datetime(2024, 1, 1, 0, 5, tzinfo=timezone.utc),
        ts_close=datetime(2024, 1, 1, 1, 0, tzinfo=timezone.utc),
        symbol="EURUSD",
        direction="BUY",
        entry_price=1.10500,
        sl_price=1.10400,
        tp_price=1.10700,
        exit_price=1.10650,
        exit_reason="tp_hit",
        pnl_pips=15.0,
        pnl_money=150.00,
        r_multiple=1.50,
        setup_type="trap",
        direction_strict=True,
        mmd_alignment="confirmed",
        d1_zone="bull_promo",
        confluence_type="mm_d",
        lot_size=1.00,
        risk_pct=1.00,
    )


def test_ledger_writes_header(tmp_path: Path) -> None:
    p = tmp_path / "ledger.csv"
    ledger = TradeLedger(p)
    ledger.close()
    text = p.read_text(encoding="utf-8")
    first_line = text.splitlines()[0]
    expected_cols = (
        "trade_id,ts_signal,ts_open,ts_close,symbol,direction,"
        "entry_price,sl_price,tp_price,exit_price,exit_reason,"
        "pnl_pips,pnl_money,r_multiple,setup_type,direction_strict,"
        "mmd_alignment,d1_zone,confluence_type,lot_size,risk_pct"
    )
    assert first_line == expected_cols


def test_ledger_appends_row(tmp_path: Path) -> None:
    p = tmp_path / "ledger.csv"
    with TradeLedger(p) as ledger:
        ledger.append(_row("T1"))
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    assert len(rows) == 1
    assert rows[0]["trade_id"] == "T1"
    assert rows[0]["symbol"] == "EURUSD"
    assert rows[0]["entry_price"] == "1.105000"  # 6 decimals


def test_ledger_appends_multiple_rows(tmp_path: Path) -> None:
    p = tmp_path / "ledger.csv"
    with TradeLedger(p) as ledger:
        ledger.append(_row("T1"))
        ledger.append(_row("T2"))
        ledger.append(_row("T3"))
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    assert len(rows) == 3
    assert [r["trade_id"] for r in rows] == ["T1", "T2", "T3"]


def test_ledger_formats_floats_with_precision(tmp_path: Path) -> None:
    p = tmp_path / "ledger.csv"
    with TradeLedger(p) as ledger:
        ledger.append(_row())
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    r = rows[0]
    # Prices: 6 decimals
    assert "." in r["entry_price"] and len(r["entry_price"].split(".")[1]) == 6
    # pnl_pips: 1 decimal
    assert r["pnl_pips"] == "15.0"
    # pnl_money: 2 decimals
    assert r["pnl_money"] == "150.00"
    # r_multiple: 2 decimals
    assert r["r_multiple"] == "1.50"
    # lot_size: 2 decimals
    assert r["lot_size"] == "1.00"


def test_ledger_iso_timestamp_format(tmp_path: Path) -> None:
    p = tmp_path / "ledger.csv"
    with TradeLedger(p) as ledger:
        ledger.append(_row())
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    r = rows[0]
    # ISO 8601 with timezone offset
    assert r["ts_signal"] == "2024-01-01T00:00:00+00:00"
    assert r["ts_open"] == "2024-01-01T00:05:00+00:00"
    assert r["ts_close"] == "2024-01-01T01:00:00+00:00"


def test_ledger_context_manager_auto_closes(tmp_path: Path) -> None:
    p = tmp_path / "ledger.csv"
    with TradeLedger(p) as ledger:
        ledger.append(_row())
    # File should be closed after exit; we can still read it
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    assert len(rows) == 1


def test_ledger_boolean_serialization(tmp_path: Path) -> None:
    p = tmp_path / "ledger.csv"
    with TradeLedger(p) as ledger:
        ledger.append(_row())
    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    # direction_strict=True → string "True"
    assert rows[0]["direction_strict"] == "True"
