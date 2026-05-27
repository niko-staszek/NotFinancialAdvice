"""MMD (Magic Moving Averages) cloud computation — Pine→Python port.

Source: NFA/MMD/pine/mmd_clouds.pine.

Three main clouds (per MMD_CLOUDS.md "Cloud Table"):
    Orange — period 48  → fast / consolidation detection
    Blue   — period 288 → medium trend
    Green  — period 1440 → slow / primary trend direction

A cloud band is `[EMA(period), SMA(period)]`. Its midpoint is the average
of EMA and SMA, used for stacking comparison.

Pine source uses `ta.sma` and `ta.ema` on `close` exactly as ported here.
No deviations from plan's algorithm: band = [SMA, EMA], midpoint = (SMA+EMA)/2.

Alignment classification per strategy_ea.md §3.2:
    confirmed — clouds stacked in same direction as sentiment
    weakened  — partial agreement
    vetoed    — clouds stacked fully opposite to sentiment
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd


@dataclass
class CloudValues:
    orange_ema: pd.Series
    orange_sma: pd.Series
    orange_mid: pd.Series
    blue_ema: pd.Series
    blue_sma: pd.Series
    blue_mid: pd.Series
    green_ema: pd.Series
    green_sma: pd.Series
    green_mid: pd.Series


def compute_clouds(bars: pd.DataFrame) -> CloudValues:
    """Compute the three main MMD clouds on the given bars."""
    close = bars["close"]
    orange_ema = close.ewm(span=48, adjust=False).mean()
    orange_sma = close.rolling(window=48).mean()
    blue_ema = close.ewm(span=288, adjust=False).mean()
    blue_sma = close.rolling(window=288).mean()
    green_ema = close.ewm(span=1440, adjust=False).mean()
    green_sma = close.rolling(window=1440).mean()
    return CloudValues(
        orange_ema=orange_ema,
        orange_sma=orange_sma,
        orange_mid=(orange_ema + orange_sma) / 2,
        blue_ema=blue_ema,
        blue_sma=blue_sma,
        blue_mid=(blue_ema + blue_sma) / 2,
        green_ema=green_ema,
        green_sma=green_sma,
        green_mid=(green_ema + green_sma) / 2,
    )


def classify_alignment(
    orange_mid: float,
    blue_mid: float,
    green_mid: float,
    sentiment: Literal["bull", "bear", "transitional"],
) -> Literal["confirmed", "weakened", "vetoed"]:
    """Return cloud-alignment classification given the three midpoints + sentiment.

    Bull cloud stacking: orange > blue > green (fast above slow).
    Bear cloud stacking: green > blue > orange.
    """
    full_bull = orange_mid > blue_mid > green_mid
    full_bear = green_mid > blue_mid > orange_mid

    if sentiment == "bull":
        if full_bull:
            return "confirmed"
        if full_bear:
            return "vetoed"
        return "weakened"
    if sentiment == "bear":
        if full_bear:
            return "confirmed"
        if full_bull:
            return "vetoed"
        return "weakened"
    # Transitional sentiment never reaches §3.5 composite — return weakened as a safe default.
    return "weakened"
