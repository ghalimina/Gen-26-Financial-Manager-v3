# DATA_LINEAGE_AUDIT.md
# End-to-End Data Lineage, Provenance & Point-in-Time Traceability Audit
**System:** GEN-26 Quantitative Financial Architecture  
**Audit Scope:** Full Data Pipeline Provenance (Yahoo Finance, Parquet, SQLite, JSON Feeds)  
**Audit Date:** 2026-09-17  
**Audit Context:** `RESEARCH_ONLY / SHADOW_ONLY / NON_PRODUCTION / NO_LIVE_TRADING / NO_ML`  

---

## 1. Data Source Registry & Lineage Provenance

Every data element utilized in the GEN-26 research and production framework was audited from its initial external ingestion point through transformations, adjustments, storage, and consumption:

| Dataset / File | Primary Ingestion Source | Ingestion / Download Date | Historical Coverage Period | Timestamp Convention & Timezone | Egyptian Trading Calendar Alignment | Symbol Format Convention | Ingestion Mechanism |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Clean Research Parquets** (`research_v43/data/*.parquet`) | Yahoo Finance API (`yfinance` 0.2.x) | 2026-08-16 | 2020-01-02 to 2026-08-16 | Daily midnight UTC (`00:00:00`), representing EOD Cairo (UTC+2 / UTC+3 DST) | Sunday–Thursday trading week (Fri/Sat excluded) | Reuters ticker with exchange suffix: `{TICKER}.CA` | Automated batch download via `yfinance.download(tkr, start="2020-01-01")` |
| **Production SQLite DB** (`data/gen26_production.db`) | Scraped Mubasher / Direct EGX Feeds | Continuous daily updates | 2026-07-12 to 2026-09-10 (Truncated 2 months) | ISO-8601 Date String (`YYYY-MM-DD`) | Sunday–Thursday trading week | Standard Reuters format (`COMI.CA`, etc.) | Ingested via `core/price_sync_service.py` into `historical_daily_bars` |
| **Live Canonical JSON** (`data/canonical_prices_live.json`) | Web Scraping & Direct Feeds | Live real-time | Real-time current quotes | ISO-8601 Timestamp with Cairo offset | Real-time session status | Egyptian tickers with and without `.CA` suffix | SSoT cache polled by `dashboard/app.py` |
| **Point-in-Time Fundamentals** (`data/egx_fundamentals_pit.parquet`) | EGX Corporate Disclosures & Financial Filings | 2026-08-17 | 2019-Q4 to 2026-Q1 | Date of filing publication (EOD) | Matched to closest prior trading session | Egyptian ticker (`COMI.CA`, etc.) | Extracted from structured financial reports with publication lag |

---

## 2. Comprehensive Field-by-Field Audit

The following table traces every critical financial and quantitative variable across the pipeline, auditing its dimensional units, adjustments, and Point-in-Time safety:

