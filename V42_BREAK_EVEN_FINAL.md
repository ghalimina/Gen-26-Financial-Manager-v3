# 🏛️ GEN-26 V42 — FINAL BREAK-EVEN RECONCILIATION
**Generated via Walk-Forward Backtest Ledger**

## 1. THE CONTRADICTION
- **Claim A:** True Break-even ≈ 1.258%
- **Claim B:** True Break-even = 2.5161%

## 2. DEFINITIONS
- **Per-side Friction:** The percentage of transaction value paid ONCE (either on entry or exit). Includes broker commissions, taxes, clearing fees, and slippage.
- **Round-trip Friction:** The sum of entry and exit friction percentages. If entry = exit = X%, then Round-trip = 2X%.
- **Raw Turnover:** Sum of all Entry Values + Exit Values.
- **Gross PnL:** Sum of (Exit Price - Entry Price) * Quantity for all trades.
- **Break-even Friction (Round-trip):** Gross PnL / Raw Turnover. (The maximum round-trip fee the system can afford before net profit becomes zero).

## 3. RAW LEDGER RECONCILIATION
Based on the 386 trades in the verified backtest ledger:
- **Total Gross Profit:** EGP 126,286.46
- **Total Raw Turnover:** EGP 10,038,147.58
- **Actual Friction Paid in Simulation:** EGP 45,171.70
- **Average Implied Per-Side Fee used in simulation:** 0.4500% (Round-trip = 0.9000%)

## 4. MATHEMATICAL BREAK-EVEN
- **True Break-Even (Round-Trip):** EGP 126,286.46 / EGP 10,038,147.58 = **1.2581%**
- **True Break-Even (Per-Side):** **0.6290%**

## 5. VERDICT
**CLAIM A IS CORRECT (ROUND-TRIP).**
The value 1.258% is the **ROUND-TRIP** break-even point.
The value 2.5161% was erroneously calculated by doubling the round-trip value instead of doubling the per-side value.

If the real-world per-side friction (fees + slippage) is below **0.6290%**, the system has a mathematical edge.
