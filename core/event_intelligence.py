#!/usr/bin/env python3
# =============================================================================
# core/event_intelligence.py — GEN-26 Corporate Event & Arabic Disclosure Parser
# Processes corporate actions, disclosures, and events into structured schemas
# with materiality, sentiment direction, and expected impact horizon.
# =============================================================================

from typing import Dict, List, Any, Optional
import re
import datetime
import uuid


class EventStage:
    RUMOR = "RUMOR"
    INTENTION = "INTENTION"
    ANNOUNCEMENT = "ANNOUNCEMENT"
    SIGNED = "SIGNED"
    COMPLETED = "COMPLETED"


class CorporateEvent:
    def __init__(
        self,
        event_id: str,
        ticker: str,
        company_name: str,
        event_time: str,
        event_type: str,
        direction: str,  # POSITIVE, NEGATIVE, NEUTRAL
        materiality: str,  # HIGH, MEDIUM, LOW
        confidence: float,
        expected_horizon: str,  # SHORT_TERM, MEDIUM_TERM, LONG_TERM
        headline: str,
        stage: str = EventStage.ANNOUNCEMENT,
        impact_breakdown: Optional[Dict[str, str]] = None,
        source: str = "EGX_DISCLOSURE"
    ):
        self.event_id = event_id
        self.ticker = ticker
        self.company_name = company_name
        self.event_time = event_time
        self.event_type = event_type
        self.direction = direction
        self.materiality = materiality
        self.confidence = confidence
        self.expected_horizon = expected_horizon
        self.headline = headline
        self.stage = stage
        self.impact_breakdown = impact_breakdown or {
            "effect_on_revenue": "UNKNOWN",
            "effect_on_cost": "UNKNOWN",
            "effect_on_debt": "UNKNOWN",
            "effect_on_capex": "UNKNOWN",
            "effect_on_dividend": "UNKNOWN"
        }
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "ticker": self.ticker,
            "company_name": self.company_name,
            "event_time": self.event_time,
            "event_type": self.event_type,
            "direction": self.direction,
            "materiality": self.materiality,
            "confidence": self.confidence,
            "expected_horizon": self.expected_horizon,
            "headline": self.headline,
            "stage": self.stage,
            "impact_breakdown": self.impact_breakdown,
            "source": self.source
        }


