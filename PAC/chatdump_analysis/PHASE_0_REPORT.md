# Phase 0 -- Exit Report

**Run date:** 2026-05-25
**Branch:** phase-0-pac-chatdump-mining

## Inputs
- chatdump: `C:/Users/nikof/Documents/GitHub/PAC/chatdump.json` (42 MB, 15,231 messages: 2,123 mentor + 13,108 student)
- assets: `C:/Users/nikof/Documents/GitHub/PAC/assests/` (6,670 files)

## Asset cleanup result

| Bucket | Count |
|---|---|
| emoji_svg | 206 |
| emoji_gif | 8 |
| avatar | 409 |
| strategy_artifact | 6 |
| chart | 6,041 |
| **TOTAL** | **6,670** |

Files were moved (not deleted). `_junk/` holds 623 files (emoji + avatars); `source-materials/` holds 6,047 files (charts + strategy artifacts). User must manually delete `_junk/` once reviewed.

## Chatdump parsing result
- Total messages: 15,231 (2,123 mentor / 13,108 student)
- Catalog rows (HIGH + MEDIUM): 167
- Unparsed rows (LOW): 275
- Mentor catalog rows: 8
- Student catalog rows: 159

## Component frequency (top 10)

| Component | Mentor | Student | Mentor share |
|---|---:|---:|---:|
| `measured_move` | 50 | 310 | 13.9% |
| `ema_sma` | 35 | 287 | 10.9% |
| `trap_setup` | 24 | 115 | 17.3% |
| `fail_setup` | 18 | 113 | 13.7% |
| `spike_channel` | 16 | 138 | 10.4% |
| `fibonacci` | 16 | 190 | 7.8% |
| `elliott` | 13 | 125 | 9.4% |
| `session_box` | 7 | 68 | 9.3% |
| `signal_candle` | 2 | 6 | 25.0% |
| `battle_zone` | 2 | 33 | 5.7% |

## Setup distribution highlights
- Top symbols by mentor activity: GOLD/XAUUSD (treated as the same instrument; dominates both mentor and student rows), USOIL/CL, US500, NAS100, EURUSD
- Top sessions: london and america dominate; asia is rare (only ~5 rows); one row tagged "dead" (off-hours)
- Top day-of-week: Mon, Tue, Wed appear across almost every symbol bucket; Thu is common; Fri has moderate activity; Sun/weekend nearly absent

## Mentor audit highlights
- Mentor trades audited: 8
- Most common deviation flags: `missing_sl` (all 8 rows), `missing_tp` (all 8 rows), `no_screenshot` (all 8 rows), `unclassified_setup` (6 of 8 rows; 2 rows have `measured_move` classification)
- Spot-check disagreement rate: 1/20. Row "NQ SELL | moze short na NQ hmm" is borderline -- it is a speculative statement rather than a firm trade call, but it was correctly included with HIGH confidence because it contains a screenshot URL plus direction + symbol. Reasonable. One row with a blank `content_pl` (USDCHF BUY) was correctly captured via symbol/direction emoji detection even without text. No obvious mis-classifications found; 0 genuine chat-only messages incorrectly elevated to HIGH.

## Phase 0 exit-criteria checklist
- [x] Cleanup report reviewed; `_junk/` ready for manual delete (user must do this themselves).
- [x] `trades_catalog.csv` produced with 167 rows -- spot-check looks reasonable.
- [x] `component_frequency.md` ranked list produced; feeds Phase 1 inclusion rule.
- [x] `mentor_audit.md` produced; setup classifications ready for user arbitration.

## Notes / follow-ups for Phase 1

**Components most-referenced by mentors (from frequency report):**
1. `measured_move` (50 mentor refs, 13.9% share)
2. `ema_sma` (35 mentor refs)
3. `trap_setup` (24 mentor refs, 17.3% share -- highest mentor share in top 5)
4. `fail_setup` (18 mentor refs)
5. `spike_channel` (16 mentor refs)

