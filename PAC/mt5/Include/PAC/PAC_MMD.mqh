//+------------------------------------------------------------------+
//| PAC_MMD.mqh — iCustom loader + ClassifyAlignment                  |
//| Mirror hedgehog/proposer/pac/mmd.py classify_alignment            |
//|                                                                   |
//| Canonical semantics (per mmd.py, authoritative):                  |
//|   full_bull = orange_mid > blue_mid > green_mid                   |
//|   full_bear = green_mid  > blue_mid > orange_mid                  |
//|   bull sentiment: full_bull→confirmed, full_bear→vetoed,          |
//|                   else→weakened                                    |
//|   bear sentiment: full_bear→confirmed, full_bull→vetoed,          |
//|                   else→weakened                                    |
//|   transitional sentiment: always weakened (safe default)          |
//|                                                                   |
//| Midpoint = (EMA + SMA) / 2 per cloud, read from PAC_MMD_Clouds    |
//| buffers 0..5 (EMA/SMA × 3 clouds).                                |
//|                                                                   |
//| DEVIATION from plan's spelled-out code: the plan implemented a    |
//| per-cloud count-of-agreement classifier (close > max(EMA,SMA))    |
//| with 3/3→confirmed, 2/3→weakened, ≤1/3→vetoed. That is not what  |
//| Plan 4's mmd.py does. The Plan 5 design spec mandates this port  |
//| be "line-for-line" with mmd.py. Authoritative source: mmd.py      |
//| classify_alignment (midpoint stacking) and tests in               |
//| hedgehog/proposer/pac/tests/test_mmd.py.                          |
//+------------------------------------------------------------------+
#property strict
#ifndef __PAC_MMD_MQH__
#define __PAC_MMD_MQH__

//+------------------------------------------------------------------+
//| Raw EMA-minus-SMA cloud_value triple, as exposed by buffers 6/7/8 |
//| of PAC_MMD_Clouds. Kept for API parity with the iCustom contract  |
//| even though midpoint-based classification reads buffers 0..5.     |
//+------------------------------------------------------------------+
struct CloudValues {
    double orange;   // period 48  cloud value = ema48  - sma48
    double blue;     // period 288 cloud value = ema288 - sma288
    double green;    // period 1440 cloud value = ema1440 - sma1440
};

//+------------------------------------------------------------------+
//| Cloud midpoints (one per main cloud). Midpoint = (EMA+SMA)/2.    |
//| This is the canonical input to mmd.py classify_alignment.        |
//+------------------------------------------------------------------+
struct CloudMidpoints {
    double orange_mid;   // period 48  midpoint
    double blue_mid;     // period 288 midpoint
    double green_mid;    // period 1440 midpoint
};

int  g_mmd_handle    = INVALID_HANDLE;
bool g_mmd_available = false;

bool InitMMD(string symbol) {
    g_mmd_handle = iCustom(symbol, PERIOD_M5, "PAC\\PAC_MMD_Clouds", 48, 288, 1440);
    g_mmd_available = (g_mmd_handle != INVALID_HANDLE);
    if (!g_mmd_available)
        PrintFormat("PAC_MMD: iCustom failed (err=%d) — fallback to weakened", GetLastError());
    return g_mmd_available;
}

void ReleaseMMD() {
    if (g_mmd_handle != INVALID_HANDLE) {
        IndicatorRelease(g_mmd_handle);
        g_mmd_handle = INVALID_HANDLE;
    }
    g_mmd_available = false;
}

bool MMD_Available() { return g_mmd_available; }

//+------------------------------------------------------------------+
//| Read the 3 precomputed cloud_value buffers (indices 6/7/8) at    |
//| the given bar shift. Mirrors the iCustom contract documented at   |
//| Plan 5 design spec Section 2.                                     |
//+------------------------------------------------------------------+
bool ReadCloudValues(int bar_shift, CloudValues &out) {
    if (!g_mmd_available) return false;
    double tmp[1];
    if (CopyBuffer(g_mmd_handle, 6, bar_shift, 1, tmp) != 1) return false;
    out.orange = tmp[0];
    if (CopyBuffer(g_mmd_handle, 7, bar_shift, 1, tmp) != 1) return false;
    out.blue = tmp[0];
    if (CopyBuffer(g_mmd_handle, 8, bar_shift, 1, tmp) != 1) return false;
    out.green = tmp[0];
    return true;
}

