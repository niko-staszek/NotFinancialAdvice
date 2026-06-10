"""CBS configuration: instruments, pip sizes, tolerance ladder, window grid, costs.

All values are PSND-derived. Tolerances are expressed in *pips* and converted to
price via PIP_SIZE. The tolerance ladder multiplies BASE_TOLERANCE_PIPS so a too-
tight baseline does not understate completion (design §2.3).
"""
from __future__ import annotations

INSTRUMENTS: tuple[str, ...] = (
    "EURUSD", "GBPUSD", "USDCAD", "USDJPY", "USDCHF", "AUDUSD", "NZDUSD",
    "XAUUSD", "XTIUSD", "BTCUSD", "ETHUSD",
)

# Price increment of one "pip" as PSND counts it.
PIP_SIZE: dict[str, float] = {
    "EURUSD": 0.0001, "GBPUSD": 0.0001, "USDCAD": 0.0001, "USDCHF": 0.0001,
    "AUDUSD": 0.0001, "NZDUSD": 0.0001,
    "USDJPY": 0.01,
    "XAUUSD": 0.1,    # PSND tolerance "15 pips" on gold = 1.5 in price; pip=0.1
    "XTIUSD": 0.01,
    "BTCUSD": 1.0,    # crypto tolerance expressed directly in $ below
    "ETHUSD": 1.0,
}

# PSND baseline settle tolerance, in pips (×PIP_SIZE = price). Crypto in $ via pip=1.0.
BASE_TOLERANCE_PIPS: dict[str, float] = {
    "EURUSD": 5, "GBPUSD": 5, "USDCAD": 5, "USDCHF": 5, "AUDUSD": 5, "NZDUSD": 5,
    "USDJPY": 5,
    "XAUUSD": 15, "XTIUSD": 15,
    "BTCUSD": 10, "ETHUSD": 5,
}

ANCHORS: tuple[int, ...] = tuple(range(24))          # 0..23
BLOCKS: tuple[int, ...] = tuple(range(1, 25))        # 1..24 hours
TOLERANCE_MULTIPLIERS: tuple[int, ...] = (1, 2, 3, 4)

RR_LIST: tuple[float, ...] = (1.0, 2.0, 3.0)   # reward:risk levels tested by Engine B's R:R grid

CLOCK_CAP_HOURS: int = 72
ATR_PERIOD_M5: int = 14
ATR_SL_K: float = 1.5            # fallback SL = entry ± k*ATR when no structural level
MIN_RISK_ATR_K: float = 0.5      # floor on stop distance (× ATR) so planned R can't explode
ENTRY_LOOKBACK_HOURS: int = 12   # bars before window_open a detector may read


def tolerance_price(symbol: str, mult: int) -> float:
    """Settle tolerance in price units for `symbol` at ladder multiplier `mult`."""
    return BASE_TOLERANCE_PIPS[symbol] * PIP_SIZE[symbol] * mult
