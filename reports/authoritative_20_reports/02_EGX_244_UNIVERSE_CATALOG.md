# 02 — EGX 244-Stock Universe Catalog & Liquidity Funnel
**GEN-26 Quantitative Autonomous Platform | Version 3.2.0-Authoritative | Institutional Whitepaper**

---

## Executive Summary
The GEN-26 Platform tracks the complete **244-stock universe** of genuine Egyptian Exchange (EGX) equities listed on the Thndr broker platform. To prevent execution failures and illiquidity slippage, the universe passes through a rigorous **3-Tier Institutional Liquidity Funnel**.

---

## 1. 3-Stage Institutional Liquidity Funnel

```
+====================================================================================================+
| STAGE 1: Total Listed Catalog               | 244 Equities (Complete Genuine EGX Universe)         |
+---------------------------------------------+------------------------------------------------------+
| STAGE 2: Active Tradable Universe           | 170 Equities (Filtered for 30-Day ADV >= 1,000,000)  |
+---------------------------------------------+------------------------------------------------------+
| STAGE 3: Daily Active Focus Opportunities   | 24 Equities (High-Conviction Alpha & Prime Liquidity)|
+====================================================================================================+
```

---

## 2. Canonical Pricing Single Source of Truth (SSoT)

All components read live canonical market prices from the unified SSoT store (`data/canonical_prices_live.json` and `core/market_price_service.py`):

| Ticker | Company Name (Arabic) | Sector | Canonical Price | Status |
| :--- | :--- | :--- | :---: | :---: |
| **`COMI.CA`** | البنك التجاري الدولي (CIB) | الخدمات المالية والبنوك | **139.28 EGP** | Verified SSoT |
| **`SWDY.CA`** | السويدي إليكتريك | الصناعة والمقاولات | **127.99 EGP** | Verified SSoT |
| **`TMGH.CA`** | مجموعة طلعت مصطفى | التطوير العقاري | **97.51 EGP** | Verified SSoT |
| **`MFPC.CA`** | مصر لإنتاج الأسمدة (موبكو) | الموارد الأساسية والكيماويات | **39.34 EGP** | Verified SSoT |
| **`ETEL.CA`** | المصرية للاتصالات (WE) | الاتصالات وتكنولوجيا المعلومات | **116.00 EGP** | Verified SSoT |
| **`FWRY.CA`** | فوري لتكنولوجيا المدفوعات الإلكترونية | تكنولوجيا المدفوعات | **18.85 EGP** | Verified SSoT |
| **`ABUK.CA`** | أبو قير للأسمدة | الموارد الأساسية والكيماويات | **75.76 EGP** | Verified SSoT |
| **`HRHO.CA`** | مجموعة إي إف جي القابضة (هيرميس) | الخدمات المالية غير المصرفية | **25.90 EGP** | Verified SSoT |

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
