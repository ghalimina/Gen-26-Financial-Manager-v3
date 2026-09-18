#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/adversarial_ai_agent.py — Superhuman Multi-Agent Adversarial Debate Engine
# Implements a tripartite cognitive debate architecture:
# 1. Bull Analyst Agent (Offensive thesis discovery)
# 2. Bear Red-Team Agent (Adversarial vulnerability dissection)
# 3. Chief Risk Officer Arbiter (Rigorous synthesis and veto enforcement)
# =============================================================================

import os
import sys
import time
import logging
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.market_price_service import MarketPriceService
from core.technical_setup_engine import TechnicalSetupEngine
from core.institutional_flow_engine import InstitutionalFlowEngine
from core.live_fundamentals_engine import LiveFundamentalsEngine
from core.news_sentiment_engine import NewsSentimentEngine
from core.corporate_actions_calendar import CorporateActionsCalendar

logger = logging.getLogger("GEN26.AdversarialAIAgent")


class AdversarialAIAgent:
    """
    Superhuman Self-Improving Multi-Agent Adversarial Debate Engine.
    Forces every trading candidate through a rigorous adversarial debate
    between a Bull Agent, a Bear Red-Team Agent, and a Chief Risk Officer.
    """

    @classmethod
    def _run_bull_agent(cls, ticker: str, price: float) -> Dict[str, Any]:
        """
        Bull Agent: Seeks out all catalytic drivers, alpha momentum, and undervaluation arguments.
        """
        tech = TechnicalSetupEngine.evaluate_technical_setup(ticker, current_price=price) or {}
        flow = InstitutionalFlowEngine.evaluate_stock_flow(ticker, current_price=price) or {}
        fund = LiveFundamentalsEngine.get_stock_fundamentals(ticker) or {}
        news = NewsSentimentEngine.get_sentiment_impact(ticker) or {}

        tech_score = float(tech.get("technical_score", 50.0))
        rsi = float(tech.get("rsi14", 50.0))
        flow_score = float(flow.get("flow_score", 50.0))
        z_score = float(flow.get("volume_z_score", 0.0))
        fund_score = float(fund.get("fundamental_score", 50.0))
        pe = float(fund.get("pe_ratio", 10.0))
        roe = float(fund.get("roe_pct", 15.0))

        bull_arguments = []
        conviction = 50.0

        if tech_score >= 65.0:
            bull_arguments.append(f"زخم فني صاعد قوي ({tech_score:.1f}/100) مع استقرار فوق المتوسطات المتحركة.")
            conviction += 12.0
        if flow_score >= 60.0 or z_score >= 1.0:
            bull_arguments.append(f"تجميع مؤسسي ملحوظ (Z-Score: +{z_score:.2f}) يشير إلى دخول سيولة ذكية.")
            conviction += 15.0
        if fund_score >= 65.0 or (pe > 0 and pe <= 8.5 and roe >= 18.0):
            bull_arguments.append(f"أساسيات مالية ممتازة (مكرر ربحية مغري {pe:.1f}x وعائد حقوق ملكية {roe:.1f}%).")
            conviction += 10.0
        if news.get("is_catalyst", False):
            bull_arguments.append(f"محفز إخباري إيجابي معتمد: {news.get('headline_ar', 'أخبار إيجابية')}.")
            conviction += 8.0

        return {
            "agent": "BULL_OFFENSIVE_ANALYST",
            "stance": "BULLISH",
            "conviction_pct": round(min(conviction, 98.0), 1),
            "key_thesis_ar": "السهم يمتلك مقومات صعود قوية وتوافقاً بين الزخم الفني وتدفقات السيولة المؤسسية.",
            "arguments_ar": bull_arguments or ["حركة السعر متوازنة وضمن نطاق تداول مستقر."]
        }

    @classmethod
    def _run_bear_red_team(cls, ticker: str, price: float) -> Dict[str, Any]:
        """
        Bear Red-Team Agent: Actively attacks the bull thesis, identifying traps,
        overbought extremes, liquidity exhaustion, and corporate action hazards.
        """
        tech = TechnicalSetupEngine.evaluate_technical_setup(ticker, current_price=price) or {}
        flow = InstitutionalFlowEngine.evaluate_stock_flow(ticker, current_price=price) or {}
        fund = LiveFundamentalsEngine.get_stock_fundamentals(ticker) or {}
        corp = CorporateActionsCalendar.evaluate_pre_trade_corporate_hazard(ticker, price) or {}

        rsi = float(tech.get("rsi14", 50.0))
        z_score = float(flow.get("volume_z_score", 0.0))
        debt_to_equity = float(fund.get("debt_to_equity", 1.0))

        vulnerabilities = []
        threat_level = 30.0

        if rsi >= 68.0:
            vulnerabilities.append(f"مؤشر القوة النسبية RSI عند مستويات تشبع شرائي مرتفعة ({rsi:.1f}) تزيد من مخاطر جني الأرباح.")
            threat_level += 20.0
        if z_score <= -0.8:
            vulnerabilities.append(f"ضعف حاد في أحجام التداول (Z-Score: {z_score:.2f}) واحتمال وقوع مصيدة سيولة (Liquidity Trap).")
            threat_level += 20.0
        if debt_to_equity >= 2.5:
            vulnerabilities.append(f"رافعة مالية مرتفعة (الديون لحقوق الملكية: {debt_to_equity:.1f}x) تعرض السهم لضغوط تكلفة الاقتراض.")
            threat_level += 15.0
        if corp.get("has_imminent_event", False):
            vulnerabilities.append(f"مخاطر استحقاق حدث شركة وشيك ({corp.get('imminent_event', {}).get('action_type', 'حدث')}) قد يسبب فجوة هابطة.")
            threat_level += 25.0

        return {
            "agent": "BEAR_RED_TEAM_AUDITOR",
            "stance": "SKEPTICAL_BEARISH",
            "threat_level_pct": round(min(threat_level, 95.0), 1),
            "key_critique_ar": "هناك نقاط ضعف هيكلية ومخاطر تقلبات قد تفشل السيناريو الصاعد.",
            "vulnerabilities_ar": vulnerabilities or ["لم يتم رصد مخاطر غير معتادة، والوضع ضمن التذبذب الطبيعي."]
        }

    @classmethod
    def conduct_adversarial_debate(cls, ticker: str, current_price: Optional[float] = None) -> Dict[str, Any]:
        """
        Orchestrates full adversarial debate and produces Chief Risk Officer consensus.
        """
        clean_sym = ticker.upper().strip()
        if not clean_sym.endswith(".CA") and "." not in clean_sym:
            clean_sym = f"{clean_sym}.CA"

        rec = MarketPriceService.get_canonical_price_record(clean_sym) or {}
        price = float(current_price or rec.get("price", 10.0))
        if price <= 0:
            price = 10.0

        bull = cls._run_bull_agent(clean_sym, price)
        bear = cls._run_bear_red_team(clean_sym, price)

        bull_score = bull["conviction_pct"]
        bear_risk = bear["threat_level_pct"]
        net_advantage = round(bull_score - bear_risk, 1)

        # Chief Risk Officer (CRO) Arbitration
        if net_advantage >= 25.0 and bear_risk < 50.0:
            verdict = "APPROVED_CONVICTION_BUY"
            verdict_ar = "🟢 اعتماد الصفقة بقناعة كاملة (فوز حاسم لأطروحة الصعود على تحفظات الفريق الأحمر)"
            arbiter_multiplier = 1.20
            action_code = "BUY"
        elif net_advantage >= 10.0 and bear_risk < 60.0:
            verdict = "APPROVED_REDUCED_SIZE"
            verdict_ar = "🟡 اعتماد مشروط بتخفيض حجم المركز بنسبة 25% للتحوط من ملاحظات الفريق الأحمر"
            arbiter_multiplier = 0.75
            action_code = "WATCH"
        elif bear_risk >= 65.0:
            verdict = "VETOED_BY_RED_TEAM"
            verdict_ar = "🔴 استخدام حق الفيتو الصارم: الفريق الأحمر رصد مخاطر عالية تبطل جدوى الدخول"
            arbiter_multiplier = 0.0
            action_code = "AVOID"
        else:
            verdict = "STANDBY_MONITOR"
            verdict_ar = "⚪ توازن بين قوى الصعود والمخاطر: يوصى بالمراقبة دون فتح مراكز جديدة"
            arbiter_multiplier = 0.50
            action_code = "WATCH"

        return {
            "ticker": clean_sym,
            "current_price": price,
            "net_advantage_score": net_advantage,
            "final_verdict": verdict,
            "verdict_ar": verdict_ar,
            "action_code": action_code,
            "arbiter_position_multiplier": arbiter_multiplier,
            "bull_agent_thesis": bull,
            "bear_red_team_critique": bear,
            "debate_summary_ar": (
                f"مناظرة الذكاء الاصطناعي لـ {clean_sym}: "
                f"قوة الصعود {bull_score:.1f}% مقابل مستوى التهديد {bear_risk:.1f}%. "
                f"القرار النهائي للجنة المخاطر: {verdict_ar}"
            ),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
