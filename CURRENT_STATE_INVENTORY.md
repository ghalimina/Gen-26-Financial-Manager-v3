# CURRENT_STATE_INVENTORY.md
# Comprehensive Repository, Component & Execution Inventory
**System:** GEN-26 Financial Manager / Quantitative Trading Research Framework  
**Corpus / Workspace:** `c:\Users\Administrator\Desktop\New folder` (`ghalimina/Gen-26-Financial-Manager-v3`)  
**Audit Date:** 2026-09-17  
**Auditor Classification:** Senior Quantitative Research Engineer, Financial Data Engineer, Code Auditor & Statistical Validation Specialist  
**Execution Context:** `RESEARCH_ONLY / SHADOW_ONLY / NON_PRODUCTION / NO_LIVE_TRADING / NO_ML`

---

## 1. Executive Overview & Repository Reality

An exhaustive forensic audit of the repository reveals that the codebase is split across **two distinct development tracks and historical epochs**:

1. **The Historical Quantitative Research Track (`research_v43` on branch `research/full-feature-rebuild-v43`):**
   Contains the actual quantitative backtesting engines, walk-forward validation splits, Newey-West HAC calculations, disjoint offset analyzers, and the locked Phase 1, Phase 2, Phase 2.5, and Phase 2.75 research suites. This track was purged from the active `main` branch during commit `31fe1a4` (2026-08-29) and superseded by documentation summaries (`MASTER_PROJECT_INVENTORY.md`).
2. **The Production / Paper Trading & UI Track (`core/`, `dashboard/`, `reports/` on branch `main`):**
   The active working tree on `main` contains a 134-module Python application implementing a Flask dashboard, SQLite databases (`gen26_production.db`, `gen26_market.db`), simulated live paper trading, and 20 authoritative institutional markdown reports.
3. **The Incipient Sandbox Track (`research_v5/`):**
   A newly initialized, incomplete research sandbox containing only a data downloader (`research_v5/src/01_baseline_data.py`) for 10 EGX stocks.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    REPOSITORY TIMELINE & DIVERGENCE                              │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Epoch 1: Quantitative Research (August 15–20, 2026)                                              │
│   ├── Branch: research/full-feature-rebuild-v43                                                 │
│   ├── Engines: phase1_cost_aware_baselines.py, phase2_market_regime.py, phase25_validation.py     │
│   └── Artifacts: phase_1_report.md, phase_2_report.md, phase_25_report.md, phase_2_75_report.md │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Epoch 2: Branch Split & Production Overhaul (August 21–29, 2026)                                  │
│   ├── Commit 56e65fa: Added TradingView charts & research_v43 snapshot                          │
│   ├── Commit e109f6f: Production deployment with core/ engines and dashboard/app.py              │
│   └── Commit 31fe1a4: Purged research_v43 reports from main, copying MASTER_PROJECT_INVENTORY.md  │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Epoch 3: Active Working Tree on main (Current State, September 2026)                             │
│   ├── core/ (134 modules): Production application & synthetic validators                         │
│   ├── reports/authoritative_20_reports/ (20 Markdown reports)                                    │
│   └── research_v5/ (Incomplete sandbox, only 10 stocks ingested)                                 │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure & Module Responsibilities

