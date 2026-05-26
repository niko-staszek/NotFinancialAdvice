"""PAC component keyword classifier.

For each message we tag which PAC components it references. Keyword lists
are Polish + English to handle code-switched messages. Matching is whole-word
where possible (\\b boundaries), case-insensitive.
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Set


class Component(Enum):
    SIGNAL_CANDLE = "signal_candle"
    GAP_CANDLE = "gap_candle"
    MEASURED_MOVE = "measured_move"
    SPIKE_FLAG = "spike_flag"
    SPIKE_CHANNEL = "spike_channel"
    TRAP_SETUP = "trap_setup"
    FAIL_SETUP = "fail_setup"
    RANGE_TRAP = "range_trap"
    RANGE_FAIL = "range_fail"
    SESSION_BOX = "session_box"
    D1_OHLC_BIAS = "d1_ohlc_bias"
    BATTLE_ZONE = "battle_zone"
    TRENDLINE = "trendline"
    EMA_SMA = "ema_sma"
    FIBONACCI = "fibonacci"
    ELLIOTT = "elliott"
    HIDDEN_CHANNEL = "hidden_channel"
    DOUBLE_TOP_BOTTOM = "double_top_bottom"
    REVERSAL_LINE = "reversal_line"
    MMD_CLOUDS = "mmd_clouds"


# Keyword lists. Each entry is regex-compiled with IGNORECASE.
# Use \\b boundaries where the term is a word; allow Polish chars where needed.
_KEYWORDS: dict[Component, list[str]] = {
    Component.SIGNAL_CANDLE: [
        r"\bsignal\s+candle\b", r"\bsignalk[ai]\b", r"\bsygnałówk[ai]\b",
        r"\bpin\s*bar\b", r"\bhammer\b",
    ],
    Component.GAP_CANDLE: [
        r"\bgap\s+candle\b", r"\bgapówk[ai]\b", r"\bmarubozu\b",
    ],
    Component.MEASURED_MOVE: [
        r"\bmeasured\s+move\b", r"\bMM\b", r"\bAB\s*=\s*CD\b",
        r"\bmiar(?:k[aę]|a)\b", r"\bmiara\s+ruchu\b", r"\bprojekcja\b",
    ],
    Component.SPIKE_FLAG: [
        r"\bspike\s*&?\s*flag\b", r"\bspike\s+flag\b", r"\bflag[aą]\b",
    ],
    Component.SPIKE_CHANNEL: [
        r"\bspike\s*&?\s*channel\b", r"\bkanał\b",
    ],
    Component.TRAP_SETUP: [
        r"\btrap\b", r"\bpułapk[ai]\b", r"\bdwóch\s+prób\b", r"\btwo[-\s]*try\b",
        r"\bto[-\s]*try\b",
    ],
    Component.FAIL_SETUP: [
        r"\bfail\b", r"\bfailówk[ai]\b", r"\bgłębok(?:ej?|a)\s+korekt[aiey]\b",
    ],
    Component.RANGE_TRAP: [
        r"\brange[\s-]+(?:\d[\s-]*)?(?:try\s+)?trap\b",
    ],
    Component.RANGE_FAIL: [
        r"\brange[\s-]+(?:\d[\s-]*)?(?:try\s+)?fail\b",
    ],
    Component.SESSION_BOX: [
        r"\bsession\s+box\b", r"\basia\s+box\b", r"\blondon\s+box\b",
        r"\bsesj[aą]\b", r"\basia\b", r"\blondyn\b", r"\bNY\b",
    ],
    Component.D1_OHLC_BIAS: [
        r"\bOHLC\b", r"\bD1\b", r"\bpromo\s+zone\b", r"\bstref[aę]\s+promocyj",
        r"\bdaily\s+candle\b",
    ],
    Component.BATTLE_ZONE: [
        r"\bbattle\s+zone\b", r"\bBZ\b", r"\bstref[aę]\s+walki\b", r"\bcongestion\b",
    ],
    Component.TRENDLINE: [
        r"\btrend\s*line\b", r"\bTL\b", r"\blini[aę]\s+trendu\b",
    ],
    Component.EMA_SMA: [
        r"\bEMA\b", r"\bSMA\b", r"\bEMA\s*21\b", r"\bSMA\s*61\b",
        r"\bśredni[ae]\b",
    ],
    Component.FIBONACCI: [
        r"\bfibo\b", r"\bfib\b", r"\bretracement\b", r"\bextension\b",
        r"\bexpansion\b", r"\b(?:0\.|0,)?(?:382|618|786)\b", r"\b138\.?2\b",
        r"\b161\.?8\b",
    ],
    Component.ELLIOTT: [
        r"\belliott\b", r"\bwave\b", r"\bfal[aęi]\b", r"\bimpuls\b",
    ],
    Component.HIDDEN_CHANNEL: [
        r"\bhidden\s+channel\b", r"\bukryty\s+kanał\b", r"\brotation\s+channel\b",
    ],
    Component.DOUBLE_TOP_BOTTOM: [
        r"\bdouble\s+top\b", r"\bdouble\s+bottom\b", r"\bpodwójn[ey]\s+(?:dno|szczyt)\b",
        r"\bDT\b", r"\bDB\b",
    ],
    Component.REVERSAL_LINE: [
        r"\breversal\s+line\b", r"\bRL\b", r"\bodwrócenie\b",
    ],
    Component.MMD_CLOUDS: [
        r"\bMMD\b", r"\bmagic\s+clouds\b", r"\bmagiczne\s+średnie\b",
        r"\bchmur[ayę]\b",
    ],
}

_COMPILED: dict[Component, list[re.Pattern[str]]] = {
    comp: [re.compile(p, re.IGNORECASE) for p in patterns]
    for comp, patterns in _KEYWORDS.items()
}


def classify_components(text: str) -> Set[Component]:
    """Return the set of PAC components referenced in `text`.

    Polish and English mentions are both recognized. Empty input yields {}.
    """
    if not text:
        return set()
    hit: Set[Component] = set()
    for comp, patterns in _COMPILED.items():
        for p in patterns:
            if p.search(text):
                hit.add(comp)
                break
    return hit


SETUP_PRIORITY: list[Component] = [
    Component.TRAP_SETUP,
    Component.FAIL_SETUP,
    Component.RANGE_TRAP,
    Component.RANGE_FAIL,
    Component.SPIKE_FLAG,
    Component.SPIKE_CHANNEL,
    Component.DOUBLE_TOP_BOTTOM,
    Component.MEASURED_MOVE,
]


def setup_for(text: str) -> str:
    """Classify `text` into a setup name by SETUP_PRIORITY, else 'unclassified'."""
    comps = classify_components(text or "")
    for c in SETUP_PRIORITY:
        if c in comps:
            return c.value
    return "unclassified"
