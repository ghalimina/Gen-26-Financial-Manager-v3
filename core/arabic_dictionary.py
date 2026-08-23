#!/usr/bin/env python3
# =============================================================================
# core/arabic_dictionary.py — GEN-26 Centralized Arabic Financial Terminology
# Single Source of Truth (SSoT) for all Arabic labels, tooltips, actions, and messages.
# =============================================================================

from typing import Dict, Any


class ArabicFinancialDictionary:
    """
    Authoritative dictionary of standardized Arabic quantitative and financial terms.
    """

    TERMINOLOGY = {
        # Core Navigation & Sections
        "dashboard": "لوحة التحكم الكمية",
        "market_overview": "نظرة عامة على السوق",
        "stock_ranking": "ترتيب الأسهم والفرص",
        "stock_details": "ملف الاستخبارات للسهم",
        "my_real_portfolio": "محفظتي الحقيقية",
        "paper_portfolio": "المحفظة التجريبية (3/30)",
        "signal_history": "سجل الإشارات والقرارات",
        "risk_center": "مركز إدارة المخاطر والقواعد",
        "stress_center": "مركز اختبارات الضغط والسيولة",
        "paper_vs_backtest": "التداول التجريبي مقابل الاختبار التاريخي",
        "observatory": "مرصد الانحراف والانزلاق",
        "universe_audit": "فحص وتغطية بورصة مصر",
        "system_health": "صحة واستقرار النظام",

        # Action Recommendations
        "BUY": "شراء تراجعي (Limit)",
        "WATCH": "مراقبة",
        "HOLD": "احتفاظ",
        "REDUCE": "تخفيض / جني أرباح",
        "EXIT": "خروج / وقف خسارة",
        "AVOID": "تجنب",

        # Quantitative & Financial Metrics
        "rank": "الترتيب",
        "symbol": "رمز السهم",
        "company": "اسم الشركة",
        "gen26_score": "تقييم GEN-26 الكلي",
        "alpha_score": "نقاط الألفا (Alpha)",
        "risk_score": "نقاط الأمان (Risk)",
        "liquidity_score": "نقاط السيولة",
        "current_price": "السعر الحالي",
        "entry_price": "سعر الدخول المقترح",
        "target_price": "السعر المستهدف",
        "stop_loss": "وقف الخسارة (-7%)",
        "expected_return": "العائد المتوقع",
        "confidence": "درجة الثقة",
        "sector": "القطاع",
        "volume": "حجم التداول",
        "adv_20d": "متوسط التداول اليومي (20 يوم)",
        "market_regime": "حالة السوق والاتجاه",
        "breadth": "اتساع السوق (Advance Ratio)",

        # Status Badges & Alerts
        "STABLE": "مستقر",
        "WATCH_STATUS": "تحت المراقبة",
        "WARNING": "تحذير",
        "CRITICAL": "حرج",
        "PASS": "سليم / متوافق",
        "FAIL": "فشل / غير متوافق",
        "BLOCKED": "محظور / مغلق",
        "PAPER_ACTIVE": "التداول التجريبي نشط",
        "LIVE_BLOCKED": "التداول الحقيقي محظور بأمان",

        # Informational / Loading / Error Messages
        "loading": "جاري تحميل البيانات المالية...",
        "no_data": "لا توجد بيانات متاحة حالياً.",
        "error_loading": "حدث خطأ أثناء تحميل البيانات.",
        "stale_data": "البيانات قديمة، لا يمكن إنشاء أمر تداول آمن.",
        "market_closed": "السوق المصري مغلق حالياً (أيام التداول: الأحد إلى الخميس 10:00 - 14:30).",
        "not_available": "غير متاح"
    }

    @classmethod
    def get(cls, key: str, default: str = "") -> str:
        """Retrieves standardized Arabic translation for a given term."""
        return cls.TERMINOLOGY.get(key, default or key)
