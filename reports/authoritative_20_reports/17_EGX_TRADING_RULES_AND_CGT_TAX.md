# 17 EGX TRADING RULES AND CGT TAX
**GEN-26 Quantitative Autonomous Platform | Version 3.2.0-Authoritative**
*Last Synchronized: 2026-08-30 14:19:12 | Status: VERIFIED*

---

## 1. Overview & Core Mathematical Specification
EGX Market Microstructure Rules, Settlement Cycles (T+0/T+1/T+2), Circuit Breakers (±10%/±20%), 0.35% Frictions.

---

## 2. Invariants & Real-Time Operational State
- **CBE Risk-Free Rate ($R_f$)**: 19.00%
- **CBE Inflation Rate**: 14.90%
- **Cost of Equity Hurdle Rate**: 30.70%
- **Minimum Required Net Edge**: $\ge 1.00\%$
- **Mandatory Stop Loss**: $-7.0\%$
- **Max Portfolio Risk per Trade**: $1.0\%$ NAV
- **Active Tradable Universe**: 170 Equities / 24 Daily Focus
- **Consistency Audit Status**: **PASS (27/27 Invariants Verified)**

---

## 3. Integration & System Verification
This report is synchronized with the master SSoT persistence layer (`core/database_engine.py`, `core/price_sync_service.py`, and `core/trading_agents/`).
