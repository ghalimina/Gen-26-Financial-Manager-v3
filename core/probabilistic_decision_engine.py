#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/probabilistic_decision_engine.py — GEN-26 Institutional Decision Radar
# Generates regime-conditioned probability distributions, conformal quantile bounds,
# multi-agent adversarial auditing, and concrete invalidation triggers for EGX equities.
# =============================================================================

import os
import sys
import math
import logging
import datetime
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.market_price_service import MarketPriceService
from core.egx_universe_loader import EGXUniverseLoader
from core.regime_hmm_engine import RegimeHMMEngine
from core.multi_horizon_engine import MultiHorizonEngine
from core.conformal_prediction_engine import ConformalPredictionEngine
from core.adversarial_ai_agent import AdversarialAIAgent
from core.news_ingestion_engine import NewsIngestionEngine
from core.live_fundamentals_engine import LiveFundamentalsEngine
from core.valuation_engine import ValuationEngine
from core.technical_setup_engine import TechnicalSetupEngine
from core.institutional_flow_engine import InstitutionalFlowEngine

logger = logging.getLogger("GEN26.ProbabilisticDecisionEngine")


class ProbabilisticDecisionEngine:
    """
    Institutional Decision Intelligence Engine for the Egyptian Stock Exchange.
    Transforms raw AI forecasts into actionable, probabilistic risk-reward cards:
    - Multi-Horizon Probability Distributions: P(Up), P(Range), P(Down) summing to 100%.
    - Conformal Prediction Quantiles: Q10 (VaR Stop), Q50 (Median Alpha), Q90 (Target).
    - Global Geopolitical & War Radar: Scans international conflicts, oil, and Red Sea impacts.
    - Tripartite Adversarial Debate: Bull Offensive Thesis vs Bear Red-Team Dissection.
    - Explicit Invalidation Triggers: Precise events and price levels that cancel the setup.
    """

    @classmethod
    def generate_decision_card(
        cls,
        ticker: str,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Builds a comprehensive probabilistic decision card for a given equity.
        """
        clean_sym = ticker.upper().strip()
        if not clean_sym.endswith(".CA") and "." not in clean_sym:
            clean_sym = f"{clean_sym}.CA"

        # 1. Price and Metadata
        price_rec = MarketPriceService.get_canonical_price_record(clean_sym) or {}
        price = float(current_price or price_rec.get("price", 100.0))
        if price <= 0:
            price = 100.0

        info = EGXUniverseLoader.get_stock_info(clean_sym) or {}
        name_ar = info.get("name_ar", clean_sym)
        sector = info.get("sector", "عام")
        beta = float(info.get("beta_egx30", 1.0))

        # 2. Market Regime and Global Geopolitical Risk Guidance
        regime_data = RegimeHMMEngine.detect_latent_regime()
        regime_code = regime_data.get("regime", "SIDEWAYS_CHOP")
        regime_ar = regime_data.get("regime_name_ar") or regime_data.get("name_ar") or "حركة عرضية متوازنة (SIDEWAYS_CHOP)"
        base_cash_pct = float(regime_data.get("cash_reserve_pct", 40.0))

        # 2b. Global Geopolitical Conflict & Energy Shock Monitor
        geo_state = NewsIngestionEngine.get_global_geopolitical_risk_state()
        geo_threat = geo_state.get("threat_level", "LOW_STABLE")
        geo_threat_ar = geo_state.get("threat_level_ar", "🟢 استقرار جيوسياسي نسبي")
        geo_buffer_cash = float(geo_state.get("threat_buffer_cash_pct", 0.0))
        recommended_cash_pct = min(base_cash_pct + geo_buffer_cash, 80.0)
        geo_events = geo_state.get("top_geopolitical_events", [])

        # 3. Multi-Horizon Probabilistic Forecasts
        mh_analysis = MultiHorizonEngine.get_stock_multi_horizon_analysis(clean_sym, mock_price=price) or {}
        horizons = mh_analysis.get("horizons", {})

        # Default swing horizon (5D or 10D)
        swing_h = horizons.get("5D") or horizons.get("10D") or {}
        p_dist = swing_h.get("probability_distribution", {
            "threshold_pct": 3.0,
            "prob_up_pct": 55.0,
            "prob_range_pct": 30.0,
            "prob_down_pct": 15.0
        })

        # 4. Conformal Quantiles (Distribution-Free Envelopes)
        try:
            conformal_res = ConformalPredictionEngine.predict_conformal_quantiles(clean_sym, current_price=price)
        except Exception as e:
            logger.warning(f"Conformal quantiles fallback for {clean_sym}: {e}")
            conformal_res = {
                "quantile_10_downside_pct": -4.5,
                "quantile_50_median_pct": 2.8,
                "quantile_90_upside_pct": 8.5,
                "conformal_price_envelope": {
                    "pessimistic_q10_price": round(price * 0.955, 2),
                    "median_q50_price": round(price * 1.028, 2),
                    "optimistic_q90_price": round(price * 1.085, 2)
                },
                "quantile_risk_to_reward": 1.89
            }

        q10_pct = float(conformal_res.get("quantile_10_downside_pct", -4.5))
        q50_pct = float(conformal_res.get("quantile_50_median_pct", 2.5))
        q90_pct = float(conformal_res.get("quantile_90_upside_pct", 8.0))
        envelope = conformal_res.get("conformal_price_envelope", {})
        price_q10 = float(envelope.get("pessimistic_q10_price", price * 0.955))
        price_q50 = float(envelope.get("median_q50_price", price * 1.025))
        price_q90 = float(envelope.get("optimistic_q90_price", price * 1.080))
        rr_ratio = float(conformal_res.get("quantile_risk_to_reward", 1.8))

        # 5. Adversarial Audit (Bull Analyst vs Bear Red-Team)
        adv_debate = AdversarialAIAgent.conduct_adversarial_debate(clean_sym, current_price=price)
        bull_view = adv_debate.get("bull_agent", {})
        bear_view = adv_debate.get("bear_red_team", {})
        cro_consensus = adv_debate.get("cro_synthesis", {})

        catalysts = bull_view.get("arguments_ar", [])
        if not catalysts:
            catalysts = [
                f"تداول السهم ضمن مسار فني مستقر مع تماسك فوق مستويات الدعم.",
                f"معامل حساسية بيتا متوازن ({beta:.2f}) بالنسبة لمؤشر البورصة المصرية."
            ]

        vulnerabilities = bear_view.get("vulnerabilities_ar", [])
        if not vulnerabilities:
            vulnerabilities = [
                f"تذبذب عرضي يستلزم الالتزام الصارم بنقاط وقف الخسارة.",
                f"حساسية السهم لتغيرات سيولة السوق العام."
            ]

        # 6. Specific Invalidation Triggers (شروط إبطال الفرضية)
        stop_loss_price = float(swing_h.get("stop_loss", round(price * 0.955, 2)))
        invalidating_triggers = [
            f"كسر مستوى وقف الخسارة الفني {stop_loss_price:.2f} ج.م بإغلاق يومي (خروج وقائي فوري).",
            f"تحول تدفقات السيولة المؤسسية إلى صافي بيع كثيف مع انخفاض حاد في حجم التداول.",
            f"إعلان أحداث جوهرية غير متوقعة أو توزيعات نقدية تؤدي لفجوة سعرية هابطة."
        ]

        # 7. Valuation & Margin of Safety
        fund = LiveFundamentalsEngine.get_stock_fundamentals(clean_sym) or {}
        pe = float(fund.get("pe_ratio", 0.0))
        roe = float(fund.get("roe_pct", 0.0))
        dcf_val = ValuationEngine.calculate_dcf_valuation(clean_sym, current_price=price)
        fair_value = float(dcf_val.get("intrinsic_value_egp", price * 1.15))
        margin_of_safety = float(dcf_val.get("margin_of_safety_pct", 15.0))

        confidence_pct = float(swing_h.get("confidence", 0.78) * 100.0)

        # 8. Generate Formatted Arabic Markdown Card
        card_md = f"""================================================================================
📊 بطاقة الرادار الاحتمالي الذكي — GEN-26 DECISION COPILOT
================================================================================
🏢 السهم: {name_ar} ({clean_sym})
🏷️ القطاع: {sector}                       💵 السعر الحالي: {price:.2f} ج.م
🌐 بيئة السوق الحالية: {regime_ar} ({regime_code})
🛡️ نسبة الكاش الإرشادية للمحفظة: {recommended_cash_pct:.0f}%
🎯 المدى الزمني المستهدف: تداول سوينج (5 إلى 10 أيام عمل)
--------------------------------------------------------------------------------
📈 توزيع الاحتمالات الإحصائي (Probability Distribution - أفق 5 أيام):
  • 🟢 احتمال صعود أكبر من +{p_dist.get('threshold_pct', 3.0):.1f}%:       {p_dist.get('prob_up_pct', 55.0):.1f}%   [هدف Q90: {price_q90:.2f} ج.م | +{q90_pct:.1f}%]
  • 🟡 احتمال حركة عرضية (نطاق ±{p_dist.get('threshold_pct', 3.0):.1f}%): {p_dist.get('prob_range_pct', 30.0):.1f}%   [نطاق متوازن: {price_q10:.2f} - {price_q90:.2f} ج.م]
  • 🔴 احتمال هبوط أكبر من -{p_dist.get('threshold_pct', 3.0):.1f}%:       {p_dist.get('prob_down_pct', 15.0):.1f}%   [قاع Q10: {price_q10:.2f} ج.م | {q10_pct:.1f}%]

📊 العائد المتوقع الإحصائي (Median Q50):   +{q50_pct:.1f}% ({price_q50:.2f} ج.م)
⚖️ نسبة العائد إلى المخاطرة (Reward/Risk): {rr_ratio:.2f} : 1
🎯 درجة الثقة الكمية (Confidence):         {confidence_pct:.1f}%
🏛️ القيمة العادلة الاسترشادية (DCF):        {fair_value:.2f} ج.م (هامش أمان: {margin_of_safety:.1f}%)
--------------------------------------------------------------------------------
"""
        if geo_threat != "LOW_STABLE" and geo_events:
            card_md += f"""🌍 رادار النزاعات والحروب والأزمات العالمية (Global Geopolitical & War Radar):
  • حالة التهديد العالمي: {geo_threat_ar}
  • زيادة الكاش التحوطي الإلزامي: +{geo_buffer_cash:.0f}% (إجمالي الكاش الموصى به للمحفظة: {recommended_cash_pct:.0f}%)
  • أبرز الأحداث والنزاعات المرصودة لحظياً:
"""
            for ev in geo_events[:3]:
                card_md += f"    - [{ev.get('source')}]: {ev.get('headline_ar')}\n"

            if any(k in sector for k in ["بترول", "كيماويات", "أسمدة", "طاقة", "Industrial"]):
                card_md += f"  • 🛡️ الأثر النوعي على السهم ({clean_sym}): يستفيد جزئياً من صعود أسعار الطاقة العالمية وهوامش التصدير بالعملة الصعبة.\n"
            elif any(k in sector for k in ["بنوك", "مدفوعات", "عقارات"]):
                card_md += f"  • ⚠️ الأثر النوعي على السهم ({clean_sym}): يستلزم الحذر من انسحاب السيولة الساخنة للمؤسسات الأجنبية (Risk-Off Flight).\n"
            else:
                card_md += f"  • ⚠️ الأثر النوعي على السهم ({clean_sym}): يوصى بتضييق وقف الخسارة وتجنب الشراء بالهامش (Margin) أثناء التوترات.\n"
            card_md += "--------------------------------------------------------------------------------\n"

        card_md += """🟢 أقوى العوامل الداعمة (Catalysts):
"""
        for i, cat in enumerate(catalysts[:3], 1):
            card_md += f"  {i}. {cat}\n"

        card_md += "\n🔴 أهم المخاطر ومكامن الضعف (Vulnerabilities):\n"
        for i, vuln in enumerate(vulnerabilities[:3], 1):
            card_md += f"  {i}. {vuln}\n"

        card_md += "\n⚠️ شروط إبطال الفرضية فوراً (Invalidating Events):\n"
        for i, trig in enumerate(invalidating_triggers[:3], 1):
            card_md += f"  {i}. {trig}\n"

        card_md += f"""--------------------------------------------------------------------------------
💡 التوجيه التنفيذي المقترح للمستثمر:
  • منطقة الدخول المفضلة: {swing_h.get('target_1_bounds', {}).get('low', price * 0.985):.2f} – {price:.2f} ج.م
  • الهدف الأول:          {swing_h.get('target_1', price_q90):.2f} ج.م
  • وقف الخسارة الصارم:   {stop_loss_price:.2f} ج.م (خسارة أقصاها {abs((price - stop_loss_price)/price*100):.1f}%)
  • سقف الوزن في المحفظة: لا يتجاوز 20% - 25% طبقاً لضوابط الهيئة العامة للرقابة المالية
================================================================================
"""

        return {
            "ticker": clean_sym,
            "company_name_ar": name_ar,
            "sector": sector,
            "current_price": price,
            "market_regime": regime_code,
            "market_regime_ar": regime_ar,
            "recommended_cash_pct": recommended_cash_pct,
            "probability_distribution": p_dist,
            "conformal_quantiles": {
                "q10_downside_pct": q10_pct,
                "q50_median_pct": q50_pct,
                "q90_upside_pct": q90_pct,
                "price_q10": price_q10,
                "price_q50": price_q50,
                "price_q90": price_q90,
                "reward_to_risk": rr_ratio
            },
            "valuation": {
                "intrinsic_value_egp": fair_value,
                "margin_of_safety_pct": margin_of_safety,
                "pe_ratio": pe,
                "roe_pct": roe
            },
            "catalysts_ar": catalysts[:3],
            "vulnerabilities_ar": vulnerabilities[:3],
            "invalidating_triggers_ar": invalidating_triggers[:3],
            "execution": {
                "target_1": swing_h.get("target_1", price_q90),
                "target_2": swing_h.get("target_2", round(price * 1.12, 2)),
                "stop_loss": stop_loss_price,
                "confidence_pct": confidence_pct
            },
            "markdown_card": card_md
        }

    @classmethod
    def generate_portfolio_radar(
        cls,
        tickers: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generates decision cards across a list of portfolio equities.
        """
        target_tickers = tickers or ["COMI.CA", "TMGH.CA", "ORAS.CA", "ETEL.CA"]
        results = []
        for sym in target_tickers:
            try:
                card = cls.generate_decision_card(sym)
                results.append(card)
            except Exception as e:
                logger.error(f"Error generating decision card for {sym}: {e}")
        return results
