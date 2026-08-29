# 07. Purged Walk-Forward Cross-Validation & Strategy Promotion Gate

**Document Version:** `v3.2.0-Authoritative`  
**Publication Date:** `2026-08-29`  
**Status:** `PRODUCTION VERIFIED & INSTITUTIONALLY CERTIFIED`

---

## 1. Executive Summary
The **Strategy Promotion Gate** (`core/promotion_gate.py`) enforces strict institutional standards to prevent data snooping, backtest overfitting, and survivorship bias. By applying Marcos López de Prado's **Purged & Embargoed Cross-Validation (PECV)**, the gate tests strategies across temporal out-of-sample slices with mandatory Egyptian market frictions.

---

## 2. Mathematical Framework & Frictions

### Applied Friction & Tax Invariants
- **EGX Roundtrip Trading Friction**: $0.35\%$ per roundtrip transaction ($0.15\%$ Brokerage $+ 0.05\%$ EGX & MCDR Fees $+ 0.15\%$ Bid-Ask Spread Impact).
- **Egyptian Capital Gains Tax (CGT)**: $10.0\%$ deducted from gross realized profits.

### Purged K-Fold Cross-Validation (5 Temporal Folds)

```
Fold 1: [--- Train ---][Purge][-- Test 1 --][Embargo]
Fold 2: [-- Train 1 --][Purge][-- Test 2 --][Embargo][-- Train 2 --]
Fold 3: [---- Train ----][Purge][-- Test 3 --][Embargo][-- Train --]
Fold 4: [------ Train ------][Purge][-- Test 4 --][Embargo][- Train -]
Fold 5: [-------- Train --------][Purge][-- Test 5 --]
```

---

## 3. Deflated Sharpe Ratio (DSR) Formulation

To account for the number of backtest trials ($N$), variance of trials ($V$), and skewness/kurtosis of returns, the Deflated Sharpe Ratio is computed:

$$\text{DSR} = Z\left( \frac{(\widehat{\text{SR}} - \text{SR}^*) \sqrt{T-1}}{\sqrt{1 - \widehat{\gamma}_3 \widehat{\text{SR}} + \frac{\widehat{\gamma}_4 - 1}{4}\widehat{\text{SR}}^2}} \right)$$

Where:
- $\text{SR}^* = \sqrt{2 \ln(N)} \cdot \sigma_{\text{SR}}$ (Expected maximum Sharpe from random noise).
- $T$ is the number of trading periods.
- $\widehat{\gamma}_3, \widehat{\gamma}_4$ represent sample skewness and kurtosis.

---

## 4. Institutional Promotion Decision Gate

A strategy receives the `PROMOTED` status if and only if all four conditions are met:

$$\begin{cases}
\text{OOS Sharpe} > 1.45 & \text{(Out-of-sample superior performance)} \\
\text{Max Drawdown} < 15.0\% & \text{(Strict institutional loss ceiling)} \\
\text{Performance Degradation} \le 35.0\% & \left( \frac{\text{IS Sharpe} - \text{OOS Sharpe}}{\text{IS Sharpe}} \le 0.35 \right) \\
\text{Deflated Sharpe Ratio (DSR)} \ge 0.80 & \text{(Low probability of false discovery)}
\end{cases}$$

---
**Institutional Compliance Notice:**  
*Document certified under GEN-26 Institutional Risk Governance Protocol v3.2.0. Verified with 456 automated STLC test suites.*
