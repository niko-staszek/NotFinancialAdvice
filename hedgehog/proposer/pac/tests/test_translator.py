"""Tests for the cached Polish→English translator."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from hedgehog.proposer.pac.translator import TranslationCache


class _StubTranslator:
    """Counts calls; returns deterministic uppercase as the 'translation'."""
    def __init__(self) -> None:
        self.calls = 0

    def translate(self, text: str) -> str:
        self.calls += 1
        return f"<EN>{text.upper()}</EN>"


def test_translates_on_first_call(tmp_path: Path) -> None:
    cache_path = tmp_path / "cache.json"
    stub = _StubTranslator()
    cache = TranslationCache(cache_path, translator=stub)

    out = cache.translate("dzień dobry")
    assert out == "<EN>DZIEŃ DOBRY</EN>"
    assert stub.calls == 1


def test_second_call_hits_cache(tmp_path: Path) -> None:
    cache_path = tmp_path / "cache.json"
    stub = _StubTranslator()
    cache = TranslationCache(cache_path, translator=stub)

    cache.translate("dzień dobry")
    cache.translate("dzień dobry")
    assert stub.calls == 1


def test_cache_persists_across_instances(tmp_path: Path) -> None:
    cache_path = tmp_path / "cache.json"
    stub1 = _StubTranslator()
    cache1 = TranslationCache(cache_path, translator=stub1)
    cache1.translate("test")
    cache1.flush()

    stub2 = _StubTranslator()
    cache2 = TranslationCache(cache_path, translator=stub2)
    out = cache2.translate("test")
    assert out == "<EN>TEST</EN>"
    assert stub2.calls == 0  # served from on-disk cache


def test_empty_string_short_circuits(tmp_path: Path) -> None:
    """Empty input returns empty output without calling the translator."""
    stub = _StubTranslator()
    cache = TranslationCache(tmp_path / "c.json", translator=stub)
    assert cache.translate("") == ""
    assert stub.calls == 0


def test_offline_mode_returns_input_when_no_cache_hit(tmp_path: Path) -> None:
    """Offline mode never calls the translator; returns original text on miss."""
    cache_path = tmp_path / "cache.json"
    stub = _StubTranslator()
    cache = TranslationCache(cache_path, translator=stub, offline=True)
    out = cache.translate("brak tłumaczenia")
    assert out == "brak tłumaczenia"
    assert stub.calls == 0
