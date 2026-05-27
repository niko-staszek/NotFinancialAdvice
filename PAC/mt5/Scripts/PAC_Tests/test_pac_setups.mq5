//+------------------------------------------------------------------+
//| test_pac_setups.mq5                                               |
//|                                                                   |
//| Mirrors hedgehog/proposer/pac/tests/test_setups.py scenarios      |
//| against the MQL5 port in PAC_Setups.mqh. Each scenario constructs |
//| pre-seeded states, invokes the appropriate step function, and     |
//| anchors the expected state transition.                            |
//|                                                                   |
//| Config defaults baked in (must match Python Config defaults):     |
//|   trap_first_try_level                      = 0.382               |
//|   trap_failure_threshold_atr_multiple       = 0.2                 |
//|   trap_max_bars_between_tries               = 20                  |
//|   trap_max_first_try_penetration_fib        = 0.20                |
//|   fail_min_first_attempt_depth_fib          = 0.382               |
//|   fail_second_attempt_shortfall_atr_multiple = 0.3                |
//|   fail_max_bars_between_attempts            = 30                  |
//|   spike_min_bars                            = 3                   |
//|   spike_min_magnitude_atr                   = 3.0                 |
//|   spike_max_counter_bars                    = 1                   |
//|   channel_min_bars                          = 5                   |
//+------------------------------------------------------------------+
#property strict
#include "helpers\\TestRunner.mqh"
#include "..\\..\\Include\\PAC\\PAC_Setups.mqh"

// Local cfg defaults that mirror Config().
#define TRAP_FIRST_TRY_LEVEL                 0.382
#define TRAP_FAILURE_THRESH_ATR_MULT         0.2
#define TRAP_MAX_BARS_BETWEEN_TRIES          20
#define TRAP_MAX_FIRST_TRY_PENETRATION_FIB   0.20

#define FAIL_MIN_FIRST_ATTEMPT_DEPTH_FIB     0.382
#define FAIL_SECOND_ATTEMPT_SHORTFALL_ATR    0.3
#define FAIL_MAX_BARS_BETWEEN_ATTEMPTS       30

#define SPIKE_MIN_BARS                       3
#define SPIKE_MIN_MAGNITUDE_ATR              3.0
#define SPIKE_MAX_COUNTER_BARS               1
#define CHANNEL_MIN_BARS                     5

//+------------------------------------------------------------------+
//| Helper — build a bull MM matching the Python _bull_mm() fixture.  |
//+------------------------------------------------------------------+
MeasuredMove _MakeBullMM() {
    MeasuredMove mm;
    mm.id = 1;
    mm.direction = "bull";
    mm.a_bar = 10;  mm.a_price = 100.0;
    mm.b_bar = 20;  mm.b_price = 110.0;
    mm.c_bar = 25;  mm.c_price = 104.0;
    mm.d_target = 114.0;
    mm.validity = "valid";
    mm.overshoot_bars = 0;
    return mm;
}

//+------------------------------------------------------------------+
//| Anchor: test_trap_state_initial_is_idle                           |
//+------------------------------------------------------------------+
void TestTrapStateInitialIsIdle() {
    TrapState s;
    Setups_InitTrapState(s, 1);
    ASSERT_STR_EQ(s.state, "idle", "TrapState_initial_state_is_idle");
    ASSERT_FALSE(Setups_TrapTriggered(s), "TrapState_initial_not_triggered");
}

//+------------------------------------------------------------------+
//| Anchor: test_trap_state_first_try_failed                          |
//| Bull MM: trap_level=103.82, failure_thresh=0.2, max_pen=2.0.      |
//| Bar low=103.7 → distance=0.12<=0.2, penetration=0.12<=2.0         |
//| → first_try_failed with extreme=103.7                             |
//+------------------------------------------------------------------+
void TestTrapStateFirstTryFailed() {
    MeasuredMove mm = _MakeBullMM();
    TrapState s;
    Setups_InitTrapState(s, mm.id);

    bool advanced = Setups_StepTrap(
        s,
        /* open */ 104.0, /* high */ 104.2, /* low */ 103.7, /* close */ 104.0,
        /* bar_idx */ 26, mm, /* atr */ 1.0,
        TRAP_FIRST_TRY_LEVEL,
        TRAP_FAILURE_THRESH_ATR_MULT,
        TRAP_MAX_BARS_BETWEEN_TRIES,
        TRAP_MAX_FIRST_TRY_PENETRATION_FIB
    );

    ASSERT_TRUE(advanced, "TrapState_first_try_advanced");
    ASSERT_STR_EQ(s.state, "first_try_failed", "TrapState_first_try_failed_state");
    ASSERT_NEAR(s.first_try_extreme, 103.7, 1e-9, "TrapState_first_try_extreme_103_7");
    ASSERT_EQ_INT(s.first_try_bar, 26, "TrapState_first_try_bar_26");
}

