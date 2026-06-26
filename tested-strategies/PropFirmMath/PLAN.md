# PropFirmMath — Implementation Plan

Goal: empirically test whether the JJ Simon method is a real edge or survivorship.
Reduce to one number first — **after-cost per-trade expectancy of the 1-min fade-to-09:29
signal on NQ** — then, only if positive, build the prop-firm wrapper that converts it.

Inputs: [`QUANTIFY.md`](QUANTIFY.md) (rules + params), [`EXTRACTION.md`](EXTRACTION.md) (raw).
Discipline: **TDD** (test before impl), **audit-trail** (every run → `reports/<name>-<UTCstamp>/`
with raw result + config + driver + log + sha256 manifest), **verify-before-reporting** (no
metric stated unless traced to an inspected result file — per prior GoldCore fabrication note).

---

## Repo layout
```
PropFirmMath/
  transcript/            # raw.en.vtt, transcript_clean.txt   [done]
  EXTRACTION.md  QUANTIFY.md  PLAN.md  NOTES.md                [done]
  data/                  # NQ/MNQ 1-min bars (gitignored, large)
  core/                  # shared: bars, sessions, costs, pivots
  signal/                # Layer A — entry/exit engine
  wrapper/               # Layer B — firm rules, eval/funded MC, portfolio EV
  tests/                 # pytest, TDD
  run.py                 # CLI: run.py signal | eval | portfolio
  reports/               # audit-trail run dirs
```

---

## Phase 0 — Data (the known blocker)
Same wall as OpeningRangeFVG: need real **NQ/MNQ 1-min** with extended hours 08:00–20:00 ET.
- **Task 0.1** Decide source: MT5 M1 export (NAS100 proxy) vs. databento/CME sample vs. IBKR.
  - MT5 NAS100 = CFD proxy, not true NQ futures; spread differs → cost model less faithful.
  - Prefer real futures 1-min if obtainable; else proxy + flag the caveat in every report.
- **Task 0.2** Loader → normalized parquet: `ts_et, o,h,l,c, volume`. Tests: tz correctness (ET, DST), session tagging, no gaps in RTH.
- **Gate 0:** ≥ 6 months clean 1-min before proceeding. No data → STOP, report blocker.

