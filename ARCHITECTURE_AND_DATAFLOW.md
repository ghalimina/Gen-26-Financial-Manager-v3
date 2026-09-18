# ARCHITECTURE_AND_DATAFLOW.md
# Comprehensive Architecture & Data-Flow Forensic Audit
**System:** GEN-26 Quantitative Financial Architecture  
**Scope:** Complete End-to-End Pipeline & Duplicate Implementations Analysis  
**Audit Context:** `RESEARCH_ONLY / SHADOW_ONLY / NON_PRODUCTION / NO_LIVE_TRADING / NO_ML`

---

## 1. End-to-End Data Pipeline Architecture

The quantitative research and production system processes data through 16 distinct functional stages. The architecture currently exhibits significant divergence between the **historical research pipeline** (`research_v43`) and the **active production runtime** (`core/`):

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 GEN-26 COMPLETE DATA-FLOW TOPOLOGY                                      │
├────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Raw Ingestion       │ Yahoo Finance API (Historical) / EGX Direct Feed & Scrapers (Live)            │
│ 2. Cleaning & Parquet  │ DQ Score Filter, Volume Outlier Filter, Parquet Serialization                 │
│ 3. Adjustments         │ Split & Dividend Adjustments (Adj Close, Adj Open, Adj High, Adj Low)          │
│ 4. Trading Calendar    │ EGX Sunday–Thursday Trading Schedule (Sunday = 0 / Egypt Holiday Table)        │
│ 5. Universe Selection  │ 27-Stock Liquid Core (Research) vs 244-Stock All-EGX Catalog (Production)     │
│ 6. Feature Engineering │ Moving Averages (20, 50, 200), Momentum (5D, 10D, 20D, 60D), RSI14, RVol20D   │
│ 7. Market Breadth      │ Advance/Decline Ratio, 10D/30D Oscillator, % Above SMA20/50                   │
│ 8. Benchmark Index     │ Equal-Weight Cross-Sectional Index Level (Base = 1000)                        │
│ 9. Regime Engine       │ 4 Canonical States: BULL, BEAR, CRISIS, SIDEWAYS + High/Low Volatility         │
│ 10. Signal Generation  │ BL3_Momentum Anchor + Regime & Breadth Filter Gates                           │
│ 11. Entry Timing       │ Signal at Close t → Planned Execution at Open t+1 (Implemented as Close t)    │
│ 12. Forward Target     │ 20-Trading-Day Forward Return (Close[t+20] / Close[t] - 1.0)                  │
│ 13. Friction Model     │ 0.90% RT Base Case (0.35% Statutory + Dynamic Slippage / ATR Model)           │
│ 14. Position / Risk    │ Equal-Weight 1 Unit per Signal (Research) vs Cash Gate & 65% Cap (Production)  │
│ 15. Statistical Tests  │ Profit Factor, Sharpe Ratio, Newey-West HAC (L=20), Disjoint Offsets, Bootstrap│
│ 16. Reporting & UI     │ Markdown Dossiers, JSON Status Files, Flask Dashboard (Port 5000)             │
└────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Stage-by-Stage Forensic Matrix

The table below maps every stage of the pipeline, identifying its implementation across research and production, temporal safety, and potential vulnerabilities:

