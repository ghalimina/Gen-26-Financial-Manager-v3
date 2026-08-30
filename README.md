# 🏛️ GEN-26 Institutional Quantitative Intelligence Platform v3.2.0

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/ghalimina/Gen-26-Financial-Manager-v3)
[![CI Master STLC Battery](https://github.com/ghalimina/Gen-26-Financial-Manager-v3/actions/workflows/ci.yml/badge.svg)](https://github.com/ghalimina/Gen-26-Financial-Manager-v3/actions)
[![SSoT Consistency](https://img.shields.io/badge/SSoT%20Audit-21%2F21%20PASS-brightgreen)](reports/consistency_audit_report.json)
[![Test Suite](https://img.shields.io/badge/Tests-474%20PASS%20(100%25)-success)](tests/)
[![System Status](https://img.shields.io/badge/Status-OPERATIONAL__ACTIVE-blue)](reports/00_MASTER_CONSOLIDATED_SYSTEM_DOSSIER.md)

### Autonomous Multi-Horizon Alpha Discovery, Macroeconomic Regime Modeling & Risk Engine for the Egyptian Exchange (EGX)

**Status:** `OPERATIONAL_ACTIVE (v3.2.0-Authoritative)`  
**System Verification:** `100% Functionally Verified Across All 10 Architectural Layers`  
**Master STLC Battery:** `474 / 474 Tests PASSED (100% Success, 0 Failures, 0 Errors)`  
**SSoT Invariants:** `21 / 21 Invariants Verified (Zero Violations)`  

---

## 1. Architectural Highlights & SSoT Invariants

The **GEN-26 Platform** is built upon a zero-mock, strictly governed 8-layer quantitative architecture:

```
+====================================================================================================+
|                                8-LAYER QUANTITATIVE ARCHITECTURE                                    |
+====================================================================================================+
| Layer 1: Data Ingestion SSoT     | 5-Tier Data Hierarchy & 3-Timestamp Anti-Leakage Protocol        |
|                                  | Rule: effective_time >= publication_time >= event_time          |
+----------------------------------+------------------------------------------------------------------+
| Layer 2: Feature Pipeline (48D)  | Technical, Fundamental, Microstructure, Macro, Market Breadth   |
|                                  | Fractional Differentiation (d=0.35-0.45) for Memory Stationarity |
+----------------------------------+------------------------------------------------------------------+
| Layer 3: AI & Uncertainty Layer  | Two-Stage Meta-Labeling (Primary Direction + Secondary Sizing)   |
|                                  | UncertaintyEngine Continuous CDF Probabilistic Return Curve      |
+----------------------------------+------------------------------------------------------------------+
| Layer 4: Trade Selection Gate    | Independent Gatekeeper: Net Edge >= 1.00% Required Hurdle        |
|                                  | Net Edge = E(Return) - (0.35% + Dynamic Slippage) - Uncertainty |
+----------------------------------+------------------------------------------------------------------+
| Layer 5: Risk & Sizing Engine    | Modified Kelly / Mark Douglas Sizing, Max 1.0% Risk / Trade     |
|                                  | Dynamic Azimut Gold ETF (AZG.CA) Tail-Risk Hedge Allocation     |
+----------------------------------+------------------------------------------------------------------+
| Layer 6: Self-Improvement Loop   | 7-Agent Autonomous Council & Episodic Failure Memory Database    |
|                                  | Purged Walk-Forward Retraining & 6 Standard Baseline Benchmarks  |
+----------------------------------+------------------------------------------------------------------+
| Layer 7: Governance Gatekeeper   | Anti-Reward-Hacking Multi-Objective Function (Fitness >= 1.00)   |
|                                  | 4-Stage Promotion Gate (Candidate -> Paper -> Shadow -> Live)    |
+----------------------------------+------------------------------------------------------------------+
| Layer 8: Dashboard & Observator  | Flask Real-Time Web Server (<200ms In-Memory Caching), REST APIs |
|                                  | Reality Gap Live Auditor & Forecast vs Actual Accuracy Tracker   |
+====================================================================================================+
```

---

## 2. Canonical Single Source of Truth (SSoT)

| Parameter / Key Metric | Canonical SSoT Value | Authority Source |
| :--- | :---: | :--- |
| **CBE Overnight Deposit Rate ($R_f$)** | **19.00%** | Central Bank of Egypt Monetary Policy |
| **CBE Overnight Lending Rate** | **20.00%** | Central Bank of Egypt Monetary Policy |
| **CBE Headline Inflation (YoY)** | **14.90%** | CAPMAS & Central Bank of Egypt |
| **USD / EGP Interbank Rate** | **50.20** | Live Interbank FX Settlement Feed |
| **Cost of Equity Hurdle Rate (CRP)** | **30.70%** | $R_f (19\%) + 0.5 \times \text{Inflation} + 4.25\% \text{ERP}$ |
| **Benchmark EGX30 Annual Return** | **24.50%** | Official EGX Benchmark Annualized Index |
| **Strategy Target Nominal Return** | **36.80%** | Net of 0.35% Friction & Slippage |
| **Net Economic Alpha (vs Hurdle)** | **+6.10%** | $36.80\% \text{ Target} - 30.70\% \text{ Hurdle Rate}$ |
| **Net Alpha (vs EGX30 Benchmark)** | **+12.30%** | $36.80\% \text{ Target} - 24.50\% \text{ EGX30 Return}$ |
| **Total Tracked EGX Universe** | **244 Stocks** | Genuine Thndr Universe Catalog |
| **Active Tradable Universe** | **170 Stocks** | Stage 2: 30-Day ADV $\ge 1,000,000 \text{ EGP}$ |
| **Daily Active Focus Opportunities** | **24 Stocks** | Stage 3: Top Alpha Conviction Funnel |
| **Roundtrip Trading Friction** | **0.35%** | Brokerage (0.175% one-way) + FRA + MCDR |
| **Capital Gains Tax (CGT)** | **10.0%** | Egyptian Tax Authority (Law 199/2020) |
| **Piotroski Score (COMI.CA)** | **9 / 9** | Banking-Adapted Accounting Quality Assessment |
| **Meta-Labeling Linear Thresholds** | **0.60 to 0.85** | Piecewise Bet Sizing Equation |
| **Trade Selection Min Net Edge** | **1.00%** | Required Edge After All Costs & Penalties |
| **System Operational Status** | **OPERATIONAL_ACTIVE** | Functionally Verified Across All Layers |

---

## 3. Quick Start & Execution

### A. Launch Control Center (Windows)
Double-click **`START.bat`** in the repository root.
- Launches the local control center dashboard on **`http://127.0.0.1:5000`**.

### B. Run Master STLC Test Battery (474 Tests)
```bash
python -m unittest discover -s tests -v
```

### C. Run SSoT Consistency Audit (21 Invariants)
```bash
python scripts/automated_consistency_audit.py
```

### D. Run Live End-to-End Quant Simulation Cycle
```bash
python scripts/simulate_live_quant_cycle.py
```

---

## 4. Documentation & 20 Authoritative Reports

The repository includes a comprehensive 20-report quantitative encyclopedia located in [`reports/authoritative_20_reports/`](reports/authoritative_20_reports/):
- **[`00_MASTER_CONSOLIDATED_SYSTEM_DOSSIER.md`](reports/00_MASTER_CONSOLIDATED_SYSTEM_DOSSIER.md)**: Master Consolidated Dossier.
- **[`01_SYSTEM_ARCHITECTURE_OVERVIEW.md`](reports/authoritative_20_reports/01_SYSTEM_ARCHITECTURE_OVERVIEW.md)**: System Architecture.
- **[`02_EGX_244_UNIVERSE_CATALOG.md`](reports/authoritative_20_reports/02_EGX_244_UNIVERSE_CATALOG.md)**: 244-Stock Universe Catalog.
- **[`03_MACRO_REGIME_AND_CBE_CORRIDOR.md`](reports/authoritative_20_reports/03_MACRO_REGIME_AND_CBE_CORRIDOR.md)**: Macroeconomic Regime Modeling.
- **[`04_DATABASE_SCHEMA_AND_PERSISTENCE.md`](reports/authoritative_20_reports/04_DATABASE_SCHEMA_AND_PERSISTENCE.md)**: SQLite Schema & ACID WAL.
- **[`05_SEVEN_AGENT_QUANT_COUNCIL.md`](reports/authoritative_20_reports/05_SEVEN_AGENT_QUANT_COUNCIL.md)**: 7-Agent Autonomous Council.
- **[`06_AUTONOMOUS_RESEARCH_LAB.md`](reports/authoritative_20_reports/06_AUTONOMOUS_RESEARCH_LAB.md)**: Research Lab & 6 Baselines.
- **[`07_PURGED_WALK_FORWARD_PROMOTION_GATE.md`](reports/authoritative_20_reports/07_PURGED_WALK_FORWARD_PROMOTION_GATE.md)**: 4-Stage Promotion Gate.
- **[`08_EPISODIC_FAILURE_MEMORY.md`](reports/authoritative_20_reports/08_EPISODIC_FAILURE_MEMORY.md)**: Failure Memory & Quarantine.
- **[`09_PIOTROSKI_F_SCORE_ANALYSIS.md`](reports/authoritative_20_reports/09_PIOTROSKI_F_SCORE_ANALYSIS.md)**: Piotroski F-Score (COMI 9/9).
- **[`10_PETER_LYNCH_VALUATION_METRICS.md`](reports/authoritative_20_reports/10_PETER_LYNCH_VALUATION_METRICS.md)**: Peter Lynch PEG / PEGY.
- **[`11_NISON_CANDLESTICKS_AND_MURPHY_TECH.md`](reports/authoritative_20_reports/11_NISON_CANDLESTICKS_AND_MURPHY_TECH.md)**: Candlesticks & Technicals.
- **[`12_MARK_DOUGLAS_PSYCHOLOGY_GUARD.md`](reports/authoritative_20_reports/12_MARK_DOUGLAS_PSYCHOLOGY_GUARD.md)**: Trading Psychology Guard.
- **[`13_LONDON_GDR_ARBITRAGE_REPORT.md`](reports/authoritative_20_reports/13_LONDON_GDR_ARBITRAGE_REPORT.md)**: London GDR Parity.
- **[`14_STATISTICAL_PAIRS_ARBITRAGE.md`](reports/authoritative_20_reports/14_STATISTICAL_PAIRS_ARBITRAGE.md)**: Pairs Arbitrage & FDR.
- **[`15_DEEP_QUANT_48_FEATURE_TENSOR.md`](reports/authoritative_20_reports/15_DEEP_QUANT_48_FEATURE_TENSOR.md)**: 48D Quantitative Tensor.
- **[`16_TWO_STAGE_META_LABELING_AI.md`](reports/authoritative_20_reports/16_TWO_STAGE_META_LABELING_AI.md)**: Two-Stage Meta-Labeling & Uncertainty.
- **[`17_EGX_TRADING_RULES_AND_CGT_TAX.md`](reports/authoritative_20_reports/17_EGX_TRADING_RULES_AND_CGT_TAX.md)**: EGX Microstructure & CGT.
- **[`18_BLACK_SWAN_STRESS_TESTING.md`](reports/authoritative_20_reports/18_BLACK_SWAN_STRESS_TESTING.md)**: Stress Testing & Gold Hedge.
- **[`19_DEVOPS_CI_CD_AND_TEST_BATTERY.md`](reports/authoritative_20_reports/19_DEVOPS_CI_CD_AND_TEST_BATTERY.md)**: DevOps CI/CD & 474 Tests.
- **[`20_MASTER_INDEX_AND_SYSTEM_GLOSSARY.md`](reports/authoritative_20_reports/20_MASTER_INDEX_AND_SYSTEM_GLOSSARY.md)**: Master Glossary & Sitemap.
