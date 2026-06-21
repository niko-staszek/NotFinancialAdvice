# Reverse-engineering: "Scalper Pro v4.1 [ZynAlgo]"

Reconstruct an **equivalent** Pine v6 indicator that reproduces the observable plotted
behavior of the protected ZynAlgo script. We do **not** recover original source (compiled
server-side, not retrievable). Goal = match output: dashboard values, signal timing,
SL/TP geometry.

- Original pineId: `PUB;03f721e7c9c9445f9e61f0b99eeb9c20`
- Original entity on chart: `1YbVvY`
- Our reconstruction: `SPZ/recovered_indicator.pine`

## Method
Iterative hypothesis-testing. Match the highest-confidence, deterministic pieces first
(RSI/ADX/Volume dashboard numbers), then the harder score → signal logic.

Status legend: ✅ confirmed from TV (settings/dashboard/study values) · 🔶 hypothesis · ❓ unknown

---

## 1. Confirmed parameter map (settings dialog → input ID → value)

Input IDs come from `data_get_indicator`; labels/sections from the settings dialog DOM.

### 🏆 Score / Signal Filter
| Label | input id | value | meaning |
|---|---|---|---|
| Minimum Score (0-100) | in_0 | 60 | ✅ signal fires when confluence score ≥ this |
| HIGH QUALITY Threshold | in_1 | 80 | ✅ score ≥ this ⇒ "high quality" signal |
| Signal Cooldown Bars | in_2 | 25 | ✅ min bars between signals |
| Stability Mode | in_3 | true | ✅ bool gate (smoothing/persistence) |
| Smart Signal Filter | in_4 | true | ✅ bool gate |
| Trading Style | in_5 | "Swing" | ✅ preset → internal lengths (Scalp/Intraday/Swing) |
| Anti Flip Score Filter | in_6 | true | ✅ block immediate direction flips |

### 🔒 Session
| Label | input id | value |
|---|---|---|
| Use Session Filter | in_7 | true |
| Time (server time) | in_8 | "0700-1800" |

### 🎯 ZynAlgo Entry / SL / TP
| Label | input id | value | meaning |
|---|---|---|---|
| Enable TP/SL Logic | in_9 | true | |
| Distance | in_10 | 2.8 | ✅ SL distance = 2.8 × ATR (🔶 ATR length TBD) |
| Enable TP1 | in_11 | true | |
| R:R Ratio TP1 | in_12 | 1 | ✅ TP1 at 1R |
| Enable TP2 | in_13 | true | |
| R:R Ratio TP2 | in_14 | 2 | ✅ TP2 at 2R |
| Enable TP3 | in_15 | true | |
| R:R Ratio TP3 | in_16 | 3 | ✅ TP3 at 3R |
| Show TP/SL Box | in_17 | true | |
| TP/SL Box Width | in_18 | 10 | bars |
| Stored TP/SL Boxes | in_19 | 25 | max retained boxes |

### 🖥️ Dashboard UI
| Label | input id | value |
|---|---|---|
| Show Dashboard | in_20 | true |
| Dashboard X Position | in_21 | "Right" |
| Dashboard Y Position | in_22 | "Top" |
| Dashboard Scale | in_23 | "Normal" |
| Compact mode | in_24 | true |
| Mobile Dashboard | in_25 | false |
| Mobile Dashboard X Position | in_26 | "Right" |
| Mobile Dashboard Y Position | in_27 | "Bottom" |
| Show Signal Labels | in_28 | true |
| Show TP/SL Result Shapes | in_29 | true |

### 📊 Performance
| Label | input id | value |
|---|---|---|
| Profit Factor Lookback Candles | in_30 | 10000 |

### Output plots (Style tab → study values)
`TP1/TP2/TP3 Hit Long`, `TP1/TP2/TP3 Hit Short`, `SL Hit Long`, `SL Hit Short`
(boolean markers, above/below bar). Graphic objects: Boxes, Pane labels, Lines, Tables.

---

## 2. Dashboard = the calculation family (✅ observed live)

Read from `data_get_pine_tables` on **OANDA:XAUUSD, 1D**, current bar:

```
Scalper Pro v4 | XAUUSD 1D | READY
MARKET STATE
Market   | BEAR  | HTF DN
ADX      | 36.8  | STRONG
RSI      | 35.6  | BEAR
Volume   | 0.57x | normal
ACTIVE POSITION
Position | —     | —
Entry    | —
Stop Loss| —
TP1      | —
PERFORMANCE
Prof. Factor | ? | POOR
Expectancy   | ? | per trade
```

