# PAC MT5 Expert Advisor

Implementation of the Price Action Cycle (PAC) strategy as an MT5 Expert
Advisor + MMD cloud indicator. This is the MQL5 leg of the Phase 2
"two-engine" build: it is a minimal 1:1 port of the Python reference
implementation at `hedgehog/proposer/pac/` (Plan 4), and is cross-validated
against it via the Phase 3 triangulation contract (ledger diff).

Behavioural spec: `../strategy_ea.md`.

## Status — read this first

**The MQL5 sources in this tree have NOT yet been compiled or run in
MetaEditor / MetaTrader 5.** They were written 1:1 against the Python
reference and the design spec, but no `.ex5` has been produced and no
Strategy Tester run has been executed. The next step before any backtest
is a **compile pass**: open each file in MetaEditor and fix whatever the
MQL5 compiler flags (forward-reference ordering, implicit casts, `iCustom`
argument arity, CTrade API drift, etc.). Until that pass is done, treat
everything here as source-complete but unvalidated.

Consequently:

- The end-to-end Strategy Tester smoke (Plan 5 Task 21) is **deferred** —
  it requires a clean MetaEditor compile plus a running MT5 with history,
  neither of which was available when this tree was authored.
- The MQL5 unit-test scripts under `Scripts/PAC_Tests/` likewise have not
  been run; `tools/run_mql5_tests.py` (below) is ready to drive them once
  MT5 is present, and its log-parsing layer is unit-tested independently
  of MT5.

## One-time setup

1. **Install MT5** with the 7 whitelisted symbols on Market Watch:
   XAUUSD, USOIL, US500, NAS100, EURUSD, GBPUSD, USDCAD.

