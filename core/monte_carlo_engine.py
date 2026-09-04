#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/monte_carlo_engine.py — 1,000-Path Monte Carlo Portfolio Simulator
# Simulates fat-tailed capital trajectories, VaR/CVaR cones, and profit probabilities.
# =============================================================================

import os
import sys
import math
import random
import datetime
import logging
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.real_portfolio import RealPortfolioTracker
from core.frozen_invariants import FrozenRiskInvariants

logger = logging.getLogger("GEN26.MonteCarloEngine")


class MonteCarloEngine:
    """
    Institutional Monte Carlo Capital Trajectory Simulator for EGX Portfolios.
    """

    @classmethod
    def simulate_trajectories(
        cls,
        initial_equity: Optional[float] = None,
        days: int = 60,
        num_paths: int = 1000,
        annual_drift: float = 0.280,          # Realistic target annual return (28.00%)
        annual_volatility: float = 0.22,      # EGX constituent weighted annual volatility
        cash_ratio: float = 0.35,             # 35% mandatory risk-free cash buffer
        risk_free_rate: float = 0.190         # CBE Overnight Deposit rate (19.00%)
    ) -> Dict[str, Any]:
        """
        Runs 1,000 Monte Carlo simulation paths over specified horizon.
        """
        if initial_equity is None or initial_equity <= 0:
            analysis = RealPortfolioTracker.analyze_real_portfolio()
            initial_equity = float(analysis.get("portfolio_equity_egp", 100000.0))

        days = max(5, min(365, int(days)))
        num_paths = max(100, min(2000, int(num_paths)))

        # Blended drift and volatility accounting for risk-free cash buffer
        stock_ratio = 1.0 - cash_ratio
        blended_drift = (stock_ratio * annual_drift) + (cash_ratio * risk_free_rate)
        blended_volatility = stock_ratio * annual_volatility

        dt = 1.0 / 252.0  # 252 trading days per year
        daily_drift = (blended_drift - 0.5 * (blended_volatility ** 2)) * dt
        daily_vol = blended_volatility * math.sqrt(dt)

        # Pre-seed for reproducibility while supporting stochastic spread
        random.seed(42)
        nu = 5.0  # Degrees of freedom (fat-tail parameter for emerging market equities)
        t_scale = math.sqrt((nu - 2.0) / nu)  # Scale factor so Var(shock) = 1.0

        # Generate paths: matrix of [num_paths, days + 1]
        paths = []
        for _ in range(num_paths):
            path = [initial_equity]
            curr = initial_equity
            for _ in range(days):
                # Exact Student's t-distribution sampling: T = Z / sqrt(V / nu)
                z = random.gauss(0, 1)
                v = random.gammavariate(nu / 2.0, 2.0)  # Chi-squared(nu)
                t_shock = (z / math.sqrt(v / nu)) * t_scale  # Standardized Student's t (mean=0, var=1)

                daily_return = math.exp(daily_drift + daily_vol * t_shock)
                curr = round(curr * daily_return, 2)
                path.append(curr)
            paths.append(path)

        # Calculate time-slice percentiles
        percentile_10 = []
        percentile_50 = []  # Median
        percentile_90 = []
        worst_path = []
        best_path = []

        for d in range(days + 1):
            slice_vals = sorted([p[d] for p in paths])
            p10 = slice_vals[int(0.10 * num_paths)]
            p50 = slice_vals[int(0.50 * num_paths)]
            p90 = slice_vals[int(0.90 * num_paths)]
            pmin = slice_vals[0]
            pmax = slice_vals[-1]

            percentile_10.append(round(p10, 2))
            percentile_50.append(round(p50, 2))
            percentile_90.append(round(p90, 2))
            worst_path.append(round(pmin, 2))
            best_path.append(round(pmax, 2))

        final_values = sorted([p[-1] for p in paths])
        median_final = percentile_50[-1]
        mean_final = round(sum(final_values) / num_paths, 2)

        # Value at Risk & CVaR
        var_95_val = final_values[int(0.05 * num_paths)]
        var_99_val = final_values[int(0.01 * num_paths)]

        var_95_egp = round(initial_equity - var_95_val, 2)
        var_95_pct = round((var_95_egp / initial_equity) * 100.0, 2)

        var_99_egp = round(initial_equity - var_99_val, 2)
        var_99_pct = round((var_99_egp / initial_equity) * 100.0, 2)

        # CVaR (Expected Shortfall)
        cvar_95_tail = final_values[:int(0.05 * num_paths)]
        cvar_95_val = sum(cvar_95_tail) / max(1, len(cvar_95_tail))
        cvar_95_egp = round(initial_equity - cvar_95_val, 2)
        cvar_95_pct = round((cvar_95_egp / initial_equity) * 100.0, 2)

        # Profit Probabilities
        profitable_count = sum(1 for v in final_values if v > initial_equity)
        prob_profit_pct = round((profitable_count / num_paths) * 100.0, 1)

        target_return_val = initial_equity * (1.0 + (annual_drift * (days / 252.0)))
        target_achieved_count = sum(1 for v in final_values if v >= target_return_val)
        prob_target_pct = round((target_achieved_count / num_paths) * 100.0, 1)

        # Sample trajectories for UI visualization (10 paths)
        sample_paths = [paths[i] for i in range(0, num_paths, num_paths // 10)][:10]

        return {
            "initial_equity_egp": initial_equity,
            "horizon_days": days,
            "simulations_count": num_paths,
            "blended_annual_drift_pct": round(blended_drift * 100.0, 2),
            "blended_annual_volatility_pct": round(blended_volatility * 100.0, 2),
            "cash_buffer_pct": round(cash_ratio * 100.0, 1),
            "expected_median_final_egp": median_final,
            "expected_mean_final_egp": mean_final,
            "expected_gain_pct": round(((median_final - initial_equity) / initial_equity) * 100.0, 2),
            "prob_profit_pct": prob_profit_pct,
            "prob_target_pct": prob_target_pct,
            "var_95": {
                "final_equity": var_95_val,
                "loss_egp": max(0.0, var_95_egp),
                "loss_pct": max(0.0, var_95_pct)
            },
            "var_99": {
                "final_equity": var_99_val,
                "loss_egp": max(0.0, var_99_egp),
                "loss_pct": max(0.0, var_99_pct)
            },
            "cvar_95": {
                "expected_shortfall_egp": max(0.0, cvar_95_egp),
                "expected_shortfall_pct": max(0.0, cvar_95_pct)
            },
            "timeline_days": list(range(days + 1)),
            "cones": {
                "p90_bullish": percentile_90,
                "p50_median": percentile_50,
                "p10_bearish": percentile_10,
                "worst_case": worst_path,
                "best_case": best_path
            },
            "sample_paths": sample_paths
        }
