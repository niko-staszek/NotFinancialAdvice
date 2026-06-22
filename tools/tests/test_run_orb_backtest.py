"""Tests for tools/run_orb_backtest.py — pure-function unit tests.

No MetaTrader 5 required. Only build_tester_ini and ledger_path_for are
exercised here; run() is terminal-gated and deferred to a later phase.

Import convention: load the module by file path via importlib so tools/
need not be an importable package.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "run_orb_backtest", ROOT / "tools" / "run_orb_backtest.py"
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["run_orb_backtest"] = _mod
_spec.loader.exec_module(_mod)

build_tester_ini = _mod.build_tester_ini
ledger_path_for = _mod.ledger_path_for


def test_ini_contains_window_and_symbol():
    ini = build_tester_ini(
        symbol="US100.cash",
        from_date="2024.01.01",
        to_date="2024.03.31",
        expert="ORB\\ORB_EA.ex5",
        set_file="ORB_US100_baseline.set",
        report="r.htm",
        label="lbl",
    )
    assert "Symbol=US100.cash" in ini and "FromDate=2024.01.01" in ini
    assert "ShutdownTerminal=1" in ini and "Model=1" in ini


def test_ledger_path_uses_label():
    p = ledger_path_for("/data", "win01")
    assert "ledger_win01.csv" in p
