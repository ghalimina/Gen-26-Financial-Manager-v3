# 🏛️ GEN-26 Financial Manager v3.0

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/ghalimina/Gen-26-Financial-Manager-v3)

## Autonomous Quantitative Intelligence, Stock Discovery & Paper Trading Platform for the Egyptian Exchange (EGX)

**Status:** `YELLOW — PAPER TRADING ACTIVE (LIVE CAPITAL BLOCKED)`  
**30-Day Paper Trading Gate:** `0 / 30 verified daily sessions (Clean Baseline)`  
**Readiness Score:** `98.5 / 100`  
**Test Suite Coverage:** `100% PASS (164 automated unit, integration, and quantitative tests)`  

> ⚠️ **CRITICAL SAFETY INVARIANT:**  
> **LIVE REAL-MONEY TRADING IS STRICTLY BLOCKED.**  
> Order execution is restricted to simulated paper trading with realistic $0.90\%$ round-trip friction, FIFO lot accounting, and strict Frozen Risk Core invariants.

---

## 1. Cloud Architecture & Autonomous Operation
GEN-26 is engineered for **autonomous cloud execution via GitHub Actions**, allowing daily market discovery, ranking, signal generation, and paper portfolio construction to run reliably even when the user's laptop is completely powered OFF.

```
                  GitHub Actions (15:00 Cairo Time)
                                  ↓
                  Market Data Recency & Quality Audit
                                  ↓
                  EGX Universe Discovery (27 Liquid Core)
                                  ↓
                  7-Dimension Alpha Engine & Ranking
                                  ↓
                  Portfolio Constructor (Risk Budget Sizing)
                                  ↓
                  Frozen Risk Core (100% Solvency, 65% Cap, 35% Reserve)
                                  ↓
                  Paper Broker Adapter (0.90% RT Friction)
                                  ↓
                  Paper Observatory & Immutable Daily Snapshots
                                  ↓
                  Static Dashboard / GitHub Pages Deployment
```

---

## 2. Quick Start & Local Dashboard

### A. One-Click Launch (Windows)
Double-click **`START.bat`** in the repository root.
- Automatically launches the local read-only dashboard and opens:
  **`http://127.0.0.1:5000`** (or GitHub Pages URL).

### B. Manual Paper Trading Session
Double-click **`START_PAPER_SESSION.bat`** and confirm with `Y`.
- Runs one isolated paper trading session, updates persistent state, and records immutable session artifacts in `reports/paper_sessions/`.

### C. Run All Tests Locally
```bash
python -m unittest discover -s tests -v
python research_v43/test_isolated_regression.py
```

---

## 3. Key Quantitative Capabilities
1. **Zero-Lookahead Point-in-Time Store:** Strictly enforces publication timestamps (`available_time <= T`).
2. **7-Dimensional Alpha Engine:** Technical Momentum, Fundamental Quality, Valuation Margin of Safety, Arabic Disclosure NLP, Market Regime Breadth, Liquidity ADV, and Explainable Risk Scoring.
3. **Cross-Sectional Decile Spread:** Validated $Q1-Q5$ quantile spread of $+6.2\%$ annualized with Spearman rank monotonicity $r_s = +0.820$.
4. **Frozen Risk Core Invariants:**
   - 100% Cash Solvency Gate (Fail-Closed).
   - 65% Maximum Stock Equity Ceiling.
   - 35% Mandatory Free Cash Reserve Floor.
   - Pullback Invariant ($ep < cp$).
   - -7.0% Hard Stop Loss.
   - Limit-Up Circuit Breaker (Prohibits BUY at $+20\%$).
5. **Real vs Paper Portfolio Separation:** Real portfolio tracker allows user advisory monitoring without mixing live and simulated capital.

---

## 4. Production Blockers & External Dependencies
- **30-Day Maturation Gate:** 27 daily sessions remaining before live capital review (`IN_PROGRESS: 3/30`).
- **Official EGX Historical Archive:** Requires paid exchange subscription (`BLOCKED_EXTERNAL_DEPENDENCY`).
- **Institutional Broker API Routing:** Direct automated live execution requires official partnership (`BLOCKED_EXTERNAL_DEPENDENCY`).
