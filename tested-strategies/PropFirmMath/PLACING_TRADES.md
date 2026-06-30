# Placing Trades Across Prop Accounts — Dead Simple

How JJ spreads ~20–30 trades/day over ~30 accounts. **Based on his videos — not validated by us.**

## The golden rule
**Never put the SAME trade on all your accounts at once.** If it loses, they ALL lose together →
that's how you blow up. JJ calls copy-trading everything *"one of the worst things you can do."*

## The simple method (what he actually does — NO copy-trading)
- Each setup goes on **ONE account.** A **different** account each time.
- Over the day, ~30 accounts each take **about 1 trade.** Wins and losses average out across them.
- 5 accounts → **5 different setups**, not the same setup 5 times.

### Worked example (say you have 10 accounts)
| Time | Signal | Goes on |
|---|---|---|
| 9:33 AM | NY-AM continuation short | **Account 1** only |
| 9:50 AM | NY-AM reversion long | **Account 2** only |
| 2:05 PM | PM continuation | **Account 3** only |
| 6:05 PM | Evening continuation | **Account 4** only |
| … | … | …next account |
- If Account 1's trade loses → only Account 1 is hurt. The rest are fine. ✅
- **Wrong way:** put the 9:33 short on Accounts 1–10 → one loss = ten losses. ❌

## When you're starting (few accounts)
- Trade **one account at a time.** Setup → Account 1. Next setup → Account 2. Bank payouts, buy more, repeat.

## Which account gets which trade (routing)
- **Simple:** just rotate evenly (next free account).
- **Better:** send a **wide-stop / high-ATR** trade to a firm with more room; a tight one elsewhere. Each
  firm's best risk size differs — match the trade to the firm.
- **Evals vs funded:** be **aggressive on cheap evals** (take displacement entries); be **careful on funded**
  (wait for the break-of-structure). Different reward:risk is fine per firm.

## Scaling into a winner (his trick)
- Once a **funded** account is already **in profit** on a trade, you can add **evals in the SAME direction**
  (staggered entries) — like one big position spread across accounts. **Only add into something already working.**

## Risk rules — on EVERY account
- **Same fixed risk per trade** (1 unit). Size contracts to the stop (≈3 on a 16.5 stop, 2 on a 25, 1 on a 50).
- **Daily profit target AND hard daily loss limit per account** — hit either → stop that account for the day.
- If you ever gamble/tilt, do it on a **cheap fresh account** (~$500 real), never a +$10k one.

## Copy-trading (advanced — only much later)
- Only once you **know your numbers** (pass rate, payout rate, avg payout) **AND** risk-of-ruin < 5%
  (rule of thumb: **never under ~$10k invested**, ideally ~$50k/month income first).
- Even then: copy in **small clusters (~5 accounts), never all** — and still 5 *different* setups.

## Track it
Log every trade in the **Trades** tab of `tracker/PropFirm_Tracker.xlsx`, filling the **Account** column,
so you can see per-account results and never accidentally stack one trade everywhere.
