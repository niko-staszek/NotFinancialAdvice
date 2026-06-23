// SH_Ledger.mqh — one UTF-8 CSV row per closed trade, written FILE_COMMON so the
// Strategy Tester and live share the same path. Header is gate-compatible (net_pnl).
#ifndef SH_LEDGER_MQH
#define SH_LEDGER_MQH
int SH_LedgerOpen(string path) {
  int h = FileOpen(path, FILE_WRITE|FILE_CSV|FILE_ANSI|FILE_COMMON, ",");
  if (h != INVALID_HANDLE)
    FileWrite(h, "trade_id","symbol","dir","ts_open_utc","ts_close_utc","entry","sl","tp",
                 "lots","exit_reason","gross_pnl","commission","swap","net_pnl","r_multiple",
                 "swept_level","sweep_side","target_mode","fill_depth");
  return h;
}
void SH_LedgerRow(int h,int id,string sym,int dir,datetime to,datetime tc,double entry,double sl,
                  double tp,double lots,string reason,double gross,double comm,double swap,double net,
                  double rmult,double sweptLevel,int sweepSide,string targetMode,double fillDepth) {
  if (h == INVALID_HANDLE) return;
  FileWrite(h, id, sym, (dir>0?"long":"short"), (string)(long)to, (string)(long)tc, entry, sl, tp,
               lots, reason, gross, comm, swap, net, rmult,
               sweptLevel, sweepSide, targetMode, fillDepth);
}
void SH_LedgerClose(int h) { if (h != INVALID_HANDLE) FileClose(h); }
#endif