| Variable Name | Exact Source Field | Adjustment State | Dimensional Unit | Transformation Applied | Point-in-Time Classification | Potential Failure Mode / Risk |
| :--- | :--- | :--- | :---: | :--- | :---: | :--- |
| **`Close`** | Raw Yahoo EOD Close | Unadjusted | EGP | Direct capture | `PIT_SAFE` | Excludes splits/dividends; cannot be used for return series. |
| **`Adj Close`** | Yahoo `Adj Close` | Backward-Adjusted | EGP | Adjusted for splits & cash dividends | `PIT_SAFE` | SSoT for close-to-close returns. Backward adjusted. |
| **`Open`** | Raw Yahoo EOD Open | Split-Adjusted Only | EGP | Direct capture | `PIT_SAFE` | Not adjusted for cash dividends! Requires $(Adj\_Close / Close)$ scaling for Open-to-Close. |
| **`High` / `Low`** | Raw Yahoo High / Low | Split-Adjusted Only | EGP | Direct capture | `PIT_SAFE` | Closing auction cross prices occasionally fall outside $[Low, High]$ in EGX. |
| **`Volume`** | Raw Yahoo Volume | Unadjusted shares | Number of shares | Direct capture | `DATA_DEFECT` | `ORAS.CA` has 96.32% zero-volume days. Causes division-by-zero in liquidity models. |
| **`Ret_1D_Trailing`** | Derived from `Adj Close` | Backward-Adjusted | Decimal fraction | `c.pct_change(1)` | `PIT_SAFE` | Trailing 1-day return $Close[t] / Close[t-1] - 1.0$. True point-in-time. |
| **`Fwd_Ret_1D`** | Derived from `Adj Close` | Backward-Adjusted | Decimal fraction | `c.shift(-1) / c - 1.0` | **`DANGEROUS LEAKAGE IF USED AT t`** | Target label for tomorrow ($Close[t+1]/Close[t]-1$). Leaked into Breadth in Phase 2! |
| **`Fwd_Ret_20D`** | Derived from `Adj Close` | Backward-Adjusted | Decimal fraction | `c.shift(-20) / c - 1.0` | `PIT_SAFE (AS LABEL)` | 20-trading-day forward holding return. Used strictly as target evaluation variable. |
| **`SMA_20` / `SMA_50`** | Derived from `Adj Close` | Backward-Adjusted | EGP | `c.rolling(W).mean()` | `PIT_SAFE` | Strictly trailing moving average. Safe if minimum period requirement enforced. |
| **`Mom_20D`** | Derived from `Adj Close` | Backward-Adjusted | Decimal fraction | `c / c.shift(20) - 1.0` | `PIT_SAFE` | 20-day trailing price momentum. Point-in-time safe. |
| **`Breadth_AdvanceRatio`** | Cross-sectional Mean | Clean vs Buggy | Ratio $[0, 1]$ | `mean(Pos_1D)` across universe | **`LEAKAGE IN PHASE 2 / SAFE IN P2.75`** | Phase 2 used `Fwd_Ret_1D > 0` (Lookahead). Phase 2.75 used `Ret_1D_Trailing > 0` (Clean). |
| **`BM_Index`** | Cross-sectional Return | Clean vs Buggy | Index Points (Base 1000) | `(1 + mean(ret)).cumprod() * 1000` | **`LEAKAGE IN PHASE 2 / SAFE IN P2.75`** | Phase 2 accumulated `Fwd_Ret_1D` into benchmark, leaking future returns into moving averages. |
| **`R_BULL` / `R_BEAR`** | Derived from `BM_Index` | Clean vs Buggy | Binary Flag $\{0, 1\}$ | Moving average & momentum filters | **`CORRUPTED IN P2 / CLEAN IN P2.75`** | Corrupted in Phase 2 due to future benchmark accumulation; clean in Phase 2.75. |
| **`RobustScaler`** | Machine Learning Feature | Z-Score Normalization | Standardized unit | `(X - median) / IQR` | **`LEAKAGE IN EARLY T6 / FIXED IN QA`** | Early Tier 6 fitted across entire 2020–2026 dataset; fixed in QA sweep to fit on `X_train` only. |

---

## 3. Data Lineage Vulnerability & Point-in-Time Checklist

1. **What date does each feature represent?**
   * Every trailing feature (`Mom_20D`, `SMA_50`, `RVol_20D`, `Ret_1D_Trailing`) represents market state up to and including the Close of date $t$.
2. **What information was available at that date?**
   * The official closing auction price of date $t$, historical closing bars $t-1, t-2, \dots$, and previously published financial disclosures.
3. **Does the feature contain future information?**
   * **In Phase 2 Locked Spec:** YES. `Breadth_AdvanceRatio` and `BM_Index` used `Fwd_Ret_1D`, which contains the closing price of date $t+1$.
   * **In Phase 2.75 / Clean Room:** NO. All features strictly evaluate `Ret_1D_Trailing`.
4. **Is the feature shifted correctly?**
   * Moving averages and rolling standard deviations use default trailing windows (no forward lookback).
   * Forward returns use negative shifts (`shift(-1)`, `shift(-20)`), which are safe *only* when evaluated as target outcomes post-signal.
5. **Is any scaler or normalizer fitted on future data?**
   * In Tier 6 ML (historical), `RobustScaler` initially leaked full-sample statistics. This was resolved in commit `312b55b` by fitting strictly on `X_train`. Tier 6 ML is currently disabled in production.
6. **Can any future row leak into a prior row during pandas operations?**
   * `bfill()` operations were audited across all feature scripts: zero instances of backward filling future price data were found. `ffill(limit=5)` is used safely for corporate filing persistence.

---
*Data lineage verified from raw API response to final strategy evaluation metrics.*
