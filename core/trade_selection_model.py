#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/trade_selection_model.py — Independent 'When NOT to Trade' Selection Gate
# Part of GEN-26 Expanded Architecture Version 2.0
# Computes Net Edge after all statutory frictions, dynamic slippage, and uncertainty penalties.
# =============================================================================

import math
import logging
from typing import Dict, Any, Optional

from core.dynamic_risk_manager import DynamicRiskManager

logger = logging.getLogger("GEN26.TradeSelectionModel")


class TradeSelectionModel:
    """
    Independent gatekeeper model dedicated to answering 'When NOT to Trade'.
    Rejects marginal signals where expected return does not overwhelmingly clear
    all trading frictions and uncertainty risk penalties.
    """

    MINIMUM_NET_EDGE_REQUIRED_PCT: float = 1.00  # Minimum 1.00% net alpha hurdle
    ROUNDTRIP_FRICTION_PCT: float = 0.35

    @classmethod
    def evaluate_trade_eligibility(
        cls,
        ticker: str,
        expected_return_pct: float,
        order_value_egp: float = 100_000.0,
        adv30_egp: float = 10_000_000.0,
        uncertainty_score: float = 0.25,
        market_regime: str = "BULL"
    ) -> Dict[str, Any]:
        """
        Calculates Net Edge = E(Return) - (0.35% + Dynamic Slippage) - Uncertainty Penalty.
        """
        # 1. Dynamic Slippage from Almgren-Chriss Model
        slippage_pct = DynamicRiskManager.calculate_dynamic_slippage(
            order_value_egp=order_value_egp,
            adv30_egp=adv30_egp
        )

        # 2. Total Frictions (Statutory Brokerage/Taxes + Market Impact)
        total_frictions_pct = cls.ROUNDTRIP_FRICTION_PCT + slippage_pct

        # 3. Uncertainty Penalty (Scales with Epistemic Uncertainty & Volatility)
        uncertainty_penalty_pct = round(float(uncertainty_score * 1.50), 3)

        # 4. Net Edge Calculation
        net_edge_pct = round(float(expected_return_pct - total_frictions_pct - uncertainty_penalty_pct), 3)

        # 5. Decision Logic
        if net_edge_pct >= cls.MINIMUM_NET_EDGE_REQUIRED_PCT:
            decision = "DECISION_TRADE_CANDIDATE"
            decision_ar = "الموافقة على الصفقة: فائض العائد الصافي يتجاوز التكاليف والمخاطر"
            is_tradeable = True
        else:
            decision = "DECISION_PASS_NO_TRADE"
            if net_edge_pct <= 0:
                decision_ar = f"استبعاد الصفقة: العائد المتوقع لا يغطي تكاليف الاحتكاك والانزلاق السعري ({total_frictions_pct:.2f}%)"
            else:
                decision_ar = f"استبعاد الصفقة: فائض العائد الصافي ({net_edge_pct:.2f}%) أقل من الحد الأدنى للأمان المؤسسي (1.00%)"
            is_tradeable = False

        return {
            "ticker": ticker,
            "expected_return_pct": round(float(expected_return_pct), 2),
            "roundtrip_friction_pct": cls.ROUNDTRIP_FRICTION_PCT,
            "dynamic_slippage_pct": round(float(slippage_pct), 3),
            "total_frictions_pct": round(float(total_frictions_pct), 3),
            "uncertainty_penalty_pct": round(float(uncertainty_penalty_pct), 3),
            "net_edge_pct": net_edge_pct,
            "hurdle_threshold_pct": cls.MINIMUM_NET_EDGE_REQUIRED_PCT,
            "decision": decision,
            "decision_ar": decision_ar,
            "is_tradeable": is_tradeable
        }


if __name__ == "__main__":
    print("Testing TradeSelectionModel...")
    # High edge trade
    res1 = TradeSelectionModel.evaluate_trade_eligibility("COMI.CA", expected_return_pct=5.5, order_value_egp=200000, adv30_egp=50000000)
    # Low edge marginal trade
    res2 = TradeSelectionModel.evaluate_trade_eligibility("MARGINAL.CA", expected_return_pct=1.2, order_value_egp=100000, adv30_egp=2000000)
    import json
    print("Trade 1:", json.dumps(res1, indent=2, ensure_ascii=False))
    print("Trade 2:", json.dumps(res2, indent=2, ensure_ascii=False))
