// ORB_Time.mqh — anchor the opening range to NY 09:30 ET using the US DST calendar.
#ifndef ORB_TIME_MQH
#define ORB_TIME_MQH

// nth weekday helper: day-of-month for the `nth` `dow` (0=Sun) in (year,month).
int ORB_NthWeekday(int year,int month,int dow,int nth){
  datetime first = StringToTime(StringFormat("%04d.%02d.01 00:00:00",year,month));
  MqlDateTime t; TimeToStruct(first,t);
  int shift = (dow - t.day_of_week + 7) % 7;
  return 1 + shift + (nth-1)*7;
}
// last weekday-of-month
int ORB_LastWeekday(int year,int month,int dow){
  int dim = 31; // walk back to a valid date
  while(true){ datetime d=StringToTime(StringFormat("%04d.%02d.%02d 00:00:00",year,month,dim));
    MqlDateTime t; TimeToStruct(d,t); if(t.mon==month) break; dim--; }
  datetime last = StringToTime(StringFormat("%04d.%02d.%02d 00:00:00",year,month,dim));
  MqlDateTime lt; TimeToStruct(last,lt);
  int shift = (lt.day_of_week - dow + 7) % 7;
  return dim - shift;
}

// US DST: 2nd Sunday March 07:00 UTC -> 1st Sunday Nov 06:00 UTC.
bool ORB_IsUsDST(datetime utc){
  MqlDateTime t; TimeToStruct(utc,t);
  int y=t.year;
  datetime start=StringToTime(StringFormat("%04d.03.%02d 07:00:00",y,ORB_NthWeekday(y,3,0,2)));
  datetime end  =StringToTime(StringFormat("%04d.11.%02d 06:00:00",y,ORB_NthWeekday(y,11,0,1)));
  return (utc>=start && utc<end);
}
datetime ORB_UtcToEt(datetime utc){ return utc - (ORB_IsUsDST(utc) ? 4*3600 : 5*3600); }
int ORB_EtMinutesOfDay(datetime et){ MqlDateTime t; TimeToStruct(et,t); return t.hour*60+t.min; }

// server time + (server->UTC offset seconds) -> UTC -> ET minutes-of-day
int ORB_EtMinutesFromServer(datetime serverTime,int srvToUtcOffsetSec){
  datetime utc = serverTime - srvToUtcOffsetSec;   // server = UTC + offset
  return ORB_EtMinutesOfDay(ORB_UtcToEt(utc));
}
bool ORB_InOpeningRange(datetime serverTime,int srvToUtcOffsetSec,int orMinutes){
  int m=ORB_EtMinutesFromServer(serverTime,srvToUtcOffsetSec);
  return (m>=570 && m<570+orMinutes);            // 09:30 .. 09:30+orMinutes
}
bool ORB_InEntryWindow(datetime serverTime,int srvToUtcOffsetSec,int startEt,int endEt){
  int m=ORB_EtMinutesFromServer(serverTime,srvToUtcOffsetSec);
  int s=(startEt/100)*60+(startEt%100), e=(endEt/100)*60+(endEt%100);
  return (m>=s && m<e);
}
bool ORB_AtOrAfterFlat(datetime serverTime,int srvToUtcOffsetSec,int flatEt){
  int m=ORB_EtMinutesFromServer(serverTime,srvToUtcOffsetSec);
  int f=(flatEt/100)*60+(flatEt%100);
  return (m>=f);
}
#endif
