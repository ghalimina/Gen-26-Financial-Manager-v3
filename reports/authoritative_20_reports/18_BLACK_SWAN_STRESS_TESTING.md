# 18 — Black Swan Stress Testing & Dynamic Gold ETF Hedging
**GEN-26 Quantitative Autonomous Platform | Version 3.2.0-Authoritative | Institutional Whitepaper**

---

## Executive Summary
The risk engine (`core/risk_stress_testing_engine.py`) performs parametric Covariance VaR, Cornish-Fisher Modified VaR (99% confidence), and automated allocation to the **Azimut Gold ETF (`AZG.CA`)** (5%–20% allocation) to protect capital during currency devaluations and market flash crashes.
