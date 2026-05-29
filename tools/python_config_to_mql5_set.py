#!/usr/bin/env python
"""Generate PAC_Config.mqh + Presets/*.set from the Plan 4 Config dataclass.

Single source of truth: ``hedgehog.proposer.pac.config.Config``. This script
holds all MQL5-specific metadata (input groupings, name prefixes, type
overrides) in ``MQL5_MAPPING`` below. Every Config field MUST appear in the
mapping — the generator raises ``ValueError`` on any unmapped field so a new
Config knob can never silently fall out of the MQL5 inputs.

Modes:
    --regen           Emit PAC_Config.mqh + all 7 .set presets
    --check           Diff generated-vs-on-disk; exit 1 on drift
    --preset SYMBOL   Emit one .set preset for the given symbol
"""
from __future__ import annotations

import argparse
import dataclasses
import difflib
import sys
from pathlib import Path

# Make ``hedgehog`` importable regardless of cwd.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hedgehog.proposer.pac.config import Config  # noqa: E402

# The 7 PAC-whitelisted symbols (one preset per symbol).
PRESET_SYMBOLS = ("XAUUSD", "USOIL", "US500", "NAS100", "EURUSD", "GBPUSD", "USDCAD")

# ─── MQL5 metadata ──────────────────────────────────────────────────
# Maps every Config field → (MQL5 input name, group label, type override).
# A non-None override forces the MQL5 type (used for tuple fields that
# serialize to a comma-joined string input). Reconciled field-for-field
# against config.Config — keep in sync or the generator will raise.
MQL5_MAPPING: dict[str, tuple[str, str, str | None]] = {
    # §1 Risk Management
    "risk_percent":                 ("InpRiskPercent",          "§1 Risk Management", None),
    "min_rr":                       ("InpMinRR",                "§1 Risk Management", None),
    "max_trades_per_session":       ("InpMaxTradesPerSession",  "§1 Risk Management", None),
    "daily_dd_stop_pct":            ("InpDailyDDStopPct",       "§1 Risk Management", None),
    "weekly_dd_stop_pct":           ("InpWeeklyDDStopPct",      "§1 Risk Management", None),
    "correlation_groups":           ("InpCorrelationGroups",    "§1 Risk Management", "string"),
    "news_filter_enabled":          ("InpNewsFilterEnabled",    "§1 Risk Management", None),
    "news_filter_window_min":       ("InpNewsFilterWindowMin",  "§1 Risk Management", None),

    # §3.1 EMA/SMA Sentiment
    "ema_period":                   ("InpEmaPeriod",            "§3 Direction Filter", None),
    "sma_period":                   ("InpSmaPeriod",            "§3 Direction Filter", None),
    "dynamic_cross_max_bars":       ("InpDynamicCrossMaxBars",  "§3 Direction Filter", None),
    "mmd_strict":                   ("InpMmdStrict",            "§3 Direction Filter", None),
    "direction_strict":             ("InpDirectionStrict",      "§3 Direction Filter", None),

    # §4 Entry Trigger
    "wick_to_body_ratio_min":               ("InpWickToBodyRatioMin",        "§4 Entry Trigger", None),
    "candle_range_atr_multiple_min":        ("InpCandleRangeAtrMultMin",     "§4 Entry Trigger", None),
    "close_position_within_wick_pct":       ("InpClosePositionWithinWickPct", "§4 Entry Trigger", None),
    "confluence_pips_threshold_atr_multiple": ("InpConfluencePipsAtrMult",   "§4 Entry Trigger", None),
    "confluence_required_levels":           ("InpConfluenceRequiredLevels",  "§4 Entry Trigger", None),

    # §5 Target Engine
    "impulse_atr_multiple_min":             ("InpImpulseAtrMultMin",         "§5 Target Engine", None),
    "max_active_measured_moves":            ("InpMaxActiveMeasuredMoves",    "§5 Target Engine", None),
    "fib_levels_retracement":               ("InpFibLevelsRetracement",      "§5 Target Engine", "string"),
    "fib_levels_extension":                 ("InpFibLevelsExtension",        "§5 Target Engine", "string"),
    "cluster_pips_threshold_atr_multiple":  ("InpClusterPipsAtrMult",        "§5 Target Engine", None),
    "cluster_member_min":                   ("InpClusterMemberMin",          "§5 Target Engine", None),
    "overshoot_bars_min":                   ("InpOvershootBarsMin",          "§5 Target Engine", None),
    "settle_buffer_atr_multiple":           ("InpSettleBufferAtrMult",       "§5 Target Engine", None),

    # §6 Setup Recognition
    "trap_first_try_level":                 ("InpTrapFirstTryLevel",            "§6 Setups", None),
    "trap_failure_threshold_atr_multiple":  ("InpTrapFailureThreshAtrMult",     "§6 Setups", None),
    "trap_max_bars_between_tries":          ("InpTrapMaxBarsBetweenTries",      "§6 Setups", None),
    "trap_max_first_try_penetration_fib":   ("InpTrapMaxFirstTryPenetrationFib", "§6 Setups", None),
    "fail_min_first_attempt_depth_fib":     ("InpFailMinFirstAttemptDepthFib",  "§6 Setups", None),
    "fail_max_first_attempt_depth_fib":     ("InpFailMaxFirstAttemptDepthFib",  "§6 Setups", None),
    "fail_second_attempt_shortfall_atr_multiple": ("InpFailSecondAttemptShortfallAtrMult", "§6 Setups", None),
    "fail_max_bars_between_attempts":       ("InpFailMaxBarsBetweenAttempts",   "§6 Setups", None),
    "spike_min_bars":                       ("InpSpikeMinBars",                 "§6 Setups", None),
    "spike_min_magnitude_atr":              ("InpSpikeMinMagnitudeAtr",         "§6 Setups", None),
    "spike_max_counter_bars":               ("InpSpikeMaxCounterBars",          "§6 Setups", None),
    "pullback_invalidation_fib":            ("InpPullbackInvalidationFib",      "§6 Setups", None),
    "exhaustion_fib":                       ("InpExhaustionFib",                "§6 Setups", None),
    "channel_min_bars":                     ("InpChannelMinBars",               "§6 Setups", None),

    # §7 Order Management
    "wick_buffer_in_spreads":               ("InpWickBufferInSpreads",          "§7 Order Management", None),
    "min_sl_distance_atr_multiple":         ("InpMinSlDistanceAtrMult",         "§7 Order Management", None),
    "max_slippage_pips":                    ("InpMaxSlippagePips",              "§7 Order Management", None),
    "partials_enabled":                     ("InpPartialsEnabled",              "§7 Order Management", None),
    "partials_trigger_r":                   ("InpPartialsTriggerR",             "§7 Order Management", None),
    "partials_close_fraction":              ("InpPartialsCloseFraction",        "§7 Order Management", None),
    "partials_breakeven_after":             ("InpPartialsBreakevenAfter",       "§7 Order Management", None),
    "trailing_enabled":                     ("InpTrailingEnabled",              "§7 Order Management", None),
    "trailing_activation_r":                ("InpTrailingActivationR",          "§7 Order Management", None),
    "trailing_distance_atr_multiple":       ("InpTrailingDistanceAtrMult",      "§7 Order Management", None),
    "trailing_freeze_atr_at_activation":    ("InpTrailingFreezeAtrAtActivation", "§7 Order Management", None),
}

