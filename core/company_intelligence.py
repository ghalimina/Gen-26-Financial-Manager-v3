#!/usr/bin/env python3
# =============================================================================
# core/company_intelligence.py — GEN-26 Company Intelligence & Accounting Risk
# Evaluates fundamental company quality, cash conversion, earnings quality,
# and generates quantitative Accounting Risk indicators (LOW, MEDIUM, HIGH).
# =============================================================================

from typing import Dict, Any, Optional
import numpy as np


class CompanyIntelligenceEngine:
    """
    Computes fundamental metrics, earnings quality scores, and accounting risk indicators.
    """

    # Sector benchmark ratios for EGX core companies
    EGX_SECTOR_PROFILES = {
        "Banking": {"avg_roe": 22.0, "avg_net_margin": 30.0, "avg_de_ratio": 6.5},
        "Real Estate": {"avg_roe": 14.0, "avg_net_margin": 18.0, "avg_de_ratio": 1.2},
        "Industrial": {"avg_roe": 18.0, "avg_net_margin": 15.0, "avg_de_ratio": 0.8},
        "Telecom & Tech": {"avg_roe": 20.0, "avg_net_margin": 22.0, "avg_de_ratio": 0.5},
        "Fertilizers & Chemicals": {"avg_roe": 25.0, "avg_net_margin": 28.0, "avg_de_ratio": 0.4},
        "General": {"avg_roe": 15.0, "avg_net_margin": 12.0, "avg_de_ratio": 1.0}
    }

    @staticmethod
    def compute_company_quality_score(
        roe_pct: float,
        net_margin_pct: float,
        operating_cash_flow_egp: float,
        net_income_egp: float,
        debt_to_equity: float,
        revenue_growth_pct: float = 10.0,
        sector: str = "General"
    ) -> Dict[str, Any]:
        """
        Computes composite Company Quality Score (0 to 100), Earnings Quality, and Accounting Risk.
        """
        profile = CompanyIntelligenceEngine.EGX_SECTOR_PROFILES.get(
            sector, CompanyIntelligenceEngine.EGX_SECTOR_PROFILES["General"]
        )

        score_components = {}

        # 1. Profitability & Efficiency (Weight: 30%)
        roe_score = min(100.0, max(0.0, (roe_pct / max(profile["avg_roe"], 1.0)) * 75.0))
        margin_score = min(100.0, max(0.0, (net_margin_pct / max(profile["avg_net_margin"], 1.0)) * 75.0))
        profitability_score = (roe_score * 0.6) + (margin_score * 0.4)
        score_components["profitability"] = round(profitability_score, 1)

        # 2. Earnings Quality & Cash Conversion (Weight: 35%)
        # High quality: Operating Cash Flow >= Net Income
        if net_income_egp > 0:
            cash_conversion_ratio = operating_cash_flow_egp / net_income_egp
            if cash_conversion_ratio >= 1.0:
                earnings_quality_score = min(100.0, 80.0 + (cash_conversion_ratio - 1.0) * 20.0)
            elif cash_conversion_ratio >= 0.6:
                earnings_quality_score = 60.0 + (cash_conversion_ratio - 0.6) * 50.0
            else:
                earnings_quality_score = max(10.0, cash_conversion_ratio * 100.0)
        else:
            earnings_quality_score = 30.0 if operating_cash_flow_egp > 0 else 10.0

        score_components["earnings_quality"] = round(earnings_quality_score, 1)

        # 3. Balance Sheet & Solvency (Weight: 20%)
        # Lower debt relative to sector norm is safer
        target_de = profile["avg_de_ratio"]
        if debt_to_equity <= target_de:
            solvency_score = 100.0 - (debt_to_equity / max(target_de, 0.1)) * 25.0
        else:
            solvency_score = max(10.0, 75.0 - ((debt_to_equity - target_de) / max(target_de, 0.1)) * 40.0)
        score_components["solvency"] = round(solvency_score, 1)

        # 4. Growth Momentum (Weight: 15%)
        growth_score = min(100.0, max(0.0, (revenue_growth_pct / 15.0) * 75.0))
        score_components["growth"] = round(growth_score, 1)

        # Composite Quality Score
        composite_quality = (
            profitability_score * 0.30 +
            earnings_quality_score * 0.35 +
            solvency_score * 0.20 +
            growth_score * 0.15
        )
        composite_quality = round(max(0.0, min(100.0, composite_quality)), 1)

        # Accounting Risk Indicator
        if earnings_quality_score < 40.0 or debt_to_equity > (target_de * 2.5):
            accounting_risk = "HIGH"
        elif earnings_quality_score < 65.0 or debt_to_equity > (target_de * 1.5):
            accounting_risk = "MEDIUM"
        else:
            accounting_risk = "LOW"

        return {
            "quality_score": composite_quality,
            "earnings_quality_score": round(earnings_quality_score, 1),
            "accounting_risk": accounting_risk,
            "components": score_components,
            "roe_pct": roe_pct,
            "net_margin_pct": net_margin_pct,
            "cash_conversion_ratio": round(operating_cash_flow_egp / max(net_income_egp, 1.0), 2) if net_income_egp > 0 else 0.0,
            "debt_to_equity": round(debt_to_equity, 2)
        }
