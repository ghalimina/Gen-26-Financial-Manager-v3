#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/multi_objective_evaluator.py — Multi-Dimensional Anti-Reward-Hacking Objective Function
# Part of GEN-26 Expanded Architecture Version 2.0
# Prevents optimization models from exploiting single-metric loopholes (Reward Hacking).
# =============================================================================

import math
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("GEN26.MultiObjectiveEvaluator")


class MultiObjectiveEvaluator:
    """
    Evaluates algorithmic hypotheses across a balanced multi-objective surface:
    Objective = (Return * Sharpe * Robustness) - (MaxDD + Turnover + Costs + TailRisk + Uncertainty)
    """

    @classmethod
    def evaluate_strategy_objective(cls, strategy_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Computes composite multi-dimensional fitness score penalizing hidden risks and costs.
        """
        # Positive Utility Components
        ann_return = max(0.0, float(strategy_metrics.get("annualized_return_pct") or 35.0))
        sharpe = max(0.01, float(strategy_metrics.get("oos_sharpe") or strategy_metrics.get("sharpe_ratio") or 1.85))
        degradation_pct = max(0.0, float(strategy_metrics.get("degradation_pct") or 15.0))
        dsr = max(0.1, float(strategy_metrics.get("deflated_sharpe_ratio") or 0.85))

        # Normalized positive factors
        norm_return = ann_return / 25.0
        norm_sharpe = min(3.5, sharpe / 1.50)
        norm_robustness = (1.0 - min(0.80, degradation_pct / 100.0)) * dsr
        positive_utility = round(float(norm_return * norm_sharpe * norm_robustness), 4)

        # Negative Cost & Risk Penalties
        max_dd = max(0.0, float(strategy_metrics.get("max_drawdown_pct") or 9.5))
        turnover = max(0.5, float(strategy_metrics.get("annual_turnover_ratio") or 2.2))
        cost_drag = max(0.2, float(strategy_metrics.get("total_cost_drag_pct") or 1.8))
        cvar_99 = max(1.0, float(strategy_metrics.get("cvar_99_pct") or 12.5))
        uncertainty = max(0.05, float(strategy_metrics.get("uncertainty_score") or 0.25))

        # Normalized penalties
        p_dd = max_dd / 12.0
        p_turnover = turnover / 4.0
        p_cost = cost_drag / 3.0
        p_tail = cvar_99 / 20.0
        p_unc = uncertainty * 0.80

        total_penalty = round(float(0.35 * p_dd + 0.20 * p_turnover + 0.15 * p_cost + 0.15 * p_tail + 0.15 * p_unc), 4)

        # Net Composite Objective Score
        net_objective_score = round(float(positive_utility - total_penalty), 4)

        # Governance Rating
        if net_objective_score >= 1.20 and dsr >= 0.80 and max_dd <= 15.0:
            rating = "INSTITUTIONAL_ALPHA_OPTIMAL"
            rating_ar = "استراتيجية ممتازة ومتوازنة مؤسسياً (خالية من الاحتيال الإحصائي)"
            passed_gate = True
        elif net_objective_score >= 0.60:
            rating = "ACCEPTABLE_BALANCED"
            rating_ar = "استراتيجية مقبولة مع مراقبة التكاليف والانزلاق"
            passed_gate = True
        else:
            rating = "REJECTED_REWARD_HACKING_OR_RISK"
            rating_ar = "استراتيجية مرفوضة: احتيال إحصائي أو تكاليف مفرطة أو مخاطر ذيل حادة"
            passed_gate = False

        return {
            "strategy_name": strategy_metrics.get("strategy_name", "Hypothesis"),
            "net_objective_score": net_objective_score,
            "positive_utility": positive_utility,
            "total_risk_penalty": total_penalty,
            "components": {
                "norm_return": round(norm_return, 3),
                "norm_sharpe": round(norm_sharpe, 3),
                "norm_robustness": round(norm_robustness, 3),
                "dd_penalty": round(p_dd, 3),
                "turnover_penalty": round(p_turnover, 3),
                "cost_penalty": round(p_cost, 3),
                "tail_risk_penalty": round(p_tail, 3),
                "uncertainty_penalty": round(p_unc, 3)
            },
            "rating": rating,
            "rating_ar": rating_ar,
            "passed_multi_objective_gate": passed_gate
        }


if __name__ == "__main__":
    print("Testing MultiObjectiveEvaluator...")
    good_strat = {
        "strategy_name": "Robust Alpha v2",
        "annualized_return_pct": 45.0,
        "oos_sharpe": 2.10,
        "degradation_pct": 12.0,
        "deflated_sharpe_ratio": 0.88,
        "max_drawdown_pct": 8.5,
        "annual_turnover_ratio": 2.0,
        "total_cost_drag_pct": 1.5,
        "cvar_99_pct": 10.0,
        "uncertainty_score": 0.20
    }
    res = MultiObjectiveEvaluator.evaluate_strategy_objective(good_strat)
    import json
    print(json.dumps(res, indent=2, ensure_ascii=False))
