"""Tests for tools/python_config_to_mql5_set.py — the Config→MQL5 bridge.

The generator's single source of truth is hedgehog.proposer.pac.config.Config.
These tests assert on the REAL Config field names/defaults (the plan's
MQL5_MAPPING sketch used stale names; the generator reconciles against the
live dataclass and raises if any field is unmapped).
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools" / "python_config_to_mql5_set.py"

PRESET_SYMBOLS = ["XAUUSD", "USOIL", "US500", "NAS100", "EURUSD", "GBPUSD", "USDCAD"]


def _run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
    )


def test_regen_emits_pac_config_mqh(tmp_path):
    out_mqh = tmp_path / "PAC_Config.mqh"
    out_presets_dir = tmp_path / "Presets"
    out_presets_dir.mkdir()
    result = _run(
        "--regen",
        "--mqh-output", str(out_mqh),
        "--presets-dir", str(out_presets_dir),
    )
    assert result.returncode == 0, result.stderr
    assert out_mqh.exists()
    text = out_mqh.read_text(encoding="utf-8")

    # Banner present
    assert "AUTO-GENERATED — DO NOT EDIT" in text

    # Config fields emitted as input declarations (real field -> Inp name).
    assert "input double InpRiskPercent" in text
    assert "input double InpMinRR" in text
    assert "input int    InpEmaPeriod" in text
    # A bool field renders as `input bool`.
    assert "input bool   InpDirectionStrict" in text
    # A tuple field renders as `input string` (correlation_groups).
    assert "input string InpCorrelationGroups" in text

    # Default values match Config() (whitespace before '=' is alignment).
    assert re.search(r"InpRiskPercent\s+= 1\.0;", text)
    assert re.search(r"InpMinRR\s+= 1\.5;", text)
    assert re.search(r"InpEmaPeriod\s+= 21;", text)
    assert re.search(r"InpDirectionStrict\s+= true;", text)

    # Every emitted line traces back to its Config field via a comment.
    assert "// → Config.risk_percent" in text

    # All 7 presets emitted alongside the mqh.
    for sym in PRESET_SYMBOLS:
        assert (out_presets_dir / f"PAC_{sym}_M5.set").exists()


def test_check_passes_when_file_matches(tmp_path):
    out_mqh = tmp_path / "PAC_Config.mqh"
    out_presets_dir = tmp_path / "Presets"
    out_presets_dir.mkdir()
    assert _run("--regen", "--mqh-output", str(out_mqh),
                "--presets-dir", str(out_presets_dir)).returncode == 0
    result = _run("--check", "--mqh-output", str(out_mqh),
                  "--presets-dir", str(out_presets_dir))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "no drift" in result.stdout.lower()


def test_check_fails_when_file_is_stale(tmp_path):
    out_mqh = tmp_path / "PAC_Config.mqh"
    out_presets_dir = tmp_path / "Presets"
    out_presets_dir.mkdir()
    assert _run("--regen", "--mqh-output", str(out_mqh),
                "--presets-dir", str(out_presets_dir)).returncode == 0
    # Corrupt the mqh so it no longer matches the dataclass.
    text = out_mqh.read_text(encoding="utf-8").replace("1.0", "2.0", 1)
    out_mqh.write_text(text, encoding="utf-8")
    result = _run("--check", "--mqh-output", str(out_mqh),
                  "--presets-dir", str(out_presets_dir))
    assert result.returncode != 0
    assert "drift detected" in result.stdout.lower() or "diff" in result.stdout.lower()


def test_preset_mode_emits_set_file(tmp_path):
    out_presets_dir = tmp_path / "Presets"
    out_presets_dir.mkdir()
    result = _run("--preset", "EURUSD", "--presets-dir", str(out_presets_dir))
    assert result.returncode == 0, result.stderr
    preset_file = out_presets_dir / "PAC_EURUSD_M5.set"
    assert preset_file.exists()
    text = preset_file.read_text(encoding="utf-8")
    assert "InpRiskPercent=1.0" in text
    assert "InpMinRR=1.5" in text
    # Bool renders lowercase in .set form.
    assert "InpDirectionStrict=true" in text
