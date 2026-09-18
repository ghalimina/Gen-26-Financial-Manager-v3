# MAIN_RUNTIME_FORENSIC_AUDIT.md
# Comprehensive Main Runtime, Production Core & Synthetic Validator Forensic Audit
**System:** GEN-26 Quantitative Financial Architecture  
**Target Branch:** `main` (Active Working Tree)  
**Components Audited:** `core/`, `dashboard/`, `data/gen26_production.db`, `tests/test_hardening_phase_2.py`  
**Audit Date:** 2026-09-17  
**Audit Context:** `RESEARCH_ONLY / SHADOW_ONLY / NON_PRODUCTION / NO_LIVE_TRADING / NO_ML`  

---

## 1. Executive Summary of Main Runtime State

An exhaustive audit of the active `main` branch reveals a critical dichotomy between:
1. **The Live Production Core & Risk Perimeter (`dashboard/app.py`, `core/frozen_invariants.py`):**
   * Real, robust, functional Flask server and user interface.
   * Production safety invariants (Cash Gate $\ge 10\%$, Allocation Cap $\le 65\%$, Max Position Size $\le 10\%$) are **100% active, genuine, and strictly enforced**.
2. **The Internal Quantitative Validation & Calibration Modules (`core/`):**
   * Severely compromised by **synthetic random generation**, **hardcoded static dictionaries**, and **nominal share-price heuristics**.
   * Tests pass fraudulently against mock constants rather than empirical market data.
   * Driven by **historical bar starvation** in `data/gen26_production.db` (which contains only 2 months of bars).

---

## 2. In-Depth Component Audit of Active Defects

### A. Synthetic Random Backtest in `core/edge_verifier.py`
* **File & Lines:** `core/edge_verifier.py:52-67`
* **Defect Type:** `FAKE_EMPIRICAL_VALIDATION` / `CODE_BUG`
* **Actual Code:**
  ```python
  np.random.seed(42)
  n_periods = lookback_days
  n_stocks = 25  # Core active liquid cross-section

  # Generate realistic empirical price paths with regime shifts & fat tails
  drift = 0.0008  # ~20% annual EGX equity drift
  volatility = 0.018  # ~28% annual volatility
  daily_returns = np.random.normal(drift, volatility, (n_periods, n_stocks))
  ```
* **Forensic Evidence:**
  The class `StatisticalEdgeVerifier` claims to run a "vectorized 1-year historical backtest across active EGX liquid equities" and outputs `data/realized_statistical_edge.json`. In reality, it runs zero database queries against historical market data. It simulates Gaussian noise using `np.random.normal`, artfully injected with random jumps, and calculates Hit Rate and Profit Factor from these fake numbers.
* **Impact:** The system issues official audit certifications ("Realized Edge Verified") based entirely on random numbers with seed 42.

---

### B. Hardcoded Parameter Stability in `core/statistical_validator.py`
* **File & Lines:** `core/statistical_validator.py:129-137`
* **Defect Type:** `HARDCODED_STATIC_DICTIONARY`
* **Actual Code:**
  ```python
  # Empirical stability results across lookback neighborhood
  neighborhood_pf = {
      14: 1.980,
      16: 2.050,
      18: 2.110,
      20: base_pf,
      22: 2.125,
      24: 2.080,
      26: 2.020
  }
  ```
* **Forensic Evidence:**
  The method `evaluate_parameter_neighborhood_stability()` purports to evaluate strategy sensitivity in a $\pm 30\%$ neighborhood around the optimal lookback. Instead of performing a parametric sweep over historical bars, it returns a static hardcoded dictionary.
* **Impact:** Unit test `tests/test_statistical_validation.py` passes fraudulently against static mock values. The system fails to alert the user if a parameter spike is unstable in real market data.

---

### C. Inverted Sample Size in Deflated Sharpe Ratio (DSR)
* **File & Lines:** `core/statistical_validator.py:51-52`
* **Defect Type:** `STATISTICAL_FORMULA_ERROR`
* **Actual Code:**
  ```python
  # Standard error of Sharpe with skewness and kurtosis correction (Mertens, 2002)
  # Annualized observations count (years)
  years = T / 252.0 if T >= 252 else T
  variance_sr = (1.0 - skewness * sr + ((kurtosis - 1.0) / 4.0) * (sr ** 2)) / max(1.0, years)
  ```
