# FINDINGS_REGISTER.md
# Comprehensive Findings, Defects & Forensic Risk Register
**System:** GEN-26 Quantitative Financial Architecture  
**Audit Period:** Current Working Tree (`main`) & Research Archive (`research_v43`)  
**Audit Date:** 2026-09-17  
**Audit Context:** `RESEARCH_ONLY / SHADOW_ONLY / NON_PRODUCTION / NO_LIVE_TRADING / NO_ML`

---

## 1. Classification & Severity Framework

Every finding in this register is classified under the following formal criteria:

### Severity Levels:
* **`CRITICAL`**: Invalidates a major research conclusion, contaminates the holdout dataset, or creates direct financial execution risk in production.
* **`HIGH`**: Materially affects quantitative signal validity, statistical inference, or backtesting credibility.
* **`MEDIUM`**: Methodological limitation, pricing discrepancy, or material reproducibility issue requiring correction.
* **`LOW`**: Documentation drift, maintainability defect, or minor arithmetic rounding inconsistency.
* **`INFORMATIONAL`**: Architectural context, structural design decision, or verified positive invariant.

### Types:
`Code Bug` | `Data Bug` | `Lookahead Leakage` | `Timing Error` | `Cost Modeling Error` | `Statistical Error` | `Selection Bias` | `Survivorship Bias` | `Methodological Limitation` | `Documentation Error` | `Reproducibility Issue` | `False Positive` | `Already Fixed` | `Unresolved`

---

## 2. Complete Forensic Findings Master Register

