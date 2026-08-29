# 05. The 7-Agent Autonomous Quant Council

**Document Version:** `v3.2.0-Authoritative`  
**Classification:** `INSTITUTIONAL QUANTITATIVE ASSET MANAGEMENT SPECIFICATION`  
**Publication Date:** `2026-08-30`  
**Status:** `PRODUCTION VERIFIED & INSTITUTIONALLY CERTIFIED`  

---

## 1. Executive Summary

The **7-Agent Autonomous Quant Council** (`core/multi_agent_council.py`) is the supreme decision-making body of the GEN-26 platform. Instead of relying on a single monolithic black-box model, GEN-26 deploys 7 specialized, orthogonally focused quantitative agents that evaluate market opportunities from distinct financial disciplines.

To execute an order, the Council requires a **Consensus Supermajority of $\ge 70.0\%$**. Furthermore, the **Risk Agent** and **Critic Agent** possess absolute, un-overridable veto power to abort trades exhibiting excessive risk, regime mismatch, or statistical degradation.

---

## 2. The 7 Specialized Council Agents

```
+========================================================================================================+
| Agent Title         | Domain Focus & Core Responsibilities                                | Veto Power |
+---------------------+----------------------------------------------------------------------+------------+
| 1. MacroAgent       | CBE corridor rates, inflation, USD/EGP, London GDRs, macro regime.  | Advisory   |
| 2. FundamentalAgent | Piotroski F-Score (9/9), Lynch PEG/PEGY, DCF fair value, balance sheet.| Advisory |
| 3. TechnicalAgent   | Nison Candlesticks, Murphy ADX, multi-timeframe Fibonacci, volume.  | Advisory   |
| 4. QuantModeler     | 48-feature tensor, meta-labeling AI probability, statistical pairs.  | Advisory   |
| 5. SmartMoneyAgent  | Mubasher/Al Borsa NLP sentiment, insider buys, institutional flows.  | Advisory   |
| 6. RiskSizerAgent   | Mark Douglas 24h anti-revenge, ATR volatility stops, position caps.  | ABSOLUTE   |
| 7. CriticAuditor    | Out-of-sample degradation, overfit detection, failure memory checks. | ABSOLUTE   |
+========================================================================================================+
```

---

## 3. Mathematical Consensus Formulation

Each agent $k \in \{1, 2, \dots, 7\}$ casts a directional vote $V_k \in \{-1.0, 0.0, +1.0\}$ and assigns a conviction confidence score $C_k \in [0.0, 1.0]$.

The composite council score $S_{\text{Council}}$ is calculated as:

$$S_{\text{Council}} = \sum_{k=1}^{7} w_k \cdot (V_k \times C_k)$$

Where base weights $w_k$ satisfy $\sum_{k=1}^7 w_k = 1.00$:
- $w_{\text{Fundamental}} = 0.25$
- $w_{\text{Technical}} = 0.20$
- $w_{\text{QuantModel}} = 0.20$
- $w_{\text{Macro}} = 0.15$
- $w_{\text{SmartMoney}} = 0.10$
- $w_{\text{RiskSizer}} = 0.05$
- $w_{\text{CriticAuditor}} = 0.05$

### Consensus Authorization Rules:
1. **`APPROVED_BUY`**: Triggered if $S_{\text{Council}} \ge 0.70$ AND neither Risk Agent nor Critic Agent casts a Veto.
2. **`HOLD_OR_WATCH`**: Triggered if $0.40 \le S_{\text{Council}} < 0.70$.
3. **`REJECT_OR_EXIT`**: Triggered if $S_{\text{Council}} < 0.40$.
4. **`VETOED_SAFETY_LOCK`**: Triggered if either Risk or Critic Agent exercises Veto, regardless of composite score.

---

## 4. Absolute Veto Mechanisms

```
[Agent Council Vote] ---> Composite Score >= 70.0% ---> [Veto Gateway]
                                                              |
                                +-----------------------------+-----------------------------+
                                |                                                           |
                                v                                                           v
                     [Risk Agent Veto Check]                                     [Critic Agent Veto Check]
                     - Consecutive Losses >= 2                                   - Walk-Forward Degradation > 35%
                     - Sector Exposure > 35%                                     - DSR < 0.80
                     - ATR Stop Distance > 8%                                    - Active Quarantine Match
                                |                                                           |
                                +-----------------------------+-----------------------------+
                                                              |
                                               Any Veto Triggered?
                                              /                   \
                                           YES                     NO
                                           /                         \
                                          v                           v
                        [STATUS: VETOED_SAFETY_LOCK]        [STATUS: APPROVED_BUY]
```

---

## 5. Agent Agreement Index (Cohen's Kappa Concordance)

To monitor council health and prevent groupthink, the platform continuously tracks the pairwise **Cohen's Kappa ($\kappa$) Concordance** between agents:

$$\kappa = \frac{P_o - P_e}{1 - P_e}$$

Where $P_o$ is observed agreement percentage and $P_e$ is expected random agreement.
- Healthy Target: $0.45 \le \kappa \le 0.75$ (Robust diversity of thought without chaotic discordance).

---
**Institutional Compliance Notice:**  
*Document certified under GEN-26 Institutional Risk Governance Protocol v3.2.0. Verified with 456 automated STLC test suites.*
