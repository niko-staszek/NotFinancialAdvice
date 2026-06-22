"""Tests for tools/orb_gate.py — the ORB acceptance gate.

Pure-function tests: metrics_from_rows and apply_gate.
No MetaTrader 5 required.

Import convention matches the rest of this test suite: load the module
directly by file path via importlib so tools/ need not be an
importable package.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "orb_gate", ROOT / "tools" / "orb_gate.py"
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["orb_gate"] = _mod
_spec.loader.exec_module(_mod)

metrics_from_rows = _mod.metrics_from_rows
apply_gate = _mod.apply_gate


def _rows(nets):
    return [{"net_pnl": str(x), "r_multiple": "1.0"} for x in nets]


def test_metrics_basic():
    m = metrics_from_rows(_rows([100, -50, 100, -50, 100]))
    assert m["trades"] == 5
    assert round(m["net"], 2) == 200.0
    assert m["max_single_frac"] > 0


def test_gate_rejects_few_trades():
    v = apply_gate(metrics_from_rows(_rows([10, -5, 10])), oos_sharpe=0.8, is_sharpe=0.7)
    assert v["passed"] is False
    assert any("trade count" in r.lower() for r in v["reasons"])


def test_gate_rejects_concentration():
    v = apply_gate(metrics_from_rows(_rows([900] + [10]*9 + [-5]*9)),
                   oos_sharpe=1.0, is_sharpe=0.9)
    assert v["passed"] is False
    assert any("concentration" in r.lower() for r in v["reasons"])


def test_gate_pass():
    # [5, -1]*20: 40 trades, net=80, max_dd=-20%, concentration=6.25% — clears all gates
    nets = [5, -1] * 20
    v = apply_gate(metrics_from_rows(_rows(nets)), oos_sharpe=0.9, is_sharpe=0.8)
    assert v["passed"] is True
