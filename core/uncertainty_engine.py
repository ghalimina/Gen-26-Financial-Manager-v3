#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/uncertainty_engine.py — Probabilistic Distribution & Forecast Uncertainty Engine
# Part of GEN-26 Expanded Architecture Version 2.0
# Outputs full return probability distributions and controls uncertainty risk haircuts.
# =============================================================================

import math
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("GEN26.UncertaintyEngine")


def norm_cdf(x: float) -> float:
    """Standard normal cumulative distribution function approximation."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


class UncertaintyEngine:
    """
    Evaluates probabilistic forecast distributions and quantifies epistemic and aleatoric uncertainty
    to adjust dynamic bet sizing or enforce hard 'NO_TRADE' safety gates under elevated fog-of-war.
    """

    UNCERTAINTY_THRESHOLDS = {
        "LOW": 0.35,
        "MEDIUM": 0.65,
        "HIGH": 1.00
    }

    @classmethod
    def evaluate_forecast_distribution(
        cls,
        ticker: str,
        expected_return_pct: float,
        base_confidence: float = 75.0,
        volatility_atr_pct: float = 2.50,
        current_price: float = 100.0,
        regime: str = "BULL"
    ) -> Dict[str, Any]:
        """
        Generates full probability distribution for the asset return horizon.
        """
        # Regime volatility scaling multiplier
        regime_multipliers = {
            "STRONG_BULL": 0.90,
            "GOLDILOCKS_EXPANSION": 0.90,
            "SIDEWAYS_CHOP": 1.10,
            "RATE_HIKING_CYCLE": 1.20,
            "HIGH_INFLATION": 1.35,
            "BEAR_CORRECTION": 1.40,
            "FLASH_CRASH": 1.80
        }
        reg_mult = regime_multipliers.get(regime.upper(), 1.10)

        # Standard deviation of forecast distribution (in percentage points)
        forecast_std = max(0.8, volatility_atr_pct * reg_mult * (1.0 - (base_confidence / 200.0)))

        mu = float(expected_return_pct)
        sigma = float(forecast_std)

        # Probabilities of return thresholds
        # P(R >= +1%) = 1 - Phi((1 - mu) / sigma)
        z_up_1 = (1.0 - mu) / sigma
        prob_up_1pct = round((1.0 - norm_cdf(z_up_1)) * 100.0, 1)

        z_up_3 = (3.0 - mu) / sigma
        prob_up_3pct = round((1.0 - norm_cdf(z_up_3)) * 100.0, 1)

        z_down_1 = (-1.0 - mu) / sigma
        prob_down_1pct = round(norm_cdf(z_down_1) * 100.0, 1)

        z_down_3 = (-3.0 - mu) / sigma
        prob_down_3pct = round(norm_cdf(z_down_3) * 100.0, 1)

        prob_range = max(0.0, round(100.0 - prob_up_1pct - prob_down_1pct, 1))

        # 90% Confidence Interval
        ci_90_low_pct = round(mu - 1.645 * sigma, 2)
        ci_90_high_pct = round(mu + 1.645 * sigma, 2)

        ci_90_low_price = round(current_price * (1.0 + ci_90_low_pct / 100.0), 2)
        ci_90_high_price = round(current_price * (1.0 + ci_90_high_pct / 100.0), 2)

        # Uncertainty Score Calculation [0.0 - 1.0]
        # Combines forecast dispersion, confidence deficit, and downside tail probability
        uncertainty_score = (sigma / 8.0) * 0.50 + ((100.0 - base_confidence) / 100.0) * 0.30 + (prob_down_1pct / 100.0) * 0.20
        uncertainty_score = max(0.05, min(0.98, uncertainty_score))

        if uncertainty_score < cls.UNCERTAINTY_THRESHOLDS["LOW"]:
            uncertainty_tier = "LOW"
            uncertainty_tier_ar = "عدم يقين منخفض (ثقة تنبؤية عالية)"
            sizing_multiplier = 1.00
            trade_action = "PERMIT_FULL_SIZE"
        elif uncertainty_score < cls.UNCERTAINTY_THRESHOLDS["MEDIUM"]:
            uncertainty_tier = "MEDIUM"
            uncertainty_tier_ar = "عدم يقين معتدل (تخفيض احترازي للحجم)"
            sizing_multiplier = 0.65
            trade_action = "HAIRCUT_SIZE_35PCT"
        else:
            uncertainty_tier = "HIGH"
            uncertainty_tier_ar = "عدم يقين مرتفع (ضبابية حرجة)"
            sizing_multiplier = 0.00
            trade_action = "NO_TRADE_SAFETY_LOCK"

        return {
            "ticker": ticker,
            "expected_return_pct": round(mu, 2),
            "forecast_std_pct": round(sigma, 2),
            "prob_up_1pct": prob_up_1pct,
            "prob_up_3pct": prob_up_3pct,
            "prob_range": prob_range,
            "prob_down_1pct": prob_down_1pct,
            "prob_down_3pct": prob_down_3pct,
            "confidence_interval_90_pct": [ci_90_low_pct, ci_90_high_pct],
            "price_range_90": [ci_90_low_price, ci_90_high_price],
            "uncertainty_score": round(float(uncertainty_score), 3),
            "uncertainty_tier": uncertainty_tier,
            "uncertainty_tier_ar": uncertainty_tier_ar,
            "sizing_multiplier": sizing_multiplier,
            "trade_action": trade_action
        }


if __name__ == "__main__":
    print("Testing UncertaintyEngine...")
    res = UncertaintyEngine.evaluate_forecast_distribution(
        ticker="COMI.CA",
        expected_return_pct=4.5,
        base_confidence=82.0,
        volatility_atr_pct=2.1,
        current_price=139.28,
        regime="BULL"
    )
    import json
    print(json.dumps(res, indent=2, ensure_ascii=False))
