# PIT_LOOKAHEAD_FORENSIC.md
# Exhaustive Point-in-Time (PIT) & Lookahead Forensic Audit
**System:** GEN-26 Quantitative Financial Architecture  
**Audit Scope:** Every Feature, Target, Benchmark, Scaling Operation & Transformation across the Repository  
**Classification Mandate:** Strict Temporal Safety Verification  
**Audit Context:** `RESEARCH_ONLY / SHADOW_ONLY / NON_PRODUCTION / NO_LIVE_TRADING / NO_ML`

---

## 1. Feature-by-Feature Temporal Safety Registry

Every mathematical feature and transformation in the repository has been inspected at the code level and classified into one of four strict categories:
1. **`STRICTLY_TRAILING_PIT_SAFE`**: Uses only past information $\le t$. Fully safe for backtesting.
2. **`FORWARD_LOOKING_TARGET`**: Legitimate forward target label (e.g. $t \to t+H$). Safe ONLY as target; illegal as feature.
3. **`LOOKAHEAD_LEAKAGE_CONFIRMED`**: Contaminated feature accessing future data $> t$. Catastrophically distorts backtest validity.
4. **`POTENTIALLY_CONTAMINATED`**: Feature or operation exhibiting lookahead risk, full-sample leakage, or unverified indexing.

