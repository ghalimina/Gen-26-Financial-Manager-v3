# CORRECTIVE_ACTION_PLAN.md
# Comprehensive Quantitative Corrective Action & Remediation Plan
**System:** GEN-26 Quantitative Financial Architecture  
**Scope:** Remediation of Confirmed Defects, Leakages, and Architectural Divergence  
**Policy Enforcement:** Strict Non-Production / Research-Only Sandbox / Zero ML / Production Core Protected  
**Audit Context:** `RESEARCH_ONLY / SHADOW_ONLY / NON_PRODUCTION / NO_LIVE_TRADING / NO_ML`

---

## 1. Remediation Governance & Safety Principles

To maintain absolute safety and protect production integrity, this corrective plan strictly adheres to the following governance rules:
1. **Zero Production Modification Without Prior Authorization:**
   Production logic (`dashboard/app.py`, `core/frozen_invariants.py`, Cash Gate, 65% Allocation Cap, and live state) must remain **100% untouched**.
2. **No Silent Modification of Locked Definitions:**
   Any change to a frozen research definition (e.g. invalidating the August 19 locked specification or updating baseline hurdles) must be explicitly approved by the repository owner before being codified.
3. **No Optimization Against Validation or Holdout:**
   No parameter tuning, threshold shifting, or feature searching on the 2025 Validation or 2026 Holdout periods is permitted.
4. **No Machine Learning:**
   Tier 6 ML models remain strictly disabled in research and restricted to shadow advisory mode.
5. **Preservation of Audit Trails:**
   Historical reports must never be deleted or modified. All corrected runs must be published as independent before/after companion artifacts.

---

## 2. Prioritized Corrective Action Matrix

| Action ID | Defect Addressed | Problem Summary & Evidence | Proposed Technical Correction | Target Files & Locations | Production Risk | Validation & Regression Test Required | Authorization Required? |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- | :---: |
| **CAP-01** | **F-01 / F-02**<br>Breadth & Benchmark Forward Lookahead | `Breadth_AdvanceRatio` and `BM_Index` calculated from `Fwd_Ret_1D`, accessing tomorrow's return at date $t$. | Formally invalidate the August 19 locked specification. Enforce `Ret_1D_Trailing` for all breadth and benchmark calculations. | `research_v43/reports/phase_2_locked_specification.md`<br>`research_v43/engines/phase2_market_regime.py` | **NONE**<br>*(Research Only)* | Run `scratch/clean_room/forensic_engine_audit.py`. Assert zero correlation between signal state at $t$ and $Fwd\_Ret\_1D$. | **YES**<br>*(Requires explicit approval to invalidate locked spec)* |
| **CAP-02** | **F-04**<br>Synthetic Random Backtest in Production Engine | `StatisticalEdgeVerifier` runs `np.random.normal` (seed 42) on fake data, falsely certifying empirical edge. | Replace random array generation with real vectorized backtesting over historical bars stored in SQLite or Parquet. | `core/edge_verifier.py`<br>`tests/test_hardening_phase_2.py` | **LOW**<br>*(Protected by feature flag)* | Unit test verifying that `run_vectorized_backtest()` queries real historical bars and computes empirical hit rate. | **YES**<br>*(Production module modification proposal)* |
| **CAP-03** | **F-05**<br>Hardcoded Parameter Plateau Dictionary | `evaluate_parameter_neighborhood_stability()` returns a static hardcoded dictionary ($1.98$ to $2.138$). | Implement true parametric sweep calculating empirical Profit Factor across lookback neighborhood $k \in [14, 26]$. | `core/statistical_validator.py`<br>`tests/test_statistical_validation.py` | **LOW**<br>*(Validation utility only)* | Assert that modifying historical input data dynamically changes the returned neighborhood values. | **YES**<br>*(Production module modification proposal)* |
| **CAP-04** | **F-06**<br>Nominal Share Price Used as Fundamental Alpha | `WeightCalibrator._extract_historical_factor_matrix` computes `fund_s = 60.0 + closes[i] / 10.0`. | Replace nominal price with true fundamental accounting ratios (ROE, Net Margin) from `data/egx_fundamentals_pit.parquet`. | `core/weight_calibrator.py` | **LOW**<br>*(Internal helper)* | Assert that nominal stock splits (e.g. 10:1 split) do not alter the fundamental quality factor score. | **YES**<br>*(Production module modification proposal)* |
| **CAP-05** | **F-07**<br>Synthetic 100 EGP Reference in Market Breadth | `MarketBreadthEngine.compute_market_breadth` compares nominal stock prices against hardcoded `ref_base = 100.0` EGP. | Compute actual percentage price changes from previous official closing bars (`prices_dict[t] / prev_close - 1.0`). | `core/market_breadth_engine.py` | **LOW**<br>*(Internal calculation)* | Unit test verifying that a 7 EGP stock rising +5% is classified as an Advancer, not a "deep crash" decline. | **YES**<br>*(Production module modification proposal)* |
| **CAP-06** | **F-08**<br>Gross vs Net Profit Factor Hurdle Inconsistency | Phase 1 baseline reported Gross PF ($2.138$) as Net PF, creating an unadjusted hurdle discrepancy of $+0.317$. | Formally update baseline reference documentation to explicitly report both True Net PF ($1.821$) and Gross PF ($2.138$). | `docs/MASTER_PROJECT_INVENTORY.md`<br>`reports/phase_1_baseline_metrics.json` | **NONE**<br>*(Documentation only)* | Automated formula test asserting $\text{PF}_{\text{Net}} = \sum (r-c)^+ / |\sum (r-c)^-|$. | **NO**<br>*(Factual correction)* |
| **CAP-07** | **F-10**<br>`ORAS.CA` Zero-Volume Illiquidity Distortion | 96.32% zero-volume days in `ORAS.CA` distorts volume-weighted liquidity and slippage models. | Flag `ORAS.CA` as `ILLIQUID_OTC_BLOCK_ONLY` and apply fixed illiquidity penalty slippage cap (50 bps) instead of ATV model. | `research_v43/engines/phase1_cost_aware_baselines.py`<br>`core/liquidity_filter.py` | **NONE**<br>*(Research parameter)* | Verify that dynamic slippage estimator does not produce infinite friction or NaN on zero-volume days. | **NO**<br>*(Data sanitation)* |
| **CAP-08** | **F-11**<br>Survivorship Bias Clarification | False claim that survivorship was resolved by 8 active stocks in Phase 2.6 Part A. | Formally retract Phase 2.6 Part A and mandate that all future reports carry the permanent caveat `SURVIVORSHIP_BIAS_UNRESOLVED`. | `reports/authoritative_20_reports/02_EGX_244_UNIVERSE_CATALOG.md`<br>`MASTER_PROJECT_INVENTORY.md` | **NONE**<br>*(Documentation only)* | Audit text review confirming retraction of historical delisting resolution claim. | **NO**<br>*(Factual correction)* |
| **CAP-09** | **F-13**<br>Research Codebase Unification | Quantitative research engines and Parquet datasets are segregated on `research/full-feature-rebuild-v43`. | Merge research engines and clean Parquet data into an isolated workspace directory (`research/` or `research_v5/`) on `main`. | Workspace directory creation (`research/`) | **NONE**<br>*(Isolated from production `core/`)* | Full test run verifying that research suite executes autonomously without altering `core/` or `dashboard/`. | **YES**<br>*(Requires approval to port branch files)* |
| **CAP-10** | **F-14**<br>Production SQLite Bar Hydration | `historical_daily_bars` in `gen26_production.db` contains only 2 months of bars (July–Sept 2026). | Populate `historical_daily_bars` with full 5-year historical clean bars (2020–2026) from Parquet dataset. | `scripts/populate_real_historical_bars.py`<br>`data/gen26_production.db` | **NONE**<br>*(Read-only table expansion)* | Database query asserting $> 30,000$ historical bars spanning 2020–2026 present in SQLite. | **NO**<br>*(Maintenance script execution)* |
| **CAP-11** | **F-15**<br>Target Entry Timing Alignment | Research target evaluates $Close[t+20]/Close[t]-1$, omitting overnight execution gap to Open $t+1$. | Implement dual-target evaluation in research: Target A (Close-to-Close) and Target B (Open-to-Close). | `research_v43/engines/phase25_forensic_repair_suite.py` | **NONE**<br>*(Research only)* | Regression test comparing tracking error between Target A and Target B across all universe constituents. | **NO**<br>*(Research refinement)* |
| **CAP-12** | **F-17**<br>Deflated Sharpe Ratio Mertens Variance Inversion | Mertens variance divided by `years = T / 252` instead of observation count $T$, inflating variance by $252\times$. | Correct denominator in `core/statistical_validator.py` line 52 to use sample observation count $T$. | `core/statistical_validator.py` | **LOW**<br>*(Statistical utility)* | Unit test verifying that Mertens variance matches Bailey & Lopez de Prado (2014) benchmark test fixture. | **YES**<br>*(Production module modification proposal)* |

