"""21-column CSV writer for trade ledger — Phase 2 triangulation schema."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hedgehog.proposer.pac.config import Config
    from hedgehog.proposer.pac.orders import Position


@dataclass
class LedgerRow:
    """Single trade row in the Phase 2 triangulation schema."""

    trade_id: str
    ts_signal: datetime
    ts_open: datetime
    ts_close: datetime
    symbol: str
    direction: str
    entry_price: float
    sl_price: float
    tp_price: float
    exit_price: float
    exit_reason: str
    pnl_pips: float
    pnl_money: float
    r_multiple: float
    setup_type: str
    direction_strict: bool
    mmd_alignment: str
    d1_zone: str
    confluence_type: str
    lot_size: float
    risk_pct: float


class TradeLedger:
    """Append-mode CSV writer for trade rows in the Phase 2 triangulation schema."""

    _COLS = (
        "trade_id",
        "ts_signal",
        "ts_open",
        "ts_close",
        "symbol",
        "direction",
        "entry_price",
        "sl_price",
        "tp_price",
        "exit_price",
        "exit_reason",
        "pnl_pips",
        "pnl_money",
        "r_multiple",
        "setup_type",
        "direction_strict",
        "mmd_alignment",
        "d1_zone",
        "confluence_type",
        "lot_size",
        "risk_pct",
    )

    def __init__(self, path: Path) -> None:
        """Create parent dir if needed, open file in write mode, write header row."""
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._f = open(self.path, "w", encoding="utf-8", newline="")
        self._writer = csv.writer(self._f)
        self._writer.writerow(self._COLS)
        self._f.flush()

    def append(self, row: LedgerRow) -> None:
        """Format row per schema and write it (do NOT flush)."""
        self._writer.writerow([
            row.trade_id,
            row.ts_signal.isoformat(),
            row.ts_open.isoformat(),
            row.ts_close.isoformat(),
            row.symbol,
            row.direction,
            f"{row.entry_price:.6f}",
            f"{row.sl_price:.6f}",
            f"{row.tp_price:.6f}",
            f"{row.exit_price:.6f}",
            row.exit_reason,
            f"{row.pnl_pips:.1f}",
            f"{row.pnl_money:.2f}",
            f"{row.r_multiple:.2f}",
            row.setup_type,
            str(row.direction_strict),
            row.mmd_alignment,
            row.d1_zone,
            row.confluence_type,
            f"{row.lot_size:.2f}",
            f"{row.risk_pct:.2f}",
        ])

    def write_partial(
        self,
        pos: Position,
        ts_signal: datetime,
        ts_close: datetime,
        exit_price: float,
        cfg: Config,
        pnl_pips: float,
        pnl_money: float,
        r_multiple: float,
    ) -> float:
        """Emit a partial-close ledger row sharing the parent trade's id (Task 6).

        Derives the partial lot size as ``cfg.partials_close_fraction *
        pos.lot_size``, writes a row with ``exit_reason='partial'`` and
        ``trade_id=pos.trade_id``, and returns the lot count that was closed
        so the caller can shrink the in-flight Position before its eventual
        exit row.

        All immutable trade metadata (symbol, direction, entry/SL/TP, setup,
        confluence, MMD, D1 zone) is copied from ``pos``. The ``exit_price``,
        ``pnl_*``, and ``r_multiple`` reflect this partial leg only — the
        engine is responsible for computing them against ``current_price`` at
        the moment ``maybe_partial_close`` fires. The returned lot count gives
        the engine a single source of truth for the partial portion.

        Phase 3 diff: rows sharing a ``trade_id`` must be collapsed before
        applying the match key (otherwise a 2-row partial+exit trade looks
        like two unrelated trades).
        """
        partial_lot_closed = cfg.partials_close_fraction * pos.lot_size
        row = LedgerRow(
            trade_id=pos.trade_id,
            ts_signal=ts_signal,
            ts_open=pos.ts_open,
            ts_close=ts_close,
            symbol=pos.symbol,
            direction=pos.direction,
            entry_price=pos.entry_price,
            sl_price=pos.sl_price,
            tp_price=pos.tp_price,
            exit_price=exit_price,
            exit_reason="partial",
            pnl_pips=pnl_pips,
            pnl_money=pnl_money,
            r_multiple=r_multiple,
            setup_type=pos.setup_type,
            direction_strict=cfg.direction_strict,
            mmd_alignment=pos.mmd_alignment,
            d1_zone=pos.d1_zone,
            confluence_type=pos.confluence_type,
            lot_size=partial_lot_closed,
            risk_pct=cfg.risk_percent,
        )
        self.append(row)
        return partial_lot_closed

    def flush(self) -> None:
        """Flush the file buffer."""
        self._f.flush()

    def close(self) -> None:
        """Flush and close the file."""
        self._f.flush()
        self._f.close()

    def __enter__(self) -> TradeLedger:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit — close file."""
        self.close()
