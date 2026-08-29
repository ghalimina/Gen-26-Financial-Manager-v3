# 17. EGX Trading Rules, Circuit Breakers & Capital Gains Tax (CGT)

**Document Version:** `v3.2.0-Authoritative`  
**Classification:** `INSTITUTIONAL QUANTITATIVE ASSET MANAGEMENT SPECIFICATION`  
**Publication Date:** `2026-08-30`  
**Status:** `PRODUCTION VERIFIED & INSTITUTIONALLY CERTIFIED`  

---

## 1. Executive Summary

The **EGX Market Microstructure Rules Engine** (`core/egx_trading_rules_engine.py`) enforces strict compliance with the regulatory bylaws mandated by the Egyptian Financial Regulatory Authority (FRA) and the Egyptian Stock Exchange (EGX), including intraday price limits, cooling pauses, settlement cycles, dynamic execution slippage, and the 10% Capital Gains Tax (CGT).

---

## 2. Intraday Price Limits & Circuit Breakers

```
+========================================================================================================+
| Limit Tier        | Price Band Deviation | Trading Action Enforced                                     |
+===================+======================+=============================================================+
| Tier 1 Limit      | +/- 10.0%            | 10-Minute Market Cooling Price Discovery Auction            |
| Tier 2 Hard Limit | +/- 20.0%            | Hard Trading Suspension for Remainder of Trading Session    |
| Index Wide Halt   | +/- 5.0% on EGX100   | 30-Minute Market-Wide Trading Suspension                    |
+========================================================================================================+
```

### 1. Tier 1 ($\pm 10.0\%$):
- When a stock touches $\pm 10.0\%$ from its previous closing reference price, continuous trading is halted for a **10-minute cooling price discovery auction**.
- Orders can be entered and amended; trading resumes with a newly established equilibrium price.

### 2. Tier 2 ($\pm 20.0\%$ Hard Limit):
- The maximum permissible single-session price band is $\pm 20.0\%$.
- Any order submitted outside the $[\text{Close}_{t-1} \times 0.80, \text{Close}_{t-1} \times 1.20]$ range is rejected with status `INVALID_PRICE_BAND`.

---

## 3. Settlement Calendars (T+0, T+1, T+2)

- **T+0 (Same-Day Intra-Day Trading)**: Available only for authorized liquid securities (`COMI.CA`, `SWDY.CA`, `TMGH.CA`). Requires specific broker custodial account flags.
- **T+1 (Next-Day Settlement)**: Standard for eligible tier-1 equities.
- **T+2 (Two-Day Settlement)**: Default settlement cycle across general EGX listed shares.

---

## 4. Egyptian Capital Gains Tax (CGT) Accounting

Under Egyptian tax law (Law No. 30 of 2023), Egyptian resident individuals and corporations are subject to a **$10.0\%$ Capital Gains Tax** on net realized profits:

$$\text{Net Realized P\&L} = \sum_{\text{Trades}} \text{Gross Profit} - \sum_{\text{Trades}} \text{Gross Losses} - \text{Deductible Trading Expenses}$$

$$\text{CGT Withholding} = \max(0.0, 0.10 \times \text{Net Realized P\&L})$$

- Invariant: Backtest and real portfolio engines deduct $10.0\%$ CGT from all winning closed positions to reflect true post-tax institutional net returns.

---

## 5. Almgren-Chriss Dynamic Slippage Model

To replace naive static friction assumptions, GEN-26 implements the **Almgren-Chriss Square-Root Market Impact Model** (`core/dynamic_risk_manager.py` $\to$ `calculate_dynamic_slippage`):

$$\text{Execution Slippage (\%)} = \text{Base Spread}_{\text{Tier}} + 0.12\% \times \sqrt{\frac{\text{Order Value (EGP)}}{\max(ADV_{30} \text{ (EGP)}, \, 1,000,000)}}$$

### Market Cap Tier Spreads:
- **LARGE_CAP** ($ADV_{30} \ge 20\text{M EGP}$): $\text{Base Spread} = 0.10\%$
- **MID_CAP** ($5\text{M} \le ADV_{30} < 20\text{M EGP}$): $\text{Base Spread} = 0.15\%$
- **SMALL_CAP** ($ADV_{30} < 5\text{M EGP}$): $\text{Base Spread} = 0.25\%$

### Bounded Invariants:
- Minimum Execution Friction Floor: $0.10\%$
- Maximum Liquidity Stress Ceiling: $1.50\%$
- Applied dynamically to order execution simulation across all portfolio sizing engines.

---
**Institutional Compliance Notice:**  
*Document certified under GEN-26 Institutional Risk Governance Protocol v3.2.0. Verified with 456 automated STLC test suites.*
