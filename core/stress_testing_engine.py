#!/usr/bin/env python3
# =============================================================================
# core/stress_testing_engine.py — GEN-26 Monte Carlo Portfolio Stress Testing
# Institutional Risk Assessment Engine:
# 1. 10,000-Path Geometric Brownian Motion (GBM) Monte Carlo Simulation.
# 2. Value at Risk (VaR 95% and VaR 99%) over 30-day forward incubation horizon.
# 3. Conditional VaR (CVaR 99% / Expected Shortfall).
# 4. Automated Execution Guard: If VaR 99% > 12%, halts automated broker orders.
# =============================================================================

import os
import sys
import math
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)


class MonteCarloStressTester:
    """
    Monte Carlo Geometric Brownian Motion Simulator and VaR/CVaR Risk Engine.
    """

    VAR_99_HALT_THRESHOLD_PCT = 12.00  # Hard stop if 30-day VaR 99% exceeds 12.0%
    DEFAULT_N_SIMULATIONS = 10_000
    DEFAULT_HORIZON_DAYS = 30

    @classmethod
    def run_portfolio_monte_carlo(
        cls,
        weights: Optional[Dict[str, float]] = None,
        annualized_return: float = 0.28,
        annualized_volatility: float = 0.18,
        initial_portfolio_value_egp: float = 1_000_000.0,
        n_simulations: int = DEFAULT_N_SIMULATIONS,
        horizon_days: int = DEFAULT_HORIZON_DAYS
    ) -> Dict[str, Any]:
        """
        Executes 10,000-path GBM Monte Carlo simulation over the forward horizon.
        Calculates VaR 95%, VaR 99%, and CVaR 99% (Expected Shortfall).
        """
        np.random.seed(42)
        dt = 1.0 / 252.0
        time_steps = horizon_days
        mu = annualized_return
        sigma = annualized_volatility

        # Vectorized GBM simulation matrix: (n_simulations, time_steps)
        daily_drift = (mu - 0.5 * sigma**2) * dt
        daily_vol = sigma * np.sqrt(dt)

        shock_matrix = np.random.normal(0.0, 1.0, size=(n_simulations, time_steps))
        cumulative_returns = np.exp(np.cumsum(daily_drift + daily_vol * shock_matrix, axis=1))

        # Ending terminal portfolio values and returns
        terminal_multipliers = cumulative_returns[:, -1]
        terminal_returns_pct = (terminal_multipliers - 1.0) * 100.0
        terminal_values_egp = initial_portfolio_value_egp * terminal_multipliers

        # Sort returns ascending (losses are negative)
        sorted_returns = np.sort(terminal_returns_pct)

        # 1. Parametric / Historical Percentiles
        var_95_idx = int(0.05 * n_simulations)
        var_99_idx = int(0.01 * n_simulations)

        var_95_pct = round(abs(float(sorted_returns[var_95_idx])), 2)
        var_99_pct = round(abs(float(sorted_returns[var_99_idx])), 2)

        # 2. Conditional VaR (Expected Shortfall = average of worst 1% losses)
        worst_1pct_losses = sorted_returns[:var_99_idx]
        cvar_99_pct = round(abs(float(np.mean(worst_1pct_losses))) if len(worst_1pct_losses) > 0 else var_99_pct * 1.2, 2)

        # 3. VaR Invariant Check
        execution_halted = bool(var_99_pct > cls.VAR_99_HALT_THRESHOLD_PCT)
        var_status_ar = "🔴 تم تعليق الأوامر الآلية (مخاطر VaR > 12%)" if execution_halted else "🟢 استقرار المخاطر وضمن الحدود الآمنة (VaR <= 12%)"

        return {
            "status": "MONTE_CARLO_SIMULATION_SUCCESS",
            "n_simulations": n_simulations,
            "horizon_days": horizon_days,
            "annualized_volatility_pct": round(sigma * 100.0, 2),
            "expected_annual_return_pct": round(mu * 100.0, 2),
            "initial_value_egp": initial_portfolio_value_egp,
            "var_95_pct": var_95_pct,
            "var_99_pct": var_99_pct,
            "cvar_99_pct": cvar_99_pct,
            "var_99_loss_egp": round(initial_portfolio_value_egp * (var_99_pct / 100.0), 2),
            "cvar_99_loss_egp": round(initial_portfolio_value_egp * (cvar_99_pct / 100.0), 2),
            "var_99_halt_threshold_pct": cls.VAR_99_HALT_THRESHOLD_PCT,
            "execution_halted": execution_halted,
            "can_execute_orders": not execution_halted,
            "var_status_ar": var_status_ar,
            "percentiles": {
                "p5": round(float(np.percentile(terminal_returns_pct, 5)), 2),
                "p25": round(float(np.percentile(terminal_returns_pct, 25)), 2),
                "median_p50": round(float(np.percentile(terminal_returns_pct, 50)), 2),
                "p75": round(float(np.percentile(terminal_returns_pct, 75)), 2),
                "p95": round(float(np.percentile(terminal_returns_pct, 95)), 2)
            }
        }


# Default alias
MonteCarloSimulator = MonteCarloStressTester


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    import json
    res = MonteCarloStressTester.run_portfolio_monte_carlo()
    print("Monte Carlo 10,000-Path Simulation Results:")
    print(json.dumps(res, ensure_ascii=False, indent=2))
