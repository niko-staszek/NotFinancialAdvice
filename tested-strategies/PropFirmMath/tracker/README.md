# Prop-Firm Tracker — how to use

`PropFirm_Tracker.xlsx` — tracks your evals, trades, and payouts; the Dashboard auto-calculates.

## Open it as a Google Sheet
1. Go to **Google Drive → New → File upload →** pick `PropFirm_Tracker.xlsx`.
2. Double-click it → **Open with → Google Sheets** (it converts to a native Sheet). Save a copy.
   *(Or just open in Excel — same file.)*

## The 4 tabs
- **Dashboard** — read-only summary. Updates itself from the other tabs. Pass rate, total spend, total
  payouts, NET, return multiple, win rate, total R.
- **Accounts** — one row per eval/account you buy. Fill **Firm, Size, Eval cost, Result** (dropdown:
  Pending/Passed/Failed), Date, Notes.
- **Trades** — one row per trade. Fill the dropdowns (Block, Dir, Type, Result = TP/SL/BE). **R fills in
  automatically** (TP = +1.5, SL = −1, BE = 0). PnL ($) you type in.
- **Payouts** — one row per withdrawal. Date, Firm, Amount.

## Honest note
The Dashboard's win rate / R is a **tally of what you log**, not a validated backtest — it excludes costs
and slippage. Use it to track real results, not to "prove" the strategy. The real test is the Python
backtest (Phase 0 in `../PROPFIRM_ROADMAP.md`).