| Feature / Transformation Name | Mathematical Formula / Implementation | Classification | Source File & Location | Temporal Status & Audit Notes |
| :--- | :--- | :---: | :--- | :--- |
| `Adj Close (t)` | Sourced from backward-adjusted daily bar | **PIT_SAFE** | `research_v43/data/*.parquet` | Backward-adjusted historical close as of close of session $t$. |
| `Ret_1D_Trailing` | `Adj Close[t] / Adj Close[t-1] - 1.0` | **PIT_SAFE** | `phase1_cost_aware_baselines.py:75` | Strict trailing 1-session return. |
| `Mom_5D`, `Mom_10D`, `Mom_20D` | `Adj Close[t] / Adj Close[t-k] - 1.0` | **PIT_SAFE** | `phase1_cost_aware_baselines.py:78` | Strict trailing momentum using shift($+k$). |
| `SMA_20`, `SMA_50`, `SMA_200` | `c.rolling(W).mean()` | **PIT_SAFE** | `phase1_cost_aware_baselines.py:84` | Strict trailing moving average over past $W$ sessions. |
| `EMA_12`, `EMA_26` | `c.ewm(span=W, adjust=False).mean()` | **PIT_SAFE** | `phase1_cost_aware_baselines.py:86` | Strict trailing recursive exponential average. |
| `RSI_14` | Rolling 14-day gains / losses | **PIT_SAFE** | `phase1_cost_aware_baselines.py:90` | Standard Wilder trailing RSI calculation. |
| `RVol_20D` | `c.pct_change().rolling(20).std() * sqrt(252)` | **PIT_SAFE** | `phase1_cost_aware_baselines.py:94` | Trailing 20-day historical realized volatility. |
| `ATR_Pct` | `rolling_mean(True_Range, 20) / c * 100` | **PIT_SAFE** | `phase1_cost_aware_baselines.py:98` | Trailing 20-day Average True Range percentage. |
| `AvgTradedVal_20D` | `(c * v).rolling(20).mean() / 1e6` | **PIT_SAFE** | `phase1_cost_aware_baselines.py:102` | Trailing 20-day turnover proxy in millions EGP. |
| `Slip_Est` | `(ATR_Pct * 0.0012 * sqrt(1 / ATV)).clip(...)` | **PIT_SAFE** | `phase1_cost_aware_baselines.py:105` | Trailing dynamic slippage estimate. |
| `Cost_Model_RT` | `BASE_FEE_RT + 2.0 * Slip_Est` | **PIT_SAFE** | `phase1_cost_aware_baselines.py:106` | Trailing estimated round-trip transaction friction. |
| `BL3_Momentum` | `Mom_20D > 0 & Adj Close > SMA_50` | **PIT_SAFE** | `phase1_cost_aware_baselines.py:270` | Pure rule-based trailing momentum filter. |
| `Breadth_AboveSMA20` | `mean(c_i > SMA20_i)` across universe | **PIT_SAFE** | `phase2_market_regime.py:263` | Cross-sectional mean of trailing moving average status. |
| `Breadth_AboveSMA50` | `mean(c_i > SMA50_i)` across universe | **PIT_SAFE** | `phase2_market_regime.py:264` | Cross-sectional mean of trailing moving average status. |
| `Breadth_AdvanceRatio_BUGGY` | `mean(Fwd_Ret_1D > 0)` across universe | **LOOKAHEAD_LEAKAGE_CONFIRMED** | `phase2_market_regime.py:265` | **CRITICAL LEAK.** Slices forward return from $t \to t+1$. |
| `Breadth_Osc10D_BUGGY` | `rolling(10) - rolling(30)` of Buggy Breadth | **LOOKAHEAD_LEAKAGE_CONFIRMED** | `phase2_market_regime.py:275` | Inherits 24-hour forward lookahead from AdvanceRatio. |
| `Breadth_AdvanceRatio_CLEAN` | `mean(Ret_1D_Trailing > 0)` across universe | **PIT_SAFE** | `phase275_forensic_reset.py:262` | Clean-room reconstruction using trailing daily returns. |
| `Breadth_Osc10D_CLEAN` | `rolling(10) - rolling(30)` of Clean Breadth | **PIT_SAFE** | `phase275_forensic_reset.py:270` | Trailing momentum of cross-sectional market breadth. |
| `BM_Index (Phase 2 Buggy)` | `(1 + mean(Fwd_Ret_1D)).cumprod() * 1000` | **LOOKAHEAD_LEAKAGE_CONFIRMED** | `phase2_market_regime.py:164` | Benchmark index advances 1 day ahead of real calendar time. |
| `BM_Mom20D (Phase 2 Buggy)` | `BM_Index / BM_Index.shift(20) - 1.0` | **LOOKAHEAD_LEAKAGE_CONFIRMED** | `phase2_market_regime.py:167` | Computed on lookahead-contaminated benchmark index. |
| `R_BULL (Phase 2 Buggy)` | `BM_Mom20D > 0.02 & BM_Idx > SMA50...` | **LOOKAHEAD_LEAKAGE_CONFIRMED** | `phase2_market_regime.py:214` | Regime classification observes tomorrow's market return. |
| `R_BULL (Clean)` | Same formula using `Ret_1D_Trailing` index | **PIT_SAFE** | Clean Room Reconstruction | Fully trailing point-in-time safe regime classification. |
| `P2_Breadth_Momentum (Buggy)` | `BL3 & AdvRatio_Buggy > 0.5 & Osc > 0` | **LOOKAHEAD_LEAKAGE_CONFIRMED** | `phase2_market_regime.py:345` | Primary signal candidate corrupted by lookahead breadth. |
| `P2_Breadth_Momentum (Clean)` | `BL3 & AdvRatio_Clean > 0.5 & Osc > 0` | **PIT_SAFE** | `phase275_forensic_reset.py:320` | Cleaned signal evaluated in Phase 2.75 ($PF = 1.454$). |
| `P2_BullBreadth` | `BL3 & R_BULL & AboveSMA20 > 0.55` | **CONTAMINATED IN P2 / SAFE IN P2.75** | `phase2_market_regime.py:352` | Contaminated in P2 via `R_BULL`; safe when cleaned. |
| `Fwd_Ret_1D` | `c.shift(-1) / c - 1.0` | **FORWARD_TARGET** | `research_v43/data/*.parquet` | Target label for 1-day holding horizon. |
| `Fwd_Ret_20D` | `c.shift(-20) / c - 1.0` | **FORWARD_TARGET** | `research_v43/data/*.parquet` | Primary 20-day target label for strategy evaluation. |
| `Fwd_Ret_60D` | `c.shift(-60) / c - 1.0` | **FORWARD_TARGET** | `research_v43/data/*.parquet` | Long-term target label. |
| `RobustScaler (Tier 6 Buggy)` | Fit on full feature matrix $X$ | **LOOKAHEAD_LEAKAGE_CONFIRMED** | `BUG-03` (Changelog / Tier 6) | Fit on full sample across train and test folds. Fixed in QA. |
| `RobustScaler (Tier 6 Clean)` | Fit on `X_train`, transform `X_test` | **PIT_SAFE** | `t6_ml_model_layer.py:180` | Walk-forward expanding scaler; zero test leakage. |
| `High/Low Volatility Quantiles`| `BM_Vol.rolling(252).quantile(0.80)` | **PIT_SAFE** | `phase2_market_regime.py:228` | Uses trailing rolling 252-day expanding/rolling quantile. |
| `Universe Membership` | Static 27-stock constituent list | **SURVIVORSHIP_BIASED** | `historical_universe.csv` | Uses 2026 survivors throughout 2020–2025 backtest. |

