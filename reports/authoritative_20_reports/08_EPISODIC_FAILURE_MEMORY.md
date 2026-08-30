# 08 — Episodic Failure Memory & Anti-Overfitting Safeguards
**GEN-26 Quantitative Autonomous Platform | Version 3.2.0-Authoritative | Institutional Whitepaper**

---

## Executive Summary
The **Episodic Failure Memory** module (`core/episodic_failure_memory.py`) prevents the platform from repeating historic quantitative mistakes. Every rejected hypothesis, stop-loss trigger, or regime breakdown is archived in SQLite table `failure_cases_memory`.

---

## 1. Automated Feature Quarantine

When an experiment fails due to look-ahead bias or extreme regime overfitting, its constituent feature combinations are quarantined:
- **Temporary Quarantine**: 90 market sessions.
- **Strict Prohibition**: Banned from inclusion in any Stage 1 hypothesis until cleared by the Adversarial Critic Agent.
