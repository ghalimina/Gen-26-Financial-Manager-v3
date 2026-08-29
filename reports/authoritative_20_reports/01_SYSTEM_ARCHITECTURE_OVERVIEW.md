# 01. System Architecture Overview & High-Level Data Flow

## 1. Executive Summary
The **GEN-26 Institutional Quant Platform** is an enterprise-grade quantitative research, market intelligence, portfolio optimization, and risk management system built specifically for the **Egyptian Stock Exchange (EGX)**. The platform integrates institutional quantitative finance principles, machine learning feature engineering, Marcos López de Prado’s Advances in Financial Machine Learning (AFML) framework, a 7-Agent Autonomous Council, and strict fail-closed safety firewalls.

---

## 2. Core 5-Layer Layered Stack Architecture

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
- **Piotroski F-Score** (`core/quant_books_engine.py`): 9-point fundamental accounting quality framework.
- **Peter Lynch Valuation Engine**: PEG ratios, Net Cash per share, and classification (`FAST_GROWER`, `STALWART`, `SLOW_GROWER`, `CYCLICAL`).
- **Steve Nison Japanese Candlesticks**: Pattern recognition (Engulfing, Hammer, Morning Star, Piercing Line).
- **John J. Murphy Technical Indicators**: ADX 14-period trend filter and Fibonacci retracements ($23.6\%, 38.2\%, 50.0\%, 61.8\%, 78.6\%$).
- **Mark Douglas Anti-Revenge Circuit Breaker**: 24-hour psychological lockout after 2 consecutive stop-losses; minimum $R:R \ge 1:2.5$.

### Layer 3: Multi-Source Intelligence & 48-Feature Quant Fusion Engine
- **5 Live Intelligence Feeds** (`core/multi_source_intelligence.py`): Mubasher Egypt, Al Borsa News, Enterprise Press, Central Bank of Egypt (CBE) official telemetry, Global Commodities (Gold, Brent, Gas, Fertilizers) & London GDRs.
- **48-Dimensional Quant Feature Tensor** (`core/deep_quant_fusion_engine.py`): 12 Technicals, 12 Fundamentals/Books, 12 Macro/Arbitrage, 12 Smart Money/NLP features.
- **Two-Stage Meta-Labeling Model**: Primary directional forecast combined with a secondary Meta-Confidence model predicting success probability and scaling dynamic position sizing.

### Layer 4: Self-Improving Multi-Agent Quant Council & Autonomous Lab
- **7-Agent Deliberation Council** (`core/multi_agent_council.py`): Macro, Fundamental, Technical, Quantitative, Risk, Smart Money, and Critic Agents.
- **Autonomous Research Lab** (`core/autonomous_research_lab.py`): Automated hypothesis generation, purged walk-forward cross-validation, adversarial screening, and promotion verdicts.
- **Episodic Failure Memory**: Root-cause analysis and quarantined patterns to prevent repeating historical mistakes.

### Layer 5: REST API & Institutional Arabic Web Terminal
- **Flask REST API Server** (`dashboard/app.py`): 14 endpoint categories with in-memory TTL caching delivering sub-200ms response times.
- **Institutional RTL Dashboard** (`dashboard/templates/index.html`): Real-time market radar, Stock dossiers, Real portfolio tracker, TradingView charts, Algo order blotter, and Autonomous Research Lab.

---

## 3. High-Level Data Flow Sequence

1. **Ingestion**: Raw prices, news, filings, macro rates, and London GDR prices are ingested and validated.
2. **Feature Extraction**: 48 normalized factors are computed for each tradable stock.
3. **Council Deliberation**: The 7 agents evaluate the stock independently and cast weighted votes.
4. **Risk Gating**: Mark Douglas anti-revenge, sector concentration (max 35%), and dynamic ratcheting trailing stops are enforced.
5. **Execution Advisory**: Final high-conviction recommendations (`APPROVED_BUY`, `HOLD_OR_REJECT`) are presented in the UI and recorded in the SQLite audit log.
