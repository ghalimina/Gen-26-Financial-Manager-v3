#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, math, logging
from typing import Dict, Any, Optional

from .multi_layer_scanner import MultiLayerScanner

logger = logging.getLogger("GEN26.AlphaScorer")

class AlphaScorer:
    """
    Computes transparent Alpha Score (0-100), Win Probability, and Opportunity Score.
    """

    @classmethod
    def calculate_alpha_score(cls, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        stock_rec = scan_result.get("stock_rec")
        layer_scores = scan_result.get("layer_scores", {})
        weights = scan_result.get("layer_weights", MultiLayerScanner.get_regime_weights())

        # Ground in authentic overall score if available from precomputed rankings
        if stock_rec and stock_rec.get("overall_score") is not None:
            alpha_score = round(float(stock_rec["overall_score"]), 1)
        else:
            raw_score = 0.0
            for k, w in weights.items():
                raw_score += layer_scores.get(k, 50.0) * w
            alpha_score = round(max(10.0, min(100.0, raw_score)), 1)

        # Empirically calibrated Win Probability P(R > 0)
        if stock_rec and stock_rec.get("probability_up_pct") is not None:
            prob_profit = round(float(stock_rec["probability_up_pct"]), 1)
        else:
            prob_profit = round(50.0 + (alpha_score - 50.0) * 0.60, 1)
            prob_profit = max(25.0, min(88.0, prob_profit))

        # Expected 20D Return %
        if stock_rec and stock_rec.get("expected_return_pct") is not None:
            exp_return_pct = round(float(stock_rec["expected_return_pct"]), 2)
        else:
            exp_return_pct = round(1.0 + ((alpha_score - 50.0) / 50.0) * 8.0, 2)

        # Uncertainty Score (0.05 - 0.90)
        if stock_rec and stock_rec.get("uncertainty_score") is not None:
            uncertainty_score = round(float(stock_rec["uncertainty_score"]), 2)
        else:
            uncertainty_score = round(1.0 - (alpha_score / 120.0), 2)
            uncertainty_score = max(0.10, min(0.90, uncertainty_score))

        # Liquidity multiplier
        liq_mult = 1.00
        risk_factor = 0.20

        # Opportunity Score = ExpReturn * Prob * Liq * (1 - Risk)
        opportunity_score = round(exp_return_pct * (prob_profit / 100.0) * liq_mult * (1.0 - risk_factor), 2)

        # Classification Tier & Action Verdict
        rec_act = (stock_rec.get("action") or stock_rec.get("decision")) if stock_rec else None
        if rec_act in ["STRONG_BUY", "BUY"] or alpha_score >= 80.0:
            tier = "STRONG_ALPHA"
            tier_ar = "ألفا صاعدة (Alpha >= 80)"
            action_verdict = "STRONG_BUY" if alpha_score >= 80.0 else "BUY"
        elif alpha_score >= 70.0:
            tier = "MODERATE_ALPHA"
            tier_ar = "ألفا معتدلة (Alpha 70-79)"
            action_verdict = "BUY"
        elif alpha_score >= 55.0 or rec_act in ["WATCH", "HOLD"]:
            tier = "NEUTRAL_WATCH"
            tier_ar = "مراقبة واحتفاظ (Alpha 55-69)"
            action_verdict = "WATCH"
        else:
            tier = "UNDERPERFORMANCE_AVOID"
            tier_ar = "تجنب ومخاطر (Alpha < 55)"
            action_verdict = "AVOID"

        return {
            "ticker": scan_result.get("ticker", "UNKNOWN"),
            "current_price": scan_result.get("current_price", 0.0),
            "alpha_score": alpha_score,
            "win_prob": prob_profit,
            "win_probability_pct": prob_profit,
            "expected_return": exp_return_pct,
            "expected_return_pct": exp_return_pct,
            "uncertainty_score": uncertainty_score,
            "opportunity_score": opportunity_score,
            "tier": tier,
            "tier_ar": tier_ar,
            "action_verdict": action_verdict,
            "layer_scores": layer_scores,
            "layer_weights": weights
        }

