# 02 — EGX 244-Stock Universe Catalog & Liquidity Funnel
**GEN-26 Quantitative Autonomous Platform | Version 3.2.0-Authoritative | Institutional Whitepaper**

---

## Executive Summary
The GEN-26 Platform tracks the complete **244-stock universe** of genuine Egyptian Exchange (EGX) equities listed on the Thndr broker platform. To prevent execution failures and illiquidity slippage, the universe passes through a rigorous **3-Tier Institutional Liquidity Funnel**.

---

## 1. 3-Tier Liquidity Funnel Filtering

```
[ Full EGX Universe: 244 Listed Equities ]
                  │
                  ▼  (Rule 1: 30-Day ADV >= 500,000 EGP)
[ Liquid Active Universe: ~165-170 Equities ]
                  │
                  ▼  (Rule 2: Trading Days >= 80% over 60 Sessions)
[ Core Research Universe: ~70-90 Equities ]
                  │
                  ▼  (Rule 3: Max Bid-Ask Spread <= 2.50%)
[ Elite Tradable Alpha Universe: ~25-35 Equities ]
```

---

## 2. Canonical Pricing Single Source of Truth (SSoT)

All components read live canonical market prices from the unified SSoT store (`data/canonical_prices_live.json` and `core/market_price_service.py`):

| Ticker | Company Name (Arabic) | Sector | Canonical Price | Status |
| :--- | :--- | :--- | :---: | :---: |
| **`COMI.CA`** | البنك التجاري الدولي | Banking & Financial Services | **139.28 EGP** | Verified SSoT |
| **`SWDY.CA`** | السويدي إليكتريك | Industrial & Construction | **127.99 EGP** | Verified SSoT |
| **`TMGH.CA`** | مجموعة طلعت مصطفى | Real Estate & Development | **97.51 EGP** | Verified SSoT |
| **`MFPC.CA`** | مصر لإنتاج الأسمدة (موبكو) | Basic Resources & Petrochemicals | **39.34 EGP** | Verified SSoT |
| **`ETEL.CA`** | المصرية للاتصالات | Telecom, Media & Technology | **116.00 EGP** | Verified SSoT |
| **`FWRY.CA`** | فوري لتكنولوجيا البنوك | Technology / FinTech | **18.85 EGP** | Verified SSoT |
| **`ABUK.CA`** | أبو قير للأسمدة | Basic Resources & Petrochemicals | **75.76 EGP** | Verified SSoT |
| **`HRHO.CA`** | إي إف جي القابضة (هيرميس) | Non-Bank Financial Services | **25.90 EGP** | Verified SSoT |

---

## 3. Sector Classifications
The 244 equities are categorized across 12 standard EGX industrial sectors:
1. Banking & Financial Services
2. Real Estate & Development
3. Basic Resources & Petrochemicals
4. Industrial Goods, Services & Automobiles
5. Food, Beverages & Tobacco
6. Healthcare & Pharmaceuticals
7. Telecommunications, Media & Technology
8. Building Materials & Construction
9. Non-Bank Financial Services (NBFS)
10. Energy & Support Services
11. Travel, Tourism & Leisure
12. Education & Consumer Services
