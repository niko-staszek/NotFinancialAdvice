"""Tests for tools/run_mql5_tests.py — the MQL5 test harness.

Only the LOG-PARSING surface is unit-tested here. That is the part of the
harness that does NOT require MetaTrader 5: given the raw text of an MT5
Experts/Journal log containing `MQL5TEST {...}` sentinel lines (a mix of
PASS, FAIL, and unrelated/malformed noise), the parser must correctly
count passes/failures, collect failure detail, and drive the process
exit code.

The MT5-invocation path (`run_test_script` / `find_mt5_log_dir`) is a thin
shell around this parser and is exercised only on a machine with MT5
installed — see the module docstring in run_mql5_tests.py.

`MQL5TEST` line format (emitted by Scripts/PAC_Tests/helpers/TestRunner.mqh):
    MQL5TEST {"test":"name","result":"PASS"}
    MQL5TEST {"test":"name","result":"FAIL","expected":"X","got":"Y"}
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / "tools" / "run_mql5_tests.py"

# Import the harness module directly by path so the test does not depend on
# tools/ being an importable package.
_spec = importlib.util.spec_from_file_location("run_mql5_tests", HARNESS)
rmt = importlib.util.module_from_spec(_spec)
sys.modules["run_mql5_tests"] = rmt
_spec.loader.exec_module(rmt)


# ─── A representative MT5 log: 3 PASS, 2 FAIL, plus noise ─────────────
SAMPLE_LOG = """\
0	14:01:02.123	Scripts	test_pac_pip (EURUSD,M5)	initializing
0	14:01:02.130	Scripts	test_pac_pip (EURUSD,M5)	MQL5TEST {"test":"PipSize_EURUSD","result":"PASS"}
0	14:01:02.131	Scripts	test_pac_pip (EURUSD,M5)	MQL5TEST {"test":"PipSize_XAUUSD","result":"PASS"}
0	14:01:02.140	Scripts	test_pac_pip (EURUSD,M5)	some unrelated log line, not a sentinel
0	14:01:02.150	Scripts	test_pac_pip (EURUSD,M5)	MQL5TEST {"test":"PipSize_Unknown","result":"FAIL","expected":"0.0","got":"0.0001"}
0	14:01:02.160	Scripts	test_pac_pip (EURUSD,M5)	MQL5TEST {"test":"PriceToPips_EURUSD","result":"PASS"}
0	14:01:02.170	Scripts	test_pac_pip (EURUSD,M5)	MQL5TEST {"test":"PipsToPrice_XAUUSD","result":"FAIL","expected":"5.0","got":"4.9"}
0	14:01:02.180	Scripts	test_pac_pip (EURUSD,M5)	test_pac_pip: done
"""


def test_parser_counts_passes_and_failures():
    res = rmt.parse_mql5test_lines(SAMPLE_LOG)
    assert res.passed == 3
    assert res.failed == 2
    assert res.total == 5


def test_parser_collects_failure_detail():
    res = rmt.parse_mql5test_lines(SAMPLE_LOG)
    names = [f["test"] for f in res.failures]
    assert names == ["PipSize_Unknown", "PipsToPrice_XAUUSD"]
    # expected/got carried through verbatim
    first = res.failures[0]
    assert first["expected"] == "0.0"
    assert first["got"] == "0.0001"


def test_exit_code_zero_when_all_pass():
    log = (
        'MQL5TEST {"test":"a","result":"PASS"}\n'
        'MQL5TEST {"test":"b","result":"PASS"}\n'
    )
    res = rmt.parse_mql5test_lines(log)
    assert res.passed == 2
    assert res.failed == 0
    assert res.exit_code == 0


def test_exit_code_nonzero_when_any_fail():
    log = (
        'MQL5TEST {"test":"a","result":"PASS"}\n'
        'MQL5TEST {"test":"b","result":"FAIL","expected":"1","got":"2"}\n'
    )
    res = rmt.parse_mql5test_lines(log)
    assert res.passed == 1
    assert res.failed == 1
    assert res.exit_code == 1


def test_exit_code_nonzero_when_no_sentinels_found():
    # A run that emitted zero MQL5TEST lines is a failure (the script never
    # ran, or crashed before any assertion) — never a silent green.
    res = rmt.parse_mql5test_lines("just noise\nno sentinels here\n")
    assert res.total == 0
    assert res.exit_code == 1


def test_malformed_json_is_counted_separately_not_as_pass():
    log = (
        'MQL5TEST {"test":"good","result":"PASS"}\n'
        'MQL5TEST {this is not valid json}\n'
        'MQL5TEST {"test":"truncated","result":\n'
    )
    res = rmt.parse_mql5test_lines(log)
    assert res.passed == 1
    assert res.failed == 0
    assert res.malformed == 2
    # A malformed sentinel must NOT pass silently.
    assert res.exit_code == 1


def test_unknown_result_value_is_malformed():
    # result that is neither PASS nor FAIL is not a valid assertion outcome.
    log = 'MQL5TEST {"test":"weird","result":"SKIPPED"}\n'
    res = rmt.parse_mql5test_lines(log)
    assert res.passed == 0
    assert res.failed == 0
    assert res.malformed == 1
    assert res.exit_code == 1


def test_prefix_with_concatenated_no_space_brace():
    # MQL5 Print() concatenates its comma-separated args with no separator,
    # so the real emitted text is `MQL5TEST {...}` (one space after the
    # literal token). Also tolerate accidental loss of that space.
    log = (
        'MQL5TEST {"test":"with_space","result":"PASS"}\n'
        'MQL5TEST{"test":"no_space","result":"PASS"}\n'
    )
    res = rmt.parse_mql5test_lines(log)
    assert res.passed == 2
    assert res.failed == 0


def test_parse_log_file_round_trip(tmp_path):
    # parse_log_file reads a file (utf-16-le or utf-8) and returns the same
    # TestResults the string parser would.
    log_file = tmp_path / "20260528.log"
    log_file.write_text(SAMPLE_LOG, encoding="utf-16-le")
    res = rmt.parse_log_file(log_file)
    assert res.passed == 3
    assert res.failed == 2


def test_parse_log_file_missing_returns_empty(tmp_path):
    res = rmt.parse_log_file(tmp_path / "does_not_exist.log")
    assert res.total == 0
    assert res.exit_code == 1


def test_results_merge_aggregates():
    a = rmt.parse_mql5test_lines('MQL5TEST {"test":"a","result":"PASS"}\n')
    b = rmt.parse_mql5test_lines(
        'MQL5TEST {"test":"b","result":"FAIL","expected":"1","got":"2"}\n'
    )
    merged = rmt.TestResults.merge([a, b])
    assert merged.passed == 1
    assert merged.failed == 1
    assert merged.total == 2
    assert merged.exit_code == 1
    assert [f["test"] for f in merged.failures] == ["b"]
