# DMC Strategy — Quantified Spec

**DMC = "Dumb Money Concepts"** — a deliberate play on Smart Money Concepts (SMC).
Source: YouTube channel [@DumbMoneyHunter](https://www.youtube.com/@DumbMoneyHunter)
("Dumb Money Hunter | Maven Founder"). See [links.md](links.md) for the two source videos
and machine transcripts.

**Status:** SPEC ONLY — **UNVALIDATED**. No backtest has been run. Creator's win-rate claims
(80–90%, "nearly 100%") are unverified marketing (see §7). Nothing here is evidence of edge.
Do not size risk against this document.

---

## §1 Core concept

The whole system reduces to one classification of how price interacts with a **level**:

| Event | Definition | Meaning |
|---|---|---|
| **GAIN** | Bar closes beyond the level | Breakout / reclaim |
| **LOSE** | Bar closes back through the level the opposite way | Break the other side |
| **FAIL** | Wick/attempt beyond the level, then close back inside the range | Rejection |

The tradeable signal is **FAIL (failure-to-break)**: after a failed attempt at a level, price is
assumed to **reverse to the ORIGIN of the move that produced that level**. A **REGAIN**
(lose-a-level-then-reclaim-it quickly) is treated as **equivalent to a FAIL-wick** → target the
**opposite side of the zone**.

Stated scope from the videos: *"We only know the **next move**"* — not the whole trend, just the
single next leg toward the move's origin.

---

## §2 Definitions

- **Level** — an **untested candle body extreme** on a higher timeframe. Body extreme =
  `max(open, close)` (upper) or `min(open, close)` (lower). Wicks are explicitly *not* the level
  (the wick is the "attempt").
- **Untested** — no later bar has traded through that body price since the candle formed. Once a
  level is **tested** (traded through once), it is assumed **unlikely to hold again** unless a *new*
  level formed at that location.
- **Origin of move** — the swing pivot where the leg that created/left the level began. This is the
  primary **FAIL target**.
- **Zone** — the price region between the level and the origin of the move.
- **Next move / bias** — direction of the next HTF leg implied by the most recent FAIL or REGAIN at
  the controlling (nearest interacting untested HTF) level. **Explicitly NOT** defined by
  higher-highs/higher-lows; the creator rejects HH/HL trend definition.
- **Controlling level** — the nearest untested HTF level price is currently interacting with.

---

## §3 Variant A — HTF level-reaction (swing / intraday)

Source: *"Easiest Trading Strategy (80-90% Win Rate) - DMC"*. General, asset-agnostic
(creator demos on FX, indices, BTC).

**Inputs:** HTF level set `H` (default `{Daily, Weekly, Monthly}`), execution TF `X`
(default `H1` or `H4`).

```
1. LEVEL MAP   For each TF in H, mark untested body extremes -> candidate level set L.
2. BIAS        Find controlling level Lc (nearest untested HTF level price interacts with).
               Classify last interaction at Lc:
                 FAIL above resistance  OR  REGAIN of support   -> bias = UP, target = origin
                 FAIL below support     OR  REGAIN of resistance -> bias = DOWN, target = origin
3. ENTRY       Pick ONE mode (see below).
4. STOP        Beyond the NEXT level past Lc (not Lc itself). Fallback: k * ATR.
5. TARGET      Origin of the move (primary) | next opposing HTF level | new swing extreme.
6. EXIT-INVAL  After entry, if price FAILS to make a new extreme in the bias direction
               (expected next move stalls/reverses) -> exit; may re-enter later.
```

**Entry modes (mutually exclusive — must fix one per backtest):**

| Mode | Rule | Creator's note |
|---|---|---|
| `blind` | Resting limit at the untested level `Lc` | Only for D/W/M levels; tight stop, quick scalp |
| `retest` | Wait for first reaction (wick) off `Lc`, enter on the retest of `Lc` in bias dir | For lower-TF levels |
| `dca` | 1–2 limit legs spread across the zone | **Max 2 legs. No martingale.** First leg exits at break-even once averaged |

**Stop:** placed **behind the next level beyond** `Lc`, *not* at `Lc` — explicitly to "let the
market stop out the other guys without stopping you out."

**Target / hold:** other side of the zone / next key level / new swing high. Creator quotes a
**~1–1.5 hour per trade** horizon for intraday — note this conflicts with a swing-to-origin target
and must be resolved per test (see §6).

---

## §4 Variant B — Market-open scalp

Source: *"This DMC Market Open Strategy Is Too Easy"*. Specialization of Variant A onto the
**Nasdaq cash open**.

**Instrument:** Nasdaq (NQ / US100). **Session:** US/Eastern.

```
1. REF CANDLE  The 09:00 ET H1 candle (the hour BEFORE the 09:30 cash open).
2. BIAS        If 09:00 H1 FAILED to make a new high vs prior swing/range high
                  (wick + close back inside)            -> BEARISH (expect retest then down)
               If price REGAINED a lost level (close back above) -> BULLISH (target new high)
3. ENTRY       At/after 09:30 open, in bias direction. Prefer a pullback into the zone
               (e.g. pre-market low / "London low" retest). Hold horizon 3-5 min ("09:30-09:34").
4. TARGET      Next high/low — low-R scalp. Optional add/scale at the retest.
5. STOP        Discretionary in the video ("somewhere") -> MUST be fixed before testing
               (candidate: beyond the pre-market extreme or the 09:00 H1 candle extreme).
```

Creator's framing: in-and-out within ~3–5 minutes, "low R", one contract, target a single new high.

---

## §5 Parameters

| # | Parameter | Variant | Default | Status |
|---|---|---|---|---|
| P1 | HTF level set `H` | A | `{D, W, M}` | FIXED |
| P2 | Execution TF `X` | A | `H1` / `H4` | FIXED |
| P3 | Body-extreme definition | A/B | `max/min(open, close)` | FIXED |
| P4 | "Untested" rule | A/B | not traded through since formation | **FREE** — needs exact bar test |
| P5 | "Origin of move" detector | A/B | swing pivot starting the leg | **FREE** — needs swing algo (depth `d`) |
| P6 | Entry mode | A | one of {blind, retest, dca} | **FREE** — must pick one |
| P7 | DCA legs | A | ≤ 2 | FIXED (no martingale) |
| P8 | Stop placement | A | beyond next level past `Lc` | semi-free (needs "next level" rule) |
| P9 | Stop fallback `k·ATR` | A | `k`, ATR period unset | **FREE** |
| P10 | Target rule | A | origin \| next level \| new swing | **FREE** — must pick one |
| P11 | Hold horizon | A | ~1–1.5 h | **FREE** — conflicts with P10 |
| P12 | Reference candle | B | 09:00 ET H1 | FIXED |
| P13 | "New high failure" lookback | B | prior swing/range high | **FREE** — define window |
| P14 | Open entry timing | B | ≥ 09:30 ET, pullback preferred | semi-free |
| P15 | Scalp hold | B | 3–5 min | FIXED |
| P16 | Open stop | B | unspecified ("somewhere") | **FREE** — must define |

---

## §6 Testability gaps (must resolve before any backtest)

The strategy is **discretionary as stated**. These free parameters are exactly the degrees of
freedom that let any winning clip be drawn in hindsight; each must be pinned to a deterministic
proxy before a number means anything.

| Gap | Proposed algorithmic proxy |
|---|---|
| "Untested level" (P4) | Body extreme with no later bar `low ≤ level ≤ high`; keep top-K nearest by price in a `W`-bar lookback |
| "Origin of move" (P5) | ZigZag / fractal swing of depth `d`; origin = pivot that starts the leg leaving the level |
| "Next move / bias" | Classify the last interaction at the nearest untested HTF level (FAIL vs REGAIN) — deterministic given P4/P5 |
| Entry-mode ambiguity (P6) | Pick exactly one mode per run; do not blend |
| Stop "next level behind" (P8) | The next untested level beyond `Lc`; if none within `W`, fall back to `k·ATR` |
| Target "new high" (P10) | Next opposing untested level, OR `n`-bar swing extreme — pick one |
| Hold 1–1.5 h vs swing target (P11) | Mutually inconsistent — Variant A swing uses level targets; only the open-scalp uses the minute horizon |
| Open stop "somewhere" (P16) | Beyond pre-market extreme or 09:00 H1 candle extreme |

---

## §7 Validation status & claim check

Per [docs/strategy-validation.md](../docs/strategy-validation.md) — the standing rule of this repo:

- **Claims are marketing until proven.** "80–90% win rate" / "nearly 100%" / "you're going to be
  right" carry no trade log, no losers, no losing days. *"This DMC Market Open Strategy Is Too Easy"*
  is a **montage of winners** — textbook survivorship/cherry-pick.
- **Win-rate-inflation structure.** Even if the clips are real, the described mechanics inflate hit
  rate without implying edge: tiny TP vs **loose-or-absent stop** ("I don't really use them too
  much"), **DCA** averaging, and **"exit and re-enter if it goes against me"** (scratches/re-entries
  not counted as losses). That is **negative skew + blow-up risk**, not an edge. **High win rate ≠
  positive expectancy.**
- **Priors** (per the survival study): discretionary, multi-rule, level-pattern strategies survive
  rigorous OOS testing far less often than simple mean-reversion. Real edge on these timeframes
  ≈ OOS Sharpe 0.5–1.5, not "nearly 100%".

**To move from SPEC → evidence**, a future build must:
1. Fix every **FREE** parameter in §5/§6 (deterministic proxies).
2. Run **walk-forward** (optimize ~70%, blind on ~30%, stitch OOS), net of spread/commission/slippage.
3. Clear the **auto-reject gate**: OOS DD > −35% → reject; OOS Sharpe < 0.5 or > 2.5 → reject;
   OOS beats in-sample by > 30% → reject; < 30 trades → not significant; any single trade > ~25–30%
   of net P&L → reject.
4. **Sanity:** would buy-and-hold of the asset have matched it? (The Nasdaq was broadly up over the
   demo period — long-the-open scalps can be exposure, not edge.)

Until then: **provisional / in-sample only / unvalidated.**

---

## §8 Audit trail (when backtested)

Any run that produces a reported number must leave a CBS-style audit folder
(`DMC/reports/<run>-<utcstamp>/`): raw events, aggregated tables, `config.json`, `run.log`,
`manifest.sha256`. No metric may be stated unless it traces to a file in that folder
(enforced by the `audit-trail` skill).
