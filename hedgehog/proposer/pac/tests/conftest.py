"""Pytest fixtures shared across PAC ingest tests."""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Directory containing test fixtures."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_chatdump_path(fixtures_dir: Path) -> Path:
    """Path to the synthetic chatdump JSON used in tests."""
    return fixtures_dir / "sample_chatdump.json"


@pytest.fixture
def sample_assets_dir(fixtures_dir: Path) -> Path:
    """Path to the synthetic asset folder used in cleanup tests."""
    return fixtures_dir / "sample_assets"


@pytest.fixture
def tmp_out(tmp_path: Path) -> Path:
    """Fresh temporary output directory for tests that write files."""
    out = tmp_path / "out"
    out.mkdir()
    return out
