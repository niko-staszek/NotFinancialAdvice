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