* **Forensic Evidence:**
  In Mertens (2002) and Bailey & Lopez de Prado (2014), the asymptotic variance of the estimated Sharpe ratio is scaled by the total sample observation count $T$:
  $$V[\widehat{SR}] = \frac{1}{T} \left(1 - \gamma_3 SR + \frac{\gamma_4 - 1}{4} SR^2\right)$$
  The code divides by `years = T / 252.0` instead of $T$, inflating the variance estimator by a factor of $252$, and suppressing the resulting $z$-statistic by $\sqrt{252} \approx 15.87\times$.

---

### D. Nominal Share Price Used as Fundamental Alpha
* **File & Lines:** `core/weight_calibrator.py:202`
* **Defect Type:** `METHODOLOGICAL_LIMITATION` / `HEURISTIC_BIAS`
* **Actual Code:**
  ```python
  # Factor 2: Fund
  fund_s = float(np.clip(60.0 + (closes[i] / 10.0), 30.0, 90.0))
  ```
* **Forensic Evidence:**
  In extracting historical factors for SLSQP Sharpe optimization, the "Fundamental Factor" is computed directly from the nominal share price. A stock trading at $750$ EGP (`ORAS.CA`) receives the maximum fundamental score ($90.0$), while a stock trading at $7$ EGP (`RAYA.CA`) receives a depressed score ($60.7$).
* **Impact:** Arbitrarily biases portfolio weighting toward high-nominal-share-price companies, regardless of earnings, book value, or financial health.

---

### E. Synthetic 100 EGP Reference in Market Breadth
* **File & Lines:** `core/market_breadth_engine.py:49-68`
* **Defect Type:** `HEURISTIC_BIAS` / `SYNTHETIC_FALLBACK`
* **Actual Code:**
  ```python
  ref_base = 100.0
  if p > ref_base:
      # Bullish price
      prev = ref_base
      ma20 = ref_base * 1.05
  elif p < ref_base * 0.5:
      # Deep crash price
      prev = ref_base
      ma20 = ref_base
  ```
* **Forensic Evidence:**
  When evaluating prices without explicit historical bars, the breadth engine compares nominal stock prices against an arbitrary reference of $100.0$ EGP. Stocks with nominal prices under $50$ EGP (such as `COMI.CA` at 40 EGP in 2020, or `FWRY.CA` at 6 EGP) are classified as "deep crash" stocks.
* **Impact:** Distorts Advance/Decline ratios in production paper trading.

---

### F. Historical Bar Starvation in `data/gen26_production.db`
* **File:** `data/gen26_production.db` (Table: `historical_daily_bars`)
* **Forensic Evidence:**
  ```sql
  SELECT COUNT(*), MIN(market_date), MAX(market_date), COUNT(DISTINCT ticker) 
  FROM historical_daily_bars;
  -- Result: (8199, '2026-07-12', '2026-09-10', 189)
  ```
* **Finding:** Contains only 8,199 daily bars spanning 2 months. Required 200-day moving averages (`SMA_200`) and 252-day lookbacks fail to resolve, triggering silent fallbacks to the synthetic Gaussian models in `weight_calibrator` and `edge_verifier`.

---

## 3. Production Safety Perimeter Verification

While the internal validation engines contain synthetic mocks, the **production risk gates remain 100% genuine, uncompromised, and active**:

| Safety Gate | Enforcing Module | Threshold | Verification Status | Audit Finding |
| :--- | :--- | :---: | :---: | :--- |
| **Cash Gate Floor** | `core/frozen_invariants.py:15`<br>`dashboard/app.py` | $\ge 10.0\%$ | **VERIFIED ACTIVE** | Orders that would reduce cash below 10% are strictly blocked. |
| **Allocation Cap** | `core/frozen_invariants.py:18`<br>`dashboard/app.py` | $\le 65.0\%$ | **VERIFIED ACTIVE** | Total portfolio equity exposure cannot exceed 65%. |
| **Max Position Limit** | `core/frozen_invariants.py:21` | $\le 10.0\%$ | **VERIFIED ACTIVE** | Single constituent exposure cannot exceed 10% of total capital. |
| **Live Execution Firewall** | `core/live_execution_firewall.py` | `LIVE_TRADING_ENABLED = False` | **VERIFIED ACTIVE** | Hardcoded block prevents any live order dispatch to brokers. |

---
*Main runtime audit verified against active working tree source code.*
