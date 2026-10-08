#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/egx_trading_rules_engine.py — EGX Trading Mechanics & Regulatory Execution Guard
# Enforces the 15 Institutional Egyptian Exchange Rules:
# 1. Circuit Breakers (Limit Up / Limit Down price ceilings and floors).
# 2. Settlement Tiers (T+0 Same Day, T+1 Next Day, T+2 Standard).
# 3. Margin Eligibility (FRA List A 80% Margin vs Non-Margin List B).
# 4. Net Profit Friction & 10% Egyptian Capital Gains Tax (CGT) Calculator.
# 5. Market Impact & ADV Order Sizing Safeguard (Max 10% ADV per session).
# =============================================================================

import os
import sys
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.market_price_service import MarketPriceService


class EGXTradingRulesEngine:
    """
    Authoritative institutional trading rules and execution protection guard
    for Egyptian Stock Exchange (EGX) equities.
    """

    # Top EGX30 Blue-Chips subject to wide ±20.0% circuit breaker bands
    EGX30_WIDE_BAND_CONSTITUENTS = {
        "COMI.CA", "SWDY.CA", "TMGH.CA", "EKHO.CA", "ETEL.CA", "ABUK.CA",
        "MFPC.CA", "FWRY.CA", "EFIH.CA", "HRHO.CA", "EAST.CA", "ORAS.CA",
        "EGAL.CA", "JUFO.CA", "GBCO.CA", "AUTO.CA", "MASR.CA", "MNHD.CA",
        "PHDC.CA", "HELI.CA", "AMOC.CA", "SKPC.CA", "ESRS.CA", "ADIB.CA",
        "CICH.CA", "EMFD.CA", "ORHD.CA", "BTFH.CA", "ISPH.CA", "DOMT.CA"
    }

    # FRA Margin List A Equities (Permitted for intraday T+0 trading and up to 80% margin financing)
    MARGIN_LIST_A_T0_EQUITIES = {
        "COMI.CA", "SWDY.CA", "TMGH.CA", "EKHO.CA", "ETEL.CA", "ABUK.CA",
        "MFPC.CA", "FWRY.CA", "EFIH.CA", "HRHO.CA", "EAST.CA", "ORAS.CA",
        "EGAL.CA", "JUFO.CA", "AUTO.CA", "MASR.CA", "PHDC.CA", "HELI.CA",
        "AMOC.CA", "SKPC.CA", "ADIB.CA", "CICH.CA", "EMFD.CA", "BTFH.CA",
        "ISPH.CA", "DOMT.CA", "RAYA.CA", "CCAP.CA", "DSCW.CA", "POUL.CA"
    }

    # T+1 Settlement Equities
    SETTLEMENT_T1_EQUITIES = {
        "OLFI.CA", "PRDC.CA", "QNBE.CA", "MILS.CA", "SCFM.CA", "CEFM.CA",
        "UEFM.CA", "WCDF.CA", "ZEOT.CA", "FERT.CA", "INEG.CA", "NEDA.CA",
        "ACAMD.CA", "BINV.CA", "ORWE.CA", "OCDI.CA", "CLHO.CA", "ALCN.CA"
    }

    # Default Egyptian Exchange transaction friction parameters (SSoT Thndr + EGX + MCDR)
    ROUNDTRIP_FRICTION_RATE = 0.0094  # 0.94% (Brokerage + EGX/MCDR/Guarantee/FRA fees)
    CAPITAL_GAINS_TAX_RATE = 0.10     # 10% Egyptian CGT on net realized capital gains

    # =========================================================================
    # 1. CIRCUIT BREAKERS (LIMIT UP / LIMIT DOWN)
    # =========================================================================

    @classmethod
    def evaluate_price_limits(
        cls,
        ticker: str,
        current_price: float,
        prev_close: float
    ) -> Dict[str, Any]:
        """
        Evaluates EGX price limits and circuit breakers.
        - Wide-band equities (EGX30): ±20% limit band (threshold: ±19.8%).
        - Standard equities: ±10% limit band (threshold: ±9.8%).
        """
        sym_clean = ticker.upper().strip()
        if not sym_clean.endswith(".CA") and "." not in sym_clean:
            sym_clean = f"{sym_clean}.CA"

        if prev_close <= 0 or current_price <= 0:
            return {
                "ticker": sym_clean,
                "can_buy": True,
                "can_sell": True,
                "status": "NORMAL_TRADING",
                "limit_type": "NONE",
                "pct_change": 0.0,
                "max_limit_pct": 20.0 if sym_clean in cls.EGX30_WIDE_BAND_CONSTITUENTS else 10.0,
                "reason_ar": "بيانات الأسعار الأولية غير متوفرة أو مستقرة",
                "upper_limit_price": round(current_price * 1.20, 2),
                "lower_limit_price": round(current_price * 0.80, 2)
            }

        is_wide_band = sym_clean in cls.EGX30_WIDE_BAND_CONSTITUENTS
        max_allowed_band = 20.0 if is_wide_band else 10.0
        trigger_threshold = 19.8 if is_wide_band else 9.8

        pct_change = round(((current_price - prev_close) / prev_close) * 100.0, 2)
        upper_limit = round(prev_close * (1.0 + (max_allowed_band / 100.0)), 2)
        lower_limit = round(prev_close * (1.0 - (max_allowed_band / 100.0)), 2)

        if pct_change >= trigger_threshold:
            return {
                "ticker": sym_clean,
                "can_buy": False,
                "can_sell": True,
                "status": "LIMIT_UP",
                "limit_type": "LIMIT_UP",
                "pct_change": pct_change,
                "max_limit_pct": max_allowed_band,
                "reason_ar": "السهم عند الحد الأقصى للصعود (Limit Up) - لا توجد عروض بيع",
                "upper_limit_price": upper_limit,
                "lower_limit_price": lower_limit
            }
        elif pct_change <= -trigger_threshold:
            return {
                "ticker": sym_clean,
                "can_buy": True,
                "can_sell": False,
                "status": "LIMIT_DOWN",
                "limit_type": "LIMIT_DOWN",
                "pct_change": pct_change,
                "max_limit_pct": max_allowed_band,
                "reason_ar": "السهم عند الحد الأدنى (Limit Down) - لا توجد طلبات شراء",
                "upper_limit_price": upper_limit,
                "lower_limit_price": lower_limit
            }
        else:
            return {
                "ticker": sym_clean,
                "can_buy": True,
                "can_sell": True,
                "status": "NORMAL_TRADING",
                "limit_type": "NONE",
                "pct_change": pct_change,
                "max_limit_pct": max_allowed_band,
                "reason_ar": "تداول حر طبيعي ضمن الحدود السعرية المسموحة",
                "upper_limit_price": upper_limit,
                "lower_limit_price": lower_limit
            }

    # =========================================================================
    # 2. SETTLEMENT & MARGIN TIERS
    # =========================================================================

    @classmethod
    def get_settlement_and_margin_tier(cls, ticker: str) -> Dict[str, Any]:
        """
        Determines the settlement cycle (T+0, T+1, T+2) and FRA margin eligibility.
        """
        sym_clean = ticker.upper().strip()
        if not sym_clean.endswith(".CA") and "." not in sym_clean:
            sym_clean = f"{sym_clean}.CA"

        if sym_clean in cls.MARGIN_LIST_A_T0_EQUITIES:
            settlement_type = "T0_SAME_DAY"
            margin_tier = "MARGIN_LIST_A"
            max_margin_ratio_pct = 80.0
            description_ar = "سهم مؤهل للتداول في ذات الجلسة (T+0) وقائمة الشراء بالهامش (أ) حتى 80%"
            is_t0_eligible = True
            is_marginable = True
        elif sym_clean in cls.SETTLEMENT_T1_EQUITIES:
            settlement_type = "T1_NEXT_DAY"
            margin_tier = "MARGIN_LIST_B"
            max_margin_ratio_pct = 50.0
            description_ar = "سهم تسوية اليوم التالي (T+1) وقائمة الهامش المتحفظة (ب) حتى 50%"
            is_t0_eligible = False
            is_marginable = True
        else:
            settlement_type = "T2_REGULAR"
            margin_tier = "NON_MARGIN_LIST_B"
            max_margin_ratio_pct = 0.0
            description_ar = "سهم تسوية قياسية (T+2) غير مؤهل للتداول الهامشي أو ذات الجلسة"
            is_t0_eligible = False
            is_marginable = False

        return {
            "ticker": sym_clean,
            "settlement_type": settlement_type,
            "margin_eligibility": margin_tier,
            "max_margin_ratio_pct": max_margin_ratio_pct,
            "is_t0_eligible": is_t0_eligible,
            "is_marginable": is_marginable,
            "description_ar": description_ar
        }

    # =========================================================================
    # 3. NET PROFIT FRICTION & 10% CGT TAX CALCULATOR
    # =========================================================================

    @classmethod
    def calculate_net_proceeds(
        cls,
        gross_pnl: float,
        holding_days: int = 1,
        order_turnover_egp: float = 0.0,
        is_resident: bool = True
    ) -> Dict[str, Any]:
        """
        Calculates net realized proceeds after automatically deducting:
        1. ~0.35% roundtrip brokerage, EGX, MCDR, and FRA fees.
        2. 10% Egyptian Capital Gains Tax (CGT) on positive net realized gains.
        """
        turnover = max(order_turnover_egp, abs(gross_pnl) * 5.0, 1000.0)
        friction_fees = round(turnover * cls.ROUNDTRIP_FRICTION_RATE, 2)

        net_before_tax = round(gross_pnl - friction_fees, 2)

        if net_before_tax > 0 and is_resident:
            cgt_tax = round(net_before_tax * cls.CAPITAL_GAINS_TAX_RATE, 2)
            net_proceeds = round(net_before_tax - cgt_tax, 2)
            tax_rate_applied_pct = 10.0
        else:
            cgt_tax = 0.0
            net_proceeds = net_before_tax
            tax_rate_applied_pct = 0.0

        return {
            "gross_pnl_egp": round(gross_pnl, 2),
            "order_turnover_egp": round(turnover, 2),
            "friction_fees_egp": friction_fees,
            "roundtrip_fee_rate_pct": round(cls.ROUNDTRIP_FRICTION_RATE * 100.0, 2),
            "cgt_tax_egp": cgt_tax,
            "cgt_tax_rate_pct": tax_rate_applied_pct,
            "net_proceeds_egp": net_proceeds,
            "is_profitable_net": net_proceeds > 0,
            "holding_days": max(holding_days, 1),
            "description_ar": (
                f"إجمالي الأرباح {gross_pnl:+,.2f} ج.م | عمولات تداول ومقاصة: {friction_fees:,.2f} ج.م | "
                f"ضريبة أرباح رأسمالية (10%): {cgt_tax:,.2f} ج.م | صافي العائد الفعلي: {net_proceeds:+,.2f} ج.م"
            )
        }

    # =========================================================================
    # 4. MARKET IMPACT & ADV ORDER SIZING SAFEGUARD
    # =========================================================================

    @classmethod
    def check_market_impact(
        cls,
        ticker: str,
        order_value_egp: float
    ) -> Dict[str, Any]:
        """
        Validates order size against 20-day Average Daily Volume (ADV).
        If order exceeds 10% of ADV, raises a market impact warning and recommends
        splitting the order across 2-3 sessions to prevent severe execution slippage.
        """
        sym_clean = ticker.upper().strip()
        if not sym_clean.endswith(".CA") and "." not in sym_clean:
            sym_clean = f"{sym_clean}.CA"

        from core.institutional_flow_engine import InstitutionalFlowEngine
        adv_benchmarks = InstitutionalFlowEngine._ADV_BENCHMARKS.get(sym_clean, {})
        adv20_turnover = float(adv_benchmarks.get("adv20_turnover_egp", 15_000_000.0))

        if adv20_turnover <= 0:
            adv20_turnover = 15_000_000.0

        adv_ratio_pct = round((order_value_egp / adv20_turnover) * 100.0, 2)

        if adv_ratio_pct > 10.0:
            is_safe = False
            recommended_chunks = 3 if adv_ratio_pct > 25.0 else 2
            chunk_size = round(order_value_egp / recommended_chunks, 2)
            warning_ar = (
                f"⚠️ تحذير تأثير السوق: حجم الأمر ({order_value_egp:,.0f} ج.م) يمثل {adv_ratio_pct:.1f}% "
                f"من متوسط السيولة اليومية ({adv20_turnover:,.0f} ج.م). يوصى بتجزئة التنفيذ على {recommended_chunks} جلسات "
                f"بمتوسط {chunk_size:,.0f} ج.م لكل جلسة لتفادي الانزلاق السعري."
            )
        else:
            is_safe = True
            recommended_chunks = 1
            chunk_size = round(order_value_egp, 2)
            warning_ar = None

        return {
            "ticker": sym_clean,
            "order_value_egp": round(order_value_egp, 2),
            "adv20_turnover_egp": round(adv20_turnover, 2),
            "adv_ratio_pct": adv_ratio_pct,
            "is_safe": is_safe,
            "recommended_chunks": recommended_chunks,
            "recommended_chunk_size_egp": chunk_size,
            "warning_ar": warning_ar
        }
