"""Tests for Polish-local-time conversion with DST per strategy_ea.md §2.3."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from hedgehog.proposer.pac.helpers.timeutil import (
    utc_to_polish_local,
    is_in_session,
    session_for,
)


def _utc(year: int, month: int, day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def test_winter_cet_offset_plus_one() -> None:
    # 2026-01-15 12:00 UTC → 13:00 Polish local (CET)
    pl = utc_to_polish_local(_utc(2026, 1, 15, 12))
    assert pl.hour == 13
    assert pl.minute == 0


def test_summer_cest_offset_plus_two() -> None:
    # 2026-07-15 12:00 UTC → 14:00 Polish local (CEST)
    pl = utc_to_polish_local(_utc(2026, 7, 15, 12))
    assert pl.hour == 14


def test_dst_spring_forward_last_sunday_of_march_2026() -> None:
    # Spring transition 2026: last Sunday of March = 29 March 2026
    # Before 01:00 UTC on 29 March → still CET (+1)
    # At 01:00 UTC on 29 March → CEST (+2). MT5 server time and most brokers transition
    # at this UTC instant. Our timeutil aligns with that.
    pre = utc_to_polish_local(_utc(2026, 3, 29, 0, 30))   # 00:30 UTC = 01:30 CET
    post = utc_to_polish_local(_utc(2026, 3, 29, 1, 30))  # 01:30 UTC = 03:30 CEST
    assert pre.hour == 1
    assert post.hour == 3


def test_dst_fall_back_last_sunday_of_october_2026() -> None:
    # Fall transition 2026: last Sunday of October = 25 October 2026
    # Before 01:00 UTC on 25 October → CEST (+2)
    # At 01:00 UTC on 25 October → CET (+1)
    pre = utc_to_polish_local(_utc(2026, 10, 25, 0, 30))   # 00:30 UTC = 02:30 CEST
    post = utc_to_polish_local(_utc(2026, 10, 25, 1, 30))  # 01:30 UTC = 02:30 CET
    assert pre.hour == 2
    assert post.hour == 2  # both 02:30 local; this is the duplicated "fallback" hour


@pytest.mark.parametrize("utc_hour,expected_session", [
    (22, "asia"),   # 23:00 PLT (winter) — Asia opens
    (23, "asia"),   # midnight PLT — still Asia
    (3, "asia"),    # 04:00 PLT — still Asia
    (6, "asia"),    # 07:00 PLT — Asia closes 07:59
    (7, "london"),  # 08:00 PLT — London opens
    (12, "london"), # 13:00 PLT — still London (closes 13:59)
    (13, "america"),# 14:00 PLT — America opens
    (20, "america"),# 21:00 PLT — America still on (closes 21:59)
    (21, "dead"),   # 22:00 PLT — dead hour
])
def test_session_for_winter_cet(utc_hour: int, expected_session: str) -> None:
    """Session classification for winter (CET, +1 offset)."""
    # Use Jan 15 2026 (CET)
    dt_utc = _utc(2026, 1, 15, utc_hour)
    assert session_for(dt_utc) == expected_session


def test_is_in_session_london() -> None:
    # 10:00 UTC on 2026-01-15 → 11:00 CET → London session
    assert is_in_session(_utc(2026, 1, 15, 10), "london") is True
    # 22:00 UTC → 23:00 CET → Asia
    assert is_in_session(_utc(2026, 1, 15, 22), "london") is False


def test_empty_datetime_naive_treated_as_utc() -> None:
    """A naive datetime (no tzinfo) is treated as UTC for convenience."""
    naive = datetime(2026, 1, 15, 12, 0)
    pl = utc_to_polish_local(naive)
    assert pl.hour == 13  # CET = UTC+1
