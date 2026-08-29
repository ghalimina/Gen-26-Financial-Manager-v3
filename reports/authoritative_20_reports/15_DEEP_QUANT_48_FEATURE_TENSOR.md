# 15. The 48-Dimensional Quant Feature Tensor

## 1. Executive Summary
The **Deep Quant Feature Fusion Engine** (`core/deep_quant_fusion_engine.py`) extracts and standardizes a high-dimensional **48-feature tensor** for each EGX equity. Features span across technical signals, classic book value metrics, macroeconomic/arbitrage indicators, and alternative NLP/smart-money data.

---

## 2. 48-Feature Tensor Decomposition

```
+-------------------------------------------------------------------------------+
|                      48-DIMENSIONAL QUANT FEATURE TENSOR                      |
+-----------------------+-----------------------+---------------+---------------+
| 1. Technical (12)     | 2. Fundamental (12)   | 3. Macro (12) | 4. Flow (12)  |
| - RSI (14)            | - Piotroski F-Score   | - CBE Rate    | - Block Ratio |
| - MACD Histogram      | - Peter Lynch PEG     | - Inflation   | - Foreign Net |
| - ADX (14)            | - ROE / ROIC          | - USD/EGP     | - GDR Prem    |
| - ATR Volatility      | - Net Cash / Share    | - ERP Spread  | - Sentiment   |
| - Bollinger %B        | - Gross Margin Delta  | - T-Bill Net  | - OBV Slope   |
| - OBV / Volume Ratio  | - Debt-to-Equity      | - Brent Oil   | - MCDR Flow   |
| - EMA (20/50/200)     | - Asset Turnover      | - Natural Gas | - Retail Skew |
| - Stochastic (K/D)    | - Current Ratio       | - Gold Parity | - Bid/Ask Imb |
| - Williams %R         | - Graham Number Diff  | - Sector Beta | - Insider Buy |
| - Donchian Channel    | - Price / Book (P/B)  | - FX Vol      | - Social Buzz |
| - Price / 52w High    | - Trailing P/E        | - CDS Spread  | - Fund Alloc  |
| - Hist Vol (30d)      | - Dividend Yield      | - Yield Curve | - Vol Surge   |
+-----------------------+-----------------------+---------------+---------------+
```

---

## 3. Normalization & Preprocessing Protocol

To ensure mathematical stability and prevent gradient vanishing or outlier explosion:
1. **Winsorization**: Extreme outliers are capped at the $1^{\text{st}}$ and $99^{\text{th}}$ percentiles:
   $$x_{\text{clipped}} = \max(Q_{0.01}, \min(Q_{0.99}, x))$$
2. **Robust Z-Score Normalization**:
   $$z = \frac{x_{\text{clipped}} - \text{Median}(X)}{\text{IQR}(X) / 1.349}$$
3. **Min-Max Uniform Scaling**: Rescaled into the standardized interval $[0.0, 1.0]$.

---

## 4. Tensor Consumption Pipeline

The resulting $N \times 48$ tensor ($N = 244$ stocks) is streamed synchronously into:
1. The **Two-Stage Meta-Labeling Machine Learning Model**.
2. The **7-Agent Autonomous Deliberation Council**.
3. The **Institutional Cross-Sectional Ranking Matrix**.
