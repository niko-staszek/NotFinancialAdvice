# CBS — "Can't Be Simpler" Strategy Reference

This is my (Claude's) understanding of how the strategy works.
Niko corrects this file when something is wrong — this is the single source of truth for the codebase.

---

## DATA TIMEZONE

All data files are in **UTC (GMT+0)**. Verified from forex market hours:
- Forex week opens **Sunday 22:00 UTC** (= Monday 00:00 GMT+2 broker)
- Forex week closes **Friday 21:00 UTC** (= Friday 23:00 GMT+2 broker)

### Broker timezone conversion

| UTC (our data) | GMT+2 (MT broker winter) | GMT+3 (MT broker DST) | EST |
|---|---|---|---|
| 00:00 | 02:00 | 03:00 | 19:00 prev day |
| 07:00 | 09:00 | 10:00 | 02:00 |
| 08:00 | 10:00 | 11:00 | 03:00 |
| 12:00 | 14:00 | 15:00 | 07:00 |
| 16:00 | 18:00 | 19:00 | 11:00 |
| 21:00 | 23:00 | 00:00 next | 16:00 |

### Key sessions in UTC
- **Asian:** 00:00–07:00 UTC (Tokyo 09:00-16:00 JST)
- **London:** 07:00–16:00 UTC (London 07:00-16:00 GMT winter)
- **New York:** 12:00–21:00 UTC (NY 07:00-16:00 EST winter)
- **Overlap:** 12:00–16:00 UTC (London + NY)

**Important:** When applying offset targets on a live broker, convert the offset to the broker's server timezone. Our "08:00 UTC offset" = 10:00 on a GMT+2 broker = 11:00 on a GMT+3 (DST) broker.

---

## INSTRUMENTS

### Forex
EURUSD, GBPUSD, USDCAD, USDJPY, USDCHF, AUDUSD, NZDUSD

### CFD
XAUUSD (Gold), XTIUSD (Oil)

### Crypto
BTCUSD, ETHUSD

---

## PIP VALUES

| Instrument | 1 pip = | Notes |
|------------|---------|-------|
| Forex (non-JPY) | 0.0001 | EURUSD, GBPUSD, USDCAD, USDCHF, AUDUSD, NZDUSD |
| USDJPY | 0.01 | |
| XAUUSD | 0.1 | 10 cents per pip |
| XTIUSD | 0.01 | |
| BTCUSD | 1.0 | $1 per pip |
| ETHUSD | 1.0 | $1 per pip |


---

## TIMEFRAMES

- **H1** — day range (primary execution timeframe)
- **H4** — week range (swings, imbalances, trend, channels)
- **D1** — month range
- **M5/M15** — signal candle confirmation after LLR break

---

## INDICATORS

### EMA21
Primary indicator. Used on H1 for COMING entry filter and on H4 for trend determination.

---

## PREVIOUS PERIOD LEVELS

Notation: `P(D/W/M)(O/H/L/C)` = Previous (Day/Week/Month) (Open/High/Low/Close)

We compute OHLC for the previous day, previous week, and previous month, then map them forward.

---

## TARGET CALCULATION (Fibonacci Expansion)

We use **Fibonacci expansion** to project a single target from the previous period's price action.

### Source data
- Open, High, Low of the period (default = Previous Day)

### Expansion formula
```
target = C + (B - A) × 1.0
```
Only level **1.0** is used — one target, no other levels.

### Directions
- **Bullish**: A=Open, B=High, C=Low → `target = Low + (High - Open)`
- **Bearish**: A=Open, B=Low, C=High → `target = High + (Low - Open)`

Both simplify to the same value: **target = High + Low - Open**

This means there is **one target per period**, not multiple. The direction (whether price approaches from above or below) determines if it's a bullish or bearish trade setup.

### Multiple targets per day via different windows
The default period is the Previous Day (00:00–24:00 UTC), giving one target for the whole day. But we can also compute targets from:
**offseted MAIN TARGET** - e.g. instead of 00:00–24:00 we take 01:00-01:00 or even 01:30-01:30, yes minutes count too!
**shorter intraday windows** — e.g., 07:00–13:00 or 22:00–24:00. Each window produces its own O/H/L, and therefore its own single target. Different windows may produce targets with higher settle-on-day ratios than the default full-day window.

### Offset target research findings (from research/08_offset_targets and research/09_offset_backtest)

**08:00 UTC offset is definitively superior to the main 00:00 target across ALL instruments.**

The 08:00 UTC window (= 10:00 GMT+2 broker time) measures the previous "day" from London open to London open, capturing the full London+NY directional move instead of starting from Asian session noise.

| Symbol | Main 00:00 PF | 08:00 UTC PF | 08:00 WR | 08:00 Pips |
|--------|--------------|-------------|----------|-----------|
| EURUSD | 1.70 | 3.23 | 92.7% | +8,133 |
| GBPUSD | 1.90 | 3.32 | 92.2% | +11,289 |
| USDCAD | 2.25 | 2.91 | 92.2% | +7,437 |
| USDJPY | 1.72 | 3.63 | 90.7% | +9,751 |
| USDCHF | 1.56 | 1.92 | 90.1% | +3,842 |
| AUDUSD | 2.56 | 4.18 | 93.4% | +6,997 |
| NZDUSD | 1.80 | 3.97 | 92.9% | +5,902 |
| XAUUSD | 1.59 | 5.21 | 90.3% | +13,928 |
| BTCUSD | 2.21 | 4.35 | 84.0% | +347,584 |
| ETHUSD | 2.74 | 5.38 | 92.0% | +8,884 |

Combined (main + 08:00 offset) gives 50-96% coverage of all trading days, vs 36-81% with main alone. The two targets are different >85% of the time (differ by >3 pips).

### Multi-offset discovery (from research/11_offset_sweep and research/12_multi_offset_backtest)

**ALL offsets from 00:00 to 12:00 UTC are profitable on ALL instruments.** PF increases monotonically from 00:00 to 12:00. Best offsets are 11:00-12:00 UTC (London+NY overlap).

Trading ALL 13 offsets simultaneously (one trade per offset per day):

| Symbol | Trades | Trd/Yr | WR | Pips | PF |
|--------|--------|--------|------|------|------|
| EURUSD | 3,544 | 461 | 89.0% | +47,102 | 2.52 |
| GBPUSD | 6,269 | 816 | 90.3% | +90,720 | 2.95 |
| USDCAD | 9,763 | 1,273 | 91.4% | +90,825 | 2.65 |
| USDJPY | 5,529 | 720 | 89.6% | +104,780 | 3.19 |
| USDCHF | 5,923 | 771 | 88.1% | +49,017 | 2.00 |
| AUDUSD | 6,368 | 829 | 93.6% | +71,051 | 3.72 |
| NZDUSD | 2,799 | 365 | 91.1% | +42,666 | 3.16 |
| XAUUSD | 2,064 | 198 | 87.1% | +155,052 | 3.58 |
| BTCUSD | 17,152 | 1,940 | 82.8% | +3,904,786 | 3.61 |
| ETHUSD | 1,789 | 202 | 89.8% | +98,538 | 4.42 |

**Grand total: 61,200 trades, +4,654,538 pips, avg PF 3.18**

Risk management: with 13 simultaneous offsets, risk per trade = base_risk / 13 (e.g., 0.15% per trade if base is 2%).

### Target settle tolerance (slippage)
How close price must get to a target for it to count as "settled":

| Type | Settle tolerance | + Spread | Total |
|------|-----------------|----------|-------|
| Forex | 5 pips | 0–1.5 | 5 + spread |
| XAUUSD | 15 pips | 9-70 | 24 pips |
| XTIUSD | 15 pips | 5-70 | 20 pips |
| BTCUSD | $10 | 30-120 | $40 |
| ETHUSD | $5 | 5-120 | $10 |

---

## FIBONACCI RETRACEMENT

Created at PDH and PDL (previous day high and low) and we keep it for the all targets of the day, even if we take smaller or shifted targets.

### Levels
- **Internal** (important): 0.382, 0.618
- **External**: -0.382, -0.618, 1.382, 1.618, 2.618

Formula: `level_price = PDL + (PDH - PDL) × level`

Also computed for Previous Week and Previous Month H/L.

---

## SWINGS (on H4)

1. Price moves in one direction for at least 3 candles.
2. An opposite candle starts approximately at the close of the previous candle.
3. We track only a few recent swings (2–4 is typical — roughly day, week, month range).

### Swing High (SH) / Swing Low (SL)
Used for trend determination and as S/R levels (obstacles).

---

## IMBALANCE (on H4 and H1)

1. Three consecutive candles in one direction.
2. The gap between high of candle 1 and low of candle 3 (bullish) or low of candle 1 and high of candle 3 (bearish) = the imbalance box.
3. Price tends to return to fill this zone.
4. **Minimum size: 20 pips** to be considered.

---

## CLUSTERS

Formed when **retracement levels** from different periods (day, week, month) land close together.

### Important: clusters are day-level, not target-level
Clusters are built from **retracement levels** (PD/PW/PM high-low). These are the same for the entire day — they don't change depending on which expansion target you're looking at. A target might land inside an existing cluster (making it a TARGET CLUSTER = stronger level), but the cluster map itself is identical for all targets on that day.

### Common cluster combos
- 61.8% + 38.2% (from different periods)
- 61.8% + 61.8%
- 61.8% + 161.8%
- 38.2% + 161.8%
- PDH/PDL can also be part of a cluster
- A fib expansion **target** inside a cluster = **TARGET CLUSTER** (stronger level)

### Cluster size (max distance between levels to count as cluster)

| Type | Size |
|------|------|
| Forex | 5 pips |
| Gold, Oil | 15 pips |
| BTCUSD | $10 |
| ETHUSD | $5 |

---

## SUPPORT AND RESISTANCE

These things act as S/R (and therefore obstacles):
1. Clusters
2. Trend channels
3. EMA21
4. Imbalance boxes
5. Last 2 swings (H4)

---

## TREND (on H4)

### Bullish
- Price is above EMA21 and bounces from it.
- Each new Swing High is higher than the previous.

### Bearish
- Price is below EMA21 and bounces from it.
- Each new Swing Low is lower than the previous.

### Trend Channel
- Connect at least 2 swing points to draw a trendline.
- Draw parallel line on the opposite side — attach to "biggest bump" if no clean fit.
- Channel boundaries act as S/R (obstacles).

---

## LLR — Line of Least Resistance (on H1)

1. A line connecting **at least 2 micro-swings** (not big structural swings — the small direction changes in the last 5-7 candles).
2. Draw from both sides (support and resistance sides).
3. **For BUY:** connect the last 2 micro swing LOWS → ascending support line. Price should be ABOVE it.
4. **For SELL:** connect the last 2 micro swing HIGHS → descending resistance line. Price should be BELOW it.
5. The LLR updates dynamically as new micro-swings form.
6. It acts as the "last line of defense" — if price breaks below support LLR (for buys), the trade idea is dead.

### Micro-swing detection
A micro-swing low = a bar whose Low is lower than both its immediate neighbors (lookback=1). Same logic inverted for highs. This gives frequent, fresh swing points from the last ~5-7 bars — not the big H4/D1 structural swings.

### Signal candle (M5/M15)
- Candle body > 60% of total range (strong conviction).
- Closes in the direction of the break.
- Optional confirmation — adds quality but reduces quantity.

### LLR research findings

**On H1:** LLR only rejects 2-3% of trading days in the diagnostic funnel (02_diagnostic_funnel). It's a permissive filter — most bars that pass EMA21 + H4 trend also pass LLR. Of bars reaching the LLR check, ~65-73% pass.

**On M15:** LLR gives signal before target settlement in 87-89% of cases (03_ltf_analysis). For targets 10-20 pips away, LLR signal rate is 97-100%. LLR has higher signal rate than EMA21 on M15 (78% vs 55% for close targets <10 pips).

**LLR vs no LLR in backtesting:**
- On H1 (04_h1_permutations): LLR adds almost nothing — PF difference is <0.02 for most instruments.
- On M15 (05_m15_backtest): LLR barely matters. Example EURUSD baseline: LLR+H4 PF=1.67 vs H4-only PF=1.67. Removing LLR adds ~6 trades with no PF change.
- **Exception:** LLR helps on USDCAD (+0.07 PF), NZDUSD (+0.05 PF), XAUUSD (+0.03 PF), and in multi-offset configurations where it acts as a quality gate.

**Bottom line:** On M15, LLR swings update too fast to provide meaningful S/R — by the time a swing forms and breaks, the move is already happening. H4 trend is the real edge. LLR is useful as an optional quality filter but not essential on M15. On H1, LLR is more meaningful because swings are larger and slower.

---

## STRATEGY #1 — REACTION (we can test it but in reality less important)

Price reacts at the TARGET (or a cluster containing the target).

### Rules
1. Place **BUY/SELL limit** order at target ± 5 pips offset (wider if cluster is >15 pips range). Spread must be factored in.
2. If no reaction and price moves 100 pips past target → trigger Strategy #3 (AVERAGING).
3. Lot size: **0.01 per $1,000** balance.
4. **SL 1:1** (stop loss = take profit distance).
5. TP = 15 pips in the bounce direction.

---

## STRATEGY #2 — COMING

Trend-following approach toward the target.

### Rules (in order)
1. **EMA21 filter**: Full candle above EMA21 → BUY direction. Full candle below EMA21 → SELL direction. "Full candle" = entire bar (high/low) is on one side.
2. **Minimum distance**: If less than 15 pips to the target → do NOT open. (Spread is additional — so effective minimum is 15 + spread.)
3. **Trailing stop**: Activate only after price has moved ~35% of the distance to target. Once activated, trail at 15 pips — i.e., wait 15 pips of further movement, then move SL by 15 pips, and keep trailing in 15-pip steps.
4. **Settle tolerance**: Target is considered reached within the settle tolerance PLUS spread. Forex = 5 pips, Gold = 15 pips, BTC = $10, ETH = $5 (see table above).
5. **Obstacles**: Create order after the last obstacle. If there are 2+ obstacles between price and target → skip. Max 1 obstacle allowed in the path.
6. **Cluster-aware TP**: If target is inside a cluster, set TP to the **closer side** of the cluster (minus settle tolerance).
7. **Spread awareness**: Forex 0–5 pips, gold ~9 pips. Factored into entry and settle.
8. **Tiered confidence SL** (forex only — gold/crypto keep SL 1:1):
    - **Tier A** (distance ≤ 35 pips): SL **3:1**, **no trailing stop**. These short-distance targets have 70-90% settle rates — give the trade maximum room, don't trail.
    - **Tier B** (35–100 pips): SL **1.5:1**, trailing activates at **50%** of distance. Medium probability — moderate room.
    - **Tier C** (>100 pips): SL **1:1**, trailing activates at **35%**. Standard approach for low-probability long shots.
    - Gold/crypto are excluded from tiers because their pip-based distances don't map to the same settle probabilities. Their standard SL 1:1 already produces strong profit factors (XAUUSD PF=2.32, BTCUSD PF=4.30).
10. **Position sizing by distance**: Risk % of balance scales with distance to target:
    - ≤30 pips → risk **0.5%** of balance
    - 30–50 pips → risk **1%** of balance
    - ≥50 pips → risk **2%** of balance

    Lot size is calculated from the risk % and SL distance (which equals distance to target).
9. **Max spread filter**: Do NOT place orders when current spread exceeds threshold. Forex: 15 pips. Gold: 16 pips. Crypto: TBD (no hard limit defined yet).

### H4 trend confirmation
It's good if trade direction agree with H4 trend, couse the h4 trend channel can work as S/R lines

### Entry timing
On M5 or M15 bars, we can wait for signal candle for better confirmation.

---

## STRATEGY #3 — AVERAGING

Recovery strategy when a position is underwater.

### Conditions (all must be met)
1. **Min diff**: The SL must be 100+ pips away (i.e., the trade is deep enough underwater that averaging makes sense — the 100 pip threshold refers to SL distance, not floating P&L).
2. **Expected direction**: Price must be moving in the recovery direction.
3. **EMA21 confirmation**: BUY averaging only above EMA21, SELL averaging only below EMA21.
4. **Max multiplier**: Total averaging lots ≤ 4× the original position's lots.

---

## LLR FINDINGS (Research Summary)

LLR (Line of Least Resistance) works on M15 with **micro-swings** (lookback=1 — a low lower than both its immediate neighbors, or a high higher than both neighbors).

### How LLR works
- **For BUY**: connect the last 2 micro swing lows = ascending support line. Price must be **ABOVE** this line.
- **For SELL**: connect the last 2 micro swing highs = descending resistance line. Price must be **BELOW** this line.
- The line **updates dynamically** as new swings form (every 5-7 candles on M15).
- LLR acts as the "last line of market defense" — once broken, it flips from support to resistance (or vice versa).
- Confirmed working across all 10 instruments on M15 timeframe.

### Research results
- **On H1:** LLR only rejects 2-3% of trading days (from 02_diagnostic_funnel). It is a permissive filter — ~65-73% of bars that reach the LLR check pass.
- **On M15:** LLR gives signal before target settlement in 87-89% of cases (from 03_ltf_analysis). For targets 10-20 pips away, LLR signal rate is 97-100%.
- **Backtest impact:** On M15, LLR barely changes PF (e.g., EURUSD: LLR+H4 PF=1.67 vs H4-only PF=1.67). Exception: LLR helps on USDCAD (+0.07 PF), NZDUSD (+0.05 PF), XAUUSD (+0.03 PF), and in multi-offset configurations where it acts as a quality gate.
- **Bottom line:** H4 trend is the real edge. LLR is useful as an optional quality filter but not essential on M15 due to fast swing updates. On H1, LLR is more meaningful because swings are larger and slower.

---

## OFFSET TARGETS

### Standard target
Target = **H + L - O** from the previous day's 00:00-24:00 UTC window.

### Offset targets
Shift the measurement window: 01:00-01:00, 02:00-02:00, ... 12:00-12:00 UTC. Each offset produces its own O/H/L from the shifted "day", and therefore its own target.

### Key findings
- Different offsets produce different targets — **85-95% differ by >3 pips** from the main 00:00 target.
- **ALL 13 offsets** (00:00 through 12:00 UTC) are profitable on ALL instruments.
- PF increases monotonically from 00:00 to 12:00. **Best offsets: 11:00-12:00 UTC** (London+NY overlap).
- **Combined result:** 61,200 trades over 6 years, **+4,654,538 pips**, average **PF 3.18**.

### Risk management with multi-offset
With 13 simultaneous offsets, risk per trade = base_risk / 13 (e.g., 0.15% per trade if base is 2%).

---

## ARCHITECTURE

```
Python Engine (one codebase)
    │
    ├── MT5: direct via mt5.order_send()  ← fast, no latency
    │
    └── MT4: file bridge via CSV           ← universal, thin EA
```

- **MT5 mode**: Python connects directly to MetaTrader 5 terminal via the `MetaTrader5` package. Orders are sent via `mt5.order_send()`. Bar data is fetched via `mt5.copy_rates_from_pos()`.
- **Bridge mode**: Python writes trade signals to CSV files in `MQL4/Files/`. A thin MQ4 EA (`CBS_Bridge_EA.mq4`) reads the CSV and executes orders in MT4. Data still comes from MT5 (or an external feed).
- **Backtest mode**: Runs on historical CSV data from the `DATA/` directory. Same `SignalGenerator` logic as live, same indicator functions from `research/indicators.py`.

---

## USAGE / QUICK START

```bash
# Backtest (all instruments, fixed spread)
python -m engine.main --backtest --symbols all

# Backtest (specific instruments, random spread, date range)
python -m engine.main --backtest --symbols EURUSD,XAUUSD --spread-mode random --from-date 2023-01-01 --to-date 2025-12-31

# Live MT5 (dry run first!)
python -m engine.main --symbols EURUSD,XAUUSD --mode mt5 --dry-run

# Live MT5 (real execution)
python -m engine.main --symbols EURUSD,XAUUSD --mode mt5 --risk 1.0 --gmt-offset 2

# Live MT4 bridge
python -m engine.main --symbols EURUSD --mode bridge
```

### CLI flags
| Flag | Default | Description |
|------|---------|-------------|
| `--symbols` | all | Comma-separated list, or "all" |
| `--mode` | mt5 | `mt5` (direct) or `bridge` (file-based for MT4) |
| `--risk` | 1.0 | Risk per trade as % of balance |
| `--gmt-offset` | 2 | Broker server GMT offset |
| `--dry-run` | off | Compute signals but do not execute trades |
| `--no-h4` | off | Disable H4 trend filter |
| `--use-llr` | off | Enable LLR support/resistance filter |
| `--min-distance` | per-instrument | Override minimum distance in pips |
| `--backtest` | off | Run backtest on historical CSV data |
| `--from-date` | 2020-01-01 | Backtest start date |
| `--to-date` | 2025-12-31 | Backtest end date |
| `--spread-mode` | fixed | `fixed`, `random`, or `historical` |
| `--log-level` | INFO | DEBUG, INFO, WARNING, ERROR |

---

## SPREAD RANGES

Realistic spread ranges per instrument, used by the `random` spread mode in backtesting. Spreads are drawn uniformly from [min, max] for each trade.

| Instrument | Min (pips) | Max (pips) |
|------------|-----------|-----------|
| EURUSD | 0.5 | 3.0 |
| GBPUSD | 0.8 | 3.5 |
| USDJPY | 0.5 | 2.5 |
| USDCHF | 0.8 | 3.0 |
| AUDUSD | 0.5 | 2.5 |
| USDCAD | 0.8 | 3.5 |
| NZDUSD | 0.5 | 3.0 |
| XAUUSD | 15.0 | 70.0 |
| BTCUSD | 30.0 | 100.0 |
| ETHUSD | 5.0 | 30.0 |

---

## FILE STRUCTURE

```
CBS/
├── strategy.md                    # This file — single source of truth
├── GOALS.md                       # Current goals and priorities
├── IDEAS.md                       # Feature ideas and brainstorms
├── CBS_MT.set                     # MetaTrader preset file
│
├── engine/                        # Live trading + backtest engine
│   ├── __init__.py
│   ├── config.py                  # Engine config (re-exports research.config + live settings)
│   ├── main.py                    # CLI entry point, live trading loop (CBSEngine)
│   ├── backtest.py                # Historical backtest runner (CBSBacktester)
│   ├── signals.py                 # Signal generator (SignalGenerator, Signal dataclass)
│   ├── journal.py                 # Trade journal CSV writer
│   └── executors/
│       ├── mt5_executor.py        # MT5 direct execution (order_send, trailing, positions)
│       └── file_bridge.py         # MT4 file bridge (CSV signal writer)
│
├── research/                      # Research scripts (numbered sequence)
│   ├── config.py                  # Shared config: instruments, tiers, paths, pip values
│   ├── data_loader.py             # CSV data loading utilities
│   ├── indicators.py              # Indicator functions (EMA, LLR, H4 trend)
│   ├── 01_target_analysis.py      # Target settlement analysis
│   ├── 02_diagnostic_funnel.py    # Filter rejection funnel
│   ├── 03_ltf_analysis.py         # Lower timeframe LLR/EMA analysis
│   ├── 04_h1_permutations.py      # H1 filter permutation testing
│   ├── 05_m15_backtest.py         # M15 baseline backtest
│   ├── 06_capture_rate.py         # Capture rate analysis
│   ├── 07_per_instrument.py       # Per-instrument optimization
│   ├── 08_offset_targets.py       # Offset target discovery
│   ├── 09_offset_backtest.py      # Single offset backtest (08:00 UTC)
│   ├── 10_combined_backtest.py    # Main + offset combined backtest
│   ├── 11_offset_sweep.py         # All offsets 00-12 sweep analysis
│   ├── 12_multi_offset_backtest.py # Full multi-offset backtest (definitive)
│   ├── 13_intraday_window_scan.py # Intraday window scanning
│   ├── 14_intraday_backtest.py    # Intraday window backtest
│   └── README.md                  # Research scripts documentation
│
├── ea/                            # MetaTrader Expert Advisors
│   ├── CBS_Bridge_EA.mq4         # MT4 file bridge EA (reads CSV signals)
│   ├── CBS_COMING_EA.mq4         # MT4 standalone COMING strategy EA
│   ├── CBS_COMING_EA.mq5         # MT5 standalone COMING strategy EA
│   ├── Include/                   # MQL include files
│   │   ├── CBS_Config.mqh         # EA configuration parameters
│   │   ├── CBS_Filters.mqh        # Entry filters (EMA, LLR, H4 trend)
│   │   ├── CBS_FilterLearner.mqh  # Adaptive filter learning
│   │   ├── CBS_Indicators.mqh     # Indicator calculations
│   │   ├── CBS_Journal.mqh        # Trade journaling
│   │   ├── CBS_Targets.mqh        # Target computation
│   │   └── CBS_TradeManager.mqh   # Trade management (SL/TP/trailing)
│   └── Presets/                   # Per-instrument .set files
│       ├── CBS_EURUSD.set
│       ├── CBS_GBPUSD.set
│       └── ... (one per instrument)
│
└── archive/                       # Old scripts and models (historical reference)
    ├── cbs_engine/                # Previous engine version
    ├── analysis/                  # Old analysis outputs
    ├── models/                    # ML models (v2, deprecated)
    ├── models_v1/                 # ML models (v1, deprecated)
    └── *.py                       # Old backtest/analysis scripts
```