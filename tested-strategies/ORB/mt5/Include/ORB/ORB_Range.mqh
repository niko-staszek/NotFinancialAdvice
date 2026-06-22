#ifndef ORB_RANGE_MQH
#define ORB_RANGE_MQH
double ORB_Width(double hi,double lo){ return hi-lo; }
double ORB_Mid(double hi,double lo){ return (hi+lo)*0.5; }
double ORB_Median(const double &a[],int n){
  double b[]; ArrayResize(b,n); for(int i=0;i<n;i++) b[i]=a[i];
  ArraySort(b);
  if(n%2==1) return b[n/2];
  return (b[n/2-1]+b[n/2])*0.5;
}
double ORB_Rvol(double todayVol,const double &priorVols[],int n){
  double m=ORB_Median(priorVols,n); return (m>0.0)? todayVol/m : 0.0;
}
bool ORB_RangeGuardOk(double width,const double &priorWidths[],int n,double lo,double hi){
  double m=ORB_Median(priorWidths,n); if(m<=0.0) return false;
  return (width>=lo*m && width<=hi*m);
}
#endif
