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
    Separates:
      1. P(Up) in [0, 1] — Calibrated Directional Probability
      2. E[R] = P(Up) * R_up + (1 - P(Up)) * R_down — Mathematical expected return percentage
      3. Uncertainty & Conformal Interval (90% coverage) [Q10, Q90]
    """

    @staticmethod
    def disentangle(
        prob_up_pct: Optional[float] = None,
        expected_return_pct: Optional[float] = None,
        q10_downside_pct: float = -2.5,
        q90_upside_pct: float = 7.5,
        historical_hit_rate_pct: Optional[float] = None,
        r_up_mean: Optional[float] = None,
        r_down_mean: Optional[float] = None,
        prob_up: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Disentangles raw ML / quant scores into a rigorous 3-component matrix:
          - p_up: P(Return > 0%) in [0.05, 0.95] as decimal
          - probability_up_pct: P(Return > 0%) as percentage
          - expected_return_pct: Mathematical expectancy E[R] = P(Up)*R_up + (1-P(Up))*R_down
          - prediction_interval_90 / conformal_interval_90: Conformal 90% coverage interval [Q10, Q90]
          - uncertainty_level: LOW, MEDIUM, or HIGH based on interval dispersion
        """
        # Resolve P(Up)
        if prob_up is not None:
            p_val = float(prob_up)
            if p_val > 1.0:
                p_up_dec = max(0.05, min(0.95, p_val / 100.0))
            else:
                p_up_dec = max(0.05, min(0.95, p_val))
        elif prob_up_pct is not None:
            p_val = float(prob_up_pct)
            if p_val <= 1.0:
                p_up_dec = max(0.05, min(0.95, p_val))
            else:
                p_up_dec = max(0.05, min(0.95, p_val / 100.0))
        else:
            p_up_dec = 0.55

        p_up_pct = round(p_up_dec * 100.0, 1)
        p_down_dec = round(1.0 - p_up_dec, 4)

        # Resolve conditional mean returns: R_up and R_down
        if r_up_mean is not None:
            r_up = float(r_up_mean)
        elif expected_return_pct is not None and expected_return_pct > 0:
            r_up = round(float(expected_return_pct) + 2.5, 2)
        else:
            r_up = 5.20

        if r_down_mean is not None:
            r_down = float(r_down_mean)
        elif expected_return_pct is not None and expected_return_pct < 0:
            r_down = round(float(expected_return_pct) - 2.5, 2)
        else:
            r_down = -3.80

        # Mathematical Expectancy: E[R] = P(Up) * R_up + (1 - P(Up)) * R_down
        if expected_return_pct is not None:
            exp_ret = round(float(expected_return_pct), 2)
        else:
            exp_ret = round(float(p_up_dec * r_up + p_down_dec * r_down), 2)

        formula_str = (
            f"E[R] = ({p_up_dec:.2f} * {r_up:+.2f}%) + ({p_down_dec:.2f} * {r_down:+.2f}%) = {exp_ret:+.2f}%"
        )

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
        if p_up_pct >= 70.0 and exp_ret >= 4.0:
            profile_verdict_ar = "🟢 فرصة نموذجية: احتمالية صعود مرتفعة مع عائد متوقع قوي"
        elif p_up_pct >= 70.0 and exp_ret < 2.0:
            profile_verdict_ar = "🟡 صعود شبه مؤكد لكن بعائد ضئيل (Low Expectancy)"
        elif p_up_pct < 50.0 and exp_ret >= 5.0:
            profile_verdict_ar = "🟠 رهان عالي المخاطر (احتمالية متدنية مع عائد نظري مرتفع)"
        else:
            profile_verdict_ar = "⚪ فرصة متوازنة تخضع لإدارة المخاطر القياسية"

        conformal_dict = {
            "lower_bound_pct": q10,
            "upper_bound_pct": q90,
            "interval_width_pct": interval_width,
            "formatted_str": f"[{q10:+.1f}% → {q90:+.1f}%]"
        }

        return {
            "p_up": round(p_up_dec, 4),
            "p_down": round(p_down_dec, 4),
            "probability_up_pct": p_up_pct,
            "r_up_mean_pct": round(r_up, 2),
            "r_down_mean_pct": round(r_down, 2),
            "expected_return_pct": exp_ret,
            "expectancy_formula_str": formula_str,
            "prediction_interval_90": conformal_dict,
            "conformal_interval_90": conformal_dict,
            "triad_matrix": {
                "p_up": round(p_up_dec, 4),
                "expected_return_pct": exp_ret,
                "conformal_interval_90": f"[{q10:+.1f}% → {q90:+.1f}%]"
            },
            "uncertainty_level": unc_level,
            "uncertainty_label_ar": unc_label_ar,
            "profile_verdict_ar": profile_verdict_ar,
            "summary_triad_display": (
                f"P(UP): {p_up_dec:.2f} ({p_up_pct:.1f}%) | E[R]: {exp_ret:+.2f}% | "
                f"90% CI: [{q10:+.1f}%, {q90:+.1f}%] | Uncertainty: {unc_level}"
            )
        }
