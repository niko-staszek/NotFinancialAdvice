//+------------------------------------------------------------------+
//| PAC_Targets.mqh — §5 Target Engine                                |
//|                                                                   |
//| Port of hedgehog/proposer/pac/targets.py line-for-line:           |
//|   §5.1 Targets_DetectMeasuredMoves — AB=CD pattern scanner        |
//|   §5.2 Targets_FibLevels           — retracement + extension      |
//|   §5.2 Targets_FindClusters        — forward-greedy grouping      |
//|   §5.3 Targets_ExtendedMM          — 1.382 overshoot target       |
//|   §5.4 Targets_ApplySettle         — inward buffer on raw target  |
//|                                                                   |
//| DEVIATIONS from the plan sketch in favour of Python source:       |
//|   - Plan struct field "mm_id" → Python "id"; we follow Python.    |
//|   - Plan struct field "state" with values b_formed/c_formed/      |
//|     active/d_hit → Python "validity" ∈ {valid, invalid}. The      |
//|     wider lifecycle is owned by engine.py, not targets.py.        |
//|   - Plan FibLevel has separate {ratio, source_mm_id, kind}, but   |
//|     Python emits (price, label) where label encodes both          |
//|     retracement/extension kind and ratio (e.g. "fib_R_0.382").    |
//|     We mirror Python's compact label format.                      |
//|   - Plan Cluster has only member_count; Python returns (price,    |
//|     [labels]). We expose both price + count + label array.        |
//|   - Plan DetectMeasuredMoves took only swings + a scalar          |
//|     ema21_at_b; Python derives ATR internally and reads EMA at    |
//|     each pivot bar (A, B, C). We accept a full EMA series (one    |
//|     value per bar) so the EMA-side check matches Python exactly.  |
//|   - Plan ExtendedMM(mm, ratio) accepted a ratio param; Python     |
//|     hard-codes 1.382 and gates on overshoot_bars_min. v2 will     |
//|     escalate to 1.618 once 1.382 has been reached (Python TODO).  |
//|                                                                   |
//| ATR semantics — Python uses an internal Wilder ATR(20) computed   |
//| from the `bars` DataFrame. MQL5 callers pass an externally-built  |
//| ATR series (matching helpers/atr.py — see PAC_Swing.mqh           |
//| _ComputeATR for the byte-identical reference implementation).     |
//+------------------------------------------------------------------+
#property strict

#include "PAC_Swing.mqh"   // Swing, SwingKind, _ComputeATR

//+------------------------------------------------------------------+
//| MeasuredMove — one detected AB=CD pattern.                        |
//|                                                                   |
//| Field naming mirrors targets.MeasuredMove exactly:                |
//|   id              : sequential int starting at 1                  |
//|   direction       : "bull" | "bear"                               |
//|   a_bar, a_price  : first pivot (low for bull, high for bear)     |
//|   b_bar, b_price  : impulse extreme (high for bull, low for bear) |
//|   c_bar, c_price  : pullback pivot (matches a kind)               |
//|   d_target        : projected target = c_price ± (b-a) span       |
//|   validity        : "valid" | "invalid"                           |
//|   overshoot_bars  : count of bars beyond D — engine increments;   |
//|                     extended_mm_target gates on it.               |
//+------------------------------------------------------------------+
struct MeasuredMove {
    int       id;
    string    direction;        // "bull" | "bear"
    int       a_bar;
    double    a_price;
    int       b_bar;
    double    b_price;
    int       c_bar;
    double    c_price;
    double    d_target;
    string    validity;         // "valid" | "invalid"
    int       overshoot_bars;   // initialised to 0; engine updates
};

//+------------------------------------------------------------------+
//| FibLevel — one Fibonacci retracement / extension level.           |
//|                                                                   |
//| Python returns flat list of (price, label) tuples; we wrap them   |
//| as a struct. The `label` field encodes both kind ("R" or "E")    |
//| and ratio (e.g. "fib_R_0.382", "fib_E_1.382") to match the        |
//| Python label format exactly — so downstream code can grep by      |
//| substring identically.                                            |
//+------------------------------------------------------------------+
struct FibLevel {
    double    price;
    string    label;            // e.g. "fib_R_0.382" / "fib_E_1.618"
};

