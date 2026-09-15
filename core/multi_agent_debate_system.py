#!/usr/bin/env python3
# =============================================================================
# core/multi_agent_debate_system.py — Multi-Agent Rational Debate & Investment Memo Engine
# Coordinates an adversarial debate between:
# 1. BullThesisAgent: Formulates evidence-based long thesis.
# 2. BearThesisAgent (Devil's Advocate): Uncovers valuation, debt, technical & macro vulnerabilities.
# 3. ChiefRiskArbiter: Synthesizes the debate into a consensus verdict and Arabic investment memo.
# =============================================================================

import os
import sys
import logging
from typing import Dict, Any, Optional, List

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.market_price_service import MarketPriceService
from core.valuation_engine import ValuationEngine
from core.conformal_prediction_engine import ConformalPredictionEngine
from core.ai_prediction_model import AIPredictionModel
from core.technical_setup_engine import TechnicalSetupEngine
from core.institutional_flow_engine import InstitutionalFlowEngine
from core.corporate_actions_calendar import CorporateActionsCalendar
from core.news_sentiment_engine import NewsSentimentEngine

logger = logging.getLogger("GEN26.MultiAgentDebate")


class BullThesisAgent:
    """Formulates structured positive investment catalysts."""
    @classmethod
    def analyze_bull_thesis(
        cls,
        ticker: str,
        current_price: float,
        val_data: Dict[str, Any],
        conf_data: Dict[str, Any],
        ai_data: Dict[str, Any],
        tech_data: Dict[str, Any],
        flow_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        points = []
        score = 50.0

        # 1. Valuation Catalyst
        mos = float(val_data.get("margin_of_safety_pct", 0.0))
        fv = float(val_data.get("intrinsic_fair_value", current_price))
        if mos >= 15.0:
            score += 18.0
            points.append(f"تداول السهم بخصم جذاب ({mos:.1f}%) دون قيمته العادلة المرجحة ({fv:.2f} ج.م) طبقاً لـ {val_data.get('primary_model_name_ar', 'نموذج التقييم')}.")
        elif mos > 0:
            score += 8.0
            points.append(f"السعر الحالي أقل بصورة طفيفة من القيمة العادلة المرجحة ({fv:.2f} ج.م).")

        # 2. Conformal Upside Catalyst
        q90 = float(conf_data.get("quantile_90_upside_pct", 0.0))
        rr = float(conf_data.get("quantile_risk_to_reward", 1.0))
        if rr >= 2.0:
            score += 15.0
            points.append(f"توزيع العائد المئيني غير متماثل لصالح الصعود: نسبة الربح إلى المخاطرة المحتملة (RR) تبلغ {rr:.2f}x مع سقف صعود تفاؤلي لـ 10 جلسات عند +{q90:.1f}%.")

        # 3. AI Ensemble Alpha Catalyst
        alpha = float(ai_data.get("expected_alpha_10d_pct", 0.0))
        if alpha >= 1.0:
            score += 12.0
            points.append(f"مجمع خوارزميات Gradient Boosting يتوقع توليد ألفا موجبة قدرها +{alpha:.2f}% مقارنة بمؤشر البورصة المصرية.")

        # 4. Institutional Smart Flow Catalyst
        flow_regime = flow_data.get("flow_regime", "BALANCED_NEUTRAL")
        if "ACCUMULATION" in flow_regime or "INFLOW" in flow_regime:
            score += 10.0
            points.append(f"رصد تدفقات تجميعية مؤسسية قوية ({flow_data.get('description_ar', 'شراء مؤسسي ملحوظ')}).")

        # 5. Technical Alignment
        tech_score = float(tech_data.get("technical_score", 50.0))
        setup_name = tech_data.get("setup_label_ar", tech_data.get("setup_classification", "نطاق عرضي"))
        if tech_score >= 60.0:
            score += 8.0
            points.append(f"هيكل فني إيجابي بنموذج ({setup_name}) مع مؤشر قوة فنية يبلغ {tech_score:.1f}/100.")

        conviction = min(max(score, 20.0), 98.0)
        return {
            "agent": "BullThesisAgent",
            "agent_role_ar": "وكيل أطروحة الشراء والنمو (Bull Catalyst)",
            "conviction_score": round(conviction, 1),
            "thesis_summary_ar": f"توافر محفزات كمية داعمة للشراء بقيادة {points[0] if points else 'مؤشرات التقييم والزخم'}",
            "key_catalysts": points
        }


class BearThesisAgent:
    """Devil's Advocate: Uncovers risk points, debt burdens, resistance and valuation drag."""
    @classmethod
    def analyze_bear_thesis(
        cls,
        ticker: str,
        current_price: float,
        val_data: Dict[str, Any],
        conf_data: Dict[str, Any],
        tech_data: Dict[str, Any],
        corp_data: Dict[str, Any],
        news_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        concerns = []
        penalty_score = 30.0

        # 1. Valuation Overhang / Negative Margin of Safety
        mos = float(val_data.get("margin_of_safety_pct", 0.0))
        fv = float(val_data.get("intrinsic_fair_value", current_price))
        if mos == 0.0 and current_price > fv:
            premium_pct = ((current_price - fv) / fv) * 100.0
            penalty_score += 22.0
            concerns.append(f"مخاطرة تقييم: السهم يتداول بعلاوة سعرية تفوق قيمته العادلة بنسبة +{premium_pct:.1f}%، مما يحد من هامش الأمان الاستثماري.")

        # 2. Downside VaR Concern
        q10 = float(conf_data.get("quantile_10_downside_pct", -3.0))
        if q10 <= -6.0:
            penalty_score += 15.0
            concerns.append(f"اتساع نطاق الخسارة المحتملة في السيناريو المتشائم المئيني (Q10) إلى {q10:.1f}%، مما يتطلب وقاية مالية صارمة.")

        # 3. Technical Overbought / Overhead Resistance
        rsi = float(tech_data.get("rsi14", 50.0))
        if rsi >= 68.0:
            penalty_score += 12.0
            concerns.append(f"مؤشر القوة النسبية (RSI={rsi:.1f}) يقترب من مناطق التشبع الشرائي، مما يرفع احتمالية حدوث جني أرباح وتصحيح خاطف.")

        # 4. Corporate Hazards
        if corp_data.get("has_imminent_event", False):
            penalty_score += 15.0
            concerns.append(f"وجود استحقاق وشيك لحدث جوهري في جدول أعمال الشركة ({corp_data.get('warning_ar', 'توزيعات أو جمعية عمومية')}).")

        # 5. Sentiment Risks
        if news_data.get("is_risk_event", False) or news_data.get("alpha_shock_pct", 0.0) < -1.0:
            penalty_score += 14.0
            concerns.append(f"ضغط إخباري سلبي قصير الأجل: {news_data.get('headline_ar', 'تأثير صدمة أخبار سلبية')}.")

        conviction = min(max(penalty_score, 15.0), 95.0)
        return {
            "agent": "BearThesisAgent",
            "agent_role_ar": "وكيل محامي الشيطان والمخاطر (Devil's Advocate)",
            "risk_severity_score": round(conviction, 1),
            "antithesis_summary_ar": f"تحذير من مخاطر كامنة: {concerns[0] if concerns else 'تقلبات السوق العامة وتكاليف التمويل'}",
            "key_vulnerabilities": concerns if concerns else ["تقلبات قطاعية عامة وتأثير سعر الفائدة المرتفع."]
        }


class ChiefRiskArbiter:
    """Synthesizes debate points, resolves conflicts, and produces the final investment memorandum."""
    @classmethod
    def arbitrate(
        cls,
        ticker: str,
        current_price: float,
        bull_report: Dict[str, Any],
        bear_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        bull_score = bull_report["conviction_score"]
        bear_score = bear_report["risk_severity_score"]
        net_spread = bull_score - bear_score

        # Structured Transcript of the Debate
        dialogue = [
            {
                "speaker": "BullThesisAgent",
                "speaker_ar": "وكيل الشراء",
                "statement_ar": bull_report["thesis_summary_ar"],
                "points": bull_report["key_catalysts"]
            },
            {
                "speaker": "BearThesisAgent",
                "speaker_ar": "محامي الشيطان",
                "statement_ar": bear_report["antithesis_summary_ar"],
                "points": bear_report["key_vulnerabilities"]
            }
        ]

        # Resolution Logic
        if bear_score >= 80.0 or net_spread <= -15.0:
            verdict = "REJECT_RISK_DOMINANT"
            verdict_ar = "🔴 رفض فتح مراكز شراء (Risk Dominant): مخاطر محامي الشيطان تفوق الجدوى وتُعرض رأس المال لانتكاسة غير مبررة."
            pos_multiplier = 0.00
            decision_code = "AVOID"
        elif net_spread >= 25.0 and bear_score < 50.0:
            verdict = "CONFIRM_STRONG_BUY"
            verdict_ar = "🟢 تأكيد الشراء بثقة كاملة (Full Size): تفوق كاسح لأطروحة الشراء على كافة المخاطر المرصودة."
            pos_multiplier = 1.25
            decision_code = "STRONG_BUY"
        elif net_spread >= 10.0:
            verdict = "CONDITIONAL_HALF_SIZE"
            verdict_ar = "🟡 شراء مشروط بنصف الكمية المعتادة (Half Size): المحفزات إيجابية ولكن هناك مخاطر قصيرة الأجل تستوجب الحذر."
            pos_multiplier = 0.75
            decision_code = "ACCUMULATE"
        else:
            verdict = "HOLD_AND_WAIT"
            verdict_ar = "🟡 مراقبة واحتفاظ (Hold & Wait): توازن بين المحفزات والمخاطر ولا توجد ميزة تفوق كافية لفتح مركز جديد."
            pos_multiplier = 0.50
            decision_code = "HOLD"

        # Executive Investment Memorandum
        memo = (
            f"مذكرة لجنة الاستثمار المؤسسية لسهم {ticker} عند سعر {current_price:.2f} ج.م:\n"
            f"• خلاصة أطروحة الشراء (قوة الاقتناع: {bull_score}%): {bull_report['thesis_summary_ar']}\n"
            f"• خلاصة أطروحة المخاطر (درجة التحذير: {bear_score}%): {bear_report['antithesis_summary_ar']}\n"
            f"• حكم قاضي المخاطر النهائي: {verdict_ar}\n"
            f"• معامل ضبط حجم المركز الموصى به: {pos_multiplier:.2f}x."
        )

        dialogue.append({
            "speaker": "ChiefRiskArbiter",
            "speaker_ar": "قاضي المخاطر ورئيس اللجنة",
            "statement_ar": verdict_ar,
            "net_conviction_spread": round(net_spread, 1),
            "arbiter_position_multiplier": pos_multiplier
        })

        return {
            "ticker": ticker,
            "current_price": current_price,
            "consensus_verdict": verdict,
            "consensus_decision": decision_code,
            "consensus_verdict_ar": verdict_ar,
            "net_conviction_spread": round(net_spread, 1),
            "arbiter_position_multiplier": pos_multiplier,
            "bull_conviction_score": bull_score,
            "bear_risk_score": bear_score,
            "debate_dialogue": dialogue,
            "executive_investment_memo_ar": memo
        }


class MultiAgentDebateSystem:
    """Master Orchestrator for Adversarial Multi-Agent Debate."""

    @classmethod
    def conduct_debate(
        cls,
        ticker: str,
        current_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executes complete multi-agent debate session across valuation, conformal quantiles,
        AI prediction, and technical/hazard modules.
        """
        sym = ticker.upper().strip()
        cp = current_price or MarketPriceService.get_latest_price(sym)
        if not cp or cp <= 0:
            cp = 100.0

        # Collect intelligence inputs
        val_data = ValuationEngine.evaluate_comprehensive_valuation(sym, current_price=cp)
        conf_data = ConformalPredictionEngine.predict_conformal_quantiles(sym, current_price=cp)
        ai_data = AIPredictionModel.predict_stock(sym, current_price=cp)
        tech_data = TechnicalSetupEngine.evaluate_technical_setup(sym, current_price=cp)
        flow_data = InstitutionalFlowEngine.evaluate_stock_flow(sym, current_price=cp)
        corp_data = CorporateActionsCalendar.evaluate_pre_trade_corporate_hazard(sym, cp)
        news_data = NewsSentimentEngine.get_sentiment_impact(sym)

        # Execute Bull and Bear arguments
        bull = BullThesisAgent.analyze_bull_thesis(sym, cp, val_data, conf_data, ai_data, tech_data, flow_data)
        bear = BearThesisAgent.analyze_bear_thesis(sym, cp, val_data, conf_data, tech_data, corp_data, news_data)

        # Arbitrate and synthesize
        decision = ChiefRiskArbiter.arbitrate(sym, cp, bull, bear)

        return {
            "ticker": sym,
            "current_price": cp,
            "bull_report": bull,
            "bear_report": bear,
            "arbitration": decision,
            "verdict": decision["consensus_verdict"],
            "verdict_ar": decision["consensus_verdict_ar"],
            "arbiter_multiplier": decision["arbiter_position_multiplier"],
            "investment_memo_ar": decision["executive_investment_memo_ar"],
            "debate_dialogue": decision["debate_dialogue"]
        }
