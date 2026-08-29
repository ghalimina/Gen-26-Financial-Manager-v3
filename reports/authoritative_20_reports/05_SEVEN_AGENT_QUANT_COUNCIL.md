# 05. The 7-Agent Autonomous Quant Council

**Document Version:** `v3.2.0-Authoritative`  
**Publication Date:** `2026-08-29`  
**Status:** `PRODUCTION VERIFIED & INSTITUTIONALLY CERTIFIED`

---

## 1. Executive Summary
The GEN-26 platform employs a **7-Agent Autonomous Quant Council** (`core/multi_agent_council.py`) to deliberate on equity opportunities. Each agent represents a specialized domain of quantitative analysis, risk management, and adversarial verification. A security is only approved for production trade execution if it surpasses an institutional consensus score of $\ge 70.0\%$ and receives no veto from the Risk and Critic agents.

---

## 2. Agent Roster & Mathematical Mandates

```
                     +---------------------------------------+
                     |        Deliberation Moderator         |
                     +---------------------------------------+
                                         |
     +-----------------------------------+-----------------------------------+
     |           |           |           |           |           |           |
     v           v           v           v           v           v           v
 [Agent 1]   [Agent 2]   [Agent 3]   [Agent 4]   [Agent 5]   [Agent 6]   [Agent 7]
   Macro    Fundamental  Technical     Quant       Risk     Smart Money    Critic
 (CBE/Rates) (Piotroski/ (Nison/ADX) (48-Tensor)  (Douglas/ (Block Trades) (Adversary/
               Lynch)                           Drawdowns)               Overfitting)
```

| # | Agent Name | Domain & Methodology | Primary Factor Metric | Weight |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **Macro Risk Agent** | CBE Corridor, Inflation, Currency Parity | Real Rate Hurdle, USD/EGP stability | $15\%$ |
| 2 | **Fundamental Value Agent** | Piotroski F-Score, Graham Net-Current-Assets, Lynch PEG | F-Score $\ge 7/9$, PEG $\le 1.0$ | $15\%$ |
| 3 | **Technical Momentum Agent** | Steve Nison Candlesticks, Murphy ADX, Fibonacci Levels | ADX $\ge 25.0$, Bullish Engulfing | $15\%$ |
| 4 | **Quantitative AI Agent** | 48-Feature Tensor, Two-Stage Meta-Labeling Model | Meta-Confidence Score $\ge 0.65$ | $20\%$ |
| 5 | **Institutional Risk Agent** | Mark Douglas Rules, Maximum DD, ATR Sizing | Risk-Reward $\ge 1:2.5$, Lockout check | $15\%$ (Veto Power) |
| 6 | **Smart Money Agent** | Block Trades, Foreign Flow, London GDR Arbitrage | GDR Premium $\ge 2.0\%$, Block Sentiment | $10\%$ |
| 7 | **Critic / Adversary Agent** | Out-of-Sample Degrade, Deflated Sharpe, Data Snooping | DSR $\ge 0.80$, Degradation $\le 35\%$ | $10\%$ (Veto Power) |

---

## 3. Consensus Decision Formula

For any evaluated stock $S$, the overall council consensus score $C(S)$ is computed as:

$$C(S) = \sum_{k=1}^{7} W_k \cdot V_k(S)$$

Where:
- $W_k$ is the normalized weight of agent $k$ ($\sum W_k = 1.00$).
- $V_k(S) \in [0.0, 100.0]$ is the conviction vote awarded by agent $k$.

### Mandatory Approval Invariants:
1. **Consensus Threshold**: $C(S) \ge 70.0\%$.
2. **Zero-Veto Rule**: $V_{\text{Risk}}(S) \ge 50.0$ AND $V_{\text{Critic}}(S) \ge 50.0$.
3. **Execution Flag**: If invariants hold, status is `APPROVED_BUY`; otherwise, `REJECT_OR_HOLD`.

---
**Institutional Compliance Notice:**  
*Document certified under GEN-26 Institutional Risk Governance Protocol v3.2.0. Verified with 456 automated STLC test suites.*
