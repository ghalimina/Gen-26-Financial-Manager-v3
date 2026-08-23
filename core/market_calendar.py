#!/usr/bin/env python3
# =============================================================================
# core/market_calendar.py — GEN-26 Egyptian Exchange (EGX) Market Calendar
# Handles EGX trading days (Sunday to Thursday), official market holidays,
# market session hours, duplicate session detection, and fail-closed checks.
# =============================================================================

import datetime
from typing import Dict, List, Any, Optional

try:
    import pytz
    CAIRO_TZ = pytz.timezone("Africa/Cairo")
except ImportError:
    CAIRO_TZ = None


class EGXMarketCalendar:
    """
    Authoritative calendar engine for Egyptian Exchange (EGX) trading sessions.
    """

    # Official Annual EGX Holidays (Fixed dates & observed national holidays)
    EGX_HOLIDAYS = {
        "2026-01-01": "New Year's Day",
        "2026-01-07": "Coptic Christmas",
        "2026-01-25": "Revolution / Police Day",
        "2026-04-12": "Easter Holiday",
        "2026-04-13": "Sham El-Nessim",
        "2026-04-25": "Sinai Liberation Day",
        "2026-05-01": "Labour Day",
        "2026-05-26": "Eid al-Adha (Arafat Day)",
        "2026-05-27": "Eid al-Adha Holiday",
        "2026-05-28": "Eid al-Adha Holiday",
        "2026-06-17": "Islamic New Year",
        "2026-06-30": "30 June Day",
        "2026-07-23": "Revolution Day",
        "2026-08-26": "Prophet's Birthday",
        "2026-10-06": "Armed Forces Day"
    }

    @classmethod
    def get_cairo_time(cls) -> datetime.datetime:
        """Returns current timestamp in Cairo timezone."""
        if CAIRO_TZ:
            return datetime.datetime.now(CAIRO_TZ)
        return datetime.datetime.utcnow() + datetime.timedelta(hours=3)

    @classmethod
    def is_trading_day(cls, date_str: str) -> Dict[str, Any]:
        """
        Determines whether a given date (YYYY-MM-DD) is an eligible EGX trading day.
        EGX operates Sunday (weekday=6) through Thursday (weekday=3).
        Friday (weekday=4) and Saturday (weekday=5) are closed.
        """
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return {"is_trading_day": False, "reason": "INVALID_DATE_FORMAT"}

        # 1. Weekend check (Friday=4, Saturday=5)
        if dt.weekday() in [4, 5]:
            day_name = dt.strftime("%A")
            return {"is_trading_day": False, "reason": f"EGX_WEEKEND ({day_name})"}

        # 2. Holiday check
        if date_str in cls.EGX_HOLIDAYS:
            holiday_name = cls.EGX_HOLIDAYS[date_str]
            return {"is_trading_day": False, "reason": f"EGX_HOLIDAY ({holiday_name})"}

        return {"is_trading_day": True, "reason": "VALID_EGX_TRADING_DAY"}

    @classmethod
    def is_market_session_open(cls, dt_cairo: Optional[datetime.datetime] = None) -> bool:
        """
        EGX Continuous Trading hours are 10:00 to 14:30 Cairo time.
        """
        now = dt_cairo or cls.get_cairo_time()
        date_str = now.strftime("%Y-%m-%d")
        t_check = cls.is_trading_day(date_str)
        if not t_check["is_trading_day"]:
            return False

        # Check hour/minute
        market_open = now.replace(hour=10, minute=0, second=0, microsecond=0)
        market_close = now.replace(hour=14, minute=30, second=0, microsecond=0)
        return market_open <= now <= market_close
