//+------------------------------------------------------------------+
//| PAC_Swing.mqh — ATR-filtered ZigZag swing detector                |
//| Port of hedgehog/proposer/pac/helpers/swing.py                    |
//|                                                                   |
//| Algorithm (directional state machine, from swing.py):             |
//|   1. Compute ATR(period) over bar series (Wilder smoothing).      |
//|   2. Start in "up" direction at first valid-ATR bar.              |
//|   3. In up state: extend cur_high; emit 'high' pivot and switch   |
//|      to "down" when cur_high - low_i >= threshold.                |
//|   4. In down state: mirror.                                        |
//|   5. Threshold = atr.iloc[i] * atr_min_multiple, recomputed per   |
//|      bar (it scales with current ATR).                            |
//|                                                                   |
//| DEVIATION from plan.md spelled-out code: the plan's pseudocode    |
//| tracked running_high AND running_low simultaneously, but swing.py |
//| uses a directional state machine. This file ports swing.py        |
//| faithfully to keep MQL5 output byte-identical to Plan 4's pytest. |
//+------------------------------------------------------------------+
#property strict

enum SwingKind { SWING_HIGH = 1, SWING_LOW = -1 };

struct Swing {
    int       bar_idx;
    double    price;
    SwingKind kind;
};

//+------------------------------------------------------------------+
//| Compute ATR(period) into atr_out[], aligned with bars[].         |
//| Wilder smoothing matching helpers/atr.py compute_atr exactly.    |
//| First (period - 1) values are 0.0 (sentinel for NaN); valid ATR  |
//| starts at index (period - 1).                                    |
//+------------------------------------------------------------------+
void _ComputeATR(const MqlRates &bars[], int n, int period, double &atr_out[]) {
    ArrayResize(atr_out, n);
    ArrayInitialize(atr_out, 0.0);
    if (n == 0 || n < period) return;

    // Compute true range per bar.
    double tr[];
    ArrayResize(tr, n);
    // First bar TR uses only (high - low) — no prev_close.
    tr[0] = bars[0].high - bars[0].low;
    for (int i = 1; i < n; i++) {
        double prev_close = bars[i - 1].close;
        double tr1 = bars[i].high - bars[i].low;
        double tr2 = MathAbs(bars[i].high - prev_close);
        double tr3 = MathAbs(bars[i].low - prev_close);
        double max12 = (tr1 > tr2) ? tr1 : tr2;
        tr[i] = (max12 > tr3) ? max12 : tr3;
    }

    // Simple average over first `period` TR values.
    double sum = 0.0;
    for (int j = 0; j < period; j++) sum += tr[j];
    atr_out[period - 1] = sum / period;

    // Recursive Wilder smoothing for the rest.
    for (int i = period; i < n; i++) {
        atr_out[i] = (atr_out[i - 1] * (period - 1) + tr[i]) / period;
    }
}

//+------------------------------------------------------------------+
//| Detect swing pivots in bars[] of length n.                        |
//| Returns count of detected swings; populates output[] in           |
//| chronological order. Empty (count=0) if too few bars to compute   |
//| ATR or no retracement ever exceeds threshold.                     |
//|                                                                   |
//| atr_min_multiple: multiplier × per-bar ATR = pivot threshold.     |
//| atr_period: lookback for Wilder ATR (default 20 per strategy_ea). |
//+------------------------------------------------------------------+
int Swing_Detect(const MqlRates &bars[], int n,
                 double atr_min_multiple, int atr_period,
                 Swing &output[]) {
    ArrayResize(output, 0);
    if (n < atr_period + 2) return 0;

    double atr[];
    _ComputeATR(bars, n, atr_period, atr);

    ArrayResize(output, n);  // upper bound
    int out_count = 0;

    // Start scanning from first bar with valid ATR (index period - 1).
    int start = atr_period - 1;
    int    cur_high_idx = start;
    double cur_high_price = bars[start].high;
    int    cur_low_idx = start;
    double cur_low_price = bars[start].low;

    // Initial direction = "up" (matches swing.py).
    // 0 = up, 1 = down
    int direction = 0;

    for (int i = start + 1; i < n; i++) {
        double threshold = atr[i] * atr_min_multiple;
        if (atr[i] <= 0.0) continue;  // skip pre-ATR bars (sentinel for NaN)

        if (direction == 0) {  // up
            if (bars[i].high > cur_high_price) {
                cur_high_price = bars[i].high;
                cur_high_idx = i;
            } else if (cur_high_price - bars[i].low >= threshold) {
                // Drop from tracked high exceeded threshold — emit the high.
                output[out_count].bar_idx = cur_high_idx;
                output[out_count].price   = cur_high_price;
                output[out_count].kind    = SWING_HIGH;
                out_count++;
                cur_low_price = bars[i].low;
                cur_low_idx = i;
                direction = 1;  // down
            }
        } else {  // down
            if (bars[i].low < cur_low_price) {
                cur_low_price = bars[i].low;
                cur_low_idx = i;
            } else if (bars[i].high - cur_low_price >= threshold) {
                output[out_count].bar_idx = cur_low_idx;
                output[out_count].price   = cur_low_price;
                output[out_count].kind    = SWING_LOW;
                out_count++;
                cur_high_price = bars[i].high;
                cur_high_idx = i;
                direction = 0;  // up
            }
        }
    }

    ArrayResize(output, out_count);
    return out_count;
}
