# JJ Simon Strategy — Dead-Simple Rules

Plain-English version. The full/precise version is `STRATEGY_RULES.md`; this is the cheat sheet.
**Honest note:** the trade edge here is *tiny* (JJ himself says ~1–2%). The money comes from the
**prop-firm method** (see `PROPFIRM_ROADMAP.md`), not from this being magic. **We have NOT tested it yet.**

## The whole idea in one line
Price runs **away** from a "fair price," then snaps **back** to it. Trade the run first, then the snap-back.

## What you trade
- **Instrument:** NQ (Nasdaq-100 futures). **Chart:** 1-minute.

## When you trade (New York time) — 4 daily "blocks"
| Block | Starts | Trade until | Notes |
|---|---|---|---|
| New York morning | **9:30 AM** | **11:00 AM** | the main one |
| New York afternoon | **2:00 PM** | ~3:00 PM | |
| Evening reopen | **6:00 PM** | ~7:30 PM | |
| Asia | **8:00 PM** | ~9:30 PM | |
| (News) | **8:30 AM** | — | only on red-folder US news days |
- **Skip 11:00 AM – 1:00 PM** (dead zone). Don't trade outside these blocks.

## The "fair price"
- It's the **opening candle of the block** (the 9:29/session-open candle body). **Draw a flat line at it.**
- Price above the line = expensive (lean short). Below = cheap (lean long).

## How to trade each block (2 steps)
1. **First ~10–15 minutes → CONTINUATION.** Trade in the **direction of the opening move** (away from the line).
2. **After that, rest of the block → REVERSION.** Trade **back toward the line.**

## Entry trigger (same for both steps)
Take the trade when a candle **CLOSES past the recent swing high/low**, **OR** it's a **"decisive" candle**
(big body, the wick *against* your direction is **≤ 20%** of the candle). That's your "go" candle.

## Stop loss / take profit — pick by ATR (1-min ATR, in points)
| ATR (points) | Stop loss | Take profit |
|---|---|---|
| **above 20** | 50 | 75 |
| **7 to 20** | 25 | 38 |
| **below 7** | 16.5 | 25 |
- Always about **1.5× reward vs risk**. **Don't move the stop. No partials. Let it hit TP or SL.**
- **Big-candle switch:** if the "go" candle is **taller than 25 points → use HALF the contracts and 50 / 76.**

## Position size (so every trade risks the same)
- Pick contracts so each trade risks your fixed unit (e.g. ~$1,000): **~3 contracts on a 16.5 stop, 2 on a 25, 1 on a 50.**

## Daily limits
- **Max ~3 trades per block** (a 4th only if it's a perfect setup).
- Stop the morning by **11:00 AM**.
- **No managing trades** — EXCEPT: if a **new block opens while you're in a trade, move the stop to break-even.**

## News (8:30 AM), simple version
- **Expected news** (number came out near forecast) → **fade back** to the price just before the news (8:29 candle). *His best trade.*
- **Shock news** (way off, or a surprise headline/tweet) → **go WITH** the move instead.
- News stop/target = looser, your call.

## Advanced (NOT in this simple version — add later once the basics work)
- Moving the fair-price line mid-block (after a news event, or a big volume push that *stays* at a new level).
- Follow-up / second-attempt trades and second-move continuations.
- Different reward:risk per prop firm; the news-"drift" hold-for-hours trade.
