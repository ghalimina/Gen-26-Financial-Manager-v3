# 03. Macro Regime, CBE Corridor & Equity Risk Premium (ERP)

## 1. Macroeconomic Context & Official Data
The GEN-26 Macroeconomic Barometer (`core/macro_risk_manager.py`) tracks the monetary policy parameters set by the Monetary Policy Committee (MPC) of the Central Bank of Egypt (CBE), along with headline inflation, foreign exchange rates, and sovereign treasury yields.

---

## 2. Official Telemetry Ingestion Metrics

| Macro Metric | Official Rate / Value | Regulatory Authority | Quantitative Impact on EGX Equities |
| :--- | :--- | :--- | :--- |
| **CBE Overnight Deposit Rate** | **$19.00\%$** | Central Bank of Egypt (MPC) | Risk-free rate floor ($R_f$) for Egyptian cash holdings |
| **CBE Overnight Lending Rate** | **$20.00\%$** | Central Bank of Egypt (MPC) | Upper corridor rate; benchmark for corporate debt costs |
| **Headline Annual Inflation** | **$14.90\%$** | CAPMAS / CBE Disclosures | Positive real interest rate environment ($+4.10\%$) |
| **USD/EGP Official Spot Rate** | **$50.20$ EGP** | Interbank Market / CBE | Official anchor for London GDR arbitrage parity |
| **91-Day T-Bill Yield (Net)** | **$26.40\%$** | Ministry of Finance Auctions | Alternative riskless yield benchmark for institutional allocators |
| **Macro Regime State** | **`HIGH_RATES_STABLE_FX`** | GEN-26 Classification Engine | Favors high cash-flow, net-cash, export-oriented stocks |

---

## 3. Equity Risk Premium (ERP) & Hurdle Rate Formulation

The platform computes the **EGX Required Cost of Equity (Hurdle Rate)** dynamically using the Capital Asset Pricing Model (CAPM) augmented with sovereign Country Risk Premium (CRP):

$$E(R_i) = R_f + (\beta_i \cdot \text{ERP}_{\text{EGX}}) + \text{CRP}_{\text{Egypt}}$$

Where:
- $R_f = 19.00\%$ (CBE Overnight Deposit Floor)
- $\beta_i = 1.00$ (Market Benchmark Beta)
- $\text{ERP}_{\text{EGX}} = 7.50\%$ (Egyptian Equity Risk Premium)
- $\text{CRP}_{\text{Egypt}} = 4.20\%$ (Egyptian Country Risk Premium)

### Institutional Hurdle Rate Benchmark:
$$E(R_i) = 19.00\% + (1.00 \times 7.50\%) + 4.20\% = \mathbf{30.70\%} \text{ Annualized}$$

Equities evaluated by the platform must demonstrate an expected total return (Alpha + Beta) exceeding the $30.70\%$ hurdle rate to qualify for active capital deployment.

---

## 4. Sector Rotation & Inflation Resilience

The Macro Agent biases factor weightings based on the active regime:
1. **Net Beneficiaries of High Rates**: Commercial Banks (`COMI.CA`, `ADIB.CA`) with expanding Net Interest Margins (NIM).
2. **Export / Hard Currency Generators**: Petrochemicals (`ABUK.CA`, `MFPC.CA`), Industrial Exporters (`SWDY.CA`, `EGAL.CA`), and Tourism/Hospitality.
3. **Penalized Sectors**: Highly leveraged real estate developers with floating debt burdens.
