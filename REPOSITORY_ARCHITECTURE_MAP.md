# REPOSITORY_ARCHITECTURE_MAP.md
# Concrete Dependency Flow & Execution Map
**System:** GEN-26 Quantitative Financial Architecture  
**Audit Context:** `RESEARCH_ONLY / SHADOW_ONLY / NON_PRODUCTION / NO_LIVE_TRADING / NO_ML`  
**Audit Date:** 2026-09-17  

---

## 1. Concrete End-to-End Dependency Flow

This document maps the **actual implementation flow as it exists in code today**, distinguishing between the research pipeline (`research_v43` on branch `research/full-feature-rebuild-v43` and `scratch/clean_room/`) and the active production runtime (`core/` and `dashboard/` on branch `main`).

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               ACTUAL DEPENDENCY & EXECUTION FLOW                                 │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Data Ingestion      │ yfinance download (Research) / EGX Scraper & Poll (Runtime)             │
│          ▼                                                                                       │
│ 2. Data Cleaning       │ Volume > 0, High >= Low, Parquet Serialization (Clean Parquets)         │
│          ▼                                                                                       │
│ 3. Feature Generation  │ Rolling Windows: SMA20/50/200, Mom20D, Vol20D, Breadth Ratios           │
│          ▼                                                                                       │
│ 4. Signal Generation   │ BL3_Momentum Anchor (Mom20D > 0 & Close > SMA50) + Breadth/Regime Gates │
│          ▼                                                                                       │
│ 5. Portfolio Sizing    │ Equal-Weight 1 Unit per Signal (Research) vs 10% Slot Cap (Production)  │
│          ▼                                                                                       │
│ 6. Cost Model          │ 0.90% RT (35 bps statutory + dynamic slippage clip 0.10%–0.50%)         │
│          ▼                                                                                       │
│ 7. Backtest Execution  │ 20-Day Forward Return Evaluation (Close[t+20] / Close[t] - 1.0)         │
│          ▼                                                                                       │
│ 8. Trade Metrics       │ Profit Factor, Sharpe, Max Drawdown (Sequential compounding in P1/P2)   │
│          ▼                                                                                       │
│ 9. Validation Gates    │ Purged Walk-Forward, Newey-West HAC (L=20), Disjoint Offsets (k=20)     │
│          ▼                                                                                       │
│ 10. Reports Generation │ Markdown Dossiers, JSON Artifacts, CSV Tables                           │
│          ▼                                                                                       │
│ 11. Dashboard Runtime  │ Flask Server (Port 5000), Real-Time Polling, Frozen Risk Gates          │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Stage-by-Stage Implementation

### Stage 1: Data Ingestion
* **Research Implementation:**
  * File: `research_v43/src/01_baseline_data.py` & `research_v43/engines/phase26_forensic_suite.py:load_or_fetch_delisted_data()`
  * Source: Yahoo Finance API (`yfinance.download(ticker, start="2020-01-01", end="2026-01-01")`).
  * Inputs: Egyptian Exchange ticker strings with suffix `.CA` (e.g., `COMI.CA`, `FWRY.CA`).
  * Outputs: Unadjusted OHLCV DataFrame (`Open`, `High`, `Low`, `Close`, `Adj Close`, `Volume`).
  * Index: Daily `DatetimeIndex` (Sun–Thu trading week).
* **Production Runtime Implementation:**
  * File: `core/egx_direct_feed_service.py` & `core/price_sync_service.py`
  * Source: Live web scraping from Mubasher / EGX broker feeds, cached to `data/canonical_prices_live.json`.
  * Database: Ingests intraday ticks into `data/gen26_production.db` (`historical_daily_bars` table).
  * Current Reality: Contains only 8,199 historical bars (spanning 2026-07-12 to 2026-09-10), starving long-lookback calculations.

### Stage 2: Cleaning & Adjustment
* **Research Implementation:**
  * File: `research_v43/engines/t0_data_foundation.py`
  * Deduplication: `df = df[~df.index.duplicated(keep="last")]`.
  * Sanity Filters: Asserts `High >= Low`, `High >= Close`, `Low <= Open`. Penalizes zero volume and price jumps.
  * Corporate Action Treatment: Evaluates price continuity on backward split-adjusted prices (`Adj Close`). Note: Yahoo Finance provides backward dividend/split adjustment *only* on `Adj Close`; `Open`, `High`, `Low` are split-adjusted but not dividend-adjusted.
  * Serialization: Stored as 27 clean Parquet files in `research_v43/data/{TICKER}_clean.parquet` (42,641 total stock-day rows).
