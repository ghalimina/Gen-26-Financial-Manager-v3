# SURVIVORSHIP_AND_UNIVERSE_AUDIT.md
# Comprehensive Stock Universe, Listing History & Survivorship Bias Forensic Audit
**System:** GEN-26 Quantitative Financial Architecture  
**Audit Scope:** 27-Stock Research Panel, 8-Stock Delisting Resolution Claim, 244-Stock Production Universe  
**Audit Date:** 2026-09-17  
**Formal Audit Classification:** **`SURVIVORSHIP_BIAS_UNRESOLVED`**  
**Audit Context:** `RESEARCH_ONLY / SHADOW_ONLY / NON_PRODUCTION / NO_LIVE_TRADING / NO_ML`  

---

## 1. Executive Forensic Verdict on Survivorship Bias

> [!WARNING]
> **Definitive Finding on Survivorship Bias:**
> 1. The 27-stock research panel comprises companies that **survived and remained actively traded on the Egyptian Exchange through August 2026**.
> 2. The historical claim in `phase_2_6_survivorship_reconstruction.md` that survivorship bias was audited and resolved using 8 historical delisted stocks is **COMPLETELY DEBUNKED AND RETRACTED**.
> 3. All 8 companies tested (`DSCW.CA`, `BTFH.CA`, `KABO.CA`, `ORHD.CA`, `RREI.CA`, `SDTI.CA`, `SPMD.CA`, `UEGC.CA`) are **actively listed, surviving EGX equities**.
> 4. Consequently, **SURVIVORSHIP BIAS REMAINS 100% UNRESOLVED** in the quantitative research datasets. Historical win rates and Profit Factors carry an inherent, uncorrected upward survivorship bias.

---

## 2. Forensic Audit of the 8 Tickers Mislabeled as "Delisted"

A zero-trust check was performed against the official Egyptian Exchange (EGX) registry and financial filing disclosures for the 8 tickers claimed as "historical delisted stocks":

| Ticker | Company Name | Yahoo Bars (2020–2025) | Real Status on EGX (Verified 2026) | Corporate Reality & Provenance |
| :--- | :--- | :---: | :---: | :--- |
| **`DSCW.CA`** | Dice Sport & Casual Wear | 1,455 bars | **ACTIVE LISTING** | Actively traded; ongoing corporate disclosures. Not delisted. |
| **`BTFH.CA`** | Beltone Holding | 1,455 bars | **ACTIVE LISTING** | Major IHC-backed financial services firm; highly liquid active stock. Not delisted. |
| **`KABO.CA`** | El Nasr Clothing & Textiles | 1,455 bars | **ACTIVE LISTING** | Listed and regularly traded on EGX. Not delisted. |
| **`ORHD.CA`** | Orascom Development Egypt | 1,455 bars | **ACTIVE LISTING** | EGX-listed subsidiary actively traded (only Swiss parent holding AG delisted from SIX Zurich in 2025). |
| **`RREI.CA`** | Arab Real Estate Investment (ALICO) | 1,455 bars | **ACTIVE LISTING** | Listed and trading on EGX. Not delisted. |
| **`SDTI.CA`** | Sharm Dreams for Tourism | 1,455 bars | **ACTIVE LISTING** | Listed and actively reporting on EGX. Not delisted. |
| **`SPMD.CA`** | Speed Medical | 1,361 bars | **ACTIVE LISTING** | Experienced regulatory scrutiny/halts in 2021–2022, but remains actively listed and traded. |
| **`UEGC.CA`** | El Saeed Contracting & Real Estate | 1,455 bars | **ACTIVE LISTING** | Actively listed and publishing board resolutions through August 2026. |

### Mechanism of the False Resolution:
The data ingestion script queried Yahoo Finance (`yfinance.download(tkr, start="2020-01-01", end="2026-01-01")`). Because Yahoo Finance purges historical daily bars for liquidated or delisted companies, the downloads returned complete historical series **precisely because these 8 companies are surviving, active entities**. Comparing 27 surviving stocks against 35 surviving stocks was mathematically incapable of measuring survivorship bias.

---

## 3. Historical Availability & Asymmetry of the 27-Stock Universe

The 27 core equities were audited for historical continuity from `2020-01-02` to `2026-08-16`:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                               27-STOCK UNIVERSE CONTINUITY PROFILE                               │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Standard Universe Session Count  │ 1,606 daily trading sessions (2020-01-02 to 2026-08-16)       │
│ Full Continuity Stocks (25/27)   │ 25 stocks have uninterrupted continuous daily records.        │
│ Late Commencing Stock            │ ORAS.CA begins on 2021-08-10 (1,224 bars, missing 19 months).  │
│ Early Terminated Stock           │ ESRS.CA ends on 2025-03-13 (1,263 bars, discontinued).       │
│ Calendar Anomaly Stock           │ ADIB.CA contains 1,609 bars (3 extra holiday trading bars).   │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Consequences for Cross-Sectional Breadth:
1. **Denominator Shifts:** The total number of reporting stocks $M_t$ in cross-sectional breadth aggregations shifts over time:
   * 2020-01-02 to 2021-08-09: $M_t = 26$ stocks (no `ORAS.CA`).
   * 2021-08-10 to 2025-03-13: $M_t = 27$ stocks (complete universe).
   * 2025-03-14 to 2026-08-16: $M_t = 26$ stocks (no `ESRS.CA`).
2. **Missing Value Handling:** In `phase2_market_regime.py`, missing stocks on any given date are omitted from the cross-sectional mean rather than imputed as 0% return. This avoids artificial drift, but confirms that universe composition was not static.
3. **Selection Bias Inherent to 27 Equities:** The 27 equities selected in August 2026 represented the largest, most liquid surviving blue-chips on the EGX. Equities that suffered corporate distress, insolvency, or involuntary delisting between 2020 and 2025 are completely unrepresented in the historical parquet files.

---

## 4. Formal Audit Classification

Under strict institutional audit criteria, the universe and survivorship state is formally classified as:

### **`SURVIVORSHIP_BIAS_UNRESOLVED`**

* **Reason:** No commercial point-in-time delisted stock database (such as Compustat Point-in-Time or Bloomberg EGX Historical Index Membership) was ingested.
* **Mandatory Action:** All future quantitative reports, research papers, and performance dashboards must display the permanent, non-removable disclaimer:
  > *`CAUTION: SURVIVORSHIP_BIAS_UNRESOLVED. Backtested win rates and Profit Factors evaluate active surviving equities and reflect an inherent upward survival selection bias.`*

---
*Survivorship and universe audit verified against exchange records and corporate registries.*
