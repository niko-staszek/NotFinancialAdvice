"""Tests for streaming chatdump reader."""
from __future__ import annotations

from pathlib import Path

from hedgehog.proposer.pac.reader import iter_messages


def test_iter_messages_yields_all_five(sample_chatdump_path: Path) -> None:
    msgs = list(iter_messages(sample_chatdump_path))
    assert len(msgs) == 5


def test_iter_messages_yields_dicts_with_expected_keys(sample_chatdump_path: Path) -> None:
    msgs = list(iter_messages(sample_chatdump_path))
    for m in msgs:
        assert "id" in m
        assert "timestamp" in m
        assert "content" in m
        assert "author" in m
        assert "name" in m["author"]


def test_iter_messages_preserves_order(sample_chatdump_path: Path) -> None:
    ids = [m["id"] for m in iter_messages(sample_chatdump_path)]
    assert ids == ["100", "101", "102", "103", "104"]


def test_iter_messages_is_lazy(sample_chatdump_path: Path) -> None:
    """iter_messages returns an iterator, not a list."""
    it = iter_messages(sample_chatdump_path)
    assert iter(it) is it  # iterator protocol
