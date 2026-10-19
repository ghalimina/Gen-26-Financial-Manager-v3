#!/usr/bin/env python3
# =============================================================================
# core/intraday_session_clock.py — EGX Intraday Trading Session Clock & Phase Engine
# Real-time state machine tracking Cairo timezone EGX trading sessions, auctions,
# countdown timers, and micro-structure execution phases.
# =============================================================================

import os
import datetime
from typing import Dict, Any, Optional

try:
    from zoneinfo import ZoneInfo
    CAIRO_TZ = ZoneInfo("Africa/Cairo")
except Exception:
    CAIRO_TZ = datetime.timezone(datetime.timedelta(hours=2))


class EGXSessionClock:
    """
    Authoritative state machine for Egyptian Exchange (EGX) operational hours and session phases.
    """

    PHASES_INFO = {
        "PRE_MARKET_WAIT": {
            "name_ar": "ما قبل الجلسة (انتظار المزاد)",
            "description_ar": "السوق مغلق في انتظار مزاد الافتتاح لاستكشاف السعر.",
            "is_trading": False,
            "badge_color": "secondary"
        },
        "PRE_OPEN_AUCTION": {
            "name_ar": "مزاد سعر الافتتاح (Discovery)",
            "description_ar": "مزاد تحديد سعر الفتح (09:30 - 10:00 ص) بدون تنفيذ مباشر.",
            "is_trading": False,
            "badge_color": "warning"
        },
        "CONTINUOUS_TRADING": {
            "name_ar": "جلسة التداول المستمر (Active)",
            "description_ar": "جلسة التداول الرسمية المباشرة (10:00 ص - 02:15 م).",
            "is_trading": True,
            "badge_color": "success"
        },
        "CLOSING_AUCTION": {
            "name_ar": "مزاد سعر الإغلاق (Fixing)",
            "description_ar": "مزاد تحديد سعر الإغلاق وحساب متوسط التنفيذات (02:15 - 02:30 م).",
            "is_trading": False,
            "badge_color": "warning"
        },
        "POST_CLOSE": {
            "name_ar": "تسوية ما بعد الإغلاق",
            "description_ar": "فترة تداول الصفقات والتسويات الختامية (02:30 - 03:00 م).",
            "is_trading": False,
            "badge_color": "info"
        },
        "MARKET_CLOSED_OVERNIGHT": {
            "name_ar": "السوق مغلق (بانتظار جلسة الغد)",
            "description_ar": "انتهت جلسة اليوم، السوق مغلق ويستأنف نشاطه في يوم العمل القادم.",
            "is_trading": False,
            "badge_color": "dark"
        },
        "WEEKEND_HOLIDAY": {
            "name_ar": "عطلة نهاية الأسبوع (الجمعة/السبت)",
            "description_ar": "بورصة مصر في عطلة أسبوعية رسمية. تفتح الجلسة القادمة يوم الأحد 09:30 ص.",
            "is_trading": False,
            "badge_color": "dark"
        }
    }

    @classmethod
    def get_cairo_now(cls) -> datetime.datetime:
        """Returns current datetime in Africa/Cairo timezone."""
        try:
            return datetime.datetime.now(CAIRO_TZ)
        except Exception:
            return datetime.datetime.now()

    @classmethod
    def get_session_status(cls, dt: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        """
        Determines current session phase, remaining countdown, and market status.
        """
        if dt is None:
            now = cls.get_cairo_now()
        else:
            now = dt

        # EGX Trading days: Sunday (6) through Thursday (3). Friday (4) and Saturday (5) are weekend.
        # Python weekday: Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
        weekday = now.weekday()
        is_weekend = (weekday in (4, 5))  # Friday or Saturday

        time_now = now.time()
        t_pre_open = datetime.time(9, 30, 0)
        t_open = datetime.time(10, 0, 0)
        t_close_auction = datetime.time(14, 15, 0)
        t_post_close = datetime.time(14, 30, 0)
        t_market_end = datetime.time(15, 0, 0)

        if is_weekend:
            phase = "WEEKEND_HOLIDAY"
            # Calculate time to next Sunday 09:30
            days_ahead = (6 - weekday) % 7
            if days_ahead == 0 and time_now >= t_pre_open:
                days_ahead = 7
            next_open = (now + datetime.timedelta(days=days_ahead)).replace(
                hour=9, minute=30, second=0, microsecond=0
            )
            time_to_next = int((next_open - now).total_seconds())
            next_phase_desc = "حتى افتتاح مزاد الأحد"
        elif time_now < t_pre_open:
            phase = "PRE_MARKET_WAIT"
            target = now.replace(hour=9, minute=30, second=0, microsecond=0)
            time_to_next = int((target - now).total_seconds())
            next_phase_desc = "حتى بدء مزاد الافتتاح"
        elif t_pre_open <= time_now < t_open:
            phase = "PRE_OPEN_AUCTION"
            target = now.replace(hour=10, minute=0, second=0, microsecond=0)
            time_to_next = int((target - now).total_seconds())
            next_phase_desc = "حتى انطلاق التداول المستمر"
        elif t_open <= time_now < t_close_auction:
            phase = "CONTINUOUS_TRADING"
            target = now.replace(hour=14, minute=15, second=0, microsecond=0)
            time_to_next = int((target - now).total_seconds())
            next_phase_desc = "حتى بدء مزاد الإغلاق"
        elif t_close_auction <= time_now < t_post_close:
            phase = "CLOSING_AUCTION"
            target = now.replace(hour=14, minute=30, second=0, microsecond=0)
            time_to_next = int((target - now).total_seconds())
            next_phase_desc = "حتى انتهاء مزاد الإغلاق"
        elif t_post_close <= time_now < t_market_end:
            phase = "POST_CLOSE"
            target = now.replace(hour=15, minute=0, second=0, microsecond=0)
            time_to_next = int((target - now).total_seconds())
            next_phase_desc = "حتى إغلاق السوق التام"
        else:
            phase = "MARKET_CLOSED_OVERNIGHT"
            # Next trading session: tomorrow if Sun-Wed, or Sunday if Thursday
            days_ahead = 3 if weekday == 3 else 1
            next_open = (now + datetime.timedelta(days=days_ahead)).replace(
                hour=9, minute=30, second=0, microsecond=0
            )
            time_to_next = int((next_open - now).total_seconds())
            next_phase_desc = "حتى افتتاح مزاد الغد" if days_ahead == 1 else "حتى افتتاح مزاد الأحد"

        # Format countdown
        if time_to_next < 0:
            time_to_next = 0
        hours = time_to_next // 3600
        minutes = (time_to_next % 3600) // 60
        seconds = time_to_next % 60
        countdown_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        phase_meta = cls.PHASES_INFO.get(phase, {})

        return {
            "status": "SUCCESS",
            "cairo_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "cairo_time_short": now.strftime("%H:%M:%S"),
            "timezone": "Africa/Cairo (UTC+2)",
            "weekday_name_ar": ["الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت", "الأحد"][weekday],
            "is_trading_day": not is_weekend,
            "is_market_open": phase_meta.get("is_trading", False),
            "current_phase": phase,
            "phase_name_ar": phase_meta.get("name_ar", phase),
            "description_ar": phase_meta.get("description_ar", ""),
            "badge_color": phase_meta.get("badge_color", "secondary"),
            "countdown_seconds": time_to_next,
            "countdown_formatted": countdown_formatted,
            "next_phase_label_ar": next_phase_desc,
            "intraday_pulse": "BULLISH_FLOW" if phase == "CONTINUOUS_TRADING" else "SETTLED_HARMONIC"
        }


# Aliases for compatibility
IntradaySessionClock = EGXSessionClock
intraday_session_clock = EGXSessionClock


def get_egx_session_clock() -> Dict[str, Any]:
    return EGXSessionClock.get_session_status()


if __name__ == "__main__":
    import pprint
    pprint.pprint(get_egx_session_clock())