---

## 2. In-Depth Forensic Investigation of Confirmed Leakages

### LEAK-01: Forward Target Leakage in Market Breadth (`Breadth_AdvanceRatio`)
1. **File Path:** `research_v43/engines/phase2_market_regime.py`
2. **Function:** `build_breadth(panel: pd.DataFrame) -> pd.DataFrame`
3. **Relevant Code Lines (lines 255–267):**
   ```python
   for tkr, df in panel.groupby("Ticker"):
       df = df.copy().sort_index()
       c = df["Adj Close"]
       df["Above_SMA20"] = (c > c.rolling(20).mean()).astype(int)
       df["Above_SMA50"] = (c > c.rolling(50).mean()).astype(int)
       df["Pos_1D"] = (df["Fwd_Ret_1D"] > 0).astype(int)  # today's return <--- CRITICAL BUG
       df["New_20D_High"] = (c >= c.rolling(20).max()).astype(int)
       df["New_20D_Low"] = (c <= c.rolling(20).min()).astype(int)
       out.append(df[["Above_SMA20", "Above_SMA50", "Pos_1D", "New_20D_High", "New_20D_Low"]])

   per_stock = pd.concat(out).sort_index()
   breadth = per_stock.groupby(per_stock.index).mean()
   breadth.columns = ["Breadth_AboveSMA20", "Breadth_AboveSMA50", "Breadth_AdvanceRatio", ...]
   ```
4. **Exact Leakage Mechanism:**
   The developer added a comment `# today's return` next to `df["Fwd_Ret_1D"] > 0`, erroneously believing that `Fwd_Ret_1D` represented the return of day $t$. In reality, `Fwd_Ret_1D` was created in `t0_data_foundation.py` as `c.shift(-1) / c - 1.0`, which is the return from day $t \to t+1$. By averaging this across the universe on day $t$, `Breadth_AdvanceRatio` measured what percentage of stocks were going to rise *tomorrow*.
5. **Minimal Reproducible Demonstration:**
   ```python
   # Signal at date t reads tomorrow's return
   signal_today = breadth["Breadth_AdvanceRatio"].loc["2024-01-10"]
   # signal_today is perfectly correlated with average return on 2024-01-11
   actual_tomorrow_return = panel.loc["2024-01-10", "Fwd_Ret_1D"].mean()
   # Demonstration: Correlation between signal_today and tomorrow's market direction is positive by construction
   ```
6. **Affected Metrics:**
   * Phase 2 Development Profit Factor artificially inflated from **`2.000`** to **`2.605`** ($+0.605$).
   * Phase 2 Validation Profit Factor artificially inflated from **`1.454`** to **`1.592`** ($+0.138$).
   * Phase 2 Trade Count reduced from **`3,838`** to **`3,477`** (omitting false breakouts that fell next day).
7. **Status:** **REAL BUG (CONFIRMED & REPRODUCED)**.
8. **Correction Implemented in Phase 2.75:**
   ```python
   df["Pos_1D"] = (df["Ret_1D_Trailing"] > 0).astype(int)
   ```

---

### LEAK-02: Forward Benchmark Accumulation & Regime Contamination
1. **File Path:** `research_v43/engines/phase2_market_regime.py`
2. **Function:** `build_regime(panel: pd.DataFrame) -> pd.DataFrame`
3. **Relevant Code Lines (lines 160–165):**
   ```python
   # Equal-weight daily return = cross-sectional mean of daily returns
   daily_ret = panel.groupby(panel.index)["Fwd_Ret_1D"].mean()  # <--- CRITICAL BUG

   # Build index level from daily returns (base 1000)
   bm_idx = (1.0 + daily_ret).cumprod() * 1000.0
   ```