//+------------------------------------------------------------------+
//| Full Trap lifecycle: idle → first_try_failed → second_try_failed  |
//| → triggered.                                                      |
//+------------------------------------------------------------------+
void TestTrapStateFullLifecycle() {
    MeasuredMove mm = _MakeBullMM();
    TrapState s;
    Setups_InitTrapState(s, mm.id);

    // Step 1: idle → first_try_failed.
    Setups_StepTrap(s, 104.0, 104.2, 103.7, 104.0, 26, mm, 1.0,
                    TRAP_FIRST_TRY_LEVEL, TRAP_FAILURE_THRESH_ATR_MULT,
                    TRAP_MAX_BARS_BETWEEN_TRIES,
                    TRAP_MAX_FIRST_TRY_PENETRATION_FIB);
    ASSERT_STR_EQ(s.state, "first_try_failed", "TrapLifecycle_step1_first_try_failed");

    // Step 2: another low near 103.7 within 0.2 of first_try_extreme.
    // |103.75 - 103.7| = 0.05 ≤ 0.2 → second_try_failed.
    Setups_StepTrap(s, 104.0, 104.2, 103.75, 104.0, 30, mm, 1.0,
                    TRAP_FIRST_TRY_LEVEL, TRAP_FAILURE_THRESH_ATR_MULT,
                    TRAP_MAX_BARS_BETWEEN_TRIES,
                    TRAP_MAX_FIRST_TRY_PENETRATION_FIB);
    ASSERT_STR_EQ(s.state, "second_try_failed", "TrapLifecycle_step2_second_try_failed");

    // Step 3: close reacts up by >= 0.2.
    // close=104.0 - second_extreme=103.75 = 0.25 ≥ 0.2 → triggered.
    Setups_StepTrap(s, 103.9, 104.1, 103.8, 104.0, 31, mm, 1.0,
                    TRAP_FIRST_TRY_LEVEL, TRAP_FAILURE_THRESH_ATR_MULT,
                    TRAP_MAX_BARS_BETWEEN_TRIES,
                    TRAP_MAX_FIRST_TRY_PENETRATION_FIB);
    ASSERT_STR_EQ(s.state, "triggered", "TrapLifecycle_step3_triggered");
    ASSERT_TRUE(Setups_TrapTriggered(s), "TrapLifecycle_predicate_returns_true");
}

//+------------------------------------------------------------------+
//| Anchor: test_fail_state_initial_is_idle                           |
//+------------------------------------------------------------------+
void TestFailStateInitialIsIdle() {
    FailState s;
    Setups_InitFailState(s, 1);
    ASSERT_FALSE(Setups_FailTriggered(s), "FailState_initial_not_triggered");
}

//+------------------------------------------------------------------+
//| Anchor: test_fail_state_first_attempt_pierces_38_pct              |
//| Bull MM: fib_382 = 103.82. Bar low=102.0 < 103.82 → advances.     |
//+------------------------------------------------------------------+
void TestFailStateFirstAttempt() {
    MeasuredMove mm = _MakeBullMM();
    FailState s;
    Setups_InitFailState(s, mm.id);

    bool advanced = Setups_StepFail(
        s,
        /* open */ 103.0, /* high */ 103.5, /* low */ 102.0, /* close */ 102.5,
        /* bar_idx */ 26, mm, /* atr */ 1.0,
        FAIL_MIN_FIRST_ATTEMPT_DEPTH_FIB,
        FAIL_SECOND_ATTEMPT_SHORTFALL_ATR,
        FAIL_MAX_BARS_BETWEEN_ATTEMPTS
    );
    ASSERT_TRUE(advanced, "FailState_first_attempt_advanced");
    ASSERT_STR_EQ(s.state, "first_attempt_done",
                  "FailState_first_attempt_done_state");
    ASSERT_NEAR(s.first_attempt_extreme, 102.0, 1e-9, "FailState_first_attempt_extreme");
}

//+------------------------------------------------------------------+
//| Anchor: test_spike_channel_state_initial_is_idle                  |
//+------------------------------------------------------------------+
void TestSpikeChannelInitialIsIdle() {
    SpikeChannelState s;
    Setups_InitSpikeChannelState(s);
    ASSERT_STR_EQ(s.state, "idle", "SpikeChannel_initial_state_is_idle");
    ASSERT_FALSE(Setups_SpikeChannelTriggered(s), "SpikeChannel_initial_not_triggered");
}

