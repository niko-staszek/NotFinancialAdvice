# ORB Strategy — Quantified Spec

**ORB = "Opening Range Breakout"** — bias-gated, index-only. Define the first 15 minutes
of the NY cash open as the day's opening auction range, then trade a breakout of that
range **only in the direction of a higher-timeframe trend bias**, and **only when
participation (relative volume) confirms**. Intraday, flat by the close, no overnight.

**Source:** original design synthesis (this repo, design session 2026-06-21). Not
transcribed from a video. Informed by the documented ORB literature (Zarattini & Aziz,
*"Can Day Trading Really Be Profitable"*, 2023 — 5-min ORB on US equities, RVOL-filtered)
and by this repo's own prior result on the same family (see §13, IVB).

**Status:** TESTED — **REJECTED (no generalizable edge)**, 2026-06-22. The path matters:
(1) an initial walk-forward read REJECT (Sharpe −0.20) but via a **harness bug** — per-window
OOS runs restart the 14-day RVOL warmup, dropping ~30% of each OOS window; (2) corrected
**continuous** OOS test (fixed spec default S0/E0/RVOL≥1.0, span 2022-10→2026-04) showed US100
**PASSES** (PF 1.14, Sharpe(t) +1.04; runner E3 PF 1.54 / +2.14); (3) **cross-instrument is
decisive — same config + method: US100 passes (+1.04/+2.14) but US500 FAILS (−1.06/−0.04) and
US30 FAILS (−1.30/+0.42).** Positive on the single most-volatile/most-trending index only,
negative on the two correlated peers → **not a robust edge** — Nasdaq-specific trend/volatility
exposure (n=1 instrument = cherry-pick risk). Matches ETR (worked only on gold/BTC, failed the
basket) and the breakout-family prior. **Do not deploy.** Evidence:
`reports/ORB-fullperiod-20260622/` (gate_cross_instrument.txt + ledgers). The deterministic
kernel and the research pipeline (codified gate, headless tester, EA framework) are built,
validated, and reusable — the *edge* is not there. (`sharpe()` = per-trade t-statistic, not
annualized equity Sharpe.)

**Goal (this phase):** research-first. Settle whether ORB has real, out-of-sample edge on
US100 before any FTMO deployment. Success = clears the repo validation gate
([docs/strategy-validation.md](../docs/strategy-validation.md)) net of costs. FTMO prop
rules are documented (§9) but non-binding until edge is proven.

---

## §1 Core thesis

The first 15 minutes after the NY cash open is the day's most informationally dense
auction: overnight orders, economic releases, and institutional positioning all clear
into one range. A break **out of that range, in the direction of the prevailing trend,
backed by above-average volume** reflects *acceptance* of a new price area — an opening
drive that tends to continue.

The edge, if any, lives in the **filters**, not the breakout itself:

- **Bias gate** removes counter-trend false breaks (a break of the range *against* the
  daily trend is the most common fakeout).
- **RVOL gate** removes low-participation breaks (no volume = no conviction = noise).

Pure both-ways ORB is the weakest survivor in this repo's meta-study (breakout/trend
family ≈ 18–22% survival vs mean-reversion ≈ 38%; see
[strategy-validation.md §4](../docs/strategy-validation.md)). This spec is the
**bias-gated, participation-filtered subset** — the one with a microstructure reason to
survive — built to be *failed fast* if it does not.

---

## §2 Instrument & session

| Item | Value | Notes |
|------|-------|-------|
| Dev instrument | **US100.cash** (FTMO Nasdaq-100 CFD) | highest intraday volatility + cleanest momentum = best breakout signal-to-noise |
| Cross-validation | US500.cash, GER40.cash | §10 — frozen params, free OOS robustness check |
| Cash open | **09:30 ET** (NY) | the volume spike; NOT the CFD's ~23h session start |
| Cash close / EOD flat | **16:00 ET** | hard-flatten, no overnight |
| Broker | FTMO-Demo | server time = **GMT+2 (EET, winter) / GMT+3 (EEST, summer)** |

**Time-zone handling.** Anchor everything to **exchange local time (ET)** and convert to
broker server time in code. 09:30 ET ≈ **16:30 server** and 16:00 ET ≈ **23:00 server**
*most* of the year, because US and EU DST shift together — **except** the ~2–3 week
windows each spring/autumn where the two DST transitions are misaligned, during which the
offset drifts by 1h. The EA must compute the offset from a true ET clock, not hardcode
16:30 server.

---

## §3 Opening range

- **OR window = 09:30–09:45 ET** (first 15 minutes). Walk-forward alternative: **M30**
  (09:30–10:00 ET).
