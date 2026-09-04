# 01 — System Architecture Overview & Master SSoT Hierarchy
**GEN-26 Quantitative Autonomous Platform | Version 3.2.0-Authoritative | Institutional Whitepaper**
*Last Synchronized: 2026-08-30 14:19:12 | Status: PRODUCTION_READY (27/27 SSoT Invariants PASS)*

---

## Executive Summary & Design Philosophy
The **GEN-26 Platform** is an institutional-grade, multi-horizon algorithmic quantitative trading, macroeconomic regime detection, and self-improving artificial intelligence platform tailored specifically for the **Egyptian Exchange (EGX)**.

The system enforces a **Zero-Mock, Strict Invariance Policy**: every data point, market price, corporate metric, and signal originates from verified canonical services and real-time feeds with zero synthetic assumptions.

---

## 1. Master SSoT Hierarchy & 8-Layer Architecture

```
+====================================================================================================+
|                                MASTER SSoT HIERARCHY & ARCHITECTURE                                |
+====================================================================================================+
| Layer 1: Data Ingestion SSoT     | 5-Tier Data Hierarchy (Tier 1 Primary to Tier 5 Institutional)   |
|                                  | 3-Timestamp Anti-Leakage Invariant (effective >= pub >= event)   |
+----------------------------------+------------------------------------------------------------------+
| Layer 2: Feature Pipeline (48D)  | Technical, Fundamental, Microstructure, Macro, Market Breadth   |
|                                  | Fractional Differentiation (d=0.35-0.45) for Memory Stationarity |
+----------------------------------+------------------------------------------------------------------+
| Layer 3: AI & Uncertainty Layer  | Two-Stage Meta-Labeling (Random Forest + LightGBM Classifier)    |
|                                  | Multi-Model LLM Router (Claude 3.5, DeepSeek-V3, GPT-4o, Gemini) |
+----------------------------------+------------------------------------------------------------------+
| Layer 4: Trade Selection Gate    | Independent Model: Net Edge >= 1.00% Required Hurdle             |
|                                  | Net Edge = E(Return) - (0.35% + Dynamic Slippage) - Uncertainty |
+----------------------------------+------------------------------------------------------------------+
| Layer 5: Risk & Sizing Engine    | Modified Kelly / Mark Douglas Sizing, Max 1.0% Risk / Trade     |
|                                  | 35% Risk-Free Cash Buffer Floor, Mandatory -7.0% Stop Loss       |
+----------------------------------+------------------------------------------------------------------+
| Layer 6: Self-Improvement Loop   | 7-Agent Council + 9-Agent TradingAgents Dialectical Framework   |
|                                  | Episodic Failure Memory Database & Purged Walk-Forward Gate      |
+----------------------------------+------------------------------------------------------------------+
| Layer 7: Push & Alerts Gateway   | Telegram Bot Real-Time Push Gateway (Targets +8%/+15%, Stops)    |
|                                  | Real Portfolio Persistent CRUD Engine & Audit Logging            |
+----------------------------------+------------------------------------------------------------------+
| Layer 8: Dashboard & Observator  | Flask Real-Time Server (<200ms In-Memory Caching), REST APIs     |
|                                  | EGX 244 Sector Heatmap & 1,000-Path Monte Carlo Capital Cone     |
+====================================================================================================+
```

---

## 2. 3-Timestamp Anti-Leakage Protocol

$$\text{effective\_time} \ge \text{publication\_time} \ge \text{event\_time}$$

1. **$\text{event\_time}$**: Exact real-world timestamp when the underlying economic/corporate event occurred.
2. **$\text{publication\_time}$**: Timestamp when the information was published by an authorized source.
3. **$\text{effective\_time}$**: Exact market session timestamp when the information became actionable for algorithmic execution.

---

## 3. 4 Elite Extension Modules Implemented
1. **Multi-Model LLM Router (`core/trading_agents/llm_router.py`)**: Hot-swappable connectors to Claude 3.5 Sonnet, DeepSeek-V3, GPT-4o, and Gemini 1.5 Pro with deterministic offline fallback.
2. **Telegram Bot Real-Time Push Gateway (`core/telegram_notifier.py` / `core/portfolio_alert_engine.py`)**: Real-time push alerts on Target Hits (+8.0% / +15.0%), Stop Loss proximity, and ex-dividend reminders.
3. **Interactive EGX 244 Sector Treemap Heatmap (`core/market_heatmap_engine.py`)**: Complete hierarchical sector aggregation and volume-weighted performance for all 244 Egyptian equities.
4. **Monte Carlo 1,000-Path Capital Trajectory Simulator (`core/monte_carlo_engine.py`)**: Simulates fat-tailed Student's t distribution paths with VaR 95%, VaR 99%, CVaR, and probability cones.
