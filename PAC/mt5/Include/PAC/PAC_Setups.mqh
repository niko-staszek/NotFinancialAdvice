//+------------------------------------------------------------------+
//| PAC_Setups.mqh — §6 setup state machines                          |
//|                                                                   |
//| Port of hedgehog/proposer/pac/setups.py line-for-line:            |
//|   §6.1 Trap         — Setups_StepTrap        (TrapState)          |
//|   §6.2 Fail         — Setups_StepFail        (FailState)          |
//|   §6.3 Spike & Ch.  — Setups_StepSpikeChannel(SpikeChannelState)  |
//|                                                                   |
//| Each step function takes the current state by-reference (it will  |
//| be overwritten), the bar context, and config thresholds. Returns  |
//| true if the state advanced this call, false otherwise.            |
//|                                                                   |
//| Python uses FROZEN dataclasses + dataclasses.replace() so each    |
//| step returns a NEW immutable state. MQL5 lacks frozen structs and |
//| return-by-value-with-strings is allocation-heavy in MT5, so the   |
//| port mutates by reference but keeps the same transition semantics |
//| (identical state-string values; same threshold checks).           |
//|                                                                   |
//| DEVIATIONS from the plan sketch in favour of Python source:       |
//|   - TrapState has NO `direction` field. Direction is owned by the |
//|     MM struct passed into the step function.                      |
//|   - TrapState state values are exactly                            |
//|     {idle, first_try_failed, second_try_failed, triggered}        |
//|     (NOT the plan's {first_try_active, second_try_active}).       |
//|   - FailState states are {idle, first_attempt_done,               |
//|     second_attempt_done, triggered}.                              |
//|   - SpikeChannelState has NO mm_id, NO direction sketch field —   |
//|     the spike algorithm is MM-independent. It DOES track its own  |
//|     direction (bull/bear/none) discovered from the spike window.  |
//|   - SpikeChannelState states: {idle, spike_detected,              |
//|     channel_active, pullback_active, triggered, invalidated}.     |
//|   - The plan sketch parameter names ("fib_38_level", "failure     |
//|     _thresh") implied caller-precomputed values; Python computes  |
//|     these inside the step from cfg + mm + atr. We keep Python's   |
//|     approach so call-site code mirrors engine.py 1:1.             |
//|                                                                   |
//| Predicate helpers Setups_TrapTriggered etc. read `state.state ==  |
//| "triggered"` to match Python's predicates exactly.                |
//+------------------------------------------------------------------+
#property strict

#include "PAC_Targets.mqh"   // MeasuredMove for trap/fail step inputs

//+------------------------------------------------------------------+
//| TrapState — §6.1 two-failed-attempts retest pattern.              |
//|                                                                   |
//| Field naming mirrors setups.TrapState exactly:                    |
//|   mm_id              : the MM this trap is tied to                |
//|   state              : "idle"|"first_try_failed"|                 |
//|                        "second_try_failed"|"triggered"            |
//|   first_try_extreme  : low(bull)/high(bear) at first failed touch |
//|   first_try_bar      : bar_idx of first touch                     |
//|   second_try_extreme : same for second attempt                    |
//|   second_try_bar     : bar_idx of second attempt                  |
//|                                                                   |
//| MQL5 has no nullable doubles; use EMPTY_VALUE sentinel for the    |
//| "None" / "not yet seen" case Python uses Optional[float] for.     |
//+------------------------------------------------------------------+
struct TrapState {
    int       mm_id;
    string    state;
    double    first_try_extreme;
    int       first_try_bar;
    double    second_try_extreme;
    int       second_try_bar;
};

//+------------------------------------------------------------------+
//| FailState — §6.2 deep-then-shallow retest pattern.                |
//+------------------------------------------------------------------+
struct FailState {
    int       mm_id;
    string    state;
    double    first_attempt_extreme;
    int       first_attempt_bar;
    double    second_attempt_extreme;
    int       second_attempt_bar;
};

