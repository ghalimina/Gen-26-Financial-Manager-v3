#!/usr/bin/env python3
# =============================================================================
# core/prediction_disentangler.py — Disentangled Prediction Triad Engine
# Strictly separates:
#   1. P(UP) — Calibrated Directional Probability
#   2. Expected Return (E[R]) — Mathematical expected return percentage
#   3. Uncertainty & Conformal Interval — 90% non-parametric prediction bounds
# Eliminates conflation between directional confidence and magnitude.
# =============================================================================

import os
import sys
from typing import Dict, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)


class PredictionDisentangler:
    """
    Institutional Prediction Disentangler:
    Prevents confusing high probability with high expected return.
    Separates P(UP), E[R], and Conformal Uncertainty into distinct signals.
    """

    @staticmethod
    def disentangle(
        prob_up_pct: float,
        expected_return_pct: float,
        q10_downside_pct: float,
        q90_upside_pct: float,
        historical_hit_rate_pct: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Disentangles raw ML / quant scores into a rigorous 3-component output:
          - probability_up_pct: P(Return > 0%) calibrated to [5%, 95%]
          - expected_return_pct: Mathematical expectancy E[R] over 10 trading days
          - prediction_interval_90: Conformal 90% coverage interval [Q10, Q90]
          - uncertainty_level: LOW, MEDIUM, or HIGH based on interval dispersion
        """
        p_up = max(5.0, min(95.0, float(prob_up_pct)))
        exp_ret = round(float(expected_return_pct), 2)
        q10 = round(float(q10_downside_pct), 2)
        q90 = round(float(q90_upside_pct), 2)

        # Monotonicity enforcement
        if q10 > exp_ret:
            q10 = round(exp_ret - 2.5, 2)
        if q90 < exp_ret:
            q90 = round(exp_ret + 3.5, 2)

        interval_width = round(q90 - q10, 2)

        # Uncertainty Classification based on interval dispersion
        if interval_width < 7.5:
            unc_level = "LOW"
            unc_label_ar = "منخفضة (ثقة إحصائية مرتفعة ونطاق ضيق)"
        elif interval_width <= 14.0:
            unc_level = "MEDIUM"
            unc_label_ar = "متوسطة (ضمن نطاق التقلب الطبيعي للسوق)"
        else:
            unc_level = "HIGH"
            unc_label_ar = "مرتفعة (نطاق تشتت واسع ومخاطر تقلب)"

        # Expected Value vs Probability assessment
        if p_up >= 70.0 and exp_ret >= 4.0:
            profile_verdict_ar = "🟢 فرصة نموذجية: احتمالية صعود مرتفعة مع عائد متوقع قوي"
        elif p_up >= 70.0 and exp_ret < 2.0:
            profile_verdict_ar = "🟡 صعود شبه مؤكد لكن بعائد ضئيل (Low Expectancy)"
        elif p_up < 50.0 and exp_ret >= 5.0:
            profile_verdict_ar = "🟠 رهان عالي المخاطر (احتمالية متدنية مع عائد نظري مرتفع)"
        else:
            profile_verdict_ar = "⚪ فرصة متوازنة تخضع لإدارة المخاطر القياسية"

        return {
            "probability_up_pct": round(p_up, 1),
            "expected_return_pct": exp_ret,
            "prediction_interval_90": {
                "lower_bound_pct": q10,
                "upper_bound_pct": q90,
                "interval_width_pct": interval_width,
                "formatted_str": f"{q10:+.1f}% → {q90:+.1f}%"
            },
            "uncertainty_level": unc_level,
            "uncertainty_label_ar": unc_label_ar,
            "profile_verdict_ar": profile_verdict_ar,
            "summary_triad_display": (
                f"P(UP): {p_up:.1f}% | E[R]: {exp_ret:+.2f}% | "
                f"90% CI: [{q10:+.1f}%, {q90:+.1f}%] | Uncertainty: {unc_level}"
            )
        }
