# 14 — Statistical Pairs Arbitrage & Benjamini-Hochberg FDR
**GEN-26 Quantitative Autonomous Platform | Version 3.2.0-Authoritative | Institutional Whitepaper**

---

## Executive Summary
Identifies cointegrated equity pairs across the EGX universe using the Engle-Granger two-step test and prunes spurious cointegration via the **Benjamini-Hochberg False Discovery Rate (FDR)** algorithm:

$$p_{(i)} \le rac{i}{m} 	imes 0.05$$

Pairs passing FDR correction generate mean-reverting Z-score trading signals ($Z > +2.0$ Short Spread, $Z < -2.0$ Long Spread).
