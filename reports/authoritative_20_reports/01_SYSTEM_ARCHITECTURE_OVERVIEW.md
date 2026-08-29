# 01. System Architecture Overview & Single Source of Truth (SSoT)

**Document Version:** `v3.2.0-Authoritative`  
**Publication Date:** `2026-08-29`  
**Status:** `PRODUCTION VERIFIED & INSTITUTIONALLY CERTIFIED`

---

## 1. Executive Summary
The **GEN-26 Institutional Quant Platform** is an enterprise-grade quantitative research, market intelligence, portfolio optimization, and risk management system built specifically for the **Egyptian Stock Exchange (EGX)**. The platform integrates institutional quantitative finance principles, machine learning feature engineering, Marcos López de Prado’s Advances in Financial Machine Learning (AFML) framework, a 7-Agent Autonomous Council, and strict fail-closed safety firewalls.

---

## 2. Master Single Source of Truth (SSoT) Hierarchy

```
+-------------------------------------------------------------------------------+
|                      MASTER SSoT HIERARCHY & SPECIFICATIONS                   |
+-------------------+-----------------------------------------------------------+
| SSoT Dimension    | Authoritative Production Standard & Invariant             |
+-------------------+-----------------------------------------------------------+
| 1. Universe SSoT  | 244 Total Listed Catalog -> 170 Liquid Core -> Top 24     |
|                   | Daily Focus Equities (Thndr-mapped with Egyptian ISINs).  |
+-------------------+-----------------------------------------------------------+
| 2. Friction SSoT  | 0.35% Round-Trip (0.20% Brokerage + 0.15% EGX/MCDR/FRA).  |
|                   | Note: 0.90% was a legacy placeholder and is superseded.   |
+-------------------+-----------------------------------------------------------+
| 3. Decision SSoT  | 7-Agent Council is the master decision framework,         |
|                   | integrating 4 calibrated factor scores + Macro/Risk/Flow. |
+-------------------+-----------------------------------------------------------+
| 4. Test SSoT      | 456 Automated Tests verified by raw discovery runner.     |
+-------------------+-----------------------------------------------------------+
| 5. Macro SSoT     | CBE Deposit 19.00%, Lending 20.00%, Inflation 14.90%,     |
|                   | USD/EGP 50.20, Hurdle Rate with CRP: 30.70% Annualized.   |
+-------------------+-----------------------------------------------------------+
```

---

## 3. Core 5-Layer Layered Stack Architecture

```
+-------------------------------------------------------------------------------+
| Layer 5: Institutional RTL Web Dashboard & REST API (/api/*, Sub-200ms Cache)  |
+-------------------------------------------------------------------------------+
                                      |
+-------------------------------------------------------------------------------+
| Layer 4: Self-Improving Quant Council & Autonomous Research Lab (7 Agents)     |
+-------------------------------------------------------------------------------+
                                      |
+-------------------------------------------------------------------------------+
| Layer 3: Multi-Source Market Intelligence & Deep 48-Feature Quant Fusion AI    |
+-------------------------------------------------------------------------------+
                                      |
+-------------------------------------------------------------------------------+
| Layer 2: 10 Classic Quant Books Mathematical Suite & Risk Sizing Engine        |
+-------------------------------------------------------------------------------+
                                      |
+-------------------------------------------------------------------------------+
| Layer 1: EGX Market Microstructure, Canonical Price Store & Data Persistence   |
+-------------------------------------------------------------------------------+
```

### Layer 1: EGX Market Microstructure & Canonical Price SSoT
- **Canonical Price Service** (`core/market_price_service.py`): Real-time Single Source of Truth (SSoT) aggregating TradingView real-time feeds, yfinance, and official EGX settlement quotes.
- **Circuit Breaker Invariants** (`core/egx_trading_rules_engine.py`): $\pm 10\%$ and $\pm 20\%$ price limits, intraday 10-minute cooling auctions, T+0/T+1/T+2 settlement calendars.
- **SQLite WAL Persistence** (`core/database_engine.py`): High-throughput ACID-compliant database with write-ahead logging (WAL) storing council decisions, failure memory, and walk-forward research iterations.

### Layer 2: 10 Classic Quant Books Mathematical Suite
- **Piotroski F-Score** (`core/quant_books_engine.py`): 9-point fundamental accounting quality framework (COMI.CA: 9/9).
- **Peter Lynch Valuation Engine**: Classic PEG ($\frac{P/E}{G}$) and Dividend-Adjusted PEGY ($\frac{P/E}{G + Y}$), Net Cash per share, and classification.
- **Steve Nison Japanese Candlesticks**: Pattern recognition (Engulfing, Hammer, Morning Star, Piercing Line).
- **John J. Murphy Technical Indicators**: ADX 14-period trend filter and Fibonacci retracements ($23.6\%, 38.2\%, 50.0\%, 61.8\%, 78.6\%$).
- **Mark Douglas Anti-Revenge Circuit Breaker**: 24-hour psychological lockout after 2 consecutive stop-losses; minimum $R:R \ge 1:2.5$.

