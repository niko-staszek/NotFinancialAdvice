"""§3 Direction Filter — five sub-filters composing the direction gate.

Each function corresponds to a section of strategy_ea.md:

    §3.1  sentiment()             — EMA21 / SMA61 price-position classification
    §3.2  mmd_alignment()         — MMD cloud stacking alignment (delegates to mmd.classify_alignment)
    §3.3  d1_promo_zone()         — Previous D1 bar body/wick zone classification
    §3.4  session_box_position()  — Session high/low box breakout position
    §3.5  composite_direction()   — Composite gate combining all four sub-filters

All functions are pure / stateless; session state (e.g. first-touch tracking for §3.3)
is deferred to v2.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Literal

import pandas as pd

from hedgehog.proposer.pac.config import Config
from hedgehog.proposer.pac.helpers.timeutil import is_in_session
from hedgehog.proposer.pac.mmd import CloudValues, classify_alignment


# ---------------------------------------------------------------------------
# §3.1 Sentiment — EMA21 / SMA61
# ---------------------------------------------------------------------------

def sentiment(
    bars: pd.DataFrame,
    cfg: Config,
    bar_idx: int,
) -> Literal["bull", "bear", "transitional"]:
    """Classify trend sentiment at *bar_idx* using EMA(cfg.ema_period) and SMA(cfg.sma_period).

    Returns:
        'bull'         — close > EMA AND close > SMA
        'bear'         — close < EMA AND close < SMA
        'transitional' — price is between the two MAs, or MAs are NaN (insufficient data)
    """
    close_series = bars["close"]
    ema = close_series.ewm(span=cfg.ema_period, adjust=False).mean()
    sma = close_series.rolling(window=cfg.sma_period).mean()

    close_val: float = close_series.iloc[bar_idx]
    ema_val: float = ema.iloc[bar_idx]
    sma_val: float = sma.iloc[bar_idx]

    # Insufficient data → NaN MA values
    if math.isnan(ema_val) or math.isnan(sma_val):
        return "transitional"

    if close_val > ema_val and close_val > sma_val:
        return "bull"
    if close_val < ema_val and close_val < sma_val:
        return "bear"
    return "transitional"


# ---------------------------------------------------------------------------
# §3.2 MMD Alignment
# ---------------------------------------------------------------------------

def mmd_alignment(
    clouds: CloudValues,
    bar_idx: int,
    sentiment_value: Literal["bull", "bear", "transitional"],
    cfg: Config,
) -> Literal["confirmed", "weakened", "vetoed"]:
    """Classify MMD cloud stacking alignment at *bar_idx* relative to *sentiment_value*.

    Delegates to mmd.classify_alignment() after reading the three midpoint values.
    Returns 'weakened' if any midpoint is NaN (insufficient warmup data).

    cfg is accepted for API consistency (unused in v1 — no MMD-specific thresholds yet).
    """
    orange_mid: float = clouds.orange_mid.iloc[bar_idx]
    blue_mid: float = clouds.blue_mid.iloc[bar_idx]
    green_mid: float = clouds.green_mid.iloc[bar_idx]

    if math.isnan(orange_mid) or math.isnan(blue_mid) or math.isnan(green_mid):
        return "weakened"

    return classify_alignment(orange_mid, blue_mid, green_mid, sentiment_value)


# ---------------------------------------------------------------------------
# §3.3 D1 Promo Zone
# ---------------------------------------------------------------------------

def d1_promo_zone(
    d1_bars: pd.DataFrame,
    current_utc: datetime,
    current_price: float,
) -> Literal["bull_promo", "bear_promo", "neutral", "first_touch_bull_promo", "first_touch_bear_promo"]:
    """Classify current_price relative to the previous D1 bar's body/wick zones.

    Returns:
        'bull_promo'  — price is in the buyers' promotional zone (lower wick of prev D1)
        'bear_promo'  — price is in the sellers' promotional zone (upper wick of prev D1)
        'neutral'     — price is inside the body, or no prior D1 bar exists

    v2 deferral: 'first_touch_bull_promo' / 'first_touch_bear_promo' require per-day
    state tracking (whether today has already seen a touch of the zone). This stateless
    v1 implementation never returns those variants — the Literal is included so callers
    and composite_direction can handle them transparently once v2 is implemented.

    Algorithm (§3.3):
        Bearish D1 (close < open):
            Zone above body (Open..High)  → bear_promo  (sellers defended price)
            Zone below body (Low..Close)  → bull_promo  (buyers' demand area)
        Bullish D1 (close > open):
            Zone below body (Low..Open)   → bull_promo  (buyers' launch pad)
            Zone above body (Close..High) → bear_promo  (resistance / distribution)
        Neutral D1 (doji):
            No clear zone → neutral
    """
    if d1_bars.empty:
        return "neutral"

    # Ensure time_utc is datetime-comparable (may be tz-aware or naive).
    current_date = current_utc.date()

    # Filter: keep only bars whose date is strictly before today.
    # Support both tz-aware and tz-naive time_utc columns.
    time_col = d1_bars["time_utc"]
    if hasattr(time_col.iloc[0], "tzinfo") and time_col.iloc[0].tzinfo is not None:
        bar_dates = time_col.dt.date
    else:
        bar_dates = time_col.dt.date

    prior = d1_bars[bar_dates < current_date]
    if prior.empty:
        return "neutral"

    prev = prior.loc[prior["time_utc"].idxmax()]
    prev_open: float = float(prev["open"])
    prev_high: float = float(prev["high"])
    prev_low: float = float(prev["low"])
    prev_close: float = float(prev["close"])

    if prev_close < prev_open:
        # Bearish D1
        body_top = prev_open
        body_bot = prev_close
        if current_price > body_top:
            # Above body, in upper wick: sellers' promo
            return "bear_promo"
        if current_price < body_bot:
            # Below body, in lower wick: buyers' promo
            return "bull_promo"
        # Inside body
        return "neutral"

    if prev_close > prev_open:
        # Bullish D1
        body_bot = prev_open
        body_top = prev_close
        if current_price < body_bot:
            # Below body, in lower wick: buyers' launch pad
            return "bull_promo"
        if current_price > body_top:
            # Above body, in upper wick: distribution / resistance
            return "bear_promo"
        # Inside body
        return "neutral"

    # Doji — no clear zone
    return "neutral"


# ---------------------------------------------------------------------------
# §3.4 Session Box Position
# ---------------------------------------------------------------------------

def session_box_position(
    bars: pd.DataFrame,
    bar_idx: int,
    session: Literal["asia", "london", "america"],
    cfg: Config,
    atr_value: float,
) -> Literal["above", "inside", "below"]:
    """Classify current bar's close relative to today's session high/low box.

    Algorithm (§3.4):
        1. Find all bars up to (but NOT including) bar_idx whose time_utc falls
           within *session* on the same calendar date as bars[bar_idx].
        2. Session high = max of those bars' highs; session low = min of lows.
        3. If box range < 0.5 × atr_value → return 'inside' (narrow-box filter).
        4. If current close > session_high → 'above'.
           If current close < session_low  → 'below'.
           Otherwise                        → 'inside'.

    Returns 'inside' if no prior session bars exist (bar_idx is exactly at session open).

    cfg is accepted for API consistency (unused in v1).
    """
    current_bar_time: datetime = bars["time_utc"].iloc[bar_idx]
    current_date = current_bar_time.date() if hasattr(current_bar_time, "date") else current_bar_time.to_pydatetime().date()

    # Collect bars strictly before bar_idx that belong to the same session on the same date.
    prior_bars = bars.iloc[:bar_idx]
    if prior_bars.empty:
        return "inside"

    # Filter to same day AND same session
    def _in_session_today(row_time: pd.Timestamp) -> bool:
        t = row_time.to_pydatetime()
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
        return t.date() == current_date and is_in_session(t, session)

    mask = prior_bars["time_utc"].apply(_in_session_today)
    session_bars = prior_bars[mask]

    if session_bars.empty:
        return "inside"

    session_high: float = float(session_bars["high"].max())
    session_low: float = float(session_bars["low"].min())
    box_range = session_high - session_low

    # Narrow-box filter
    if box_range < 0.5 * atr_value:
        return "inside"

    current_close: float = float(bars["close"].iloc[bar_idx])

    if current_close > session_high:
        return "above"
    if current_close < session_low:
        return "below"
    return "inside"


# ---------------------------------------------------------------------------
# §3.5 Composite Direction
# ---------------------------------------------------------------------------

def composite_direction(
    sentiment_value: Literal["bull", "bear", "transitional"],
    mmd_value: Literal["confirmed", "weakened", "vetoed"],
    d1_value: Literal["bull_promo", "bear_promo", "neutral", "first_touch_bull_promo", "first_touch_bear_promo"],
    box_value: Literal["above", "inside", "below"],
    cfg: Config,
) -> Literal["bull", "bear", "neutral"]:
    """Gate all four sub-filters into a single direction decision.

    Strict mode (cfg.direction_strict=True, default):
        bull iff:
            sentiment == 'bull'
            AND mmd not vetoed  (or 'confirmed' only if cfg.mmd_strict=True)
            AND d1 in bull-permissive set
            AND box != 'inside'
        bear iff: mirror
        neutral otherwise

    Loose mode (cfg.direction_strict=False):
        Only sentiment is required; all other filters become advisory.
        Returns 'bull' / 'bear' directly from sentiment_value.
        Returns 'neutral' only if sentiment == 'transitional'.

    MMD strict (cfg.mmd_strict=True):
        In addition to the base strict rule, requires mmd_value == 'confirmed'
        (not just non-vetoed).
    """
    if not cfg.direction_strict:
        # Loose mode — only sentiment matters
        if sentiment_value == "bull":
            return "bull"
        if sentiment_value == "bear":
            return "bear"
        return "neutral"

    # Strict mode
    _bull_d1 = {"bull_promo", "first_touch_bull_promo", "neutral"}
    _bear_d1 = {"bear_promo", "first_touch_bear_promo", "neutral"}

    def _mmd_ok() -> bool:
        if cfg.mmd_strict:
            return mmd_value == "confirmed"
        return mmd_value != "vetoed"

    if (
        sentiment_value == "bull"
        and _mmd_ok()
        and d1_value in _bull_d1
        and box_value != "inside"
    ):
        return "bull"

    if (
        sentiment_value == "bear"
        and _mmd_ok()
        and d1_value in _bear_d1
        and box_value != "inside"
    ):
        return "bear"

    return "neutral"
