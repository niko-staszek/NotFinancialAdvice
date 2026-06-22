# ScalperProReconEA — MT5 auto-trader (SPZ reconstruction)

Self-contained MQL5 Expert Advisor that runs **our reconstruction** of "Scalper Pro v4.1
[ZynAlgo]" natively in MT5 — no TradingView, no bridge, no cron. Computes EMA/ADX/RSI/ATR +
regime + score itself and trades on bar close.

## ⚠️ Read first
- **This is the reconstruction, not the original.** Measured ~PF 1.5–2 **gross of costs**,
  OOS unvalidated, partly trend-exposure (see `SPZ/NOTES.md`). NOT the original's claimed PF 6.
- **It has NOT been compiled or tested by the author of this file.** Compile in MetaEditor,
  run the Strategy Tester, then **forward-test on a demo** and confirm a real net-of-cost edge
  **before any real capital**.
- Live trading is **blocked on REAL accounts** unless you set `AllowLiveTrading=true`. Prop
  *challenge* accounts are usually DEMO-mode and will trade with the default (false).

## Install
1. Copy `ScalperProReconEA.mq5` to `<MT5 data folder>/MQL5/Experts/`.
2. Open MetaEditor → compile (F7). Fix any broker-specific issues.
3. Enable **Algo Trading** in the terminal.

## Attach (recommended combos)
One instance per symbol, defaults are Intraday 13/34:

| Symbol | Timeframe | Style (EMAs) | Risk/trade | Notes |
|---|---|---|---|---|
| XAUUSD | **H1** | Intraday 13/34 | 0.625% | |
| BTCUSD | **H4** | Intraday 13/34 | 0.625% | |

`RiskPctPerTrade=0.625` is the **combined** prop-safe size (XAU+BTC together, 5%-daily/10%-max,
2× buffer). Running only ONE symbol → it's conservative; you may raise it (gold-solo ≈0.56%,
BTC-solo ≈1.25% — but re-verify DD first).

HTF auto-derives (`HtfTimeframe=PERIOD_CURRENT`): H1→H4, H4→D1.

## How it trades (matches the v3.2 recon)
- Regime = slope of slow EMA over `SlopeLen` bars / ATR; `|slope|<FlatBand` ⇒ SIDEWAY ⇒ **no trade**.
- Score = votes(Market, HTF, RSI)×25 + (ADX≥thr)×25, capped 100; enter when `≥MinScore`,
  in session, past `CooldownBars`, regime aligned.
- SL = `SlAtrMult`×ATR (=1R) and TP = `TpRR`×R (=+3R) placed **broker-side** (auto-exit).
- Reverses on a cooled opposite signal. One position per symbol (netting accounts).
- Lots sized dynamically: `risk$ / (SL_price_distance / tickSize × tickValue)`.

## Verify before trusting (do not skip)
1. **Strategy Tester**, each symbol, "Every tick based on real ticks", with realistic
   spread/commission — confirm it trades and the numbers roughly match the Python recon
   (PF/DD/trade count). Mismatch ⇒ a porting bug.
2. **Demo forward-test** several weeks. Watch concurrent floating DD when both symbols are open
   (they overlap ~50% of the time).
3. Only then, small live with `AllowLiveTrading=true`.

## Known limitations / caveats
- Netting assumed (one position per symbol). Hedging accounts: add a per-magic position loop.
- HTF EMA read at shift 1 (last closed bar) — minor difference vs Pine `request.security`.
- The recon's score is coarse (steps of 25); `MinScore` 60 and 75 behave alike.
- Broker min-stop-distance not explicitly checked (2.8×ATR is normally well beyond it).