class EventIntelligenceEngine:
    """
    Parses Arabic and English corporate disclosures into structured events with contextual stages.
    """

    # Keyword rules and mapping
    EVENT_PATTERNS = [
        (r"(استحواذ|شراء حصة|عرض شراء إجباري|M&A|Acquisition)", "ACQUISITION", "POSITIVE", "HIGH", "LONG_TERM"),
        (r"(عقد|توقيع اتفاقية|ترسية مشروع|مشروع جديد|Contract|Agreement)", "NEW_CONTRACT", "POSITIVE", "HIGH", "MEDIUM_TERM"),
        (r"(توزيع أرباح|كوبون نقدي|توزيعات نقدية|أرباح مرحلية|Dividend)", "DIVIDEND", "POSITIVE", "MEDIUM", "SHORT_TERM"),
        (r"(أسهم مجانية|زيادة رأس مال مجانية|Bonus Shares)", "BONUS_SHARES", "POSITIVE", "MEDIUM", "MEDIUM_TERM"),
        (r"(شراء أسهم خزينة|برنامج شراء خزينة|Treasury Shares|Buyback)", "BUYBACK", "POSITIVE", "HIGH", "MEDIUM_TERM"),
        (r"(زيادة رأس المال باكتتاب|قدامى المساهمين|Rights Issue)", "RIGHTS_ISSUE", "NEUTRAL", "MEDIUM", "MEDIUM_TERM"),
        (r"(خسائر|تراجع أرباح|انخفاض صافي الربح|Loss|Profit Drop)", "EARNINGS_DECLINE", "NEGATIVE", "HIGH", "MEDIUM_TERM"),
        (r"(نمو أرباح|ارتفاع صافي الربح|طفرة في الأرباح|Profit Growth)", "EARNINGS_GROWTH", "POSITIVE", "HIGH", "MEDIUM_TERM"),
        (r"(إيقاف التداول|تحقيق رقابي|مخالفات|Suspension|Halt)", "REGULATORY_HALT", "NEGATIVE", "HIGH", "SHORT_TERM"),
        (r"(تغيير الإدارة|استقالة العضو المنتدب|تعيين رئيس جديد|CEO Change)", "MANAGEMENT_CHANGE", "NEUTRAL", "MEDIUM", "MEDIUM_TERM"),
        (r"(إعادة هيكلة الديون|جدولة قروض|Debt Restructuring)", "DEBT_RESTRUCTURING", "POSITIVE", "MEDIUM", "LONG_TERM")
    ]

    STAGE_PATTERNS = [
        (r"(تدرس|تعتزم|تبحث|تتفاوض|بدء دراسة|Under Study)", EventStage.INTENTION),
        (r"(أنباء عن|شائعات|Unconfirmed)", EventStage.RUMOR),
        (r"(توقيع|إبرام|اتفاق مبدئي|Signed Agreement)", EventStage.SIGNED),
        (r"(أتمت|تنفيذ|إغلاق الصفقة|Completed|Finalized)", EventStage.COMPLETED),
        (r"(إعلان|إفصاح|Announcement)", EventStage.ANNOUNCEMENT)
    ]

    @classmethod
    def parse_disclosure_text(
        cls,
        text: str,
        ticker: str,
        company_name: str = "",
        timestamp: Optional[str] = None
    ) -> CorporateEvent:
        """
        Parses text into a standardized CorporateEvent object with contextual stage detection.
        """
        ts = timestamp or datetime.datetime.now().isoformat()
        clean_text = text.strip()

        matched_type = "GENERAL_DISCLOSURE"
        matched_dir = "NEUTRAL"
        matched_mat = "LOW"
        matched_hor = "SHORT_TERM"
        confidence = 0.50

        for pattern, ev_type, direction, materiality, horizon in cls.EVENT_PATTERNS:
            if re.search(pattern, clean_text, re.IGNORECASE):
                matched_type = ev_type
                matched_dir = direction
                matched_mat = materiality
                matched_hor = horizon
                confidence = 0.88
                break

        # Contextual Stage
        matched_stage = EventStage.ANNOUNCEMENT
        for s_pat, stage_val in cls.STAGE_PATTERNS:
            if re.search(s_pat, clean_text, re.IGNORECASE):
                matched_stage = stage_val
                break

        # Impact breakdown heuristic
        impacts = {
            "effect_on_revenue": "POSITIVE" if matched_type in ["NEW_CONTRACT", "ACQUISITION", "EARNINGS_GROWTH"] else "NEUTRAL",
            "effect_on_cost": "INCREASE" if matched_type in ["EXPANSION"] else "NEUTRAL",
            "effect_on_debt": "DECREASE" if matched_type == "DEBT_RESTRUCTURING" else "NEUTRAL",
            "effect_on_capex": "INCREASE" if matched_type in ["NEW_CONTRACT", "ACQUISITION"] else "NEUTRAL",
            "effect_on_dividend": "POSITIVE" if matched_type in ["DIVIDEND", "BONUS_SHARES"] else "NEUTRAL"
        }

        # Discount confidence if rumor or early study
        if matched_stage == EventStage.RUMOR:
            confidence *= 0.60
        elif matched_stage == EventStage.INTENTION:
            confidence *= 0.80

        return CorporateEvent(
            event_id=str(uuid.uuid4())[:12],
            ticker=ticker.upper(),
            company_name=company_name or ticker,
            event_time=ts,
            event_type=matched_type,
            direction=matched_dir,
            materiality=matched_mat,
            confidence=round(confidence, 2),
            expected_horizon=matched_hor,
            headline=clean_text[:120],
            stage=matched_stage,
            impact_breakdown=impacts
        )

    @classmethod
    def compute_event_score(cls, events: List[CorporateEvent]) -> float:
        """
        Computes composite Event Score (0 to 100) based on recent corporate events.
        """
        if not events:
            return 50.0  # Neutral baseline

        score = 50.0
        for ev in events:
            weight = 20.0 if ev.materiality == "HIGH" else (10.0 if ev.materiality == "MEDIUM" else 5.0)
            if ev.direction == "POSITIVE":
                score += weight * ev.confidence
            elif ev.direction == "NEGATIVE":
                score -= weight * ev.confidence

        return round(max(0.0, min(100.0, score)), 1)