- `OR_high` = highest high in the window; `OR_low` = lowest low; `OR_width = OR_high − OR_low`.
- `OR_mid = (OR_high + OR_low) / 2`.
- Defined by the 09:30–09:45 *clock window* regardless of chart timeframe (one M15 bar, or
  three M5 bars).

---

## §4 Bias gate (directional filter)

Only the trend-aligned side is armed each day:

- Compute **EMA(50) on the D1 chart** of US100.
- **Prior completed daily close > EMA50 → LONG-only today.**
- **Prior completed daily close < EMA50 → SHORT-only today.**

The opposite-side breakout is ignored entirely. This is the single most important filter
in the spec — it removes the counter-trend fakeout, the dominant ORB failure mode.

- Tuned parameter: **bias EMA length ∈ {20, 50, 100, 200}**, default 50.
- *Alternative to test (not v1):* opening-location bias — open above prior-day high → long,
  below prior-day low → short (gap-and-go). Documented for a later variant; v1 uses the D1
  EMA for simplicity (one parameter).

---

## §5 Participation gate (RVOL) + range guard

**Relative volume (RVOL).**
- `RVOL = (tick volume of the 09:30–09:45 ET window) ÷ (median tick volume of the same
  09:30–09:45 window over the trailing 14 sessions)`.
- **Gate: arm the trade only if RVOL ≥ 1.5.** Tuned ∈ {1.0–2.0}.
- **Honest caveat:** US100.cash is a CFD — its "volume" is **tick volume** (count of price
  changes), not true exchange volume. On indices this tracks the underlying futures
  reasonably well, so it is a usable proxy — but it is a proxy, not ground truth. RVOL is
  weaker here than it would be on a real-volume futures feed.

**Range guard (news/gap protection).** Skip the day entirely if the opening range is
abnormal vs its own recent history:
- Skip if `OR_width > 2.0 × median(OR_width, last 14 sessions)` — gap/news blow-off, the
  range is already the move.
- Skip if `OR_width < 0.5 × median(OR_width, last 14 sessions)` — dead/holiday session, no
  energy.

(Self-referential to recent OR widths — scale-correct, unlike comparing a 15-min range to a
daily ATR.)

---

## §6 Entry

- **Stop order on the bias-aligned side only:**
  - LONG bias → **buy-stop at `OR_high + buffer`**.
  - SHORT bias → **sell-stop at `OR_low − buffer`**.
- `buffer = 0.1 × OR_width` (small, to avoid wick triggers). Fixed, not tuned in v1.
- **One trade per day, maximum.** One order, one side.
- **Entry window:** order armed at 09:45 ET, valid until **11:30 ET**. If unfilled by
  11:30, cancel — no late-session entries (the opening-drive thesis has expired).

---

## §7 Stop loss — a compared dimension

SL placement is *not* assumed; it is one of two things the walk-forward decides (see §8 and
§10). `R` is defined per-arm as `R = |entry − SL|`, so all targets scale consistently.

| Arm | Stop loss | Hypothesis |
|-----|-----------|------------|
| **S0** | **Opposite OR end** (LONG SL = `OR_low`; SHORT SL = `OR_high`) | Structural invalidation — thesis ("accepted outside the range") dies only when price reclaims the whole range. Robust to retests. **Prior favourite.** |
| **S1** | **OR midpoint** (`OR_mid`) | Halves the stop → doubles RR ("2:1"). Wins *only if* US100 opens are gap-and-go with no retrace. Risk: the midpoint sits in the throwback zone where breakouts routinely pull back, so win-rate may crater below the breakeven that the better RR implies. |
| **S2** | **k × ATR(14) on M15** (risk-normalized) | Normalizes stop distance across volatile/quiet days. Controls wide-OR risk. k tuned ∈ {1.0–1.5}. |

**Design note (why S1 is not the default despite "2:1"):** a tighter stop does not
manufacture edge — it trades win-rate for reward-to-risk. At 1:1 you need >50% wins; at
2:1 only >33%. But if the midpoint stop drops the win rate from ~50% to ~30% (retests are
common on index opens), you fall *below* the 33% breakeven and are worse off. With fixed
1%/trade risk, the tighter stop also does **not** risk more dollars — it just doubles
position size and doubles stop-out probability. Stop placement should mark where the trade
is *wrong* (structural), not be chosen to hit a target RR. S0 is the default; S1 is tested
because the gap-and-go case is real and only data settles it.

**Wide-OR cap:** the §5 range guard already removes the widest days; S2 additionally caps
risk on borderline-wide days.

