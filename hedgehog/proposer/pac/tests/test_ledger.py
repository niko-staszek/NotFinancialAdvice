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


def test_partial_close_writes_separate_ledger_row_with_same_trade_id(
    tmp_path: Path,
) -> None:
    """Task 6 — Partial-close ledger row.

    A trade with one partial then full close produces 2 ledger rows
    sharing trade_id, distinguished by exit_reason and ts_close.
    """
    from datetime import datetime, timezone

    from hedgehog.proposer.pac.config import Config
    from hedgehog.proposer.pac.orders import Position

    cfg = Config().replace(partials_enabled=True)
    p = tmp_path / "ledger.csv"

    pos = Position(
        symbol="EURUSD",
        direction="BUY",
        entry_price=1.0820,
        sl_price=1.0810,
        tp_price=1.0850,
        lot_size=1.5,
        ts_open=datetime(2024, 5, 15, 8, 30, 5, tzinfo=timezone.utc),
        setup_type="trap",
        confluence_type="mm_d",
        mmd_alignment="confirmed",
        d1_zone="bull_promo",
        direction_strict_at_entry=True,
        trade_id="abc123",
    )
    ts_signal = datetime(2024, 5, 15, 8, 30, tzinfo=timezone.utc)
    ts_partial = datetime(2024, 5, 15, 9, 15, tzinfo=timezone.utc)
    ts_exit = datetime(2024, 5, 15, 10, 30, tzinfo=timezone.utc)

    with TradeLedger(p) as ledger:
        # Partial close at 1R — write_partial derives the partial lot size
        # from cfg.partials_close_fraction × pos.lot_size, writes the row,
        # and returns the lot count that was closed so the caller can shrink
        # the in-flight Position before the eventual exit row.
        partial_lot_closed = ledger.write_partial(
            pos=pos,
            ts_signal=ts_signal,
            ts_close=ts_partial,
            exit_price=1.0830,
            cfg=cfg,
            pnl_pips=10.0,
            pnl_money=75.0,
            r_multiple=1.0,
        )
        # Engine reduces remaining position size by what the partial closed.
        pos.lot_size -= partial_lot_closed

        # Final TP close — uses ordinary append() via _make_ledger_row caller.
        ledger.append(LedgerRow(
            trade_id=pos.trade_id,
            ts_signal=ts_signal,
            ts_open=pos.ts_open,
            ts_close=ts_exit,
            symbol=pos.symbol,
            direction=pos.direction,
            entry_price=pos.entry_price,
            sl_price=pos.sl_price,
            tp_price=pos.tp_price,
            exit_price=1.0850,
            exit_reason="tp_hit",
            pnl_pips=30.0,
            pnl_money=112.5,
            r_multiple=3.0,
            setup_type=pos.setup_type,
            direction_strict=True,
            mmd_alignment=pos.mmd_alignment,
            d1_zone=pos.d1_zone,
            confluence_type=pos.confluence_type,
            lot_size=pos.lot_size,
            risk_pct=cfg.risk_percent,
        ))

    rows = list(csv.DictReader(p.open(encoding="utf-8")))
    assert len(rows) == 2

    by_reason = {row["exit_reason"]: row for row in rows}
    assert "partial" in by_reason
    assert "tp_hit" in by_reason
    # Same trade_id, different exit_reason and ts_close
    assert by_reason["partial"]["trade_id"] == "abc123"
    assert by_reason["tp_hit"]["trade_id"] == "abc123"
    assert by_reason["partial"]["ts_close"] != by_reason["tp_hit"]["ts_close"]
    # Partial row's lot_size should reflect the closed fraction (0.5 of 1.5 = 0.75)
    assert by_reason["partial"]["lot_size"] == "0.75"
    # Exit row's lot_size should reflect what remained (1.5 - 0.75 = 0.75)
    assert by_reason["tp_hit"]["lot_size"] == "0.75"
