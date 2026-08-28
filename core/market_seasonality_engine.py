#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/market_seasonality_engine.py — EGX Seasonality & Market Psychology Engine
# Models 3 Key Egyptian Calendar & Behavioral Anomalies:
# 1. Ramadan Session Contraction (Shortened hours, ~30% volume dip, downscaled holding).
# 2. Thursday Profit-Taking Window (Pre-weekend discount entry for Sunday open).
# 3. December Year-End Window Dressing (Institutional NAV pumping in top blue-chips).
# =============================================================================

import os
import sys
import datetime
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)


class MarketSeasonalityEngine:
    """
    Evaluates calendar seasonality, institutional behavioral patterns,
    and market psychology cycles across the Egyptian Stock Exchange.
    """

    REGIME_RAMADAN = "RAMADAN_CONTRACTION"
    REGIME_THURSDAY_DIP = "THURSDAY_PROFIT_TAKING"
    REGIME_DECEMBER_DRESSING = "DECEMBER_WINDOW_DRESSING"
    REGIME_STANDARD = "STANDARD_ACTIVE_CYCLE"

    # Known approximate Ramadan calendar windows
    _RAMADAN_WINDOWS = [
        ("2026-02-18", "2026-03-20"),
        ("2027-02-08", "2027-03-09")
    ]

    @classmethod
    def evaluate_current_seasonality(cls, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluates the active seasonality regime and yields operational strategy adjustments.
        """
        if date_str:
            try:
                current_date = datetime.date.fromisoformat(date_str)
            except Exception:
                current_date = datetime.date.today()
        else:
            current_date = datetime.date.today()

        date_iso = current_date.isoformat()
        weekday = current_date.weekday()  # Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4, Saturday=5, Sunday=6
        month = current_date.month
        day = current_date.day

        # 1. Check Ramadan Window
        is_ramadan = False
        for start_r, end_r in cls._RAMADAN_WINDOWS:
            if start_r <= date_iso <= end_r:
                is_ramadan = True
                break

        if is_ramadan:
            regime = cls.REGIME_RAMADAN
            vol_factor = 0.70
            holding_bias = "SHORTENED_SWING_2_4_DAYS"
            strategy_ar = (
                "🌙 موسم شهر رمضان المبارك: تقليص ساعات الجلسة وتراجع السيولة بنحو 30%؛ "
                "يوصى بتقصير فترات الاحتفاظ واستخدام أوامر محددة السعر (Limit Orders) حصراً لتجنب الانزلاق."
            )
            trading_hours_ar = "10:00 صباحاً - 01:30 ظهراً (جلسة رمضانية مختصرة)"

        # 2. Check December Year-End Window Dressing (Dec 10 to Dec 31)
        elif month == 12 and day >= 10:
            regime = cls.REGIME_DECEMBER_DRESSING
            vol_factor = 1.20
            holding_bias = "EXTENDED_HOLD_BLUE_CHIPS"
            strategy_ar = (
                "🎄 تجميل الميزانيات السنوية (Window Dressing): مدراء الصناديق والمؤسسات يعززون مشترياتهم "
                "في الأسهم القيادية (COMI, SWDY, TMGH, HRHO) لرفع تقييم وثائق الاستثمار السنوية (NAV)."
            )
            trading_hours_ar = "10:00 صباحاً - 02:30 بعد الظهر (تداولات إغلاق سنوية مكثفة)"

        # 3. Check Thursday Pre-Weekend Profit Taking (Thursday is weekday == 3 in Python)
        elif weekday == 3:
            regime = cls.REGIME_THURSDAY_DIP
            vol_factor = 0.90
            holding_bias = "TACTICAL_THURSDAY_ACCUMULATE"
            strategy_ar = (
                "⚡ جني أرباح نهاية الأسبوع (خميس): عمليات تسييل وإغلاق صفقات الهامش قبل العطلة الأسبوعية؛ "
                "تراجعات النصف ساعة الأخير تخلق فرص شراء بخصم سعري مناسب لافتتاح جلسة الأحد."
            )
            trading_hours_ar = "10:00 صباحاً - 02:30 بعد الظهر (ضغط تسييل في النصف ساعة الأخير)"

        # 4. Standard Active Market Cycle
        else:
            regime = cls.REGIME_STANDARD
            vol_factor = 1.00
            holding_bias = "STANDARD_QUANT_MULTI_HORIZON"
            strategy_ar = (
                "📊 دورة تداول اعتيادية: سيولة مستقرة واستجابة كاملة للمحركات الكمية والذكاء الاصطناعي."
            )
            trading_hours_ar = "10:00 صباحاً - 02:30 بعد الظهر"

        return {
            "date": date_iso,
            "day_name": current_date.strftime("%A"),
            "seasonality_regime": regime,
            "volume_adjustment_factor": vol_factor,
            "holding_period_bias": holding_bias,
            "strategy_tweak_ar": strategy_ar,
            "trading_hours_ar": trading_hours_ar,
            "is_ramadan": is_ramadan,
            "is_year_end_window": (month == 12 and day >= 10),
            "is_thursday_session": (weekday == 3)
        }
