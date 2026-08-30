# 01 — System Architecture Overview & Master SSoT Hierarchy
**GEN-26 Quantitative Autonomous Platform | Version 3.2.0-Authoritative | Institutional Whitepaper**

---

## Executive Summary & Design Philosophy
The **GEN-26 Platform** is an institutional-grade, multi-horizon algorithmic quantitative trading, macroeconomic regime detection, and self-improving artificial intelligence platform tailored specifically for the **Egyptian Exchange (EGX)**.

The system enforces a **Zero-Mock, Strict Invariance Policy**: every data point, market price, corporate metric, and signal originates from verified canonical services and real-time feeds with zero synthetic assumptions.

---

## 1. Master SSoT Hierarchy & 8-Layer Architecture

The platform is structured into 8 strictly governed architectural layers:

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
|                                  | UncertaintyEngine Continuous CDF Probabilistic Distribution     |
+----------------------------------+------------------------------------------------------------------+
| Layer 4: Trade Selection Gate    | Independent Model: Net Edge >= 1.00% Required Hurdle             |
|                                  | Net Edge = E(Return) - (0.35% + Dynamic Slippage) - Uncertainty |
+----------------------------------+------------------------------------------------------------------+
| Layer 5: Risk & Sizing Engine    | Modified Kelly / Mark Douglas Sizing, Max 1.0% Risk / Trade     |
|                                  | Dynamic Azimut Gold ETF (AZG.CA) Tail-Risk Hedge Allocation     |
+----------------------------------+------------------------------------------------------------------+
| Layer 6: Self-Improvement Loop   | 7-Agent Autonomous Council & Episodic Failure Memory Database    |
|                                  | Purged Walk-Forward Retraining & Baseline Benchmark Suite        |
+----------------------------------+------------------------------------------------------------------+
| Layer 7: Governance Gatekeeper   | Anti-Reward-Hacking Multi-Objective Function (Fitness >= 1.00)   |
|                                  | 4-Stage Promotion Gate (Candidate -> Paper -> Shadow -> Live)    |
+----------------------------------+------------------------------------------------------------------+
| Layer 8: Dashboard & Observator  | Flask Real-Time Web Server (<200ms In-Memory Caching), REST APIs |
|                                  | Reality Gap Live Auditor & Forecast vs Actual Accuracy Tracker   |
+====================================================================================================+
```

---

## 2. 3-Timestamp Anti-Leakage Protocol

To eliminate look-ahead bias in backtesting and live simulation, all ingested data records enforce the strict temporal ordering:

$$	ext{effective\_time} \ge 	ext{publication\_time} \ge 	ext{event\_time}$$

1. **$	ext{event\_time}$**: Exact real-world timestamp when the underlying economic/corporate event occurred.
2. **$	ext{publication\_time}$**: Timestamp when the information was published by an authorized source.
3. **$	ext{effective\_time}$**: Exact market session timestamp when the information became actionable for algorithmic execution.

---

## 3. End-to-End Live Simulation & Verification

The platform's execution pipeline is continuously audited via automated verification scripts:
- **`scripts/simulate_live_quant_cycle.py`**: Executes live canonical ingestion, multi-horizon probabilistic forecasting, uncertainty scoring, trade selection gating, 7-agent deliberation, and atomic SQLite persistence.
- **`scripts/automated_consistency_audit.py`**: Audits 21 Single Source of Truth (SSoT) invariants.
- **Master STLC Test Battery**: 474 automated unit, integration, and stress tests passing 100% with zero failures.
