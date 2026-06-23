# tools/sync_sweephunter_to_terminal.ps1 — mirror SweepHunter sources into the FTMO terminal tree.
# Also copies the shared ORB_Time.mqh dependency (SH_Time.mqh includes ..\ORB\ORB_Time.mqh).
param(
  [string]$DataDir = "$env:APPDATA\MetaQuotes\Terminal\81A933A9AFC5DE3C23B15CAB19C63850"
)
$ErrorActionPreference = "Stop"
$src = "tested-strategies/SweepHunter/mt5"

# SweepHunter's own trees
foreach ($sub in @("Include/SweepHunter","Experts/SweepHunter","Scripts/SweepHunter_Tests")) {
  $dst = Join-Path "$DataDir/MQL5" $sub
  New-Item -ItemType Directory -Force $dst | Out-Null
  Copy-Item "$src/$sub/*" $dst -Recurse -Force
}

# Shared dependency: ORB_Time.mqh (DST/ET calendars) into Include/ORB/
$orbInc = Join-Path "$DataDir/MQL5" "Include/ORB"
New-Item -ItemType Directory -Force $orbInc | Out-Null
Copy-Item "tested-strategies/ORB/mt5/Include/ORB/ORB_Time.mqh" $orbInc -Force

Write-Host "Synced SweepHunter sources (+ ORB_Time dep) to $DataDir/MQL5"
