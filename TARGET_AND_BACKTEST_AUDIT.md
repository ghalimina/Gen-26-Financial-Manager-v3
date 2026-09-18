# TARGET_AND_BACKTEST_AUDIT.md
# Comprehensive Forward Target, Trade Construction & Backtest Engine Forensic Audit
**System:** GEN-26 Quantitative Financial Architecture  
**Audit Scope:** Entry/Exit Execution Contracts, Return Construction, Overlapping Trade Units, Capital Assumptions & Compounding Artifacts  
**Audit Context:** `RESEARCH_ONLY / SHADOW_ONLY / NON_PRODUCTION / NO_LIVE_TRADING / NO_ML`

---

## 1. Executive Summary: The True Nature of "Trades" in GEN-26

A foundational finding of this forensic audit is that **the reported "trade counts" ($N = 17,000$ in Phase 1, $N = 3,922$ in Phase 2, and $N = 770$ in Phase 2.5 Validation) DO NOT represent executed trades, independent investment bets, or portfolio transactions**.

They represent **daily stock-date signal occurrences** evaluated over overlapping 20-trading-day forward horizons.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             WHAT A "TRADE" ACTUALLY REPRESENTS IN RESEARCH                       │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Reported Count (N)  │ Daily Cross-Sectional Signal Flags (Stock-Date Pairs where Signal == True)  │
│ Holding Horizon     │ Fixed 20 Trading Sessions (~28 Calendar Days)                              │
│ Same-Stock Overlap  │ UNRESTRICTED: A stock signaling on 15 consecutive days opens 15 parallel   │
│                     │ 20-day positions in the same asset simultaneously.                         │
│ Cross-Sectional     │ UNRESTRICTED: Up to 22 different stocks signal on the exact same date.     │
│ Portfolio Capital   │ UNBOUNDED: Assumes infinite capital (1 theoretical unit per signal).       │
│ Independence        │ FALSE: Consecutive observations share 19 out of 20 trading sessions.       │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Trade Execution Contract vs Code Reality

| Parameter | Specification Contract (Locked Doc) | Executable Code Implementation | Forensic Finding & Discrepancy Analysis |
| :--- | :--- | :--- | :--- |
| **Signal Date ($t$)** | Close of session $t$ (14:30 Cairo time). | Sliced at index date $t$. | **MATCH.** Sourced after session close. |
| **Information Set at $t$** | Only historical prices $\le t$. | Phase 2 used `Fwd_Ret_1D` in Breadth. | **CRITICAL LOOKAHEAD IN PHASE 2.** Fixed in Phase 2.75 to trailing returns. |
| **Entry Date** | Next trading session ($t+1$). | Day $t$ (Implicitly). | **TIMING GAP.** Slices target as $Close_{t+20} / Close_t - 1.0$. |
| **Entry Price** | Opening price on day $t+1$ ($Open_{t+1}$). | Closing price on day $t$ ($Close_t$). | **OVERNIGHT GAP OMITTED.** Assumes fill at Close $t$. Mean gap: $-0.0033\%$; extreme variance $\pm 8.69\%$. |
| **Exit Date** | Day $t+20$ (20th trading session). | Day $t+20$ (`shift(-20)`). | **MATCH.** Exactly 20 Egyptian trading sessions forward. |
| **Exit Price** | Closing price on day $t+20$ ($Close_{t+20}$).| Closing price on day $t+20$. | **MATCH.** Evaluates close-to-close return. |
| **Holding Horizon** | 20 Trading Days (Fixed). | 20 Trading Days (Fixed). | **MATCH.** No intraday stops or profit targets in research engine. |
| **Gross Return Formula** | $\frac{Close_{t+20} - Open_{t+1}}{Open_{t+1}}$ | $\frac{Close_{t+20} - Close_t}{Close_t} = \text{Fwd\_Ret\_20D}$ | **FORMULA DISCREPANCY.** Uses close-to-close forward return. |
| **Cost Application** | Deducted from each trade. | Linear subtraction: $Net = Gross - 0.0090$. | **DISCREPANCY IN REPORTING.** Net return was computed, but Profit Factor was reported as gross wins over gross losses. |
| **Deduplication** | None specified. | No deduplication implemented. | **HIGH REDUNDANCY.** Identical positions opened every session during trends. |
| **Position Sizing** | Equal-weight (1 unit). | Equal-weight (1 unit). | **UNBOUNDED CAPITAL.** Requires expanding balance sheet to hold up to 22 concurrent positions. |
| **Drawdown Logic** | Portfolio Mark-to-Market equity. | Sequential compounding: $\prod (1 + r_i)$. | **SEVERE METHODOLOGICAL ARTIFACT.** Multiplies overlapping trade returns sequentially, producing fake -100% drawdown. |

---

## 3. The Compounding Distortion Artifact (`BUG-05`)

