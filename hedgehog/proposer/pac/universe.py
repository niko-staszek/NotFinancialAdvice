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
    "normalize_symbol",
    "is_tradable",
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
