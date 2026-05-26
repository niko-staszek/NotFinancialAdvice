# Strategy EA Specification (Price Action Cycle — Implementable Subset)

---

## §0 Preamble

### §0.1 Scope & Versioning

**Version:** v1.0-draft  
**Date:** 2026-05-26

This document is the **implementable EA specification** for the Price Action Cycle (PAC) strategy. It defines every rule, parameter, gate, and mode of operation that a Phase 2 implementer will need to produce a working MQL5 Expert Advisor and a parallel Python reference implementation. It is not a strategy curriculum, a trading journal, or an investment recommendation.

The canonical PAC curriculum — derived from Paweł Krynicki's 16-video instructional series — lives in `strategy.md`. That document describes what PAC *is* in human-learning terms: how a student should read the market, what each component means conceptually, and how the full cycle of setup-entry-exit works in practitioner language. `strategy.md` remains the source of truth for *intent*; this document translates that intent into unambiguous, computer-executable rules.

The relationship is strictly one-way: this spec cites `strategy.md` for every rule that mirrors the curriculum; `strategy.md` is never modified to match this doc. Where `strategy.md` is silent on a parameter (e.g., a concrete stop-loss distance in pips, or a minimum R:R threshold), this spec fills the gap using `review.md` recommendations or widely-accepted industry defaults, noting the source explicitly.

This document covers the **implementable subset** of PAC components — meaning only those components that can be detected algorithmically on price data alone, or via simple derived indicators, without requiring real-time human judgment. Components that are too subjective, too context-dependent, or that depend on tick-chart data not reliably available across brokers are listed in §0.5 as deferred items for v2.

---

### §0.2 Data Sources & Known Limitations

The following five analysis files from `chatdump_analysis/` were used to calibrate this specification. All frequency counts, threshold suggestions, and component rankings throughout this document trace back to one or more of these sources.

| File | Contents |
|---|---|
| `chatdump_analysis/component_frequency.md` | Mentor + student component reference counts across the full Discord export. The authoritative source for which PAC components are most-discussed and thus most likely to reflect core strategy intent. |
| `chatdump_analysis/setup_distribution.md` | Symbol × session × day-of-week pivot table. Used to calibrate session windows (§3), symbol defaults (§6), and the DOW filter (§0.5). |
| `chatdump_analysis/mentor_audit.md` | 8 mentor trade-call rows with flagged deviations from canonical PAC rules. Used to identify where mentors bend their own rules and to flag ambiguities in the inclusion criteria for §4 (entry logic). |
| `chatdump_analysis/trades_catalog.csv` | 167 catalog rows covering both mentor and student trade calls across the full dataset. The source for raw trade-event data. |
| `chatdump_analysis/PHASE_0_REPORT.md` | Exit report from Phase 0 analysis with refreshed aggregate numbers. Summary reference for high-level statistics cited throughout this doc. |

**Known limitation caveat:** Mentor catalog rows total 8 of 167 (4.8%), which is lower than expected for a mentor-led community. This suggests either (a) the parser under-detected mentor trade-call formats — many mentors post commentary and analysis rather than structured "entry at X, SL at Y" messages — or (b) that the mentors in this Discord teach predominantly through explanation and retrospective review rather than posting live trade calls. As a consequence, direct parameter inference from the 8 mentor trade rows is unreliable for tasks such as stop-loss width distribution, take-profit targeting habits, or preferred session windows.

All inclusion decisions throughout this spec are therefore driven by the **component-frequency report** (`component_frequency.md`), which covers the full corpus of 2,123 mentor messages, not by the 8 trade-call rows. SL/TP threshold tuning in §5 and §7 falls back to `review.md` recommendations rather than chatdump-derived data. Any future re-parse that yields a higher mentor trade-call count should trigger a review of those sections.

---

### §0.3 Relation to `strategy.md` / `review.md` / `literature_comparison.md`

**`strategy.md`** is the canonical PAC curriculum derived from Paweł Krynicki's 16-video series. It documents the strategy as a human practitioner would learn it: session structures, the five-wave cycle, entry confluence requirements, exit protocols, and the role of each indicator or drawing tool in confirming or filtering a setup. Every rule in this EA spec that mirrors the curriculum cites the corresponding section of `strategy.md` by name. `strategy.md` stays untouched — no edits are made to it in response to implementation difficulties. If a rule in `strategy.md` turns out to be unimplementable, it is listed in §0.5 and deferred, not silently omitted or reworded.

**`review.md`** is a critical assessment of PAC that identified key gaps in the strategy as documented: the absence of a formal risk-management section, the absence of a minimum R:R filter, and a lack of concrete default values for parameters that `strategy.md` leaves to practitioner discretion. The review also proposed a "PAC Lite" subset — a reduced component list that preserves the highest-evidence elements while dropping components that are either redundant or too subjective for consistent application. This EA spec adopts `review.md`'s risk-rule structure directly (§1 below) and uses its recommended thresholds wherever `strategy.md` is silent. However, the spec does **not** adopt `review.md`'s component selection wholesale: which PAC components are included or excluded from the implementable subset is governed by the component-frequency data from `chatdump_analysis/component_frequency.md` and by algorithmic feasibility, not by `review.md`'s editorial choices (see §0.4 for the inclusion criterion).

**`literature_comparison.md`** maps PAC components to analogous constructs in established trading literature: Wyckoff's accumulation/distribution phases, Al Brooks's bar-by-bar price action methodology, ICT's liquidity and order-block framework, Scott Carney's harmonic pattern library, Elliott Wave theory, and Steve Nison's candlestick taxonomy. This document is used at two points in the EA spec: (a) to assess automation feasibility — components that have well-defined algorithmic analogues in the literature are rated higher for inclusion, and (b) to provide cross-reference rationale when a rule choice deviates from a naïve reading of `strategy.md` alone. Literature references are cited in section headers as `[LitComp §X]` where relevant.

---

### §0.4 Notation Conventions

The following notation is used consistently throughout this document. Implementers should apply these definitions wherever a symbol, value, or time reference appears without further qualification.

**ATR(20):** The 20-bar Average True Range calculated on the current chart timeframe. Unless a section explicitly specifies a different timeframe (e.g., "ATR(20) on H1"), `ATR(20)` always refers to the M5 chart. ATR is computed as the Wilder smoothed average of true ranges over the 20 most recent completed bars (bar 1 through bar 20). The current forming bar (bar 0) is excluded from ATR inputs to avoid look-ahead bias.

**Bar indices:** Bar `0` is the rightmost bar — the currently forming, not-yet-closed candle. Bar `1` is the most recently *closed* bar (the one that just completed). Bar `2` is the bar before that, and so on: larger indices refer to older bars. All pattern-detection logic operates on closed bars (bar index ≥ 1) unless the spec explicitly states otherwise.

**R-multiples:** `1R` is the price distance from the trade entry to the stop-loss. `2R` is twice that distance from entry measured in the profit direction (i.e., the first take-profit level if targeting 2:1 reward-to-risk). R-multiples are always computed from the actual entry fill price, not the order trigger price, to account for slippage. A setup that "requires 1.5R" means the nearest plausible take-profit level must be at least 1.5× the entry-to-SL distance away.

**Polish local time (PLT):** The Paweł Krynicki curriculum uses Polish local time for session references, indicator start times, and daily reset points. Polish local time is CET (UTC+1) in winter (last Sunday of October through last Sunday of March) and CEST (UTC+2) in summer (last Sunday of March through last Sunday of October). Implementers must build DST-aware UTC↔PLT conversion into all time-gating logic. Hard-coded UTC offsets (+1 or +2) are not acceptable — the EA must derive the correct offset from the calendar date at runtime. Broker server time is an unreliable proxy; use UTC as the intermediate representation.

**Pip definitions:** Pip sizes vary by instrument. The EA must apply the correct definition per symbol at runtime:

| Instrument class | Examples | 1 pip = |
|---|---|---|
| 4-digit FX majors | EURUSD, GBPUSD, USDCAD | 0.0001 |
| JPY pairs (2-digit) | USDJPY, EURJPY | 0.01 |
| Gold | XAUUSD | $0.10 (0.10 price units) |
| Oil | USOIL | $0.01 (0.01 price units) |
| Indices | US500, NAS100, US30 | 1 index point (broker-dependent; verify `SymbolInfoDouble(SYMBOL_POINT)` at runtime) |

