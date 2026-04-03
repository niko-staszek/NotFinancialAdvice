//+------------------------------------------------------------------+
//| CBS_Clusters.mqh v1.0                                            |
//| CLU Filter: Fibonacci retracement cluster blocker                |
//|                                                                  |
//| Per strategy.md: clusters form when Fib levels from PD/PW/PM    |
//| land close together. If a cluster sits between entry and target, |
//| trade waits for price to clear it before entering.               |
//|                                                                  |
//| Matches Python 18_best_targets.py:                               |
//|   compute_fib_clusters() L193-221                                |
//|   find_blockers() L224-239                                       |
//|   compute_prev_period_levels() L242-267                          |
//|   CLU logic in simulate() L431-473                               |
//+------------------------------------------------------------------+
#ifndef CBS_CLUSTERS_MQH
#define CBS_CLUSTERS_MQH

//+------------------------------------------------------------------+
//| Constants                                                         |
//+------------------------------------------------------------------+
#define CLU_MAX_LEVELS    21    // 7 Fib ratios x 3 periods
#define CLU_MAX_CLUSTERS  15    // Max clusters after grouping
#define CLU_MAX_BLOCKERS  10    // Max blockers between entry and target
#define CLU_N_FIBS        7     // Number of Fib ratios

// Fib ratios from Python: FIB_LEVELS = [0.382, 0.618, -0.382, -0.618, 1.382, 1.618, 2.618]
double g_fibRatios[CLU_N_FIBS] = {0.382, 0.618, -0.382, -0.618, 1.382, 1.618, 2.618};

//+------------------------------------------------------------------+
//| Cluster struct                                                    |
//+------------------------------------------------------------------+
struct FibCluster
{
   double center;     // Average price of levels in cluster
   double zone_low;   // Cluster zone lower boundary
   double zone_high;  // Cluster zone upper boundary
   int    n_periods;  // Number of distinct periods contributing (need >= 2)
};

//+------------------------------------------------------------------+
//| Blocker struct (cluster between entry and target)                  |
//+------------------------------------------------------------------+
struct Blocker
{
   double center;      // Cluster center price
   double clear_price; // Price that must be exceeded to clear this blocker
};

//+------------------------------------------------------------------+
//| Get Previous Day High/Low from D1 bars                            |
//| shift=1 means yesterday's bar                                    |
//+------------------------------------------------------------------+
bool GetPrevDayHL(string symbol, double &high, double &low)
{
   MqlRates d1[];
   ArraySetAsSeries(d1, true);

   if(CopyRates(symbol, PERIOD_D1, 1, 1, d1) < 1)
      return false;

   high = d1[0].high;
   low  = d1[0].low;
   return true;
}

//+------------------------------------------------------------------+
//| Get Previous Week High/Low                                        |
//| Scans last 5 D1 bars before today (approximate prev week)        |
//+------------------------------------------------------------------+
bool GetPrevWeekHL(string symbol, double &high, double &low)
{
   MqlRates d1[];
   ArraySetAsSeries(d1, true);

   // Get up to 10 D1 bars, skip today (shift 1), take 5
   int copied = CopyRates(symbol, PERIOD_D1, 1, 5, d1);
   if(copied < 2)
      return false;

   high = d1[0].high;
   low  = d1[0].low;
   for(int i = 1; i < copied; i++)
   {
      if(d1[i].high > high) high = d1[i].high;
      if(d1[i].low  < low)  low  = d1[i].low;
   }
   return true;
}

//+------------------------------------------------------------------+
//| Get Previous Month High/Low                                       |
//| Scans last ~22 D1 bars before today                               |
//+------------------------------------------------------------------+
bool GetPrevMonthHL(string symbol, double &high, double &low)
{
   MqlRates d1[];
   ArraySetAsSeries(d1, true);

   int copied = CopyRates(symbol, PERIOD_D1, 1, 22, d1);
   if(copied < 5)
      return false;

   high = d1[0].high;
   low  = d1[0].low;
   for(int i = 1; i < copied; i++)
   {
      if(d1[i].high > high) high = d1[i].high;
      if(d1[i].low  < low)  low  = d1[i].low;
   }
   return true;
}

//+------------------------------------------------------------------+
//| Project Fib levels from a single period's high/low                |
//| levels[] must be pre-sized to at least CLU_N_FIBS                |
//| Returns number of levels added                                    |
//+------------------------------------------------------------------+
int ProjectFibLevels(double high, double low, double &levels[], int start_idx, int period_id)
{
   double range = high - low;
   if(range <= 0)
      return 0;

   int count = 0;
   for(int i = 0; i < CLU_N_FIBS; i++)
   {
      int idx = start_idx + count;
      if(idx >= ArraySize(levels))
         break;
      levels[idx] = low + range * g_fibRatios[i];
      count++;
   }
   return count;
}