* **Production Runtime Implementation:**
  * File: `core/price_anomaly_resolver.py` & `core/data_quality.py`
  * Reconciles cross-source price variance between canonical cache and broker feeds. Resolves splits via ratio matching.

### Stage 3: Feature Generation
* **Research Implementation:**
  * File: `research_v43/engines/phase1_cost_aware_baselines.py:prepare_data()` & `phase2_market_regime.py:build_regime()`
  * Trailing Returns: `Ret_1D_Trailing = c.pct_change(1)`.
  * Moving Averages: `SMA_20 = c.rolling(20).mean()`, `SMA_50 = c.rolling(50).mean()`, `SMA_200 = c.rolling(200).mean()`.
  * Momentum: `Mom_20D = c / c.shift(20) - 1.0`.
  * Volatility: `ATR_Pct = ATR(14) / c`, `RVol_20D = Ret_1D.rolling(20).std() * sqrt(252)`.
  * Market Breadth: Cross-sectional aggregation across all 27 stocks:
    * Clean: `Breadth_AdvanceRatio = mean(Ret_1D_Trailing > 0)`.
    * Buggy (Phase 2): `Breadth_AdvanceRatio = mean(Fwd_Ret_1D > 0)` *(Lookahead defect)*.
* **Production Runtime Implementation:**
  * File: `core/technical_setup_engine.py` & `core/market_breadth_engine.py`
  * `core/market_breadth_engine.py` lines 49–68: Contains an active synthetic fallback comparing nominal price against `ref_base = 100.0` EGP.

### Stage 4: Signal Generation
* **Research Implementation:**
  * File: `research_v43/engines/phase1_cost_aware_baselines.py` & `phase2_market_regime.py`
  * Rule `BL3_Momentum`: `(Mom_20D > 0) & (Adj_Close > SMA_50)`.
  * Rule `P2_Breadth_Momentum`: `(BL3_Momentum == True) & (Breadth_AdvanceRatio > 0.50) & (Breadth_Osc10D > 0)`.
  * Rule `P2_BullBreadth`: `(BL3_Momentum == True) & (R_BULL == 1) & (Breadth_AboveSMA20 > 0.55)`.
* **Production Runtime Implementation:**
  * File: `core/alpha_engine.py` & `core/multi_horizon_engine.py`
  * Aggregates model scores using weights calibrated by `core/weight_calibrator.py`.
  * Active Defect: `core/weight_calibrator.py` computes `fund_s = 60.0 + closes[i] / 10.0`, biasing weights toward nominal high-priced stocks.

### Stage 5: Portfolio Construction & Sizing
* **Research Implementation:**
  * Unconstrained Trade Pooling: Standard research engines (`phase1`, `phase2`) treat every signal independently with 1 unit equal sizing, ignoring cash constraints and portfolio concurrency.
  * Calendar MTM Portfolio: `research_v43/reports/phase_2_5_calendar_portfolio.json` implemented a constrained daily MTM portfolio:
    * 10% maximum slot cap per stock (maximum 10 simultaneous positions).
    * 65% maximum total portfolio exposure cap.
    * 10% cash reserve floor.
* **Production Runtime Implementation:**
  * File: `core/frozen_invariants.py` & `core/real_portfolio.py`
  * Enforces strict production safety gates:
    * Cash Gate: Minimum 10% cash balance required at all times.
    * Allocation Cap: Maximum 65% total portfolio equity deployed.
    * Single-Stock Limit: Maximum 10% of portfolio equity in any single asset.