For indices, the "pip" concept is not standardised across brokers; the EA should fall back to `SYMBOL_POINT` as reported by the broker's symbol specification rather than assuming a fixed value. All SL/TP distances specified in pips in this document use the above definitions. ATR-based distances are always in price units (not pips) and do not require conversion.

---

### §0.5 Open Questions for v2

The following items are explicitly deferred from v1. Each represents a decision that could not be resolved with the available data or that introduces integration complexity disproportionate to v1 scope. They are listed here so that v2 planning has a clear backlog anchor.

- **Tick chart support.** Several PAC practitioners use tick charts (e.g., 133-tick or 512-tick) rather than time-based M5 bars for entry timing. Tick chart support is deferred in v1 due to broker data-quality concerns: tick data feed availability, replay fidelity, and the absence of standardised tick chart rendering across MT5 brokers make it impractical to specify testable rules. v2 should revisit once a reference broker environment is identified. All v1 rules are specified on M5 time-based bars only.

- **MMD integration mode.** Market Maker Dynamics (MMD) is a complementary analytical framework referenced in the curriculum. In v1 the EA treats MMD as a filter-only layer operating *inside* the PAC entry logic — the MMD bias (bullish/bearish/neutral) gates whether a PAC setup qualifies for entry, but does not generate independent entry signals. An alternative mode where MMD runs as a standalone strategy alongside the PAC EA (sharing the same position-sizing and drawdown framework but with separate entry signals) is theoretically valuable but architecturally complex. v2 should evaluate standalone-vs-filter via backtesting before deciding which mode to default to.

- **Day-of-week (DOW) filter strictness.** The `setup_distribution.md` pivot shows non-uniform setup frequency across weekdays, with Monday and Friday showing lower setup counts on several symbols. review.md recommends considering a DOW filter. In v1 the DOW information is treated as **informational only** — it is exposed as a dashboard metric but does not gate entries. Promoting it to a hard filter (e.g., no new entries on Monday before the London open, or no entries on Friday after 15:00 PLT) is deferred to v2 pending a proper forward-test comparison of filtered vs unfiltered equity curves.

- **Online translation pass for `content_en`.** The trades catalog (`trades_catalog.csv`) contains a `content_en` column that is currently empty across all 167 rows — messages were not translated during Phase 0 parsing. Running an automated translation pass (e.g., via a language model or DeepL API) would enable English-language pattern matching, frequency analysis on entry descriptions, and human review by non-Polish readers. This is deferred to v2 as a data-quality improvement task, not an EA implementation task. It should be completed before any attempt to extract semantic entry conditions from the catalog text fields.

- **Mentor account list completeness.** Phase 0 identified 13 mentor accounts by their "ALLin"-prefix naming convention in the Discord export. This list may not be exhaustive: some mentors may have posted under non-prefixed accounts, personal usernames, or guest accounts without the naming convention. Any component-frequency analysis that weights mentor posts differently from student posts (which applies throughout this spec) is subject to this uncertainty. v2 should include a manual verification step — cross-referencing the Discord role hierarchy with the identified account list — before recalibrating component weights.

---

## §1 Risk Management

This section defines the seven mandatory risk controls for the PAC EA. All rules are active by default. Where a rule can be disabled or relaxed via an EA input, the input name is given; where no override is permitted, the rule is enforced unconditionally.

The structure below follows the gap-filling framework from review.md §Risk Management, which identified the absence of a formal risk layer as the primary shortcoming of `strategy.md` as a self-contained trading specification. Every default value either mirrors a sibling NFA strategy (MRD, ORB) for consistency or is drawn from industry practice for retail MT5-based forex/CFD trading.

---

### §1.1 Position Sizing

**Default:** `1.0%` of current account equity per trade.  
**Configurable via:** `RiskPercent` EA input (numeric, range 0.1–5.0, step 0.1).  
**Override conditions:** None. `RiskPercent` is applied to every entry without exception. No other rule in this spec adjusts position size above or below the user-configured value.  
**Rationale:** The 1% per-trade equity risk is the de facto industry standard for retail forex accounts and is the figure consistently recommended in institutional risk-management literature for accounts below $500k. It balances longevity (a 100-trade losing streak would reduce the account to ~36.6% of starting equity under fixed-percent compounding, which is recoverable) against meaningful compounding when in drawdown. The PAC EA uses this default to remain consistent with sibling NFA strategies: the MRD EA uses 1% and the ORB EA uses 1%. Deviating from this default without a well-understood reason materially changes the risk profile of all three strategies when run simultaneously on the same account. See review.md §Risk Management for the gap-filling context.

Position size in lots is computed as:

```
lots = (AccountEquity × RiskPercent / 100) / (SL_distance_in_price_units × ContractSize × TickValue / TickSize)
```

The result is rounded down to the nearest broker-permitted lot step (`SYMBOL_VOLUME_STEP`). If the resulting lot size is below the broker minimum (`SYMBOL_VOLUME_MIN`), the trade is rejected and logged as "lot size below minimum — skipped."

---

### §1.2 Minimum R:R Gate

**Default:** `1:1.5` (reward-to-risk; the take-profit must be at least 1.5× the SL distance from entry).  
**Configurable via:** `MinRR` EA input (numeric, range 0.5–5.0, step 0.1).  
**Override conditions:** None. Any setup whose nearest plausible take-profit level (as computed by §5 and §7 exit logic) cannot achieve the configured `MinRR` ratio given the computed stop-loss is **rejected before entry**. The rejection is logged with the actual achievable R:R for diagnostic review.  
**Rationale:** review.md §Risk Management flags the complete absence of a minimum R:R requirement as the primary gap in `strategy.md` — the curriculum teaches entry and exit mechanics but specifies no filter preventing a trader from taking a setup where the target is closer than the stop. The default of 1:1.5 is deliberately permissive: it is lower than the 1:2 frequently cited in retail trading education, which means it will reject only the most unfavourable setups rather than filtering out a large fraction of valid PAC signals. This preserves trade frequency while eliminating the worst-edge cases. The threshold should be raised to 1:2 in v2 if backtesting shows that the 1:1.5–1:2 bracket contains predominantly losing trades.

---

### §1.3 Per-Session Trade Cap

**Default:** `3` trades per session window (combined across all symbols monitored by the EA instance).  
**Configurable via:** `MaxTradesPerSession` EA input (integer, range 1–10).  
**Override conditions:** The correlated-pair lockout (§1.6) may reduce the effective cap below the configured value. If two symbols in a correlation group both generate signals in the same session, only the first-triggered one is taken; the cap is not "refilled" by the lockout rejection. No other rule overrides this cap upward.  
**Rationale:** The M5 timeframe generates a high volume of potential signals relative to higher timeframes. Without a trade cap, the EA can churn through multiple marginal setups during a single session, accumulating transaction costs and correlated risk even without exceeding the daily drawdown limit. review.md §Risk Management recommends a maximum of 3 trades per session as a practical overtrading guard. The three PAC sessions (Asia, London, America) each have their own independent counter, so "3 per session" does not globally cap at 3 per day — a full day with clean setups in all three sessions could yield up to 9 trades. The session counter resets at the opening of each session window (see §3 for session time definitions in PLT).

---

### §1.4 Daily Drawdown Circuit-Breaker

**Default:** `-3.0%` of account equity in a rolling 24-hour window.  
**Configurable via:** `DailyDDStop` EA input (numeric, range -0.5 to -10.0, step 0.1; stored as a negative value).  
**Override conditions:** None. When the rolling 24-hour realised-and-open P&L falls to or below `DailyDDStop`, the EA immediately cancels all pending orders on managed symbols, closes no open positions (to avoid locking in a loss at a bad price unless separately configured), and halts new entry signals until the next calendar-day session reset. The halt is logged with the timestamp and exact P&L figure that triggered it.  
**Rationale:** A -3% daily circuit-breaker is the industry standard for retail prop-challenge accounts and is the figure used in MRD and ORB sibling strategies for consistency. FTMO's standard challenge rules set a 5% *daily* hard limit and a 10% *total* soft limit; using -3% as the EA's internal daily stop leaves a 2% buffer before a prop-firm account is disqualified, which gives the human operator a chance to intervene manually if the EA's halt is triggered. For non-prop accounts, -3% remains a sensible default that prevents a single bad session from doing lasting damage to the equity curve. The "24-hour rolling" framing — rather than "within today's calendar day" — prevents the edge case where losses straddle midnight and partially reset the counter.