//+------------------------------------------------------------------+
//| Sort a double array (simple insertion sort, small arrays)         |
//+------------------------------------------------------------------+
void SortDoubles(double &arr[], int size)
{
   for(int i = 1; i < size; i++)
   {
      double key = arr[i];
      int j = i - 1;
      while(j >= 0 && arr[j] > key)
      {
         arr[j + 1] = arr[j];
         j--;
      }
      arr[j + 1] = key;
   }
}

//+------------------------------------------------------------------+
//| Build Fib clusters from PD/PW/PM levels                           |
//|                                                                   |
//| Matches Python compute_fib_clusters() L193-221:                  |
//| 1. Project 7 Fib levels from each of PD/PW/PM (21 total)        |
//| 2. Sort all levels by price                                      |
//| 3. Group levels within cluster_size_pips of each other           |
//| 4. Keep groups that contain levels from 2+ distinct periods      |
//|                                                                   |
//| Returns: number of clusters found                                 |
//+------------------------------------------------------------------+
int BuildClusters(string symbol, double pip_size, double cluster_size_pips,
                  FibCluster &clusters[])
{
   ArrayResize(clusters, CLU_MAX_CLUSTERS);

   // Get period levels
   double pd_h, pd_l, pw_h, pw_l, pm_h, pm_l;
   bool has_pd = GetPrevDayHL(symbol, pd_h, pd_l);
   bool has_pw = GetPrevWeekHL(symbol, pw_h, pw_l);
   bool has_pm = GetPrevMonthHL(symbol, pm_h, pm_l);

   if(!has_pd && !has_pw && !has_pm)
      return 0;

   // Project all Fib levels + track which period each came from
   double all_levels[CLU_MAX_LEVELS];
   int    level_period[CLU_MAX_LEVELS];  // 0=PD, 1=PW, 2=PM
   int    n_levels = 0;

   if(has_pd)
   {
      int added = ProjectFibLevels(pd_h, pd_l, all_levels, n_levels, 0);
      for(int i = 0; i < added; i++) level_period[n_levels + i] = 0;
      n_levels += added;
   }
   if(has_pw)
   {
      int added = ProjectFibLevels(pw_h, pw_l, all_levels, n_levels, 1);
      for(int i = 0; i < added; i++) level_period[n_levels + i] = 1;
      n_levels += added;
   }
   if(has_pm)
   {
      int added = ProjectFibLevels(pm_h, pm_l, all_levels, n_levels, 2);
      for(int i = 0; i < added; i++) level_period[n_levels + i] = 2;
      n_levels += added;
   }

   if(n_levels < 2)
      return 0;

   // Sort levels (carry period_id along)
   // Simple parallel sort by level price
   for(int i = 1; i < n_levels; i++)
   {
      double keyL = all_levels[i];
      int    keyP = level_period[i];
      int j = i - 1;
      while(j >= 0 && all_levels[j] > keyL)
      {
         all_levels[j + 1]   = all_levels[j];
         level_period[j + 1] = level_period[j];
         j--;
      }
      all_levels[j + 1]   = keyL;
      level_period[j + 1] = keyP;
   }

   // Group into clusters (same algorithm as Python)
   double cdist = cluster_size_pips * pip_size;
   int n_clusters = 0;
   int i = 0;

   while(i < n_levels && n_clusters < CLU_MAX_CLUSTERS)
   {
      // Start a new group from level[i]
      int group_start = i;
      int j = i + 1;

      // Extend group while levels are within cdist of the first level
      while(j < n_levels && (all_levels[j] - all_levels[group_start]) <= cdist)
         j++;

      // Count distinct periods in this group
      bool has_period[3] = {false, false, false};
      for(int k = group_start; k < j; k++)
         has_period[level_period[k]] = true;

      int n_periods = 0;
      for(int k = 0; k < 3; k++)
         if(has_period[k]) n_periods++;

      // Only keep clusters from 2+ distinct periods
      if(n_periods >= 2)
      {
         double sum = 0;
         double lo  = all_levels[group_start];
         double hi  = all_levels[j - 1];

         for(int k = group_start; k < j; k++)
            sum += all_levels[k];

         clusters[n_clusters].center    = sum / (j - group_start);
         clusters[n_clusters].zone_low  = lo;
         clusters[n_clusters].zone_high = hi;
         clusters[n_clusters].n_periods = n_periods;
         n_clusters++;
      }

      // Advance: skip past group (or step by 1 if no group formed)
      i = (j > group_start + 1) ? j : (i + 1);
   }

   return n_clusters;
}

