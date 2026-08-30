# 03 — Macroeconomic Regime, CBE Corridor & Hurdle Rates
**GEN-26 Quantitative Autonomous Platform | Version 3.2.0-Authoritative | Institutional Whitepaper**

---

## Executive Summary
Macroeconomic regime modeling in GEN-26 is anchored directly in the official monetary policy rates established by the **Central Bank of Egypt (CBE)**, the headline inflation statistics from CAPMAS, and the real-time interbank foreign exchange market.

---

## 1. Central Bank of Egypt (CBE) Monetary Policy Rates

The canonical macroeconomic invariants of the platform are:
- **CBE Overnight Deposit Rate ($R_f$)**: **19.00%**
- **CBE Overnight Lending Rate**: **20.00%**
- **CBE Official Inflation (Headline CPI YoY)**: **14.90%**
- **USD / EGP Interbank Exchange Rate**: **50.20**

---

## 2. Institutional Hurdle Rate & Return Formulation

Any quantitative equity strategy deployed in Egypt must hurdle the sovereign risk-free return adjusted for currency and equity risk premiums:

$$\text{Hurdle Rate}_{\text{CRP}} = R_f (19.00\%) + \text{Inflation} (14.90\%) \times 0.50 + \text{Equity Risk Premium} (4.25\%) = \mathbf{30.70\%}$$

### Comparative Alpha Metrics:
- **Cost of Equity Hurdle Rate**: **30.70%**
- **Benchmark EGX30 Annualized Return**: **24.50%**
- **Strategy Target Nominal Annualized Return**: **36.80%** (Net of 0.35% roundtrip friction and dynamic slippage)
- **Net Economic Alpha above Hurdle Rate**: **+6.10%** ($36.80\% - 30.70\% = +6.10\%$)
- **Net Alpha above EGX30 Benchmark**: **+12.30%** ($36.80\% - 24.50\% = +12.30\%$)

Any candidate model achieving an annualized expected return below **30.70%** is rejected by the governance gate as economically non-viable.

---

## 3. Macro Regime State Machine

The platform detects 4 distinct macroeconomic regimes using Hidden Markov Models (HMM) and interbank liquidity feeds:
1. **RATE_HIKING_CYCLE**: Tight monetary policy, favoring high-cash dividend yield equities.
2. **HIGH_INFLATION_EXPANSION**: Pricing power stocks and commodity exporters outperform.
3. **MONETARY_EASING_CYCLE**: Credit expansion, favoring real estate and leveraged industrials.
4. **DEVALUATION_PRESSURE**: High London GDR arbitrage activity, favoring USD-revenue earners.
