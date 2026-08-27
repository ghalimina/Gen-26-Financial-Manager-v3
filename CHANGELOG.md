# Changelog

All notable changes to the **GEN-26 Institutional Quant Platform** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.1.0] - 2026-08-26 — Genesis Hardening & Universe Expansion Phase 1

### 🚀 Added
- **Complete Thndr / EGX 224-Stock Universe (`data/thndr_egx_224_universe.json`)**:
  Expanded platform investment coverage to 224 active Egyptian Exchange equities with Arabic/English taxonomy, sectors, and ISIN identifiers.
- **Dynamic Institutional Liquidity Gate Engine (`core/liquidity_filter.py`)**:
  Enforces 3-pillar liquidity screening (ADV30 > 500k shares, ADT30 > 1M EGP, and Zero-Volume Days < 3) to protect models and capital from illiquid assets.
- **Dynamic Liquidity Funnel Header & REST API (`/api/universe/funnel_stats`)**:
  Interactive 3-stage market funnel banner displaying Total Universe (224) -> Tradable Liquid Count -> Daily Qualified Opportunities.
- **Genuine Selenium Headless Browser E2E Test Suite (`tests/e2e_browser_tests.py`)**:
  Full browser automation verifying real DOM rendering, tab switching, and bookmark persistence into `data/user_watchlist.json`.
- **Automated Changelog Generator (`scripts/generate_changelog.py`)**:
  Standardized script compiling git history and milestones into Keep a Changelog format.

### 🔄 Changed
- **Technical Setup Engine (`core/technical_setup_engine.py`)**:
  Completely eradicated hardcoded mock dictionary `_TECHNICAL_PROFILES`. Replaced with strictly dynamic Wilder's RSI, ATR14, MACD (12,26,9), ADX14, ROC, and OBV calculations from empirical bar data.
- **Strict Data Fallback Rule**:
  Stocks lacking sufficient historical bars ($N < 14$) return `status = "DATA_INSUFFICIENT"` with `technical_score = NaN` and are explicitly excluded from ML inference.
- **Multi-Horizon Engine (`core/multi_horizon_engine.py`)**:
  Injected `LiquidityGateEngine` before technical calculation and ML inference, saving CPU cycles and shielding the model from noise.

### 🗑️ Removed
- Deleted hardcoded static `_TECHNICAL_PROFILES` dictionary from `core/technical_setup_engine.py`.
- Removed blocking browser `alert()` and `confirm()` dialogs in `dashboard/templates/index.html`, standardizing on modern non-blocking toasts.

### 🛡️ Fixed
- Fixed multi-threaded race condition in `core/ai_prediction_model.py` by introducing `_TRAIN_LOCK = threading.RLock()`.
- Fixed slice indexing discrepancy in `hv_20` historical volatility calculation.
- Fixed non-blocking watchlisted ticker deletions in browser DOM and backend JSON synchronization.

---

## [3.0.0] - 2026-08-23 — Production Baseline & Multi-Layer Architecture

### Added
- **Multi-Horizon Forecasting Engine (`core/multi_horizon_engine.py`)**:
  Forward projections across 5 discrete time horizons: 1D, 5D, 10D, 20D, and 60D with dynamic price targets (T1, T2, T3) and ATR stops.
- **AI Meta-Labeling & XGBoost Forecast (`core/meta_labeling_engine.py`)**:
  Secondary ML probability model evaluating probability of success and volatility-adjusted returns.
- **Market Breadth & Regime Engine (`core/market_breadth_engine.py`)**:
  Advance/Decline ratio, New Highs/Lows, and EGX30 MA200 breadth classification.
- **Macro Intelligence Engine (`core/macro_intelligence_engine.py`)**:
  CBE interest rate corridors, inflation rates, and USD/EGP regime tracking.
- **Corporate Actions Calendar (`core/corporate_actions_calendar.py`)**:
  Pre-trade corporate action hazard scoring for dividends, splits, and AGMs.
- **Institutional Order Blotter & HRP Execution (`core/portfolio_optimizer.py`)**:
  Hierarchical Risk Parity (HRP) allocation weights and Algo EMS Order Blotter.

---

## Recent Commit History
- `cd32d97` (2026-08-24): fix(pricing): enforce dynamic real-time DOM refresh and single source of truth for ORAS.CA at 782.25 EGP
- `ca37f88` (2026-08-23): chore: sync validated session logs and execution status
- `534f321` (2026-08-23): fix(feed): resolve ORAS.CA root cause via TradingView direct scanner, multi-source fallback, and intelligent circuit breaker escalation
- `1ab0b61` (2026-08-23): feat: complete test suite, verification scripts, documentation, and data baseline
- `ce3c589` (2026-08-23): feat: core engines, daily pipeline workflow, and app runtime
- `16e7d5a` (2026-08-23): chore(v42): intelligence report 2026-08-23
- `d0673e8` (2026-08-23): chore(paper): V4.1 paper session 2026-08-23
- `981df41` (2026-08-20): chore(v42): intelligence report 2026-08-20
- `93e9c24` (2026-08-20): chore(paper): V4.1 paper session 2026-08-20
- `55e6364` (2026-08-19): chore(v42): intelligence report 2026-08-19
- `3d3d08c` (2026-08-19): chore(paper): V4.1 paper session 2026-08-19
- `f14a658` (2026-08-18): chore(v42): intelligence report 2026-08-18
- `66d602e` (2026-08-18): chore(v42): intelligence report 2026-08-18
- `c9c2d01` (2026-08-18): chore(v42): intelligence report 2026-08-18
- `4579af3` (2026-08-18): chore(cleanup): remove obsolete audit artifacts and temporary scratch files
- `f5a69ed` (2026-08-18): chore(v42): intelligence report 2026-08-18
- `ebf123c` (2026-08-18): feat(ui): add persistent truth banner, honesty badges, beginner Arabic tooltips, breadth proxy, and paper progress widget
- `bd3bb22` (2026-08-18): chore(v42): intelligence report 2026-08-18
- `7050ee2` (2026-08-18): fix(ci): add git pull rebase before push in both workflow jobs to prevent push race condition
- `ced8790` (2026-08-18): chore(paper): V4.1 paper session 2026-08-18
- `89a7bb5` (2026-08-18): fix(screener): sanitize inf/nan values in egx_screener before RobustScaler
- `9e3dd3d` (2026-08-18): chore(v42): intelligence report 2026-08-18
- `61d5239` (2026-08-18): fix(ci): track session_manager.py and market_data_provider.py for headless runner
- `97b92c6` (2026-08-18): chore(v42): intelligence report 2026-08-18
- `4316b47` (2026-08-18): docs(forward): add daily and weekly forward validation reports