⇒ This is a **score-based confluence model**. Four state inputs feed a 0–100 score:
1. **Market** trend (BULL/BEAR) + **HTF** direction (UP/DN)
2. **ADX** strength (STRONG/WEAK)
3. **RSI** momentum (BULL/BEAR)
4. **Volume** ratio (x of average → normal/high)

Score ≥ Minimum Score (60) in a direction, inside session, past cooldown ⇒ entry.
SL = Distance×ATR; TP1/2/3 at R:R 1/2/3. Self-tracks Profit Factor / Expectancy.

### Deterministic anchors — ✅ ALL MATCH EXACTLY (overlay verified 2026-06-19)
XAUUSD **Daily**:
| metric | original | our recon | match |
|---|---|---|---|
| ADX | 36.8 STRONG | 36.8 STRONG | ✅ |
| RSI | 35.6 BEAR | 35.6 BEAR | ✅ |
| Volume ratio | 0.57x normal | 0.57x normal | ✅ |
| Market / HTF | BEAR / HTF DN | BEAR / HTF DN | ✅ |

XAUUSD **H1** (the design TF — both held an identical live SHORT):
| metric | original | our recon | match |
|---|---|---|---|
| ADX | 35.2 STRONG | 35.2 STRONG | ✅ |
| RSI | 39.7 BEAR | 39.7 BEAR | ✅ |
| Volume | 0.75x normal | 0.75x normal | ✅ |
| Entry | 4242.040 | 4242.040 | ✅ EXACT |
| Stop Loss | 4303.624 | 4303.624 | ✅ EXACT |
| TP1 | 4180.456 | 4180.456 | ✅ EXACT |

⇒ Entry/SL/TP identical to the cent ⇒ **ATR length = 14 confirmed**, SL = 2.8×ATR
confirmed, R:R 1/2/3 confirmed, signal fired on the SAME bar. Sub-indicator lengths
(RSI 14, DMI 14/14, Vol SMA 20, EMA 21/50 Swing) all confirmed by exact value match.

---

## 3. Confirmed vs guessed

### ✅ Confirmed
- Full input list, names, sections, defaults (above).
- Output = dashboard table + signal labels + TP/SL boxes + hit markers.
- SL = 2.8×ATR; TP R:R = 1/2/3.
- Dashboard sub-states: Market+HTF, ADX, RSI, Volume.

### ✅ Now CONFIRMED by exact overlay match
- RSI length = 14; BULL if >50.
- ADX via `ta.dmi(14,14)`; STRONG if >25.
- Volume ratio = volume / `ta.sma(volume, 20)`.
- ATR length = 14; SL = 2.8×ATR; TP R:R 1/2/3.
- Market trend = EMA(21) vs EMA(50) for Swing (BEAR matched on D and H1).
- HTF dir = close vs HTF EMA — matched (HTF DN on both D and H1).
- Score crosses 60 on the SAME bar the original fires (entry bar identical on H1).

### 🔶 Still approximate / diverging (refine next)
- **Signal frequency vs TF.** On Daily our recon fired ~25 signals; original fired 0
  (no boxes). Original is intraday-only on signals → likely the **session filter**
  (`0700-1800`) suppresses Daily bars in the original; our `time()` session check lets
  Daily through. On H1 frequencies are comparable (~25–33).
- **Score magnitude.** Original showed this trade's quality as **"OK"** (60–79 band);
  ours computes **100**. Entry threshold (60) is right, but our weighting is too
  generous → recalibrate component weights.
- **Hit markers.** Ours re-draw a circle every in-position bar (teal "blobs"); original
  draws ONE outcome label at exit. Fix: fire once on the hit transition.
- **Result labels.** Original draws `BUY/SELL` then `TP +1R` / `WIN 3R` / `SL -1R` with
  bar-count; ours lacks these. Only +1R / +3R / -1R seen (no +2R) ⇒ TP2 is pass-through,
  exits labeled at TP1 and TP3 only.
- **Performance panel.** Original PF 6.08 / Exp 1.06R; ours "?" because the tracker
  doesn't log trades closed by reversal. Align close/PF logic.

### Position-management model (inferred from label ledger, then verified)
Durations up to 272 bars to TP3 rule out a tight BE/TP1 lock. Final model (v3.1):
- enter on signal; **fixed SL −1R, target TP3 +3R**; hold ≥ `cooldownBars` (25) ignoring
  opposite signals (anti-flip).
- exits: TP3 → "WIN 3R" (+3R) ; initial SL → "SL −1R" (−1R) ; cooled opposite signal →
  REVERSE, realized profit "TP +1R" / loss "SL −1R". TP1/TP2 are milestones only.
