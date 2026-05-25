"""Smoke tests for the unified CLI dispatcher."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from hedgehog.proposer.pac import cli


def test_cli_help_lists_subcommands(capsys: pytest.CaptureFixture) -> None:
    with pytest.raises(SystemExit):
        cli.main(["--help"])
    out = capsys.readouterr().out
    for sub in ("parse-chatdump", "analyze-components", "analyze-setups", "audit-mentors", "all"):
        assert sub in out


def test_cli_parse_chatdump_offline(sample_chatdump_path: Path, tmp_out: Path) -> None:
    rc = cli.main([
        "parse-chatdump",
        "--chatdump", str(sample_chatdump_path),
        "--catalog", str(tmp_out / "trades_catalog.csv"),
        "--unparsed", str(tmp_out / "trades_unparsed.csv"),
        "--cache", str(tmp_out / "cache.json"),
        "--offline",
    ])
    assert rc == 0
    assert (tmp_out / "trades_catalog.csv").exists()


def test_cli_all_runs_full_pipeline(sample_chatdump_path: Path, tmp_out: Path) -> None:
    rc = cli.main([
        "all",
        "--chatdump", str(sample_chatdump_path),
        "--out-dir", str(tmp_out),
        "--offline",
    ])
    assert rc == 0
    for name in (
        "trades_catalog.csv",
        "trades_unparsed.csv",
        "component_frequency.md",
        "setup_distribution.md",
        "mentor_audit.md",
    ):
        assert (tmp_out / name).exists(), f"missing {name}"