## Phase 1 — Layer A signal engine (TDD) ← the make-or-break
Build the per-trade simulator. **This phase alone can kill the project.** (v2 defined the triggers — see QUANTIFY §A2–A6.)
- **1.1 core/sessions** — tag bars by block (03:00/08:30/09:30/14:00/18:00/20:00 ET); set `P_fair` = **09:30 open candle**; enforce **11:00 hard cutoff**. Tests first.
- **1.2 core/structure** — (a) pivot H/L over `L` bars → BoS = close beyond opposing pivot; (b) **displacement candle** = body ≥ `m`×prev body AND wick ≤ `w`% of range. Both close-confirmed. Fixture tests. (`L,m,w` = the only sweep params.)
- **1.3 core/costs** — commission + spread per RT (MNQ default); parameterized.
- **1.4 signal/bias** — two biases agree: reversion toward `P_fair` + low-TF momentum. First trade = open-candle color, 0–10 min.
- **1.5 signal/entries** — continuation (0–10 min, open color, trigger=BoS|displacement) + reversion (10–90 min, toward `P_fair`, trigger=BoS|displacement); grade each A+/A/B; instant re-entry after unfair stop-out.
- **1.6 signal/exits** — **fixed 25 pt SL / 38 pt TP (1:1.5)**; funded variant = extend TP; no BE/partials; avoid 9:45/10:00 news holds.
- **1.7 backtest loop** — iterate bars, emit ledger (entry, exit, R, grade, setup-type, block).
- **1.8 metrics** — per-trade WR **by grade**, after-cost expectancy (R), daily P&L dist, % winning days, MAE.
- **Run → `reports/signal-<stamp>/`.**
- **Gate 1 (KILL GATE):** sweep `{L, m, w}`. Test **(a) all setups vs (b) A+ only** — v2 claims A+≈70–80%, blend unknown. If **no** config yields after-cost expectancy > 0 with stable WR across train/OOS → **report negative, STOP.** Layer B is moot. (QUANTIFY §2.1 — primary falsifier; also note JJ's own "live edge 1–5%" admission.)

## Phase 2 — Layer B firm-rule simulator (only if Gate 1 passes)
- **2.1 wrapper/firm** — rule model: target, **trailing DD** (v2 recipe: ratchets UP on new equity highs, **locks at start balance** once profit ≥ buffer, EOD-evaluated), daily-loss, consistency %, min-days, eval_cost, size, split. Parameterize Topstep/E8/TradeFi-like tiers.
- **2.2 wrapper/eval_mc** — Monte-Carlo eval: draw trade sequences from Phase-1 empirical dist, apply rules → empirical `p_pass`, `time_to_pass`. Tests on synthetic dists with known answers.
- **2.3 Validate matched-R:R claim** — does R:R = target/DD ratio (1:1.5 for 3k/2k) raise `p_pass` vs other R:R? Report the curve. (QUANTIFY §2.3 falsifier.)
- **2.4 wrapper/funded_mc** — funded sim: $10k→withdraw $5k cycle → `p_payout`, `payout_size` dist.
- **Run → `reports/eval-<stamp>/`.** Reproduce his `p_pass≈25–33%`? Report gap honestly.

## Phase 3 — Portfolio EV + risk of ruin
- **3.1 wrapper/portfolio** — per-eval EV, `avg_cost_to_funded = eval_cost/p_pass`, return multiple, aggregate over N accounts.
- **3.2 risk of ruin** — `(1 − p_pass·p_payout)^N`, **AND** a correlated variant.
- **3.3 CORRELATION (critical)** — 40 accounts trade the *same* NQ signal same day → outcomes correlated, so independent `(P_fail)^N` flatters RoR (QUANTIFY §2.4). Model a shared daily factor; report RoR under ρ∈{0, 0.3, 0.6, 0.9}. **This is the most likely real-world flaw.**
- **3.4 Kelly** — eval count vs bankroll; ¼/½ Kelly. Reproduce $5k→$17k / $100k-mo=$4.5M-alloc checkpoints.
- **Run → `reports/portfolio-<stamp>/`.**

## Phase 4 — Sensitivity & verdict
- Sweep costs (proxy vs real), WR ±, ρ, eval price. Tornado chart of what the EV is most fragile to.
- **VERDICT.md**: is the edge real after costs+correlation, or survivorship? Trace every number to a `reports/` file.

---

## Decision gates (stop-loss on effort)
| Gate | Pass condition | If fail |
|---|---|---|
| 0 | ≥6mo clean 1-min data | STOP — report data blocker |
| **1** | after-cost expectancy > 0, stable OOS | **STOP — thesis dead** |
| 2 | reproduce p_pass ≥ ~20% | flag eval economics weak |
| 3 | RoR acceptable *under correlation* | flag wrapper fragile |

## Build order / next session
1. Phase 0.1 data-source decision (needs user input: real futures vs MT5 proxy).
2. TDD core/ (sessions, pivots, costs).
3. Phase 1 signal → **hit Gate 1 fast** — cheapest path to kill-or-continue.

## Out of scope (v1)
- 11:00–14:00 "longer hold" — **confirmed nonexistent** by v2 (was a v1 misread). 11:00 = hard cutoff.
- Funded "different strategy" — v2 softens to same engine + extended-TP management; model that.
- Live execution / MT5 EA — only after Gates 1–3 pass.
- News-calendar feed (Phase 1 uses session opens only; add 08:30 red-folder block later).

## Risks
- **Data fidelity:** MT5 NAS100 ≠ NQ futures; cost model drives the whole verdict → prefer real futures.
- **2 remaining signal unknowns:** swing-detection `L` + displacement cutoff `m,w` are param-sensitive; report the full sweep, not a cherry-picked best.
- **Grade selection:** A+ 70–80% is JJ's only WR claim; if blend < 40% and only A+ clears, that's a much rarer setup → fewer trades/day → recompute the wrapper's trade frequency.
- **Overfitting:** strict train/OOS split; Gate 1 requires OOS stability, not in-sample peak.
