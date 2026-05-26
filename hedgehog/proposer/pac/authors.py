"""Mentor identification for the PAC Discord chatdump.

Verified rule from the design spec: any author whose `name` or `nickname`
contains the substring 'allin' (case-insensitive) is a mentor. This catches
all 13 verified mentor accounts in the chatdump (e.g. `ALLin Paweł Krynicki`,
`allintraders`, etc.) and no student accounts.
"""
from __future__ import annotations

from typing import Mapping, Optional

MENTOR_MARKER = "allin"


def is_mentor(author: Mapping[str, Optional[str]]) -> bool:
    """Return True if `author` is a mentor account.

    Accepts a DiscordChatExporter author dict. Either `name` or `nickname`
    may be missing or None; both are checked case-insensitively for the
    'allin' marker.
    """
    for field in ("name", "nickname"):
        value = author.get(field)
        if value and MENTOR_MARKER in value.lower():
            return True
    return False
