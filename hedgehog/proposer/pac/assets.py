"""Asset classifier for the chatdump assets folder.

Rules (from the design spec):
- Emoji SVGs (.svg) → EMOJI_SVG
- Animated emoji GIFs (.gif) → EMOJI_GIF
- Discord avatar pattern (32hex-16hex.{png,jpg}) → AVATAR
- 'unknown-' files smaller than 50KB → AVATAR
- .set / .xmind / .docx / .zip → STRATEGY_ARTIFACT
- Everything else → CHART (screenshots, larger images)
"""
from __future__ import annotations

import re
from enum import Enum
from pathlib import Path

# 32 hex chars, dash, 16 hex chars, then .png/.jpg/.jpeg
_AVATAR_RE = re.compile(r"^[a-f0-9]{32}-[a-f0-9]{16}\.(png|jpg|jpeg)$", re.IGNORECASE)

# Files starting with 'unknown-' AND smaller than this threshold are avatars
_UNKNOWN_AVATAR_MAX_BYTES = 50_000

_STRATEGY_EXTS = {".set", ".xmind", ".docx", ".zip"}


class AssetBucket(Enum):
    EMOJI_SVG = "emoji_svg"
    EMOJI_GIF = "emoji_gif"
    AVATAR = "avatar"
    STRATEGY_ARTIFACT = "strategy_artifact"
    CHART = "chart"


def classify_asset(path: Path, size_bytes: int) -> AssetBucket:
    """Classify a single asset path into one of the buckets."""
    name = path.name
    suffix = path.suffix.lower()

    if suffix == ".svg":
        return AssetBucket.EMOJI_SVG
    if suffix == ".gif":
        return AssetBucket.EMOJI_GIF
    if suffix in _STRATEGY_EXTS:
        return AssetBucket.STRATEGY_ARTIFACT
    if _AVATAR_RE.match(name):
        return AssetBucket.AVATAR
    if name.startswith("unknown-") and size_bytes < _UNKNOWN_AVATAR_MAX_BYTES:
        return AssetBucket.AVATAR
    return AssetBucket.CHART