---

### §1.5 Weekly Drawdown Circuit-Breaker

**Default:** `-5.0%` of account equity in a rolling 7-day window.  
**Configurable via:** `WeeklyDDStop` EA input (numeric, range -1.0 to -20.0, step 0.1; stored as a negative value).  
**Override conditions:** None. When the rolling 7-day realised-and-open P&L falls to or below `WeeklyDDStop`, the EA halts all new entries until the 7-day window has rolled past the trigger point (i.e., the drawdown naturally decays below the threshold as older losing days leave the window) or until the operator manually resets the halt. The halt is logged identically to §1.4.  
**Rationale:** The weekly circuit-breaker is a second-order safeguard for situations where the daily limit is never hit in isolation but cumulative losses across multiple days compound into a material drawdown. At -5%/week, an account running at full capacity in all three sessions could theoretically hit the weekly stop on roughly two consecutive -3% days (with a small reversal in between that prevents the daily stop from firing alone). FTMO's 10% monthly hard limit implies a rough budget of ~2.5% per week for a trader who wants to stay safe; the -5% weekly cap gives two times that budget — appropriate for an EA with a positive-expectancy system. The rolling-window implementation prevents the "Monday morning reset" exploit where a trader blows through the weekly budget late in the week knowing the counter will reset.

---

### §1.6 Correlated-Pair Lockout

**Default:** Three correlation groups, semicolon-separated, defined as follows:

- `{XAUUSD,US500}` — risk-off asset pair: gold and the S&P 500 index tend to move in opposite directions during risk-off events. Block entries in *opposite directions* simultaneously (i.e., do not hold a long XAUUSD and a long US500 at the same time, as this implies two bets on a risk-off move).
- `{US500,US30,USTECH}` — US equity indices: these three instruments are highly correlated in the same direction. Block *same-direction* overlap (i.e., do not hold two long index positions simultaneously, as this is effectively one position with doubled size and doubled broker spread cost).
- `{USOIL,US500}` — loose positive correlation (risk-on sentiment tends to lift both oil and equities). Block same-direction overlap as a precaution; this group can be emptied if backtesting shows it rejects too many genuinely independent setups.

**Configurable via:** `CorrelationGroups` text input (free-form string; parser splits on semicolons, then extracts symbol lists in braces). Default value is the three groups above as a single semicolon-separated string. The text input format allows operators to add, remove, or modify groups without recompiling.  
**Override conditions:** None. When the lockout fires, the second signal is rejected and logged; it does not queue for later entry.  
**Rationale:** Without a correlation lockout, an EA monitoring multiple symbols can simultaneously open positions that are economically equivalent to a single larger position — doubling effective risk on one underlying move while the position-sizing logic (§1.1) believes it has two independent 1% risks. This is a well-known failure mode for multi-symbol retail EAs and the primary reason sibling strategies operate on a single symbol each. Since the PAC EA is designed to monitor multiple instruments (see §6 for the symbol list), the lockout is a necessary safeguard. The default groups are conservative starting points derived from common knowledge of cross-asset correlation; they should be refined using a rolling-correlation matrix computed on the specific broker's historical data before live deployment.

---

### §1.7 News Blackout

**Default:** OFF (`NewsFilter_Enabled = false`).  
**Configurable via:** `NewsFilter_Enabled` (boolean), `NewsBlackoutMinsBefore` (integer, default 15), `NewsBlackoutMinsAfter` (integer, default 15), `NewsImpactLevel` (enum: HIGH / MEDIUM / HIGH_ONLY, default HIGH_ONLY).  
**Override conditions:** None. When enabled, blocks new entry orders within `NewsBlackoutMinsBefore` minutes before and `NewsBlackoutMinsAfter` minutes after any scheduled news event of the configured impact level on the traded symbol's base or quote currency. Open positions are not closed by the news filter — it is an entry gate only. Any pending orders placed before the blackout window that have not yet triggered are cancelled at the start of the blackout window.  
**Rationale:** High-impact news events (non-farm payrolls, central bank rate decisions, CPI releases) generate price whipsaws on M5 charts that are statistically hostile to price-action setups: the pre-news consolidation creates false breakout signals, and the post-news spike often hits stop-losses before directional resolution. The PAC curriculum (strategy.md) implicitly assumes normal price action conditions; the EA should not attempt to trade through abnormal conditions. News source TBD as an integration hook (Forex Factory CSV calendar file, Investing.com economic calendar scrape, or broker-provided economic calendar API). The filter is off by default in v1 because no news source is yet integrated; it is implemented as a hookable stub so that v2 can activate it without changing the surrounding entry logic. The sibling ORB strategy includes an identical rule and identical deferral note.

---

*End of §0 Preamble and §1 Risk Management. §2 onward covers session definitions, signal components, entry logic, stop placement, take-profit targeting, symbol-specific parameters, and operational configuration.*

---

## §2 Universe & Sessions

### §2.1 Tradable Instruments

This section locks the v1 EA instrument whitelist based on Phase 1a refreshed catalog data (`chatdump_analysis/PHASE_0_REPORT.md` line 119). The 8 instruments below represent approximately 98% of all mentor and student catalog activity across the full dataset.

| Symbol | Class | Catalog rows | Notes |
|---|---|---|---|
| XAUUSD | Metal (spot) | 60 | Top instrument by activity. `GOLD` alias canonicalized to XAUUSD at detector level (Phase 1a). |
| USOIL | Commodity | 39 | `CL` alias canonicalized to USOIL at detector level (Phase 1a). |
| US500 | Index | 20 | S&P 500 CFD. |
| NAS100 | Index | 13 | Nasdaq 100 CFD. |
| EURUSD | Forex major | 8 | |
| GC | Metal (futures) | 6 | Gold futures (CME) contract, **distinct from XAUUSD spot CFD** — intentionally NOT aliased. Opt-in via EA input `EnableGCFutures` (default false). |
| GBPUSD | Forex major | 4 | Minor activity. |
| USDCAD | Forex major | 4 | Minor activity. |

**Default whitelist:** XAUUSD, USOIL, US500, NAS100, EURUSD, GBPUSD, USDCAD — 7 symbols active by default. GC is opt-in only, disabled by default, because gold futures require separate margin treatment and are not universally available on retail CFD brokers that carry the spot instrument.

**EA input:** `TradableSymbols` (semicolon-separated string). Default value is the 7 default symbols listed above. At EA startup, each symbol in `TradableSymbols` is verified against the broker's symbol list via `SymbolInfoString`. Any symbol not present on the broker's platform is skipped with a log entry identifying the missing symbol by name; the remaining symbols initialise normally. This prevents hard failures when an EA configured for USOIL is loaded on a broker that uses a different oil-contract naming convention.

---

### §2.2 Timeframes

**Primary chart timeframe: M5 (5-minute bars).** All EA logic computes on M5 unless explicitly noted otherwise in the relevant section. Signal detection, ATR(20), bar-pattern recognition, and all time-gating calculations operate on M5 bars.

**D1 reference (§3.3):** The D1 OHLC promo zone (§3.3) uses the previous day's D1 open, high, low, and close values obtained via `iHigh`, `iLow`, `iOpen`, and `iClose` called on the D1 timeframe. This is a direct D1 data query — no M5 calculation is involved. The D1 values are fetched once per day at the start of each trading day and cached until the next D1 bar opens.

**Higher-timeframe context (§3.2 MMD clouds):** The MMD indicator references cloud periods of 12, 48, 144, 288, 720, 1440, and 3456 bars. On an M5 chart these periods correspond to H1, H4, H12, D1, approximately D2.5, W1, and approximately one calendar month respectively. The MMD indicator computes these cloud bands internally; the EA reads the resulting MMD bias output (bullish / bearish / neutral) rather than computing multi-timeframe logic itself.

