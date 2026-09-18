# CONFIRMED_FIX_PLAN.md
# Comprehensive Quantitative Fix & Remediation Plan
**System:** GEN-26 Quantitative Financial Architecture  
**Execution Context:** Isolated Audit/Fix Branch (`audit/forensic-remediation-v1`)  
**Audit Date:** 2026-09-17  
**Policy Enforcement:** `RESEARCH_ONLY / SHADOW_ONLY / NON_PRODUCTION / NO_LIVE_TRADING / NO_ML`  

---

## 1. Classification of Findings by Action Category

Every finding from [FINDINGS_REGISTER.md](file:///c:/Users/Administrator/Desktop/New%20folder/FINDINGS_REGISTER.md) is categorized under formal remediation criteria:

### Category A: Confirmed Active Defects (Eligible for Direct Code Remediation)
* **F-04:** Synthetic random backtest in `core/edge_verifier.py`.
* **F-05:** Hardcoded parameter stability dictionary in `core/statistical_validator.py`.
* **F-06:** Nominal share price used as fundamental alpha score in `core/weight_calibrator.py`.
* **F-07:** Synthetic nominal 100 EGP reference price in `core/market_breadth_engine.py`.
* **F-14:** Production SQLite database historical bar starvation in `data/gen26_production.db`.
* **F-17:** Inverted observation count denominator in DSR Mertens formula in `core/statistical_validator.py`.

### Category B: Historical Defects Already Fixed (Require Verification & Regression Tests)
* **F-01 / F-02:** Market breadth and benchmark forward lookahead leakage (Fixed in Phase 2.75).
* **F-09:** Sequential compounding drawdown distortion (Fixed in Phase 2.5 MTM portfolio).
* **F-21:** Full-sample `RobustScaler` normalization leakage (Fixed in Tier 6 QA sweep).
* **F-22:** Duplicate accounting disclosures collision (Fixed in Tier 3 QA sweep).
* **F-23:** Stock split corporate action data quality penalty (Fixed in Tier 0 QA sweep).

### Category C: Methodological Limitations (Documented, Not Tuned or Forced to Pass)
* **F-10:** Severe zero-volume illiquidity in `ORAS.CA` (96.32% zero-volume days).
* **F-11:** Unresolved survivorship bias across historical 27-stock blue-chip universe.
* **F-12:** Disjoint execution offset degradation on isolated 2025 validation year ($PF = 1.591$).
* **F-15:** Overnight entry gap between Close $t$ and Open $t+1$ (Mean $-0.0033\%$, variance $\pm 8.69\%$).
* **F-16:** Overlapping 20-day trade return serial correlation and trade-level Sharpe annualization.
* **F-18:** Truncation of Ezz Steel Rebar (`ESRS.CA`) ending on March 13, 2025.

### Category D: Unsupported Claims & Documentation Errors (Corrected via Official Amendments)
* **F-03:** Prior 2026 holdout exposure before locking (Retroactive freeze declaration invalid).
* **F-08:** Gross vs Net Profit Factor reporting discrepancy in baseline documentation ($2.138$ vs $1.821$).
* **F-11:** False historical claim that 8 delisted stocks proved zero survivorship bias.

### Category E: Informational Architecture & System Invariants (Preserved as Intact)
* **F-13:** Segregation of research pipeline on `research/full-feature-rebuild-v43` branch.
* **F-19:** Closing auction cross-price boundary variance in Egyptian Exchange clearing.
* **F-20:** Unused / incomplete research sandbox draft (`research_v5/`).
* **F-24:** Production core safety invariants (Cash Gate $\ge 10\%$, Allocation Cap $\le 65\%$, Max Pos $\le 10\%$) preserved.

---

## 2. Itemized Code Fix Specifications (Category A Defects)

### Fix 1: Empirical Vectorized Backtest in `core/edge_verifier.py`
* **Finding ID:** **`F-04`**
* **Root Cause:** Placeholder implementation using `np.random.normal(0.0008, 0.018)` with `np.random.seed(42)` instead of historical market data.
* **File Changed:** `core/edge_verifier.py`
* **Function Changed:** `StatisticalEdgeVerifier.run_vectorized_backtest()`
* **Before Behavior:** Generates 250 rows of synthetic Gaussian numbers and reports fake empirical edge metrics.
* **Correct Behavior:** Queries real daily bars from `historical_daily_bars` in `data/gen26_production.db` (or parquet fallback), calculates realized multi-factor composite scores, and executes vectorized 10-day forward return evaluation across active constituents.
* **Test Added:** `tests/test_forensic_audit_remediation.py:test_empirical_edge_verifier_queries_real_bars`
* **Research Impact:** Reports genuine realized hit rate and Profit Factor based on authentic EGX market history.
* **Historical Invalidation:** Invalidates all prior runs of `realized_statistical_edge.json`.

---

### Fix 2: Empirical Parameter Stability Sweep in `core/statistical_validator.py`
* **Finding ID:** **`F-05`**
* **Root Cause:** Placeholder returning hardcoded dictionary `{14: 1.980, 16: 2.050, ..., 26: 2.020}`.
* **File Changed:** `core/statistical_validator.py`
* **Function Changed:** `StatisticalValidator.evaluate_parameter_neighborhood_stability()`
* **Before Behavior:** Always returns identical static dictionary regardless of strategy or market data.
* **Correct Behavior:** Accepts an empirical return panel or trade series, executes a parameter sweep across $k \in [14, 26]$ around base lookback $k=20$, and dynamically computes empirical mean PF, coefficient of variation, and plateau stability.
* **Test Added:** `tests/test_forensic_audit_remediation.py:test_parameter_stability_is_empirical`
* **Research Impact:** Replaces fake unit test passes with real sensitivity verification.

---

### Fix 3: DSR Mertens Variance Denominator Correction
* **Finding ID:** **`F-17`**
* **Root Cause:** Divides variance by `years = T / 252` instead of total observations $T$.
* **File Changed:** `core/statistical_validator.py`
* **Function Changed:** `StatisticalValidator.compute_deflated_sharpe_ratio()`
* **Before Behavior:**
  ```python
  years = T / 252.0 if T >= 252 else T
  variance_sr = (1.0 - skewness * sr + ((kurtosis - 1.0) / 4.0) * (sr ** 2)) / max(1.0, years)
  ```
* **Correct Behavior:**
  ```python
  variance_sr = (1.0 - skewness * sr + ((kurtosis - 1.0) / 4.0) * (sr ** 2)) / max(1.0, float(T))
  ```
* **Test Added:** `tests/test_forensic_audit_remediation.py:test_deflated_sharpe_ratio_mertens_formula`
* **Research Impact:** Restores mathematical alignment with Bailey & Lopez de Prado (2014) standard error formula.

---

### Fix 4: Price-Invariant Fundamental Scoring in `core/weight_calibrator.py`
* **Finding ID:** **`F-06`**
* **Root Cause:** Line 202 scores fundamentals using nominal share price: `fund_s = float(np.clip(60.0 + (closes[i] / 10.0), 30.0, 90.0))`.
* **File Changed:** `core/weight_calibrator.py`
* **Function Changed:** `WeightCalibrator._extract_historical_factor_matrix()`
* **Before Behavior:** High nominal share price receives high fundamental score.
* **Correct Behavior:** Computes normalized valuation / return ratio (or standardized price momentum and low-volatility score) that is strictly invariant to nominal share splits.
* **Test Added:** `tests/test_forensic_audit_remediation.py:test_weight_calibrator_split_invariance`
* **Research Impact:** Eliminates arbitrary factor bias toward high-nominal-price equities.

---

### Fix 5: Trailing Percentage Breadth in `core/market_breadth_engine.py`
* **Finding ID:** **`F-07`**
* **Root Cause:** Compares nominal stock price against static reference `ref_base = 100.0` EGP.
* **File Changed:** `core/market_breadth_engine.py`
* **Function Changed:** `MarketBreadthEngine.compute_market_breadth()`
* **Before Behavior:** Classifies any stock under 50 EGP as "deep crash".
* **Correct Behavior:** Computes Advance/Decline ratio from percentage price changes relative to previous day close (`prices_dict[t] / prev_close - 1.0`).
* **Test Added:** `tests/test_forensic_audit_remediation.py:test_market_breadth_percentage_basis`
* **Research Impact:** Production paper breadth accurately reflects market cross-section.

---

### Fix 6: SQLite Historical Bar Hydration
* **Finding ID:** **`F-14`**
* **Root Cause:** Table `historical_daily_bars` in `data/gen26_production.db` contains only 2 months of bars (July–Sept 2026).
* **Script Created:** `scripts/hydrate_historical_daily_bars.py`
* **Target Database:** `data/gen26_production.db`
* **Action:** Populates `historical_daily_bars` with full 5-year historical clean bars (2020–2026) from clean Parquet files.
* **Database State After Fix:** Table expands from 8,199 rows to $> 42,000$ rows.
* **Research Impact:** Eliminates historical starvation; engines can calculate 200-day moving averages without triggering synthetic fallbacks.

---

## 3. Phased Execution Roadmap

1. **Step 1: Database Hydration (Non-Destructive Table Insertion)**
   * Execute `scripts/hydrate_historical_daily_bars.py`.
   * Assert row count $> 40,000$ spanning 2020–2026.
2. **Step 2: Core Validator & Calculation Remediation**
   * Apply Fixes 1, 2, 3, 4, 5 to `core/` files.
3. **Step 3: Regression Test Suite Implementation & Verification**
   * Create and execute `tests/test_forensic_audit_remediation.py`.
   * Assert all 5 remediation tests pass.
4. **Step 4: Rerun and Generate Comparison CSV**
   * Rerun edge verification and generate `reports/forensic_metrics_before_after.csv`.
5. **Step 5: Master Test Suite Pass Verification**
   * Run fast CI test suite (`scripts/run_ci_fast_tests.py`) to confirm zero regressions across existing functionality.

---
*Confirmed fix plan formulated: targeted, minimal, test-backed, and protective of production safety.*
