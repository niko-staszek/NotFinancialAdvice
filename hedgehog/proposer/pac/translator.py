"""Polish→English translation with on-disk JSON cache.

We only translate text we actually need to read (mentor posts + high-confidence
trade mentions). Translation is the slow + rate-limited part; the cache makes
re-runs free and lets us swap the backend transparently.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol


class Translator(Protocol):
    def translate(self, text: str) -> str: ...


class _GoogleTranslator:
    """Thin wrapper around deep_translator.GoogleTranslator.

    Imported lazily so the package works in environments without network
    access — only constructed when an uncached translation is requested.
    """
    def __init__(self) -> None:
        from deep_translator import GoogleTranslator  # type: ignore
        self._gt = GoogleTranslator(source="pl", target="en")

    def translate(self, text: str) -> str:
        return self._gt.translate(text)


class TranslationCache:
    """Persistent translation cache.

    Usage:
        cache = TranslationCache(Path('cache.json'))
        en = cache.translate('dzień dobry')
        cache.flush()  # persist (or call .translate(..., flush=True))
    """

    def __init__(
        self,
        cache_path: Path,
        translator: Translator | None = None,
        offline: bool = False,
        flush_every: int = 50,
    ) -> None:
        self.cache_path = Path(cache_path)
        self.offline = offline
        self.flush_every = flush_every
        self._dirty = 0
        self._cache: dict[str, str] = {}
        if self.cache_path.exists():
            try:
                self._cache = json.loads(self.cache_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self._cache = {}
        self._translator = translator

    def translate(self, text: str) -> str:
        if not text:
            return ""
        if text in self._cache:
            return self._cache[text]
        if self.offline:
            return text  # offline: pass-through on miss
        if self._translator is None:
            self._translator = _GoogleTranslator()
        try:
            out = self._translator.translate(text) or text
        except Exception:
            # Translator failure should not break the whole pipeline.
            return text
        self._cache[text] = out
        self._dirty += 1
        if self._dirty >= self.flush_every:
            self.flush()
        return out

    def flush(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(
            json.dumps(self._cache, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._dirty = 0
