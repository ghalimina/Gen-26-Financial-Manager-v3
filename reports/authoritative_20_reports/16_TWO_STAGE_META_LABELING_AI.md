# 16 — Two-Stage Meta-Labeling AI & Uncertainty Engine
**GEN-26 Quantitative Autonomous Platform | Version 3.2.0-Authoritative | Institutional Whitepaper**

---

## Executive Summary
GEN-26 utilizes Marcos López de Prado's **Two-Stage Meta-Labeling Architecture** coupled with an independent **Uncertainty Engine** (`core/uncertainty_engine.py`) and **Trade Selection Gate** (`core/trade_selection_model.py`).

---

## 1. Two-Stage Meta-Labeling Formulation

$$	ext{Position Size Multiplier} = \min\left(1.0, \max\left(0.0, rac{\hat{p}_{	ext{meta}} - 0.60}{0.85 - 0.60}ight)ight)$$

- If $\hat{p}_{	ext{meta}} < 0.60$: Multiplier = $0.00$ (**NO_TRADE / Safety Lock**).
- If $\hat{p}_{	ext{meta}} \ge 0.85$: Multiplier = $1.00$ (**Full Sizing**).

---

## 2. Trade Selection Model ("When NOT to Trade")

The trade selection model enforces the strict **Net Edge Hurdle**:

$$	ext{Net Edge} = E(	ext{Return}) - (0.35\% + 	ext{Dynamic Slippage}) - 	ext{Uncertainty Penalty} \ge \mathbf{1.00\%}$$

Trades with expected returns lower than 1.00% after all frictions and uncertainty are rejected with `DECISION_PASS_NO_TRADE`.
