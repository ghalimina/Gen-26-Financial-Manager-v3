#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/yield_curve_engine.py — Nelson-Siegel Egyptian Sovereign Yield Curve Engine
# Models the Egyptian Treasury term structure of interest rates:
# 1. Calibrates Nelson-Siegel parameters (beta_0, beta_1, beta_2, lambda).
# 2. Computes dynamic yields for all standard maturities (91D, 182D, 273D, 364D, 3Y, 5Y, 10Y).
# 3. Classifies term structure regime (NORMAL, INVERTED, HUMPED, FLAT).
# 4. Provides horizon-specific discount factors D(tau) and Risk-Free Rates R_f(tau).
# =============================================================================

import math
import numpy as np
from typing import Dict, List, Any, Optional, Tuple


class YieldCurveEngine:
    """
    Nelson-Siegel Egyptian Sovereign Term Structure & Dynamic Risk-Free Rate Engine.
    """

    # Baseline Egyptian sovereign parameters reflecting CBE corridor & T-Bill auctions
    DEFAULT_BETA_0 = 24.50   # Long-term level (10Y bond anchor)
    DEFAULT_BETA_1 = 3.25    # Short-term spread (slope)
    DEFAULT_BETA_2 = -4.10   # Medium-term curvature (hump/trough)
    DEFAULT_LAMBDA = 1.35    # Scale parameter controlling maturity of maximum curvature

    STANDARD_MATURITIES = {
        "91D": 0.25,
        "182D": 0.50,
        "273D": 0.75,
        "364D": 1.00,
        "3Y": 3.00,
        "5Y": 5.00,
        "10Y": 10.00
    }

    @classmethod
    def calculate_yield(
        cls,
        tau_years: float,
        beta_0: float = DEFAULT_BETA_0,
        beta_1: float = DEFAULT_BETA_1,
        beta_2: float = DEFAULT_BETA_2,
        lambda_param: float = DEFAULT_LAMBDA
    ) -> float:
        """
        Nelson-Siegel functional form:
        y(tau) = beta_0 + beta_1 * ((1 - exp(-tau/lambda)) / (tau/lambda))
                        + beta_2 * (((1 - exp(-tau/lambda)) / (tau/lambda)) - exp(-tau/lambda))
        """
        tau = max(float(tau_years), 1e-4)
        m = tau / max(lambda_param, 1e-4)
        exp_neg = math.exp(-m)

        factor_1 = (1.0 - exp_neg) / m
        factor_2 = factor_1 - exp_neg

        y = beta_0 + (beta_1 * factor_1) + (beta_2 * factor_2)
        return round(float(y), 2)

    @classmethod
    def generate_sovereign_curve(
        cls,
        beta_0: Optional[float] = None,
        beta_1: Optional[float] = None,
        beta_2: Optional[float] = None,
        lambda_param: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Generates full Egyptian Treasury Bill & Bond yield curve:
        - Computes zero-coupon yields across 91D to 10Y
        - Computes continuous discount factors D(tau) = exp(-y * tau)
        - Classifies curve topology (INVERTED, HUMPED, NORMAL)
        """
        b0 = beta_0 if beta_0 is not None else cls.DEFAULT_BETA_0
        b1 = beta_1 if beta_1 is not None else cls.DEFAULT_BETA_1
        b2 = beta_2 if beta_2 is not None else cls.DEFAULT_BETA_2
        lam = lambda_param if lambda_param is not None else cls.DEFAULT_LAMBDA

        curve_points = {}
        discount_factors = {}

        for tenure, tau in cls.STANDARD_MATURITIES.items():
            yld = cls.calculate_yield(tau, b0, b1, b2, lam)
            curve_points[tenure] = yld
            # Continuous discount factor D(tau) = exp(- (yield / 100) * tau)
            d_factor = math.exp(-(yld / 100.0) * tau)
            discount_factors[tenure] = round(d_factor, 4)

        # Classify curve shape
        y_short = curve_points["91D"]
        y_med = curve_points["364D"]
        y_long = curve_points["10Y"]

        if y_short > y_long + 1.0:
            shape = "INVERTED"
            desc_ar = "منحنى عائد مقلوب: الفائدة قصيرة الأجل تفوق طويلة الأجل، مما يشير لضغوط تضخمية مشددة مؤقتة."
        elif y_long > y_short + 1.5:
            shape = "NORMAL_UPWARD"
            desc_ar = "منحنى عائد صاعد طبيعي: علاوة مخاطر زمنية اعتيادية."
        elif y_med > y_short and y_med > y_long:
            shape = "HUMPED"
            desc_ar = "منحنى عائد محدب: ذروة الفائدة تتركز في أذون الخزانة لأجل سنة."
        else:
            shape = "FLAT"
            desc_ar = "منحنى عائد شبه مستوٍ عبر الآفاق الزمنية."

        return {
            "parameters": {
                "beta_0_level": b0,
                "beta_1_slope": b1,
                "beta_2_curvature": b2,
                "lambda_scale": lam
            },
            "yields_pct": curve_points,
            "discount_factors": discount_factors,
            "curve_shape": shape,
            "description_ar": desc_ar,
            "anchor_10y_yield_pct": y_long,
            "benchmark_tbill_364d_pct": y_med
        }

    @classmethod
    def get_horizon_risk_free_rate(cls, holding_days: int) -> float:
        """Returns the exact matched Risk-Free Rate R_f for a specific investment horizon."""
        tau = max(holding_days / 365.25, 0.05)
        return cls.calculate_yield(tau)