# Visual-alignment widths for the generated `input` declarations.
_TYPE_WIDTH = 6   # longest base type token is "double"/"string" (6)
_NAME_WIDTH = 38  # longest Inp name (InpFailSecondAttemptShortfallAtrMult = 36) + pad


def _validate_mapping() -> None:
    """Fail loudly if Config and MQL5_MAPPING have drifted apart."""
    config_fields = {f.name for f in dataclasses.fields(Config)}
    mapped = set(MQL5_MAPPING)
    missing = config_fields - mapped
    if missing:
        raise ValueError(
            "Config fields missing from MQL5_MAPPING: "
            + ", ".join(sorted(missing))
        )
    extra = mapped - config_fields
    if extra:
        raise ValueError(
            "MQL5_MAPPING references non-existent Config fields: "
            + ", ".join(sorted(extra))
        )


def _mql5_type(value, override: str | None) -> str:
    if override is not None:
        return override
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "double"
    if isinstance(value, (list, tuple)):
        return "string"
    return "string"


def _flatten_tuple(value) -> str:
    """Flatten a (possibly nested) tuple/list to a comma-joined string.

    correlation_groups is nested — ``(("XAUUSD","US500"), ...)`` — and is
    serialized with ';' between groups and ',' within a group so the MQL5
    Universe_InitCorrelationGroups parser can round-trip it.
    """
    if value and isinstance(value[0], (list, tuple)):
        return ";".join(",".join(str(x) for x in group) for group in value)
    return ",".join(str(x) for x in value)


def _mql5_value(value, mtype: str) -> str:
    """Render a Config value as an MQL5 literal for `PAC_Config.mqh`."""
    if mtype == "bool":
        return "true" if value else "false"
    if mtype == "string":
        if isinstance(value, (list, tuple)):
            return f'"{_flatten_tuple(value)}"'
        return f'"{value}"'
    return repr(value)  # int / float — repr(1.0)=='1.0', repr(3)=='3'


def _set_value(value, mtype: str) -> str:
    """Render a Config value for the `.set` preset (key=value, no quotes)."""
    if mtype == "bool":
        return "true" if value else "false"
    if isinstance(value, (list, tuple)):
        return _flatten_tuple(value)
    return str(value)