//+------------------------------------------------------------------+
//| Cluster — grouped Fibonacci levels (arithmetic mean of members). |
//|                                                                   |
//| Python returns (cluster_price, [member_labels]). We expose the    |
//| count plus a parallel array of labels so callers can introspect.  |
//| For brevity, member_labels is capped at MAX_CLUSTER_MEMBERS — the |
//| count field reflects the true membership even if labels are       |
//| truncated.                                                        |
//+------------------------------------------------------------------+
#define MAX_CLUSTER_MEMBERS 16
struct Cluster {
    double    price;
    int       member_count;
    string    member_labels[MAX_CLUSTER_MEMBERS];
};

//+------------------------------------------------------------------+
//| §5.1 Detect AB=CD measured-move patterns from a swing list.       |
//|                                                                   |
//| Mirrors targets.detect_measured_moves line-for-line:              |
//|   For each consecutive triple (A, B, C) of swings, check bull and |
//|   bear patterns:                                                  |
//|                                                                   |
//|   Bull (low → high → low):                                        |
//|     A < EMA(A) AND B > EMA(B) AND C < EMA(C)                      |
//|     C > A (partial pullback, not full retest)                     |
//|     (B - A) >= impulse_atr_multiple_min × ATR(B)                  |
//|     d_target = C + (B - A)                                        |
//|                                                                   |
//|   Bear (high → low → high): mirror of bull.                       |
//|                                                                   |
//| Returns the most recent ≤ max_active_measured_moves MMs           |
//| (Python: mms[-N:]).                                               |
//|                                                                   |
//| Parameters:                                                       |
//|   bars                 : MqlRates[] used for ATR computation      |
//|   n_bars               : array length of bars[]                   |
//|   swings               : Swing[] from Swing_Detect                |
//|   sw_count             : array length of swings[]                 |
//|   ema_series           : EMA values aligned with bars (1:1)       |
//|   ema_len              : array length of ema_series[]             |
//|   impulse_atr_mult_min : cfg.impulse_atr_multiple_min (1.5)       |
//|   max_active_mms       : cfg.max_active_measured_moves (5)        |
//|   atr_period           : ATR lookback (20 matches Wilder default) |
//|   out_mms              : output MM array (sized to count)         |
//|                                                                   |
//| EMA-side check uses pivot prices (a.price/b.price/c.price), NOT   |
//| bar close — see targets.py module docstring for rationale.        |
//+------------------------------------------------------------------+
int Targets_DetectMeasuredMoves(
    const MqlRates &bars[], int n_bars,
    const Swing &swings[], int sw_count,
    const double &ema_series[], int ema_len,
    double impulse_atr_mult_min,
    int max_active_mms,
    int atr_period,
    MeasuredMove &out_mms[]
) {
    ArrayResize(out_mms, 0);
    if (sw_count == 0 || n_bars == 0) return 0;

    // Compute ATR locally using the same Wilder helper as PAC_Swing.
    double atr[];
    _ComputeATR(bars, n_bars, atr_period, atr);

    // Upper bound; we trim at the end.
    MeasuredMove buf[];
    ArrayResize(buf, sw_count);
    int buf_count = 0;
    int next_id = 1;

    for (int i = 0; i < sw_count - 2; i++) {
        // Python: a, b, c = swings[i], swings[i+1], swings[i+2]
        int a_idx = swings[i].bar_idx;
        int b_idx = swings[i + 1].bar_idx;
        int c_idx = swings[i + 2].bar_idx;
        double a_price = swings[i].price;
        double b_price = swings[i + 1].price;
        double c_price = swings[i + 2].price;
        SwingKind a_kind = swings[i].kind;
        SwingKind b_kind = swings[i + 1].kind;
        SwingKind c_kind = swings[i + 2].kind;

        // Skip if ATR unavailable at B (insufficient history). Python uses
        // pd.isna(); MQL5 zero-sentinel matches _ComputeATR's pre-warm 0.0.
        if (b_idx >= n_bars) continue;
        double atr_at_b = atr[b_idx];
        if (atr_at_b <= 0.0) continue;

        // EMA bounds — skip if any pivot bar lacks EMA.
        if (a_idx >= ema_len || b_idx >= ema_len || c_idx >= ema_len) continue;
        double ema_a = ema_series[a_idx];
        double ema_b = ema_series[b_idx];
        double ema_c = ema_series[c_idx];
        if (ema_a == EMPTY_VALUE || ema_b == EMPTY_VALUE || ema_c == EMPTY_VALUE) continue;

        // ---- Bull: low → high → low ----
        if (a_kind == SWING_LOW && b_kind == SWING_HIGH && c_kind == SWING_LOW) {
            double ab_distance = b_price - a_price;

            if (ab_distance < impulse_atr_mult_min * atr_at_b) continue;

            // EMA-side check on pivot prices.
            if (!(a_price < ema_a && b_price > ema_b && c_price < ema_c)) continue;

            // C must be above A (partial pullback only).
            if (c_price <= a_price) continue;

            buf[buf_count].id              = next_id;
            buf[buf_count].direction       = "bull";
            buf[buf_count].a_bar           = a_idx;
            buf[buf_count].a_price         = a_price;
            buf[buf_count].b_bar           = b_idx;
            buf[buf_count].b_price         = b_price;
            buf[buf_count].c_bar           = c_idx;
            buf[buf_count].c_price         = c_price;
            buf[buf_count].d_target        = c_price + ab_distance;
            buf[buf_count].validity        = "valid";
            buf[buf_count].overshoot_bars  = 0;
            buf_count++;
            next_id++;
        }
        // ---- Bear: high → low → high ----
        else if (a_kind == SWING_HIGH && b_kind == SWING_LOW && c_kind == SWING_HIGH) {
            double ab_distance = a_price - b_price;

            if (ab_distance < impulse_atr_mult_min * atr_at_b) continue;

            if (!(a_price > ema_a && b_price < ema_b && c_price > ema_c)) continue;

            // C must be below A (partial pullback only).
            if (c_price >= a_price) continue;

            buf[buf_count].id              = next_id;
            buf[buf_count].direction       = "bear";
            buf[buf_count].a_bar           = a_idx;
            buf[buf_count].a_price         = a_price;
            buf[buf_count].b_bar           = b_idx;
            buf[buf_count].b_price         = b_price;
            buf[buf_count].c_bar           = c_idx;
            buf[buf_count].c_price         = c_price;
            buf[buf_count].d_target        = c_price - ab_distance;
            buf[buf_count].validity        = "valid";
            buf[buf_count].overshoot_bars  = 0;
            buf_count++;
            next_id++;
        }
    }

    // Cap to most-recent N (Python: mms[-N:]).
    int keep_from = 0;
    if (buf_count > max_active_mms) {
        keep_from = buf_count - max_active_mms;
    }
    int kept = buf_count - keep_from;
    ArrayResize(out_mms, kept);
    for (int k = 0; k < kept; k++) {
        out_mms[k] = buf[keep_from + k];
    }
    return kept;
}

