#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/corporate_actions_engine.py — Corporate Actions Shield & Intrinsic DCF Engine
# 1. Dividend & Ex-Date Shield: Prevents false stop-loss triggers on ex-dividend drops.
# 2. Corporate Actions Registry: Tracks dividends, bonus shares, splits, and capital changes.
# 3. Two-Stage DCF Intrinsic Valuation & Margin of Safety calculation.
# =============================================================================

import os
import sys
import json
import datetime
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.market_price_service import MarketPriceService
from core.corporate_actions_calendar import CorporateActionsCalendar, ActionType


class CorporateActionsEngine:
    """
    Institutional engine managing corporate actions protection and fundamental DCF valuation.
    """

    # Default Egyptian equity valuation parameters
    DEFAULT_DISCOUNT_RATE_PCT = 21.50   # Cost of Equity / WACC in EGP (~19.75% corridor + ERP)
    DEFAULT_TERMINAL_GROWTH_PCT = 6.50  # Long-term nominal Egyptian GDP growth rate

    # =========================================================================
    # 1. DIVIDEND & EX-DATE SHIELD (STOP-LOSS PROTECTION)
    # =========================================================================

    @classmethod
    def check_ex_dividend_shield(
        cls,
        ticker: str,
        current_price: float,
        prev_close: float,
        date_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates whether a current price drop on or near the Ex-Dividend date
        is purely mechanical due to cash dividend payout or bonus share distribution,
        and suppresses false Stop-Loss execution.
        """
        sym_clean = ticker.upper().strip()
        if not sym_clean.endswith(".CA") and "." not in sym_clean:
            sym_clean = f"{sym_clean}.CA"

        ref_date = date_str or datetime.date.today().isoformat()

        # Check calendar events for this ticker
        events = CorporateActionsCalendar.VERIFIED_EVENTS_DB
        matching_event = None

        for ev in events:
            if ev.get("ticker") == sym_clean:
                ex_date = ev.get("ex_date")
                if ex_date:
                    # Compare date or allow matching within known event registry
                    if ex_date == ref_date or date_str is None:
                        matching_event = ev
                        break

        # If no specific scheduled event in database, check general dividend drops
        if matching_event:
            div_val = float(matching_event.get("equivalent_egp") or matching_event.get("value", 0.0))
            action_type = matching_event.get("action_type", "CASH_DIVIDEND")
            
            # Theoretical ex-dividend price = prev_close - dividend
            theoretical_ex_price = max(0.01, prev_close - div_val)
            actual_drop = prev_close - current_price
            
            # If price drop is within 1.5x of the dividend amount, suppress stop loss
            if actual_drop > 0 and actual_drop <= (div_val * 1.5):
                suppress = True
                reason_ar = (
                    f"🛡️ درع التوزيعات النقدية: تراجع السعر بمقدار {actual_drop:.2f} ج.م يتطابق مع تاريخ استحقاق "
                    f"الكوبون النقدي (Ex-Date: {matching_event.get('ex_date')}) بقيمة {div_val:.2f} ج.م - "
                    f"تم حجب أمر إيقاف الخسارة الزائف بنجاح."
                )
            else:
                suppress = False
                reason_ar = "حركة السعر تتجاوز أثر التوزيع النقدي المعتاد"

            return {
                "ticker": sym_clean,
                "is_ex_dividend_window": True,
                "suppress_stop_loss": suppress,
                "event_id": matching_event.get("event_id"),
                "action_type": action_type,
                "dividend_value_egp": div_val,
                "theoretical_adjusted_close": round(theoretical_ex_price, 2),
                "actual_price_drop_egp": round(actual_drop, 2),
                "reason_ar": reason_ar
            }

        return {
            "ticker": sym_clean,
            "is_ex_dividend_window": False,
            "suppress_stop_loss": False,
            "event_id": None,
            "action_type": None,
            "dividend_value_egp": 0.0,
            "theoretical_adjusted_close": round(prev_close, 2),
            "actual_price_drop_egp": round(max(0.0, prev_close - current_price), 2),
            "reason_ar": "لا توجد توزيعات نقدية مسجلة في هذا التاريخ"
        }

    # =========================================================================
    # 2. DCF INTRINSIC FAIR VALUE & MARGIN OF SAFETY
    # =========================================================================

    @classmethod
    def calculate_fair_value(
        cls,
        ticker: str,
        custom_growth_rate_pct: Optional[float] = None,
        custom_discount_rate_pct: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculates intrinsic DCF fair value, margin of safety %, and institutional verdict.
        Formula:
          1. 5-Year Cash Flow Projection discounted at WACC (~21.5%).
          2. Terminal Value discounted to present value.
          3. Margin of Safety % = ((Fair Value - Current Price) / Fair Value) * 100.
        """
        sym_clean = ticker.upper().strip()
        if not sym_clean.endswith(".CA") and "." not in sym_clean:
            sym_clean = f"{sym_clean}.CA"

        # Canonical price lookup
        canon = MarketPriceService.CANONICAL_PRICES.get(sym_clean, {})
        current_price = float(canon.get("price", 10.0))
        if current_price <= 0:
            current_price = 10.0

        # Fundamental benchmarks by sector & stock
        from core.fundamental_data_engine import FundamentalDataEngine
        try:
            fund = FundamentalDataEngine.fetch_fundamentals(sym_clean) or {}
        except Exception:
            fund = {}
        
        eps = float(fund.get("trailingEps") or fund.get("eps") or 0.0)
        pe = float(fund.get("trailingPE") or fund.get("forwardPE") or fund.get("pe_ratio") or 0.0)
        roe = float(fund.get("returnOnEquity") or fund.get("roe") or 0.18)
        bvps = float(fund.get("bookValue") or fund.get("book_value_per_share") or 0.0)

        # Fallback EPS calculation if missing
        if eps <= 0:
            if pe > 0:
                eps = current_price / pe
            elif bvps > 0:
                eps = bvps * roe
            else:
                eps = current_price * 0.11  # ~11% default earnings yield

        # Growth rates
        g_rate = (custom_growth_rate_pct or 14.0) / 100.0  # 14% 5-year growth
        r_rate = (custom_discount_rate_pct or cls.DEFAULT_DISCOUNT_RATE_PCT) / 100.0
        g_terminal = cls.DEFAULT_TERMINAL_GROWTH_PCT / 100.0

        # Stage 1: 5-Year Projected EPS / Free Cash Flow to Equity
        pv_cash_flows = 0.0
        projected_eps = eps
        for year in range(1, 6):
            projected_eps *= (1.0 + g_rate)
            discount_factor = (1.0 + r_rate) ** year
            pv_cash_flows += projected_eps / discount_factor

        # Stage 2: Terminal Value via Gordon Growth Model
        terminal_value = (projected_eps * (1.0 + g_terminal)) / (r_rate - g_terminal)
        pv_terminal_value = terminal_value / ((1.0 + r_rate) ** 5)

        # Intrinsic Fair Value per share
        dcf_fair_value = round(pv_cash_flows + pv_terminal_value, 2)
        if dcf_fair_value <= 0:
            dcf_fair_value = round(current_price * 1.15, 2)

        # Margin of Safety %
        margin_of_safety_pct = round(((dcf_fair_value - current_price) / dcf_fair_value) * 100.0, 2)
        is_undervalued = margin_of_safety_pct > 0

        # Formulate Arabic Institutional Verdict
        if margin_of_safety_pct >= 25.0:
            verdict_ar = f"🟢 سهم مقوم بأقل من قيمته العادلة بخصم كبير (فرصة ذهبية بهامش أمان {margin_of_safety_pct:.1f}%)"
            action_bias = "STRONG_ACCUMULATE"
        elif margin_of_safety_pct >= 10.0:
            verdict_ar = f"🟢 سهم مقوم بأقل من قيمته العادلة (بهامش أمان استثماري جيد {margin_of_safety_pct:.1f}%)"
            action_bias = "ACCUMULATE"
        elif margin_of_safety_pct >= -10.0:
            verdict_ar = f"🟡 سهم يتداول بالقرب من قيمته العادلة (نطاق توازن عادل {margin_of_safety_pct:+.1f}%)"
            action_bias = "HOLD"
        else:
            verdict_ar = f"🔴 سهم مقوم بأعلى من قيمته العادلة (علاوة سعرية تفوق التقييم بنسبة {abs(margin_of_safety_pct):.1f}%)"
            action_bias = "TRIM_OR_AVOID"

        return {
            "ticker": sym_clean,
            "current_price_egp": round(current_price, 2),
            "fair_value_egp": dcf_fair_value,
            "margin_of_safety_pct": margin_of_safety_pct,
            "is_undervalued": is_undervalued,
            "action_bias": action_bias,
            "verdict_ar": verdict_ar,
            "valuation_method": "Two-Stage DCF (Discounted Cash Flow to Equity)",
            "inputs": {
                "base_eps_egp": round(eps, 2),
                "growth_rate_5y_pct": round(g_rate * 100.0, 1),
                "discount_rate_wacc_pct": round(r_rate * 100.0, 1),
                "terminal_growth_pct": round(g_terminal * 100.0, 1)
            }
        }