**Components rarely referenced or only by students:**
- `range_trap` (0 mentor, 0 student -- keyword pattern may be too strict)
- `range_fail` (0 mentor, 0 student -- same concern)
- `gap_candle` (0 mentor, 3 student)
- `mmd_clouds` (0 mentor, 16 student)
- `spike_flag` (1 mentor, 20 student)

**Symbols dominating activity** (by catalog row count):
1. XAUUSD (35 rows) + GOLD (25 rows) = 60 rows combined -- these are the same instrument; `instrument_universe.yml` should map both
2. USOIL (32 rows) + CL (7 rows) = 39 rows combined -- same instrument (WTI crude); map both
3. US500 (20 rows) + ES (1 row)
4. NAS100 (13 rows) + NQ (5 rows)
5. EURUSD (8 rows)

**Sessions/DOW patterns:**
- London session is the single most common session in the distribution table; America is nearly equal. Together they cover ~95% of all trade rows.
- Asia session appears in only ~5 rows; essentially negligible.
- Monday through Wednesday are the most trade-dense days; Friday is moderate; weekend is almost absent (2 Sun rows, likely timezone edge cases).

**Suggested quantitative thresholds inferable from data:**
- Catalog is 167 rows vs 275 unparsed (ratio 37.8%/62.2%); unparsed messages were typically low-signal commentary or range-day plans without a firm direction+symbol pair -- thresholds appear well-calibrated.
- All 8 mentor rows lack SL and TP numeric fields -- either the Discord format never included them or the extractor regex needs expansion in Phase 1 to capture replies/edit context.
- Setup classification is overwhelmingly `unclassified` (159/167 rows); the component keyword classifier is working but trade-call messages rarely contain component terminology in the same message -- Phase 1 should consider cross-referencing prior messages in a session for setup context.

**Open questions for the user before Phase 1:**
1. GOLD vs XAUUSD and USOIL vs CL are the same instruments with different ticker labels. Should they be normalized to a canonical ticker in `instrument_universe.yml`?
2. `range_trap` and `range_fail` keywords produced zero matches. Are these concepts used in the chat under different terminology? The patterns may need adjustment.
3. Translation pass was not run (--offline). Should the online pass be run before Phase 1 to populate `content_en` for English-language analysis?
4. All 8 mentor trades are missing SL/TP. Were these always absent in Discord or is a different extraction strategy (e.g., scanning the reply thread) needed?
5. Mentor catalog rows = 8 out of 167 (4.8%). This is lower than expected if mentors were actively trading in the chat. Verify the mentor identification list covers all known mentor Discord handles.

---

## Phase 1a refresh (2026-05-26)

Two data-quality patches landed:

1. **`range_trap` / `range_fail` keyword patterns widened** to match "Range 2 try trap", "Range-2 Try Trap", and "range 2 try fail" — the actual vocabulary in the Polish chat. Previously these components had zero matches.

2. **Symbol aliasing** added: `GOLD` is now canonicalized to `XAUUSD` and `CL` to `USOIL` at detection time. The trades catalog, component frequency, setup distribution, and mentor audit reports now use one canonical symbol per instrument.

### Refreshed numbers

- Catalog rows: 167
- Unparsed rows: 275
- Mentor catalog rows: 8
- Student catalog rows: 159
- `range_trap` references: mentor=2, student=8 (previously 0/0)
- `range_fail` references: mentor=0, student=5 (previously 0/0)
- Top symbols (canonicalized): XAUUSD=60, USOIL=39, US500=20, NAS100=13, EURUSD=8, GC=6 (gold futures contract, CME — distinct from XAUUSD spot; intentionally not aliased), GBPUSD=4, USDCAD=4

The original-run numbers in the sections above remain as-is for historical reference; the refreshed pipeline output files in this directory are the authoritative current state.
