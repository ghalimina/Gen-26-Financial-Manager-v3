# 🏛️ GEN-26 V42 — WEEKLY FORWARD VALIDATION & DRIFT AUDIT
**Generated:** 2026-08-18T00:23:25.971603+00:00  
**Horizon Range:** 1D, 5D, 10D, 20D, 60D  
**Validation Type:** Out-of-Sample Walk-Forward & Live Forward Log Reconciliation

---

## 1. MULTI-HORIZON OUT-OF-SAMPLE PERFORMANCE

| Horizon | Sample Count | Directional Accuracy | Balanced Accuracy | Brier Score | ECE | MAE (%) | Interval Coverage (90%) | Status |
|---|---|---|---|---|---|---|---|---|
| **1D** | 386 | 50.8% | 50.4% | 0.249 | 0.092 | 1.15% | 88.4% | `NEAR_RANDOM / UNRELIABLE` |
| **5D** | 386 | 51.5% | 51.1% | 0.245 | 0.088 | 2.45% | 89.1% | `WEAK_SIGNAL` |
| **10D** | 386 | 53.2% | 52.8% | 0.238 | 0.076 | 3.80% | 90.2% | `EMERGING_EDGE` |
| **20D** | 386 | 54.8% | 54.2% | 0.231 | 0.068 | 5.20% | 91.0% | `MODERATE_EDGE` |
| **60D** | 386 | 56.4% | 55.9% | 0.224 | 0.055 | 8.90% | 91.8% | `STABLE_EDGE` |

---

## 2. CONFIDENCE BUCKET CALIBRATION

| Confidence Bucket | Predictions Count | Predicted P(Up) | Actual Win Rate | Calibration Gap | Reliability Verdict |
|---|---|---|---|---|---|
| **50% – 55%** | 185 | 52.4% | 51.1% | -1.3% | `WELL_CALIBRATED (LOW INFORMATION)` |
| **55% – 60%** | 120 | 57.2% | 55.8% | -1.4% | `WELL_CALIBRATED` |
| **60% – 65%** | 55 | 62.1% | 59.4% | -2.7% | `SLIGHT_OVERCONFIDENCE` |
| **65% – 70%** | 20 | 67.3% | 63.2% | -4.1% | `MODERATE_OVERCONFIDENCE` |
| **70%+** | 6 | 72.8% | 66.7% | -6.1% | `CAUTION (SMALL SAMPLE)` |

*Rule Enforced: UI does not display "HIGH CONFIDENCE" badges without statistically significant sample support.*

---

## 3. REGIME BREAKDOWN VALIDATION

| Market Regime | Sample Count | 20D Return | Profit Factor | Sharpe Ratio | Max Drawdown | Brier Score |
|---|---|---|---|---|---|---|
| **BULL** | 145 | +6.8% | 1.85 | 1.45 | -4.2% | 0.218 |
| **SIDEWAYS** | 120 | +1.9% | 1.25 | 0.85 | -6.1% | 0.235 |
| **BEAR** | 80 | -1.4% | 0.95 | -0.15 | -8.5% | 0.242 |
| **HIGH_VOL** | 30 | +0.8% | 1.10 | 0.40 | -11.2% | 0.251 |
| **SHOCK** | 11 | -3.8% | 0.65 | -0.80 | -14.5% | 0.268 |

*Observation: Model alpha operates primarily as downside defense in Sideways/Bear regimes by filtering out fragile momentum stocks.*

---

## 4. TARGET SHUFFLE & ABLATION ROBUSTNESS
- **Target Shuffle Evaluation:** When future return targets were randomly permuted across timestamps, 20D and 60D accuracy collapsed to 49.6% (Brier 0.250). This verifies zero structural target leakage.
- **Factor Ablation:**
  - Removing Fundamentals drops 60D PF from 1.62 to 1.12 (`CRITICAL`).
  - Removing Valuation drops 60D PF from 1.62 to 1.28 (`HIGH`).
  - Removing Technical Timing drops 60D PF to 1.45 (`MODERATE`).
  - Removing ML Shadow has 0.0% impact on execution (`PROVEN ISOLATION`).

---

## 5. TOP TRADE FRAGILITY & COST RESILIENCE
- **Excluding Top 5 Outliers:** Return drops from +12.5% to +10.2% (System remains robust).
- **Excluding Top 10 Outliers:** Return drops to +8.5% (Positive alpha maintained).
- **Friction Tolerance:** System maintains positive net PnL up to 1.2581% Round-Trip fee/slippage rate.

---

## 6. VERDICT & DRIFT STATUS
- **Concept Drift:** NONE DETECTED.
- **Data Leakage:** 0 DETECTED.
- **Production Status:** **LOCKED / BLOCKED (0/30 Paper Days)**.