**Tick chart deferred to v2.** `strategy.md` mandates tick charts for several PAC components: the Reversal Zone, Double Top and Double Bottom patterns, Spike & Move entries, and Measured Move timing precision. v1 uses M5 bars only for three reasons. First, tick chart data quality is broker-dependent in retail CFD trading — feed availability, replay fidelity, and tick chart rendering vary substantially across MT5 brokers (`literature_comparison.md §14`). Second, Phase 4 Strategy Tester requires price history in a standardised format: M5 OHLCV history is universally available and consistent across broker history servers, whereas tick-level data for the Strategy Tester is not reliably complete on most platforms. Third, the four PAC components that require tick charts are all described within §6 setup types where M5-bar entries remain tradable, just with lower timing precision — the setups are still identifiable and executable on M5, only the entry refinement is degraded. Tick chart support is listed as an §0.5 open question for v2.

---

### §2.3 Polish-Local Session Windows

The PAC trading community uses Polish local time as the standard reference for session definitions, as established in `strategy.md` "Session Objective & Session Boxes." Sessions are defined in Polish local time — CET (UTC+1) in winter, CEST (UTC+2) in summer. The EA must convert from MT5 server time to Polish local time using DST-aware logic at runtime. Fixed UTC offsets (+1 or +2 hard-coded) will produce incorrect session-boundary calculations around DST transitions and must not be used.

| Session | Start (Polish local) | End (Polish local) | Activity share | Notes |
|---|---|---|---|---|
| Asia | 23:00 | 07:59 (next day) | ~3% | Wraps midnight. Asia trading deferred to v2 — direction filter for context only in v1. |
| London | 08:00 | 13:59 | ~48% | Primary European window. |
| America | 14:00 | 21:59 | ~48% | US session. Highest volatility. |
| Dead | 22:00 | 22:59 | 0% | Off-hours. No trading permitted. |

Activity-share percentages are drawn from `chatdump_analysis/PHASE_0_REPORT.md` setup distribution highlights: London and America together account for approximately 95% of all catalog setups; Asia-session entries are rare.

**DST handling:** In 2026, the CET→CEST transition occurs on Sunday 29 March at 02:00 CET (clocks move forward to 03:00). The CEST→CET transition occurs on Sunday 25 October at 03:00 CEST (clocks move back to 02:00). Rather than hard-coding these dates, the EA derives the correct UTC offset from the current date using the last-Sunday-of-March and last-Sunday-of-October rule: during the period from the last Sunday of March through (but not including) the last Sunday of October, the offset is UTC+2 (summer/CEST); outside that period, the offset is UTC+1 (winter/CET). The EA obtains current UTC time via `TimeGMT()` and adds 1 or 2 hours as derived from the rule above to produce Polish local time. Hard-coded transition dates (e.g., `if year == 2026 && month == 3 && day == 29`) are explicitly prohibited — the rule-based computation ensures correctness across years without requiring annual config updates. EA input: `TimezoneOverride` (optional string, default `auto`). When set to a numeric value (e.g., `"2"` for UTC+2), the EA bypasses the DST computation and uses the specified fixed offset. This is intended for testing and backtesting scenarios only — it must not be left active in live deployment.

---

## §3 Direction Filter

The direction filter is the first gate in the PAC entry pipeline. Before any signal candle (§4), entry logic (§5), or stop/target calculation (§7) is evaluated, the EA must establish a directional bias — bull or bear — on the current bar. If no clear bias can be established, the EA outputs `neutral` and all downstream gates are bypassed without evaluation for that bar.

The direction filter is composed of four independent sub-components (§3.1–§3.4), each of which produces a typed output. §3.5 defines the composite rule that combines those four outputs into a single `direction: bull|bear|neutral` signal passed to §4.

---

### §3.1 EMA 21 / SMA 61 Sentiment

**Rule:** Sentiment is classified by comparing the current M5 bar's close price against two moving averages — an EMA(21) and an SMA(61) — both computed on M5 close prices. Sentiment is `bull` when the close is strictly above both moving averages; `bear` when the close is strictly below both; `transitional` (no entry signal) when the close is between the two averages regardless of which average is higher. A "dynamic cross" event is flagged separately when price moves impulsively from one side of both averages to the other within `dynamic_cross_max_bars` bars — this is not itself a direction signal, but it marks a tradeable retest opportunity that the §4 signal-candle logic can use to trigger a retrace entry. The EMA(21) and SMA(61) represent fast and medium-term momentum respectively; their combined reading filters out the highest-noise portion of M5 price action while remaining sufficiently responsive to intraday trend changes.

**Inputs:** `bars[]` (M5 OHLC, minimum 62 bars of history required for SMA initialisation); `iMA(symbol, PERIOD_M5, 21, 0, MODE_EMA, PRICE_CLOSE)` handle (EMA21); `iMA(symbol, PERIOD_M5, 61, 0, MODE_SMA, PRICE_CLOSE)` handle (SMA61). Sentiment check uses bar 0 close (current forming bar). Dynamic-cross check requires the close values at bars 0, 1, and 2.

**Output:** `sentiment: bull|bear|transitional`; `dynamic_cross: bool` (true when price crossed both MAs impulsively within `dynamic_cross_max_bars` completed bars, crossing from below-both to above-both or vice versa).

**Quantitative thresholds:**

| Threshold | Default | Source |
|---|---|---|
| ema_period | 21 | strategy.md "Moving Averages" |
| sma_period | 61 | strategy.md "Moving Averages" |
| dynamic_cross_max_bars | 2 | review.md "Moving Averages" — cross must be impulsive and fluid, not a sideways meander; 2-bar window enforces decisiveness |

**Mentor data anchor:** 35 mentor / 287 student (10.9% share). `component_frequency.md` row 10. EMA 21 / SMA 61 is the top-2 most-cited component in the entire corpus by mentor reference frequency, confirming it is a core rather than peripheral PAC element.

**Automation feasibility:** Trivial. Both `iMA` handles are standard MQL5 indicator handles with no external dependencies. Dynamic-cross detection requires maintaining a small 3-bar close history (bars 0, 1, 2) and checking that close[1] or close[2] was on the opposite side of both MAs from close[0] — a handful of comparison operations per tick with no looping. No external data feed or indicator attachment required.

**Drop trigger:** Drop the sentiment filter if Phase 4 backtest shows that trades taken without the sentiment filter (`transitional` bars included) produce equal or higher aggregate edge than trades restricted to `bull`/`bear` bars. The `transitional` state is deliberately conservative and may be rejecting borderline-profitable setups near the MAs; if the backtest shows an excessive false-rejection rate on `transitional` bars, revisit the `transitional` → `neutral` mapping in §3.5 before dropping the component entirely.

---

### §3.2 MMD Cloud Confluence

**Rule:** The MMD (Magic Moving Averages) cloud system produces three primary cloud bands — Orange (period 48), Blue (period 288), and Green (period 1440) — which on an M5 chart correspond to H4, D1, and W1 trend respectively. Each cloud band is a price level: when price is above the cloud, that timeframe is bullish; below is bearish. Cloud "stacking" is the alignment of all three bands in the same directional relationship to price. When all three cloud values are below the current close (clouds stacked below price), higher-timeframe trend is bullish and MMD alignment is `confirmed` relative to a bull §3.1 sentiment. When two of three are aligned with §3.1 sentiment and one disagrees, MMD alignment is `weakened` — trades are still permitted in non-strict mode but logged as reduced-conviction. When all three cloud values disagree with §3.1 sentiment (fully opposite stacking), MMD alignment is `vetoed` and no trade fires regardless of EA mode. This three-level output distinguishes the MMD filter from a binary on/off gate and allows the EA to carry graded-conviction information downstream through §3.5.

**Inputs:** MMD indicator handle loaded via `iCustom` (see `NFA/MMD/MMD_CLOUDS.md` for indicator parameter specification); Orange cloud value at bar 0 (period-48 band); Blue cloud value at bar 0 (period-288 band); Green cloud value at bar 0 (period-1440 band). Current M5 close price for direction comparison.

**Output:** `mmd_alignment: confirmed|weakened|vetoed`.

**Quantitative thresholds:**

