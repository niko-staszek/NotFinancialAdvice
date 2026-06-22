# ORB MT5

## Deploy to the FTMO terminal
Copy `Include/ORB`, `Experts/ORB`, `Scripts/ORB_Tests` into
`%APPDATA%\MetaQuotes\Terminal\81A933A9AFC5DE3C23B15CAB19C63850\MQL5\`.
Use `tools/sync_orb_to_terminal.ps1`.

## Compile (headless)
`& "C:\Program Files\FTMO Global Markets MT5 Terminal\MetaEditor64.exe" /compile:"<DATADIR>\MQL5\Experts\ORB\ORB_EA.mq5" /log:"<DATADIR>\MQL5\Logs\orb_compile.log"`
Exit code is unreliable — read the log and confirm "0 errors, 0 warnings".

## Unit tests (headless)
`python tools/run_mql5_tests.py --script-dir ORB/mt5/Scripts/ORB_Tests --terminal "C:\Program Files\FTMO Global Markets MT5 Terminal\terminal64.exe" --data-root "%APPDATA%\MetaQuotes\Terminal"`
