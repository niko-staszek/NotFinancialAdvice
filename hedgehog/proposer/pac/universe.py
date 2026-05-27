"""PAC instrument universe — symbol whitelist + canonicalization + session re-exports.

Per strategy_ea.md §2.1, the v1 EA trades a default 7-symbol whitelist; GC (gold
futures) is opt-in via the `enable_gc` flag (controlled by the EA input
`EnableGCFutures` per the spec).

Symbol aliasing follows the Phase 1a convention:
    GOLD → XAUUSD
    CL   → USOIL

Other symbols (EURUSD, etc.) are passed through unchanged with case normalization.

Session helpers (`session_for`, `is_in_session`, `utc_to_polish_local`) are
re-exported from `helpers/timeutil` so consumer modules can `from .universe import ...`.
"""
from __future__ import annotations

from .helpers.timeutil import (
    is_in_session,
    session_for,
    utc_to_polish_local,
)

__all__ = [
    "DEFAULT_SYMBOLS",
    "ALL_SYMBOLS_WITH_GC",
    "PIP_FACTOR_BY_SYMBOL",
    "normalize_symbol",
    "is_tradable",
    "lookup_pip_factor",
    "session_for",
    "is_in_session",
    "utc_to_polish_local",
]


# Default v1 whitelist (XAUUSD spot, US500 CFD etc.) — excludes GC.
DEFAULT_SYMBOLS: tuple[str, ...] = (
    "XAUUSD", "USOIL", "US500", "NAS100", "EURUSD", "GBPUSD", "USDCAD",
)

# Full whitelist including GC futures (opt-in).
ALL_SYMBOLS_WITH_GC: tuple[str, ...] = DEFAULT_SYMBOLS + ("GC",)


_SYMBOL_ALIASES: dict[str, str] = {
    "GOLD": "XAUUSD",
    "CL": "USOIL",
}


def normalize_symbol(raw: str) -> str:
    """Canonicalize a symbol name — applies alias map + case normalization."""
    upper = raw.upper()
    return _SYMBOL_ALIASES.get(upper, upper)


def is_tradable(symbol: str, *, enable_gc: bool = False) -> bool:
    """Return True iff `symbol` (after canonicalization) is in the active whitelist."""
    canonical = normalize_symbol(symbol)
    whitelist = ALL_SYMBOLS_WITH_GC if enable_gc else DEFAULT_SYMBOLS
    return canonical in whitelist


# Per-symbol pip-factor: multiply price-unit distance by factor to get pip count.
# Derived from strategy_ea.md §0.4 "Pip definitions" table.
# Sources:
#   4-digit FX majors: 1 pip = 0.0001 → factor 10000
#   JPY pairs (2-digit): 1 pip = 0.01 → factor 100
#   Gold (XAUUSD): 1 pip = $0.10 → factor 10
#   Oil (USOIL): 1 pip = $0.01 → factor 100
#   Indices: 1 pip = 1 point (broker-dependent; assume factor 1 for Python side)
PIP_FACTOR_BY_SYMBOL: dict[str, int] = {
    "EURUSD": 10000,
    "GBPUSD": 10000,
    "USDCAD": 10000,
    "USDJPY": 100,
    "XAUUSD": 10,
    "USOIL": 100,
    "US500": 1,
    "NAS100": 1,
    "US30": 1,
    "USTECH": 1,
    "GC": 10,  # gold futures — same convention as spot XAUUSD
}


def lookup_pip_factor(symbol: str) -> int:
    """Return the multiplier to convert price-unit distance to pip count.

    Precondition: ``symbol`` must already be canonical (uppercase, post-alias).
    Call ``normalize_symbol()`` first if the input may be lowercase or an alias
    (e.g., ``GOLD``→``XAUUSD``). This function is intentionally not
    auto-canonicalizing so callers see a loud failure on missed normalization.

    Raises:
        ValueError: if symbol is not in PIP_FACTOR_BY_SYMBOL. Fail-loud
            policy — silent defaults would skew risk on unrecognized
            instruments.
    """
    if symbol not in PIP_FACTOR_BY_SYMBOL:
        raise ValueError(
            f"Unknown symbol {symbol}; add to PIP_FACTOR_BY_SYMBOL"
        )
    return PIP_FACTOR_BY_SYMBOL[symbol]