//+------------------------------------------------------------------+
//| Find blockers between entry and target                            |
//|                                                                   |
//| Matches Python find_blockers() L224-239:                         |
//| A blocker is a cluster zone that sits between entry and target.  |
//|                                                                   |
//| For BUY (entry < target):                                        |
//|   blocker if zone_low > entry AND zone_high < target             |
//|   clear_price = zone_high (price must exceed this to clear)      |
//|                                                                   |
//| For SELL (entry > target):                                       |
//|   blocker if zone_low > target AND zone_high < entry             |
//|   clear_price = zone_low (price must drop below this to clear)   |
//|                                                                   |
//| Returns: number of blockers found                                 |
//+------------------------------------------------------------------+
int FindBlockers(double entry, double target,
                 const FibCluster &clusters[], int n_clusters,
                 double pip_size, double cluster_size_pips,
                 Blocker &blockers[])
{
   ArrayResize(blockers, CLU_MAX_BLOCKERS);
   int n_blockers = 0;

   double hz = cluster_size_pips * pip_size;  // Half-zone expansion
   bool is_buy = (target > entry);

   for(int i = 0; i < n_clusters && n_blockers < CLU_MAX_BLOCKERS; i++)
   {
      double width_price = clusters[i].zone_high - clusters[i].zone_low;
      double half_zone   = MathMax(hz, width_price / 2.0 + hz);
      double zlo = clusters[i].center - half_zone;
      double zhi = clusters[i].center + half_zone;

      if(is_buy)
      {
         // BUY: blocker must be above entry and below target
         if(zlo > entry && zhi < target)
         {
            blockers[n_blockers].center      = clusters[i].center;
            blockers[n_blockers].clear_price  = zhi;  // Must clear above this
            n_blockers++;
         }
      }
      else
      {
         // SELL: blocker must be below entry and above target
         if(zlo > target && zhi < entry)
         {
            blockers[n_blockers].center      = clusters[i].center;
            blockers[n_blockers].clear_price  = zlo;  // Must clear below this
            n_blockers++;
         }
      }
   }

   return n_blockers;
}

//+------------------------------------------------------------------+
//| CLU Filter: main entry point                                      |
//|                                                                   |
//| Returns: true  = BLOCKED (trade should NOT enter immediately)    |
//|          false = CLEAR (no blockers, trade can enter)             |
//|                                                                   |
//| If blocked, out_clear_price is set to the price that must be     |
//| exceeded before the trade can be entered (wait-for-clear logic). |
//|                                                                   |
//| Also enforces min_distance: if target is too close to entry,     |
//| the trade is blocked permanently (out_clear_price = 0).          |
//+------------------------------------------------------------------+
bool CLUFilter(string symbol, double entry, double target,
               ENUM_ORDER_TYPE dir, double pip_size,
               double cluster_size_pips, double min_distance_pips,
               double &out_clear_price)
{
   out_clear_price = 0;

   // Minimum distance check (per EA_PARAMETERS_REFERENCE.md L81-82)
   double dist_pips = MathAbs(target - entry) / pip_size;
   if(dist_pips < min_distance_pips)
   {
      if(DebugMode)
         PrintFormat("[CBS CLU] Distance %.1f pips < min %.1f pips -> BLOCKED (permanent)",
                     dist_pips, min_distance_pips);
      return true;  // Permanently blocked, no clear price
   }

   // Build clusters
   FibCluster clusters[];
   int n_clusters = BuildClusters(symbol, pip_size, cluster_size_pips, clusters);

   if(n_clusters == 0)
      return false;  // No clusters -> clear

   // Find blockers between entry and target
   Blocker blockers[];
   int n_blockers = FindBlockers(entry, target, clusters, n_clusters,
                                  pip_size, cluster_size_pips, blockers);

   if(n_blockers == 0)
      return false;  // No blockers -> clear

   // Set clear price: the furthest obstacle from entry that must be cleared
   // For BUY: max of all clear_prices (highest zone_high to cross)
   // For SELL: min of all clear_prices (lowest zone_low to cross)
   if(dir == ORDER_TYPE_BUY)
   {
      out_clear_price = blockers[0].clear_price;
      for(int i = 1; i < n_blockers; i++)
         if(blockers[i].clear_price > out_clear_price)
            out_clear_price = blockers[i].clear_price;
   }
   else
   {
      out_clear_price = blockers[0].clear_price;
      for(int i = 1; i < n_blockers; i++)
         if(blockers[i].clear_price < out_clear_price)
            out_clear_price = blockers[i].clear_price;
   }

   if(DebugMode)
      PrintFormat("[CBS CLU] %d blocker(s) found. Clear price: %.5f",
                  n_blockers, out_clear_price);

   return true;  // Blocked — caller should use wait-for-clear logic
}

//+------------------------------------------------------------------+
//| Check if price has cleared the CLU obstacle                       |
//| Called on each timer tick while slot is in clu_waiting state      |
//|                                                                   |
//| For BUY:  price must have gone above clear_price                 |
//| For SELL: price must have gone below clear_price                 |
//+------------------------------------------------------------------+
bool HasClearedCLU(string symbol, ENUM_ORDER_TYPE dir, double clear_price)
{
   double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(symbol, SYMBOL_BID);

   if(dir == ORDER_TYPE_BUY)
      return (bid > clear_price);   // Price went above cluster zone
   else
      return (ask < clear_price);   // Price went below cluster zone
}

#endif // CBS_CLUSTERS_MQH
