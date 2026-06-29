# PropFirmMath EV App — Design Spec

Date: 2026-06-26
Status: Approved (brainstorming → spec)
Source findings: video-1 interview (`aCOgfvL6lK8`) EV/portfolio math, captured in
[`../../../EXTRACTION.md`](../../../EXTRACTION.md) §5 and [`../../../QUANTIFY.md`](../../../QUANTIFY.md) Layer B.

## 1. Purpose

A local app that implements **JJ Simon's pre-purchase EV math** ("the exact maths he runs
before buying a single evaluation") and pairs it with a **real-account tracker / trade journal**,
so that tracked actuals (observed pass rate, payout rate, avg payout, win rate) feed back into
the calculator instead of relying on his self-reported rosy inputs.

This is the **Layer-B planning/tracking tool only**. It does NOT run the price-signal backtest —
that remains the separate effort in [`../../../PLAN.md`](../../../PLAN.md). The app's break-even-WR
card is the bridge that keeps the unproven signal edge ("JJ admits live edge only 1–5%") visible.

## 2. Stack & conventions

- **Python 3.13**, **Streamlit** (multipage) UI, **SQLite** storage, **pytest** for the engine.
- Charts: Streamlit-native (`st.line_chart` / Altair) for equity + drawdown.
- `scipy` for the correlated risk-of-ruin (Gaussian one-factor copula integral); `pandas`, `numpy`.
- The math lives in a **pure, I/O-free `engine.py`** so it is unit-tested independently of UI/DB.
- Subject to the repo's validation + audit-trail rules ([`../../../../docs/strategy-validation.md`](../../../../docs/strategy-validation.md)).
  No reported metric without a traced source; the app *computes* — it does not claim edge.

## 3. Architecture

```
tested-strategies/PropFirmMath/app/
  engine.py        # pure EV math (JJ + honest layer), NO I/O
  estimate.py      # tracked actuals -> observed rates -> engine inputs
  db.py            # SQLite connection, schema init, CRUD helpers
  models.py        # domain dataclasses (Firm, Account, Trade, Payout, Scenario)
  seed.py          # idempotent sample-data seeder
  app.py           # Streamlit entry / nav
  pages/
    1_Calculator.py
    2_Accounts.py
    3_Journal.py
    4_Portfolio.py
    5_Scenarios.py
  tests/
    test_engine.py     # JJ's worked numbers as oracles
    test_estimate.py
    test_db.py
  requirements.txt
  README.md            # how to run: `streamlit run app.py`
propfirm.db            # live DB — GITIGNORED (personal data); created on first run
```

Separation of concerns: `engine.py` is the math source of truth (pure, testable). `db.py` owns
persistence. `estimate.py` bridges tracked data → engine inputs. UI pages are thin: read inputs,
call `engine`/`db`, render.

## 4. EV engine (`engine.py`) — the math

All functions pure (no I/O, no globals). Notation: `p_pass` = P(pass eval), `p_payout` =
P(reach a payout | funded), `pipeline = p_pass * p_payout`, `payout_size`, `eval_cost`,
`account_size`, `n` = number of accounts.

