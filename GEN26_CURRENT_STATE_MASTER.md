# 🏛️ GEN-26 CURRENT STATE MASTER TRUTH
> المرجع الوحيد للحالة الفعلية للنظام بعيداً عن أي ادعاءات تاريخية.

### FINAL STATUS
SYSTEM STATE: STABLE (READ-ONLY SNAPSHOT)
GIT SHA: b3c7e8b
PAPER: 0 / 30
ML: ACTIVE (SHADOWED FOR EXITS, INFLUENCES ENTRY CONFIDENCE)
DATA MODE: DELAYED YFINANCE (PROXY)
65% GATE: VERIFIED (app.py)
EXIT: VERIFIED INDEPENDENT
ENTRY: VERIFIED PULLBACK
DECISION OBJECT: VERIFIED SINGLE SOURCE
GITHUB: LOCAL ONLY / NO ACTIONS DETECTED IN LOG
CRITICAL ISSUES: NONE FOUND IN CORE LOGIC
PRODUCTION: BLOCKED (NEEDS 30 PAPER DAYS)

---

### 1. Current Git Commit
- Branch: main
- SHA: b3c7e8b
- Dirty: True

### 2. Current Architecture & Active Path
`GitHub Action / UI` ➔ `market_data_provider.py (YFinance delayed proxy)` ➔ `egx_cib_lstm_engine.py / egx_screener.py` ➔ `app.py (Risk & Cash Gates)` ➔ `decision_builder.py (Single Decision Object)` ➔ `session_manager.py (Paper Trading)` ➔ `telemetry_tracker.py` ➔ `UI / CSV`

### 3. Current Data
- Provider: YFinance (Proxy)
- Mode: DELAYED / EOD

### 4. Current Risk & Portfolio
- 65% Allocation Gate is hardcoded in app.py logic and prevents new BUYs.
- Cash Gate operates correctly and subtracts T+2 settlements.

### 5. Current Entry & Exit
- Entry requires a Pullback condition.
- Exit is purely objective (Stop / Target) and independent of ML shadow interference.

### 6. Current Paper Trading
- Days Completed: 0
- Journal: authoritative_paper_sessions.json / paper_trading_journal.json

### 7. Current Decision Object
- Fully localized in `decision_builder.py` -> `build_final_decision_objects`.
- Ensures single source of truth across UI, CSV, and Paper Simulator.

### 8. Historical Claims vs Current Reality
| Item | Historical Claim | Current Reality | Evidence | Status |
|---|---|---|---|---|
| Break-even | 0.00% | 1.258% | Walk-Forward Raw Ledger | REFUTED |
| Exit | ML Dependent | Objective | decision_builder.py | REFUTED |
| Realtime | Live | Delayed Proxy | market_data_provider | PARTIALLY VERIFIED |
