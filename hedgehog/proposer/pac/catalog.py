"""Chatdump → trades_catalog.csv + trades_unparsed.csv.

For each message in the chatdump:
- Run the trade-mention detector.
- If a trade-mention with confidence HIGH or MEDIUM is produced, write a row
  to `trades_catalog.csv` with translated EN content alongside the Polish text.
- If only LOW confidence, write to `trades_unparsed.csv` for manual triage.
- If no trade-mention at all, skip.

Translation is gated: only mentor posts and HIGH/MEDIUM rows are translated
(student LOW rows skipped) to keep the translation volume tractable.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from .authors import is_mentor
from .reader import iter_messages
from .trade_detector import Confidence, TradeMention, detect_trade_mention
from .translator import TranslationCache


_CATALOG_FIELDS = [
    "message_id", "timestamp", "author_name", "author_nickname", "is_mentor",
    "symbol", "direction", "entry", "sl", "tps", "confidence",
    "content_pl", "content_en", "attachment_count",
]

_UNPARSED_FIELDS = [
    "message_id", "timestamp", "author_name", "author_nickname", "is_mentor",
    "symbol", "content_pl", "attachment_count",
]


def build_catalog(
    chatdump_path: Path,
    catalog_csv: Path,
    unparsed_csv: Path,
    translation_cache_path: Path,
    offline: bool = False,
) -> dict:
    """Stream the chatdump and emit both CSV outputs.

    Returns a summary dict with row counts.
    """
    catalog_csv = Path(catalog_csv)
    unparsed_csv = Path(unparsed_csv)
    catalog_csv.parent.mkdir(parents=True, exist_ok=True)
    unparsed_csv.parent.mkdir(parents=True, exist_ok=True)

    cache = TranslationCache(translation_cache_path, offline=offline)

    total = catalog_rows = unparsed_rows = 0

    with (
        catalog_csv.open("w", encoding="utf-8", newline="") as cat_f,
        unparsed_csv.open("w", encoding="utf-8", newline="") as un_f,
    ):
        cat_w = csv.DictWriter(cat_f, fieldnames=_CATALOG_FIELDS)
        un_w = csv.DictWriter(un_f, fieldnames=_UNPARSED_FIELDS)
        cat_w.writeheader()
        un_w.writeheader()

        for msg in iter_messages(chatdump_path):
            total += 1
            mention = detect_trade_mention(msg)
            if mention is None:
                continue
            author = msg.get("author") or {}
            mentor = is_mentor(author)
            content_pl = msg.get("content") or ""

            if mention.confidence in (Confidence.HIGH, Confidence.MEDIUM):
                content_en = cache.translate(content_pl) if (mentor or mention.confidence is Confidence.HIGH) else ""
                cat_w.writerow({
                    "message_id":      msg.get("id", ""),
                    "timestamp":       msg.get("timestamp", ""),
                    "author_name":     author.get("name") or "",
                    "author_nickname": author.get("nickname") or "",
                    "is_mentor":       "true" if mentor else "false",
                    "symbol":          mention.symbol,
                    "direction":       mention.direction or "",
                    "entry":           "" if mention.entry is None else f"{mention.entry:g}",
                    "sl":              "" if mention.sl is None else f"{mention.sl:g}",
                    "tps":             ";".join(f"{t:g}" for t in mention.tps),
                    "confidence":      mention.confidence.value,
                    "content_pl":      content_pl,
                    "content_en":      content_en,
                    "attachment_count": len(msg.get("attachments") or []),
                })
                catalog_rows += 1
            else:  # LOW
                un_w.writerow({
                    "message_id":      msg.get("id", ""),
                    "timestamp":       msg.get("timestamp", ""),
                    "author_name":     author.get("name") or "",
                    "author_nickname": author.get("nickname") or "",
                    "is_mentor":       "true" if mentor else "false",
                    "symbol":          mention.symbol,
                    "content_pl":      content_pl,
                    "attachment_count": len(msg.get("attachments") or []),
                })
                unparsed_rows += 1

    cache.flush()

    return {
        "total_messages": total,
        "catalog_rows": catalog_rows,
        "unparsed_rows": unparsed_rows,
    }
