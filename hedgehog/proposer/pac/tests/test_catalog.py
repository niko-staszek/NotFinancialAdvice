"""End-to-end test for chatdump → trades_catalog.csv pipeline."""
from __future__ import annotations

import csv
from pathlib import Path

from hedgehog.proposer.pac.catalog import build_catalog


def test_build_catalog_partitions_by_confidence(
    sample_chatdump_path: Path, tmp_out: Path
) -> None:
    catalog_csv = tmp_out / "trades_catalog.csv"
    unparsed_csv = tmp_out / "trades_unparsed.csv"
    cache_path = tmp_out / "translation_cache.json"

    summary = build_catalog(
        chatdump_path=sample_chatdump_path,
        catalog_csv=catalog_csv,
        unparsed_csv=unparsed_csv,
        translation_cache_path=cache_path,
        offline=True,  # tests must not hit the network
    )

    assert catalog_csv.exists()
    assert unparsed_csv.exists()

    with catalog_csv.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Sample contains 3 mentor messages with explicit BUY/SELL/MM keywords =>
    # all 3 should land HIGH or MEDIUM (one mentor post 104 has no price ->
    # may be LOW or unparsed depending on detector rules).
    # Two of them have prices => HIGH.
    high = [r for r in rows if r["confidence"] == "high"]
    assert len(high) >= 2
    symbols = {r["symbol"] for r in rows}
    assert {"EURUSD", "GBPUSD"}.issubset(symbols)

    # Mentor flag set correctly for both HIGH rows.
    for r in high:
        if r["symbol"] in {"EURUSD", "GBPUSD"}:
            assert r["is_mentor"] == "true"

    # Summary reports counts.
    assert summary["total_messages"] == 5
    assert summary["catalog_rows"] >= 2