//+------------------------------------------------------------------+
//| SpikeChannelState — §6.3 spike → channel → 50% pullback pattern.  |
//|                                                                   |
//| Field naming mirrors setups.SpikeChannelState exactly:            |
//|   state          : idle|spike_detected|channel_active|            |
//|                    pullback_active|triggered|invalidated          |
//|   a_bar, a_price : start of spike (window first close)            |
//|   a_prime_bar    : end of spike (window last close)               |
//|   a_prime_price  : window last close                              |
//|   b_bar, b_price : channel extreme (high for bull, low for bear,  |
//|                    updated continuously while channel_active)     |
//|   c_price        : 50% Fib of A→B, recomputed when b updates      |
//|   direction      : "bull"|"bear"|"none"                           |
//+------------------------------------------------------------------+
struct SpikeChannelState {
    string    state;
    int       a_bar;
    double    a_price;
    int       a_prime_bar;
    double    a_prime_price;
    int       b_bar;
    double    b_price;
    double    c_price;
    string    direction;
};

//+------------------------------------------------------------------+
//| Helper — initialise a TrapState to its idle defaults.             |
//+------------------------------------------------------------------+
void Setups_InitTrapState(TrapState &s, int mm_id) {
    s.mm_id              = mm_id;
    s.state              = "idle";
    s.first_try_extreme  = EMPTY_VALUE;
    s.first_try_bar      = -1;
    s.second_try_extreme = EMPTY_VALUE;
    s.second_try_bar     = -1;
}

//+------------------------------------------------------------------+
//| Helper — initialise a FailState to its idle defaults.             |
//+------------------------------------------------------------------+
void Setups_InitFailState(FailState &s, int mm_id) {
    s.mm_id                  = mm_id;
    s.state                  = "idle";
    s.first_attempt_extreme  = EMPTY_VALUE;
    s.first_attempt_bar      = -1;
    s.second_attempt_extreme = EMPTY_VALUE;
    s.second_attempt_bar     = -1;
}

//+------------------------------------------------------------------+
//| Helper — initialise a SpikeChannelState to idle defaults.         |
//+------------------------------------------------------------------+
void Setups_InitSpikeChannelState(SpikeChannelState &s) {
    s.state         = "idle";
    s.a_bar         = -1;
    s.a_price       = EMPTY_VALUE;
    s.a_prime_bar   = -1;
    s.a_prime_price = EMPTY_VALUE;
    s.b_bar         = -1;
    s.b_price       = EMPTY_VALUE;
    s.c_price       = EMPTY_VALUE;
    s.direction     = "none";
}