2. **Junction this repo's `PAC/mt5/` into the MT5 data directory** so source
   edits compile in place (no copying). On Windows, from an Administrator
   `cmd` prompt:

   ```cmd
   mklink /J "%APPDATA%\MetaQuotes\Terminal\<TERMINAL_ID>\MQL5" "<REPO>\PAC\mt5"
   ```

   - `<TERMINAL_ID>` is your terminal's data subfolder (the long hex name
     under `%APPDATA%\MetaQuotes\Terminal\`).
   - `<REPO>` is the absolute path to this checkout of `NotFinancialAdvice`.

   After the junction, MetaEditor sees `Indicators/PAC`, `Experts/PAC`,
   `Include/PAC`, `Scripts/PAC_Tests`, and `Presets` exactly as they appear
   in this directory.

3. **Compile (compile pass — currently pending, see Status above).** Order
   matters because the EA loads the indicator via `iCustom`:

   1. MetaEditor → `Indicators/PAC/PAC_MMD_Clouds.mq5` → F7. Produces
      `PAC_MMD_Clouds.ex5`.
   2. MetaEditor → `Experts/PAC/PAC_EA.mq5` → F7. Resolves the `iCustom`
      reference to the indicator compiled in step 1 and pulls in every
      `Include/PAC/*.mqh` module.
   3. Optionally compile each `Scripts/PAC_Tests/test_pac_*.mq5` to run the
      MQL5-side unit tests.

## Config bridge — generated files, do not hand-edit

`Include/PAC/PAC_Config.mqh` and `Presets/PAC_*_M5.set` (7 files) are
**auto-generated** from the single source of truth,
`hedgehog/proposer/pac/config.py` (the `Config` dataclass), by
`tools/python_config_to_mql5_set.py`. Drift between the Python config and
the MQL5 inputs is structurally impossible because both come from the same
generator run.

Regenerate after any change to `Config`:

```bash
python tools/python_config_to_mql5_set.py --regen
```

Check for drift (exit 1 if the committed files are stale — suitable for a
pre-commit hook / CI gate):

```bash
python tools/python_config_to_mql5_set.py --check
```

Emit a single symbol's preset:

```bash
python tools/python_config_to_mql5_set.py --preset EURUSD
```

## Running the EA

> Requires the compile pass above to have succeeded.

### Strategy Tester (single-symbol backtest)

1. View → Strategy Tester (Ctrl+R).
2. Expert: `PAC_EA`.
3. Symbol: EURUSD (or any whitelisted symbol).
4. Period: M5 (the strategy and the MMD indicator are M5-only; the
   indicator returns `INIT_FAILED` on any other timeframe).
5. Date range: as desired.
6. Modeling: "Every tick based on real ticks" (recommended for parity with
   the Python tick/bar semantics).
7. Inputs: Load `Presets/PAC_<SYMBOL>_M5.set`.
8. Start.

### Live / forward chart

1. Open a `<SYMBOL>` M5 chart.
2. Drag `PAC_EA` from Navigator → Expert Advisors → PAC onto the chart.
3. Enable "Algo Trading" in the toolbar.
4. Inputs: Load the matching `Presets/PAC_<SYMBOL>_M5.set`.

### Ledger output

Closed-trade rows (and partial-close rows sharing a `trade_id`) are written
to `<MT5_DataDir>/MQL5/Files/PAC/ledger.csv` — i.e. `MQL5/Files/` plus the
relative path in `InpLedgerPath` (default `PAC\ledger.csv`). The schema is
**21 columns, byte-parity with Plan 4's `ledger.py`** so the two engines'
ledgers can be diffed directly in Phase 3.

## Tests

Two independent test surfaces:

1. **MQL5 unit scripts** — `Scripts/PAC_Tests/test_pac_*.mq5`. Each emits
   one `MQL5TEST {...}` sentinel line per assertion via the shared macros in
   `Scripts/PAC_Tests/helpers/TestRunner.mqh`:

   ```
   MQL5TEST {"test":"name","result":"PASS"}
   MQL5TEST {"test":"name","result":"FAIL","expected":"X","got":"Y"}
   ```

   Run an individual script in MetaEditor (F5 on a chart), or drive them all
   from Python:

   ```bash
   python tools/run_mql5_tests.py
   ```

   `run_mql5_tests.py` launches MT5 per script, reads the resulting log,
   greps the `MQL5TEST {...}` sentinels, aggregates pass/fail, and sets its
   exit code (non-zero on any FAIL, any malformed sentinel, or **zero**
   sentinels — a run that produced nothing is never reported green). The
   MT5-invocation layer only runs where MT5 is installed; the log-parsing
   layer is pure and unit-tested in `tools/tests/test_run_mql5_tests.py`. To
   parse a previously captured log without invoking MT5:

   ```bash
   python tools/run_mql5_tests.py --log-file <path-to-mt5.log>
   ```

2. **Python parser tests** — `tools/tests/test_run_mql5_tests.py` and
   `tools/tests/test_python_config_to_mql5_set.py`. Run with:

   ```bash
   python -m pytest tools/tests -q
   ```

These tests cover the MQL5-specific plumbing (sentinel parsing, config-bridge
generation). Algorithmic *equivalence* between the MQL5 EA and the Python
engine is not asserted here — it is the job of Phase 3 (below).

## Module map — MQL5 file ↔ `strategy_ea.md` section ↔ Plan 4 Python module

Each `Include/PAC/*.mqh` mirrors exactly one Plan 4 Python module; the EA
orchestrator mirrors `engine.py`. (Mirrors the Plan 4 module ↔ section map.)

| MQL5 file | `strategy_ea.md` section | Plan 4 Python module |
|---|---|---|
| `Include/PAC/PAC_Pip.mqh` | §0.4 Pip definitions | `universe.PIP_FACTOR_BY_SYMBOL` |
| `Include/PAC/PAC_TimeUtil.mqh` | §2.3 Sessions (DST UTC↔PLT) | `helpers/timeutil.py` |
| `Include/PAC/PAC_Universe.mqh` | §2 Universe, §1.6 correlation groups | `universe.py` |
| `Include/PAC/PAC_ATR.mqh` | §0.4 ATR(20) baseline | `helpers/atr.py` |
| `Include/PAC/PAC_Swing.mqh` | §0 ATR-ZigZag swings | `helpers/swing.py` |
| `Indicators/PAC/PAC_MMD_Clouds.mq5` | §3.2 MMD clouds (Pine port) | `mmd.py` (cloud math) |
| `Include/PAC/PAC_MMD.mqh` | §3.2 MMD alignment classify | `mmd.classify_alignment` |
| `Include/PAC/PAC_Signals.mqh` | §3 Direction filter + §4 Entry trigger | `signals.py` |
| `Include/PAC/PAC_Targets.mqh` | §5 Target engine (MM / fib / clusters) | `targets.py` |
| `Include/PAC/PAC_Setups.mqh` | §6 Setup state machines (trap/fail/spike) | `setups.py` |
| `Include/PAC/PAC_Risk.mqh` | §1 Risk management | `risk.py` |
| `Include/PAC/PAC_Orders.mqh` | §7 Order management + ShouldOpen (CTrade) | `orders.py` |
| `Include/PAC/PAC_Logger.mqh` | — (ledger I/O) | `ledger.py` (21-col schema) |
| `Include/PAC/PAC_Config.mqh` | — (all tunables) | `config.Config` (generated) |
| `Experts/PAC/PAC_EA.mq5` | §3–§7 bar-loop orchestration | `engine.py` `run_backtest` |

Only `<Trade\Trade.mqh>` (CTrade) is imported from the MQL5 standard
library, and that import is confined to `PAC_Orders.mqh`.

## Phase 3 — triangulation

After Plan 5's compile pass and Strategy Tester smoke land, Phase 3 runs
both engines on identical inputs and diffs the two 21-column ledgers
(trade counts, prices within tolerance, categorical fields such as
`setup_type` / `mmd_alignment` / `d1_zone`). The triangulation contract is
defined in the Phase 2 implementation design
(`2026-05-26-phase-2-implementation-design.md`, "Triangulation contract",
held in the planning workspace). Discrepancies beyond tolerance are Phase 3
investigation items; they do not block the Plan 5 merge.