In `phase1_cost_aware_baselines.py` and `phase2_market_regime.py`, maximum drawdown was calculated as:
```python
cum = (1 + net).cumprod()
dd = (cum / cum.cummax() - 1)
mdd = dd.min()
```
### Why This Calculation Was Catastrophically Flawed:
1. `net` is an array of trade returns ordered by date and ticker:
   $$r_1, r_2, r_3, \dots, r_N$$
   Where $r_1, r_2, \dots, r_{20}$ often occur on the **exact same calendar day**.
2. Taking `(1 + net).cumprod()` mathematically assumes that the investor:
   - Invests 100% of the entire portfolio equity into Trade 1.
   - Cashes out 20 days later.
   - Reinvests 100% of the new equity into Trade 2.
   - Repeats this sequentially across all 14,844 trades!
3. If 15 stocks experience a market correction on the same day and each drops $-5\%$, sequential multiplication compounds them as:
   $$(1 - 0.05)^{15} = 0.463 \implies -53.7\% \text{ Drawdown on a single day!}$$
4. Over thousands of trades, any cluster of losing trades drives cumulative equity to near zero ($0.0006$), creating an artificial reported drawdown of **`-99.94%` to `-100.0%`**.
5. **The Realistic Fix (Phase 2.5 Calendar-Time Portfolio):**
   When the portfolio is simulated realistically using calendar time (daily Mark-to-Market tracking, 10% maximum slot cap per stock, 65% total allocation cap), the true maximum portfolio drawdown over 2020–2025 is **`-23.37%`** (CAGR $+27.69\%$, Daily Sharpe $1.188$).

---

## 4. Trade-Level Output Data Dictionary

Every trade-level output record generated by the research engines contains the following columns:

| Column Name | Data Type | Formula / Origin | Financial Interpretation & Audit Caveats |
| :--- | :---: | :--- | :--- |
| `Date` | Datetime64 | Sourced from `panel.index` | The signal generation date $t$ (as of market close). |
| `Ticker` | String | EGX Ticker Symbol (e.g. `COMI.CA`) | The constituent equity triggering the signal. |
| `Adj Close` | Float64 | Historical adjusted price at $t$ | Reference entry price used by the backtest engine. |
| `Mom_20D` | Float64 | `c[t] / c[t-20] - 1.0` | 20-session historical trailing momentum. |
| `SMA_50` | Float64 | `c.rolling(50).mean()` | 50-session simple moving average. |
| `BL3_Momentum` | Boolean | `(Mom_20D > 0) & (c > SMA_50)` | Phase 1 baseline momentum condition. |
| `Breadth_AdvanceRatio`| Float64 | Cross-sectional mean advancing % | Market participation filter (Buggy in P2, Clean in P2.75). |
| `Breadth_Osc10D` | Float64 | 10D MA - 30D MA of AdvanceRatio | Breadth momentum trend oscillator. |
| `P2_Breadth_Momentum` | Boolean | `BL3 & (AdvRatio > 0.50) & (Osc > 0)` | Primary strategy signal flag. |
| `Fwd_Ret_20D` | Float64 | `c[t+20] / c[t] - 1.0` | **Gross forward 20-trading-day return.** Target label. |
| `Net_Ret_20D` | Float64 | `Fwd_Ret_20D - 0.0090` | **Net forward return after 0.90% RT friction.** |
| `is_winner` | Boolean | `Net_Ret_20D > 0` | Trade success indicator. |
| `Cost_Model_RT` | Float64 | `0.0035 + 2 * Slip_Est` | Dynamic estimated transaction friction. |

---

## 5. Overlap & Concurrency Analysis

To evaluate whether trade records can be treated as independent observations, we analyze the concurrency distribution on the 2025 Validation set ($N = 770$ trade records):

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 2025 VALIDATION CONCURRENCY PROFILE                              │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Total Trade Records (N)      │ 770 observations                                                  │
│ Unique Signal Dates          │ 56 trading sessions                                               │
│ Average Concurrent Equities  │ 13.75 stocks per active signal date                               │
│ Maximum Concurrent Equities  │ 22 stocks (out of 27 universe stocks) on 2025-06-18               │
│ Minimum Concurrent Equities  │ 1 stock                                                           │
│ Signal Clustering Index      │ Highly clustered: Signals occur in tight cross-sectional waves    │
│                              │ during market-wide breakouts.                                     │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Critical Statistical Implication:
Because an average of **13.75 stocks trigger signals on the exact same date**, and each trade is held for **20 overlapping sessions**, these 770 observations contain massive cross-sectional and temporal correlation. 

Standard $t$-tests and uncorrected standard errors ($SE = \sigma / \sqrt{N}$) dramatically underestimate variance by assuming $N = 770$ independent bets. The effective number of independent macroeconomic bets in 2025 is closer to **$50$ to $56$**, requiring Newey-West HAC adjustments and cluster-robust inference.

---
*Target and backtesting mechanics audited and grounded in exact code routines and empirical distributions.*