//+------------------------------------------------------------------+
//| §6.1 Trap setup — advance one bar.                                |
//|                                                                   |
//| Mirrors setups.step_trap line-for-line:                           |
//|                                                                   |
//|   Bull MM:                                                        |
//|     trap_level = a_price + trap_first_try_level × ab_span         |
//|     failure_threshold = trap_failure_threshold_atr_multiple × atr |
//|     max_penetration = trap_max_first_try_penetration_fib × |ab|   |
//|                                                                   |
//|     idle → first_try_failed when                                  |
//|       |low - trap_level| <= failure_threshold AND                 |
//|       (trap_level - low) <= max_penetration                       |
//|                                                                   |
//|     first_try_failed → second_try_failed when                     |
//|       bars_since_first_try <= trap_max_bars_between_tries AND     |
//|       |low - first_try_extreme| <= failure_threshold              |
//|                                                                   |
//|     second_try_failed → triggered when                            |
//|       close - second_try_extreme >= failure_threshold             |
//|                                                                   |
//|   Bear MM: mirror with high in place of low and signs flipped.    |
//|                                                                   |
//| Parameters:                                                       |
//|   state                              : in/out                     |
//|   bar_open / bar_high / bar_low / bar_close : current bar OHLC    |
//|   bar_idx                            : current bar index          |
//|   mm                                 : the MM owning this trap    |
//|   atr                                : current ATR value          |
//|   trap_first_try_level               : cfg.trap_first_try_level   |
//|     (0.382)                                                       |
//|   trap_failure_threshold_atr_mult    : cfg.trap_failure_threshold_|
//|     atr_multiple (0.2)                                            |
//|   trap_max_bars_between_tries        : cfg.trap_max_bars_between_ |
//|     tries (20)                                                    |
//|   trap_max_first_try_penetration_fib : cfg.trap_max_first_try_    |
//|     penetration_fib (0.20)                                        |
//|                                                                   |
//| Returns true iff state advanced.                                  |
//+------------------------------------------------------------------+
bool Setups_StepTrap(
    TrapState &state,
    double bar_open, double bar_high, double bar_low, double bar_close,
    int bar_idx,
    const MeasuredMove &mm,
    double atr,
    double trap_first_try_level,
    double trap_failure_threshold_atr_mult,
    int trap_max_bars_between_tries,
    double trap_max_first_try_penetration_fib
) {
    double ab_span = mm.b_price - mm.a_price;  // pos for bull, neg for bear
    double trap_level = mm.a_price + trap_first_try_level * ab_span;
    double failure_threshold = trap_failure_threshold_atr_mult * atr;
    double max_penetration = trap_max_first_try_penetration_fib * MathAbs(ab_span);

    if (mm.direction == "bull") {
        if (state.state == "idle") {
            double low = bar_low;
            double distance_to_trap = MathAbs(low - trap_level);
            double penetration = trap_level - low;  // positive if low broke below
            if (distance_to_trap <= failure_threshold && penetration <= max_penetration) {
                state.state = "first_try_failed";
                state.first_try_extreme = low;
                state.first_try_bar = bar_idx;
                return true;
            }
        }
        else if (state.state == "first_try_failed") {
            int bars_since_first = bar_idx - state.first_try_bar;
            if (bars_since_first <= trap_max_bars_between_tries) {
                double low = bar_low;
                double distance_to_extreme = MathAbs(low - state.first_try_extreme);
                if (distance_to_extreme <= failure_threshold) {
                    state.state = "second_try_failed";
                    state.second_try_extreme = low;
                    state.second_try_bar = bar_idx;
                    return true;
                }
            }
            // v2: else reset to idle
        }
        else if (state.state == "second_try_failed") {
            double close = bar_close;
            double reaction_up = close - state.second_try_extreme;
            if (reaction_up >= failure_threshold) {
                state.state = "triggered";
                return true;
            }
        }
    }
    else {
        // Bear MM mirror.
        if (state.state == "idle") {
            double high = bar_high;
            double distance_to_trap = MathAbs(high - trap_level);
            double penetration = high - trap_level;
            if (distance_to_trap <= failure_threshold && penetration <= max_penetration) {
                state.state = "first_try_failed";
                state.first_try_extreme = high;
                state.first_try_bar = bar_idx;
                return true;
            }
        }
        else if (state.state == "first_try_failed") {
            int bars_since_first = bar_idx - state.first_try_bar;
            if (bars_since_first <= trap_max_bars_between_tries) {
                double high = bar_high;
                double distance_to_extreme = MathAbs(high - state.first_try_extreme);
                if (distance_to_extreme <= failure_threshold) {
                    state.state = "second_try_failed";
                    state.second_try_extreme = high;
                    state.second_try_bar = bar_idx;
                    return true;
                }
            }
        }
        else if (state.state == "second_try_failed") {
            double close = bar_close;
            double reaction_down = state.second_try_extreme - close;
            if (reaction_down >= failure_threshold) {
                state.state = "triggered";
                return true;
            }
        }
    }
    return false;
}

