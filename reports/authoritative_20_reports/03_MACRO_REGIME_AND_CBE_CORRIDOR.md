# 03. Macro Regime, CBE Corridor & Equity Risk Premium (ERP)

## 1. Macroeconomic Context & Official Data
The GEN-26 Macroeconomic Barometer (`core/macro_risk_manager.py`) tracks the monetary policy parameters set by the Monetary Policy Committee (MPC) of the Central Bank of Egypt (CBE), along with headline inflation, foreign exchange rates, and sovereign treasury yields.

---

## 2. Official Telemetry Ingestion Metrics

| Macro Metric | Official Rate / Value | Regulatory Authority | Quantitative Impact on EGX Equities |
| :--- | :--- | :--- | :--- |
| **CBE Overnight Lending Rate** | **$19.00\%$** | Central Bank of Egypt (MPC) | High hurdle rate; elevates Cost of Capital ($WACC$) |
| **CBE Overnight Deposit Rate** | **$18.00\%$** | Central Bank of Egypt (MPC) | Risk-free rate floor ($R_f$) for cash holdings |
| **Headline Annual Inflation** | **$14.90\%$** | CAPMAS / CBE Disclosures | Positive real interest rate environment ($+3.10\%$) |
| **USD/EGP Official Spot Rate** | **$50.20$ EGP** | Interbank Market / CBE | Benchmark for London GDR arbitrage parity |
| **91-Day T-Bill Yield (Net)** | **$26.40\%$** | Ministry of Finance Auctions | Alternative yield benchmark for asset allocators |
| **Macro Regime State** | **`HIGH_RATES_STABLE_FX`** | GEN-26 Classification Engine | Favors high cash-flow, net-cash, export-oriented stocks |

---

## 3. Equity Risk Premium (ERP) Formulation

The platform computes the **EGX Hurdle Rate** dynamically using the Capital Asset Pricing Model (CAPM) with Egyptian sovereign risk adjustments:

$$E(R_i) = R_f + \beta_i \cdot \text{ERP}_{\text{EGX}} + \text{CRP}_{\text{Egypt}}$$

Where:
- $R_f = 18.00\%$ (CBE Risk-Free Floor)
- $\text{ERP}_{\text{EGX}} = 7.50\%$ (Egyptian Equity Risk Premium)
- $\text{CRP}_{\text{Egypt}} = 4.20\%$ (Country Risk Premium)
- **Minimum Required Hurdle Rate for Equities**: $18.00\% + 7.50\% = 25.50\%$ annualized.

---

## 4. Sector Rotation & Inflation Resilience

The Macro Agent biases factor weightings based on the active regime:
1. **Net Beneficiaries of High Rates**: Commercial Banks (`COMI.CA`, `ADIB.CA`) with expanding Net Interest Margins (NIM).
2. **Export / Hard Currency Generators**: Petrochemicals (`ABUK.CA`, `MFPC.CA`), Industrial Exporters (`SWDY.CA`, `EGAL.CA`), and Tourism/Hospitality.
3. **Penalized Sectors**: Highly leveraged real estate developers with floating debt burdens.
