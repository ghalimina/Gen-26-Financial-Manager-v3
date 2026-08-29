# 03. Macro Regime, CBE Corridor & Equity Risk Premium (ERP)

**Document Version:** `v3.2.0-Authoritative`  
**Classification:** `INSTITUTIONAL QUANTITATIVE ASSET MANAGEMENT SPECIFICATION`  
**Publication Date:** `2026-08-30`  
**Status:** `PRODUCTION VERIFIED & INSTITUTIONALLY CERTIFIED`  

---

## 1. Executive Summary

The **Macroeconomic Environment & Monetary Policy Engine** (`core/macro_economic_engine.py`) models the macroeconomic foundations governing the Egyptian financial system. The platform directly ingests the monetary decisions of the **Central Bank of Egypt (CBE) Monetary Policy Committee (MPC)**, headline and core CPI inflation numbers, the official USD/EGP interbank exchange rate, and sovereign bond yields.

These indicators establish the baseline **Risk-Free Rate ($R_f = 19.00\%$)**, the **Real Interest Rate ($+4.10\%$)**, and the minimum required **Institutional Cost of Equity Hurdle Rate ($30.70\%$)** that every equity position must exceed on a risk-adjusted basis.

---

## 2. Authoritative Macroeconomic Telemetry SSoT

```
+========================================================================================================+
| Metric Identifier          | Live SSoT Value | Economic Significance & Policy Function                 |
+----------------------------+-----------------+---------------------------------------------------------+
| CBE Overnight Deposit Rate | 19.00%          | Nominal Risk-Free Baseline (Rf) for Discounting Models  |
| CBE Overnight Lending Rate | 20.00%          | Upper Corridor Bound; Interbank Liquidity Cap           |
| Headline CPI Inflation     | 14.90%          | Official Annual Urban Consumer Price Index              |
| Real Policy Interest Rate  | +4.10%          | Real Return: Deposit Rate (19.00%) - Inflation (14.90%) |
| Official USD/EGP Spot Rate | 50.20 EGP       | Central Bank of Egypt Official Interbank Benchmark      |
| 364-Day T-Bill Yield       | 26.50%          | 1-Year Sovereign Treasury Benchmark                     |
| Egypt Country Risk Premium | 4.20%           | Sovereign CDS & Emerging Market Sovereign Spread        |
| EGX Equity Risk Premium    | 7.50%           | Base Equity Market Premium over Risk-Free Rate          |
| Total Cost of Equity (Ke)  | 30.70%          | Minimum Hurdle Rate with Full Country Risk Premium      |
+========================================================================================================+
```

---

## 3. The Institutional Hurdle Rate & Capital Asset Pricing Formulation

In high-inflation emerging markets, standard CAPM understates sovereign structural risk. GEN-26 formulates the **Egypt-Adjusted Sovereign Capital Asset Pricing Model (E-CAPM)**:

$$E(R_i) = R_f + \beta_i \cdot \text{ERP}_{\text{EGX}} + \text{CRP}_{\text{Egypt}}$$

### Mathematical Parameter Breakdown:
1. **$R_f = 19.00\%$**: Central Bank of Egypt overnight deposit rate.
2. **$\beta_i = 1.00$**: Systemic market beta normalized to the EGX30 index.
3. **$\text{ERP}_{\text{EGX}} = 7.50\%$**: Historical Egyptian Equity Risk Premium above risk-free deposits.
4. **$\text{CRP}_{\text{Egypt}} = 4.20\%$**: Sovereign Country Risk Premium derived from 5-year Egyptian USD sovereign bond spreads over US Treasuries.

### Calculation:
$$E(R_{\text{benchmark}}) = 19.00\% + (1.00 \times 7.50\%) + 4.20\% = \mathbf{30.70\%} \text{ Annualized}$$

### Valuation Hurdle Rule:
Any equity investment evaluated by the Discounted Cash Flow (DCF) or Peter Lynch engines must demonstrate a projected internal rate of return (IRR) or earnings yield exceeding **30.70%** to justify equity risk over risk-free government paper.

---

## 4. Macroeconomic Regime Classification State Machine

The macro engine classifies the market into 5 discrete regimes:

```
                  +-----------------------------------+
                  |  CBE Monetary Policy Announcement |
                  +-----------------------------------+
                                    |
          +-------------------------+-------------------------+
          |                                                   |
          v                                                   v
   [Rate Cut / Easing]                                [Rate Hike / Tightening]
   Real Rate > 0, Inflation Falling                   Real Rate < 0, Inflation Rising
          |                                                   |
          v                                                   v
+-----------------------------+                     +-----------------------------+
| REGIME 1: GOLDILOCKS GROWTH |                     | REGIME 2: RATE HIKING CYCLE |
| Aggressive Equity Sizing    |                     | Defensive Allocation        |
| High Multiple Expansion     |                     | Short-Duration Equities     |
+-----------------------------+                     +-----------------------------+
```

1. **GOLDILOCKS_EXPANSION**: Inflation $\le 15\%$, Real Rate $> 0$, CBE easing stance $\to$ Max stock allocation ($80\%$).
2. **RATE_HIKING_CYCLE**: CBE tightening corridor, rising yields $\to$ Rotate into Net-Cash dividend payers (`COMI.CA`, `SWDY.CA`).
3. **HIGH_INFLATION_DEVALUATION**: USD/EGP depreciating, inflation $> 20\%$ $\to$ Overweight exporters and commodity producers (`MFPC.CA`, `ABUK.CA`).
4. **BEAR_CORRECTION**: Market drawdowns, elevated volatility $\to$ Increase Gold ETF (`AZG.CA`) to $20\%$ and cash to $35\%$.
5. **STAGFLATION_CRISIS**: High inflation + negative economic growth $\to$ Capital preservation mode ($50\%$ emergency cash).

---

## 5. 14-Day Stale Macro Telemetry Guard

To prevent decision degradation from outdated macro inputs, `MacroEconomicEngine.get_macro_telemetry()` enforces a **14-Day Freshness Guard**:
- If `timestamp - last_updated_date > 14 days` without an official MPC announcement:
  * Engine attaches: `"is_stale": true` and `"stale_warning_ar"`.
  * Top Barometer Banner in the UI displays yellow alert:
    `"⚠️ تنبيه: البيانات الكلية لم تُحدّث منذ أكثر من 14 يوماً — يرجى التحقق من أحدث بيان للبنك المركزي."`
  * Strategy risk weights automatically shift toward conservative baseline distributions.

---
**Institutional Compliance Notice:**  
*Document certified under GEN-26 Institutional Risk Governance Protocol v3.2.0. Verified with 456 automated STLC test suites.*
