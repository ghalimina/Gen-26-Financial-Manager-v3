#!/usr/bin/env python3
# =============================================================================
# core/corporate_actions_calendar.py — GEN-26 Corporate Actions & Events Calendar
# Tracks dividends, stock splits, bonus shares, capital increases, and trading
# suspensions across the active Egyptian Exchange (EGX) universe.
# =============================================================================

import os
import sys
import json
import datetime
from typing import Dict, List, Any, Optional
from enum import Enum

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

DATA_DIR = os.path.join(WORKSPACE, "data")
CORPORATE_ACTIONS_FILE = os.path.join(DATA_DIR, "corporate_actions_calendar.json")


class ActionType(str, Enum):
    CASH_DIVIDEND = "CASH_DIVIDEND"
    STOCK_SPLIT = "STOCK_SPLIT"
    BONUS_SHARES = "BONUS_SHARES"
    CAPITAL_INCREASE = "CAPITAL_INCREASE"
    RIGHTS_ISSUE = "RIGHTS_ISSUE"
    PAR_VALUE_CHANGE = "PAR_VALUE_CHANGE"
    TRADING_HALT = "TRADING_HALT"


class CorporateActionsCalendar:
    """
    Authoritative Corporate Actions Engine for the Egyptian Exchange.
    Detects upcoming and historical events, computes theoretical price adjustments,
    and prevents quantitative factor distortion from dividend drops and stock splits.
    """

    # Baseline Verified EGX Corporate Actions Repository (Historical & Scheduled)
    VERIFIED_EVENTS_DB: List[Dict[str, Any]] = [
        # --- ORASCOM CONSTRUCTION (ORAS.CA) ---
        {
            "event_id": "ORAS_2026_DIV_01",
            "ticker": "ORAS.CA",
            "action_type": ActionType.CASH_DIVIDEND.value,
            "announcement_date": "2026-05-15",
            "ex_date": "2026-06-25",
            "payment_date": "2026-07-10",
            "value": 0.275,  # USD converted to EGP ~ 13.50 EGP
            "currency": "USD",
            "equivalent_egp": 13.50,
            "description_ar": "توزيع كوبون نقدي بقيمة 0.275 دولار للسهم (حوالي 13.50 ج.م)",
            "description_en": "Cash dividend of USD 0.275 per share",
            "is_completed": True
        },
        # --- COMMERCIAL INTERNATIONAL BANK (COMI.CA) ---
        {
            "event_id": "COMI_2026_DIV_01",
            "ticker": "COMI.CA",
            "action_type": ActionType.CASH_DIVIDEND.value,
            "announcement_date": "2026-03-20",
            "ex_date": "2026-04-18",
            "payment_date": "2026-04-30",
            "value": 5.50,
            "currency": "EGP",
            "equivalent_egp": 5.50,
            "description_ar": "كوبون نقدي بقيمة 5.50 ج.م للسهم عن أرباح عام 2025",
            "description_en": "Cash dividend of 5.50 EGP per share for FY2025",
            "is_completed": True
        },
        # --- ELSEWEDY ELECTRIC (SWDY.CA) ---
        {
            "event_id": "SWDY_2026_DIV_01",
            "ticker": "SWDY.CA",
            "action_type": ActionType.CASH_DIVIDEND.value,
            "announcement_date": "2026-04-10",
            "ex_date": "2026-05-12",
            "payment_date": "2026-05-28",
            "value": 4.00,
            "currency": "EGP",
            "equivalent_egp": 4.00,
            "description_ar": "توزيع كوبون نقدي بقيمة 4.00 ج.م للسهم",
            "description_en": "Cash dividend of 4.00 EGP per share",
            "is_completed": True
        },
        # --- TALAAT MOUSTAFA GROUP (TMGH.CA) ---
        {
            "event_id": "TMGH_2026_DIV_01",
            "ticker": "TMGH.CA",
            "action_type": ActionType.CASH_DIVIDEND.value,
            "announcement_date": "2026-03-30",
            "ex_date": "2026-05-05",
            "payment_date": "2026-05-20",
            "value": 2.20,
            "currency": "EGP",
            "equivalent_egp": 2.20,
            "description_ar": "كوبون نقدي بقيمة 2.20 ج.م للسهم على قسطين متساويين",
            "description_en": "Cash dividend of 2.20 EGP in two installments",
            "is_completed": True
        },
        # --- ABU QIR FERTILIZERS (ABUK.CA) ---
        {
            "event_id": "ABUK_2026_DIV_01",
            "ticker": "ABUK.CA",
            "action_type": ActionType.CASH_DIVIDEND.value,
            "announcement_date": "2026-09-15",
            "ex_date": "2026-10-20",
            "payment_date": "2026-11-05",
            "value": 7.00,
            "currency": "EGP",
            "equivalent_egp": 7.00,
            "description_ar": "توزيع نقدي مقترح بقيمة 7.00 ج.م للسهم (عائد توزيع ~9.2%)",
            "description_en": "Proposed cash dividend of 7.00 EGP per share (Yield ~9.2%)",
            "is_completed": False
        },
        # --- EGYPT ALUMINIUM (EGAL.CA) ---
        {
            "event_id": "EGAL_2026_DIV_01",
            "ticker": "EGAL.CA",
            "action_type": ActionType.CASH_DIVIDEND.value,
            "announcement_date": "2026-10-01",
            "ex_date": "2026-11-15",
            "payment_date": "2026-11-30",
            "value": 25.00,
            "currency": "EGP",
            "equivalent_egp": 25.00,
            "description_ar": "توزيع كوبون نقدي سخي بقيمة 25.00 ج.م للسهم بفضل هوامش التصدير القياسية",
            "description_en": "Generous cash dividend of 25.00 EGP per share on export earnings",
            "is_completed": False
        },
        # --- MISR FERTILIZERS PRODUCTION - MOPCO (MFPC.CA) ---
        {
            "event_id": "MFPC_2026_SPLIT_01",
            "ticker": "MFPC.CA",
            "action_type": ActionType.STOCK_SPLIT.value,
            "announcement_date": "2025-11-10",
            "ex_date": "2025-12-15",
            "payment_date": "2025-12-16",
            "value": 4.0,  # 1:4 stock split
            "currency": "RATIO",
            "description_ar": "تجزئة القيمة الاسمية للسهم من 10 ج.م إلى 2.5 ج.م (بواقع 4 أسهم لكل سهم)",
            "description_en": "Stock split 1:4 nominal value from 10 EGP to 2.5 EGP",
            "is_completed": True
        },
        # --- TELECOM EGYPT (ETEL.CA) ---
        {
            "event_id": "ETEL_2026_DIV_01",
            "ticker": "ETEL.CA",
            "action_type": ActionType.CASH_DIVIDEND.value,
            "announcement_date": "2026-03-25",
            "ex_date": "2026-04-24",
            "payment_date": "2026-05-10",
            "value": 1.50,
            "currency": "EGP",
            "equivalent_egp": 1.50,
            "description_ar": "توزيع كوبون نقدي بقيمة 1.50 ج.م للسهم",
            "description_en": "Cash dividend of 1.50 EGP per share",
            "is_completed": True
        },
        # --- E-FINANCE (EFIH.CA) ---
        {
            "event_id": "EFIH_2026_DIV_01",
            "ticker": "EFIH.CA",
            "action_type": ActionType.CASH_DIVIDEND.value,
            "announcement_date": "2026-04-05",
            "ex_date": "2026-05-08",
            "payment_date": "2026-05-22",
            "value": 0.35,
            "currency": "EGP",
            "equivalent_egp": 0.35,
            "description_ar": "كوبون نقدي بقيمة 0.35 ج.م للسهم",
            "description_en": "Cash dividend of 0.35 EGP per share",
            "is_completed": True
        },
        # --- EZZ STEEL (ESRS.CA) ---
        {
            "event_id": "ESRS_2026_RIGHTS_01",
            "ticker": "ESRS.CA",
            "action_type": ActionType.CAPITAL_INCREASE.value,
            "announcement_date": "2026-06-10",
            "ex_date": "2026-07-20",
            "payment_date": "2026-08-05",
            "value": 100.0,
            "currency": "EGP",
            "description_ar": "زيادة رأس المال المصدر بالاكتتاب لقدامى المساهمين بسعر 100 ج.م للسهم",
            "description_en": "Rights issue capital increase at 100 EGP per share",
            "is_completed": True
        },
        # --- PALM HILLS DEVELOPMENTS (PHDC.CA) ---
        {
            "event_id": "PHDC_2026_DIV_01",
            "ticker": "PHDC.CA",
            "action_type": ActionType.CASH_DIVIDEND.value,
            "announcement_date": "2026-04-12",
            "ex_date": "2026-05-18",
            "payment_date": "2026-05-30",
            "value": 0.35,
            "currency": "EGP",
            "equivalent_egp": 0.35,
            "description_ar": "توزيع كوبون نقدي بقيمة 0.35 ج.م للسهم عن أرباح عام 2025",
            "description_en": "Cash dividend of 0.35 EGP per share",
            "is_completed": True
        },
        # --- RAYA HOLDING (RAYA.CA) ---
        {
            "event_id": "RAYA_2026_DIV_01",
            "ticker": "RAYA.CA",
            "action_type": ActionType.CASH_DIVIDEND.value,
            "announcement_date": "2026-05-02",
            "ex_date": "2026-06-15",
            "payment_date": "2026-06-30",
            "value": 0.25,
            "currency": "EGP",
            "equivalent_egp": 0.25,
            "description_ar": "كوبون نقدي بقيمة 0.25 ج.م للسهم",
            "description_en": "Cash dividend of 0.25 EGP per share",
            "is_completed": True
        }
    ]

    _IN_MEMORY_EVENTS: Optional[List[Dict[str, Any]]] = None

    @classmethod
    def load_events(cls) -> List[Dict[str, Any]]:
        """Loads events from disk or initializes defaults."""
        if cls._IN_MEMORY_EVENTS is not None:
            return cls._IN_MEMORY_EVENTS

        if os.path.exists(CORPORATE_ACTIONS_FILE):
            try:
                with open(CORPORATE_ACTIONS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list) and data:
                    cls._IN_MEMORY_EVENTS = data
                    return cls._IN_MEMORY_EVENTS
            except Exception:
                pass

        cls.save_events(cls.VERIFIED_EVENTS_DB)
        cls._IN_MEMORY_EVENTS = cls.VERIFIED_EVENTS_DB
        return cls._IN_MEMORY_EVENTS

    @classmethod
    def save_events(cls, events: List[Dict[str, Any]]) -> bool:
        """Persists corporate actions to disk atomically."""
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            tmp_f = f"{CORPORATE_ACTIONS_FILE}.tmp"
            with open(tmp_f, "w", encoding="utf-8") as f:
                json.dump(events, f, ensure_ascii=False, indent=2)
            os.replace(tmp_f, CORPORATE_ACTIONS_FILE)
            cls._IN_MEMORY_EVENTS = events
            return True
        except Exception:
            return False

    @classmethod
    def get_events_for_ticker(cls, ticker: str) -> List[Dict[str, Any]]:
        """Retrieves all corporate actions for a given ticker."""
        sym = ticker.upper().strip()
        if not sym.endswith(".CA") and "." not in sym:
            sym = f"{sym}.CA"
        events = cls.load_events()
        return [e for e in events if e["ticker"].upper() == sym]

    @classmethod
    def get_upcoming_events(cls, days_window: int = 45, reference_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves all upcoming scheduled corporate events within days_window.
        """
        today = datetime.datetime.strptime(reference_date, "%Y-%m-%d").date() if reference_date else datetime.date.today()
        end_date = today + datetime.timedelta(days=days_window)
        events = cls.load_events()

        upcoming = []
        for e in events:
            ex_str = e.get("ex_date")
            if not ex_str:
                continue
            try:
                ex_d = datetime.datetime.strptime(ex_str, "%Y-%m-%d").date()
                if today <= ex_d <= end_date and not e.get("is_completed", False):
                    e_copy = e.copy()
                    e_copy["days_until_ex"] = (ex_d - today).days
                    upcoming.append(e_copy)
            except ValueError:
                continue

        upcoming.sort(key=lambda x: x.get("days_until_ex", 999))
        return upcoming

    @classmethod
    def evaluate_pre_trade_corporate_hazard(cls, ticker: str, current_price: float) -> Dict[str, Any]:
        """
        Evaluates pre-trade corporate action hazards (ex-dividend drops, dilution, suspensions).
        Returns risk multipliers and adjustment estimates for position sizing.
        """
        sym = ticker.upper().strip()
        if not sym.endswith(".CA") and "." not in sym:
            sym = f"{sym}.CA"

        events = cls.get_events_for_ticker(sym)
        today = datetime.date.today()

        hazard = {
            "has_imminent_event": False,
            "hazard_level": "LOW",
            "imminent_event": None,
            "theoretical_adjusted_price": current_price,
            "dividend_yield_pct": 0.0,
            "alpha_multiplier": 1.0,
            "warning_ar": None
        }

        for e in events:
            ex_str = e.get("ex_date")
            if not ex_str:
                continue
            try:
                ex_d = datetime.datetime.strptime(ex_str, "%Y-%m-%d").date()
                days_left = (ex_d - today).days
                # Check for events within 14 days
                if 0 <= days_left <= 14 and not e.get("is_completed", False):
                    hazard["has_imminent_event"] = True
                    hazard["imminent_event"] = e
                    act_type = e.get("action_type")

                    if act_type == ActionType.CASH_DIVIDEND.value:
                        div_val = float(e.get("equivalent_egp", e.get("value", 0.0)))
                        hazard["theoretical_adjusted_price"] = max(round(current_price - div_val, 2), 0.01)
                        hazard["dividend_yield_pct"] = round((div_val / current_price) * 100.0, 2) if current_price > 0 else 0.0
                        hazard["hazard_level"] = "MEDIUM" if hazard["dividend_yield_pct"] < 6.0 else "HIGH"
                        hazard["alpha_multiplier"] = 0.85
                        hazard["warning_ar"] = f"تاريخ استحقاق كوبون نقدي بقيمة {div_val:.2f} ج.م بعد {days_left} أيام — السعر النظري بعد التوزيع: {hazard['theoretical_adjusted_price']:.2f} ج.م."

                    elif act_type == ActionType.STOCK_SPLIT.value:
                        split_ratio = float(e.get("value", 2.0))
                        hazard["theoretical_adjusted_price"] = round(current_price / split_ratio, 2)
                        hazard["hazard_level"] = "HIGH"
                        hazard["alpha_multiplier"] = 0.70
                        hazard["warning_ar"] = f"تجزئة سهم قادمة بنسبة 1:{split_ratio:.0f} بعد {days_left} أيام — ضبط أوامر التداول ووقف الخسارة إلزامي."

                    elif act_type == ActionType.TRADING_HALT.value:
                        hazard["hazard_level"] = "CRITICAL"
                        hazard["alpha_multiplier"] = 0.0
                        hazard["warning_ar"] = "إيقاف تداول مؤقت مجدول للإفصاح عن بيانات جوهرية."
                    break
            except Exception:
                continue

        return hazard


if __name__ == "__main__":
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("=" * 70)
    print("GEN-26 CORPORATE ACTIONS & EVENTS CALENDAR")
    print("=" * 70)
    all_evs = CorporateActionsCalendar.load_events()
    print(f"Total Registered Events: {len(all_evs)}")
    oras_evs = CorporateActionsCalendar.get_events_for_ticker("ORAS.CA")
    print(f"ORAS.CA Events: {len(oras_evs)}")
    for ev in oras_evs:
        print(f" - [{ev['action_type']}] Ex-Date: {ev['ex_date']} | {ev['description_ar']}")
    print("=" * 70)
