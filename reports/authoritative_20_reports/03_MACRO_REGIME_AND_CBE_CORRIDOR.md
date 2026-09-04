# 03 — Macroeconomic Regime, CBE Interest Corridor & Hurdle Rates
**GEN-26 Macroeconomic Barometer & Cost of Capital Invariants**
*Last Synchronized: 2026-08-30 14:19:12*

---

## 1. Central Bank of Egypt (CBE) Invariants (SSoT)
- **Overnight Deposit Rate ($R_f$)**: **19.00%** (Risk-free overnight cash baseline).
- **Overnight Lending Rate**: **20.00%**.
- **Headline Inflation (CPI YoY)**: **14.90%**.
- **USD/EGP Official FX Parity**: **50.20 EGP**.

---

## 2. Rigorous Economic Dual-Tier Hurdle Formulation
To avoid target-chasing bias and unrealistic return assumptions, the platform establishes two distinct economic benchmarks:

1. **Strategy Operational Hurdle Rate ($H_{\text{operational}}$)**:
   $$H_{\text{operational}} = R_f + \text{Roundtrip Frictions} = 19.00\% + 0.35\% = \mathbf{19.35\%}$$
   - *(Note: Assuming standard institutional annual portfolio turnover of $2\times$/year, total annual trading frictions equal $2 \times 0.35\% = 0.70\%$, making the annualised breakeven hurdle $\mathbf{19.70\%}$)*.
   - Any quantitative model generating expected return $> 19.35\%$ produces positive economic alpha (EVA) over holding risk-free cash.

2. **Realistic Target Strategy Nominal Return**:
   $$\text{Target Return} = R_f + \text{Alpha Hurdle} = 19.00\% + (7.0\% \text{ to } 9.0\%) = \mathbf{26.00\% - 28.00\%}$$
   - Generates a Sharpe ratio of **1.25 to 1.45** without forced risk escalation.

3. **Institutional Cost of Equity ($K_e$) (Damodaran Emerging Market Model)**:
   $$K_e = R_f + (\beta \times \text{ERP}_{\text{mature}}) + \text{CRP} = 19.00\% + (1.00 \times 4.60\%) + 7.10\% = \mathbf{30.70\%}$$
   - Used exclusively for fundamental DCF corporate valuations, not as a mandatory daily trade hurdle.
