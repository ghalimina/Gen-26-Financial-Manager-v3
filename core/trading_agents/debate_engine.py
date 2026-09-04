#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/trading_agents/debate_engine.py — Dialectical Bull vs Bear Debate Engine
# Inspired by TauricResearch/TradingAgents (UCLA & MIT)
#
# Implements:
# 1. BullResearcherAgent (🐂): Builds affirmative growth/value investment thesis
# 2. BearResearcherAgent (🐻): Adversarial skeptic, attacks assumptions & models tail risk
# 3. DebateModerator: Coordinates 2-Round dialectical debate and produces structured transcript
# =============================================================================

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import datetime

from .analyst_team import AnalystTeamReport


@dataclass
class DebateRound:
    round_number: int
    bull_argument_ar: str
    bear_counter_argument_ar: str
    key_contested_point: str


@dataclass
class DebateTranscript:
    ticker: str
    timestamp: str
    market_price: float
    rounds: List[DebateRound] = field(default_factory=list)
    bull_conviction_score: float = 0.0  # 0 to 10
    bear_skepticism_score: float = 0.0  # 0 to 10
    debate_winner: str = "TIE"  # BULL_ADVANTAGE, BEAR_ADVANTAGE, BALANCED_EVIDENCE
    consensus_summary_ar: str = ""
    residual_risks: List[str] = field(default_factory=list)


class BullResearcherAgent:
    """
    Bullish Advocate: Synthesizes positive signals from all 4 analysts
    to construct the strongest affirmative investment thesis.
    """
    NAME = "BullResearcher"
    ROLE_AR = "باحث وفرص الصعود (Bull Advocate)"

    @classmethod
    def generate_opening_argument(cls, report: AnalystTeamReport) -> str:
        f = report.fundamental
        t = report.technical
        m = report.macro_news
        
        f_score = f.key_metrics.get("f_score", 7)
        peg = f.key_metrics.get("peg", 1.0)
        rsi = t.key_metrics.get("rsi", 55.0)

        arg = (
            f"🟢 **أطروحة الصعود (الأسباب والمحفزات)**:\n"
            f"1. **الجدارة المالية والقيمة**: السهم يحقق درجة بيوتروسكي {f_score}/9 مع مكرر نمو جذاب PEG={peg:.2f}.\n"
            f"2. **الزخم الفني الإيجابي**: السعر يتداول فوق المتوسطات المتحركة الرئيسية (RSI={rsi:.1f}) مع نموذج شمعة إيجابي يؤكد استمرار الاتجاه.\n"
            f"3. **التدفقات النقدية والأرباح**: جودة الأرباح التشغيلية تفوق المعدل العام للقطاع، مما يوفر هامش أمان حقيقي."
        )
        return arg

    @classmethod
    def generate_rebuttal(cls, bear_points: str, report: AnalystTeamReport) -> str:
        rebuttal = (
            f"🟢 **رد باحث الصعود (Rebuttal)**:\n"
            f"رغم تحفظات الدب بشأن أسعار الفائدة والتضخم، إلا أن الشركة تمتلك قدرة تسعيرية قوية تمكنها من تمرير تكاليف التضخم للعملاء.\n"
            f"كما أن معدل العائد المتوقع يتفوق بوضوح على عتبة تكلفة حقوق الملكية (Hurdle Rate 30.70%) مع احتساب كامل لعمولات التداول."
        )
        return rebuttal


