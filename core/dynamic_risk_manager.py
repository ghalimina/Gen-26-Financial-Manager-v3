#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/dynamic_risk_manager.py — Dynamic Trailing Stop & Sector Concentration Guard
# 1. Progressive Trailing Stop Lock (+10% Breakeven, +20% / +30% Profit Locks).
# 2. Institutional Sector Concentration Guard (Max 35% Single Sector Exposure).
# =============================================================================

import os
import sys
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.egx_universe_loader import EGXUniverseLoader


class DynamicRiskManager:
    """
    Institutional dynamic risk management engine enforcing ratcheting trailing stops
    and sector concentration safeguards.
    """

    MAX_SECTOR_CONCENTRATION_PCT = 35.0  # Maximum 35% portfolio exposure to a single sector

    # =========================================================================
    # 1. DYNAMIC TRAILING STOP LOCK
    # =========================================================================

    @classmethod
    def compute_trailing_stop(
        cls,
        entry_price: float,
        peak_price: float,
        current_price: float,
        current_stop: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculates ratcheting progressive trailing stop:
        - Gain < 10%: Initial Stop (Entry * 0.95)
        - Gain >= 10%: Breakeven Stop (Entry Price)
        - Gain >= 20%: Profit Lock 1 (Peak Price * 0.92)
        - Gain >= 30%: Profit Lock 2 (Peak Price * 0.94)
        
        Rule: Stop level is an irreversible ratchet (NEVER moves down).
        """
        if entry_price <= 0:
            entry_price = 10.0
        effective_peak = max(peak_price, current_price, entry_price)
        gain_from_entry_pct = ((effective_peak - entry_price) / entry_price) * 100.0
        current_pnl_pct = round(((current_price - entry_price) / entry_price) * 100.0, 2)

        # 1. Base default stop: 5% initial risk
        initial_stop = round(entry_price * 0.95, 2)

        if gain_from_entry_pct >= 30.0:
            stage = "LOCK_STAGE_3_AGGRESSIVE_PROFIT"
            calculated_stop = round(effective_peak * 0.94, 2)
            desc_ar = f"🔒 قفل أرباح متقدم (المكاسب بلغت {gain_from_entry_pct:.1f}%): تم رفع الوقف إلى {calculated_stop:.2f} ج.م (94% من القمة)."
        elif gain_from_entry_pct >= 20.0:
            stage = "LOCK_STAGE_2_PROFIT_PROTECTION"
            calculated_stop = round(effective_peak * 0.92, 2)
            desc_ar = f"🔒 قفل أرباح جزئي (المكاسب بلغت {gain_from_entry_pct:.1f}%): تم رفع الوقف إلى {calculated_stop:.2f} ج.م (92% من القمة)."
        elif gain_from_entry_pct >= 10.0:
            stage = "LOCK_STAGE_1_BREAKEVEN"
            calculated_stop = round(entry_price, 2)
            desc_ar = f"🛡️ حماية نقطة الدخول (Breakeven): تم رفع الوقف إلى سعر الشراء {entry_price:.2f} ج.م لتأمين الصفقة بدون خسارة."
        else:
            stage = "INITIAL_RISK_BUFFER"
            calculated_stop = initial_stop
            desc_ar = f"وقف خسارة أولي عند {calculated_stop:.2f} ج.م (-5.0% من سعر الشراء)."

        # Irreversible ratchet guard
        existing_stop = current_stop if current_stop is not None and current_stop > 0 else 0.0
        final_trailing_stop = max(calculated_stop, existing_stop)

        is_stop_triggered = current_price <= final_trailing_stop
        locked_in_gain_pct = round(((final_trailing_stop - entry_price) / entry_price) * 100.0, 2) if final_trailing_stop > entry_price else 0.0

        return {
            "entry_price": round(entry_price, 2),
            "peak_price": round(effective_peak, 2),
            "current_price": round(current_price, 2),
            "current_pnl_pct": current_pnl_pct,
            "peak_gain_pct": round(gain_from_entry_pct, 2),
            "trailing_stop_price": round(final_trailing_stop, 2),
            "locked_in_profit_pct": locked_in_gain_pct,
            "is_stop_triggered": is_stop_triggered,
            "risk_stage": stage,
            "status_ar": desc_ar
        }

    # =========================================================================
    # 2. SECTOR CONCENTRATION GUARD (MAX 35% EXPOSURE)
    # =========================================================================

    @classmethod
    def evaluate_sector_concentration(
        cls,
        current_holdings: List[Dict[str, Any]],
        new_order: Dict[str, Any],
        total_portfolio_value_egp: Optional[float] = None,
        max_sector_limit_pct: float = MAX_SECTOR_CONCENTRATION_PCT
    ) -> Dict[str, Any]:
        """
        Enforces maximum 35% portfolio exposure to any single sector.
        Args:
            current_holdings: List of active holdings [{"ticker": "COMI.CA", "market_value_egp": 50000, "sector": "الخدمات المالية والبنوك"}]
            new_order: Proposed order {"ticker": "SWDY.CA", "order_value_egp": 40000, "sector": "الصناعة والمقاولات"}
        """
        new_ticker = new_order.get("ticker", "").upper().strip()
        if not new_ticker.endswith(".CA") and "." not in new_ticker:
            new_ticker = f"{new_ticker}.CA"

        # Determine target sector
        info = EGXUniverseLoader.get_stock_info(new_ticker) or {}
        target_sector = new_order.get("sector") or info.get("sector", "قطاعات متنوعة")
        new_order_val = float(new_order.get("order_value_egp", 0.0))

        # Calculate current sector exposures
        sector_totals: Dict[str, float] = {}
        total_holdings_val = 0.0

        for h in current_holdings:
            t = h.get("ticker", "").upper().strip()
            h_info = EGXUniverseLoader.get_stock_info(t) or {}
            sec = h.get("sector") or h_info.get("sector", "قطاعات متنوعة")
            val = float(h.get("market_value_egp") or (h.get("shares", 0) * h.get("current_price", 0)))
            sector_totals[sec] = sector_totals.get(sec, 0.0) + val
            total_holdings_val += val

        portfolio_base = total_portfolio_value_egp or max(total_holdings_val, 10000.0)
        current_sector_val = sector_totals.get(target_sector, 0.0)
        current_sector_pct = round((current_sector_val / portfolio_base) * 100.0, 2)

        # Simulated post-order exposure
        new_portfolio_val = max(portfolio_base, total_holdings_val + new_order_val)
        post_sector_val = current_sector_val + new_order_val
        post_sector_pct = round((post_sector_val / new_portfolio_val) * 100.0, 2)

        if post_sector_pct > max_sector_limit_pct:
            is_allowed = False
            reason_ar = (
                f"🚫 حظر تركيز قطاعي: تنفيذ الأمر سيرفع تعرض المحفظة لقطاع '{target_sector}' إلى {post_sector_pct:.1f}% "
                f"متجاوزاً الحد الأقصى المسموح به مؤسسياً ({max_sector_limit_pct:.1f}%). تم حجب الأمر لحماية المحفظة من مخاطر التركيز."
            )
        else:
            is_allowed = True
            reason_ar = (
                f"✅ نسبة التعرض لقطاع '{target_sector}' بعد التنفيذ ستكون {post_sector_pct:.1f}% "
                f"وهي ضمن الحدود الاستثمارية الآمنة (أقل من {max_sector_limit_pct:.1f}%)."
            )

        return {
            "target_ticker": new_ticker,
            "target_sector": target_sector,
            "order_value_egp": round(new_order_val, 2),
            "current_sector_exposure_pct": current_sector_pct,
            "post_order_sector_exposure_pct": post_sector_pct,
            "max_allowed_sector_limit_pct": max_sector_limit_pct,
            "is_allowed": is_allowed,
            "reason_ar": reason_ar
        }