| Finding ID | Finding Title | Severity | Defect Type | Current Status | Affected Component / File Path | Forensic Evidence & Reproduction Summary | Research / Operational Impact |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- | :--- |
| **F-01** | **Forward Target Lookahead in Market Breadth** | **`CRITICAL`** | `Lookahead Leakage` / `Code Bug` | **`CONFIRMED (HISTORICAL)`** *(Fixed in P2.75)* | `research_v43/engines/phase2_market_regime.py:265` | `df["Pos_1D"] = (df["Fwd_Ret_1D"] > 0).astype(int)` evaluated tomorrow's return at date $t$. | Artificially inflated Phase 2 Profit Factor from $2.000$ to $2.605$ in dev, and $1.454$ to $1.592$ in val. |
| **F-02** | **Forward Benchmark Accumulation Leakage** | **`CRITICAL`** | `Lookahead Leakage` / `Code Bug` | **`CONFIRMED (HISTORICAL)`** *(Fixed in P2.75)* | `research_v43/engines/phase2_market_regime.py:161-164` | `daily_ret = panel.groupby(...)["Fwd_Ret_1D"].mean()` built `BM_Index` from forward returns. | Leaked future returns into benchmark moving averages and all regime indicators (`R_BULL`, `R_BEAR`). |
| **F-03** | **Prior 2026 Holdout Exposure Before Lock** | **`CRITICAL`** | `Selection Bias` / `Methodological Limitation` | **`CONFIRMED`** | `research_v43/reports/phase_2_annual_breakdown.csv`<br>`phase_2_regime_fold_detail.csv` | Phase 2 walk-forward Fold 5 evaluated through 2026-07-19 on 2026-08-18. 2026 was locked on 2026-08-19. | The 2026 dataset was not an untouched blind holdout; the winning signal was selected after observing $PF = 3.084$ in 2026. |
| **F-04** | **Synthetic Random Backtest in Production Engine** | **`CRITICAL`** | `Code Bug` / `Methodological Limitation` | **`CONFIRMED (ACTIVE ON MAIN)`** | `core/edge_verifier.py:52-67` | Uses `np.random.seed(42)` and `np.random.normal(0.0008, 0.018)` to simulate trades, claiming real statistical edge. | Production system claims empirical backtest verification, but evaluates zero historical market data. |
| **F-05** | **Hardcoded Plateau Stability Validator** | **`HIGH`** | `Code Bug` / `Documentation Error` | **`CONFIRMED (ACTIVE ON MAIN)`** | `core/statistical_validator.py:129-137` | `evaluate_parameter_neighborhood_stability()` returns a static hardcoded dictionary with values 1.98 to 2.138. | Unit test `test_03_parameter_neighborhood_stability` passes fraudulently against static mock dictionary. |
| **F-06** | **Nominal Share Price Used as Fundamental Alpha** | **`HIGH`** | `Code Bug` / `Methodological Limitation` | **`CONFIRMED (ACTIVE ON MAIN)`** | `core/weight_calibrator.py:202` | `fund_s = float(np.clip(60.0 + (closes[i] / 10.0), 30.0, 90.0))`. Higher nominal share price gets higher score. | Arbitrarily biases factor optimization toward nominal high-priced stocks (e.g. ORAS at 759 EGP vs RAYA at 7 EGP). |
| **F-07** | **Synthetic Nominal Reference in Market Breadth** | **`HIGH`** | `Code Bug` / `Methodological Limitation` | **`CONFIRMED (ACTIVE ON MAIN)`** | `core/market_breadth_engine.py:49-68` | Compares nominal stock price against arbitrary `ref_base = 100.0` EGP, classifying stocks $< 50$ EGP as "crash". | Generates distorted advance/decline and regime classifications in the active production runtime. |
| **F-08** | **Gross vs Net Profit Factor Hurdle Inconsistency** | **`HIGH`** | `Cost Modeling Error` / `Documentation Error` | **`CONFIRMED (HISTORICAL)`** | `phase1_cost_aware_baselines.py:148-151` | `trade_metrics()` computed Gross PF ($\sum r^+ / |\sum r^-|$) while reporting it as Net PF after 0.90% cost. | Artificially elevated the baseline bar from True Net PF $1.821$ to Gross PF $2.138$ ($+0.317$ bias). |
| **F-09** | **Sequential Trade Compounding Drawdown Artifact** | **`HIGH`** | `Statistical Error` / `Code Bug` | **`ALREADY FIXED`** *(in P2.75 / P2.5)* | `phase1_cost_aware_baselines.py:159`<br>`phase2_market_regime.py` | Multiplied trade returns sequentially `(1 + net).cumprod()`, compounding overlapping same-day trades. | Generated artificial $-99.9\%$ to $-100\%$ drawdown reports, fixed by daily MTM portfolio tracking ($-23.37\%$). |
| **F-10** | **Severe Zero-Volume Illiquidity in `ORAS.CA`** | **`HIGH`** | `Data Bug` / `Modeling Limitation` | **`CONFIRMED`** | `research_v43/data/ORAS.CA_clean.parquet` | 96.32% of historical sessions recorded Volume = 0 (1,179 / 1,224 bars). Commences only 2021-08-10. | Sizing, dynamic slippage, and fill assumptions are completely unexecutable for this major constituent. |
| **F-11** | **Debunked Survivorship Bias Resolution Claim** | **`HIGH`** | `Survivorship Bias` / `Documentation Error` | **`CONFIRMED`** | `research_v43/reports/phase_2_6_survivorship_reconstruction.md` | Claimed 8 delisted stocks proved zero survivorship bias. All 8 are active listed surviving companies. | Survivorship bias remains unresolved. True strategy win rates and PFs suffer uncorrected upward bias. |
| **F-12** | **Disjoint Offset Masking via Full Sample Pooling** | **`HIGH`** | `Statistical Error` / `Selection Bias` | **`CONFIRMED`** | `research_v43/reports/phase_2_5_final_verdict.md:Section 6` | Claimed 100% of disjoint offsets passed hurdle by pooling 2020–2025. On 2025 alone, median PF is only 1.591. | 75% of disjoint execution offsets on the clean validation period fail to beat the baseline bar ($2.138$). |
| **F-13** | **Decoupling of Research Pipeline from Main Runtime** | **`HIGH`** | `Reproducibility Issue` / `Architecture` | **`CONFIRMED`** | Branch divergence between `main` and `research/full-feature-rebuild-v43` | All quantitative research scripts and parquets were purged from `main` in commit `31fe1a4`. | Impossible to run or reproduce quantitative research directly from the active `main` working tree without branch checkout. |
| **F-14** | **Production SQLite Historical Bar Starvation** | **`MEDIUM`** | `Data Bug` / `Architecture` | **`CONFIRMED`** | `data/gen26_production.db` (`historical_daily_bars`) | Contains only 8,199 bars from July 12, 2026 to September 10, 2026 (2 months). | Multi-year historical lookbacks fail in production, forcing engines into synthetic fallback modes. |
| **F-15** | **Overnight Entry Gap Discrepancy** | **`MEDIUM`** | `Timing Error` | **`CONFIRMED`** | Target formula vs Execution Contract | Contract specifies entry at Open $t+1$; code evaluates close-to-close ($Close[t+20] / Close[t] - 1$). | Introduces tracking error of $-0.0033\%$ mean and $\pm 8.69\%$ maximum single-stock variance per trade. |
| **F-16** | **Sharpe Ratio Annualization Scaling Distortion** | **`MEDIUM`** | `Statistical Error` | **`CONFIRMED`** | `trade_metrics()` across all research engines | Multiplied 20-day overlapping trade Sharpe by $\sqrt{252 / 20}$, assuming independent sequential 20-day blocks. | Overestimates trade-level signal precision due to MA(19) autocorrelation across daily overlapping windows. |
| **F-17** | **Inverted Sample Size in Deflated Sharpe Ratio (DSR)** | **`MEDIUM`** | `Statistical Error` / `Code Bug` | **`CONFIRMED`** | `core/statistical_validator.py:51-52` | Divides variance by `years = T / 252` instead of total observations $T$ in Mertens formula. | Artificially inflates Sharpe variance estimator by a factor of 252, distorting DSR $z$-score calculations. |
| **F-18** | **Truncation of Ezz Steel Rebar (`ESRS.CA`)** | **`MEDIUM`** | `Missing Data Artifact` | **`CONFIRMED`** | `research_v43/data/ESRS.CA_clean.parquet` | Ends on 2025-03-13 (1,263 rows). | Reduces cross-sectional breadth denominator from 27 to 26 after March 2025 without normalization. |
| **F-19** | **Yahoo Finance Auction Cross-Price Boundary Jumps** | **`LOW`** | `Data Bug` / `Legitimate Market Event` | **`CONFIRMED`** | 264 sessions across `RAYA.CA`, `BINV.CA`, `DOMT.CA`, `EXPA.CA` | Unadjusted Close cleared outside daily $[Low, High]$ due to exchange closing auction mechanisms. | Harmless to close-to-close returns, but triggers false positives in crude OHLC sanity checks. |
| **F-20** | **Unused/Dead Research Sandbox (`research_v5/`)** | **`LOW`** | `Maintainability` | **`CONFIRMED`** | `research_v5/` directory in workspace root | Incomplete sandbox containing only 1 downloader script for 10 stocks. | Creates confusion regarding the authoritative location of ongoing quantitative research. |
| **F-21** | **Full-Dataset Normalization Leakage (`BUG-03`)** | **`MEDIUM`** | `Lookahead Leakage` / `Code Bug` | **`ALREADY FIXED`** | `research_v43/engines/t6_ml_model_layer.py` | `RobustScaler` was initially fitted across entire sample before fold splitting. | Fixed in QA sweep: scaler is now strictly fitted on `X_train` and applied to `X_test`. |
| **F-22** | **Duplicate Accounting Disclosures Collision (`BUG-02`)**| **`LOW`** | `Data Bug` / `Code Bug` | **`ALREADY FIXED`** | `research_v43/engines/t3_fundamentals_valuation.py` | Engine crashed when multiple filings shared the same accounting period end date. | Fixed in QA sweep by retaining the latest filing publication timestamp. |
| **F-23** | **Stock Split Data Quality Penalty (`BUG-01`)** | **`LOW`** | `Data Bug` / `False Positive` | **`ALREADY FIXED`** | `research_v43/engines/t0_data_foundation.py` | Unadjusted price jumps from 2:1 or 10:1 splits penalized DQ scores as data corruption. | Fixed in QA sweep by computing price continuity exclusively on backward-adjusted prices. |
| **F-24** | **Production Core Protected & Frozen Invariants Preserved**| **`INFORMATIONAL`**| `System Invariant` | **`VERIFIED`** | `core/frozen_invariants.py`, `dashboard/app.py` | Cash Gate (min 10%), Allocation Cap (max 65%), and Max Position Size (10%) remain enforced. | Production trading core, live broker gates, and risk firewalls remain 100% untouched and safe. |

---
*Findings register compiled with formal severity rankings, file links, and reproducible proof.*