### Layer 3: Multi-Source Intelligence & 48-Feature Quant Fusion Engine
- **5 Live Intelligence Feeds** (`core/multi_source_intelligence.py`): Mubasher Egypt, Al Borsa News, Enterprise Press, Central Bank of Egypt (CBE) official telemetry, Global Commodities (Gold, Brent, Gas, Fertilizers) & London GDRs.
- **48-Dimensional Quant Feature Tensor** (`core/deep_quant_fusion_engine.py`): 12 Technicals, 12 Fundamentals/Books, 12 Macro/Arbitrage, 12 Smart Money/NLP features.
- **Two-Stage Meta-Labeling Model**: Primary directional forecast combined with a secondary Meta-Confidence model predicting success probability and scaling dynamic position sizing:
  $$f(p) = \min\left(1.0, \max\left(0.0, \frac{p - 0.60}{0.85 - 0.60}\right)\right)$$

### Layer 4: Self-Improving Multi-Agent Quant Council & Autonomous Lab
- **7-Agent Deliberation Council** (`core/multi_agent_council.py`): Macro, Fundamental, Technical, Quantitative, Risk, Smart Money, and Critic Agents.
- **Autonomous Research Lab** (`core/autonomous_research_lab.py`): Automated hypothesis generation, purged walk-forward cross-validation, adversarial screening, and promotion verdicts.
- **Episodic Failure Memory**: Root-cause analysis and quarantined patterns to prevent repeating historical mistakes.

### Layer 5: REST API & Institutional Arabic Web Terminal
- **Flask REST API Server** (`dashboard/app.py`): 14 endpoint categories with in-memory TTL caching delivering sub-200ms response times.
- **Institutional RTL Dashboard** (`dashboard/templates/index.html`): Real-time market radar, Stock dossiers, Real portfolio tracker, TradingView charts, Algo order blotter, and Autonomous Research Lab.

---

## 4. High-Level Data Flow Sequence

1. **Ingestion**: Raw prices, news, filings, macro rates, and London GDR prices are ingested and validated.
2. **Feature Extraction**: 48 normalized factors are computed for each tradable stock with sector neutralization.
3. **Council Deliberation**: The 7 agents evaluate the stock independently and cast weighted votes.
4. **Risk Gating**: Mark Douglas anti-revenge, sector concentration (max 35%), and dynamic ratcheting trailing stops are enforced.
5. **Execution Advisory**: Final high-conviction recommendations (`APPROVED_BUY`, `HOLD_OR_REJECT`) are presented in the UI and recorded in the SQLite audit log.

---

## 5. Grand Finale Institutional Innovations (Sprints B, C & D)

### 1. Reality Gap & Observability Suite
A dedicated live verification matrix (`dashboard/templates/index.html` $\to$ `#tab-observatory`) that cross-checks reported documentation specs against the live SQLite database and in-memory engines:
- **0 Discrepancy Invariant**: Ensures universe catalog (244), CBE policy rates (19.00%), round-trip friction (0.35%), active features (48), and DSR threshold (0.80) are 100% matched in real time.
- **Rolling Forecast vs. Actual Tracker**: Empirical hit rate and Information Coefficient (IC) tracking across closed prediction horizons.

### 2. Top 3 Golden Buy Opportunities Spotlight & Dynamic Portfolio Sizer
- **Top 3 Golden Buy Cards**: Dynamically extracts top liquid buy-rated equities directly from the cross-sectional ranking engine.
- **Dynamic Portfolio Sizer**: Allocates capital adhering to frozen risk rules:
  * Rank #1: Maximum 30.0% capital allocation
  * Rank #2: Maximum 25.0% capital allocation
  * Rank #3: Maximum 20.0% capital allocation
  * Emergency Cash Buffer: Minimum 25.0% - 35.0% unallocated liquidity reserved to capitalize on market drawdowns.

### 3. 4-Stage Governed Promotion Gate
Enforces Marcos López de Prado's Deflated Sharpe Ratio (DSR $\ge 0.80$) and multi-tier production gating:
- `STAGE 1: SHADOW_MODE` (30 Sessions empirical logging)
- `STAGE 2: PAPER_FULL` (0.35% friction & 10% CGT deduction)
- `STAGE 3: LIVE_MICRO` (Max 5% portfolio risk allocation, DSR $\ge 0.80$)
- `STAGE 4: SCALE_UP` (Full allocation, degradation gap $\le 20\%$)

---
**Institutional Compliance Notice:**  
*Document certified under GEN-26 Institutional Risk Governance Protocol v3.2.0. Verified with 456 automated STLC test suites.*
