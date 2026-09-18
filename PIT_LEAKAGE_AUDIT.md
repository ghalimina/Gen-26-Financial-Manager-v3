# PIT_LEAKAGE_AUDIT.md
# Comprehensive Point-in-Time (PIT) & Lookahead Leakage Audit
**System:** GEN-26 Quantitative Financial Architecture  
**Audit Scope:** Rigorous Identification, Forensic Proof & Resolution of Temporal Leakages  
**Audit Date:** 2026-09-17  
**Audit Context:** `RESEARCH_ONLY / SHADOW_ONLY / NON_PRODUCTION / NO_LIVE_TRADING / NO_ML`  

---

## 1. Summary of Confirmed Temporal Leakages

| Leakage ID | Defect Title | Component & File Location | Mechanism of Leakage | Affected Sample | Numerical Impact | Current Remediation Status |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: |
| **LEAK-01** | Forward Return Target in Market Breadth | `research_v43/engines/phase2_market_regime.py:265` | `df["Pos_1D"] = (df["Fwd_Ret_1D"] > 0)` | Dev (2020–2024), Val (2025), Holdout (2026) | Inflated Dev Net PF from $2.000$ to $2.605$; Val Net PF from $1.454$ to $1.592$ | Fixed in Phase 2.75 / Clean Room (`Ret_1D_Trailing`) |
| **LEAK-02** | Forward Benchmark Index Accumulation | `research_v43/engines/phase2_market_regime.py:161-164` | `daily_ret = panel.groupby(...)["Fwd_Ret_1D"].mean()` | Dev (2020–2024), Val (2025), Holdout (2026) | Leaked future returns into benchmark moving averages and regime classification | Fixed in Phase 2.75 / Clean Room (`Ret_1D_Trailing`) |
| **LEAK-03** | Full-Dataset Feature Normalization | `research_v43/engines/t6_ml_model_layer.py` | `RobustScaler.fit()` across entire 2020–2026 matrix | Dev and Val folds | Leaked future median and IQR into early training folds | Fixed in commit `312b55b` (fit on `X_train` only) |
| **LEAK-04** | Prior Holdout Evaluation Before Freeze | `research_v43/reports/phase_2_annual_breakdown.csv:54` | 2026 evaluated on 2026-08-18 before lock on 2026-08-19 | 2026 Holdout | Candidate selected with prior knowledge of $PF = 3.084$ in 2026 | Re-classified 2026 as contaminated selection |

---

## 2. Forensic Breakdown of Each Confirmed Leakage

### LEAK-01: Forward Target Lookahead in Market Breadth (`Breadth_AdvanceRatio`)
* **Exact File:** `research_v43/engines/phase2_market_regime.py`
* **Exact Function:** `build_breadth(panel: pd.DataFrame) -> pd.DataFrame`
* **Exact Code Fragment (line 265):**
  ```python
  df["Pos_1D"] = (df["Fwd_Ret_1D"] > 0).astype(int)  # today's return
  ```
* **Why it Leaks:**
  Variable `Fwd_Ret_1D` is defined as `c.shift(-1) / c - 1.0`, which represents the return from today's close to tomorrow's close ($t \to t+1$). The comment states `# today's return`, but the code executes tomorrow's return. At decision date $t$, this gives the model future knowledge of whether equities will advance tomorrow.
* **Which Dates are Affected:**
  Every single trading session from `2020-01-02` to `2026-08-16` across all 27 stocks.
* **Affected Partitions:**
  Development (2020–2024), Validation (2025), and Holdout (2026).
* **Numerical Impact:**
  * Development (2020–2024): Inflated Net Profit Factor from **$2.000$** to **$2.605$** ($+0.605$ artificial lift) and Win Rate from $52.76\%$ to $57.23\%$.
  * Validation (2025): Inflated Net Profit Factor from **$1.454$** to **$1.592$** ($+0.138$ lift) and Win Rate from $55.71\%$ to $57.78\%$.
* **Correct Implementation:**
  ```python
  df["Ret_1D_Trailing"] = c.pct_change(1)
  df["Pos_1D_CLEAN"] = (df["Ret_1D_Trailing"] > 0).astype(int)
  ```
