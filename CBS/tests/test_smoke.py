"""Smoke test: package is importable from repo root."""
from __future__ import annotations


def test_cbs_package_imports() -> None:
    import CBS.cbs  # noqa: F401
    assert CBS.cbs is not None
