# tools/sync_orb_to_terminal.ps1 — mirror ORB MQL5 sources into the FTMO terminal tree
param(
  [string]$DataDir = "$env:APPDATA\MetaQuotes\Terminal\81A933A9AFC5DE3C23B15CAB19C63850"
)
$ErrorActionPreference = "Stop"
$src = "tested-strategies/ORB/mt5"
foreach ($sub in @("Include/ORB","Experts/ORB","Scripts/ORB_Tests")) {
  $dst = Join-Path "$DataDir/MQL5" $sub
  New-Item -ItemType Directory -Force $dst | Out-Null
  Copy-Item "$src/$sub/*" $dst -Recurse -Force
}
Write-Host "Synced ORB sources to $DataDir/MQL5"
