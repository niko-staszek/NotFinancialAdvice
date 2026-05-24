"""Tests for mentor/student identification per the spec's verified rule:
author.name OR author.nickname contains 'allin' (case-insensitive)."""
from __future__ import annotations

import pytest

from hedgehog.proposer.pac.authors import is_mentor


@pytest.mark.parametrize("author,expected", [
    ({"name": "allintraders", "nickname": "ALLin Pablo Gradziuk"}, True),
    ({"name": "pawelkrynicki", "nickname": "ALLin Paweł Krynicki"}, True),
    ({"name": "michalciechan", "nickname": "ALLin Michał Ciechan"}, True),
    ({"name": "ALLin Lukas Serwin", "nickname": "ALLin Lukas Serwin"}, True),
    ({"name": "kiewra82", "nickname": "Karol Kiewra"}, False),
    ({"name": "szymonzxy", "nickname": "SimonxyZ"}, False),
    ({"name": "michalwik", "nickname": "Michał Wik"}, False),
    ({"name": "", "nickname": ""}, False),
    ({"name": "FALLINGstar", "nickname": "Random"}, True),  # "allin" substring match is intentional
    ({"name": None, "nickname": "ALLin Bartosz"}, True),
    ({"name": "ALLINTRADERS", "nickname": None}, True),
])
def test_is_mentor(author: dict, expected: bool) -> None:
    assert is_mentor(author) is expected
