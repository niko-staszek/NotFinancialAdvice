#ifndef ORB_LEDGER_MQH
#define ORB_LEDGER_MQH
int ORB_LedgerOpen(string path){
  int h=FileOpen(path,FILE_WRITE|FILE_CSV|FILE_ANSI,",");
  if(h!=INVALID_HANDLE)
    FileWrite(h,"trade_id","symbol","dir","ts_open_utc","ts_close_utc","entry","sl","tp",
                "lots","exit_reason","gross_pnl","commission","swap","net_pnl","r_multiple",
                "bias_ema","rvol","or_width","stop_arm","exit_arm");
  return h;
}
void ORB_LedgerRow(int h,int id,string sym,int dir,datetime to,datetime tc,double entry,double sl,
                   double tp,double lots,string reason,double gross,double comm,double swap,
                   double net,double rmult,double biasEma,double rvol,double orw,int sArm,int eArm){
  if(h==INVALID_HANDLE) return;
  FileWrite(h,id,sym,(dir>0?"long":"short"),(string)(long)to,(string)(long)tc,entry,sl,tp,lots,
            reason,gross,comm,swap,net,rmult,biasEma,rvol,orw,sArm,eArm);
}
void ORB_LedgerClose(int h){ if(h!=INVALID_HANDLE) FileClose(h); }
#endif
