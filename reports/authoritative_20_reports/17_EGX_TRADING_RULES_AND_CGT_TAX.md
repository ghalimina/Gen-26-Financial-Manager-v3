# 17. EGX Trading Rules, Circuit Breakers & Capital Gains Tax (CGT)

## 1. Executive Summary
The **EGX Market Microstructure Rules Engine** (`core/egx_trading_rules_engine.py`) enforces strict compliance with the regulatory bylaws mandated by the Egyptian Financial Regulatory Authority (FRA) and the Egyptian Stock Exchange (EGX), including intraday price limits, cooling pauses, settlement cycles, and the 10% Capital Gains Tax (CGT).

---

## 2. Intraday Price Limits & Circuit Breakers

```
+-------------------------------------------------------------------------------+
|                      EGX INTRADAY PRICE LIMIT TIERS                           |
+-------------------+-----------------------+-----------------------------------+
| Tier Level        | Price Limit Deviation | Trading Action Enforced           |
+-------------------+-----------------------+-----------------------------------+
| Tier 1 Limit      | +/- 10.0%             | 10-Minute Market Cooling Auction  |
| Tier 2 Hard Limit | +/- 20.0%             | Hard Trading Suspension for Day   |
| Index Wide Halt   | +/- 5.0% on EGX100    | 30-Minute Market-Wide Suspension  |
+-------------------+-----------------------+-----------------------------------+
```

### 1. Tier 1 ($\pm 10.0\%$):
- When a stock touches $\pm 10.0\%$ from its previous closing reference price, continuous trading is halted for a **10-minute cooling price discovery auction**.
- Trading resumes with new reference bids/asks.

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
