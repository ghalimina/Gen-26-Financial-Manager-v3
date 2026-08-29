# 10. Peter Lynch Valuation & Stock Categorization Engine

## 1. Executive Summary
The **Peter Lynch Valuation Engine** (`core/quant_books_engine.py`) implements the growth-at-a-reasonable-price (GARP) valuation methodologies pioneered by legendary Magellan Fund manager Peter Lynch (*One Up On Wall Street*).

---

## 2. Core Mathematical Metrics

### 1. Price/Earnings-to-Growth (PEG) Ratio

$$\text{PEG} = \frac{P/E}{\text{EPS Growth Rate (\%)}+ \text{Dividend Yield (\%)}} $$

Where:
- $\text{PEG} < 0.50$: **Deeply Undervalued Opportunity** (فرصة نادرة ومغرية جداً)
- $0.50 \le \text{PEG} \le 1.00$: **Fairly Valued Growth** (سعر عادل مع هامش أمان)
- $\text{PEG} > 1.50$: **Overvalued / Growth Stretched** (مبالغ في التقييم)

### 2. Net Cash Per Share

$$\text{Net Cash Per Share} = \frac{\text{Cash \& Equivalents} - \text{Total Debt}}{\text{Shares Outstanding}}$$

If $\text{Net Cash Per Share} > 0$, the effective enterprise value is lower than nominal market cap, providing downside protection.

---

## 3. The 6 Lynch Stock Categories

```
+------------------+-----------------------------------------------------+
| Category         | Definition & EGX Criteria                           |
+------------------+-----------------------------------------------------+
| FAST_GROWER      | EPS Growth > 20% annually with modest P/E.          |
| STALWART         | Large-cap, steady 10-18% growth, recession buffer.  |
| SLOW_GROWER      | EPS Growth < 8%, high dividend yield (>8%).         |
| CYCLICAL         | Revenues tied to commodity/macro cycles (Steel/Petro|
| TURNAROUND       | Depressed earnings but restructuring balance sheet. |
| ASSET_PLAY       | Hidden real estate, land bank, or hard assets.      |
+------------------+-----------------------------------------------------+
```

---

## 4. Empirical Sample Categorization

- **`SWDY.CA` (Elsewedy Electric)**:
  - Trailing $P/E$: $8.2\times$
  - EPS Growth: $+28.5\%$
  - $\text{PEG}$: $0.29$
  - **Category**: `FAST_GROWER` (High Alpha Conviction).
- **`COMI.CA` (CIB Egypt)**:
  - Trailing $P/E$: $6.8\times$
  - EPS Growth: $+18.0\%$
  - $\text{PEG}$: $0.38$
  - **Category**: `STALWART` (Institutional Anchor).