//+------------------------------------------------------------------+
//| §6.2 Fail setup — advance one bar.                                |
//|                                                                   |
//| Mirrors setups.step_fail line-for-line:                           |
//|                                                                   |
//|   fib_382 = a_price + fail_min_first_attempt_depth_fib × ab_span  |
//|   shortfall_threshold = fail_second_attempt_shortfall_atr_         |
//|     multiple × atr                                                |
//|                                                                   |
//|   Bull MM ("fail" = deep correction):                             |
//|     idle → first_attempt_done when low <= fib_382                 |
//|     first_attempt_done → second_attempt_done when                 |
//|       bars_since_first <= fail_max_bars_between_attempts AND      |
//|       low <= fib_382 AND                                          |
//|       (first_attempt_extreme - low) >= shortfall_threshold        |
//|         [i.e. second attempt was SHALLOWER than first]            |
//|     second_attempt_done → triggered when close > fib_382          |
//|                                                                   |
//|   Bear MM: mirror — uses high vs fib_382 (now lower than a_price  |
//|     because ab_span < 0), shortfall = high - first_attempt_extreme|
//|                                                                   |
//| Returns true iff state advanced.                                  |
//+------------------------------------------------------------------+
bool Setups_StepFail(
    FailState &state,
    double bar_open, double bar_high, double bar_low, double bar_close,
    int bar_idx,
    const MeasuredMove &mm,
    double atr,
    double fail_min_first_attempt_depth_fib,
    double fail_second_attempt_shortfall_atr_mult,
    int fail_max_bars_between_attempts
) {
    double ab_span = mm.b_price - mm.a_price;
    double fib_382 = mm.a_price + fail_min_first_attempt_depth_fib * ab_span;
    double shortfall_threshold = fail_second_attempt_shortfall_atr_mult * atr;

    if (mm.direction == "bull") {
        if (state.state == "idle") {
            double low = bar_low;
            if (low <= fib_382) {
                state.state = "first_attempt_done";
                state.first_attempt_extreme = low;
                state.first_attempt_bar = bar_idx;
                return true;
            }
        }
        else if (state.state == "first_attempt_done") {
            int bars_since_first = bar_idx - state.first_attempt_bar;
            if (bars_since_first <= fail_max_bars_between_attempts) {
                double low = bar_low;
                if (low <= fib_382) {
                    double shortfall = state.first_attempt_extreme - low;
                    if (shortfall >= shortfall_threshold) {
                        state.state = "second_attempt_done";
                        state.second_attempt_extreme = low;
                        state.second_attempt_bar = bar_idx;
                        return true;
                    }
                }
            }
        }
        else if (state.state == "second_attempt_done") {
            double close = bar_close;
            if (close > fib_382) {
                state.state = "triggered";
                return true;
            }
        }
    }
    else {
        // Bear MM mirror — fib_382 < a_price (ab_span negative).
        if (state.state == "idle") {
            double high = bar_high;
            if (high >= fib_382) {
                state.state = "first_attempt_done";
                state.first_attempt_extreme = high;
                state.first_attempt_bar = bar_idx;
                return true;
            }
        }
        else if (state.state == "first_attempt_done") {
            int bars_since_first = bar_idx - state.first_attempt_bar;
            if (bars_since_first <= fail_max_bars_between_attempts) {
                double high = bar_high;
                if (high >= fib_382) {
                    double shortfall = high - state.first_attempt_extreme;
                    if (shortfall >= shortfall_threshold) {
                        state.state = "second_attempt_done";
                        state.second_attempt_extreme = high;
                        state.second_attempt_bar = bar_idx;
                        return true;
                    }
                }
            }
        }
        else if (state.state == "second_attempt_done") {
            double close = bar_close;
            if (close < fib_382) {
                state.state = "triggered";
                return true;
            }
        }
    }
    return false;
}

