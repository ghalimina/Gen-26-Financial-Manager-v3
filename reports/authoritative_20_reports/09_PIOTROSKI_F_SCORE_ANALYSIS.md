# 09. Piotroski F-Score Fundamental Quality Engine

## 1. Executive Summary
The **Piotroski F-Score Engine** (`core/quant_books_engine.py`) implements Joseph Piotroski’s 9-point accounting fundamental scoring system to evaluate financial health, earnings quality, and balance sheet resilience for Egyptian equities.

---

## 2. The 9 Binary Signals

The F-Score evaluates 9 criteria across three primary financial dimensions, assigning 1 point per positive criterion:

```
Total Piotroski F-Score = Profitability (4 pts) + Leverage/Liquidity (3 pts) + Operating Efficiency (2 pts)
```

### A. Profitability Signals (4 Points)
1. **Positive Net Income**: $\text{ROA}_t > 0$ (Net Income / Total Assets $> 0$).
2. **Positive Operating Cash Flow**: $\text{CFO}_t > 0$ (Cash Flow from Operations $> 0$).
3. **Improving ROA**: $\Delta \text{ROA} = \text{ROA}_t - \text{ROA}_{t-1} > 0$.
4. **Accruals Quality**: $\text{CFO}_t > \text{ROA}_t$ (Cash flow exceeds accounting net income, indicating low earnings manipulation).

### B. Leverage, Liquidity & Solvency Signals (3 Points)
5. **Lower Long-Term Debt**: $\Delta \text{Leverage} = \text{Leverage}_t - \text{Leverage}_{t-1} \le 0$.
6. **Higher Current Ratio**: $\Delta \text{Current Ratio} = \text{CR}_t - \text{CR}_{t-1} > 0$.
7. **No Share Dilution**: $\Delta \text{Shares Outstanding} \le 0$ (Company has not issued new shares, protecting EPS).

### C. Operating Efficiency Signals (2 Points)
8. **Higher Gross Margin**: $\Delta \text{Gross Margin} = \text{GM}_t - \text{GM}_{t-1} > 0$.
9. **Higher Asset Turnover**: $\Delta \text{Asset Turnover} = \text{ATO}_t - \text{ATO}_{t-1} > 0$.

---

## 3. Score Interpretation & EGX Tiers

| F-Score Range | Quality Tier | Arabic Classification | System Recommendation |
| :--- | :--- | :--- | :--- |
| **8 – 9 Points** | Very Strong Fundamentals | جودة مالية مؤسسية فائقة | Strong Buy / Long Core Asset |
| **6 – 7 Points** | Stable Quality | مركز مالي متوازن ومستقر | Buy / Moderate Allocation |
| **4 – 5 Points** | Moderate Quality | جودة متوسطة تتطلب حذر | Neutral / Watchlist Only |
| **0 – 3 Points** | High Financial Distress | ضعف محاسبي وخطر تعثر مالي | Blacklisted / Immediate Rejection |

---

## 4. Empirical Sample Score: Commercial International Bank (`COMI.CA`)
- **ROA**: $+3.40\%$ (Point 1: 1)
- **CFO**: Positive (Point 2: 1)
- **Delta ROA**: Expanding (Point 3: 1)
- **Accruals**: Cash exceeds net profit (Point 4: 1)
- **Capital Adequacy & Leverage**: Strong (Point 5: 1)
- **Current / Liquidity Ratio**: Strong (Point 6: 1)
- **No Dilution**: Zero new shares issued (Point 7: 1)
- **Net Interest Margin / Efficiency**: Expanding (Points 8 & 9: 1, 1)
- **Total F-Score for `COMI.CA`**: **8 / 9** (Institutional Premium Tier).
