# Fair Value Theory — TradingView Indicator Design Spec

Date: 2026-06-26 · Status: approved (grilled) · Target: Pine v6 overlay indicator,
`tested-strategies/PropFirmMath/pine/FairValueTheory.pine`.
Rules from [`STRATEGY_RULES.md`](../../STRATEGY_RULES.md); timings verified against transcript3 (FX Replay).

## Purpose
On-chart helper for trading JJ Simon's Fair Value Theory on 1-min NQ: marks session blocks,
fair-value lines, trade windows, the decisive/displacement candle, structure breaks, and a
live recommendation table. **Annotator + recommender, not a strategy/backtest.**

## Sessions (ET, `America/New_York`) — verified [v2 L264–270]
| Start | Name | Type | Block len |
|---|---|---|---|
| 03:00 | London open | open | ~90m (toggle) |
| 08:30 | News | news | ~90m (toggle) |
| 09:30 | NY AM open | open | 90m |
| 14:00 | NY PM open | open | 60m (cut 15:00) |
| 18:00 | Reopen | open | ~90m (toggle) |
| 20:00 | Asia open | open | ~90m (toggle) |
Only NY AM + PM are FX-Replay-validated; others are JJ's claim (toggle, default on).

## Fair value (pt 5)
- Each block: capture the **open price of the first bar at/after the session start**; draw a
  horizontal line from that bar to block end.
- **09:30 and 14:00** lines styled + labeled "Fair Value" (the real FV anchors); others labeled by name.

## Windows & tints (pt 2) — verified, all cutoffs are TOGGLE INPUTS (FX Replay in-sample opts)
- **Continuation window** = open + `skipFirstMin`(3) … open + `contLen`(15) → AM **09:33–09:45**. One tint.
- **Mean-reversion window**: AM open…+`mrAMlen`(30) = **09:30–10:00**; PM open…+`mrPMlen`(60) = **14:00–15:00**. Second tint.
- (PM continuation 3-min skip optional — "didn't matter" [L654–58].)

## Pivots & structure break (pt 3)
- `ta.pivothigh(left,right)` / `ta.pivotlow(left,right)`, inputs **left=5, right=1**.
- Track last confirmed pivot-high price `pH`, pivot-low price `pL`.
- **Break = candle CLOSE past the pivot** (FX Replay rule): up-break `close>pH`, down-break `close<pL`.
- **BOS vs MSB from direction relative to FV:** break **away from FV = BOS** (continuation), break
  **toward FV = MSB** (reversal). Deterministic; no trend-detection needed.

## Decisive / displacement candle (pt 4) + body paint (pt 6)
- `dir = sign(close-open)`; `range = high-low` (guard >0).
- `counter_wick` = wick against the close: bullish → `open-low`; bearish → `high-open`.
- **Decisive ⇔ `counter_wick/range ≤ counterWickPct`** (input, default 20%).
- Optional **size gate** (default OFF): `range ≥ sizeMult · sma(high-low, sizeLookback)[1]`, `sizeMult∈[1.2,1.5]`.
- **White body** = decisive. **Gold body** = decisive **AND same-candle break (BOS or MSB)** (FX Replay
  "break + decisive on same candle" A+ combo). Gold overrides white. Painted via `plotcandle` (body only).

## Recommendation table (pt 4) — top-right
Rows: ATR(14) value (pts) · Bucket **LOW<7 / MID 7–20 / HIGH>20** + implied SL/TP (16.5/24.75 · 25/37.5 · 50/75) ·
Decisive ✓/✗ · BOS ✓/✗ · MSB ✓/✗ · **Recommended** (from the table below).

| Window | Price vs FV | Break needed | → Recommend |
|---|---|---|---|
| Continuation (9:33–9:45) | above FV | up (BOS) | Continuation BUY |
| Continuation | below FV | down (BOS) | Continuation SELL |
| Mean-rev (AM/PM win) | above FV | down toward FV (MSB) | Reversion SELL |
| Mean-rev | below FV | up toward FV (MSB) | Reversion BUY |
| else | — | — | None |
Recommendation requires decisive too (i.e., a gold candle in the right window/direction).

## Inputs (summary)
pivot left/right (5/1) · counterWickPct (20) · useSizeGate (off)/sizeMult(1.2)/sizeLookback(5) ·
per-session on/off · skipFirstMin(3)/contLen(15)/mrAMlen(30)/mrPMlen(60) + cutoff toggles ·
atrLen(14) · timezone(America/New_York) · colors/tints.

## Out of scope (v1)
- Thick S/R zone **boxes** (v1 = pivot levels/lines; boxes later if wanted).
- Alerts, multi-symbol, the size-gate edge test (that's the Python backtest, not the indicator).
- Non-NY session validation (timing unproven — marked but flagged).

## Gotchas
- Pivot confirms `right` bars late → break/gold flag ~1 bar after the actual bar; acceptable at right=1.
- `plotcandle` overlays bodies on native candles; set `color=na` on non-special bars.
- All session math via `hour(time,tz)*60+minute(time,tz)` minute-of-day; handle the daily open-bar capture.
