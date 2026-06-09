from __future__ import annotations

from CBS.cbs import config


def test_instruments_are_the_eleven_psnd_symbols() -> None:
    assert set(config.INSTRUMENTS) == {
        "EURUSD", "GBPUSD", "USDCAD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD",
        "XAUUSD", "XTIUSD", "BTCUSD", "ETHUSD",
    }


def test_every_instrument_has_pip_size_and_base_tolerance() -> None:
    for sym in config.INSTRUMENTS:
        assert sym in config.PIP_SIZE
        assert sym in config.BASE_TOLERANCE_PIPS


def test_jpy_pip_size_differs_from_eur() -> None:
    assert config.PIP_SIZE["USDJPY"] == 0.01
    assert config.PIP_SIZE["EURUSD"] == 0.0001


def test_grid_dimensions() -> None:
    assert config.ANCHORS == tuple(range(24))
    assert config.BLOCKS == tuple(range(1, 25))
    assert config.TOLERANCE_MULTIPLIERS == (1, 2, 3, 4)


def test_clock_cap_is_48h() -> None:
    assert config.CLOCK_CAP_HOURS == 48