---

## §8 Exit — a compared dimension (exit study)

Exit is the second compared dimension. Baseline first, runners only if the baseline shows
life.

| Arm | Mechanic | Role |
|-----|----------|------|
| **E0** | Fixed **1R** (1:1) | banker baseline — the bar every runner must beat |
| **E1** | Fixed **K×R**, K ∈ {2, 3} | does naively letting it run pay? |
| **E2** | **Partial 50% @ 1R, trail remainder on EMA(M15) close-cross** | "bank the 1:1, ride the rest as house money" — the mechanical encoding of the runner idea |
| **E3** | Full position, **EMA(M15) close-cross**, no fixed TP | pure trend-ride |
| **E4** | E2/E3 but with **EMA21(M15)** instead of EMA8 | smoother-trail check (EMA8 on M15 is fast/whippy) |

Rules binding **all** exit arms:

- **Runner exit is defined as an M15 candle that *closes* beyond the EMA against the
  position** (LONG: M15 close < EMA; SHORT: M15 close > EMA). A close-through, **not** a
  wick touch.
- Trail EMA length: tuned parameter ∈ **{8, 21}**.
- **EOD flat at 16:00 ET overrides everything.** A runner still hard-closes at the cash
  close. No overnight, ever.
- **E0 is the permanent control.** If no runner arm beats plain 1R *net of costs*, the
  runner is adding variance, not edge — ship E0.

---

## §9 Risk

**Research phase (now):**
- Fixed fractional **1% of equity per trade**.
- Position size from `R` (the SL distance in points) × US100.cash point value. *Verify the
  FTMO US100.cash contract / point value before sizing — do not assume.* Round lot size
  **down**.
- One position at a time (one trade/day).

**FTMO-aware (documented, non-binding until deploy phase):**
- Daily-loss halt: stop trading for the day at **−5%** equity.
- Max-DD kill switch: **−10%** total.
- Profit target: **+10%** (challenge).
- **Consistency rule** interaction: a once-a-day strategy concentrates profit into few
  days — flag against FTMO's no-single-day-> -X%-of-total-profit rule before live.
- News guard: FTMO restricts trading around high-impact news on some accounts. **Tension:**
  the NY open (09:30 ET) sits minutes after the 08:30 ET US data block and can coincide
  with releases — the ORB *is* a news-reactive strategy. Resolve at deploy (e.g., skip days
  with a release inside the OR window) — but note that filtering those days may remove the
  best trades; test both.
- EOD-flat already satisfies any no-overnight requirement.

---

## §10 Validation plan (the actual deliverable)

**Method — walk-forward, per [strategy-validation.md](../docs/strategy-validation.md):**
1. Sliding windows over US100.cash history; optimize on ~70%, run blind on the remaining
   ~30%, slide, repeat.
2. Stitch the OOS segments; **report the combined OOS result only.**

**Execution model:**
- **Real-tick model** in the MT5 Strategy Tester (tick data already subscribed for
  US100.cash). M1 bar history must be downloaded first — see §12.
- **Costs modelled and netted out:**
  - FTMO US100.cash **spread** (model realistically; verify live spread, ~1–2 pts).
  - **Commission** (FTMO indices are typically spread-only — verify).
  - **Stop-entry slippage** — breakouts fill *worse* than the stop price; add explicit
    slippage points on stop fills. Do **not** assume perfect fills. This is where naive ORB
    backtests lie.

**Anti-overfit — sequential, not combinatorial tuning.** The S{0,1,2} × E{0..4} grid is 15
combinations; do **not** grid-search them blindly.
1. Lock the **SL arm** using the **E0** baseline (3 runs).
2. With SL fixed, sweep the **exit arms** (5 runs).
3. Confirm bias-EMA length and RVOL threshold last.
Keep **≤ ~4 active tuned parameters** at any stage (repo prior: simple beats complex).

**Acceptance gate (repo §2, intraday-adapted):**
- OOS Sharpe in **[0.5, 1.5]** realistic (reject < 0.5 = noise, > 2.5 = the asset did it).
- OOS max drawdown better than threshold (**tighter than −35%** for a leveraged index;
  target ≤ −25–30%).
- OOS Sharpe ≤ in-sample **+30%**.
- **≥ 30 trades** (prefer ≫ — intraday has no excuse).
- **No single trade > 25–30% of net P&L** (the ETR lesson).
- **All metrics net of costs.**

