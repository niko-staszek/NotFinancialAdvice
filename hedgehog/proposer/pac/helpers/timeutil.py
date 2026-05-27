"""Polish-local-time conversion + session classification.

Per strategy_ea.md §2.3, sessions are defined in Polish local time:
    Asia    23:00 – 07:59 (wraps midnight)
    London  08:00 – 13:59
    America 14:00 – 21:59
    Dead    22:00 – 22:59

Polish DST rules:
    CET  (UTC+1) — last Sunday of October at 01:00 UTC → last Sunday of March at 01:00 UTC
    CEST (UTC+2) — last Sunday of March at 01:00 UTC → last Sunday of October at 01:00 UTC

This module computes the offset at runtime from the bar's UTC datetime,
NOT from a hard-coded transition table.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

# Non-wrapping sessions in Polish local time. (name, start_hour_inclusive, end_hour_exclusive).
_SESSIONS = [
    ("london", 8, 14),
    ("america", 14, 22),
    ("dead", 22, 23),
]


def _last_sunday(year: int, month: int) -> int:
    """Return the day-of-month of the last Sunday of the given month."""
    for day in range(31, 24, -1):
        try:
            d = datetime(year, month, day)
        except ValueError:
            continue
        if d.weekday() == 6:  # Sunday
            return day
    raise RuntimeError(f"no Sunday found in {year}-{month:02d}")


def polish_offset_hours(utc_dt: datetime) -> int:
    """Return the Polish offset in hours (1 = CET, 2 = CEST) for the given UTC datetime."""
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    year = utc_dt.year
    spring = datetime(year, 3, _last_sunday(year, 3), 1, 0, tzinfo=timezone.utc)
    fall = datetime(year, 10, _last_sunday(year, 10), 1, 0, tzinfo=timezone.utc)
    if spring <= utc_dt < fall:
        return 2  # CEST
    return 1  # CET


def utc_to_polish_local(utc_dt: datetime) -> datetime:
    """Convert a UTC datetime to a naive Polish-local-time datetime (no tzinfo).

    Naive input is treated as UTC for convenience.
    """
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    offset = polish_offset_hours(utc_dt)
    pl = utc_dt.astimezone(timezone(timedelta(hours=offset)))
    return pl.replace(tzinfo=None)


def session_for(utc_dt: datetime) -> str:
    """Return the session name for a UTC datetime: 'asia', 'london', 'america', or 'dead'."""
    pl = utc_to_polish_local(utc_dt)
    hour = pl.hour
    # Asia first — wraps midnight.
    if hour >= 23 or hour < 8:
        return "asia"
    for name, start, end in _SESSIONS:
        if start <= hour < end:
            return name
    return "dead"


def is_in_session(utc_dt: datetime, session_name: str) -> bool:
    """Convenience: True iff `utc_dt` falls in the named session."""
    return session_for(utc_dt) == session_name
