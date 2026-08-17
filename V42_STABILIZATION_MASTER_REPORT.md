# 🏛️ GEN-26 V42 — STABILIZATION + VALIDATION MASTER REPORT
**Generated:** 2026-08-17T02:07:27.436712Z
**Current Git SHA:** `2d1db2f023fd642736759aaa94e27ebe715fd788`

## 1. BASELINE STATUS
| Component | Status | Evidence |
|---|---|---|
| **V4.1 Engine** | STABLE / FROZEN | No code changed in V4.1 files |
| **V42 Engine** | RESEARCH / SHADOW | `V42_STABILIZATION_BASELINE.json` |
| **ML Models** | SHADOW | `ML_MODE = "SHADOW"` |
| **Data Mode** | YFINANCE PROXY | Delayed/EOD, clearly labeled |

---

## 2. BREAK-EVEN TRUTH
**Q1. What is the Break-even per-side?**
**Answer:** `0.6290%` (implied by backtest raw ledger).

**Q2. What is the Break-even round-trip?**
**Answer:** `1.2581%`.

**Q3. Why were previous reports contradictory?**
**Answer:** One report calculated the true *Round-Trip* value (1.258%), while another erroneously doubled it again, arriving at 2.5161% (doubling the round-trip instead of doubling the per-side). The ledger strictly verifies `1.2581%` as the Round-Trip break-even.

---

## 3. PAPER TRADING TRUTH
**Q4. How many Paper Days are actually complete?**
**Answer:** `0` (Zero).

**Q5. Are the 3 entries = 3 days?**
**Answer:** **NO**. The 3 entries in `paper_trading_journal.json` are individual trade signals. They do not represent a fully completed daily pipeline run (which requires checking data, running all engines, generating telemetry, and finishing without errors via `SessionManager`).

---

## 4. MASTER RANKER WEIGHTS
**Q6. Are Master Stock Ranker weights optimized?**
**Answer:** **NO**. They are labeled `HAND_SET_DEFAULTS` (Fund=30%, Val=20%, Tech=15%, Liq=10%, Sec=10%, Mac=10%, ML=5%).
The simulated OOS test showed hand-set (5.1% return) slightly beating Equal Weight (4.2%), but we explicitly **refuse to tune or optimize** these weights on the holdout to prevent overfitting.

---

## 5. HORIZON TRUTH
**Q7. Does 120D exist?**
**Answer:** **NOT IMPLEMENTED**. The code strictly supports 1D, 5D, 10D, 20D, and 60D. 120D is marked as `RESEARCH REQUIRED` and is not exposed.

---

## 6. VALIDATION & EDGE (OOS)
**Q8. Does V42 outperform baselines out-of-sample?**
**Answer:** In the walk-forward simulation, V42 demonstrated a slight predictive edge over simple baselines (e.g., 60D Model Return > Baseline Return), but **Calibration remains marginal** for short horizons (<5D).

**Q9. Is there a true Predictive Edge?**
**Answer:** **TENTATIVE YES**, but only for horizons >= 10D. Short-term (1D/5D) accuracy is near-random (50-52%), while 60D pushes towards 55% with acceptable Brier scores. Target Shuffle testing successfully collapsed this edge to baseline, proving the model learned a weak signal, not a hardcoded bias.

---

## 7. RISK & SAFETY
**Q10. Are there execution risks introduced by V42?**
**Answer:** **ZERO**. V42 is entirely isolated in `research_v42/`. It does not feed signals to the execution engine. V4.1's Cash Gate and 65% Allocation rules remain authoritative and untouched.

---

## 8. GITHUB AUTOMATION & CI
- **Daily Engine:** Active via `.github/workflows/v42_daily_engine.yml`.
- **Idempotency:** `SessionManager` explicitly blocks duplicate session creation on the same calendar date.
- **Failure Safety:** If V42 crashes, the GitHub action proceeds (Job 2 is independent of Job 1 paper execution).

---

## 9. CURRENT ISSUES & DEPRECATIONS
- **DEPRECATED:** `system_full_audit.py`, `daily_paper_trade_logger.py`, LSTM models. Left in tree for reference but no longer called by the main CI pipeline.
- **ISSUE (LOW):** YFinance proxy data is delayed. Real-time inference relies on stale data. Marked heavily in UI.
- **ISSUE (CRITICAL BLOCKER):** Production Gate requires 30 complete Paper Days. We have 0.

---

## 10. FINAL TRUTH TABLE

| Item | Current Truth | Evidence | Status |
|---|---|---|---|
| **Break-even (Round)** | 1.2581% | V42_BREAK_EVEN_FINAL.csv | VERIFIED |
| **Paper Days** | 0 Complete (Need 30) | authoritative_paper_sessions.json | BLOCKED |
| **Ranker Weights** | HAND_SET_DEFAULTS | V42_WEIGHT_AUDIT.md | ACCEPTED |
| **120D Horizon** | NOT IMPLEMENTED | multi_horizon_forecast_engine.py | CORRECT |
| **OOS Edge** | Marginal on >10D | V42_OOS_RESULTS.csv | EXPERIMENTAL |
| **Shuffle Test** | Edge Collapsed | V42_SHUFFLE_RESULTS.csv | PASSED |
| **Ablation Test** | Fund/Val are core | V42_ABLATION_RESULTS.csv | PASSED |
| **Calibration** | Poor on <5D | V42_CALIBRATION_RESULTS.csv | MARGINAL |
| **Cost Sensitivity** | Profitable up to 1.25% | V42_COST_RESULTS.csv | PASSED |
| **Monte Carlo** | Med DD: -8.5% | V42_MONTE_CARLO_RESULTS.csv | PASSED |
| **GitHub CI** | Re-enabled, Safe | v42_daily_engine.yml | ACTIVE |
| **Security** | No Leakage/Secrets | Code Review | PASSED |
| **Regression** | V4.1 isolated | ast.parse & Github jobs | PASSED |

---
**VERDICT:** V42 Architecture is CLEAN and SAFE. Validation proves weak but real edge at longer horizons. **Do NOT promote to production.** Await 30 full paper trading days.
