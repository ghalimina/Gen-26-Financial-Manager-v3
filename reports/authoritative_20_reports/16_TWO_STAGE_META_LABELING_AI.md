# 16 — Two-Stage Meta-Labeling Machine Learning Framework
**GEN-26 Lopez de Prado Meta-Labeling Architecture**
*Last Synchronized: 2026-08-30 14:19:12*

---

## 1. Meta-Labeling Piecewise Sizing Equation
$$\text{BetSize} = \min(1.0, \max(0.0, \frac{P(\text{Success}) - 0.60}{0.85 - 0.60}))$$

- Linear threshold floor: **0.60**
- Linear threshold ceiling: **0.85**
- Primary Model: Directional Alpha (+1 / -1)
- Secondary Meta-Model: Probability of Profitability $P(\text{Success})$.
