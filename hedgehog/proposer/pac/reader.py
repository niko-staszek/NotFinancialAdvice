"""Streaming reader for DiscordChatExporter JSON dumps.

Uses ijson to walk `messages[*]` without loading the full file. The
chatdump in this project is 42MB with 15k messages; loading it whole
works but doubles peak memory and is slow on cold runs.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

import ijson


def iter_messages(path: Path) -> Iterator[dict]:
    """Yield each message dict from a DiscordChatExporter JSON file.

    The file is streamed; only one message is materialized at a time.
    """
    with open(path, "rb") as f:
        yield from ijson.items(f, "messages.item")