//+------------------------------------------------------------------+
//| Helper — format a double to the same string form Python uses for  |
//| fib labels. Python uses f"{ratio}" which prints as "0.382" or     |
//| "1.382" with no trailing zeros. MQL5 DoubleToString(x, 3) gives   |
//| "0.382" exactly (3 decimal places). For "0.5" we need "0.5", not |
//| "0.500" — so we strip trailing zeros and trailing '.'.            |
//+------------------------------------------------------------------+
string _FormatFibRatio(double ratio) {
    string s = DoubleToString(ratio, 3);
    // Strip trailing zeros only after a decimal point.
    int dot_pos = StringFind(s, ".");
    if (dot_pos < 0) return s;
    int end = StringLen(s) - 1;
    while (end > dot_pos && StringGetCharacter(s, end) == '0') end--;
    if (end == dot_pos) end--;  // strip the dot too if nothing follows
    return StringSubstr(s, 0, end + 1);
}

//+------------------------------------------------------------------+
//| §5.2 Compute Fibonacci levels for all valid MMs.                 |
//|                                                                   |
//| Mirrors targets.fibonacci_levels exactly:                         |
//|   For each MM with validity == "valid", emit                      |
//|     price = a_price + ratio × (b_price - a_price)                 |
//|     label = "fib_R_<ratio>"  for ratios in fib_levels_retracement |
//|     label = "fib_E_<ratio>"  for ratios in fib_levels_extension   |
//|                                                                   |
//|   Bear MMs: AB span is negative, so the formula naturally         |
//|   produces correct levels with no special-casing.                 |
//|                                                                   |
//| Parameters:                                                       |
//|   mms        : MeasuredMove[] (all candidate MMs)                 |
//|   n_mms      : array length                                       |
//|   ratios_R   : fib_levels_retracement (e.g. {0.382, 0.5, 0.618})  |
//|   ratios_R_n : array length                                       |
//|   ratios_E   : fib_levels_extension (e.g. {1.382, 1.618, 2.618})  |
//|   ratios_E_n : array length                                       |
//|   out        : output FibLevel array (sized to total count)       |
//+------------------------------------------------------------------+
int Targets_FibLevels(
    const MeasuredMove &mms[], int n_mms,
    const double &ratios_R[], int ratios_R_n,
    const double &ratios_E[], int ratios_E_n,
    FibLevel &out[]
) {
    // Upper-bound size: one entry per (MM × ratio).
    int max_levels = n_mms * (ratios_R_n + ratios_E_n);
    ArrayResize(out, max_levels);
    int cnt = 0;

    for (int m = 0; m < n_mms; m++) {
        if (mms[m].validity != "valid") continue;

        double ab_span = mms[m].b_price - mms[m].a_price;

        for (int r = 0; r < ratios_R_n; r++) {
            double ratio = ratios_R[r];
            out[cnt].price = mms[m].a_price + ratio * ab_span;
            out[cnt].label = "fib_R_" + _FormatFibRatio(ratio);
            cnt++;
        }
        for (int e = 0; e < ratios_E_n; e++) {
            double ratio = ratios_E[e];
            out[cnt].price = mms[m].a_price + ratio * ab_span;
            out[cnt].label = "fib_E_" + _FormatFibRatio(ratio);
            cnt++;
        }
    }

    ArrayResize(out, cnt);
    return cnt;
}