def generate_mqh_text() -> str:
    _validate_mapping()
    cfg = Config()
    lines = [
        "//+------------------------------------------------------------------+",
        "//| PAC_Config.mqh                                                    |",
        "//| AUTO-GENERATED — DO NOT EDIT                                      |",
        "//| Source: hedgehog/proposer/pac/config.py                           |",
        "//| Regenerate: python tools/python_config_to_mql5_set.py --regen     |",
        "//+------------------------------------------------------------------+",
        "#property strict",
        "#ifndef __PAC_CONFIG_MQH__",
        "#define __PAC_CONFIG_MQH__",
        "",
    ]
    current_group = ""
    for fld in dataclasses.fields(Config):
        mql5_name, group, override = MQL5_MAPPING[fld.name]
        if group != current_group:
            if current_group:
                lines.append("")
            lines.append(f"// {group}")
            current_group = group
        value = getattr(cfg, fld.name)
        mtype = _mql5_type(value, override)
        mvalue = _mql5_value(value, mtype)
        type_padded = mtype.ljust(_TYPE_WIDTH)
        name_padded = mql5_name.ljust(_NAME_WIDTH)
        lines.append(
            f"input {type_padded} {name_padded} = {mvalue};  // → Config.{fld.name}"
        )
    lines.append("")
    lines.append("#endif // __PAC_CONFIG_MQH__")
    return "\n".join(lines) + "\n"


def generate_preset_text(symbol: str) -> str:
    _validate_mapping()
    cfg = Config()
    lines = [
        f"; PAC_{symbol}_M5.set — AUTO-GENERATED",
        f"; Source: hedgehog/proposer/pac/config.py",
        f"; Regenerate: python tools/python_config_to_mql5_set.py --preset {symbol}",
        "",
    ]
    for fld in dataclasses.fields(Config):
        mql5_name, _, override = MQL5_MAPPING[fld.name]
        value = getattr(cfg, fld.name)
        mtype = _mql5_type(value, override)
        lines.append(f"{mql5_name}={_set_value(value, mtype)}")
    return "\n".join(lines) + "\n"


def _do_regen(mqh_output: Path, presets_dir: Path) -> int:
    mqh_output.parent.mkdir(parents=True, exist_ok=True)
    mqh_output.write_text(generate_mqh_text(), encoding="utf-8")
    presets_dir.mkdir(parents=True, exist_ok=True)
    for sym in PRESET_SYMBOLS:
        (presets_dir / f"PAC_{sym}_M5.set").write_text(
            generate_preset_text(sym), encoding="utf-8"
        )
    print(f"Generated {mqh_output} + {len(PRESET_SYMBOLS)} presets")
    return 0


def _do_check(mqh_output: Path, presets_dir: Path) -> int:
    expected_mqh = generate_mqh_text()
    if not mqh_output.exists():
        print(f"drift detected: {mqh_output} does not exist")
        return 1
    actual_mqh = mqh_output.read_text(encoding="utf-8")
    if expected_mqh != actual_mqh:
        print(f"drift detected in {mqh_output.name}:")
        sys.stdout.writelines(
            difflib.unified_diff(
                actual_mqh.splitlines(keepends=True),
                expected_mqh.splitlines(keepends=True),
                fromfile="actual", tofile="expected",
            )
        )
        return 1
    for sym in PRESET_SYMBOLS:
        preset = presets_dir / f"PAC_{sym}_M5.set"
        expected = generate_preset_text(sym)
        if not preset.exists():
            print(f"drift detected: {preset.name} does not exist")
            return 1
        if expected != preset.read_text(encoding="utf-8"):
            print(f"drift detected in {preset.name}")
            return 1
    print("no drift")
    return 0


def _do_preset(symbol: str, presets_dir: Path) -> int:
    presets_dir.mkdir(parents=True, exist_ok=True)
    (presets_dir / f"PAC_{symbol}_M5.set").write_text(
        generate_preset_text(symbol), encoding="utf-8"
    )
    print(f"Generated PAC_{symbol}_M5.set")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--regen", action="store_true",
                        help="Emit PAC_Config.mqh + all .set presets")
    parser.add_argument("--check", action="store_true",
                        help="Diff against on-disk; exit 1 on drift")
    parser.add_argument("--preset", type=str, default=None,
                        help="Emit one .set preset for SYMBOL")
    parser.add_argument("--mqh-output", type=str,
                        default="PAC/mt5/Include/PAC/PAC_Config.mqh")
    parser.add_argument("--presets-dir", type=str,
                        default="PAC/mt5/Presets")
    args = parser.parse_args(argv)

    mqh_output = Path(args.mqh_output)
    presets_dir = Path(args.presets_dir)

    if args.regen:
        return _do_regen(mqh_output, presets_dir)
    if args.check:
        return _do_check(mqh_output, presets_dir)
    if args.preset:
        return _do_preset(args.preset, presets_dir)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
