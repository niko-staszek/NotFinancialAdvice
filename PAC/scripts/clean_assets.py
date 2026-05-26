"""Cleanup driver for the PAC chatdump asset folder.

Move-not-delete: every file in `src` is moved to either `junk_dir/<bucket>/`
or `keep_dir/<bucket>/` per the classifier. Writes a markdown report at
`report_path` with bucket counts and example filenames.

CLI usage (with defaults pointing at the scratch workspace):
    python -m PAC.scripts.clean_assets
"""
from __future__ import annotations

import argparse
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List

# Make the hedgehog package importable when invoked directly.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from hedgehog.proposer.pac.assets import AssetBucket, classify_asset  # noqa: E402


_BUCKET_DIRS: Dict[AssetBucket, tuple[str, str]] = {
    # bucket -> (parent kind: 'junk' or 'keep', subdir name)
    AssetBucket.EMOJI_SVG: ("junk", "emoji"),
    AssetBucket.EMOJI_GIF: ("junk", "emoji-gif"),
    AssetBucket.AVATAR: ("junk", "avatars"),
    AssetBucket.STRATEGY_ARTIFACT: ("keep", "strategy-artifacts"),
    AssetBucket.CHART: ("keep", "chart-screenshots"),
}


def clean_assets(
    src: Path,
    junk_dir: Path,
    keep_dir: Path,
    report_path: Path,
) -> dict:
    """Move every file in `src` into the right bucket directory.

    Returns a result dict with `counts` (per-bucket file counts) and
    `examples` (a few filenames per bucket for the report).
    """
    src = Path(src)
    junk_dir = Path(junk_dir)
    keep_dir = Path(keep_dir)
    report_path = Path(report_path)

    counts: Counter = Counter()
    examples: Dict[AssetBucket, List[str]] = {b: [] for b in AssetBucket}

    for child in sorted(src.iterdir()):
        if not child.is_file():
            continue
        try:
            size = child.stat().st_size
        except OSError:
            size = 0
        bucket = classify_asset(child, size_bytes=size)
        parent_kind, subdir = _BUCKET_DIRS[bucket]
        dest_parent = (junk_dir if parent_kind == "junk" else keep_dir) / subdir
        dest_parent.mkdir(parents=True, exist_ok=True)
        dest = dest_parent / child.name
        # If a duplicate name lands in the destination, append a suffix.
        if dest.exists():
            stem, suffix = dest.stem, dest.suffix
            i = 1
            while dest.exists():
                dest = dest_parent / f"{stem}__dup{i}{suffix}"
                i += 1
        shutil.move(str(child), str(dest))
        counts[bucket] += 1
        if len(examples[bucket]) < 5:
            examples[bucket].append(child.name)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(_render_report(counts, examples, src), encoding="utf-8")

    return {"counts": dict(counts), "examples": {b.value: examples[b] for b in AssetBucket}}


def _render_report(counts: Counter, examples: Dict[AssetBucket, List[str]], src: Path) -> str:
    lines: list[str] = []
    lines.append("# Asset cleanup report")
    lines.append("")
    lines.append(f"Source: `{src}`")
    lines.append("")
    lines.append("## Bucket counts")
    lines.append("")
    lines.append("| Bucket | Count |")
    lines.append("|---|---|")
    total = 0
    for b in AssetBucket:
        c = counts.get(b, 0)
        total += c
        lines.append(f"| {b.value} | {c} |")
    lines.append(f"| **TOTAL** | **{total}** |")
    lines.append("")
    lines.append("## Examples per bucket")
    lines.append("")
    for b in AssetBucket:
        if not examples[b]:
            continue
        lines.append(f"### {b.value}")
        for n in examples[b]:
            lines.append(f"- `{n}`")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("Files were **moved**, not deleted. Review the `_junk/` subdirectories and delete manually once happy.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Move PAC assets into junk/keep buckets.")
    p.add_argument("--src", default=r"C:\Users\nikof\Documents\GitHub\PAC\assests",
                   help="Source folder containing mixed assets.")
    p.add_argument("--junk-dir", default=r"C:\Users\nikof\Documents\GitHub\PAC\_junk",
                   help="Destination for junk buckets.")
    p.add_argument("--keep-dir", default=r"C:\Users\nikof\Documents\GitHub\PAC\source-materials",
                   help="Destination for kept buckets.")
    p.add_argument("--report",
                   default=r"C:\Users\nikof\Documents\GitHub\NotFinancialAdvice\PAC\chatdump_analysis\cleanup_report.md",
                   help="Path for the markdown report.")
    args = p.parse_args(argv)
    result = clean_assets(
        src=Path(args.src),
        junk_dir=Path(args.junk_dir),
        keep_dir=Path(args.keep_dir),
        report_path=Path(args.report),
    )
    print(f"Moved {sum(result['counts'].values())} files. Report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
