#!/usr/bin/env python
"""Run MQL5 unit-test scripts and aggregate their MQL5TEST results.

Each `Scripts/PAC_Tests/test_pac_*.mq5` script emits one structured sentinel
line per assertion (see `Scripts/PAC_Tests/helpers/TestRunner.mqh`):

    MQL5TEST {"test":"name","result":"PASS"}
    MQL5TEST {"test":"name","result":"FAIL","expected":"X","got":"Y"}

This harness has two clearly separated layers:

1.  **Pure parsing layer** (`parse_mql5test_lines`, `parse_log_file`,
    `TestResults`). Given the raw text of an MT5 log, it counts PASS/FAIL,
    flags malformed sentinels, collects failure detail, and computes the
    process exit code. This layer needs NOTHING from MetaTrader 5 and is
    fully unit-tested in `tools/tests/test_run_mql5_tests.py`.

2.  **MT5-invocation shell** (`find_mt5_log_dir`, `run_test_script`,
    `run_all`, `main`). A thin wrapper that launches `terminal64.exe` in
    `/Script` mode for each test script, then feeds the resulting log file
    to the parsing layer. This layer can only run on a machine with MT5
    installed and the repo `mt5/` junctioned into the terminal data dir
    (see `PAC/mt5/README.md`); it is therefore NOT exercised by the unit
    tests. Keeping it a thin shell is deliberate: all the logic worth
    testing lives in layer 1.

Exit code: 0 iff at least one sentinel was seen AND every sentinel was a
PASS. A run that produced zero sentinels (script crashed / never ran) or
any FAIL / malformed sentinel exits non-zero.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Default MT5 install / data-dir locations (Windows). Overridable via CLI.
DEFAULT_MT5_TERMINAL = Path(r"C:\Program Files\MetaTrader 5\terminal64.exe")
DEFAULT_MT5_DATA_ROOT = (
    Path.home() / "AppData" / "Roaming" / "MetaQuotes" / "Terminal"
)
DEFAULT_SCRIPT_DIR = ROOT / "PAC" / "mt5" / "Scripts" / "PAC_Tests"

# `MQL5TEST` followed by optional whitespace then the remainder of the line
# starting at the opening brace. MQL5's Print() concatenates comma-separated
# args with no separator, so the emitted token is `MQL5TEST {...}` (one
# space); we also tolerate no space. We capture from `{` to end-of-line
# rather than requiring a matching `}` so that a TRUNCATED sentinel (log line
# cut off mid-write) still reaches the JSON parser and is flagged malformed
# instead of being silently dropped.
_SENTINEL_RE = re.compile(r"MQL5TEST\s*(\{[^\n\r]*)")


# ─── Layer 1: pure parsing (unit-tested, no MT5 required) ────────────
@dataclass
class TestResults:
    """Aggregated outcome of parsing one or more MQL5 log streams."""

    passed: int = 0
    failed: int = 0
    malformed: int = 0
    failures: list[dict] = field(default_factory=list)

    @property
    def total(self) -> int:
        """Count of well-formed PASS/FAIL sentinels (excludes malformed)."""
        return self.passed + self.failed

    @property
    def exit_code(self) -> int:
        """0 only if something ran and everything that ran passed cleanly."""
        if self.passed == 0 and self.failed == 0:
            return 1  # nothing ran — never a silent green
        if self.failed > 0 or self.malformed > 0:
            return 1
        return 0

    @classmethod
    def merge(cls, results: list["TestResults"]) -> "TestResults":
        out = cls()
        for r in results:
            out.passed += r.passed
            out.failed += r.failed
            out.malformed += r.malformed
            out.failures.extend(r.failures)
        return out


def parse_mql5test_lines(text: str) -> TestResults:
    """Parse MQL5TEST sentinel lines out of raw log text.

    Lines that are not valid JSON, or whose `result` is neither PASS nor
    FAIL, are counted as `malformed` (never silently treated as a pass).
    """
    res = TestResults()
    for match in _SENTINEL_RE.finditer(text):
        blob = match.group(1)
        try:
            obj = json.loads(blob)
        except (json.JSONDecodeError, ValueError):
            res.malformed += 1
            continue
        if not isinstance(obj, dict):
            res.malformed += 1
            continue
        result = obj.get("result")
        if result == "PASS":
            res.passed += 1
        elif result == "FAIL":
            res.failed += 1
            res.failures.append(
                {
                    "test": obj.get("test", "<unnamed>"),
                    "expected": obj.get("expected"),
                    "got": obj.get("got"),
                }
            )
        else:
            res.malformed += 1
    return res


def parse_log_file(log_path: Path) -> TestResults:
    """Read an MT5 log file and parse its MQL5TEST sentinels.

    MT5 writes logs as UTF-16-LE; we fall back to UTF-8 for synthetic/test
    files. A missing file yields an empty TestResults (exit_code 1).
    """
    if not log_path.exists():
        return TestResults()
    raw = log_path.read_bytes()
    for encoding in ("utf-16-le", "utf-8", "latin-1"):
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        # A correct decode of an MT5 log will contain the sentinel token if
        # any assertions ran; if not, fall through to the next encoding only
        # when this decode produced no readable sentinel AND looked wrong.
        if "MQL5TEST" in text or encoding == "latin-1":
            return parse_mql5test_lines(text)
    return parse_mql5test_lines(raw.decode("latin-1", errors="replace"))


# ─── Layer 2: MT5-invocation shell (NOT unit-tested — needs MT5) ─────
def find_mt5_log_dir(data_root: Path = DEFAULT_MT5_DATA_ROOT) -> Path:
    """Return the most recently modified `<terminal>/MQL5/Logs` directory."""
    candidates = list(data_root.glob("*/MQL5/Logs"))
    if not candidates:
        raise FileNotFoundError(f"No MT5 log dir under {data_root}")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _latest_log(log_dir: Path) -> Path | None:
    logs = sorted(log_dir.glob("*.log"))
    return logs[-1] if logs else None


def run_test_script(
    script_rel: str,
    terminal: Path,
    log_dir: Path,
    symbol: str = "EURUSD",
    period: str = "M5",
    settle_seconds: float = 8.0,
) -> TestResults:
    """Launch one MQL5 test script under MT5 /Script mode and parse its log.

    This is intentionally a thin shell: it shells out to terminal64.exe,
    waits for the script to write its log, then defers to `parse_log_file`.
    Only runnable where MT5 is installed.
    """
    before = _latest_log(log_dir)
    cmd = [str(terminal), f"/Script:{script_rel}", f"/Symbol:{symbol}", f"/Period:{period}"]
    print(f"  launching: {' '.join(cmd)}")
    subprocess.run(cmd, check=False)
    time.sleep(settle_seconds)
    log = _latest_log(log_dir)
    if log is None:
        print(f"  WARNING: no log file appeared in {log_dir}")
        return TestResults()
    if before is not None and log == before:
        # Same file — script appended to today's log; parse it anyway.
        pass
    return parse_log_file(log)


def run_all(
    script_dir: Path,
    terminal: Path,
    data_root: Path,
    glob: str = "test_pac_*.mq5",
) -> TestResults:
    scripts = sorted(script_dir.glob(glob))
    if not scripts:
        print(f"No {glob} scripts found in {script_dir}")
        return TestResults()
    log_dir = find_mt5_log_dir(data_root)
    print(f"Reading logs from {log_dir}")
    per_script: list[TestResults] = []
    for script in scripts:
        rel = script.name  # MT5 resolves relative to MQL5/Scripts/...
        print(f"Running {rel} ...")
        per_script.append(run_test_script(rel, terminal, log_dir))
    return TestResults.merge(per_script)


def _report(res: TestResults) -> None:
    for f in res.failures:
        print(f"FAIL: {f['test']} expected={f['expected']!r} got={f['got']!r}")
    if res.malformed:
        print(f"WARNING: {res.malformed} malformed MQL5TEST line(s) ignored")
    print(f"=== {res.passed} passed, {res.failed} failed, "
          f"{res.malformed} malformed ===")
    if res.total == 0:
        print("ERROR: no MQL5TEST sentinels found — did any script run?")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--script-dir", type=Path, default=DEFAULT_SCRIPT_DIR,
                        help="dir of test_pac_*.mq5 scripts")
    parser.add_argument("--terminal", type=Path, default=DEFAULT_MT5_TERMINAL,
                        help="path to terminal64.exe")
    parser.add_argument("--data-root", type=Path, default=DEFAULT_MT5_DATA_ROOT,
                        help="MetaQuotes/Terminal data root")
    parser.add_argument("--glob", default="test_pac_*.mq5",
                        help="glob for test scripts (e.g. test_orb_*.mq5)")
    parser.add_argument("--log-file", type=Path, default=None,
                        help="parse this existing MT5 log instead of "
                             "invoking MT5 (offline mode)")
    args = parser.parse_args(argv)

    if args.log_file is not None:
        # Offline mode: skip MT5 entirely and just parse a captured log.
        res = parse_log_file(args.log_file)
        _report(res)
        return res.exit_code

    res = run_all(args.script_dir, args.terminal, args.data_root, args.glob)
    _report(res)
    return res.exit_code


if __name__ == "__main__":
    sys.exit(main())
