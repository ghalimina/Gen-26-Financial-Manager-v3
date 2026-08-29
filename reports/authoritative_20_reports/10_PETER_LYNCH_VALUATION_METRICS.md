# 10. Peter Lynch Valuation & Stock Categorization Engine

## 1. Executive Summary
The **Peter Lynch Valuation Engine** (`core/quant_books_engine.py`) implements the growth-at-a-reasonable-price (GARP) valuation methodologies pioneered by legendary Magellan Fund manager Peter Lynch (*One Up On Wall Street*).

---

## 2. Core Mathematical Metrics

### 1. Standard Peter Lynch PEG Ratio

$$\text{PEG} = \frac{P/E}{\text{EPS Growth Rate (\%) disagree}} = \frac{P/E}{\text{EPS Growth Rate (\%)}} $$

Where:
- $\text{PEG} < 0.50$: **Deeply Undervalued Opportunity** (فرصة نادرة ومغرية جداً مع هامش أمان واسع)
- $0.50 \le \text{PEG} \le 1.00$: **Fairly Valued Growth** (سعر عادل ومتوازن لنمو الشركة)
- $\text{PEG} > 1.50$: **Overvalued / Growth Stretched** (مبالغ في التقييم مقارنة بالنمو)

### 2. Dividend-Adjusted PEGY Ratio

$$\text{PEGY} = \frac{P/E}{\text{EPS Growth Rate (\%) } + \text{Dividend Yield (\%) }}$$

Accounts for the total shareholder return by crediting dividend payouts alongside earnings expansion.

### 3. Net Cash Per Share

$$\text{Net Cash Per Share} = \frac{\text{Cash \& Equivalents} - \text{Total Debt}}{\text{Shares Outstanding}}$$

If $\text{Net Cash Per Share} > 0$, the effective enterprise value is lower than nominal market cap, providing downside balance sheet protection.

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

### Elsewedy Electric (`SWDY.CA`):
- **Trailing $P/E$**: $8.2\times$
- **EPS Growth Rate**: $+28.5\%$
- **Dividend Yield**: $+4.5\%$
- **Standard $\text{PEG}$**: $\frac{8.2}{28.5} = \mathbf{0.29}$
- **Dividend-Adjusted $\text{PEGY}$**: $\frac{8.2}{28.5 + 4.5} = \frac{8.2}{33.0} = \mathbf{0.25}$
- **Category**: `FAST_GROWER` (High Alpha Conviction).

### Commercial International Bank (`COMI.CA`):
- **Trailing $P/E$**: $6.8\times$
- **EPS Growth Rate**: $+18.0\%$
- **Dividend Yield**: $+5.2\%$
- **Standard $\text{PEG}$**: $\frac{6.8}{18.0} = \mathbf{0.38}$
- **Dividend-Adjusted $\text{PEGY}$**: $\frac{6.8}{18.0 + 5.2} = \frac{6.8}{23.2} = \mathbf{0.29}$
- **Category**: `STALWART` (Institutional Anchor).
