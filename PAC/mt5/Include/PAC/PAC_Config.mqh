//+------------------------------------------------------------------+
//| PAC_Config.mqh                                                    |
//| AUTO-GENERATED — DO NOT EDIT                                      |
//| Source: hedgehog/proposer/pac/config.py                           |
//| Regenerate: python tools/python_config_to_mql5_set.py --regen     |
//+------------------------------------------------------------------+
#property strict
#ifndef __PAC_CONFIG_MQH__
#define __PAC_CONFIG_MQH__

// §1 Risk Management
input double InpRiskPercent                         = 1.0;  // → Config.risk_percent
input double InpMinRR                               = 1.5;  // → Config.min_rr
input int    InpMaxTradesPerSession                 = 3;  // → Config.max_trades_per_session
input double InpDailyDDStopPct                      = -3.0;  // → Config.daily_dd_stop_pct
input double InpWeeklyDDStopPct                     = -5.0;  // → Config.weekly_dd_stop_pct
input string InpCorrelationGroups                   = "XAUUSD,US500;US500,US30,USTECH;USOIL,US500";  // → Config.correlation_groups
input bool   InpNewsFilterEnabled                   = false;  // → Config.news_filter_enabled
input int    InpNewsFilterWindowMin                 = 15;  // → Config.news_filter_window_min

// §3 Direction Filter
input int    InpEmaPeriod                           = 21;  // → Config.ema_period
input int    InpSmaPeriod                           = 61;  // → Config.sma_period
input int    InpDynamicCrossMaxBars                 = 2;  // → Config.dynamic_cross_max_bars
input bool   InpMmdStrict                           = false;  // → Config.mmd_strict
input bool   InpDirectionStrict                     = true;  // → Config.direction_strict

// §4 Entry Trigger
input double InpWickToBodyRatioMin                  = 2.0;  // → Config.wick_to_body_ratio_min
input double InpCandleRangeAtrMultMin               = 0.5;  // → Config.candle_range_atr_multiple_min
input int    InpClosePositionWithinWickPct          = 33;  // → Config.close_position_within_wick_pct
input double InpConfluencePipsAtrMult               = 0.3;  // → Config.confluence_pips_threshold_atr_multiple
input int    InpConfluenceRequiredLevels            = 1;  // → Config.confluence_required_levels

// §5 Target Engine
input double InpImpulseAtrMultMin                   = 1.5;  // → Config.impulse_atr_multiple_min
input int    InpMaxActiveMeasuredMoves              = 5;  // → Config.max_active_measured_moves
input string InpFibLevelsRetracement                = "0.382,0.5,0.618";  // → Config.fib_levels_retracement
input string InpFibLevelsExtension                  = "1.382,1.618,2.618";  // → Config.fib_levels_extension
input double InpClusterPipsAtrMult                  = 0.3;  // → Config.cluster_pips_threshold_atr_multiple
input int    InpClusterMemberMin                    = 2;  // → Config.cluster_member_min
input int    InpOvershootBarsMin                    = 3;  // → Config.overshoot_bars_min
input double InpSettleBufferAtrMult                 = 0.5;  // → Config.settle_buffer_atr_multiple

// §6 Setups
input double InpTrapFirstTryLevel                   = 0.382;  // → Config.trap_first_try_level
input double InpTrapFailureThreshAtrMult            = 0.2;  // → Config.trap_failure_threshold_atr_multiple
input int    InpTrapMaxBarsBetweenTries             = 20;  // → Config.trap_max_bars_between_tries
input double InpTrapMaxFirstTryPenetrationFib       = 0.2;  // → Config.trap_max_first_try_penetration_fib
input double InpFailMinFirstAttemptDepthFib         = 0.382;  // → Config.fail_min_first_attempt_depth_fib
input double InpFailMaxFirstAttemptDepthFib         = 1.0;  // → Config.fail_max_first_attempt_depth_fib
input double InpFailSecondAttemptShortfallAtrMult   = 0.3;  // → Config.fail_second_attempt_shortfall_atr_multiple
input int    InpFailMaxBarsBetweenAttempts          = 30;  // → Config.fail_max_bars_between_attempts
input int    InpSpikeMinBars                        = 3;  // → Config.spike_min_bars
input double InpSpikeMinMagnitudeAtr                = 3.0;  // → Config.spike_min_magnitude_atr
input int    InpSpikeMaxCounterBars                 = 1;  // → Config.spike_max_counter_bars
input double InpPullbackInvalidationFib             = 0.5;  // → Config.pullback_invalidation_fib
input double InpExhaustionFib                       = 1.382;  // → Config.exhaustion_fib
input int    InpChannelMinBars                      = 5;  // → Config.channel_min_bars

// §7 Order Management
input int    InpWickBufferInSpreads                 = 1;  // → Config.wick_buffer_in_spreads
input double InpMinSlDistanceAtrMult                = 0.3;  // → Config.min_sl_distance_atr_multiple
input int    InpMaxSlippagePips                     = 3;  // → Config.max_slippage_pips
input bool   InpPartialsEnabled                     = false;  // → Config.partials_enabled
input double InpPartialsTriggerR                    = 1.0;  // → Config.partials_trigger_r
input double InpPartialsCloseFraction               = 0.5;  // → Config.partials_close_fraction
input bool   InpPartialsBreakevenAfter              = true;  // → Config.partials_breakeven_after
input bool   InpTrailingEnabled                     = false;  // → Config.trailing_enabled
input double InpTrailingActivationR                 = 1.5;  // → Config.trailing_activation_r
input double InpTrailingDistanceAtrMult             = 1.0;  // → Config.trailing_distance_atr_multiple
input bool   InpTrailingFreezeAtrAtActivation       = true;  // → Config.trailing_freeze_atr_at_activation

#endif // __PAC_CONFIG_MQH__
