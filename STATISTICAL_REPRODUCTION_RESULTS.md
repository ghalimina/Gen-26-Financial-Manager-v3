# STATISTICAL_REPRODUCTION_RESULTS.md
# Independent Clean-Room Quantitative Reproduction Results
**System:** GEN-26 Quantitative Financial Architecture  
**Execution Environment:** Isolated Clean-Room (`scratch/clean_room/forensic_engine_audit.py`)  
**Data Evaluated:** 27 Clean Parquet Files (42,641 stock-days, 2020-01-02 to 2026-08-16)  
**Execution Date:** 2026-09-17  
**Audit Context:** `RESEARCH_ONLY / SHADOW_ONLY / NON_PRODUCTION / NO_LIVE_TRADING / NO_ML`  

---

## 1. Master Strategy Reproduction Matrix

Below are the exact metrics recalculated using autonomous clean-room reconstruction across Development, Validation, and Holdout partitions:

| Partition Split | Strategy Signal Tested | Trade Count ($N$) | Win Rate (%) | Gross Profit Factor | True Net Profit Factor | Mean Gross (%) | Mean Net (%) | Annualized Sharpe ($\sqrt{252/20}$) | Max DD Sequential Artifact (%) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Development (2020–2024)** | **`BL3_Momentum_Recon`** | 14,844 | 51.35% | **`2.212`** | **`1.821`** | +3.87% | +2.97% | 0.697 | -100.0% (Artifact) |
| **Development (2020–2024)** | **`P2_Breadth_Momentum_BUGGY`** | 3,477 | 57.23% | **`3.180`** | **`2.605`** | +5.68% | +4.78% | 1.049 | -100.0% (Artifact) |
| **Development (2020–2024)** | **`P2_Breadth_Momentum_CLEAN`** | 3,838 | 52.76% | **`2.429`** | **`2.000`** | +4.37% | +3.47% | 0.763 | -100.0% (Artifact) |
| **Development (2020–2024)** | **`P2_BullBreadth_CLEAN`** | 7,444 | 53.21% | **`2.615`** | **`2.159`** | +4.85% | +3.95% | 0.850 | -100.0% (Artifact) |
| **Development (2020–2024)** | **`P2_Bull_Momentum_CLEAN`** | 9,049 | 51.46% | **`2.309`** | **`1.917`** | +4.29% | +3.39% | 0.734 | -100.0% (Artifact) |
| **Validation (2025)** | **`BL3_Momentum_Recon`** | 3,210 | 52.49% | **`1.717`** | **`1.304`** | +1.77% | +0.87% | 0.315 | -100.0% (Artifact) |
| **Validation (2025)** | **`P2_Breadth_Momentum_BUGGY`** | 694 | 57.78% | **`2.092`** | **`1.592`** | +2.27% | +1.37% | 0.465 | -100.0% (Artifact) |
| **Validation (2025)** | **`P2_Breadth_Momentum_CLEAN`** | 770 | 55.71% | **`1.924`** | **`1.454`** | +2.11% | +1.21% | 0.420 | -100.0% (Artifact) |
| **Validation (2025)** | **`P2_BullBreadth_CLEAN`** | 1,416 | 49.22% | **`1.848`** | **`1.398`** | +2.09% | +1.19% | 0.453 | -100.0% (Artifact) |
| **Validation (2025)** | **`P2_Bull_Momentum_CLEAN`** | 1,762 | 50.11% | **`1.814`** | **`1.369`** | +2.10% | +1.20% | 0.462 | -100.0% (Artifact) |
| **Holdout (2026 Observed)** | **`BL3_Momentum_Recon`** | 2,314 | 46.11% | **`2.395`** | **`1.907`** | +3.60% | +2.70% | 0.831 | -100.0% (Artifact) |
| **Holdout (2026 Observed)** | **`P2_Breadth_Momentum_BUGGY`** | 577 | 61.35% | **`3.084`** | **`2.502`** | +5.03% | +4.13% | 1.196 | -100.0% (Artifact) |
| **Holdout (2026 Observed)** | **`P2_Breadth_Momentum_CLEAN`** | 606 | 59.24% | **`2.697`** | **`2.185`** | +4.48% | +3.58% | 1.013 | -100.0% (Artifact) |

---

## 2. Disjoint Offset Analysis (Untouched 2025 Validation Year)

To test sensitivity to execution date and eliminate overlapping trade bias, the 2025 validation year was sliced into 20 genuinely non-overlapping calendar offsets (sampling every 20th trading day for offset $k \in [0, 19]$):

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                         2025 ISOLATED DISJOINT CALENDAR OFFSETS (CLEAN SIGNAL)                   │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Total Distinct Offsets Evaluated │ 20 non-overlapping calendar slices                            │
│ Median Net Profit Factor         │ 1.591 (Substantially below baseline bar of 2.138)             │
│ Offsets with Net PF > 1.0        │ 18 / 20 (90.0% of offsets are profitable)                     │
│ Offsets Beating Baseline Bar     │ 5 / 20 (Only 25.0% of offsets exceed the PF 2.138 hurdle)     │
│ Minimum Offset Net PF            │ 0.680 (Offset 14 suffered net losses)                         │
│ Maximum Offset Net PF            │ 3.420 (Offset 3 captured top trending breakouts)              │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

**Forensic Finding:** While the signal generates positive expected return across 90% of offsets, **75% of non-overlapping execution paths fail to reach the baseline hurdle bar of $PF = 2.138$**. This proves that the claim of "100% of offsets passed" in Phase 2.5 relied on pooling with the massive 2022 currency devaluation profits, masking weakness in the clean validation year.

---

## 3. Statistical Hypothesis Testing & Resampling

### A. Newey-West HAC Test (Validation 2025, Clean Signal)
* **Sample Size ($N$):** 770 trade records across 56 dates.
* **Mean Net Return ($\mu_{net}$):** $+1.21\%$ ($+0.0121$).
* **HAC Standard Error ($L=20$):** $0.4218\%$ ($0.004218$).
* **HAC $t$-statistic:** **`2.857`**.
* **HAC $p$-value:** **`0.0043`** ($p < 0.01$).
* **Statistical Conclusion:** The mean net return is statistically significantly greater than zero after accounting for 20-day temporal serial correlation.

### B. Stationary Block Bootstrap (Block Size = 20, Resamples = 2,000)
* **Median Net Profit Factor:** **`1.440`**.
* **95% Confidence Interval for Net PF:** **`[1.106, 1.887]`**.
* **Mean Net Return 95% CI:** **`[+0.33%, +1.94%]`**.
* **Bootstrap Conclusion:** The lower bound of the 95% confidence interval ($1.106 > 1.0$) confirms true positive expectancy, but the upper bound ($1.887 < 2.138$) demonstrates that the strategy cannot reliably clear the historical baseline bar.

---
*Clean-room reproductions executed and verified on active workspace datasets.*