### Stage 6: Cost Model
* **Research Implementation:**
  * File: `research_v43/engines/phase1_cost_aware_baselines.py:prepare_data()` lines 141–146
  * Statutory Fees: Fixed 0.35% round-trip (brokerage + exchange + MCDR + investor protection).
  * Dynamic Slippage: `Slip_Est = clip(ATR_Pct * 0.0012 * sqrt(1M / AvgTradedVal), 0.10%, 0.50%)`.
  * Total Round-Trip Friction: `Cost_Model_RT = BASE_FEE_RT + 2 * Slip_Est` (Baseline standard: 0.90% RT).
  * Dimensional Defect: In `trade_metrics()`, `profit_factor` is computed as `gw / gl` (Gross Profit Factor) while reported as Net Profit Factor after 0.90% cost.
* **Production Runtime Implementation:**
  * File: `core/mcdr_tax_engine.py`
  * Computes precise Egyptian capital gains tax (CGT at 10% on net realized gains) and MCDR clearance fees.

### Stage 7: Backtest Execution & Trade Accounting
* **Research Implementation:**
  * Contract: Signal calculated at Close of date $t$. Intended execution at Open $t+1$. Exit at Close $t+20$.
  * Actual Code: Evaluates `c.shift(-20) / c - 1.0` (Close $t+20$ / Close $t$ - 1.0).
  * Timing Error: Omits overnight gap between Close $t$ and Open $t+1$ (Mean tracking error $-0.0033\%$, single-stock variance $\pm 8.69\%$).
  * Overlapping Trades: Trades initiated on consecutive days share up to 19 calendar trading days.
* **Production Runtime Implementation:**
  * File: `core/edge_verifier.py`
  * Active Defect: Uses `np.random.normal(0.0008, 0.018)` with `np.random.seed(42)` to simulate 250 periods of synthetic returns rather than executing against historical bars.

### Stage 8: Trade Metrics & Statistics
* **Research Implementation:**
  * Files: `trade_metrics()` across all research engines.
  * Profit Factor: Sum of winning returns divided by absolute sum of losing returns.
  * Sharpe Ratio: Multiplies trade-level Sharpe by $\sqrt{252 / 20}$ (assuming independent non-overlapping blocks).
  * Max Drawdown Artifact: `(1 + net).cumprod()` sequentially compounds concurrent trades, generating artificial $-100\%$ drawdowns. Fixed in Phase 2.5 by daily calendar portfolio MTM.
* **Production Runtime Implementation:**
  * File: `core/statistical_validator.py`
  * Active Defect 1: Hardcoded stability dictionary (values 1.980 to 2.138) in `evaluate_parameter_neighborhood_stability()`.
  * Active Defect 2: Deflated Sharpe Ratio divides variance by `years = T / 252` instead of total observations $T$, inflating variance by a factor of 252.

### Stage 9: Validation & Statistical Gates
* **Research Implementation:**
  * File: `research_v43/engines/phase25_forensic_repair_suite.py` & `phase275_forensic_reset.py`
  * Purged Walk-Forward: 5 expanding folds with 20-day purge gap between train and test.
  * Newey-West HAC: Lag $L=20$ Bartlett kernel accounting for MA(19) autocorrelation induced by overlapping 20-day windows.
  * Disjoint Offset Analysis: 20 calendar offset slices evaluating non-overlapping trades.
  * Block Bootstrap: Block length 20, 2000 resamples preserving short-term serial dependence.
* **Production Runtime Implementation:**
  * Unit tests in `tests/test_hardening_phase_2.py` execute against the synthetic mocks in `core/edge_verifier.py`.

### Stage 10: Reporting & Documentation
* **Research Layer:** Generated 81 markdown reports, CSV summaries, and JSON artifacts on `research/full-feature-rebuild-v43`.
* **Production Layer:** 20 authoritative markdown reports in `reports/authoritative_20_reports/` synchronized via `scripts/sync_all_20_reports.py`.

### Stage 11: Dashboard & Live Runtime
* **Entrypoint:** `python dashboard/app.py`
* **Port:** 5000 (`/api/overview`, `/api/stocks`, `/api/signals`, `/api/system/status`).
* **Frontend:** `dashboard/templates/index.html` with TradingView Lightweight Charts, real-time Arabic/English UI, and simulated paper order dispatch.
* **Live Gates:** Cash Gate $\ge 10\%$, Allocation Cap $\le 65\%$ strictly checked before paper trade logging.

---
*Repository Architecture Map grounded in active codebase structure and execution paths.*