| Stage # | Pipeline Stage | Source File & Class/Function | Input Columns | Output Columns | Index & Calendar Behavior | Missing-Data Handling | PIT Classification | Environment |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **1** | Raw Ingestion | `research_v43/src/01_baseline_data.py`<br>`core/egx_direct_feed_service.py` | HTTP / Yahoo Finance JSON | `Open`, `High`, `Low`, `Close`, `Volume` | Daily DatetimeIndex (Sun–Thu) | Missing bars skipped | **PIT_SAFE** | Research / Prod |
| **2** | Cleaning & DQ | `research_v43/engines/t0_data_foundation.py`<br>`core/data_quality.py` | Raw OHLCV | `DQ_Score`, clean price arrays | Filter rows where Volume < 0 or High < Low | Dropped or flagged | **PIT_SAFE** | Research / Prod |
| **3** | Adjustments | `research_v43/data/*.parquet`<br>`core/price_anomaly_resolver.py` | `Close`, Splits, Dividends | `Adj Close`, `Adj_Open`, `Adj_High`, `Adj_Low` | Continuous backward-adjusted price | Forward-fill price | **PIT_SAFE** | Research / Prod |
| **4** | Trading Calendar | `research_v43/egx_trading_calendar.csv`<br>`core/market_calendar.py` | Calendar dates (2020–2026) | `is_trading_day`, `session_id` | Enforces Egyptian Sun–Thu work week | Holidays excluded | **PIT_SAFE** | Research / Prod |
| **5** | Universe Filter | `research_v43/historical_universe.csv`<br>`core/egx_universe_loader.py` | Static 27 tickers vs 244 catalog | Active universe boolean mask | Cross-sectional join by date | Excludes inactive tickers | **SURVIVORSHIP_BIASED** | Research / Prod |
| **6** | Feature Eng. | `research_v43/engines/phase1_cost_aware_baselines.py`<br>`core/technical_setup_engine.py` | `Adj Close`, `Volume` | `Mom_20D`, `SMA_20`, `SMA_50`, `RSI_14`, `ATR_Pct` | Rolling windows over sorted trading days | NaN on first $W-1$ rows | **PIT_SAFE** | Research / Prod |
| **7A** | Market Breadth (Buggy) | `research_v43/engines/phase2_market_regime.py`<br>`build_breadth()` | `Fwd_Ret_1D` *(Tomorrow's return!)* | `Breadth_AdvanceRatio`, `Breadth_Osc10D` | Daily cross-sectional mean across universe | Missing stocks omitted | **LOOKAHEAD_LEAKAGE** | Research (P2 Locked) |
| **7B** | Market Breadth (Clean) | `research_v43/engines/phase275_forensic_reset.py`<br>`core/market_breadth_engine.py` | `Ret_1D_Trailing` / live changes | `Breadth_AdvanceRatio_CLEAN`, `Breadth_Osc10D` | Daily cross-sectional mean across universe | Missing stocks omitted | **PIT_SAFE** *(Clean)* / **SYNTHETIC** *(Prod)* | Research / Prod |
| **8** | Benchmark Index | `research_v43/engines/phase2_market_regime.py`<br>`build_regime()` | Cross-sectional daily returns | `BM_Index`, `BM_Mom20D`, `BM_Vol20D` | Cumulative geometric product $\times 1000$ | Zero return on empty dates | **LOOKAHEAD IN P2** *(used Fwd_Ret_1D)* | Research |
| **9** | Regime Engine | `research_v43/engines/phase2_market_regime.py`<br>`core/regime_hmm_engine.py` | `BM_Index`, `BM_Mom20D`, `SMA50`, `SMA200` | `Regime_Primary`, `R_BULL`, `R_BEAR`, `R_CRISIS` | Daily regime state flag | Forward-fill up to 5 bars | **LOOKAHEAD IN P2** *(via BM_Index)* | Research / Prod |
| **10** | Signal Logic | `research_v43/engines/phase2_market_regime.py`<br>`core/alpha_engine.py` | `BL3_Momentum`, Breadth, Regime | `P2_Breadth_Momentum`, `P2_BullBreadth` | Boolean mask on stock-date records | False if any factor is NaN | **LEAKED IN P2 / CLEAN IN P2.75** | Research / Prod |
| **11** | Entry Timing | Research specification vs implementation | Close $t$ vs Open $t+1$ | Execution fill price | Specified at Open $t+1$; executed at Close $t$ | Assumes immediate fill | **TIMING_DISCREPANCY** | Research |
| **12** | Forward Target | `research_v43/data/*.parquet`<br>`compute_targets()` | `Adj Close` at $t$ and $t+20$ | `Fwd_Ret_20D` ($Close[t+20]/Close[t]-1$) | 20 trading sessions forward shift | Truncated at end of sample | **PIT_SAFE (Label Only)** | Research |
| **13** | Cost Model | `trade_metrics()`<br>`core/mcdr_tax_engine.py` | Gross returns, statutory fee schedules | Net trade returns after friction | Subtracted linearly from gross return | Constant 0.90% RT applied | **DISCREPANCY** *(Gross PF reported)* | Research / Prod |
| **14** | Position Sizing | `walk_forward()`<br>`core/risk_position_sizer.py` | Signal occurrences, portfolio equity | Portfolio weights, active slot allocations | Equal-weight 1 unit vs 10% slot cap | Unallocated cash earns 0% | **DISCONNECTED** | Research / Prod |
| **15** | Statistical Tests | `phase25_forensic_repair_suite.py`<br>`core/statistical_validator.py` | Trade net return array / daily equity | PF, Sharpe, HAC $t$-stat, Block Bootstrap | 20-lag Bartlett kernel, 20 disjoint offsets | Excludes NaN returns | **METHOD_DISCREPANCY** | Research / Prod |
| **16** | Reporting & UI | `reports/*.md`, `dashboard/app.py` | Aggregated metrics, live SQLite bars | HTML dashboard, markdown dossiers | Real-time polling vs static generation | Fallback to hardcoded mock | **PARTIAL DISCONNECT** | Research / Prod |

---

## 3. Duplicate Implementation & Divergence Analysis

A critical architectural flaw discovered across the repository is the **presence of multiple competing definitions for the same fundamental financial concepts**. Because research engines and production engines evolved independently, they compute key metrics using conflicting methodologies:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             DUPLICATE DEFINITIONS & ARCHITECTURAL DIVERGENCE                       │
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. 1D Return:                                                                                      │
│    - Research Clean: Adj_Close[t] / Adj_Close[t-1] - 1.0 (Trailing)                                │
│    - Research Target: Adj_Close[t+1] / Adj_Close[t] - 1.0 (Forward)                                 │
│    - Research Buggy Breadth: Treated Forward 1D Return as Today's Trailing Return                   │
│    - Production Feed: (Live_Price - Canonical_Base) / Canonical_Base                                │
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 2. Market Breadth (Advance / Decline Ratio):                                                       │
│    - Research Phase 2: mean(Fwd_Ret_1D > 0) [CRITICAL LOOKAHEAD BUG]                               │
│    - Research Phase 2.75: mean(Ret_1D_Trailing > 0) [CLEAN PIT RECONSTRUCTION]                     │
│    - Production (MarketBreadthEngine): Nominal price vs hardcoded 100.0 EGP reference [SYNTHETIC]   │
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 3. Benchmark Index:                                                                                │
│    - Research Phase 2: (1 + mean(Fwd_Ret_1D)).cumprod() * 1000 [LEAKED FORWARD INDEX]              │
│    - Research Phase 2.75: (1 + mean(Ret_1D_Trailing)).cumprod() * 1000 [CLEAN TRAILING INDEX]       │
│    - Production (MarketDataTruth): Synthetically proxied from COMI.CA or live market DB            │
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 4. Profit Factor (PF):                                                                             │
│    - Academic Standard: sum(Net Wins) / abs(sum(Net Losses))                                       │
│    - Phase 1 & 2 Engine (trade_metrics): sum(Gross Wins) / abs(sum(Gross Losses)) [GROSS ONLY]     │
│    - Phase 2.75 & 2.5: sum(max(0, Ret - Cost)) / abs(sum(min(0, Ret - Cost))) [TRUE NET PF]        │
│    - Production (edge_verifier): Evaluated on synthetic Gaussian random variables                  │
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 5. Maximum Drawdown:                                                                               │
│    - Phase 1 & 2 Engine: cumprod(1 + Net_Trade_Returns) [ARTIFICIAL -100% COMPOUNDING ARTIFACT]   │
│    - Phase 2.5 (calendar_portfolio): Daily mark-to-market portfolio equity curve [-23.37% REAL]    │
│    - Production (edge_verifier): Synthetic peak-to-valley on simulated trades                     │
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 6. Annualized Sharpe Ratio:                                                                        │
│    - Research Overlapping Trades: (mean(Net) / std(Net)) * sqrt(252 / 20) [SCALING DISTORTION]     │
│    - Research Portfolio Daily: (mean(Daily_Net) / std(Daily_Net)) * sqrt(252) [STANDARD DAILY]    │
│    - Production (statistical_validator): Bailey & Lopez de Prado DSR with inverted N/252 variance  │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Key Architectural Vulnerabilities Identified

1. **Research Pipeline Decoupling:**
   The production environment (`core/`) does not import or execute the researched signals from `research_v43`. Instead, it maintains hardcoded metadata registries in `core/alpha_engine.py` and runs simulated mock backtests in `core/edge_verifier.py`.
2. **Denormalized Database Stores:**
   `gen26_production.db` contains only 8,199 historical bars covering July 2026 to September 2026. Because full historical bars are absent from the production database, any production engine attempting historical calibration automatically triggers ungrounded random fallback routines.
3. **Execution Gap between Signal and Target:**
   Research targets evaluate $Close[t+20] / Close[t] - 1.0$, assuming zero-cost execution at the closing bell of day $t$. In actual broker operations, orders cannot be executed until the opening auction of day $t+1$, exposing positions to overnight gap risk.

---
*Architecture and data flow audited and verified against source code implementations.*
