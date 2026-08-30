# 05 — 7-Agent Autonomous Quantitative Council
**GEN-26 Quantitative Autonomous Platform | Version 3.2.0-Authoritative | Institutional Whitepaper**

---

## Executive Summary
The GEN-26 decision engine is powered by an autonomous **7-Agent Quantitative Council** (`core/multi_agent_council.py`). Each agent represents a specialized institutional discipline and votes independently with an assigned conviction score.

---

## 1. Council Member Specifications

| # | Agent Name | Domain & Methodology | Primary Features Evaluated |
| :-: | :--- | :--- | :--- |
| **1** | **Macro Strategy Agent** | CBE Corridor, Inflation, FX, HMM Regime | CBE Rates (19%/20%), USD/EGP (50.20), Net Foreign Inflows |
| **2** | **Fundamental Value Agent** | Piotroski F-Score, Graham Value, Lynch PEG | F-Score (9/9), P/E, PEG, ROE, Debt/Equity |
| **3** | **Technical Timing Agent** | Nison Candlesticks, Murphy Trends, ADX | RSI(14), ADX, MACD, Support/Resistance Zones |
| **4** | **Smart Money Radar Agent** | Institutional block trades, Insider filings | Volume Z-Score, Institutional Accumulation Index |
| **5** | **Quantitative Model Agent** | Two-Stage Meta-Labeling, Pairs Arbitrage | Random Forest Probabilities, Z-Spread, Fractional Diff |
| **6** | **Dynamic Risk Agent** | Modified Kelly, Douglas Psychology Guard | ATR Volatility, Max Drawdown, Stop Loss Distance |
| **7** | **Adversarial Critic Agent** | Overfitting detection, Deflated Sharpe Ratio | PBO, Purged Walk-Forward Degradation Hurdle |

---

## 2. Consensus Synthesis & Supermajority Rule

The final council verdict requires a **Supermajority Consensus Hurdle**:

$$	ext{Consensus Score} = rac{\sum_{i=1}^{7} w_i \cdot 	ext{Vote}_i \cdot 	ext{Conviction}_i}{\sum_{i=1}^{7} w_i} \ge \mathbf{70.0\%}$$

If the consensus score is $< 70.0\%$ or the Adversarial Critic Agent identifies data leakage / overfitting, the system executes a fail-closed `HOLD` or `NO_TRADE`.