- This **reproduces the live trade exactly** (Entry 4242.040 / SL 4303.624 / TP1 4180.456).

### 🔴 The one remaining gap — entry selectivity (score formula)
Everything above is reproduced. PF still diverges (ours 1.30 vs 6.08) because our proxy
score (votes×25 + ADX) fires LOOSER and less accurately than the original's. Symptom:
ours reads **100 / "HIGH"**, original reads **"OK" (60–79)** for the same setup ⇒ our
weighting is too generous and our entries hit SL too often. Closing this needs the actual
Stability / Smart-Filter / Anti-Flip / score logic — the hard core of a black-box recover.

---

## 4. Comparison log
| date | TF/symbol | change | result |
|---|---|---|---|
| 2026-06-19 | XAUUSD D | v1 overlay | dashboard anchors EXACT; recon over-fires (25 vs 0 signals) |
| 2026-06-19 | XAUUSD H1 | v1 overlay | anchors + live Entry/SL/TP EXACT; PF/labels/markers differ |
| 2026-06-20 | XAUUSD H1 | v2 dashboard cosmetics + state machine | dashboard FORMAT exact; PF 2.73; churns |
| 2026-06-20 | XAUUSD H1 | v3 hold-to-TP3/SL + reverse | live Entry/SL/TP EXACT again; PF 1.08 (whipsaw) |
| 2026-06-20 | XAUUSD H1 | v3.1 + cooldown/anti-flip | live trade EXACT; PF 1.30 vs 6.08 — gap = entry selectivity |
| 2026-06-21 | BTC/NQ/EUR sweep | cross-instrument compare | found 3-state Market, ADX tiers, formats, chop-filter (below) |
| 2026-06-21 | XAUUSD H1 | v3.2 (ADX tiers + formats + chop gate) | ADX tier + formats now EXACT; SIDEWAY threshold still uncalibrated |

## 5. Fidelity scorecard (v3.2)
| aspect | status |
|---|---|
| Dashboard values + format (incl. ADX FLAT/MED/STRONG, trailing-zero trim) | ✅ exact |
| Sub-indicators + lengths (RSI/ADX/Vol/EMA/HTF/ATR) | ✅ exact |
| SL/TP geometry (2.8×ATR, R:R 1/2/3) | ✅ exact |
| Live position (entry/SL/TP) — trending instruments | ✅ exact (XAUUSD, NQ) |
| Label style + vocabulary (BUY/SELL, TP+1R/WIN 3R/SL−1R) | ✅ matches |
| PF/Expectancy mechanics | ✅ compute (different trade set) |
| Market BULL/BEAR/**SIDEWAY** threshold | 🟡 3-state added; exact flat cutoff uncalibrated |
| Entry selectivity → PF magnitude | 🔴 1.30 vs 6.08 (score + regime formula proprietary) |

## 6. Cross-instrument sweep findings (2026-06-21)
Overlaid both studies on the user's best combos. Dashboard sub-values matched everywhere;
divergences were all structural and now mostly implemented:

| symbol/TF | orig Market | orig ADX | orig position | note |
|---|---|---|---|---|
| BTCUSD H4 | **FLAT** | 16.1 FLAT | — (flat) | 3rd market state; original sits out |
| NQ1! H4 | BULL | 13.7 FLAT | BUY OK | trades even with weak ADX (so ADX≠trade gate) |
| EURUSD H1 | **SIDEWAY** (hdr "SIDEWAY EMA Flat") | 25.2 **MED** | — (flat) | original sits out chop |
| XAUUSD H1 | BEAR | 35.2 STRONG | SELL OK | trends → trades |

Discoveries:
- **Market is 3-state** BULL / BEAR / **SIDEWAY (a.k.a. FLAT, "EMA Flat")**. The original
  does NOT trade in SIDEWAY → this is the real selectivity filter behind PF≈6 (it skips chop).
- **ADX label is 3-tier**: FLAT (<~20) / MED (~20–30) / STRONG (≥~30). (was STRONG/WEAK).
- **Number format trims trailing zeros**: RSI/ADX `0.#`, Volume `0.##` (e.g. "51", "0.1x").
- ADX strength is NOT the trade gate (NQ traded at ADX 13.7); **regime (trend vs flat) is**.

Open: the exact SIDEWAY/flat cutoff (EMA-slope based, but threshold unknown) and the score
weighting. Both are proprietary; with only ~4 reference points, fitting them precisely would
overfit. Current chop-gate uses slow-EMA slope > 0.6 ATR / 10 bars (🔶 placeholder).