| Directory Path | File Count | Primary Function / Scope | Research or Production | Holdout Access Risk |
| :--- | :---: | :--- | :---: | :---: |
| `core/` | 134 files | Real-time decision engine, portfolio risk management, market data fetchers, broker interface, tax calculators, synthetic validators. | Production / Paper | **HIGH** (reads current 2026 live prices) |
| `legacy_core/` | 15 files | Deprecated V1/V2 engine modules (pre-expansion algorithms). | Archive | None |
| `dashboard/` | 4 files | Flask web application (`app.py`), HTML/JS templates (`templates/index.html`). | Production / Paper UI | None |
| `data/` | 46 files | SQLite databases (`gen26_production.db`, `gen26_market.db`), JSON live cache, universe definitions, calibration weights, locked holdout reserve. | Shared Runtime State | **CRITICAL** (contains 2026 holdout reserve) |
| `reports/` | 49 files | System status JSONs, capability matrices, paper trading sessions, consolidated dossiers. | Audit Documentation | Low |
| `reports/authoritative_20_reports/` | 20 files | Synchronized architectural encyclopedia (Reports 01 to 20). | Documentation | None |
| `research_v5/` | 5 files | Newly created isolated research sandbox (Phase 0–1 only). | Research Sandbox | Low (only 10 stocks, 2020–2026) |
| `scripts/` | 48 files | Automation scripts for database hydration, price verification, report synchronization, and UI building. | DevOps / Maintenance | Moderate |
| `tests/` | 112 files | Pytest test battery covering API endpoints, core calculations, database ACID integrity, and synthetic validators. | Verification Battery | Low |
| `scratch/` | 84 files | Temporary inspection scripts, JS debuggers, and forensic clean-room extraction environment. | Research / Scratch | None |
| `.github/workflows/` | 2 files | CI/CD pipelines (`daily_pipeline.yml`, `ci_tests.yml`). | DevOps Automation | Low |
| `research_v43/` *(on research branch)* | 148 files | Historical research suite: 34 clean parquets, 7 phase engines, 81 reports/CSVs/JSONs. | Historical Research | **CONFIRMED EXPOSURE** (evaluated 2026 in Phase 2) |

---

## 3. Detailed Component Inventory

