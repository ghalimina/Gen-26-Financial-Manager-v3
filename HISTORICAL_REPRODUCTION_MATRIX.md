# HISTORICAL_REPRODUCTION_MATRIX.md
# Comprehensive Historical Reproduction & Reconciliation Matrix
**System:** GEN-26 Quantitative Financial Architecture  
**Audit Scope:** Verification of Key Claims from Historical Reports against Independent Clean-Room Execution  
**Audit Context:** `RESEARCH_ONLY / SHADOW_ONLY / NON_PRODUCTION / NO_LIVE_TRADING / NO_ML`

---

## 1. Reproduction Status Overview

Using the current repository data and independent clean-room code, we evaluated all primary claims made across historical research reports (Phase 1, Phase 2, Phase 2.5, Phase 2.75, Phase 2.6, and Production Audits).

Every claim is categorized under one of seven strict statuses:
* **`REPRODUCED`**: Exact mathematical or statistical reproduction confirmed.
* **`REPRODUCED WITH EXPECTED DIFFERENCE`**: Reconstructed with minor documented boundary or calendar differences.
* **`INVALID HISTORICAL RESULT`**: Historical result confirmed to be invalid due to code bug, lookahead leakage, or false premise.
* **`CURRENT CODE DIFFERENT`**: Historical claim cannot run on `main` because the research engine was purged from the active branch.
* **`NOT REPRODUCED`**: Executable code produces contradictory numbers.
* **`DATA DIFFERENCE`**: Discrepancy caused by dataset versioning or missing constituent bars.
* **`UNRESOLVED`**: Insufficient telemetry or data provenance to verify claim.

---

## 2. Historical Claims Reproduction Matrix

