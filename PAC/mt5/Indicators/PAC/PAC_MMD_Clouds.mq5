//+------------------------------------------------------------------+
//| PAC_MMD_Clouds.mq5                                                |
//| Port of MMD/pine/mmd_clouds.pine — 3 main clouds (Orange 48,      |
//| Blue 288, Green 1440). NO secondary clouds, NO ribbons,          |
//| NO diamonds — strict parity with Plan 4 mmd.py scope.            |
//| iCustom contract: see Plan 5 design spec Section 2.              |
//+------------------------------------------------------------------+
#property copyright "PAC"
#property indicator_chart_window
#property indicator_buffers 9
#property indicator_plots   6

// Plots: 6 visible (EMA+SMA × 3 clouds). Cloud-value buffers are hidden.
#property indicator_label1  "EMA 48"
#property indicator_type1   DRAW_LINE
#property indicator_color1  clrOrange
#property indicator_label2  "SMA 48"
#property indicator_type2   DRAW_LINE
#property indicator_color2  clrOrange
#property indicator_label3  "EMA 288"
#property indicator_type3   DRAW_LINE
#property indicator_color3  clrBlue
#property indicator_label4  "SMA 288"
#property indicator_type4   DRAW_LINE
#property indicator_color4  clrBlue
#property indicator_label5  "EMA 1440"
#property indicator_type5   DRAW_LINE
#property indicator_color5  clrGreen
#property indicator_label6  "SMA 1440"
#property indicator_type6   DRAW_LINE
#property indicator_color6  clrGreen

input int InpP48   = 48;
input int InpP288  = 288;
input int InpP1440 = 1440;

double ema48_buf[];
double sma48_buf[];
double ema288_buf[];
double sma288_buf[];
double ema1440_buf[];
double sma1440_buf[];
double cv48_buf[];     // hidden
double cv288_buf[];    // hidden
double cv1440_buf[];   // hidden

int g_h_ema48 = INVALID_HANDLE, g_h_sma48 = INVALID_HANDLE;
int g_h_ema288 = INVALID_HANDLE, g_h_sma288 = INVALID_HANDLE;
int g_h_ema1440 = INVALID_HANDLE, g_h_sma1440 = INVALID_HANDLE;

int OnInit() {
    if (Period() != PERIOD_M5) {
        Alert("PAC_MMD_Clouds: requires M5 chart timeframe");
        return INIT_FAILED;
    }

    SetIndexBuffer(0, ema48_buf,  INDICATOR_DATA);
    SetIndexBuffer(1, sma48_buf,  INDICATOR_DATA);
    SetIndexBuffer(2, ema288_buf, INDICATOR_DATA);
    SetIndexBuffer(3, sma288_buf, INDICATOR_DATA);
    SetIndexBuffer(4, ema1440_buf, INDICATOR_DATA);
    SetIndexBuffer(5, sma1440_buf, INDICATOR_DATA);
    SetIndexBuffer(6, cv48_buf,   INDICATOR_CALCULATIONS);
    SetIndexBuffer(7, cv288_buf,  INDICATOR_CALCULATIONS);
    SetIndexBuffer(8, cv1440_buf, INDICATOR_CALCULATIONS);

    g_h_ema48   = iMA(_Symbol, PERIOD_M5, InpP48,   0, MODE_EMA, PRICE_CLOSE);
    g_h_sma48   = iMA(_Symbol, PERIOD_M5, InpP48,   0, MODE_SMA, PRICE_CLOSE);
    g_h_ema288  = iMA(_Symbol, PERIOD_M5, InpP288,  0, MODE_EMA, PRICE_CLOSE);
    g_h_sma288  = iMA(_Symbol, PERIOD_M5, InpP288,  0, MODE_SMA, PRICE_CLOSE);
    g_h_ema1440 = iMA(_Symbol, PERIOD_M5, InpP1440, 0, MODE_EMA, PRICE_CLOSE);
    g_h_sma1440 = iMA(_Symbol, PERIOD_M5, InpP1440, 0, MODE_SMA, PRICE_CLOSE);

    if (g_h_ema48 == INVALID_HANDLE || g_h_sma48 == INVALID_HANDLE
     || g_h_ema288 == INVALID_HANDLE || g_h_sma288 == INVALID_HANDLE
     || g_h_ema1440 == INVALID_HANDLE || g_h_sma1440 == INVALID_HANDLE) {
        Print("PAC_MMD_Clouds: iMA handle init failed; err=", GetLastError());
        return INIT_FAILED;
    }

    IndicatorSetString(INDICATOR_SHORTNAME, "PAC_MMD_Clouds(48,288,1440)");
    return INIT_SUCCEEDED;
}

int OnCalculate(const int rates_total, const int prev_calculated,
                const datetime &time[], const double &open[],
                const double &high[], const double &low[],
                const double &close[], const long &tick_volume[],
                const long &volume[], const int &spread[]) {
    int to_copy = (prev_calculated == 0) ? rates_total : rates_total - prev_calculated + 1;
    if (to_copy <= 0) return rates_total;

    int start = (prev_calculated == 0) ? 0 : prev_calculated - 1;

    if (CopyBuffer(g_h_ema48,   0, 0, rates_total, ema48_buf)   <= 0) return 0;
    if (CopyBuffer(g_h_sma48,   0, 0, rates_total, sma48_buf)   <= 0) return 0;
    if (CopyBuffer(g_h_ema288,  0, 0, rates_total, ema288_buf)  <= 0) return 0;
    if (CopyBuffer(g_h_sma288,  0, 0, rates_total, sma288_buf)  <= 0) return 0;
    if (CopyBuffer(g_h_ema1440, 0, 0, rates_total, ema1440_buf) <= 0) return 0;
    if (CopyBuffer(g_h_sma1440, 0, 0, rates_total, sma1440_buf) <= 0) return 0;

    for (int i = start; i < rates_total; i++) {
        cv48_buf[i]   = ema48_buf[i]   - sma48_buf[i];
        cv288_buf[i]  = ema288_buf[i]  - sma288_buf[i];
        cv1440_buf[i] = ema1440_buf[i] - sma1440_buf[i];
    }

    return rates_total;
}

void OnDeinit(const int reason) {
    if (g_h_ema48 != INVALID_HANDLE)   IndicatorRelease(g_h_ema48);
    if (g_h_sma48 != INVALID_HANDLE)   IndicatorRelease(g_h_sma48);
    if (g_h_ema288 != INVALID_HANDLE)  IndicatorRelease(g_h_ema288);
    if (g_h_sma288 != INVALID_HANDLE)  IndicatorRelease(g_h_sma288);
    if (g_h_ema1440 != INVALID_HANDLE) IndicatorRelease(g_h_ema1440);
    if (g_h_sma1440 != INVALID_HANDLE) IndicatorRelease(g_h_sma1440);
}
