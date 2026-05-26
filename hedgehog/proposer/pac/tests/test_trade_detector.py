"""Tests for trade-mention detection and detail extraction."""
from __future__ import annotations

import pytest

from hedgehog.proposer.pac.trade_detector import (
    Confidence,
    TradeMention,
    detect_trade_mention,
)


def _msg(content: str, attachments: int = 0) -> dict:
    return {
        "id": "x",
        "content": content,
        "attachments": [{"id": "a"} for _ in range(attachments)],
    }


def test_high_confidence_english_buy() -> None:
    m = detect_trade_mention(_msg("BUY EURUSD @ 1.0850 SL 1.0820 TP 1.0920"))
    assert m is not None
    assert m.confidence is Confidence.HIGH
    assert m.symbol == "EURUSD"
    assert m.direction == "BUY"
    assert m.entry == pytest.approx(1.0850)
    assert m.sl == pytest.approx(1.0820)
    assert 1.0920 in m.tps


def test_high_confidence_polish_sell() -> None:
    m = detect_trade_mention(
        _msg("SELL GBPUSD 1.2680, stop 1.2710, target 1.2620")
    )
    assert m is not None
    assert m.symbol == "GBPUSD"
    assert m.direction == "SELL"
    assert m.entry == pytest.approx(1.2680)
    assert m.sl == pytest.approx(1.2710)
    assert 1.2620 in m.tps
    assert m.confidence is Confidence.HIGH


def test_high_confidence_polish_keyword() -> None:
    """'wszedłem' (Polish: 'I entered') + symbol + price is HIGH."""
    m = detect_trade_mention(_msg("wszedłem na XAUUSD 2350.5, SL 2347"))
    assert m is not None
    assert m.symbol == "XAUUSD"
    assert m.confidence is Confidence.HIGH


def test_medium_confidence_hashtag_only() -> None:
    """`#PAC #EURUSD` hashtag + price-like number = MEDIUM."""
    m = detect_trade_mention(_msg("#PAC #EURUSD analiza 1.0850"))
    assert m is not None
    assert m.symbol == "EURUSD"
    assert m.confidence is Confidence.MEDIUM


def test_low_confidence_symbol_plus_attachment() -> None:
    """Symbol mention + attachment but no price/keyword = LOW."""
    m = detect_trade_mention(_msg("ciekawa sytuacja na XAUUSD", attachments=1))
    assert m is not None
    assert m.symbol == "XAUUSD"
    assert m.confidence is Confidence.LOW


def test_no_match() -> None:
    """Plain chat without any signal returns None."""
    assert detect_trade_mention(_msg("Dzień dobry wszystkim, jaki plan na dziś?")) is None


def test_no_match_without_attachment_or_price() -> None:
    """Symbol alone with no number and no attachment doesn't qualify."""
    assert detect_trade_mention(_msg("co myślicie o EURUSD")) is None