| Historical Result / Metric Claim | Historical Report & File Reference | Historical Value Claimed | Current Independent Reproduction | Discrepancy | Forensic Explanation | Audit Status |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| **Phase 1 Baseline (`BL3_Momentum`) Dev PF** | `phase_1_report.md`<br>`phase_2_75_report.md` | Net $PF = 1.821$<br>Gross $PF = 2.212$ | Net $PF = \mathbf{1.821}$<br>Gross $PF = \mathbf{2.212}$ | **0.000** | Exact 100% reproduction in clean-room engine ($N = 14,844$, Win Rate = $51.35\%$). | **`REPRODUCED`** |
| **Phase 1 Baseline Pooled Hurdle Bar** | `MASTER_PROJECT_INVENTORY.md`<br>`phase_2_locked_specification.md` | $PF = 2.138$<br>Sharpe = $0.668$ | Gross $PF = 2.212$<br>Net $PF = 1.821$ | $+0.317$ | $2.138$ represents fold-averaged gross profit factor, not true net profit factor. | **`REPRODUCED WITH EXPECTED DIFFERENCE`** |
| **Phase 2 Locked Buggy Signal (`P2_Breadth_Mom`) Dev PF** | `phase_2_locked_specification.md`<br>`phase_2_75_report.md` | Net $PF = 2.605$<br>Sharpe = $1.049$ | Net $PF = \mathbf{2.605}$<br>Sharpe = $\mathbf{1.049}$ | **0.000** | Exact reproduction of buggy forward-looking breadth signal ($N = 3,477$, Win Rate = $57.23\%$). | **`INVALID HISTORICAL RESULT`** *(Leaked)* |
| **Phase 2 Discovery Initial Reported PF** | `phase_2_report.md`<br>`phase_2_locked_specification.md` | $PF = 2.914$<br>$N = 3,922$ | Gross $PF = 3.180$<br>Net $PF = 2.605$ | Multi-split variance | Initial report pooled all folds including 2026 data. | **`INVALID HISTORICAL RESULT`** *(Leaked & Unsealed)* |
| **Phase 2.5 Validation Collapse (`P2_Breadth_Mom` Buggy)** | `phase_25_report.md`<br>`phase_2_75_report.md` | Net $PF = 1.592$<br>Sharpe = $0.524$ | Net $PF = \mathbf{1.592}$<br>Sharpe = $\mathbf{0.524}$ | **0.000** | Exact reproduction of out-of-sample collapse on 2025 validation year ($N = 694$). | **`REPRODUCED`** |
| **Phase 2.75 Clean PIT Reconstruction Dev PF** | `phase_2_75_report.md` (Table 2) | Net $PF = 2.000$<br>Sharpe = $0.762$ | Net $PF = \mathbf{2.000}$<br>Sharpe = $\mathbf{0.763}$ | **0.000** | Exact reproduction of purged signal using trailing breadth ($N = 3,838$, Win Rate = $52.76\%$). | **`REPRODUCED`** |
| **Phase 2.75 Clean PIT Validation 2025 PF** | `phase_2_75_report.md` (Table 2) | Net $PF = 1.454$<br>Sharpe = $0.424$ | Net $PF = \mathbf{1.454}$<br>Sharpe = $\mathbf{0.424}$ | **0.000** | Exact reproduction of clean signal on 2025 validation ($N = 770$, Win Rate = $55.71\%$). | **`REPRODUCED`** |
| **Newey-West HAC Significance (2025 Validation)** | `phase_2_5_final_verdict.md` (Section 7) | $t_{\text{HAC}} = 2.094$<br>$p = 0.0363$ | $t_{\text{HAC}} = \mathbf{2.857}$<br>$p = \mathbf{0.0043}$ | $\Delta t = +0.76$ | Both confirm $p < 0.05$ statistical significance. Recomputed uses full 2025 calendar bars ($N = 770$ vs $632$). | **`REPRODUCED WITH EXPECTED DIFFERENCE`** |
| **Disjoint Offset Median PF (2025 Validation Alone)** | `phase_2_5_final_verdict.md` (Claim: $2.197$) | Median $PF = 2.197$ across offsets | Median $PF = \mathbf{1.591}$<br>(2025 alone) | **$-0.606$** | Historical report evaluated disjoint offsets on pooled 2020–2025 data. Isolated 2025 yields median $PF = 1.591$. | **`NOT REPRODUCED (ON 2025 ALONE)`** |
| **Disjoint Offsets Beating Baseline Bar (2025 Alone)** | `phase_2_5_final_verdict.md` (Claim: 100% pass) | $100\%$ pass hurdle | **25.0% pass**<br>(5 / 20 offsets) | **$-75.0\%$** | On 2025 validation alone, 15 out of 20 offsets ($75\%$) fail to reach the $PF = 2.138$ baseline bar. | **`NOT REPRODUCED`** |
| **Macro Devaluation Profit Concentration (2022)** | `phase_2_75_report.md` (Section 6) | 2022 contributes $39.9\%$ of total dev profit | 2022 Net $PF = 3.612$<br>Profit Share = $\mathbf{39.9\%}$ | **0.000** | Exact reproduction. Confirms heavy dependency on the 2022 currency floatation trend. | **`REPRODUCED`** |
| **Non-2022 Performance Attenuation** | `phase_2_5_final_verdict.md` (Section 9) | Excluding 2022:<br>Net $PF = 2.041$ | Excluding 2022:<br>Net $PF = \mathbf{2.041}$ | **0.000** | Exact reproduction on pooled 2020–2025 excluding 2022 ($N = 3,661$). | **`REPRODUCED`** |
| **Economic Break-Even Friction** | `phase_2_75_report.md` (Section 5)<br>`phase_2_5_final_verdict.md` | Break-even at $3.175\%$ to $4.003\%$ RT | Break-even at $\mathbf{3.175\%}$ to $\mathbf{4.003\%}$ RT | **0.000** | Confirmed via Brent root-finding. Strategy survives costs up to $3.17\%$ in dev and $4.00\%$ overall. | **`REPRODUCED`** |
| **Calendar-Time Portfolio CAGR & Sharpe** | `phase_2_5_final_verdict.md` (Section 8) | $\text{CAGR} = +27.69\%$<br>Sharpe = $1.188$<br>Max DD = $-23.37\%$ | Replicated via MTM simulation script | Expected precision | Verified against portfolio equity curve ($1.0\text{M} \to 4.109\text{M}$ EGP). | **`REPRODUCED`** |
| **Historical Delisting Survivorship Resolution** | `phase_2_6_survivorship_reconstruction.md` | Survivorship resolved via 8 delisted stocks | Debunked: All 8 stocks are actively listed | **FATAL PREMISE** | External exchange verification confirmed none of the 8 stocks were delisted. | **`INVALID HISTORICAL RESULT`** |
| **Sealed Final Holdout Untouched Status** | `phase_2_locked_specification.md`<br>`phase_2_75_report.md` | 2026 is 100% sealed & untouched | 2026 was evaluated in Phase 2 Fold 5 | **PRIOR EXPOSURE** | `phase_2_annual_breakdown.csv` contains 2026 results ($N = 577$, $PF = 3.084$). | **`INVALID HISTORICAL RESULT`** |
| **Production Realized Statistical Edge** | `data/realized_statistical_edge.json`<br>`core/edge_verifier.py` | $PF = 2.45$, Hit Rate = $58\%$ | Computed on `np.random.normal` (seed 42) | Synthetic Mock | Production validator uses synthetic random Gaussian walks rather than real market data. | **`CURRENT CODE DIFFERENT`** *(Synthetic)* |
| **Parametric Plateau Stability Confirmation** | `core/statistical_validator.py` | `PARAMETRIC_PLATEAU_CONFIRMED` | Sourced from hardcoded Python dict | Mock Dictionary | Hardcoded dictionary with values 1.98 to 2.138. Zero market data input. | **`CURRENT CODE DIFFERENT`** *(Synthetic)* |

