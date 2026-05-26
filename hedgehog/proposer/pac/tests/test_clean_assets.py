"""End-to-end test for the clean_assets cleanup script.

The cleanup MUST be move-not-delete: every input file ends up either
in a target bucket directory or back in source (nothing vanishes).
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from hedgehog.proposer.pac.assets import AssetBucket
import importlib.util


def _load_script(repo_root: Path):
    spec = importlib.util.spec_from_file_location(
        "clean_assets", repo_root / "PAC" / "scripts" / "clean_assets.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_clean_assets_moves_files_into_buckets(
    tmp_path: Path, sample_assets_dir: Path
) -> None:
    # Arrange — copy the synthetic sample into a writable tmp location
    work_src = tmp_path / "assests"
    shutil.copytree(sample_assets_dir, work_src)
    junk_dir = tmp_path / "_junk"
    keep_dir = tmp_path / "source-materials"
    report_path = tmp_path / "report.md"
    original_count = len(list(work_src.iterdir()))

    # Act — load the script and call its main function.
    # __file__ is at NotFinancialAdvice/hedgehog/proposer/pac/tests/test_clean_assets.py
    # parents: [0]=tests, [1]=pac, [2]=proposer, [3]=hedgehog, [4]=NotFinancialAdvice
    repo_root = Path(__file__).resolve().parents[4]
    script = _load_script(repo_root)
    result = script.clean_assets(
        src=work_src, junk_dir=junk_dir, keep_dir=keep_dir, report_path=report_path
    )

    # Assert — total file conservation
    moved_total = sum(result["counts"].values())
    assert moved_total == original_count
    # No file remains in src
    assert list(work_src.iterdir()) == []

    # Expected bucket contents
    assert (junk_dir / "emoji").exists()
    assert (junk_dir / "emoji-gif").exists()
    assert (junk_dir / "avatars").exists()
    assert (keep_dir / "strategy-artifacts").exists()
    assert (keep_dir / "chart-screenshots").exists()

    # Specific files in their right places
    assert (junk_dir / "emoji" / "1f44d-27259a90ef10d877.svg").exists()
    assert (junk_dir / "emoji-gif" / "665401015754817546-119f066c3d20d54f.gif").exists()
    assert (junk_dir / "avatars" / "01761a07197eec8c674c28785b607435-65a7e6fde92c7a21.png").exists()
    assert (keep_dir / "strategy-artifacts" / "fibbo_pac-fddd5163b7cfe9b2.set").exists()
    assert (keep_dir / "chart-screenshots" / "Zrzut_ekranu_2025-03-04_10-15.png").exists()

    # Report written
    assert report_path.exists()
    report_text = report_path.read_text(encoding="utf-8")
    assert "## Bucket counts" in report_text


def test_clean_assets_idempotent_on_empty(tmp_path: Path) -> None:
    """Running on an already-empty source yields zeroed counts, not an error."""
    src = tmp_path / "empty"
    src.mkdir()
    repo_root = Path(__file__).resolve().parents[4]
    script = _load_script(repo_root)
    result = script.clean_assets(
        src=src,
        junk_dir=tmp_path / "j",
        keep_dir=tmp_path / "k",
        report_path=tmp_path / "r.md",
    )
    assert sum(result["counts"].values()) == 0