* **Test Proving Correction:**
  `scratch/clean_room/forensic_engine_audit.py:run_forensic_reconstruction()` asserts zero correlation between signal timestamp $t$ and forward returns $t \to t+1$.

---

### LEAK-02: Forward Benchmark Accumulation Leakage (`BM_Index`)
* **Exact File:** `research_v43/engines/phase2_market_regime.py`
* **Exact Function:** `build_regime(panel: pd.DataFrame) -> pd.DataFrame`
* **Exact Code Fragment (lines 161–164):**
  ```python
  daily_ret = panel.groupby(panel.index)["Fwd_Ret_1D"].mean()
  bm_idx = (1.0 + daily_ret).cumprod() * 1000.0
  ```
* **Why it Leaks:**
  The benchmark index was constructed by compounding forward 1-day returns (`Fwd_Ret_1D`). Consequently, the calculated benchmark index level at date $t$ reflects the price level of date $t+1$. All derived indicators (`BM_Mom20D`, `SMA50`, `SMA200`, and regime filters `R_BULL`, `R_BEAR`) shifted one day into the future.
* **Which Dates are Affected:**
  All sessions from `2020-01-02` to `2026-08-16`.
* **Affected Partitions:**
  Development, Validation, and Holdout.
* **Numerical Impact:**
  Contaminated regime flags `R_BULL` and `R_BEAR`, enabling the strategy to preemptively exit ahead of market corrections or enter prior to market rallies.
* **Correct Implementation:**
  ```python
  daily_ret_trailing = panel.groupby(panel.index)["Ret_1D_Trailing"].mean()
  bm_idx_clean = (1.0 + daily_ret_trailing.fillna(0)).cumprod() * 1000.0
  ```
* **Test Proving Correction:**
  `forensic_engine_audit.py` builds `BM_Index_Trailing` strictly from trailing returns.

---

### LEAK-03: Full-Dataset Normalization Leakage (`RobustScaler`)
* **Exact File:** `research_v43/engines/t6_ml_model_layer.py`
* **Exact Function:** `train_walk_forward()`
* **Exact Code Fragment:**
  ```python
  scaler = RobustScaler()
  X_scaled = scaler.fit_transform(X)  # Fitted across entire 2020-2026 panel prior to split
  ```
* **Why it Leaks:**
  Fitting a feature scaler across the entire historical dataset exposes the training folds to distributional parameters (median and interquartile range) calculated from future test and holdout data.
* **Which Dates are Affected:**
  Training folds 1 through 4 (2020–2024).
* **Affected Partitions:**
  Development and Validation.
* **Numerical Impact:**
  Artificially boosted Tier 6 machine learning out-of-sample prediction accuracy.
* **Correct Implementation (Resolved in commit `312b55b`):**
  ```python
  scaler = RobustScaler()
  X_train_scaled = scaler.fit_transform(X_train)
  X_test_scaled = scaler.transform(X_test)
  ```
* **Status:** Fully resolved and verified in Tier 6 research changelog.

---

### LEAK-04: Prior Holdout Evaluation Before Freezing
* **Exact File:** `research_v43/reports/phase_2_annual_breakdown.csv` line 54
* **Date of Event:** 2026-08-18 (Commit `39844ee`)
* **Evidence:**
  ```csv
  2026,P2_Breadth_Momentum,577,61.35,3.084,4.13,1.195
  ```
* **Why it Leaks:**
  On August 18, 2026, Phase 2 walk-forward Fold 5 evaluated market data through July 19, 2026, publishing performance breakdowns for 2026. On August 19, 2026, `phase_2_locked_specification.md` retroactively declared 2026 as a "sealed out-of-sample holdout". The candidate signal (`P2_Breadth_Momentum`) was selected as the winner *after* observing that it achieved an extraordinary Profit Factor of $3.084$ in 2026.
* **Which Dates are Affected:**
  `2026-01-01` to `2026-07-19`.
* **Affected Partitions:**
  2026 Holdout Reserve.
* **Numerical Impact:**
  Invalidates 2026 as an untainted blind holdout.
* **Correct Action:**
  Formally classify 2026 as an observed validation extension. Reserve Q4 2026 and 2027 as the true unexamined holdout dataset.

---
*Point-in-Time audit verified: all leakages cataloged with exact file lines and clean-room replacements.*
