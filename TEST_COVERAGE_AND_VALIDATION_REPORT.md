# TEST_COVERAGE_AND_VALIDATION_REPORT.md
# Comprehensive Test Suite, Coverage & Forensic Gap Analysis Report
**System:** GEN-26 Quantitative Financial Architecture  
**Test Suite Audited:** `tests/` (112 test modules), `scripts/run_ci_fast_tests.py`, `.github/workflows/`  
**Audit Date:** 2026-09-17  
**Audit Context:** `RESEARCH_ONLY / SHADOW_ONLY / NON_PRODUCTION / NO_LIVE_TRADING / NO_ML`  

---

## 1. Executive Summary of Test Battery

The repository maintains an extensive test battery of **112 test modules** in `tests/`. However, the forensic audit reveals that high test passing rates currently mask **severe validation blind spots and synthetic mocking**:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                CURRENT TEST BATTERY BREAKDOWN                                    │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Total Test Modules in tests/     │ 112 test files                                                │
│ Fast CI STLC Battery             │ 10 test suites executing via scripts/run_ci_fast_tests.py     │
│ Production Safety Invariant Tests│ 100% PASSING (Cash Gate, Allocation Cap, Max Position Size)   │
│ Synthetic Mock Tests             │ tests/test_hardening_phase_2.py passes against np.random.normal│
│ Hardcoded Dict Tests             │ tests/test_statistical_validation.py tests static dictionary │
│ Quantitative Leakage Tests       │ COMPLETELY MISSING prior to clean-room forensic suite         │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Test Coverage & Gap Analysis Across Required Categories

| Test Category | Target Invariant to Verify | Current Status in Code | Forensic Finding & Vulnerability | Remediation Test Required |
| :--- | :--- | :---: | :--- | :--- |
| **Data Integrity Tests** | Zero duplicate dates, monotonic calendar sorting, valid OHLC ($H \ge L, H \ge C, L \le C$). | `PARTIALLY COVERED` | `tests/test_price_anomalies.py` tests live prices, but ignores historical Parquet files (`ORAS.CA` 96.3% zero volume, `ESRS.CA` truncation). | Automated census test asserting $Volume > 0$, valid OHLC, and reporting stock continuity. |
| **PIT Leakage Tests** | Current signal state at $t$ cannot have correlation with $Close[t+1]$ or $Fwd\_Ret\_1D$. | `PREVIOUSLY MISSING` | No test in `tests/` checked whether `Breadth_AdvanceRatio` accessed future returns. | Regression test asserting that replacing future prices with random noise does NOT change signal at $t$. |
| **Timing & Entry Tests** | Signal at Close $t$ enters at Open $t+1$; overnight gap is explicitly modeled. | `PREVIOUSLY MISSING` | System assumes instantaneous Close $t$ fill without testing Open $t+1$ tracking error. | Dual-target unit test asserting tracking error between Close-to-Close and Open-to-Close. |
| **Accounting & Cost Tests**| Gross and Net PF differ by exact fee schedule; no sequential drawdown compounding. | `MISLEADING` | `tests/test_statistical_validation.py` tests sequential compounding without verifying MTM daily equity. | Portfolio equity test verifying daily Mark-to-Market P&L under 10% slot cap and 65% exposure limit. |
| **Statistical Validity** | DSR divides by sample size $T$; Newey-West HAC accounts for MA(19) overlap. | `ACTIVE DEFECT` | Tests pass against inverted Mertens formula (`years = T / 252`) and hardcoded dictionary. | Benchmark test verifying DSR against Bailey & Lopez de Prado (2014) reference values. |
| **Runtime Authenticity** | Zero synthetic random numbers (`np.random.normal`) in production validation engines. | `COMPROMISED` | `tests/test_hardening_phase_2.py` explicitly tests and validates `np.random.normal` execution! | Negative test asserting zero usage of `np.random.seed(42)` in production edge verification. |
| **Production Safety Gates**| Cash Gate ($\ge 10\%$), Allocation Cap ($\le 65\%$), Max Pos ($\le 10\%$). | `FULLY VERIFIED` | `tests/test_institutional_closure_suite.py` enforces strict firewall invariants. | Maintain existing safety test battery. |

---

## 3. Specifications for Remediation Test Battery (`tests/test_forensic_audit_remediation.py`)

To guarantee that code corrections permanently eliminate defects without regressions, the following test suite is specified for implementation in the audit/fix phase:

### Test 1: `test_no_lookahead_in_market_breadth`
* **Assertion:** Compute market breadth at date $t$ using historical panel. Modify prices on date $t+1$ (e.g. inject $+50\%$ shocks). Assert that `Breadth_AdvanceRatio` and `Breadth_Osc10D` on date $t$ remain **strictly identical**.

### Test 2: `test_deflated_sharpe_ratio_mertens_formula`
* **Assertion:** Execute `compute_deflated_sharpe_ratio()` with $T = 1,000$ daily observations, $SR = 1.5$, and $N = 10$ trials. Verify that variance is scaled by $T = 1,000$ (not $T / 252 = 3.96$), and that $z$-stat matches analytical benchmark ($z \approx 4.12$).

### Test 3: `test_parameter_stability_is_empirical`
* **Assertion:** Modify underlying price returns in historical input data. Assert that `evaluate_parameter_neighborhood_stability()` returns dynamically changed values rather than the static hardcoded dictionary.

### Test 4: `test_weight_calibrator_split_invariance`
* **Assertion:** Execute `_extract_historical_factor_matrix()` on a stock. Apply an artificial 10:1 stock split to closing prices. Assert that the resulting fundamental score does not drop from $90$ to $60$.

### Test 5: `test_empirical_edge_verifier_queries_real_bars`
* **Assertion:** Verify that `StatisticalEdgeVerifier.run_vectorized_backtest()` executes SQL queries against `historical_daily_bars` in SQLite rather than generating Gaussian noise.

---
*Test coverage audit completed: gaps identified and regression test battery specified.*