### 4.1 Single-eval economics
```
expected_payout_per_eval = p_pass * p_payout * payout_size
ev_per_eval              = expected_payout_per_eval - eval_cost
return_multiple          = expected_payout_per_eval / eval_cost      # guard eval_cost>0
avg_cost_to_funded       = eval_cost / p_pass                        # guard p_pass>0
```
Optional `residual_balance` (JJ's "$2k left in the funded account"): surfaced as a separate
"non-withdrawn balance" figure, NOT added into `ev_per_eval` (avoids double-counting cash).

**Test oracles (reproduce JJ exactly):**
- `p_pass=p_payout=0.33, payout=2000, eval_cost=100` → `return_multiple ≈ 2.18` ("2x"); pipeline `≈ 1/9`.
- `p_pass=1/3, expected E[payout|funded]=1000, eval_cost=100` → `avg_cost_to_funded≈300`, `return_multiple≈3.3` ("3x").

### 4.2 Risk of ruin
```
ror_independent(pipeline, n)        = (1 - pipeline) ** n
ror_correlated(pipeline, n, rho)    = one-factor Gaussian copula:
    t = Phi_inv(1 - pipeline)        # success if latent X_i > t
    X_i = sqrt(rho)*Z + sqrt(1-rho)*eps_i
    P(all n fail) = ∫ phi(z) * Phi((t - sqrt(rho)*z)/sqrt(1-rho))**n dz
```
- `rho` default **0.5**, slider range **0–0.9**. At `rho=0`, `ror_correlated == ror_independent`
  (continuity — this is JJ's number). As `rho→1`, P(all fail) → `(1-pipeline)` (n correlated
  accounts collapse toward a single bet).
- Rationale: accounts are NOT independent — JJ copy-trades in ~5-account clusters across different
  setups/day and layers into winners (he rejects all-40-on-one-setup), so outcomes are block-correlated.
  His independent `(P_fail)^N` understates real ruin risk. App shows **both, side by side** (`rho`
  models the effective/cluster correlation).

**Test oracles:** `ror_independent(0.1, 50) ≈ 0.00515` (his "0.9^50 < 1%"); `ror_correlated(p,n,0)`
≈ `ror_independent(p,n)` within 1e-6; `ror_correlated` monotonically increases in `rho`.

### 4.3 Kelly sizing
```
b      = (payout_size - eval_cost) / eval_cost   # NET odds: eval_cost is sunk on success,
                                                 #   net gain = payout_size - eval_cost per stake
f_star = pipeline - (1 - pipeline) / b           # = p - q/b; Kelly fraction; clamp at 0
n_star(bankroll, fraction) = floor(f_star * fraction * bankroll / eval_cost)
```
Return `f_star`, full/half/quarter `n_star`. Test: `f_star>0` iff `ev_per_eval>0` (equivalently
`pipeline*payout_size > eval_cost`); quarter-Kelly N = ¼ of full N.

### 4.4 Portfolio & monthly target
```
total_ev(n)            = n * ev_per_eval
expected_payouts(n)    = n * pipeline
# planning a monthly payout target:
payouts_needed         = monthly_target_dollars / payout_size
accounts_needed        = payouts_needed / pipeline         # evals to buy for the month
allocation_needed      = accounts_needed * account_size     # funded capital represented
```
Reproduce his `$100k/mo` worked example as a **documented example** (not a strict oracle — his
intermediate figures are loose): payouts_needed `= 150k/5k = 30`, and his `30 × 150k = $4.5M`
allocation framing. Spec note: his "30 accounts" conflates evals-bought with active-funded; the
app exposes both `accounts_needed` (evals) and an `active_funded` view, and labels the assumption.

### 4.5 Break-even WR (signal reality check)
```
breakeven_wr(rr) = 1 / (1 + rr)        # risk 1 to make rr
```
Oracles: `1:1 → 0.50`, `1:1.5 → 0.40`, `1:2 → 0.333`, `1:4 → 0.20`. UI annotates with "JJ states
live edge 1–5%, breaks even on live" so the EV is never read as risk-free.

### 4.6 Scale ladder
`scale_ladder(start_bankroll, rungs)` → rows of `(bankroll, account_tier, multiple, end_bankroll)`
reproducing his `5k→17k` (~3.4x) progression. Illustrative; one oracle on the 5k→17k rung.

## 5. Data model (`db.py` / `models.py`)

SQLite. DDL:
```sql
CREATE TABLE firms (
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, account_size REAL, eval_cost REAL,
  profit_target REAL, trailing_dd REAL, daily_loss_limit REAL, consistency_pct REAL,
  payout_split REAL, payout_cadence TEXT, notes TEXT);
CREATE TABLE accounts (
  id INTEGER PRIMARY KEY, firm_id INTEGER REFERENCES firms(id), label TEXT,
  phase TEXT CHECK(phase IN ('eval','funded','passed','failed')) NOT NULL,
  status TEXT CHECK(status IN ('active','closed')) NOT NULL DEFAULT 'active',
  start_date TEXT, cost_paid REAL, current_balance REAL, notes TEXT);
CREATE TABLE trades (
  id INTEGER PRIMARY KEY, account_id INTEGER REFERENCES accounts(id), ts TEXT,
  session TEXT, direction TEXT CHECK(direction IN ('long','short')),
  grade TEXT CHECK(grade IN ('A+','A','B')), r_multiple REAL, pnl REAL);
CREATE TABLE payouts (
  id INTEGER PRIMARY KEY, account_id INTEGER REFERENCES accounts(id), date TEXT, amount REAL);
CREATE TABLE scenarios (
  id INTEGER PRIMARY KEY, name TEXT UNIQUE, params_json TEXT, created TEXT);
```
Equity curve + drawdown are **derived** from `trades` per account (cumulative `pnl`, running peak).
Drawdown-vs-limit compares running drawdown to the firm's `trailing_dd`.

## 6. `estimate.py` — actuals → engine inputs

```
observed_pass_rate(accounts)   = passed / (passed + failed)            # eval-resolved only
observed_payout_rate(accounts) = funded_with_payout / funded_total
observed_avg_payout(payouts)   = mean(amount)
wr_by_grade(trades)            = {grade: wins/total}
observed_avg_r(trades)         = mean(r_multiple)
```
**Small-sample shrinkage:** Beta-Binomial posterior mean for the two rates, weak prior centered
on JJ's 0.33 (`alpha=beta` tuned to ~5 pseudo-counts), so 3 evals don't read as "0% or 100%".
Functions return `(point_estimate, n_samples, shrunk_estimate)`; UI flags `n < 30` as
"not yet significant" (mirrors the repo's 30-trade rule). These prefill the Calculator under an
**"observed vs assumed"** toggle.

## 7. Views (Streamlit pages)

1. **Calculator** — inputs (eval_cost, p_pass, p_payout, payout_size, account_size, n, bankroll,
   rho slider, rr). Outputs: ev_per_eval, return_multiple, avg_cost_to_funded; **RoR independent
   vs correlated** as the headline honest callout; Kelly N (full/½/¼); monthly-target → allocation;
   break-even-WR card. "Save as scenario" button.
2. **Accounts** — CRUD firms + accounts; table with phase, balance, P&L, **drawdown vs trailing
   limit** (color bar), eval pass / payout status.
3. **Journal** — log trades per account; **equity curve + drawdown chart**; per-account WR by grade,
   avg R, trade count.
4. **Portfolio** — aggregate: total payouts to date, **monthly-target progress**, **observed vs
   assumed** rates (button: "use observed in Calculator"), current RoR at live N, scale-ladder position.
5. **Scenarios** — list + side-by-side compare of saved Calculator configs.

## 8. Honesty layer (woven in, not bolted on)

- RoR always shows JJ's optimistic `(1-pipeline)^N` next to the correlation-adjusted value, with a
  one-line plain explanation of why his is too low.
- Observed-vs-assumed surfaces whenever real tracked rates diverge from the entered inputs.
- Break-even-WR card keeps the unproven, cost-sensitive signal edge in view on the Calculator.

## 9. Build phases (→ feeds writing-plans)

| Phase | Deliverable | Done when |
|---|---|---|
| P1 | `engine.py` + `test_engine.py` | All §4 functions pass; JJ's worked numbers reproduced as oracles; runnable as a CLI sanity print |
| P2 | `db.py`, `models.py`, schema, `seed.py` + `test_db.py` | Tables create; CRUD round-trips; idempotent seed of 3 sample firms + a few accounts/trades/payouts |
| P3 | `app.py` + Calculator page | Calculator computes live from `engine`; save/load scenario works |
| P4 | Accounts + Journal pages | Add firm/account/trade/payout; equity + drawdown charts; drawdown-vs-limit color |
| P5 | `estimate.py` + Portfolio page + `test_estimate.py` | Observed rates compute w/ shrinkage; "use observed" feeds Calculator; monthly progress |
| P6 | Scenarios compare + README + polish | Side-by-side scenario compare; run instructions; gitignore `propfirm.db` |

**At P1/P2, review `../../../../PropDDSim/` (`propdd_sim.py`) for reusable risk-of-ruin /
drawdown-simulation code before writing from scratch.**

## 10. Decisions locked

- Correlation `rho` default **0.5**, range 0–0.9; `rho=0` reproduces JJ's independent number.
- **Seed sample data: yes** — idempotent `seed.py` (3 firms ~ Topstep/E8/TradeFi-like + a handful
  of accounts/trades/payouts) so the app isn't empty on first run. Live `propfirm.db` gitignored.
- `return_multiple = expected_payout / eval_cost` (reconciles both JJ framings; see §4.1).
- `residual_balance` shown separately, never folded into EV.

## 11. Out of scope (YAGNI)

Auth / multi-user, cloud hosting, MT5 / live-broker integration, real-time price feeds, the price
signal backtest (separate `PLAN.md`), automated trade import. This app is manual-entry tracking +
the EV/planning math only.
