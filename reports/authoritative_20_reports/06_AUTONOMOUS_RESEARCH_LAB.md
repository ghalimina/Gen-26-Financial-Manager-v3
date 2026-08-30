# 06 — Autonomous Quantitative Research Lab & 6 Baselines
**GEN-26 Quantitative Autonomous Platform | Version 3.2.0-Authoritative | Institutional Whitepaper**

---

## Executive Summary
The Autonomous Research Lab (`core/multi_agent_council.py` & `core/baseline_benchmark_suite.py`) operates as a self-improving algorithmic laboratory. It generates quantitative hypotheses, runs automated walk-forward backtests, and validates models against **6 Standard Institutional Baselines**.

---

## 1. 6 Standard Institutional Baseline Suite

Every candidate model must outperform all 6 industry baselines with statistical significance ($p < 0.01$):

1. **`BUY_HOLD_EGX30`**: Passive holding of the EGX30 benchmark.
2. **`EQUAL_WEIGHT_244`**: Daily rebalanced 1/N equal allocation across all 244 EGX equities.
3. **`MOMENTUM_20D`**: Top 10 stocks ranked by 20-day trailing rate of return.
4. **`SMA_20_50_CROSS`**: Dual Moving Average Crossover trend-following system.
5. **`RANDOM_WALK_SIMULATOR`**: Monte Carlo 1,000-path geometric Brownian motion simulator.
6. **`GEN26_ACTIVE_PRODUCTION`**: Current production champion model.

---

## 2. Statistical Significance Hurdle

To prevent cherry-picked backtest anomalies, a model is rejected unless:

$$t_{	ext{stat}} = rac{\mu_{	ext{model}} - \mu_{	ext{baseline}}}{\sigma_{	ext{diff}} / \sqrt{N}} > 2.576 \quad (p < \mathbf{0.01})$$