### A. Core Decision & Execution Engines (`core/`)
* [core/alpha_engine.py](file:///c:/Users/Administrator/Desktop/New%20folder/core/alpha_engine.py): Manages model registry metadata (`BL3_MOMENTUM_V1`, `P2_BREADTH_MOM_V2`, `HIST_GBM_ENSEMBLE_T6`), composite alpha weighting, and Benjamini-Hochberg FDR calculation.
* [core/multi_horizon_engine.py](file:///c:/Users/Administrator/Desktop/New%20folder/core/multi_horizon_engine.py): 60KB engine generating predictions across 1D, 5D, 10D, 20D, and 60D horizons using calibrated factor weights.
* [core/edge_verifier.py](file:///c:/Users/Administrator/Desktop/New%20folder/core/edge_verifier.py): Vectorized backtesting validator. **Auditor Note:** Generates synthetic Gaussian returns (`np.random.normal`) with seed 42 rather than backtesting historical data.
* [core/weight_calibrator.py](file:///c:/Users/Administrator/Desktop/New%20folder/core/weight_calibrator.py): SciPy SLSQP Sharpe ratio optimizer for composite factor weights. Falls back to synthetic normal variables if SQLite bar count is insufficient.
* [core/statistical_validator.py](file:///c:/Users/Administrator/Desktop/New%20folder/core/statistical_validator.py): Computes Deflated Sharpe Ratio (DSR) and parameter neighborhood stability. Contains hardcoded plateau dictionary.
* [core/market_breadth_engine.py](file:///c:/Users/Administrator/Desktop/New%20folder/core/market_breadth_engine.py): Computes Advance/Decline ratios and moving average participation. Contains synthetic fallback comparing stock price against hardcoded 100.0 EGP reference.
* [core/pit_store.py](file:///c:/Users/Administrator/Desktop/New%20folder/core/pit_store.py): In-memory point-in-time publication datastore for fundamentals.
* [core/frozen_invariants.py](file:///c:/Users/Administrator/Desktop/New%20folder/core/frozen_invariants.py): Freezes system invariants: Cash Gate (minimum 10% cash), Allocation Cap (maximum 65% invested), max position size (10%).

### B. Research Engines (Isolated on `research/full-feature-rebuild-v43`)
* `research_v43/engines/phase1_cost_aware_baselines.py`: Evaluates BL-0 through BL-5 baselines under 8 cost scenarios with 5-fold expanding walk-forward.
* `research_v43/engines/phase2_market_regime.py`: Builds market breadth, benchmark index, regime classifications, and evaluates Phase 2 candidates. **Contains lookahead leakage (`df["Fwd_Ret_1D"] > 0`).**
* `research_v43/engines/phase25_validation.py`: Evaluates locked Phase 2 candidates on 2025 untouched validation period. Discovers alpha collapse.
* `research_v43/engines/phase275_forensic_reset.py`: Root-cause forensic suite isolating lookahead leakage, compounding distortion, and devaluation concentration. Officially rejects `P2_Breadth_Momentum` as an alpha candidate.
* `research_v43/engines/phase25_forensic_repair_suite.py`: Implements clean trailing breadth (`Ret_1D_Trailing > 0`), 20 disjoint offsets, and Newey-West HAC.
* `research_v43/engines/phase26_forensic_suite.py`: Investigates survivorship bias (Part A) and fat-tail HHI profit concentration (Part B).
* `research_v43/engines/t0_data_foundation.py` to `t6_ml_model_layer.py`: Tiered feature engineering and screening battery (T0: Data, T1: Baseline, T2: Sector, T3: Fundamentals, T4: Liquidity, T5: Macro, T6: Machine Learning).

### C. Persistent Data Stores (`data/`)
* `data/gen26_production.db`: SQLite database storing historical daily bars (8,199 bars across 189 stocks, strictly limited to 2026-07-12 through 2026-09-10), real portfolio state, paper sessions, and model drift metrics.
* `data/gen26_market.db`: SQLite database storing stock universe metadata, live quotes, macro indicators, and agent council votes.
* `data/holdout_reserve_locked_20260814.json`: 33.5KB locked JSON containing daily OHLC prices for 27 stocks from May 13, 2026 to August 13, 2026.
* `data/canonical_prices_live.json`: 258KB Single Source of Truth (SSOT) live price registry for 244 EGX equities.
* `data/thndr_egx_244_universe.json`: Catalog of all 244 EGX equities categorized by liquidity tier, ISIN, and sector.
* `scratch/clean_room/research_v43/data/`: 27 clean Parquet files (2020-01-02 to 2026-08-16) comprising 42,641 stock-day records.

---

## 4. Execution Entrypoints

The repository currently exhibits multiple entrypoints across operations, testing, and research:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   SYSTEM EXECUTION ENTRYPOINTS                                  │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. PRODUCTION / PAPER TRADING RUNTIME                                                           │
│    Command: python dashboard/app.py                                                             │
│    Main File: dashboard/app.py                                                                  │
│    Imports: core.multi_horizon_engine, core.market_price_service, core.real_portfolio           │
│    Inputs: data/canonical_prices_live.json, data/gen26_production.db                            │
│    Outputs: Port 5000 HTTP endpoints (/api/overview, /api/stocks, /api/signals)                │
│    Date Range: Real-time live quotes (2026)                                                     │
│    Classification: Production / Paper Trading UI                                                │
│    Holdout Risk: HIGH (operates directly in 2026 calendar time)                                 │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. REPUTED QUANTITATIVE HARDENING TEST                                                          │
│    Command: pytest tests/test_hardening_phase_2.py -v                                           │
│    Main File: tests/test_hardening_phase_2.py                                                   │
│    Imports: core.weight_calibrator, core.edge_verifier, core.model_evaluator                    │
│    Inputs: Synthetic Gaussian random draws (seed 42)                                            │
│    Outputs: data/realized_statistical_edge.json, data/calibrated_weights.json                   │
│    Date Range: Synthetic 250 periods                                                            │
│    Classification: Mock Test Battery                                                            │
│    Holdout Risk: None (purely synthetic)                                                        │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. RESEARCH RECONSTRUCTION & VALIDATION (Clean-Room Layer)                                      │
│    Command: python scratch/clean_room/forensic_engine_audit.py                                  │
│    Main File: scratch/clean_room/forensic_engine_audit.py                                       │
│    Imports: pandas, numpy, scipy.stats                                                          │
│    Inputs: scratch/clean_room/research_v43/data/*_clean.parquet                                 │
│    Outputs: scratch/clean_room/audit_outputs/reproduction_matrix.csv                            │
│    Date Range: 2020-01-02 to 2025-12-31 (Dev + Val)                                             │
│    Classification: Research Forensic Audit                                                      │
│    Holdout Risk: NONE (2026 evaluated only in contamination audit)                              │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. DAILY CI/CD HEALTH CHECK                                                                     │
│    Command: python scripts/run_ci_fast_tests.py                                                 │
│    Main File: scripts/run_ci_fast_tests.py                                                      │
│    Imports: unittest runner                                                                     │
│    Outputs: Console STLC pass/fail summary                                                      │
│    Classification: DevOps Automation                                                            │
│    Holdout Risk: None                                                                           │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Git and Change History Forensic Timeline

Inspection of Git branches, commits, and tags reveals the exact evolution of the project:

| Date / Commit | Action / Event | Affected Component | Research & Methodological Impact | Verified Status |
| :--- | :--- | :--- | :--- | :---: |
| **2026-08-16**<br>`225506c` | Implement Tier 0 Data Foundation & Tier 1 Baseline | `research_v43/engines/t0_data_foundation.py`, `t1_cost_aware_baseline.py` | Established 27-stock panel, 0.90% RT cost model, and `BL3_Momentum` ($PF = 2.138$). | `VERIFIED` |
| **2026-08-18**<br>`39844ee` | Complete all 7 Tiers of quantitative research rebuild | `research_v43/engines/phase2_market_regime.py`, `t2`–`t6` engines | Evaluated 40 features across Tiers 2–6. Discarded Tiers 2, 3, 4. Permitted Tier 5 Macro. Shadow-only for Tier 6 ML. | `VERIFIED` |
| **2026-08-18**<br>`7da6d4a` | Phase 2 Signal Discovery reported | `research_v43/reports/phase_2_report.md` | Reported `P2_Breadth_Momentum` with $PF = 2.914$, $Sharpe = 1.034$, $N = 3,922$. Evaluated Fold 5 through 2026-07-19. | `VERIFIED LEAKAGE` |
| **2026-08-19**<br>`phase_2_locked_spec` | Freezing Phase 2 Locked Specification | `research_v43/reports/phase_2_locked_specification.md` | Encoded `Pos_1D = (Fwd_Ret_1D > 0)` directly in locked specification. Declared 2026 sealed **after** it had already been evaluated. | `CRITICAL SPEC DEFECT` |
| **2026-08-19**<br>`phase_25_report` | Phase 2.5 Validation on 2025 | `research_v43/engines/phase25_validation.py` | Signal collapsed in 2025 ($PF = 1.592 < 2.138$ baseline bar). Triggered Phase 2.75 reset protocol. | `VERIFIED COLLAPSE` |
| **2026-08-19**<br>`phase_2_75_report` | Phase 2.75 Root-Cause Forensic Reset | `research_v43/engines/phase275_forensic_reset.py` | Discovered lookahead leakage in `Breadth_AdvanceRatio`. Cleaned signal dropped to $PF = 1.454$ in 2025. **Officially rejected signal.** | `VERIFIED REJECTION` |
| **2026-08-20**<br>`phase_2_5_final_verdict` | Phase 2.5 Final Verdict Revision | `research_v43/reports/phase_2_5_final_verdict.md` | Re-evaluated clean signal with HAC ($p=0.0363$), disjoint offsets, and MTM portfolio ($CAGR = +27.69\%$). **Reversed verdict from REJECTED to CONDITIONAL.** | `VERIFIED CONTRADICTION` |
| **2026-08-20**<br>`phase_2_6` | Phase 2.6 Survivorship & Concentration Audit | `research_v43/reports/phase_2_6_survivorship_reconstruction.md` | Part A debunked (8 test stocks were active, not delisted). Part B confirmed acceptable HHI concentration (565.92). Overall gate: `CONDITIONAL`. | `VERIFIED LIMITATION` |
| **2026-08-23**<br>`56e65fa` | Merge TradingView charts & research snapshot | Root, `research_v43/` snapshot | Preserved `research_v43` snapshot before production divergence. | `VERIFIED` |
| **2026-08-23**<br>`e109f6f` | V3.0 Production Release Deployment | `core/`, `dashboard/`, `data/` | Built institutional dashboard, SQLite stores, paper trading loop. Disconnected research engines. | `VERIFIED DIVERGENCE` |
| **2026-08-29**<br>`31fe1a4` | Purge obsolete multi-phase reports from `main` | `reports/`, `research_v43/` removed from main | Removed raw research files from `main` to establish 244-universe SSoT. Left `MASTER_PROJECT_INVENTORY.md` in root. | `VERIFIED PURGE` |
| **Current**<br>`HEAD` | Multi-engine runtime with synthetic test suite | `core/`, `tests/`, `dashboard/` | Tests in `tests/test_hardening_phase_2.py` pass against synthetic random data, while production runs on live quotes. | `CURRENT REALITY` |

---

## 6. Master Component Inventory Table

| Component | Actual Path | Purpose | Imported/Executed By | Status | Authoritative? | Notes |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **Flask Dashboard App** | `dashboard/app.py` | Web interface, REST APIs (`/api/overview`, `/api/stocks`, `/api/signals`), broker firewall | Standalone entrypoint / User browser | `ACTIVE RUNTIME` | **YES (Production UI)** | Runs Flask server; enforces risk gates. |
| **Dashboard Template** | `dashboard/templates/index.html` | TradingView chart containers, Arabic/English UI, real-time tables | `dashboard/app.py` | `ACTIVE UI` | **YES** | SSoT for user interface layout. |
| **Multi-Horizon Engine** | `core/multi_horizon_engine.py` | Generates 1D, 5D, 10D, 20D, 60D forecast probabilities | `dashboard/app.py` | `ACTIVE RUNTIME` | **YES (Runtime Engine)** | 60KB core forecasting module. |
| **Statistical Edge Verifier** | `core/edge_verifier.py` | Vectorized backtest and edge validation | `tests/test_hardening_phase_2.py` | `ACTIVE DEFECT` | **NO (Synthetic Mock)** | Uses `np.random.normal` (seed 42); zero empirical market data. |
| **Statistical Validator** | `core/statistical_validator.py` | DSR, Monte Carlo drawdown, parameter plateau stability | `tests/test_statistical_validation.py` | `ACTIVE DEFECT` | **NO (Synthetic Mock)** | Hardcodes dictionary (1.98–2.138); Mertens variance denominator inverted. |
| **Weight Calibrator** | `core/weight_calibrator.py` | SLSQP Sharpe ratio optimization for alpha factor weights | `core/multi_horizon_engine.py` | `ACTIVE DEFECT` | **PARTIAL** | Line 202 scores fundamentals using nominal share price (`60 + close/10`). |
| **Market Breadth Engine** | `core/market_breadth_engine.py` | Computes Advance/Decline ratio and moving average breadth | `dashboard/app.py` | `ACTIVE DEFECT` | **PARTIAL** | Compares nominal stock prices to hardcoded `ref_base = 100.0` EGP. |
| **Frozen Invariants** | `core/frozen_invariants.py` | Production risk firewalls: Cash Gate (10%), Allocation Cap (65%), Pos Size (10%) | `dashboard/app.py`, `core/real_portfolio.py` | `ACTIVE FROZEN` | **YES (Protected SSoT)** | Core safety perimeter. Must remain untouched. |
| **Real Portfolio Manager** | `core/real_portfolio.py` | Tracks cash, active equity positions, and MTM equity | `dashboard/app.py` | `ACTIVE RUNTIME` | **YES** | Real portfolio state tracking. |
| **Direct EGX Feed Service** | `core/egx_direct_feed_service.py` | Ingests live quotes from scraping / broker endpoints | `dashboard/app.py`, background runner | `ACTIVE RUNTIME` | **YES** | Market price synchronization. |
| **Production SQLite DB** | `data/gen26_production.db` | Historical daily bars, paper trading logs, drift monitoring | `core/*`, `dashboard/app.py` | `ACTIVE RUNTIME` | **YES (Active DB)** | Contains only 8,199 bars (July–Sept 2026); lookback starved. |
| **Canonical Prices Live** | `data/canonical_prices_live.json` | SSoT live price cache across 244 equities | `dashboard/app.py`, `core/market_price_service.py` | `ACTIVE CACHE` | **YES** | 258KB JSON storing latest market quotes. |
| **EGX 244 Universe Catalog** | `data/thndr_egx_244_universe.json` | Catalog of 244 EGX equities with sectors and ISINs | `core/egx_universe_loader.py` | `ACTIVE CATALOG` | **YES** | Official production universe definition. |
| **Locked Holdout Reserve** | `data/holdout_reserve_locked_20260814.json` | Locked daily OHLC prices (May–Aug 2026) | `tests/test_out_of_sample_gate.py` | `CONTAMINATED` | **NO (Contaminated)** | Prior exposure in Phase 2 report; cannot serve as blind holdout. |
| **Phase 1 Baseline Engine** | `research_v43/engines/phase1_cost_aware_baselines.py` | Computes BL-0 to BL-5 baselines over 2020–2024 | Research scripts | `HISTORICAL` | **YES (Baseline SSoT)** | Established `BL3_Momentum` (True Net PF 1.821, Gross 2.138). |
| **Phase 2 Regime Engine** | `research_v43/engines/phase2_market_regime.py` | Market breadth, benchmark index, regime filtering | Research scripts | `INVALIDATED` | **NO (Corrupted)** | Contains `df["Pos_1D"] = (df["Fwd_Ret_1D"] > 0)` lookahead leakage. |
| **Phase 2.5 Validation Engine** | `research_v43/engines/phase25_validation.py` | Evaluates Phase 2 candidates on 2025 validation | Research scripts | `HISTORICAL` | **YES (Crash Detector)** | Proved `P2_Breadth_Momentum` collapse ($PF = 1.592 < 2.138$). |
| **Phase 2.75 Forensic Reset** | `research_v43/engines/phase275_forensic_reset.py` | Root-cause forensic diagnosis & candidate rejection | Research scripts | `AUTHORITATIVE` | **YES (Audit SSoT)** | Isolated lookahead leakage; officially rejected candidate signal. |
| **Clean Room Forensic Script** | `scratch/clean_room/forensic_engine_audit.py` | Autonomous clean-room reproduction & verification | Standalone audit script | `ACTIVE AUDIT` | **YES (Audit Engine)** | Independently reproduces all metrics without branch switching. |
| **Authoritative 20 Reports** | `reports/authoritative_20_reports/01`–`20.md` | Comprehensive architectural documentation | CI/CD sync script | `ACTIVE DOCS` | **YES (System Docs)** | 20 synchronized reports detailing full platform architecture. |
| **Research V5 Sandbox** | `research_v5/src/01_baseline_data.py` | Newly initialized isolated research downloader | Standalone CLI | `INCOMPLETE` | **NO (Experimental)** | Incomplete draft; ingests only 10 equities. |
| **Daily CI Pipeline** | `.github/workflows/daily_pipeline.yml` | Nightly automated testing and state synchronization | GitHub Actions runner | `ACTIVE CI` | **YES** | Fast test runner executing STLC checks. |

---
*Inventory completed and grounded in exact file paths, git commits, and filesystem contents.*

