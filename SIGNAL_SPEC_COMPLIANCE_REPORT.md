# SIGNAL_SPEC_COMPLIANCE_REPORT.md
# Comprehensive Signal Specification & Implementation Compliance Audit
**System:** GEN-26 Quantitative Financial Architecture  
**Locked Reference:** `research_v43/reports/phase_2_locked_specification.md` (Dated 2026-08-19)  
**Audit Context:** `RESEARCH_ONLY / SHADOW_ONLY / NON_PRODUCTION / NO_LIVE_TRADING / NO_ML`  
**Audit Date:** 2026-09-17  

---

## 1. Specification Compliance Master Matrix

| Rule | Locked Specification | Actual Implementation | Match? | Evidence | Required Action |
| :--- | :--- | :--- | :---: | :--- | :--- |
| **`BL3_Momentum`** | `Mom_20D > 0` AND `Adj_Close > SMA_50`. Sourced strictly from past data. | `(df["Mom_20D"] > 0) & (df["Adj Close"] > df["SMA_50"])` | **MATCH (100%)** | Exact reproduction in `phase1_cost_aware_baselines.py`, `phase2_market_regime.py`, and clean-room audit. | Maintain as sole authoritative empirical benchmark hurdle. |
| **`Mom_20D`** | Trailing 20-day return: `c / c.shift(20) - 1.0`. | `df["Mom_20D"] = c / c.shift(20) - 1.0` | **MATCH (100%)** | Pure trailing momentum calculation across all engines. | No change required. |
| **`SMA_50`** | 50-day simple moving average of backward-adjusted close. | `df["SMA_50"] = c.rolling(50).mean()` | **MATCH (100%)** | Valid trailing moving average in all engines. | No change required. |
| **`Breadth_AdvanceRatio` (Locked)** | Cross-sectional mean of `Pos_1D`, where `Pos_1D = (Fwd_Ret_1D > 0)`. | `df["Pos_1D"] = (df["Fwd_Ret_1D"] > 0).astype(int)` | **MATCHES SPEC (FLAWED SPEC)** | `phase_2_locked_specification.md` Section 1.3 explicitly codified `Fwd_Ret_1D`. `phase2_market_regime.py:265`. | Formally revoke Section 1.3 of locked spec; mandate `Ret_1D_Trailing`. |
| **`Breadth_AdvanceRatio` (Clean)** | Post-Phase 2.75 Amendment: `mean(Ret_1D_Trailing > 0)`. | `df["Pos_1D"] = (df["Ret_1D_Trailing"] > 0).astype(int)` | **MISMATCH VS LOCK / MATCHES P2.75** | `phase275_forensic_reset.py:262`. Clean-room verification confirms Net PF drops to 1.454 in 2025. | Adopt clean specification; acknowledge candidate failure against baseline bar. |
| **`Breadth_Osc10D`** | `rolling_mean(AdvRatio, 10) - rolling_mean(AdvRatio, 30) > 0`. | `breadth["Breadth_AdvanceRatio"].rolling(10).mean() - breadth["Breadth_AdvanceRatio"].rolling(30).mean()` | **MATCH** | Rolling difference matches; inherits temporal status of `Breadth_AdvanceRatio`. | Ensure calculation uses clean trailing breadth. |
| **`R_BULL` Regime** | `BM_Mom20D > 0.02` AND `BM_Index > SMA50` AND `SMA50 > SMA200`. | Input `BM_Index` constructed from `mean(Fwd_Ret_1D)` in Phase 2. | **SPEC MISMATCH (CONTAMINATED)** | Thresholds match, but underlying benchmark index was forward-contaminated in Phase 2. | Enforce trailing benchmark accumulation for regime classification. |
| **`R_BEAR` Regime** | `BM_Mom20D < -0.02` AND `BM_Index < SMA50`. | Same formula over forward-contaminated benchmark index. | **SPEC MISMATCH (CONTAMINATED)** | Contaminated by future return accumulation. | Recompute regime flags exclusively on trailing benchmark index. |
| **`P2_Breadth_Momentum`** | `BL3_Momentum == True` AND `Breadth_AdvanceRatio > 0.50` AND `Breadth_Osc10D > 0`. | Implemented with buggy breadth in Phase 2; clean breadth in Phase 2.75. | **SPEC MISMATCH (AMENDED)** | Original locked candidate was structurally invalid. Clean signal fails 2025 hurdle ($PF = 1.454 < 2.138$). | Officially reject `P2_Breadth_Momentum` as an alpha candidate. |
| **Secondary Signal: `P2_BullBreadth`** | `BL3_Momentum == True` AND `R_BULL == 1` AND `Breadth_AboveSMA20 > 0.55`. | `(p["BL3_Momentum"] == True) & (p["R_BULL"] == 1) & (p["Breadth_AboveSMA20"] > 0.55)`. | **MATCH** | Evaluated in Phase 2. In clean 2025 validation, Net PF drops to 1.398 (underperforming baseline 1.304 in trades). | Reject as standalone alpha; keep as risk overlay only. |
| **Tertiary Signal: `P2_Bull_Momentum`** | `BL3_Momentum == True` AND `R_BULL == 1`. | `(p["BL3_Momentum"] == True) & (p["R_BULL"] == 1)`. | **MATCH** | Evaluated in Phase 2. In clean 2025 validation, Net PF drops to 1.369. | Reject as outperforming alpha. |
| **Signal Priority & Conflicts** | `P2_Breadth_Momentum` declared primary candidate; `P2_BullBreadth` secondary. | Implemented as independent parallel columns; no conflict resolution needed. | **MATCH** | Multiple signals evaluated independently without mutual exclusion. | Retain independent evaluation structure. |
| **Entry Timing** | Signal generated at Close $t$; execution at Open $t+1$. | Target return evaluated as `Close[t+20] / Close[t] - 1.0`. | **MISMATCH** | Assumes entry at Close $t$ instead of Open $t+1$, omitting overnight gap. | Implement dual-target tracking: Target A (Close-to-Close) and Target B (Open-to-Close). |
| **Exit Timing & Holding Period** | Exit at Close $t+20$ (fixed 20 trading sessions). | `c.shift(-20) / c - 1.0` (fixed 20-bar forward shift). | **MATCH (100%)** | Holding period is exactly 20 trading days across all research engines. | No change required. |
| **Universe Rules** | 27 clean Parquet tickers listed in Section 4 of lock spec. | 27 Parquet files in `research_v43/data/`; expanded to 244 in production. | **MATCH (RESEARCH) / DIVERGENCE (PROD)** | All 27 parquets exist; `ORAS.CA` starts 2021-08; `ESRS.CA` ends 2025-03. | Acknowledge survivorship bias; flag `ORAS.CA` as illiquid. |
| **Liquidity Rules** | Dynamic slippage filter based on 20-day Average Traded Value (ATV). | `Slip_Est = clip(ATR_Pct * 0.0012 * sqrt(1M / ATV), 0.10%, 0.50%)`. | **MATCH** | Implemented as specified; breaks down on `ORAS.CA` (96.32% zero volume). | Apply fixed 50 bps slippage cap for illiquid/zero-volume constituents. |
| **Position Weighting** | Unconstrained 1 unit per trade (Research); Slot cap 10% (Production). | Research code runs unconstrained pooling; Phase 2.5 ran calendar portfolio. | **PARTIAL MATCH** | Research trade metrics treat trades independently; MTM portfolio restricts slots. | Maintain distinct reporting: trade-level unconstrained vs portfolio-level MTM. |
| **Benchmark Construction** | Equal-weight index of universe constituents (Base = 1000). | Phase 2 accumulated `Fwd_Ret_1D`; Phase 2.75 accumulated `Ret_1D_Trailing`. | **SPEC MISMATCH (PHASE 2)** | Benchmark in Phase 2 was forward-looking; clean in Phase 2.75. | Mandate trailing return accumulation for all benchmark series. |
| **Cost Assumptions** | 0.90% round-trip ($0.45\%$ buy $+ 0.45\%$ sell) base case. | `Net_Ret = Gross_Ret - 0.0090`. Phase 1 reported Gross PF as Net PF. | **REPORT MISMATCH** | Costs subtracted linearly, but `trade_metrics()` reported `gw / gl` (Gross PF). | Report both Gross PF and True Net PF explicitly. |
| **Risk Gates** | Production: Cash Gate $\ge 10\%$, Exposure $\le 65\%$, Pos Size $\le 10\%$. | Enforced in `core/frozen_invariants.py` and `dashboard/app.py`. | **MATCH (100%)** | Production core strictly enforces all three invariants. | Keep 100% frozen and untouched. |

---
*Signal specification compliance audit completed: all rules cross-referenced across locked specification, executable code, and report outputs.*
