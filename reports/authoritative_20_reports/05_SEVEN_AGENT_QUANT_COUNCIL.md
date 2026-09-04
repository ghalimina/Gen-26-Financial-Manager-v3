# 05 — Seven-Agent Quant Council & TradingAgents Dialectical Architecture
**GEN-26 Multi-Agent Deliberation Suite**
*Last Synchronized: 2026-08-30 14:19:12*

---

## 1. Two-Tier 7-Agent Architecture Specification

```
+====================================================================================================+
|                              7-AGENT QUANTITATIVE COUNCIL HIERARCHY                                |
+====================================================================================================+
| TIER 1: REAL-TIME TRADE SCREENING COUNCIL (5 VOTING AGENTS)                                         |
+----------------------------------------------------------------------------------------------------+
| 1. FundamentalistAgent ($w_1 = 0.25$) | Piotroski 9/9 adapted model, Lynch PEG, Graham margin       |
| 2. TechnicianAgent     ($w_2 = 0.25$) | Steve Nison candlesticks, Murphy support/resistance, ADX    |
| 3. MarketAnalystAgent  ($w_3 = 0.20$) | EGX30 breadth, foreign/institutional net flows, macro state |
| 4. QuantModelerAgent   ($w_4 = 0.20$) | Pairs arbitrage Z-score, London GDR parity, FracDiff        |
| 5. RiskSizerAgent      ($w_5 = 0.10$) | Mark Douglas sizing (max 1.0% NAV risk) + ABSOLUTE VETO     |
| --> Synthesis: Consensus Score = sum(w_i * Score_i) with sum(w_i) = 1.00                            |
+====================================================================================================+
| TIER 2: AUTONOMOUS RESEARCH LAB & EVOLUTION (2 META-AGENTS)                                        |
+----------------------------------------------------------------------------------------------------+
| 6. ResearchScientistAgent             | Formulates new hypotheses & parameter tuning from failures  |
| 7. CriticAuditorAgent                 | Adversarial anti-overfit audit & look-ahead bias gatekeeper |
+====================================================================================================+
```

---

## 2. Consensus Synthesis Formulation
$$\text{Consensus Score} = (0.25 \times S_{\text{fund}}) + (0.25 \times S_{\text{tech}}) + (0.20 \times S_{\text{mkt}}) + (0.20 \times S_{\text{quant}}) + (0.10 \times S_{\text{risk}})$$

- $\sum_{i=1}^{5} w_i = 0.25 + 0.25 + 0.20 + 0.20 + 0.10 = \mathbf{1.00}$
- **Absolute Risk Veto**: If `RiskSizerAgent` votes `REJECT` due to poor risk-reward ($R:R < 1:2.5$) or risk limit violation ($>1.0\%$ NAV), the entire candidate is rejected immediately regardless of other votes.