**Free OOS robustness.** Freeze the final parameters, then re-run **unchanged** on
**US500.cash** and **GER40.cash** (GER40 re-anchored to the 09:00 Frankfurt open — session
shift only, **no re-tuning**). Real edge survives an instrument swap; a curve-fit does not.

**Buy-and-hold sanity.** US100 has strong upward drift. Compare long-only trades against a
dumb buy-and-hold of US100 over the same period — if B&H matches it, the strategy is
capturing *exposure*, not *edge* (the Tesla trap). Also inspect the **short side
standalone**: if all the profit is long-side drift, say so.

**Audit trail.** Every reported number traces to a file under
`reports/ORB-<UTCstamp>/` (raw result + config + driver + log excerpt + sha256 manifest),
per the `audit-trail` skill and CLAUDE.md. No metric stated unless it traces to a file
inspected that session.

---

## §11 Parameters

**Tuned (walk-forward; keep ≤ ~4 active at once):**

| Parameter | Search set | Default hypothesis |
|-----------|-----------|--------------------|
| OR duration | {15, 30} min | 15 |
| Bias EMA length (D1) | {20, 50, 100, 200} | 50 |
| RVOL threshold | {1.0 … 2.0} | 1.5 |
| Stop arm | {S0, S1, S2} | S0 |
| Exit arm | {E0, E1, E2, E3, E4} | E0 baseline |
| Trail EMA (M15) | {8, 21} | 8 |
| Target K (E1) | {2, 3} | — |
| S2 ATR multiple k | {1.0, 1.5} | — |

**Fixed (not tuned in v1):**

| Parameter | Value |
|-----------|-------|
| Entry buffer | 0.1 × OR_width |
| Entry window | 09:45 → 11:30 ET |
| EOD flat | 16:00 ET |
| Range guard | OR_width ∈ [0.5, 2.0] × median(OR_width, 14 sessions) |
| RVOL lookback | 14 sessions |
| Risk per trade | 1% |
| Max trades/day | 1 |

---

## §12 Data gap — step 0 before any backtest

US100.cash **bar history is not downloaded** (only tick data is subscribed in Market
Watch). Before the first run:
1. Download M1 bar history for US100.cash (open the chart and scroll back, or let the
   tester fetch), **or** run the Strategy Tester in real-tick mode directly off the
   subscribed tick base.
2. Confirm the available history depth — walk-forward needs enough sessions for ≥ 30 OOS
   trades plus the in-sample windows (target several years of opens).

---

## §13 Known flaws & health check

Read this before trusting any future number.

- **Breakout is the weak horse.** The repo meta-study puts the breakout/trend family at
  ~18–22% survival. The bias + RVOL gates are the mitigation, not a guarantee. Expect this
  to fail the gate more likely than not — and that is an acceptable, informative outcome.
- **Tick volume ≠ true volume.** RVOL is a proxy on a CFD; weaker than on real-volume
  futures.
- **Upward-drift / Tesla trap.** US100's secular climb can make long-only trades look like
  edge when they are exposure. Mitigations: gate filters, short-side standalone inspection,
  B&H benchmark (§10).
- **News density at the open.** The 09:30 ET open sits on top of the US data block; the
  strategy is structurally news-reactive. The news-guard requirement and the strategy's
  core may be in direct tension (§9).
- **Degrees of freedom.** Two compared dimensions (SL, exit) plus four tuned knobs is a lot
  of room to fit noise. Sequential tuning (§10) and frozen-param cross-instrument OOS (§10)
  are the controls; if they are skipped, the result is not trustworthy.
- **Precedent: IVB failed.** This repo's IVB (Initial-Balance Breakout) — the same
  opening-range family — was tested on XAUUSD 2024 in-sample and showed **no edge**
  (PF 0.79–0.88, DD 74–99%; see [strategy-validation.md Findings log](../docs/strategy-validation.md#findings-log)).
  ORB is the deliberate re-attempt on the *right* instrument class (a real index, not gold
  spot) with the *missing* filters (trend bias + RVOL). It may still fail. That is the
  experiment.

---

## §14 Build order (once spec is approved)

1. **Step 0** — data (§12).
2. Implement the deterministic core EA: OR capture → bias gate → RVOL/range guard → entry
   stop order → S0 stop → E0 exit → EOD flat. (Minimum testable kernel.)
3. Walk-forward the **SL arms** on E0 (§10 step 1).
4. Walk-forward the **exit arms** with SL locked (§10 step 2).
5. Confirm bias-EMA + RVOL (§10 step 3).
6. Apply the gate (§10). If it passes, freeze params and run the **cross-instrument OOS**.
7. Only if it survives all of the above: design the FTMO-deployment risk layer (§9).