---

## 3. Forensic Analysis of Non-Reproduced & Divergent Claims

### A. The Disjoint Offset Discrepancy on Validation 2025
* **The Historical Narrative (`phase_2_5_final_verdict.md`):**
  Claimed that the clean strategy was definitively vindicated because "100% of 20 disjoint offsets achieved positive net returns with a median Profit Factor of 2.197, matching the Phase 1 Baseline bar".
* **The Forensic Truth Discovered:**
  The historical script pooled the **entire 2020–2025 dataset** when running the 20 offsets. Because 2020–2024 contained massive gains from the 2022 currency devaluation, pooling diluted the isolated 2025 performance.
* **The Isolated 2025 Reality:**
  When disjoint offsets are evaluated **strictly on the 2025 validation period**:
  * The median Net Profit Factor drops to **`1.591`**.
  * **15 out of 20 offsets (75.0%) fail to reach the baseline bar ($PF = 2.138$)**.
  * While 18 out of 20 offsets (90.0%) remain positive ($PF > 1.00$), the claim of matching or beating the baseline hurdle is **untrue for 75% of execution phases**.

### B. The 2026 Holdout Pre-Contamination Reality
* **The Historical Narrative:**
  Every report from Phase 2.5 onward proclaimed: `"Sealed Final Holdout (2026): 100% SEALED & UNTOUCHED"`.
* **The Forensic Truth Discovered:**
  Commit `39844ee` and report `phase_2_report.md` (dated 2026-08-18) ran TimeSeriesSplit through 2026-07-19 and published detailed 2026 performance breakdowns. `P2_Breadth_Momentum` was chosen as the winning candidate specifically because it generated $PF = 3.084$ during 2026. The holdout was retroactively declared "sealed" on August 19, *after its performance had already been observed*.

---
*Historical reproduction matrix verified via independent clean-room execution and cross-table reconciliation.*
