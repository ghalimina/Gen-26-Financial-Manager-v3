# 🏛️ GEN-26 V42 — FINAL PAPER TRADING TRUTH

## 1. CURRENT TRUTH
- **Verified Paper Days:** 0
- **Required Paper Days:** 30
- **Remaining Days:** 30
- **Authoritative Source:** `data/authoritative_paper_sessions.json`

## 2. SESSION DEFINITION (SessionManager)
A paper session is only counted as **1 Valid Day** if:
1. It is logged in `authoritative_paper_sessions.json` by `SessionManager.complete_session()`.
2. `status` == 'COMPLETED'
3. `completion_status` == 'SUCCESS'
4. The `market_date` is unique (no duplicate days counted).
5. It falls on a valid EGX weekday (Sun-Thu).

## 3. WHY 3 ENTRIES != 3 DAYS
The file `paper_trading_journal.json` contains 3 trade entries.
**However:**
- A trade entry is a single prediction/signal.
- Multiple signals can happen on the same day.
- A signal entry does **NOT** mean the entire daily pipeline (data fetch -> inference -> ranking -> risk gates -> telemetry) completed successfully without errors.
- Therefore, the journal is NOT the authoritative session counter. `SessionManager` is.

## 4. HISTORY CLASSIFICATION
- **Trade ID `TMGH.CA_2026-08-06` (Date: 2026-08-06):** INDIVIDUAL TRADE SIGNAL. Status: COMPLETED.
- **Trade ID `FWRY.CA_2026-08-06` (Date: 2026-08-06):** INDIVIDUAL TRADE SIGNAL. Status: COMPLETED.
- **Trade ID `MASR.CA_2026-08-13` (Date: 2026-08-13):** INDIVIDUAL TRADE SIGNAL. Status: PENDING.

## 5. GITHUB CONSISTENCY
Running locally, via headless, or via GitHub Actions triggers `SessionManager`. 
If GitHub retries the same day, `SessionManager` checks the `market_date` and blocks duplicate completion tracking.
