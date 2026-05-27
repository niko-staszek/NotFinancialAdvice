"""Tests for instrument whitelist + symbol canonicalization + session re-exports."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from hedgehog.proposer.pac.universe import (
    DEFAULT_SYMBOLS,
    ALL_SYMBOLS_WITH_GC,
    normalize_symbol,
    is_tradable,
    session_for,
    is_in_session,
    utc_to_polish_local,
)


def test_default_symbols_excludes_gc() -> None:
    assert "GC" not in DEFAULT_SYMBOLS
    assert "XAUUSD" in DEFAULT_SYMBOLS
    assert "USOIL" in DEFAULT_SYMBOLS


def test_all_symbols_with_gc_includes_gc() -> None:
    assert "GC" in ALL_SYMBOLS_WITH_GC
    assert set(DEFAULT_SYMBOLS).issubset(set(ALL_SYMBOLS_WITH_GC))


@pytest.mark.parametrize("raw,canonical", [
    ("GOLD", "XAUUSD"),
    ("gold", "XAUUSD"),
    ("CL", "USOIL"),
    ("cl", "USOIL"),
    ("XAUUSD", "XAUUSD"),     # already canonical
    ("USOIL", "USOIL"),       # already canonical
    ("EURUSD", "EURUSD"),     # no alias
    ("eurusd", "EURUSD"),     # case normalization
    ("US500", "US500"),
])
def test_normalize_symbol(raw: str, canonical: str) -> None:
    assert normalize_symbol(raw) == canonical


def test_is_tradable_default_whitelist() -> None:
    """Default whitelist excludes GC."""
    assert is_tradable("XAUUSD") is True
    assert is_tradable("USOIL") is True
    assert is_tradable("EURUSD") is True
    assert is_tradable("GC") is False  # opt-in only
    assert is_tradable("BTCUSD") is False  # not in v1


def test_is_tradable_with_gc_opt_in() -> None:
    assert is_tradable("GC", enable_gc=True) is True
    assert is_tradable("XAUUSD", enable_gc=True) is True
    assert is_tradable("BTCUSD", enable_gc=True) is False


def test_is_tradable_normalizes_alias() -> None:
    """Aliases should resolve before whitelist check."""
    assert is_tradable("GOLD") is True       # → XAUUSD, which is tradable
    assert is_tradable("CL") is True         # → USOIL


def test_session_re_exports_work() -> None:
    """session_for and is_in_session should be re-exported from helpers/timeutil."""
    dt = datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc)
    # Winter (CET +1) → 11:00 PLT → London
    assert session_for(dt) == "london"
    assert is_in_session(dt, "london") is True
    pl = utc_to_polish_local(dt)
    assert pl.hour == 11


# -------- PIP_FACTOR_BY_SYMBOL + lookup_pip_factor --------------------------


def test_pip_factor_dict_covers_all_tradable_symbols():
    """Every symbol in the tradable whitelist (incl. GC opt-in) must have a pip factor."""
    from hedgehog.proposer.pac.universe import (
        ALL_SYMBOLS_WITH_GC,
        PIP_FACTOR_BY_SYMBOL,
    )
    for symbol in ALL_SYMBOLS_WITH_GC:
        assert symbol in PIP_FACTOR_BY_SYMBOL, f"{symbol} missing pip factor"


def test_pip_factor_4digit_fx_majors():
    from hedgehog.proposer.pac.universe import lookup_pip_factor
    assert lookup_pip_factor("EURUSD") == 10000
    assert lookup_pip_factor("GBPUSD") == 10000
    assert lookup_pip_factor("USDCAD") == 10000


def test_pip_factor_jpy_pairs():
    # JPY pairs use 2-digit pip = 0.01, pip factor = 100
    from hedgehog.proposer.pac.universe import lookup_pip_factor
    assert lookup_pip_factor("USDJPY") == 100


def test_pip_factor_gold():
    # XAUUSD: 1 pip = $0.10, pip factor = 10
    from hedgehog.proposer.pac.universe import lookup_pip_factor
    assert lookup_pip_factor("XAUUSD") == 10


def test_pip_factor_oil():
    # USOIL: 1 pip = $0.01, pip factor = 100
    from hedgehog.proposer.pac.universe import lookup_pip_factor
    assert lookup_pip_factor("USOIL") == 100


def test_pip_factor_indices():
    # Indices: 1 pip = 1 point, pip factor = 1
    from hedgehog.proposer.pac.universe import lookup_pip_factor
    assert lookup_pip_factor("US500") == 1
    assert lookup_pip_factor("NAS100") == 1


def test_pip_factor_unknown_symbol_raises():
    from hedgehog.proposer.pac.universe import lookup_pip_factor
    with pytest.raises(ValueError, match="Unknown symbol UNKNOWN; add to PIP_FACTOR_BY_SYMBOL"):
        lookup_pip_factor("UNKNOWN")


def test_pip_factor_is_case_sensitive_post_canonicalization():
    # Per universe.py canonicalization, symbols are uppercase. Lowercase should fail.
    from hedgehog.proposer.pac.universe import lookup_pip_factor
    with pytest.raises(ValueError):
        lookup_pip_factor("eurusd")
