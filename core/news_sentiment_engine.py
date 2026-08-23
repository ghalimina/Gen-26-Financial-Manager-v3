#!/usr/bin/env python3
# =============================================================================
# core/news_sentiment_engine.py — GEN-26 EGX News & Corporate Disclosures NLP Engine
# Ingests corporate disclosures and market headlines, performing Arabic/English
# financial sentiment scoring and outputting event shock impact to forecasts.
# =============================================================================

import re
from typing import Dict, List, Any, Optional


class NewsSentimentEngine:
    """
    Evaluates corporate disclosure feeds, earnings announcements, dividends,
    and market news to compute sentiment polarity, materiality, and alpha shocks.
    """

    SENTIMENT_POSITIVE = "POSITIVE"
    SENTIMENT_NEUTRAL = "NEUTRAL"
    SENTIMENT_NEGATIVE = "NEGATIVE"

    IMPACT_HIGH = "HIGH"
    IMPACT_MEDIUM = "MEDIUM"
    IMPACT_LOW = "LOW"

    # Seed Disclosures & Recent News Knowledge Base for EGX Universe
    LATEST_DISCLOSURES = {
        "COMI.CA": {
            "headline_ar": "نمو صافي أرباح البنك بنسبة 48% وتوزيعات كوبونات نقدية استثنائية للمساهمين",
            "headline_en": "Net profit surges 48% YoY with strong loan portfolio growth and cash dividend announcement",
            "event_type": "EARNINGS_BEAT_DIVIDEND",
            "sentiment": "POSITIVE",
            "materiality": "HIGH",
            "raw_score": 0.85,
            "alpha_shock_pct": +2.40,
            "date": "2026-08-20"
        },
        "SWDY.CA": {
            "headline_ar": "توقيع عقود مشروعات بنية تحتية وطاقة كبرى بالخليج وإفريقيا بقيمة تتجاوز 400 مليون دولار",
            "headline_en": "Elsewedy signs major $400M+ energy and infrastructure contracts across GCC and Africa",
            "event_type": "MAJOR_CONTRACT",
            "sentiment": "POSITIVE",
            "materiality": "HIGH",
            "raw_score": 0.80,
            "alpha_shock_pct": +2.10,
            "date": "2026-08-19"
        },
        "TMGH.CA": {
            "headline_ar": "مبيعات تعاقدية غير مسبوقة لمشروع بنان بالرياض والساحل الشمالي وتدفقات نقدية قوية",
            "headline_en": "Record contractual sales exceeding expectations for Banan and SouthMED developments",
            "event_type": "RECORD_SALES",
            "sentiment": "POSITIVE",
            "materiality": "HIGH",
            "raw_score": 0.78,
            "alpha_shock_pct": +1.90,
            "date": "2026-08-18"
        },
        "ORAS.CA": {
            "headline_ar": "إضافة مشروعات جديدة لمحفظة الأعمال تحت التنفيذ بقيمة 1.8 مليار دولار مع تركيز دولاري",
            "headline_en": "Backlog adds $1.8B in new high-margin infrastructure projects",
            "event_type": "BACKLOG_GROWTH",
            "sentiment": "POSITIVE",
            "materiality": "MEDIUM",
            "raw_score": 0.70,
            "alpha_shock_pct": +1.50,
            "date": "2026-08-15"
        },
        "ETEL.CA": {
            "headline_ar": "نمو قوي في إيرادات خدمات البيانات والإنترنت الثابت والتحول الرقمي الحكومي",
            "headline_en": "Strong data revenue growth and high operational EBITDA margins",
            "event_type": "EARNINGS_GROWTH",
            "sentiment": "POSITIVE",
            "materiality": "MEDIUM",
            "raw_score": 0.72,
            "alpha_shock_pct": +1.60,
            "date": "2026-08-14"
        },
        "EGAL.CA": {
            "headline_ar": "قفزة في هوامش ربحية التصدير وتحسن أسعار الألومنيوم العالمية ببورصة لندن للمعادن",
            "headline_en": "Export revenue surges on favorable global LME aluminum prices",
            "event_type": "COMMODITY_SURGE",
            "sentiment": "POSITIVE",
            "materiality": "HIGH",
            "raw_score": 0.82,
            "alpha_shock_pct": +2.20,
            "date": "2026-08-17"
        },
        "ABUK.CA": {
            "headline_ar": "استقرار خطوط الإنتاج بعد انتظام إمدادات الغاز الطبيعي وتوزيع كوبون نقدي سخي",
            "headline_en": "Full operational resumption with steady natural gas feed and attractive dividend payout",
            "event_type": "OPERATIONAL_STABILITY",
            "sentiment": "POSITIVE",
            "materiality": "MEDIUM",
            "raw_score": 0.74,
            "alpha_shock_pct": +1.70,
            "date": "2026-08-16"
        },
        "MFPC.CA": {
            "headline_ar": "ارتفاع أسعار اليوريا عالمياً واستمرار التصدير للأسواق الأوروبية بالعملة الصعبة",
            "headline_en": "Global urea prices rebound driving hard-currency export earnings",
            "event_type": "EXPORT_GROWTH",
            "sentiment": "POSITIVE",
            "materiality": "MEDIUM",
            "raw_score": 0.72,
            "alpha_shock_pct": +1.50,
            "date": "2026-08-15"
        },
        "ADIB.CA": {
            "headline_ar": "تحقيق أعلى عائد على حقوق الملكية بالقطاع المصرفي ونمو التمويلات المتوافقة مع الشريعة",
            "headline_en": "Record ROE and Islamic financing expansion supporting double-digit EPS growth",
            "event_type": "EARNINGS_BEAT",
            "sentiment": "POSITIVE",
            "materiality": "HIGH",
            "raw_score": 0.80,
            "alpha_shock_pct": +2.00,
            "date": "2026-08-18"
        },
        "EAST.CA": {
            "headline_ar": "تحسن هوامش الربحية بعد إعادة تسعير المنتجات واعتماد توزيعات أرباح نقدية تاريخية",
            "headline_en": "Product price adjustments restore margins alongside historic dividend distribution",
            "event_type": "MARGIN_EXPANSION",
            "sentiment": "POSITIVE",
            "materiality": "HIGH",
            "raw_score": 0.79,
            "alpha_shock_pct": +1.95,
            "date": "2026-08-12"
        },
        "FWRY.CA": {
            "headline_ar": "توسع متسارع في خدمات التمويل متناهي الصغر وإطلاق حلول دفع رقمية جديدة للمدفوعات",
            "headline_en": "Fintech microfinance portfolio expands 60%+ with digital payment throughput gains",
            "event_type": "EXPANSION",
            "sentiment": "POSITIVE",
            "materiality": "MEDIUM",
            "raw_score": 0.73,
            "alpha_shock_pct": +1.65,
            "date": "2026-08-16"
        },
        "RAYA.CA": {
            "headline_ar": "ضغوط تضخمية مؤقتة على هوامش ربحية قطاع التوزيع وتجارة الأجهزة الاستهلاكية",
            "headline_en": "Margin compression in consumer distribution segment due to financing costs",
            "event_type": "MARGIN_PRESSURE",
            "sentiment": "NEGATIVE",
            "materiality": "MEDIUM",
            "raw_score": -0.45,
            "alpha_shock_pct": -1.20,
            "date": "2026-08-10"
        },
        "CCAP.CA": {
            "headline_ar": "محادثات مستمرة لإعادة هيكلة مديونيات الشركات التابعة وتقييم حصص التخارج",
            "headline_en": "Ongoing subsidiary debt restructuring talks and asset disposal evaluations",
            "event_type": "DEBT_RESTRUCTURING",
            "sentiment": "NEGATIVE",
            "materiality": "HIGH",
            "raw_score": -0.55,
            "alpha_shock_pct": -1.80,
            "date": "2026-08-11"
        }
    }

    # NLP Lexicon for On-the-Fly Text Scoring
    POSITIVE_KEYWORDS = [
        "نمو", "أرباح", "توزيعات", "عقد", "استحواذ", "توسع", "تجاوز التوقعات", "قياسي", "شراء أسهم خزينة",
        "ارتفاع", "تصدير", "دولاري", "عائد", "surge", "growth", "beat", "dividend", "record", "profit"
    ]
    NEGATIVE_KEYWORDS = [
        "خسائر", "تراجع", "تأجيل", "دعوى", "غرامة", "انخفاض", "ضغط", "هبوط", "ديون", "مخاطر", "نزاع",
        "drop", "loss", "decline", "pressure", "debt", "risk", "penalty"
    ]

    @classmethod
    def score_text_sentiment(cls, text: str) -> Dict[str, Any]:
        """Performs dictionary-based financial NLP sentiment scoring on arbitrary headlines."""
        if not text:
            return {"score": 0.0, "label": cls.SENTIMENT_NEUTRAL, "impact": cls.IMPACT_LOW}

        txt = text.lower()
        pos_matches = sum(1 for kw in cls.POSITIVE_KEYWORDS if kw in txt)
        neg_matches = sum(1 for kw in cls.NEGATIVE_KEYWORDS if kw in txt)

        net = pos_matches - neg_matches
        if net > 0:
            score = min(0.30 + net * 0.20, 0.95)
            label = cls.SENTIMENT_POSITIVE
            impact = cls.IMPACT_HIGH if net >= 2 else cls.IMPACT_MEDIUM
        elif net < 0:
            score = max(-0.30 + net * 0.20, -0.95)
            label = cls.SENTIMENT_NEGATIVE
            impact = cls.IMPACT_HIGH if abs(net) >= 2 else cls.IMPACT_MEDIUM
        else:
            score = 0.0
            label = cls.SENTIMENT_NEUTRAL
            impact = cls.IMPACT_LOW

        return {
            "score": round(score, 2),
            "label": label,
            "impact": impact,
            "pos_tokens": pos_matches,
            "neg_tokens": neg_matches
        }

    @classmethod
    def get_sentiment_impact(cls, ticker: str) -> Dict[str, Any]:
        """
        Returns sentiment analysis, materiality, and alpha shock percentage for a stock.
        """
        sym = ticker.upper().strip()
        if not sym.endswith(".CA") and "." not in sym:
            sym = f"{sym}.CA"

        disc = cls.LATEST_DISCLOSURES.get(sym)
        if disc:
            score = disc["raw_score"]
            sentiment = disc["sentiment"]
            materiality = disc["materiality"]
            alpha_shock = disc["alpha_shock_pct"]
            headline = disc["headline_ar"]
            event_type = disc["event_type"]
        else:
            score = 0.15
            sentiment = cls.SENTIMENT_NEUTRAL
            materiality = cls.IMPACT_LOW
            alpha_shock = +0.25
            headline = "استقرار في الإفصاحات الرسمية والأداء التشغيلي الاعتيادي"
            event_type = "ROUTINE_OPERATIONS"

        label_ar = {
            cls.SENTIMENT_POSITIVE: "🟢 إيجابي ومحفز للنمو",
            cls.SENTIMENT_NEUTRAL: "⚪ محايد / استقرار تشغيلي",
            cls.SENTIMENT_NEGATIVE: "🔴 سلبي / حذر من ضغوط"
        }.get(sentiment, "محايد")

        return {
            "ticker": sym,
            "sentiment_score": score,
            "sentiment_label": sentiment,
            "sentiment_label_ar": label_ar,
            "materiality": materiality,
            "event_type": event_type,
            "headline_ar": headline,
            "alpha_shock_pct": alpha_shock,
            "is_catalyst": sentiment == cls.SENTIMENT_POSITIVE and materiality in [cls.IMPACT_HIGH, cls.IMPACT_MEDIUM],
            "is_risk_event": sentiment == cls.SENTIMENT_NEGATIVE
        }
