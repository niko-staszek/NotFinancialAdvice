# MMD — Reference Links

## Source Material

- [Magiczne Średnie MMD — mql.pl](https://mql.pl/handlowe/Magiczne_Srednie_MMD.php) — original Polish write-up by Mariusz Maciej Drozdowski

## TradingView Indicator

**MMD System — Magic Moving Averages** (custom Pine Script v6, built to match this repo's docs)

- Script ID: `USER;1cbb49ef6cf64a69bedd105ee3f906d6`
- Published: https://www.tradingview.com/script/m36TYMlk-MMD-System-Magic-Moving-Averages/

Features implemented:
- All 7 clouds: 12 (Red/H1), 48 (Orange/H4), 144 (Light Blue/H12), 288 (Blue/D1), 720 (Light Green/D2.5), 1440 (Green/W1), 3456 (Purple/~MN)
- Delayed cloud: SMA/EMA(12) shifted back 144 bars
- Ribbons: Blue(288) displaced by ATR-based or fixed-% multiplier (auto-scales with volatility)
- Diamond detection: common diamond pattern with zone lines (top/bot/50% midpoint)
- MTF support: view H1/H4 cloud structure on M5/M15
- Lookback gate: renders last N bars only (default 1000) for performance