//+------------------------------------------------------------------+
//| Helper — insertion sort FibLevel array ascending by price.        |
//| Used by Targets_FindClusters before the forward-greedy walk.      |
//+------------------------------------------------------------------+
void _SortLevelsByPrice(FibLevel &arr[], int n) {
    for (int i = 1; i < n; i++) {
        FibLevel cur = arr[i];
        int j = i - 1;
        while (j >= 0 && arr[j].price > cur.price) {
            arr[j + 1] = arr[j];
            j--;
        }
        arr[j + 1] = cur;
    }
}

//+------------------------------------------------------------------+
//| §5.2 Group nearby Fibonacci levels into price clusters.           |
//|                                                                   |
//| Mirrors targets.find_clusters exactly (forward-greedy walk):      |
//|   1. Sort levels ascending by price.                              |
//|   2. Walk forward; if current level is within `threshold` of the  |
//|      LAST member added to the current group, extend the group.    |
//|      Otherwise flush the group (if >= min_members) and restart.   |
//|   3. Cluster price = arithmetic mean of member prices.            |
//|                                                                   |
//|   threshold = cluster_pips_threshold_atr_multiple × atr_value     |
//|                                                                   |
//| Python uses `<=` for the in-threshold test — we mirror that       |
//| (strict less-or-equal, ties = same group).                        |
//|                                                                   |
//| Parameters:                                                       |
//|   levels      : FibLevel[] from Targets_FibLevels                 |
//|   n_levels    : array length                                      |
//|   atr_value   : current ATR(20) value                             |
//|   cluster_atr_mult : cfg.cluster_pips_threshold_atr_multiple (0.3)|
//|   min_members : cfg.cluster_member_min (2)                        |
//|   out         : output Cluster array (sized to count)             |
//+------------------------------------------------------------------+
int Targets_FindClusters(
    const FibLevel &levels[], int n_levels,
    double atr_value,
    double cluster_atr_mult,
    int min_members,
    Cluster &out[]
) {
    ArrayResize(out, 0);
    if (n_levels == 0) return 0;

    double threshold = cluster_atr_mult * atr_value;

    // Copy + sort ascending by price.
    FibLevel sorted[];
    ArrayResize(sorted, n_levels);
    for (int i = 0; i < n_levels; i++) sorted[i] = levels[i];
    _SortLevelsByPrice(sorted, n_levels);

    // Upper-bound output capacity.
    Cluster buf[];
    ArrayResize(buf, n_levels);
    int n_clusters = 0;

    double group_prices[];
    string group_labels[];
    ArrayResize(group_prices, n_levels);
    ArrayResize(group_labels, n_levels);
    int gsize = 0;

    // Initialise with first level.
    group_prices[0] = sorted[0].price;
    group_labels[0] = sorted[0].label;
    gsize = 1;

    for (int i = 1; i < n_levels; i++) {
        double last_in_group = group_prices[gsize - 1];
        if (sorted[i].price - last_in_group <= threshold) {
            // Extend group.
            group_prices[gsize] = sorted[i].price;
            group_labels[gsize] = sorted[i].label;
            gsize++;
        } else {
            // Flush group if it qualifies.
            if (gsize >= min_members) {
                double sum = 0.0;
                for (int g = 0; g < gsize; g++) sum += group_prices[g];
                buf[n_clusters].price = sum / gsize;
                buf[n_clusters].member_count = gsize;
                // Store labels (capped at MAX_CLUSTER_MEMBERS).
                int label_cap = (gsize < MAX_CLUSTER_MEMBERS) ? gsize : MAX_CLUSTER_MEMBERS;
                for (int g = 0; g < label_cap; g++) {
                    buf[n_clusters].member_labels[g] = group_labels[g];
                }
                n_clusters++;
            }
            // Start fresh group.
            group_prices[0] = sorted[i].price;
            group_labels[0] = sorted[i].label;
            gsize = 1;
        }
    }

    // Flush final group.
    if (gsize >= min_members) {
        double sum = 0.0;
        for (int g = 0; g < gsize; g++) sum += group_prices[g];
        buf[n_clusters].price = sum / gsize;
        buf[n_clusters].member_count = gsize;
        int label_cap = (gsize < MAX_CLUSTER_MEMBERS) ? gsize : MAX_CLUSTER_MEMBERS;
        for (int g = 0; g < label_cap; g++) {
            buf[n_clusters].member_labels[g] = group_labels[g];
        }
        n_clusters++;
    }

    ArrayResize(out, n_clusters);
    for (int c = 0; c < n_clusters; c++) {
        out[c] = buf[c];
    }
    return n_clusters;
}