//+------------------------------------------------------------------+
//| Anchor: test_spike_channel_detects_spike                          |
//| Window closes [100,110,115,120,130]; last 3 = [115,120,130].      |
//| net_move = 15 ≥ 3*1=3. counter_bars=0 ≤ 1. → spike_detected.      |
//+------------------------------------------------------------------+
void TestSpikeChannelDetectsSpike() {
    SpikeChannelState s;
    Setups_InitSpikeChannelState(s);

    double closes[5] = {100.0, 110.0, 115.0, 120.0, 130.0};
    double opens[5]  = {100.0, 110.0, 115.0, 120.0, 130.0};

    bool advanced = Setups_StepSpikeChannel(
        s,
        /* open  */ opens[4], /* high */ closes[4] + 1.0,
        /* low   */ closes[4] - 1.0, /* close */ closes[4],
        /* bar_idx */ 4,
        opens, closes, 5,
        /* atr */ 1.0,
        SPIKE_MIN_BARS, SPIKE_MIN_MAGNITUDE_ATR,
        SPIKE_MAX_COUNTER_BARS, CHANNEL_MIN_BARS
    );
    ASSERT_TRUE(advanced, "SpikeChannel_spike_advanced");
    // Python test allows {"spike_detected", "channel_active"}; the MQL5
    // port performs ONE transition per call (no double-step inside
    // StepSpikeChannel — matches Python's "one bar = one return-replace"
    // semantics). So we always land on spike_detected first.
    ASSERT_STR_EQ(s.state, "spike_detected", "SpikeChannel_state_is_spike_detected");
    ASSERT_STR_EQ(s.direction, "bull", "SpikeChannel_direction_is_bull");
    // a_bar = bar_idx - spike_min_bars + 1 = 4 - 3 + 1 = 2
    ASSERT_EQ_INT(s.a_bar, 2, "SpikeChannel_a_bar_is_2");
    // a_price = closes[from] where from = window_n - spike_min_bars = 5-3=2 → closes[2]=115
    ASSERT_NEAR(s.a_price, 115.0, 1e-9, "SpikeChannel_a_price_is_115");
    ASSERT_EQ_INT(s.a_prime_bar, 4, "SpikeChannel_a_prime_bar_is_4");
    ASSERT_NEAR(s.a_prime_price, 130.0, 1e-9, "SpikeChannel_a_prime_price_is_130");
}

//+------------------------------------------------------------------+
//| Anchor: test_spike_channel_no_spike_on_flat_bars                  |
//+------------------------------------------------------------------+
void TestSpikeChannelNoSpikeFlat() {
    SpikeChannelState s;
    Setups_InitSpikeChannelState(s);

    double closes[5] = {100.0, 100.0, 100.0, 100.0, 100.0};
    double opens[5]  = {100.0, 100.0, 100.0, 100.0, 100.0};

    Setups_StepSpikeChannel(
        s,
        100.0, 100.1, 99.9, 100.0,
        4,
        opens, closes, 5, 1.0,
        SPIKE_MIN_BARS, SPIKE_MIN_MAGNITUDE_ATR,
        SPIKE_MAX_COUNTER_BARS, CHANNEL_MIN_BARS
    );
    ASSERT_STR_EQ(s.state, "idle", "SpikeChannel_flat_stays_idle");
}

//+------------------------------------------------------------------+
//| Anchor: test_trap_setup_triggered_predicate                       |
//+------------------------------------------------------------------+
void TestTrapPredicate() {
    TrapState s_trig;
    Setups_InitTrapState(s_trig, 1);
    s_trig.state = "triggered";
    ASSERT_TRUE(Setups_TrapTriggered(s_trig), "TrapPredicate_triggered_returns_true");

    TrapState s_first;
    Setups_InitTrapState(s_first, 1);
    s_first.state = "first_try_failed";
    ASSERT_FALSE(Setups_TrapTriggered(s_first), "TrapPredicate_first_try_returns_false");
}

void OnStart() {
    TestTrapStateInitialIsIdle();
    TestTrapStateFirstTryFailed();
    TestTrapStateFullLifecycle();
    TestFailStateInitialIsIdle();
    TestFailStateFirstAttempt();
    TestSpikeChannelInitialIsIdle();
    TestSpikeChannelDetectsSpike();
    TestSpikeChannelNoSpikeFlat();
    TestTrapPredicate();
    Print("test_pac_setups: scenarios complete");
}