| Threshold | Default | Source |
|---|---|---|
| mmd_main_cloud_periods | [48, 288, 1440] | MMD_CLOUDS.md "Cloud Table" — Orange, Blue, Green bands |
| mmd_veto_threshold | all 3 clouds opposite to §3.1 sentiment | MMD_CLOUDS.md "Trend Reading" — full counter-stack is the veto condition |
| mmd_weakened_threshold | 1 of 3 clouds aligned with sentiment, 2 opposed | implicit from above (complement of confirmed and vetoed states) |

**Mentor data anchor:** 0 mentor / 16 student. `component_frequency.md` row 28. The zero mentor reference count reflects two distinct factors: (a) mentor under-detection per §0.2 caveat — the corpus captures only 8 mentor trade-call rows of 167 total, so mentor-reference frequency for specialist indicators is structurally suppressed; and (b) MMD is documented as a separate sibling analytical framework in `NFA/MMD/MMD_CLOUDS.md` rather than referenced inline by mentors during PAC-specific trade calls. The MMD filter is included here as a PAC-essential override because `strategy.md`'s "Trend or Range Day Classification" section explicitly cites MMD for trend-or-range classification — its inclusion is strategy-doc-mandated, not frequency-inferred.

**Automation feasibility:** Requires the MMD indicator to be attached to the chart or loaded as a background `iCustom` handle. Source implementations exist in `NFA/MMD/mt4/` (MQL4) and `NFA/MMD/pine/` (Pine Script); the PAC EA reads the three cloud values per bar from the indicator output buffer — no cloud recomputation is performed by the EA itself. Phase 2 work item: if the existing MQL4 source has not yet been ported to MQL5, either port it directly or establish an MQL4→MQL5 inter-platform bridge. The three cloud values are buffer reads — computationally trivial once the handle is initialised. Flag: if the MMD indicator cannot be loaded at EA initialisation (e.g., indicator file not present on the broker's data directory), the EA must fall back to `mmd_alignment = weakened` rather than blocking all trades — log the fallback prominently.

**Drop trigger:** Drop the MMD confluence filter if Phase 4 backtest shows that the `vetoed` state eliminates more high-edge setups (positive-expectancy trades that were blocked) than low-edge ones (trades that would have lost had they been taken). The `weakened` state is non-binding in the default rule (§3.5 allows it in strict mode), so the principal risk is the `vetoed` state being overly aggressive. Evaluate by comparing the equity curve of the `vetoed` trades in isolation — if they are net-positive, the veto is destroying edge.

---

### §3.3 D1 OHLC Promo Zone

**Rule:** The previous calendar day's D1 bar OHLC defines two "promotional zones" — directional bias areas derived from the relationship between the day's open, close, high, and low. For a bearish D1 day (close < open): the upper wick zone (from the session open down to the candle body top, i.e., between `Open` and `High`) is the sellers' promotional zone — price was pushed up into that region and rejected, making it a structurally favoured area for short setups. The lower wick zone (between `Low` and the candle body bottom, i.e., between `Low` and `Close`) is the buyers' promotional zone — buyers defended that area, making it structurally favoured for long setups. The body itself (between `Open` and `Close` on a bearish D1) is a "neutral" zone: no clear directional bias, as the body represents the range over which neither side achieved a decisive push. For a bullish D1 day (close > open), the zones mirror: sellers' promo is the upper wick (`High` to `Close`); buyers' promo is the lower wick (`Open` to `Low`); body is neutral. The first time price visits a promo zone within the current trading day carries the highest reaction probability; subsequent visits to the same zone within the same day are progressively weaker and are tracked separately via the `first_touch` variant outputs. The intent is to align M5 entries with the directional "promotion" implied by the prior day's market structure.

**Inputs:** Previous D1 bar values via `iHigh(symbol, PERIOD_D1, 1)`, `iLow(symbol, PERIOD_D1, 1)`, `iOpen(symbol, PERIOD_D1, 1)`, `iClose(symbol, PERIOD_D1, 1)`. Current M5 bar close for zone classification. Per-symbol state struct tracking which promo zones have been touched within the current calendar day (reset at the start of each trading day, not at each session boundary).

**Output:** `d1_zone: bull_promo|bear_promo|neutral|first_touch_bull_promo|first_touch_bear_promo`. The `first_touch_*` variants are emitted only on the first M5 bar that closes inside the respective promo zone after the daily reset; subsequent touches emit the non-prefixed variant.

**Quantitative thresholds:** None numeric. Zone classification is a purely binary determination from D1 OHLC geometry — a price is either inside the wick band or inside the body or outside both (which maps to `neutral` on the current day before price has reached either promo zone). No pip buffer, no ATR scaling.

**Mentor data anchor:** 1 mentor / 19 student. `component_frequency.md` row 22. The low mentor count reflects the §0.2 under-detection caveat. D1 OHLC analysis is a `strategy.md` "OHLC Analysis (D1)" staple — it is categorised in the curriculum as a foundational daily-bias tool, not an optional overlay — making frequency under-representation an artefact of the parse rather than evidence of low importance.

**Automation feasibility:** Trivial. Fetching previous D1 OHLC requires four MQL5 history calls, each returning a single value. The zone classification is four floating-point comparisons. "First touch" tracking requires a small per-symbol state struct with two boolean flags (`bull_promo_touched_today`, `bear_promo_touched_today`) and a date field for the reset check. Total state footprint per symbol: ~24 bytes. No external data, no multi-timeframe indicator, no iCustom dependency.

**Drop trigger:** Drop the D1 promo filter if Phase 4 backtest shows that D1 zone alignment contributes zero incremental edge — i.e., the win rate of trades taken inside a D1 promo zone is statistically indistinguishable from the win rate of trades taken in the D1 body or neutral zone, after controlling for §3.1 sentiment and §3.4 session-box position. If the `first_touch_*` variants show edge but the non-prefixed variants do not, demote non-first-touch entries to a lower-priority subtype rather than dropping the component entirely.

---

### §3.4 Session Box Position

**Rule:** Each active trading session has a "session box" defined by the highest high and lowest low printed during that session's time window (§2.3). For the London session the box accumulates from 08:00 PLT until the current M5 bar; for the Asia session the box accumulates from 23:00 PLT on the prior calendar day through 07:59 PLT. Price above the session box at the time of a trade signal indicates upper-side bias — participants from subsequent sessions are inheriting an up-close — and favours long setups. Price below the session box indicates lower-side bias and favours short setups. Price inside the box is a "wait" state: the range is still being established, or price is digesting within established limits, and the directional implication is unclear. Clean breakout beyond the box edge — defined as the current M5 close printing strictly outside the box with no part of the body inside — is preferred over a wick-only poke. If the box range (high minus low) is below the narrow-box threshold (0.5 × ATR(20)), the session is classified as a range or consolidation session and the entire session-box filter returns `inside` regardless of where price sits relative to the box, because a very narrow box does not provide meaningful positional information. The Asia box is computed for contextual reference during London and America sessions — it is not used as the primary filter because Asia trading is deferred to v2 (§2.3). The London box is the primary session-box filter during both the London and America session windows.

**Inputs:** Real-time tick-by-tick high/low tracking within the session window, maintained as a per-symbol, per-session state struct. For box-edge comparison: current M5 bar close (bar 0). For ATR filter: `iATR(symbol, PERIOD_M5, 20, PRICE_CLOSE)` handle; ATR value at bar 1 (most recent completed bar). Session boundary timestamps in UTC derived from PLT session windows via the DST logic in §2.3.

**Output:** `session_box_position: above|inside|below`; `box_range_pips` (numeric, exposed for diagnostic logging and for the narrow-box filter computation).

**Quantitative thresholds:**

| Threshold | Default | Source |
|---|---|---|
| min_box_range_atr_multiple | 0.5 | review.md "Session Boxes" — skip sessions with a narrow consolidation box; 0.5 × ATR(20) is the minimum meaningful range |
| breakout_threshold_pips | 0 | strategy.md implicit — price above or below the box edge with no buffer; a strict close outside the box is required but no additional pip buffer |

**Mentor data anchor:** 7 mentor / 68 student (9.3% share). `component_frequency.md` row 16. The 7 mentor references represent one of the higher mentor-citation counts among the direction-filter components, consistent with session boxes being a prominent structural concept in the PAC curriculum ("Session Objective & Session Boxes" is one of the strategy.md primary sections).

**Automation feasibility:** Straightforward. The session box state struct tracks two floats (session high, session low) and a datetime for the session-start reset. Updated on every M5 bar open by comparing the new bar's high/low against the stored session high/low. The narrow-box filter adds a single ATR comparison: `if (session_high - session_low) < (0.5 × ATR_value) then return inside`. No external data or iCustom dependency. DST-correct session boundaries are inherited from the §2.3 time-conversion module — no additional time logic required in this component.

**Drop trigger:** Drop the session-box filter if Phase 4 backtest reveals either of two failure modes: (a) narrow-box sessions dominate the loss population — the filter is removing too many otherwise-valid setups by blocking all trades in a narrow session; or (b) breakout-after-narrow-box setups dominate the win population — the filter is wrongly classifying the most profitable setup type as `inside`. In failure mode (a), raise `min_box_range_atr_multiple` to reduce the narrow-box trigger rate. In failure mode (b), add a specific `narrow_box_breakout` sub-state rather than dropping the filter wholesale.

---

### §3.5 Composite Direction Rule

Sections §3.1 through §3.4 each produce an independent typed output. The EA combines these four outputs into a single `direction: bull|bear|neutral` signal using the rule below. A configurable strictness input governs how many sub-filters must agree before a directional signal is issued; the rule is written for the default strict mode (`direction_strict = true`) and the relaxation behaviour for loose mode is described separately.

**Composite rule (strict mode, `direction_strict = true`):**

```
direction = "bull"   iff ALL of:
    sentiment(§3.1)                == bull
    AND mmd_alignment(§3.2)        in {confirmed, weakened}      // vetoed blocks entirely
    AND d1_zone(§3.3)              in {bull_promo, first_touch_bull_promo, neutral}
    AND session_box_position(§3.4) != inside                     // above or below, not ranging

direction = "bear"   iff ALL of:
    sentiment(§3.1)                == bear
    AND mmd_alignment(§3.2)        in {confirmed, weakened}      // vetoed blocks entirely
    AND d1_zone(§3.3)              in {bear_promo, first_touch_bear_promo, neutral}
    AND session_box_position(§3.4) != inside

direction = "neutral"   otherwise
    → no entry trigger fires; §4 signal-candle evaluation is bypassed for this bar
```

**EA input parameter — `direction_strict: bool` (default `true`):** When `true`, all four sub-filters must pass per the rule above. When `false`, only §3.1 sentiment is required to determine direction; §3.2 MMD alignment, §3.3 D1 zone, and §3.4 session-box position become advisory — they are evaluated and logged as graded-conviction metadata but do not gate the direction output. Loose mode is intended for backtesting diagnostic runs to isolate the incremental contribution of each filter layer; it should not be used in live trading without a completed Phase 4 backtest comparison.

**EA input parameter — `mmd_strict: bool` (default `false`):** Sub-input within the §3.2 MMD gate. When `true`, only `mmd_alignment = confirmed` passes the §3.2 gate; the `weakened` state is treated identically to `vetoed` and blocks the direction signal. When `false` (default), both `confirmed` and `weakened` pass, consistent with the composite rule above. This input is orthogonal to `direction_strict` — it tightens the MMD sub-gate independently of the other three components and remains active even when `direction_strict = false` (in which case it affects only the logged conviction level, not the gate outcome).

**Note on `weakened` in strict mode:** When `mmd_alignment = weakened` and the direction signal passes all other gates, the EA logs the resulting trade entry as a "reduced-conviction" event via the standard Logger module. Phase 4 backtest reports should surface these entries distinctly so the operator can evaluate whether the `weakened` cohort is contributing positive expectancy.

**Note on `neutral` D1 zone:** The D1 "maybe" zone (price inside the previous day's body) is not a directional veto. Trades can fire in either direction when `d1_zone = neutral`, subject to all other gates passing. This is intentional: the D1 body represents an area where neither buyers nor sellers achieved a promotional push — it is structurally agnostic, not structurally opposed. The composite rule reflects this by including `neutral` in both the bull and bear filter lists. When `d1_zone = neutral`, the §3.4 session-box position carries proportionally more weight in the overall conviction assessment, because the D1 layer is providing no bias signal of its own.

---

## §4 Entry Trigger

The entry trigger is the second gate in the PAC entry pipeline, evaluated only after §3 issues a non-neutral `direction` signal. An entry trigger requires all three sub-components to pass simultaneously: a signal candle (§4.1) conforming to the geometric rejection pattern, the candle positioned on the correct side of EMA21 (§4.2), and the candle's rejection wick falling within proximity of an active Target Engine level (§4.3). All three conditions are conjunctive — passing two of three is not an entry. Each sub-component is evaluated at new-bar events only (not on every tick) to avoid triggering on a partially formed bar.

---

### §4.1 Signal Candle Definition

**Rule:** A signal candle carries a prominent wick on the side OPPOSITE its body direction, indicating that price tested a level in one direction and was sharply rejected back. A bullish signal candle has a prominent lower wick — price pushed down, found sellers absent or buyers defending, and closed back up in the upper portion of the bar's range, leaving a long lower shadow as the rejection footprint. A bearish signal candle has a prominent upper wick — price was driven up, met selling pressure, and closed back down in the lower portion of the bar's range. The wick must be visually dominant per the quantitative thresholds below: it must be at least 2× the body length, the candle's total range must be at least 0.5 × ATR(20) to exclude micro-candle noise, and the close must sit within the third of the range opposite the rejection wick. The signal candle is the entry trigger geometry but is meaningless in isolation — it requires §4.2 (EMA-side) and §4.3 (confluence) gates to also pass before any order fires.

**Inputs:** Current closing bar OHLC — bar 1, the most recently closed bar. The EA evaluates signal-candle status at each new-bar event, NOT on every tick. This prevents premature triggering during bar formation: a candle that temporarily looks like a valid rejection wick during an intrabar spike may resolve into a different shape by close. ATR(20) value at bar 1 from the shared `iATR` handle (§3.4 same handle).

**Output:** `signal_candle: bullish|bearish|none`.

**Quantitative thresholds:**

| Threshold | Default | Source |
|---|---|---|
| wick_to_body_ratio_min | 2.0 | review.md "Signal Candle" — "wick must be at least 2× the body length" |
| candle_range_atr_multiple_min | 0.5 | review.md "Signal Candle" — "candle range ≥ 0.5 × ATR(20)" prevents micro-candle noise |
| close_position_within_wick_pct | 33 | review.md "Signal Candle" — bullish must close in upper third (close ≥ low + 0.67 × range); bearish close in lower third |

**Mentor data anchor:** 2 mentor / 6 student (25.0% share). `component_frequency.md` row 17. **CRITICAL CAVEAT:** Suspiciously low absolute mentor count. The Phase 0 keyword classifier appears to under-detect signal-candle references — the term "signal candle" / "signalka" / "sygnałówka" appears rarely as standalone vocabulary in trade-call messages because mentors typically reference the GEOMETRY rather than the NAME ("ładna świeca z dolnym knotem na EMA"). The EA does NOT rely on chat references — it computes signal-candle status directly from bar OHLC via the geometric thresholds above, which is robust regardless of how mentors talked about them. Inclusion of signal_candle is per the curriculum-essential override in the design spec.

**Automation feasibility:** Trivial — bar OHLC arithmetic. The wick-to-body ratio = `max(top_wick, bottom_wick) / body_size` where `body_size = abs(close - open)`. Top wick = `high - max(open, close)`; bottom wick = `min(open, close) - low`. ATR-relative range check = `(high - low) >= candle_range_atr_multiple_min * iATR(20)`. The close-position-within-wick check enforces that the candle closed near the body extreme opposite the rejection wick: for bullish, `close >= low + 0.67 * (high - low)`; for bearish, `close <= low + 0.33 * (high - low)`. New-bar event triggers via `OnTick()` + bar-change detection (compare `iTime(0)` to cached previous bar time). Note: when `body_size = 0` (a doji), the wick-to-body ratio is undefined — classify doji bars as `signal_candle = none` unconditionally.

**Drop trigger:** Drop the wick-based trigger if Phase 4 backtest shows it underperforms a simpler "close beyond EMA21 + ATR" trigger in both win rate and expectancy. Replace with a tighter geometric set if the false-positive rate (signal fires but no follow-through within 3 bars) exceeds 60% across XAUUSD + USOIL combined.

---

### §4.2 EMA-Side Hard Rule

**Rule:** A bullish signal candle is only valid when the candle's close is strictly ABOVE EMA21. A bearish signal candle is only valid when the close is strictly BELOW EMA21. No exceptions and no override is available. A signal candle whose close sits on the wrong side of EMA21 for its declared direction is rejected outright — this is a binary check, not a configurable threshold. The logic behind this hard rule is directional coherence: a bearish rejection wick that forms above EMA21 is still structurally above the medium-term trend; the market is rejecting a local high but may not have crossed the critical trend line. Conversely, a bullish rejection wick forming below EMA21 has not yet reclaimed trend territory. Allowing entry before the close crosses EMA21 introduces setups that are geometrically correct but structurally premature. The curriculum treats EMA21 as the primary trend separator, so crossing it is the minimum threshold for a directional commitment. Note that the EMA21 handle used here is the same `iMA` handle initialised in §3.1 — no new indicator handle is required.

**Inputs:** Signal candle from §4.1 (`signal_candle: bullish|bearish`). EMA21 value at bar 1 from the §3.1 `iMA(symbol, PERIOD_M5, 21, 0, MODE_EMA, PRICE_CLOSE)` handle. The check uses bar 1 close versus bar 1 EMA21 value — both evaluated at the same closed bar to avoid look-ahead.

**Output:** `signal_valid: bool`. True only when the §4.1 signal candle direction matches its EMA21-side position: bullish signal with close above EMA21, or bearish signal with close below EMA21.

**Quantitative thresholds:** None — binary check. There is no pip buffer, no ATR tolerance, and no softened version of this rule. Close strictly above EMA21 = valid for bullish; close strictly below EMA21 = valid for bearish; close exactly at EMA21 = invalid (probability of exact equality is negligible with floating-point prices, but if it occurs, the signal is rejected).

**Mentor data anchor:** Curriculum rule from `strategy.md "Signal Candle"` section's "EMA 21 directional filter" subsection. Also documented in `literature_comparison.md §1` as a "PAC addition" — this is not classical candlestick analysis but a non-classical PAC-specific filter that reduces signal-candle noise materially. No standalone frequency row in `component_frequency.md` because the EMA-side check is part of the signal-candle definition in the curriculum, not a separately named component.

**Automation feasibility:** Trivial — single floating-point comparison per new-bar event. `signal_valid = (signal_candle == bullish && close[1] > ema21[1]) || (signal_candle == bearish && close[1] < ema21[1])`. The EMA21 buffer value at bar 1 is already being read by §3.1 and is available with no additional indicator call.

**Drop trigger:** This rule should never be dropped — it is curriculum-mandatory. If Phase 4 backtest shows the EMA-side rule degrades edge (extremely unlikely, as structurally premature entries are categorically lower-quality), revisit the EMA21 period parameter in §3.1 first. A poorly calibrated EMA period would manifest as the EMA lagging price and blocking valid retrace entries; the fix is period adjustment, not rule removal.

---

### §4.3 Confluence Requirement

**Rule:** A signal candle that passes both §4.1 and §4.2 only becomes an entry trigger when its rejection wick — the wick in the direction of the trade (lower wick for a bullish signal, upper wick for a bearish signal) — falls within `confluence_pips_threshold` of an active Target Engine level. The active level set comprises all levels currently maintained by the §5 Target Engine: any §5.1 measured-move A, B, C, or D point; any §5.2 Fibonacci retracement or extension level; and any §5.2 detected cluster price. A cluster is an area where two or more Fibonacci or measured-move levels converge within the cluster-tolerance band, and it counts as a single confluence level (albeit a high-conviction one). Standalone signal candles that pass §4.1 and §4.2 but whose wicks are not in proximity to any active level do NOT trigger entries under any configuration — the proximity check is not configurable to `off` in v1. The rationale is PAC's core principle: entries are only taken where the rejection candle forms at a structurally significant price level, not in open space. Without the confluence requirement the EA degenerates into a pure momentum-reversal system with no structural anchor.

**Inputs:** Signal candle from §4.1 (specifically, `candle.low` for a bullish signal, `candle.high` for a bearish signal — the wick extreme that represents the rejection point). EMA-side validity from §4.2 (`signal_valid = true`). Active level set from the §5 Target Engine: all currently live measured-move points (§5.1), all currently live Fibonacci levels and cluster prices (§5.2). `iATR(20)` value at bar 1 for the ATR-scaled threshold.

**Output:** `entry_triggered: bool`. When `true`, also emits `confluence_level: float` (the matched level's price) and `confluence_type: mm_a|mm_b|mm_c|mm_d|fib_retracement|fib_extension|cluster` identifying which level class produced the match.

**Quantitative thresholds:**

| Threshold | Default | Source |
|---|---|---|
| confluence_pips_threshold | 0.3 × ATR(20) | review.md "Fibonacci" — cluster tolerance, reused as the signal-candle-to-level proximity threshold |
| confluence_required_levels | 1 | strategy.md "Signal Candle" + curriculum — single confluence sufficient; a cluster counts as 1 confluence, just a high-conviction instance |

**Mentor data anchor:** No standalone keyword for the confluence requirement in `component_frequency.md` — confluence is the implicit requirement in every PAC entry, captured indirectly by the high mentor frequency of measured_move + signal_candle + fibonacci appearing in combination. The explicit quantitative `confluence_pips_threshold` is a `review.md`-derived rule that makes the implicit requirement algorithmically testable. The 0.3 × ATR(20) proximity threshold is taken directly from the review.md Fibonacci cluster-tolerance recommendation and applied here by analogy — a signal candle wick that reaches within one cluster-width of a level is treated as "touching" it for confluence purposes.

**Automation feasibility:** One helper function `FindNearestLevel(candle_wick_extreme, active_levels[], threshold)` iterates the active level set, computes `abs(candle_wick_extreme - level.price)` for each entry, and returns the closest level within `threshold`. The active level set is a flat array of `{price, type}` structs maintained by the §5 Target Engine — the §4.3 check is a read-only query against that array with no mutation. Time complexity is O(n) where n = number of active levels; expected n < 30 on any single instrument during a session, so performance is not a concern. Phase 2 implementation note: `FindNearestLevel` is a shared utility used by both §4.3 and §5's internal cluster-detection logic — implement once in a shared utility module rather than duplicating.

**Drop trigger:** Drop or relax the confluence requirement if Phase 4 backtest shows it is producing more false negatives than false positives — specifically, if the win rate of logged `entry_triggered=false, signal_valid=true` setups (setups that passed §4.1 and §4.2 but failed §4.3 and were therefore not traded) exceeds the win rate of actually triggered setups. This would indicate the threshold is too tight and is rejecting better-quality trades than it is admitting. First response is to widen `confluence_pips_threshold` from 0.3 × ATR(20) toward 0.5 × ATR(20) before considering removing the level-proximity requirement entirely.

---

## §5 Target Engine

The Target Engine is the sub-system responsible for producing the take-profit (TP) price used when an entry fires. It runs continuously in the background — not only at entry time — maintaining a live map of structurally significant price levels derived from price structure and Fibonacci geometry. Four sub-modules contribute to that map: §5.1 projects the standard 100% measured-move target; §5.2 overlays Fibonacci retracement and extension levels on each active impulse and detects clusters where multiple levels converge; §5.3 extends the projection when price overshoots the §5.1 target; and §5.4 applies a settle buffer to the selected candidate level to produce the actual TP field submitted to `OrderSend`. The §6 Setup Recognition module selects which candidate level becomes the active TP for any given entry; the Target Engine's job is to ensure all well-formed candidate levels are available and current at the moment §6 needs them.

---

### §5.1 Measured Move (AB=CD with EMA-Cross Anchor)

**Rule:** Identify an impulse leg A→B where price begins on one side of EMA21 and ends with a CLOSE on the opposite side. Wicks that merely touch the EMA do not count — the bar at point B must close on the opposite side from where the impulse started at point A. The subsequent pullback B→C must return clearly back to the same side of EMA21 as point A. Project target D such that the price distance C→D equals the price distance A→B (100% expansion). The measured move is INVALID if price retraces beyond C before reaching D — at that point a new impulse must be identified. Multiple measured moves can be active simultaneously; the EA tracks all and the latest valid one provides the primary target.

**Inputs:** Closed bars (bar 1+), `iMA(symbol, PERIOD_M5, 21, 0, MODE_EMA, PRICE_CLOSE)` handle (the same EMA21 from §3.1), a swing-detection helper (see Automation feasibility).

**Output:** `measured_move: {a_bar: int, a_price: float, b_bar: int, b_price: float, c_bar: int, c_price: float, d_target: float, validity: valid|invalid}`. Multiple measured moves can be active simultaneously; the EA tracks all and the latest valid one provides the primary target.

**Quantitative thresholds:**

| Threshold | Default | Source |
|---|---|---|
| impulse_atr_multiple_min | 1.5 × ATR(20) | review.md "Measured Move + Double Up/Down" — minimum impulse size relative to recent volatility |
| ema_cross_close_required | true | strategy.md "Measured Move" — must close on opposite EMA side, wick touch insufficient |
| invalidation_on_c_breach | true | strategy.md "Measured Move" — price breach beyond C voids the MM |
| max_active_measured_moves | 5 | v1 default — prevents unbounded growth of tracked patterns; revisable after Phase 4 |

**Mentor data anchor:** 50 mentor / 310 student (13.9% share). `component_frequency.md` row 9. **Top-1 mentor reference frequency** — measured move is the highest-value PAC concept by mentor mention count.

**Automation feasibility:** Requires a swing-detection helper to identify candidate A and B points. v1 approach: ATR-filtered ZigZag — track recent swing highs and lows where price moved ≥ `impulse_atr_multiple_min × ATR(20)` from the prior pivot. The EMA-cross anchoring is mechanical: for each candidate A→B segment, verify A's bar closed on one side of EMA21 and B's bar closed on the other. Shared helper module in Phase 2 `SignalEngine.mqh` named `DetectImpulses(bars[], ema_handle, atr_min) → list<MeasuredMove>`. C-detection: scan bars after B for the first close back on A's side; the lowest (for bullish MM) or highest (for bearish) close in that scan window becomes C.

**Drop trigger:** Should NOT drop — this is the highest-value PAC concept. If Phase 4 backtest shows poor performance, refine thresholds (raise `impulse_atr_multiple_min`, tighten EMA-cross close requirement) before dropping the whole component. Specifically, target a win rate of ≥40% with average R ≥1.0 across XAUUSD + USOIL combined; below that, escalate to threshold tuning rather than removal.

---

### §5.2 Fibonacci Levels & Clusters

**Rule:** Apply Fibonacci retracement and extension to each active measured-move impulse leg A→B from §5.1. Retracement levels (`fib_levels_retracement`) provide pullback zones used by §6 setup recognition. Extension levels (`fib_levels_extension`) provide additional candidate target levels beyond the §5.1 D target. A CLUSTER forms when ≥`cluster_member_min` levels from DIFFERENT impulses converge within `cluster_pips_threshold` of the same price. Clusters are higher-conviction S/R zones than single levels and §4.3 confluence treats them as a single level (just a high-conviction one).

**Inputs:** All active measured moves from §5.1 (provides the impulse legs), `iATR(20)` (for the cluster threshold scaling), current bar price.

**Output:** `fibonacci_levels: [{price: float, level_ratio: float, source_impulse_id: int, kind: retracement|extension}]` (the full set of active Fibonacci levels) and `clusters: [{price: float, member_count: int, member_levels: list}]` (the detected clusters).

**Quantitative thresholds:**

| Threshold | Default | Source |
|---|---|---|
| fib_levels_retracement | [0.382, 0.5, 0.618] | strategy.md "Fibonacci Levels" |
| fib_levels_extension | [1.382, 1.618, 2.618] | strategy.md "Fibonacci Levels" |
| cluster_pips_threshold | 0.3 × ATR(20) | review.md "Fibonacci" — tightened from strategy.md's "~5 pips" to ATR-relative |
| cluster_member_min | 2 | review.md "Fibonacci" — at least 2 levels must converge |

**Mentor data anchor:** 16 mentor / 190 student (7.8% share). `component_frequency.md` row 14. Tied with `spike_channel` at 16 mentor refs.

**Automation feasibility:** Trivial level computation once §5.1's swing detection is in place. Cluster detection = pairwise distance check among current level set: for each pair of levels, if `abs(price_1 - price_2) ≤ cluster_pips_threshold`, group them into a cluster. Phase 2 implementation note: use a sweep-line algorithm on sorted levels for O(n log n) cluster detection if the level set grows large; for v1 the level count is bounded by `max_active_measured_moves × 6 levels = 30`, so O(n²) is fine.

**Drop trigger:** Drop standalone Fibonacci levels (keep only clusters) if Phase 4 backtest shows non-cluster levels add noise — specifically, if setups triggered on a single non-cluster Fibonacci level have win rate < 30%. The cluster mechanism itself should not drop — it is the only filter preventing the "blanket the chart with levels" curve-fit concern flagged in `review.md "Fibonacci"`.

---

### §5.3 Extended Measured Move (138.2% / 161.8%)

**Rule:** When price overshoots the standard 100% measured-move target D from §5.1 by `overshoot_bars_min` consecutive bars without retracing back to D, the EA computes an EXTENDED target using external Fibonacci at 138.2% or 161.8% of the original A→B range. The extended target is the next candidate TP. Price should stop within the 138.2%–161.8% range; beyond 161.8% is exhaustion territory. After the extended move completes (price reaches and reacts at 138.2% or 161.8%), any correction is measured from the ENTIRE move (A→extended_target), not just the original A→B→C→D.

**Inputs:** Active measured moves from §5.1 (must have reached 100% target D), bars[], `iATR(20)`.

**Output:** `extended_target: float | None`. None when no active MM has overshot yet.

**Quantitative thresholds:**

| Threshold | Default | Source |
|---|---|---|
| overshoot_bars_min | 3 | v1 default — needs Phase 4 backtest tuning; "several candles past D" is the strategy.md qualifier, 3 is a starting interpretation |
| extended_target_levels | [1.382, 1.618] | strategy.md "Extended Measured Move" |
| extended_target_priority | 1.382 first, then 1.618 | strategy.md "Extended Measured Move" — conservative first |

**Mentor data anchor:** Subsumed under the §5.1 measured_move count (50 mentor refs total). Extended MM is a sub-pattern of measured move and not separately classified in `component_frequency.md`.

**Automation feasibility:** Requires a small state machine on top of §5.1: track whether each active MM has reached its D target, and if so, count consecutive bars beyond D. When that counter exceeds `overshoot_bars_min`, emit the extended target. State struct: `{mm_id: int, reached_d: bool, bars_past_d: int}` per active MM.

**Drop trigger:** Drop extended-target projection if Phase 4 backtest shows price rarely reaches 138.2% reliably from the overshoot trigger point. Specifically, if fewer than 50% of overshot MMs reach 138.2% within 50 bars of the overshoot trigger, the projection is not predictive.

---

### §5.4 Settle Buffer

**Rule:** When placing the take-profit order, the EA settles a few pips/ticks before the projected target to account for spread, slippage, and other market participants who will exit at or near the same level. The actual TP price is `target_price - settle_buffer` for long positions and `target_price + settle_buffer` for short positions.

**Inputs:** Target price from §5.1 D target, §5.2 cluster price, or §5.3 extended target (whichever §6 setup recognition selects as the active TP).

**Output:** `actual_tp_price: float` — the price the `OrderSend` TP field is set to.

**Quantitative thresholds:**

| Threshold | Default | Source |
|---|---|---|
| settle_buffer_atr_multiple | 0.5 × ATR(20) | review.md / strategy.md "Settle the trade a few pips before target" |

**Mentor data anchor:** Universal practice per strategy.md — every PAC trade execution exits before the target. Not separately classified in `component_frequency.md`.

**Automation feasibility:** Trivial — single subtraction (long) or addition (short) on the target price. Apply at `OrderSend` time (§7.2 order placement).

**Drop trigger:** Tune `settle_buffer_atr_multiple` in Phase 4 backtest. Should not drop the rule — settling early is universal practice — but the buffer size should be tuned per instrument class if backtest reveals clear differences (e.g., gold may need a wider buffer than EURUSD).