---

## 3. Recommended Phased Implementation Roadmap

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               PHASED REMEDIATION WORKFLOW & GATES                                │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Phase A: Formal Governance Decisions (Immediate / User Approval Required)                       │
│   ├── 1. Invalidate August 19 Locked Specification due to confirmed lookahead in Section 1.3     │
│   ├── 2. Declare BL3_Momentum (Net PF 1.821 / Gross PF 2.138) as the sole official baseline     │
│   ├── 3. Acknowledge P2_Breadth_Momentum as a rejected alpha candidate                          │
│   └── 4. Maintain 2026 Holdout as contaminated; freeze all holdout claims until 2027 data       │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Phase B: Research Sandbox Unification (Non-Production Workspace Setup)                           │
│   ├── 1. Establish isolated research package on main branch (research_clean_room/)               │
│   ├── 2. Hydrate production SQLite database with full 2020–2026 clean historical bars           │
│   └── 3. Implement dual-target entry tracking (Close-to-Close vs Open-to-Close)                   │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Phase C: Production Validator Remediation (Post-Approval Production Patching)                     │
│   ├── 1. Replace synthetic random backtest in core/edge_verifier.py with empirical engine       │
│   ├── 2. Replace hardcoded dictionary in core/statistical_validator.py with parametric sweep    │
│   ├── 3. Correct fundamental factor calculation in core/weight_calibrator.py                    │
│   ├── 4. Correct Mertens variance denominator in DSR formula                                     │
│   └── 5. Replace synthetic 100 EGP reference in core/market_breadth_engine.py                    │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Phase D: Official Phase 3 Factor Research Initialization (Strict Zero-ML Protocol)               │
│   ├── 1. Cross-sectional factor ranking only (Group A: Momentum, Group B: Value, Group C: Vol)   │
│   ├── 2. Zero threshold optimization                                                             │
│   └── 3. Evaluation strictly against BL3_Momentum baseline hurdle                                │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---
*Corrective action plan formulated under strict non-production constraints. Production changes submitted as proposals only.*
