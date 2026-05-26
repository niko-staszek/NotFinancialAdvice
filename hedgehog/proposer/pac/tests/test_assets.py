"""Tests for the asset classifier — pure function over Path + file size."""
from __future__ import annotations

from pathlib import Path

import pytest

from hedgehog.proposer.pac.assets import AssetBucket, classify_asset


@pytest.mark.parametrize("name,size,expected", [
    # emoji SVGs
    ("1f44d-27259a90ef10d877.svg", 2000, AssetBucket.EMOJI_SVG),
    ("2764-a3d2500d7e491034.svg", 1500, AssetBucket.EMOJI_SVG),

    # animated emoji gifs
    ("665401015754817546-119f066c3d20d54f.gif", 50000, AssetBucket.EMOJI_GIF),

    # Discord avatars: 32-hex + dash + 16-hex pattern, small file
    ("01761a07197eec8c674c28785b607435-65a7e6fde92c7a21.png", 30000, AssetBucket.AVATAR),
    ("8404026af17c426d9439df5ef55e6c9c-f04bfabcba16813c.jpg", 25000, AssetBucket.AVATAR),

    # 'unknown-' tiny files = avatars
    ("unknown-e8f8542f492fd003.png", 10000, AssetBucket.AVATAR),
    ("unknown-ade02b8ae5dd13bb.png", 49000, AssetBucket.AVATAR),

    # big 'unknown' file = chart (over 50KB threshold)
    ("unknown-bigchart.png", 200000, AssetBucket.CHART),

    # strategy artifacts
    ("fibbo_pac-fddd5163b7cfe9b2.set", 5000, AssetBucket.STRATEGY_ARTIFACT),
    ("PAC-c7ae6ea991c3703f.docx", 9000, AssetBucket.STRATEGY_ARTIFACT),
    ("Trading_Map_Basic-068087981fdceb8f.xmind", 1500000, AssetBucket.STRATEGY_ARTIFACT),
    ("LabeledLinesDrawingTool-3afd5c96db2297b7.zip", 800000, AssetBucket.STRATEGY_ARTIFACT),

    # chart screenshots
    ("Zrzut_ekranu_2025-03-04_10-15.png", 400000, AssetBucket.CHART),
    ("Screenshot_2024-12-01.jpg", 350000, AssetBucket.CHART),
    ("image0-abc123.jpeg", 250000, AssetBucket.CHART),
    ("obraz-xyz.png", 180000, AssetBucket.CHART),
])
def test_classify_asset(name: str, size: int, expected: AssetBucket) -> None:
    p = Path(name)
    assert classify_asset(p, size_bytes=size) is expected
