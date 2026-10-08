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
    ROUNDTRIP_FRICTION_PCT: float = 0.94  # 0.94% roundtrip friction (SSoT)

    @classmethod
    def evaluate_egx30_trend_gate(
        cls,
        egx30_price: Optional[float] = None,
        egx30_ma50: Optional[float] = None,
        regime: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        EGX30 Trend Gatekeeper (Mission Brief Requirement):
        If EGX30 index trades below 50-day moving average (SMA50) OR HMM regime is Bearish/Correction:
        Market Mode = CASH_PRESERVATION -> Zero Buy Signals (100% Cash).
        """
        if egx30_price is None or egx30_ma50 is None or regime is None:
            try:
                from core.regime_hmm_engine import RegimeHMMEngine
                r_state = RegimeHMMEngine.detect_latent_regime()
                if egx30_price is None:
                    egx30_price = float(r_state.get("current_price", 52494.0))
                if egx30_ma50 is None:
                    egx30_ma50 = float(r_state.get("ma_50", 52000.0))
                if regime is None:
                    regime = str(r_state.get("regime", "SIDEWAYS_CHOP"))
            except Exception:
                egx30_price = egx30_price or 52494.0
                egx30_ma50 = egx30_ma50 or 52000.0
                regime = regime or "SIDEWAYS_CHOP"

        is_below_sma50 = bool(egx30_price < egx30_ma50)
        is_bear_or_crash = regime in ["BEAR_CORRECTION", "FLASH_CRASH", "BEAR_DEFENSIVE"]

        if is_below_sma50 or is_bear_or_crash:
            market_mode = "CASH_PRESERVATION"
            can_trade = False
            cash_target_pct = 100.0
            reason_ar = "🚨 وضع حماية رأس المال (CASH_PRESERVATION): مؤشر EGX30 أسفل SMA50 أو في نظام هبوط/تصحيح — يُحظر فتح أي صفقات جديدة (كاش 100%)."
        else:
            market_mode = "SELECTIVE_TRADING"
            can_trade = True
            cash_target_pct = 35.0  # Minimum cash floor invariant
            reason_ar = "🟢 وضع التداول الانتقائي مسموح: المؤشر أعلى SMA50 وخارج نطاق التصحيح الهابط."

        return {
            "market_mode": market_mode,
            "can_trade": can_trade,
            "egx30_price": round(float(egx30_price), 2),
            "egx30_ma50": round(float(egx30_ma50), 2),
            "is_below_sma50": is_below_sma50,
            "regime": regime,
            "cash_target_pct": cash_target_pct,
            "reason_ar": reason_ar
        }

    @classmethod
    def evaluate_trade_eligibility(
        cls,
        ticker: str,
        expected_return_pct: float,
        order_value_egp: float = 100_000.0,
        adv30_egp: float = 10_000_000.0,
        uncertainty_score: float = 0.25,
        market_regime: str = "BULL",
        market_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates Net Edge = E(Return) - (0.35% + Dynamic Slippage) - Uncertainty Penalty.
        Enforces EGX30 Trend Gate (CASH_PRESERVATION -> 0 Trades).
        """
        if market_mode == "CASH_PRESERVATION":
            return {
                "ticker": ticker,
                "expected_return_pct": round(float(expected_return_pct), 2),
                "roundtrip_friction_pct": cls.ROUNDTRIP_FRICTION_PCT,
                "dynamic_slippage_pct": 0.0,
                "total_frictions_pct": 0.0,
                "uncertainty_penalty_pct": 0.0,
                "net_edge_pct": 0.0,
                "hurdle_threshold_pct": cls.MINIMUM_NET_EDGE_REQUIRED_PCT,
                "decision": "DECISION_PASS_CASH_PRESERVATION",
                "decision_ar": "استبعاد الصفقة: بوابة اتجاه EGX30 مفعلة لحماية رأس المال (CASH_PRESERVATION) — صفر إشارات شراء",
                "is_tradeable": False
            }
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

    @classmethod
    def evaluate_golden_consensus(
        cls,
        ticker: str,
        current_price: float,
        theories_result: Dict[str, Any],
        dqs_score: float,
        gdr_spread_pct: Optional[float] = None,
        is_market_bull: bool = True,
        expected_net_return_pct: float = 1.0,
        cooling_off_active: bool = False
    ) -> Dict[str, Any]:
        """
        Golden Consensus Filter (Zenith Optimization Mandate):
        Issues STRONG_BUY iff ALL conditions are met simultaneously:
        1. At least 4 of 6 theories agree with score >= 80.0 in TheoryEngine.
        2. Data Quality Score DQS >= 85.0.
        3. GDR counterpart (if exists) does not trade at a negative discount threatening down gap (Spread >= -1.0%).
        4. EGX30 index trades above 50-day moving average (is_market_bull is True).
        5. Expected Net Return after commissions, spread, and taxes E[R_net] > 0.50%.
        6. Ticker is NOT under active 48-hour Cooling-off lock (Anti-revenge trading).
        """
        # 1. Theories Agreement (Wyckoff, ICT, Minervini VCP, CAN SLIM, Dow, Elliott)
        theories_dict = theories_result.get("theories", {})
        theories_scores = {}
        for th_key, th_val in theories_dict.items():
            if isinstance(th_val, dict):
                theories_scores[th_key] = float(th_val.get("score", 0.0))

        theories_qualifying = [th for th, sc in theories_scores.items() if sc >= 80.0]
        theories_count_passed = len(theories_qualifying)
        theories_gate_passed = theories_count_passed >= 4

        # 2. Data Quality Gate (DQS >= 85)
        dqs_gate_passed = float(dqs_score) >= 85.0

        # 3. GDR Spread Gate (Spread >= -1.0% if GDR exists)
        if gdr_spread_pct is not None:
            gdr_gate_passed = float(gdr_spread_pct) >= -1.0
        else:
            gdr_gate_passed = True

        # 4. EGX30 Market Bull Gate
        market_gate_passed = bool(is_market_bull)

        # 5. Expected Net Return Gate (E[R_net] > 0.50%)
        net_return_gate_passed = float(expected_net_return_pct) > 0.50

        # 6. Anti-Revenge Cooling-Off Gate
        cooling_off_gate_passed = not bool(cooling_off_active)

        all_passed = (
            theories_gate_passed and
            dqs_gate_passed and
            gdr_gate_passed and
            market_gate_passed and
            net_return_gate_passed and
            cooling_off_gate_passed
        )

        rejection_reasons = []
        if not theories_gate_passed:
            rejection_reasons.append(f"موافقة النظريات غير كافية ({theories_count_passed}/6 نظريات >= 80، المطلوب 4 على الأقل)")
        if not dqs_gate_passed:
            rejection_reasons.append(f"جودة البيانات منخفضة (DQS={dqs_score:.1f} < 85.0)")
        if not gdr_gate_passed:
            rejection_reasons.append(f"شهادة لندن بخصم سلبي يهدد بفجوة هابطة ({gdr_spread_pct:.2f}% < -1.0%)")
        if not market_gate_passed:
            rejection_reasons.append("مؤشر السوق EGX30 أسفل SMA50 (وضع حماية رأس المال)")
        if not net_return_gate_passed:
            rejection_reasons.append(f"العائد الصافي المتوقع غير كافٍ ({expected_net_return_pct:.2f}% <= 0.50%)")
        if not cooling_off_gate_passed:
            rejection_reasons.append("السهم خاضع لحظر تداول إلزامي لمدة 48 ساعة لمكافحة التداول الانتقامي")

        verdict = "STRONG_BUY" if all_passed else ("BUY" if (theories_count_passed >= 3 and net_return_gate_passed and market_gate_passed and cooling_off_gate_passed) else "HOLD_OR_REJECT")

        verdict_badge_ar = "🟢 إجماع ذهبي معتمد (STRONG_BUY)" if all_passed else ("🟡 شراء انتقائي مشروط (BUY)" if verdict == "BUY" else "⚪ استبعاد / غير مؤهل (REJECT)")

        return {
            "ticker": ticker,
            "is_golden_consensus": all_passed,
            "consensus_verdict": verdict,
            "verdict_badge_ar": verdict_badge_ar,
            "gates": {
                "theories_passed_count": theories_count_passed,
                "theories_gate_passed": theories_gate_passed,
                "theories_qualifying": theories_qualifying,
                "dqs_score": round(dqs_score, 1),
                "dqs_gate_passed": dqs_gate_passed,
                "gdr_spread_pct": round(gdr_spread_pct, 2) if gdr_spread_pct is not None else None,
                "gdr_gate_passed": gdr_gate_passed,
                "market_bull_gate_passed": market_gate_passed,
                "expected_net_return_pct": round(expected_net_return_pct, 2),
                "net_return_gate_passed": net_return_gate_passed,
                "cooling_off_gate_passed": cooling_off_gate_passed
            },
            "rejection_reasons_ar": rejection_reasons
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

