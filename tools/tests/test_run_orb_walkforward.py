"""Tests for tools/run_orb_walkforward.py — pure-function unit tests only.

Tested: rolling_windows, stitch_oos.
NOT tested here: walk(), select_on_is() — those require MT5 terminal.

Import convention: load module by file path via importlib so tools/ need not be
an importable package (matches test_orb_gate.py pattern). The module's own
sys.path shim makes sibling imports (orb_gate, audit, run_orb_backtest) resolve
at load time without actually calling them.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "run_orb_walkforward", ROOT / "tools" / "run_orb_walkforward.py"
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["run_orb_walkforward"] = _mod
_spec.loader.exec_module(_mod)

rolling_windows = _mod.rolling_windows
stitch_oos = _mod.stitch_oos


def test_rolling_windows_cover_and_step():
    w = rolling_windows("2021-01-01", "2024-01-01", is_months=12, oos_months=3)
    assert w[0]["is_from"] == "2021.01.01"
    assert w[0]["oos_from"] == "2022.01.01" and w[0]["oos_to"] == "2022.04.01"
    assert w[1]["oos_from"] == "2022.04.01"
    assert all(x["oos_to"] <= "2024.01.01" for x in w)


def test_stitch_concats_oos_rows():
    a = [{"net_pnl": "10"}]
    b = [{"net_pnl": "-4"}]
    assert len(stitch_oos([a, b])) == 2
