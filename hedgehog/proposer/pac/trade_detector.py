"""Trade-mention detector for chatdump messages.

Cascade:
- HIGH:   explicit BUY/SELL/LONG/SHORT/KUPNO/SPRZEDAŻ/WSZEDŁEM keyword
          + symbol + at least one price-like number.
- MEDIUM: '#PAC #<SYMBOL>' hashtag pair + at least one price-like number.
- LOW:    symbol mention + at least one attachment (chart shared).
- None:   otherwise.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

# Recognised tradable symbols. Extend as Phase 0 reveals more (see catalog output).
SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD",
    "EURJPY", "EURGBP", "GBPJPY",
    "XAUUSD", "XAGUSD", "GOLD", "SILVER",
    "USOIL", "WTIUSD", "WTI.fs", "BRENT",
    "US500", "US30", "USTECH", "NAS100", "GER40", "DAX",
    "BTCUSD", "ETHUSD", "SOLUSD",
    "ES", "NQ", "YM", "GC", "CL",
]

# Canonicalize alias symbols to their CFD-style counterparts so that downstream
# catalog rows reference one symbol per instrument. Verified against the chatdump:
# 'GOLD' and 'XAUUSD' refer to the same gold market; 'CL' and 'USOIL' to crude.
_SYMBOL_ALIASES = {
    "GOLD": "XAUUSD",
    "CL":   "USOIL",
}


def _canonicalize(symbol: str) -> str:
    """Return the canonical form of a recognised symbol (alias-mapped)."""
    return _SYMBOL_ALIASES.get(symbol.upper(), symbol.upper())


# Build a regex that matches any symbol as a whole word
_SYMBOL_RE = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in SYMBOLS) + r")\b",
    re.IGNORECASE,
)

_BUY_RE = re.compile(
    r"\b(BUY|LONG|KUPNO|KUPUJE|WSZEDŁEM\s+(?:LONG|BUY|NA)?)\b",
    re.IGNORECASE,
)
_SELL_RE = re.compile(
    r"\b(SELL|SHORT|SPRZEDAŻ|SPRZEDAJE)\b",
    re.IGNORECASE,
)

# Generic price-like number: optional 1-6 digit integer + decimal point + 1-6 decimal digits
# Also bare integers >= 1000 (indices, gold) and 3-digit integers (oil).
_PRICE_RE = re.compile(r"(?<![A-Za-z])(\d{1,6}(?:[.,]\d{1,6})?)")

# SL / stop tokens followed by a price.
_SL_RE = re.compile(
    r"\b(?:SL|S\.L\.|STOP|STOPLOSS|STOP\s*LOSS|STOPER|STR)[\s:=]+(\d{1,6}(?:[.,]\d{1,6})?)",
    re.IGNORECASE,
)

# TP / target tokens followed by a price (captures all occurrences).
_TP_RE = re.compile(
    r"\b(?:TP\d?|T\.P\.|TARGET|CEL|TAKEPROFIT|TAKE\s*PROFIT|TGT)[\s:=]+(\d{1,6}(?:[.,]\d{1,6})?)",
    re.IGNORECASE,
)

# 'wszedłem' explicit Polish "I entered" — high-signal keyword.
_WSZEDLEM_RE = re.compile(r"\bwszedłem\b", re.IGNORECASE)

# Generic "@ price" used in 'BUY EURUSD @ 1.0850'.
_AT_PRICE_RE = re.compile(r"@\s*(\d{1,6}(?:[.,]\d{1,6})?)")

# #PAC #SYMBOL hashtag pair anywhere in message.
_PAC_HASHTAG = re.compile(r"#\s*PAC", re.IGNORECASE)
_SYMBOL_HASHTAG = re.compile(
    r"#\s*(" + "|".join(re.escape(s) for s in SYMBOLS) + r")\b",
    re.IGNORECASE,
)


class Confidence(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TradeMention:
    symbol: str
    direction: Optional[str]            # "BUY" | "SELL" | None when unclear
    entry: Optional[float]
    sl: Optional[float]
    tps: List[float] = field(default_factory=list)
    confidence: Confidence = Confidence.LOW


def _parse_price(s: str) -> float:
    return float(s.replace(",", "."))


def _first_symbol(text: str) -> Optional[str]:
    m = _SYMBOL_RE.search(text)
    return _canonicalize(m.group(1)) if m else None


def _hashtag_symbol(text: str) -> Optional[str]:
    m = _SYMBOL_HASHTAG.search(text)
    return _canonicalize(m.group(1)) if m else None


def _direction(text: str) -> Optional[str]:
    if _BUY_RE.search(text) or _WSZEDLEM_RE.search(text):
        return "BUY"
    if _SELL_RE.search(text):
        return "SELL"
    return None


def _entry_price(text: str, symbol: str) -> Optional[float]:
    # Prefer "@ price" if present.
    m = _AT_PRICE_RE.search(text)
    if m:
        return _parse_price(m.group(1))
    # Otherwise, take the first price-like number AFTER the symbol token in the text.
    # The `symbol` argument is the canonical form (after _canonicalize); the source
    # text may contain an alias (GOLD, CL). Try the canonical form first, then any
    # alias that maps to it.
    candidates = [symbol] + [alias for alias, canon in _SYMBOL_ALIASES.items() if canon == symbol]
    for candidate in candidates:
        sym_match = re.search(r"\b" + re.escape(candidate) + r"\b", text, re.IGNORECASE)
        if sym_match:
            tail = text[sym_match.end():]
            m = _PRICE_RE.search(tail)
            if m:
                return _parse_price(m.group(1))
    return None


def _sl(text: str) -> Optional[float]:
    m = _SL_RE.search(text)
    return _parse_price(m.group(1)) if m else None


def _tps(text: str) -> List[float]:
    return [_parse_price(m.group(1)) for m in _TP_RE.finditer(text)]


def detect_trade_mention(msg: dict) -> Optional[TradeMention]:
    """Return a TradeMention if `msg` looks like a trade post, else None."""
    content: str = msg.get("content") or ""
    attachments = msg.get("attachments") or []

    symbol = _first_symbol(content)
    hashtag_symbol = _hashtag_symbol(content)
    direction = _direction(content)
    has_explicit_keyword = bool(_BUY_RE.search(content) or _SELL_RE.search(content) or _WSZEDLEM_RE.search(content))
    has_pac_hashtag = bool(_PAC_HASHTAG.search(content))
    prices = _PRICE_RE.findall(content)

    # HIGH: explicit keyword + symbol + at least one price.
    if has_explicit_keyword and symbol and prices:
        return TradeMention(
            symbol=symbol,
            direction=direction,
            entry=_entry_price(content, symbol),
            sl=_sl(content),
            tps=_tps(content),
            confidence=Confidence.HIGH,
        )

    # MEDIUM: '#PAC #<SYMBOL>' + price.
    if has_pac_hashtag and hashtag_symbol and prices:
        return TradeMention(
            symbol=hashtag_symbol,
            direction=direction,
            entry=_entry_price(content, hashtag_symbol),
            sl=_sl(content),
            tps=_tps(content),
            confidence=Confidence.MEDIUM,
        )

    # LOW: any symbol mention + at least one attachment.
    if symbol and attachments:
        return TradeMention(
            symbol=symbol,
            direction=direction,
            entry=None,
            sl=None,
            tps=[],
            confidence=Confidence.LOW,
        )

    return None
