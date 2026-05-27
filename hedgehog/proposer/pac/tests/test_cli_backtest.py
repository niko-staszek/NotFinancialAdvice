"""Tests for the `backtest` CLI subcommand."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

from hedgehog.proposer.pac.cli import main


def _make_synthetic_bars_csv(path: Path, n: int = 200) -> None:
    """Generate a synthetic bars CSV matching the bars.py schema."""
    start = datetime(2024, 1, 1, 9, 0, tzinfo=timezone.utc)
    times = [start + timedelta(minutes=5 * i) for i in range(n)]
    closes: list[float] = []
    for i in range(n):
        if i < 50:
            closes.append(100.0)
        elif i < 90:
            closes.append(100.0 + (i - 50) * 0.25)
        elif i < 110:
            closes.append(110.0 - (i - 90) * 0.30)
        elif i < 130:
            closes.append(104.0 + (i - 110) * 0.80)
        else:
            closes.append(110.0)
    df = pd.DataFrame({
        "time_utc": pd.to_datetime(times, utc=True),
        "open": closes,
        "high": [c + 0.5 for c in closes],
        "low": [c - 0.5 for c in closes],
        "close": closes,
        "tick_volume": [100] * n,
        "real_volume": [0] * n,
        "spread": [1] * n,
    })
    df["time_utc"] = df["time_utc"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    df.to_csv(path, index=False)


def test_cli_backtest_runs_to_completion(tmp_path: Path) -> None:
    bars_csv = tmp_path / "bars.csv"
    _make_synthetic_bars_csv(bars_csv, n=200)
    ledger_csv = tmp_path / "ledger.csv"
    rc = main([
        "backtest",
        "--bars", str(bars_csv),
        "--symbol", "EURUSD",
        "--output", str(ledger_csv),
    ])
    assert rc == 0
    assert ledger_csv.exists()


def test_cli_backtest_help_lists_subcommand(capsys: pytest.CaptureFixture) -> None:
    """The new `backtest` subcommand should appear in the main --help output."""
    with pytest.raises(SystemExit):
        main(["--help"])
    out = capsys.readouterr().out
    assert "backtest" in out


def test_cli_backtest_missing_bars_arg_fails(tmp_path: Path) -> None:
    """Missing required --bars should cause SystemExit (argparse fail)."""
    with pytest.raises(SystemExit):
        main([
            "backtest",
            "--symbol", "EURUSD",
            "--output", str(tmp_path / "ledger.csv"),
        ])