//+------------------------------------------------------------------+
//| Read EMA/SMA buffers (indices 0..5) at bar_shift and compute     |
//| midpoint = (ema + sma) / 2 for each of the 3 main clouds.         |
//+------------------------------------------------------------------+
bool ReadCloudMidpoints(int bar_shift, CloudMidpoints &out) {
    if (!g_mmd_available) return false;
    double tmp[1];
    double ema48, sma48, ema288, sma288, ema1440, sma1440;

    if (CopyBuffer(g_mmd_handle, 0, bar_shift, 1, tmp) != 1) return false;
    ema48 = tmp[0];
    if (CopyBuffer(g_mmd_handle, 1, bar_shift, 1, tmp) != 1) return false;
    sma48 = tmp[0];
    if (CopyBuffer(g_mmd_handle, 2, bar_shift, 1, tmp) != 1) return false;
    ema288 = tmp[0];
    if (CopyBuffer(g_mmd_handle, 3, bar_shift, 1, tmp) != 1) return false;
    sma288 = tmp[0];
    if (CopyBuffer(g_mmd_handle, 4, bar_shift, 1, tmp) != 1) return false;
    ema1440 = tmp[0];
    if (CopyBuffer(g_mmd_handle, 5, bar_shift, 1, tmp) != 1) return false;
    sma1440 = tmp[0];

    out.orange_mid = (ema48   + sma48)   * 0.5;
    out.blue_mid   = (ema288  + sma288)  * 0.5;
    out.green_mid  = (ema1440 + sma1440) * 0.5;
    return true;
}

//+------------------------------------------------------------------+
//| Pure classifier — line-for-line port of mmd.py classify_alignment.|
//| Inputs: three cloud midpoints + sentiment ("bull"/"bear"/         |
//| "transitional").                                                  |
//| Returns: "confirmed" | "weakened" | "vetoed".                     |
//+------------------------------------------------------------------+
string ClassifyAlignmentSimple(double orange_mid, double blue_mid,
                               double green_mid, string sentiment) {
    bool full_bull = (orange_mid > blue_mid) && (blue_mid > green_mid);
    bool full_bear = (green_mid  > blue_mid) && (blue_mid > orange_mid);

    if (sentiment == "bull") {
        if (full_bull) return "confirmed";
        if (full_bear) return "vetoed";
        return "weakened";
    }
    if (sentiment == "bear") {
        if (full_bear) return "confirmed";
        if (full_bull) return "vetoed";
        return "weakened";
    }
    // Transitional sentiment never reaches §3.5 composite — weakened as safe default.
    return "weakened";
}

//+------------------------------------------------------------------+
//| End-to-end: read live midpoint buffers + classify against         |
//| sentiment. Fallback per strategy_ea.md §3.2: indicator            |
//| unavailable → weakened (does NOT block trading).                  |
//|                                                                   |
//| `close` is accepted for API/signature stability with callers that |
//| may also want to log price context; the canonical mmd.py logic    |
//| does NOT consult close for the alignment decision itself.         |
//+------------------------------------------------------------------+
string ClassifyAlignmentLive(double close, string sentiment, int bar_shift) {
    if (!g_mmd_available) return "weakened";

    CloudMidpoints mids;
    if (!ReadCloudMidpoints(bar_shift, mids)) return "weakened";

    return ClassifyAlignmentSimple(mids.orange_mid, mids.blue_mid,
                                   mids.green_mid, sentiment);
}

//+------------------------------------------------------------------+
//| Convenience helper — classify directly from a CloudMidpoints      |
//| struct. Equivalent to ClassifyAlignmentSimple but accepts the     |
//| struct form for callers that already hold a CloudMidpoints.       |
//+------------------------------------------------------------------+
string ClassifyAlignmentFromMidpoints(CloudMidpoints &mids, string sentiment) {
    return ClassifyAlignmentSimple(mids.orange_mid, mids.blue_mid,
                                   mids.green_mid, sentiment);
}

#endif // __PAC_MMD_MQH__
