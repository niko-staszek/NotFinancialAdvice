#!/usr/bin/env python
"""Headless ORB MQL5 self-test runner (FTMO terminal).

Why this exists: terminal64's `/Script:` flag does NOT run a script on this
build (verified 2026-06-22 — the terminal cold-starts but never loads the
script). The working method is `/config:<ini>` with a `[StartUp] Script=...`
section. MT5 is single-instance per data dir, so each test must cold-start a
fresh terminal; our `test_orb_*.mq5` scripts end with `TerminalClose(0)` to
self-terminate, which keeps the next cold-start clean AND lets the blocking
`subprocess.run` return on its own.

Pipeline per test:  sync -> MetaEditor /compile -> write [StartUp] ini ->
cold-start terminal64 /config (blocks until the script self-closes) -> parse
MQL5TEST sentinels with the tested parse layer from run_mql5_tests.

Usage:
    python tools/run_orb_selftest.py                 # all test_orb_*
    python tools/run_orb_selftest.py --name test_orb_range
"""
from __future__ import annotations
import argparse, os, re, subprocess, sys, time
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
from run_mql5_tests import parse_log_file, TestResults  # reuse the tested parse layer

FTMO_DATA = Path(os.environ["APPDATA"]) / "MetaQuotes/Terminal/81A933A9AFC5DE3C23B15CAB19C63850"
TERMINAL = Path(r"C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe")
MEDITOR  = Path(r"C:\Program Files\FTMO Global Markets MT5 Terminal\MetaEditor64.exe")
SCRIPTS_SUBDIR = "ORB_Tests"
REPO = Path(__file__).resolve().parents[1]


def _close_terminals():
    """Best-effort graceful close of any running terminal64 (single-instance guard)."""
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-Process terminal64 -ErrorAction SilentlyContinue | "
         "ForEach-Object { $null = $_.CloseMainWindow() }"],
        check=False,
    )
    time.sleep(3)


def _sync():
    subprocess.run(["pwsh", str(REPO / "tools" / "sync_orb_to_terminal.ps1")], check=False)


def compile_test(name, data_dir=FTMO_DATA, meditor=MEDITOR):
    mq5 = data_dir / "MQL5" / "Scripts" / SCRIPTS_SUBDIR / f"{name}.mq5"
    log = data_dir / "orb_compile.log"
    subprocess.run([str(meditor), f"/compile:{mq5}", f"/log:{log}"], check=False)
    time.sleep(2)
    txt = log.read_text(encoding="utf-16", errors="ignore") if log.exists() else ""
    last = txt.strip().splitlines()[-1] if txt.strip() else "no compile log"
    m = re.search(r"Result:\s*(\d+)\s*error", txt)   # exact count — "0 errors" is a substring of "30 errors"
    ok = (m is not None and int(m.group(1)) == 0)
    return ok, last


def run_test(name, data_dir=FTMO_DATA, terminal=TERMINAL, timeout=120):
    ini = data_dir / f"orb_selftest_{name}.ini"
    ini.write_text(
        f"[StartUp]\nScript={SCRIPTS_SUBDIR}\\{name}\nSymbol=EURUSD\nPeriod=M5\n",
        encoding="ascii",
    )
    logdir = data_dir / "MQL5" / "Logs"
    for f in logdir.glob("2*.log"):
        try:
            f.unlink()
        except OSError:
            pass
    try:
        subprocess.run([str(terminal), f"/config:{ini}"], check=False, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"[{name}] TIMEOUT — terminal did not self-close (missing TerminalClose?)")
        _close_terminals()
    logs = sorted(logdir.glob("2*.log"))
    return parse_log_file(logs[-1]) if logs else TestResults()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--name", help="single test (e.g. test_orb_range); default runs all test_orb_*")
    ap.add_argument("--no-sync", action="store_true", help="skip the repo->terminal sync step")
    args = ap.parse_args(argv)

    if not args.no_sync:
        _sync()
    _close_terminals()

    src_dir = REPO / "ORB" / "mt5" / "Scripts" / SCRIPTS_SUBDIR
    names = [args.name] if args.name else [p.stem for p in sorted(src_dir.glob("test_orb_*.mq5"))]
    if not names:
        print("no test_orb_*.mq5 scripts found")
        return 1

    results = []
    for nm in names:
        ok, line = compile_test(nm)
        print(f"[{nm}] compile: {line}")
        if not ok:
            print(f"[{nm}] COMPILE FAILED")
            results.append(TestResults(failed=1))
            continue
        r = run_test(nm)
        print(f"[{nm}] {r.passed} passed, {r.failed} failed, {r.malformed} malformed")
        for f in r.failures:
            print(f"    FAIL {f['test']}: expected={f['expected']} got={f['got']}")
        results.append(r)

    merged = TestResults.merge(results)
    print(f"=== TOTAL {merged.passed} passed, {merged.failed} failed, {merged.malformed} malformed ===")
    return merged.exit_code


if __name__ == "__main__":
    sys.exit(main())
