"""Tests for the component-frequency analyzer."""
from __future__ import annotations

from pathlib import Path

from hedgehog.proposer.pac.freq import analyze_component_frequency
from hedgehog.proposer.pac.components import Component


def test_aggregates_mentor_and_student_counts(
    sample_chatdump_path: Path, tmp_out: Path
) -> None:
    report_path = tmp_out / "component_frequency.md"
    summary = analyze_component_frequency(
        chatdump_path=sample_chatdump_path,
        report_path=report_path,
    )

    # Mentor msgs 100 + 102 + 104 reference MM, signal candle, fail, spike & flag, fibo, etc.
    # Student msg 101 references TRAP_SETUP via "trap setup po dwóch próbach".
    assert summary["mentor_message_count"] == 3
    assert summary["student_message_count"] == 2
    assert summary["counts"][Component.MEASURED_MOVE.value]["mentor"] >= 1
    assert summary["counts"][Component.TRAP_SETUP.value]["student"] >= 1
    assert report_path.exists()
    text = report_path.read_text(encoding="utf-8")
    assert "# Component frequency" in text
    assert Component.MEASURED_MOVE.value in text