//+------------------------------------------------------------------+
//| §6.3 Spike & channel setup — advance one bar.                     |
//|                                                                   |
//| Mirrors setups.step_spike_channel line-for-line:                  |
//|                                                                   |
//|   idle → spike_detected when                                      |
//|     window has >= spike_min_bars bars AND                         |
//|     |net_move| >= spike_min_magnitude_atr × atr AND               |
//|     counter_bars_in_window <= spike_max_counter_bars              |
//|                                                                   |
//|   spike_detected → channel_active when bar_idx > a_prime_bar      |
//|     (initialises b_price = bull?high:low, c_price = (a+b)/2)      |
//|                                                                   |
//|   channel_active                                                  |
//|     - always update b = extreme (bull→max(b, high), bear→min(b,   |
//|       low)) and c = (a + b) / 2.                                  |
//|     - once bars_in_channel >= channel_min_bars, check pullback:   |
//|         bull: low  <= c → pullback_active                         |
//|         bear: high >= c → pullback_active                         |
//|                                                                   |
//|   pullback_active                                                 |
//|     bull:                                                         |
//|       low  < a_price        → invalidated                         |
//|       close >= c_price      → triggered                           |
//|     bear:                                                         |
//|       high > a_price        → invalidated                         |
//|       close <= c_price      → triggered                           |
//|                                                                   |
//|   triggered/invalidated are terminal.                             |
//|                                                                   |
//| Parameters:                                                       |
//|   state                              : in/out                     |
//|   bar_open / bar_high / bar_low / bar_close : current bar OHLC    |
//|   bar_idx                            : current bar index          |
//|   window_opens / window_closes       : the bars_window slice      |
//|     (length = spike_min_bars; ending at current bar)              |
//|   window_n                           : array length               |
//|   atr                                : current ATR value          |
//|   spike_min_bars                     : cfg.spike_min_bars (3)     |
//|   spike_min_magnitude_atr            : cfg.spike_min_magnitude_atr|
//|   spike_max_counter_bars             : cfg.spike_max_counter_bars |
//|   channel_min_bars                   : cfg.channel_min_bars (5)   |
//|                                                                   |
//| Returns true iff state advanced (or, while in channel_active,     |
//| b_price/c_price were updated — informational only).               |
//+------------------------------------------------------------------+
bool Setups_StepSpikeChannel(
    SpikeChannelState &state,
    double bar_open, double bar_high, double bar_low, double bar_close,
    int bar_idx,
    const double &window_opens[], const double &window_closes[], int window_n,
    double atr,
    int spike_min_bars,
    double spike_min_magnitude_atr,
    int spike_max_counter_bars,
    int channel_min_bars
) {
    if (state.state == "idle") {
        if (window_n < spike_min_bars) return false;

        // Use the last `spike_min_bars` bars of the window.
        int from = window_n - spike_min_bars;
        double net_move = window_closes[window_n - 1] - window_closes[from];
        if (MathAbs(net_move) < spike_min_magnitude_atr * atr) return false;

        bool is_bull = (net_move > 0);
        // Count counter-direction bars (close - open in the wrong direction).
        int counter_bars = 0;
        for (int i = from; i < window_n; i++) {
            double bar_move = window_closes[i] - window_opens[i];
            if (is_bull && bar_move < 0) counter_bars++;
            else if (!is_bull && bar_move > 0) counter_bars++;
        }
        if (counter_bars > spike_max_counter_bars) return false;

        // Spike confirmed.
        state.state = "spike_detected";
        state.a_bar = bar_idx - spike_min_bars + 1;
        state.a_price = window_closes[from];
        state.a_prime_bar = bar_idx;
        state.a_prime_price = window_closes[window_n - 1];
        state.direction = is_bull ? "bull" : "bear";
        return true;
    }
    else if (state.state == "spike_detected") {
        // After at least 1 bar beyond the spike, move to channel_active.
        if (bar_idx > state.a_prime_bar) {
            double b_price = (state.direction == "bull") ? bar_high : bar_low;
            double c_price = (state.a_price + b_price) / 2.0;
            state.state = "channel_active";
            state.b_bar = bar_idx;
            state.b_price = b_price;
            state.c_price = c_price;
            return true;
        }
    }
    else if (state.state == "channel_active") {
        // Update B (tracks furthest extreme).
        double new_b;
        if (state.direction == "bull") {
            new_b = (bar_high > state.b_price) ? bar_high : state.b_price;
        } else {
            new_b = (bar_low < state.b_price) ? bar_low : state.b_price;
        }
        double new_c = (state.a_price + new_b) / 2.0;
        state.b_price = new_b;
        state.c_price = new_c;

        int bars_in_channel = bar_idx - state.b_bar;
        if (bars_in_channel < channel_min_bars) return true;  // updated but no state change

        // Check for pullback toward C.
        if (state.direction == "bull") {
            if (bar_low <= new_c) {
                state.state = "pullback_active";
                return true;
            }
        } else {
            if (bar_high >= new_c) {
                state.state = "pullback_active";
                return true;
            }
        }
        // Channel updated without state change.
        return true;
    }
    else if (state.state == "pullback_active") {
        if (state.direction == "bull") {
            if (bar_low < state.a_price) {
                state.state = "invalidated";
                return true;
            }
            if (bar_close >= state.c_price) {
                state.state = "triggered";
                return true;
            }
        } else {
            if (bar_high > state.a_price) {
                state.state = "invalidated";
                return true;
            }
            if (bar_close <= state.c_price) {
                state.state = "triggered";
                return true;
            }
        }
    }
    // triggered / invalidated terminal.
    return false;
}

//+------------------------------------------------------------------+
//| Predicate helpers — mirror Python's *_setup_triggered functions.  |
//+------------------------------------------------------------------+
bool Setups_TrapTriggered(const TrapState &state)               { return state.state == "triggered"; }
bool Setups_FailTriggered(const FailState &state)               { return state.state == "triggered"; }
bool Setups_SpikeChannelTriggered(const SpikeChannelState &state) { return state.state == "triggered"; }