4. **Exact Leakage Mechanism:**
   The cross-sectional benchmark index `BM_Index` was constructed by accumulating `Fwd_Ret_1D`. Consequently, `BM_Index` on date $t$ reflects the price level of date $t+1$. Any moving average or momentum indicator derived from `BM_Index` (`BM_Mom20D`, `SMA50`, `SMA200`) and the resulting regime states (`R_BULL`, `R_BEAR`, `R_CRISIS`) had advance knowledge of tomorrow's market return.
5. **Affected Metrics:**
   * All regime-conditioned signals (`P2_Bull_Momentum`, `P2_BullBreadth`, `P2_NotBear_Momentum`) had lookahead information in their regime flags during Phase 2.
6. **Status:** **REAL BUG (CONFIRMED & REPRODUCED)**.
7. **Correction:**
   Construct the benchmark index using trailing daily returns:
   ```python
   daily_ret_trailing = panel.groupby(panel.index)["Ret_1D_Trailing"].mean()
   bm_idx = (1.0 + daily_ret_trailing.fillna(0)).cumprod() * 1000.0
   ```

---

### LEAK-03: Full-Dataset Normalization Leakage (`BUG-03`)
1. **File Path:** `research_v43/engines/t6_ml_model_layer.py`
2. **Function:** Initial implementation of Tier 6 Machine Learning Pipeline.
3. **Leakage Mechanism:**
   `RobustScaler` was initially fitted across the entire historical feature matrix $X$ (2020–2026) prior to splitting into walk-forward training and test folds:
   ```python
   # Flawed code in initial Tier 6 sweep:
   X_scaled = scaler.fit_transform(X)  # Leaked test fold distribution into training fold
   ```
4. **Impact:** Allowed test set medians and interquartile ranges (IQR) to inform training set feature representations.
5. **Status:** **ALREADY FIXED (CONFIRMED)**.
   The changelog and active code in `t6_ml_model_layer.py` show that `scaler.fit_transform(X_train)` is now strictly fitted on training folds only, and applied to test folds via `scaler.transform(X_test)`.

---

### LEAK-04: Prior Holdout Exposure (Phase 2 Holdout Pre-Contamination)
1. **File Path:** `research_v43/reports/phase_2_annual_breakdown.csv` and `research_v43/reports/phase_2_regime_fold_detail.csv`
2. **Leakage Mechanism:**
   In Phase 2 (dated 2026-08-18), the 5-fold expanding walk-forward evaluated Fold 5 from **2025-07-09 to 2026-07-19**. The output files explicitly contained 2026 performance numbers:
   `2026,P2_Breadth_Momentum,577,61.35,3.084,4.13,1.195`
   Only on **2026-08-19** (the following day) did `phase_2_locked_specification.md` declare that 2026 was a "sealed final holdout that must NOT be evaluated until Phase 6".
3. **Impact:**
   The 2026 holdout was not a blind, untouched dataset. The candidate signal (`P2_Breadth_Momentum`) was selected as the winner after the research team observed that it achieved an exceptional Profit Factor of $3.084$ in 2026.
4. **Status:** **CRITICAL METHODOLOGICAL LEAKAGE (CONFIRMED)**.
5. **Correction Protocol:**
   The 2026 calendar period cannot be used as an untainted blind holdout for `P2_Breadth_Momentum` or any candidate evaluated in Phase 2. A true blind holdout requires data generated strictly after August 20, 2026, or a completely unexamined asset class.

---

## 3. Detailed Audit of Other Transformation Types

* **Shift Operations:**
  All feature shifts in `phase1_cost_aware_baselines.py` (`shift(1)`, `shift(5)`, `shift(20)`) use positive integers, moving past data forward in time. This is 100% PIT-safe. Target labels use negative shifts (`shift(-20)`), which is correct for labels.
* **Rolling & Expanding Windows:**
  All rolling windows specify explicit window sizes without `center=True`. Slicing is strictly backward-looking.
* **Groupby & Resampling:**
  `groupby("Ticker")` operations are applied before rolling indicators, preventing cross-sectional contamination between stocks during indicator calculation.
* **Joins & Merges:**
  Cross-sectional breadth and regime indices are merged into stock panels using `how="left"` on the DatetimeIndex, ensuring alignment to date $t$.
* **Imputation & Missing Values:**
  Missing prices are forward-filled with a strict limit (`ffill(limit=5)`). No backward filling (`bfill`) exists in the feature calculation pipeline.

---
*Point-in-Time safety audit completed with line-by-line evidence and reproducible verification.*