//+------------------------------------------------------------------+
//| §5.3 Extended MM target — 1.382 extension once price overshoots D.|
//|                                                                   |
//| Mirrors targets.extended_mm_target:                               |
//|   Return EMPTY_VALUE if overshoot_bars < overshoot_bars_min.      |
//|                                                                   |
//|   ab_span = |b_price - a_price|                                   |
//|   bull → c_price + 1.382 × ab_span                                |
//|   bear → c_price - 1.382 × ab_span                                |
//|                                                                   |
//| Sentinel: Python returns Optional[float] / None — MQL5 has no     |
//| Optional, so we return EMPTY_VALUE (DBL_MAX) as the "not yet"     |
//| sentinel. Callers should check `result != EMPTY_VALUE`. This      |
//| matches the EMPTY_VALUE convention used across PAC_Signals.mqh.   |
//|                                                                   |
//| Parameters:                                                       |
//|   mm                  : MeasuredMove (read-only)                  |
//|   overshoot_bars_min  : cfg.overshoot_bars_min (3)                |
//+------------------------------------------------------------------+
double Targets_ExtendedMM(const MeasuredMove &mm, int overshoot_bars_min) {
    if (mm.overshoot_bars < overshoot_bars_min) return EMPTY_VALUE;

    double ab_span = MathAbs(mm.b_price - mm.a_price);
    if (mm.direction == "bull") {
        return mm.c_price + 1.382 * ab_span;
    }
    return mm.c_price - 1.382 * ab_span;
}

//+------------------------------------------------------------------+
//| §5.4 Settle buffer — pull target inward by ATR multiple.          |
//|                                                                   |
//| Mirrors targets.apply_settle_buffer:                              |
//|   settle_buffer = settle_buffer_atr_multiple × atr_value          |
//|   bull (long)   → target - settle_buffer                          |
//|   bear (short)  → target + settle_buffer                          |
//|                                                                   |
//| Parameters:                                                       |
//|   target_price             : raw target (e.g. d_target)           |
//|   direction                : "bull" | "bear"                      |
//|   atr_value                : current ATR(20) value                |
//|   settle_buffer_atr_mult   : cfg.settle_buffer_atr_multiple (0.5) |
//+------------------------------------------------------------------+
double Targets_ApplySettle(double target_price, string direction,
                           double atr_value, double settle_buffer_atr_mult) {
    double settle_buffer = settle_buffer_atr_mult * atr_value;
    if (direction == "bull") return target_price - settle_buffer;
    return target_price + settle_buffer;
}