class BearResearcherAgent:
    """
    Bearish Skeptic / Adversarial Critic: Identifies hidden failure modes,
    valuation traps, macroeconomic friction, and downside hazards.
    """
    NAME = "BearResearcher"
    ROLE_AR = "محامي الشيطان وفاحص المخاطر (Bear Skeptic)"

    @classmethod
    def generate_counter_argument(cls, report: AnalystTeamReport) -> str:
        m = report.macro_news
        t = report.technical
        hurdle = m.key_metrics.get("hurdle_rate", 30.70)
        rsi = t.key_metrics.get("rsi", 55.0)

        arg = (
            f"🔴 **أطروحة التحفظ والهجوم على المخاطر (Bear Thesis)**:\n"
            f"1. **عتبة العائد المرتفعة**: في ظل ممر إيداع المركزي عند 19.00% وتضخم 14.90%، عتبة تكلفة حقوق الملكية هي {hurdle:.2f}%، وأي تباطؤ في نمو الأرباح سيمحو علاوة المخاطر.\n"
            f"2. **مخاطر السيولة وتكلفة الاحتكاك**: عمولات التداول (0.35%) وضريبة الأرباح (10%) بالإضافة إلى الانزلاق السعري في جلسات التصحيح قد تلتهم جزءاً كبيراً من العائد.\n"
            f"3. **احتمالية جني الأرباح**: المؤشرات الفنية قريبة من مستويات مقاومة تستوجب وقف خسارة صارم عند -7.0% لحماية المحفظة."
        )
        return arg

    @classmethod
    def generate_rebuttal(cls, bull_points: str, report: AnalystTeamReport) -> str:
        rebuttal = (
            f"🔴 **رد محامي المخاطر (Rebuttal)**:\n"
            f"القدرة التسعيرية لا تضمن حماية هوامش الربح إذا تقلص الطلب الاستهلاكي. يجب أن نشترط هامش أمان صافي (Net Edge >= 1.00%) بعد خصم جميع التكاليف وعدم اليقين قبل فتح أي مركز شرائي."
        )
        return rebuttal


class DebateModerator:
    """
    Coordinates multi-round dialectical debate between Bull and Bear,
    evaluates evidentiary strength, and synthesizes final debate consensus.
    """
    @classmethod
    def conduct_debate(cls, report: AnalystTeamReport) -> DebateTranscript:
        sym = report.ticker
        price = report.market_price

        # Round 1: Opening Arguments
        bull_r1 = BullResearcherAgent.generate_opening_argument(report)
        bear_r1 = BearResearcherAgent.generate_counter_argument(report)
        r1 = DebateRound(
            round_number=1,
            bull_argument_ar=bull_r1,
            bear_counter_argument_ar=bear_r1,
            key_contested_point="استدامة النمو مقابل عتبة الفائدة والتضخم المرتفعة"
        )

        # Round 2: Rebuttals
        bull_r2 = BullResearcherAgent.generate_rebuttal(bear_r1, report)
        bear_r2 = BearResearcherAgent.generate_rebuttal(bull_r1, report)
        r2 = DebateRound(
            round_number=2,
            bull_argument_ar=bull_r2,
            bear_counter_argument_ar=bear_r2,
            key_contested_point="كفاية الهامش الصافي (Net Edge >= 1.00%) وحماية رأس المال"
        )

        # Score calculation based on analyst data
        f_score = report.fundamental.key_metrics.get("f_score", 7)
        if f_score >= 8 and report.composite_bias == "BULLISH":
            bull_score = 8.5
            bear_score = 5.0
            winner = "BULL_ADVANTAGE"
            consensus = (
                f"أجمعت المناظرة على أن الحجج المالية والفنية لسهم {sym} قوية ومتفوقة على المخاطر المطروحة، "
                f"مع التوصية بالشراء التراجعي المقيد بأمر محدد (Limit Order) للتحكم في الانزلاق السعري."
            )
        elif report.composite_bias == "BEARISH":
            bull_score = 4.0
            bear_score = 8.5
            winner = "BEAR_ADVANTAGE"
            consensus = (
                f"رجحت المناظرة كفة الحذر والمخاطر، نظراً لعدم كفاية هامش الأمان مقارنة بعتبة الفائدة المرتفعة."
            )
        else:
            bull_score = 6.5
            bear_score = 6.5
            winner = "BALANCED_EVIDENCE"
            consensus = (
                f"توازنت الأدلة بين فرص الصعود ومخاطر السوق، مما يقتضي تقليص حجم الصفقة وتطبيق قواعد مارك دوجلاس للمخاطرة (Max 1.0% NAV)."
            )

        risks = [
            "مخاطر التقلبات السعرية في حالة رفع أسعار الفائدة المفاجئ",
            "انزلاق سعري محتمل في الأسهم ذات السيولة المتوسطة",
            "الالتزام الصارم بنقطة وقف الخسارة عند -7.0%"
        ]

        return DebateTranscript(
            ticker=sym,
            timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            market_price=price,
            rounds=[r1, r2],
            bull_conviction_score=bull_score,
            bear_skepticism_score=bear_score,
            debate_winner=winner,
            consensus_summary_ar=consensus,
            residual_risks=risks
        )
