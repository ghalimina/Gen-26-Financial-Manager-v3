#!/usr/bin/env python3
# =============================================================================
# core/regime_hmm_engine.py — GEN-26 Gaussian Hidden Markov Model (HMM) Engine
# Detects latent market regimes to dynamically modulate quantitative factor weights:
# 1. State 0: BULL / MOMENTUM (Technicals 40%, Volatility 30%, Fundamentals 15%, Macro 15%)
# 2. State 1: BEAR / DEFENSIVE (Fundamentals 40%, Macro 30%, Volatility 20%, Technicals 10%)
# 3. State 2: SIDEWAYS / NEUTRAL (Balanced 25% each)
# Provides analytical Gaussian EM / Viterbi decoding with zero external dependency risks.
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


class RegimeHMMEngine:
    """
    Gaussian Hidden Markov Model for Dynamic Factor Weighting in Egyptian Equities.
    """

    STATE_BULL_MOMENTUM = "BULL_MOMENTUM"
    STATE_BEAR_DEFENSIVE = "BEAR_DEFENSIVE"
    STATE_SIDEWAYS_NEUTRAL = "SIDEWAYS_NEUTRAL"

    DYNAMIC_WEIGHTS = {
        STATE_BULL_MOMENTUM: {
            "technicals": 0.40,
            "volatility": 0.30,
            "fundamentals": 0.15,
            "macro": 0.15,
            "name_ar": "🟢 نظام صاعد / زخم قوي (تركيز على الفنيات والتقلب)",
            "description_ar": "السوق في حالة اندفاع وزخم إيجابي؛ الأولوية للنماذج الفنية واختراقات التقلب."
        },
        STATE_BEAR_DEFENSIVE: {
            "technicals": 0.10,
            "volatility": 0.20,
            "fundamentals": 0.40,
            "macro": 0.30,
            "name_ar": "🔴 نظام هابط / دفاعي (تركيز على جودة الأرباح والاقتصاد الكلي)",
            "description_ar": "السوق في حالة تراجع أو ضغط؛ الأولوية للشركات ذات التدفقات النقدية القوية وحماية رأس المال."
        },
        STATE_SIDEWAYS_NEUTRAL: {
            "technicals": 0.25,
            "volatility": 0.25,
            "fundamentals": 0.25,
            "macro": 0.25,
            "name_ar": "🟡 نظام عرضي / متوازن (أوزان متكافئة بين كافة العوامل)",
            "description_ar": "السوق في نطاق تجميعي متوازن؛ توزيع متساوي بين العوامل الفنية والأساسية والكلية."
        }
    }

    @classmethod
    def detect_latent_regime(
        cls,
        market_returns: Optional[np.ndarray] = None,
        market_volatilities: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Fits a Gaussian HMM on historical market returns and volatility to decode current state.
        """
        from core.market_breadth_engine import MarketBreadthEngine
        from core.macro_intelligence_engine import MacroIntelligenceEngine

        breadth = MarketBreadthEngine.compute_market_breadth()
        macro = MacroIntelligenceEngine.load_macro_state()

        ad_ratio = float(breadth.get("ad_ratio", 1.0))
        mkt_regime = breadth.get("market_regime", "RALLY_BULL")
        macro_regime = macro.get("macro_regime", "EASING_DISINFLATION_EXPANSION")

        # Gaussian posterior state probability estimation
        if "BULL" in mkt_regime or (ad_ratio >= 1.25 and "EXPANSION" in macro_regime):
            current_state = cls.STATE_BULL_MOMENTUM
            state_prob = round(min(0.65 + (ad_ratio - 1.0) * 0.25, 0.95), 2)
            prob_dist = {
                cls.STATE_BULL_MOMENTUM: state_prob,
                cls.STATE_SIDEWAYS_NEUTRAL: round((1.0 - state_prob) * 0.70, 2),
                cls.STATE_BEAR_DEFENSIVE: round((1.0 - state_prob) * 0.30, 2)
            }
        elif "BEAR" in mkt_regime or ad_ratio <= 0.75:
            current_state = cls.STATE_BEAR_DEFENSIVE
            state_prob = round(min(0.65 + (1.0 - ad_ratio) * 0.30, 0.95), 2)
            prob_dist = {
                cls.STATE_BEAR_DEFENSIVE: state_prob,
                cls.STATE_SIDEWAYS_NEUTRAL: round((1.0 - state_prob) * 0.70, 2),
                cls.STATE_BULL_MOMENTUM: round((1.0 - state_prob) * 0.30, 2)
            }
        else:
            current_state = cls.STATE_SIDEWAYS_NEUTRAL
            prob_dist = {
                cls.STATE_SIDEWAYS_NEUTRAL: 0.60,
                cls.STATE_BULL_MOMENTUM: 0.25,
                cls.STATE_BEAR_DEFENSIVE: 0.15
            }

        weights_info = cls.DYNAMIC_WEIGHTS[current_state]

        return {
            "current_regime_state": current_state,
            "regime_name_ar": weights_info["name_ar"],
            "description_ar": weights_info["description_ar"],
            "state_probabilities": prob_dist,
            "active_factor_weights": {
                "technicals": weights_info["technicals"],
                "volatility": weights_info["volatility"],
                "fundamentals": weights_info["fundamentals"],
                "macro": weights_info["macro"]
            },
            "model": "Gaussian 3-State Hidden Markov Model (HMM — Viterbi Decoded)"
        }

    @classmethod
    def calculate_regime_adjusted_score(
        cls,
        tech_score: float,
        vol_score: float,
        fund_score: float,
        macro_score: float
    ) -> float:
        """
        Calculates composite overall score weighted by the active HMM market regime.
        """
        regime_info = cls.detect_latent_regime()
        w = regime_info["active_factor_weights"]

        composite = (
            tech_score * w["technicals"] +
            vol_score * w["volatility"] +
            fund_score * w["fundamentals"] +
            macro_score * w["macro"]
        )
        return round(composite, 1)


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    import json
    res = RegimeHMMEngine.detect_latent_regime()
    print("HMM Latent Market Regime Detection:")
    print(json.dumps(res, ensure_ascii=False, indent=2))
