#!/usr/bin/env python3
# =============================================================================
# core/tax_margin_manager.py — GEN-26 Tax-Loss Harvesting & Margin Cost Engine
# Institutional Portfolio Accounting Realism:
# 1. Overnight Margin Interest Calculator (EGX standard: CBE Lending + 2.0%).
# 2. Capital Gains Tax Estimator (Egyptian Equities 10% Capital Gains Tax Law).
# 3. Automated Tax-Loss Harvesting Advisor (Offsets realized gains before year-end).
# 4. Comprehensive Cost Realism & Net-of-Tax Performance Auditing.
# =============================================================================

import os
import sys
import json
import datetime
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)


class TaxMarginManager:
    """
    Institutional Tax Harvesting and Margin Financing Cost Manager for Egyptian Equities.
    """

    DEFAULT_MARGIN_SPREAD_PCT = 2.00  # Spread above CBE Corridor Lending Rate
    EGX_CAPITAL_GAINS_TAX_RATE = 0.10  # 10% Capital Gains Tax rate for resident portfolios

    @classmethod
    def calculate_margin_financing_cost(
        cls,
        borrowed_capital_egp: float,
        days_held: int = 1,
        cbe_lending_rate_pct: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculates accrued overnight margin financing interest:
        Cost = Borrowed_Amount * ((CBE_Lending + Spread) / 365) * Days
        """
        if borrowed_capital_egp <= 0 or days_held <= 0:
            return {
                "borrowed_capital_egp": 0.0,
                "days_held": days_held,
                "margin_interest_cost_egp": 0.0,
                "annual_margin_rate_pct": 0.0,
                "daily_cost_egp": 0.0
            }

        from core.macro_intelligence_engine import MacroIntelligenceEngine
        macro = MacroIntelligenceEngine.load_macro_state()
        cbe_rate = cbe_lending_rate_pct or (macro.get("cbe_corridor_rate_pct", 19.25) + 1.0)
        annual_rate = cbe_rate + cls.DEFAULT_MARGIN_SPREAD_PCT

        daily_rate = (annual_rate / 100.0) / 365.0
        total_interest = round(borrowed_capital_egp * daily_rate * days_held, 2)
        daily_cost = round(borrowed_capital_egp * daily_rate, 2)

        return {
            "borrowed_capital_egp": borrowed_capital_egp,
            "days_held": days_held,
            "annual_margin_rate_pct": round(annual_rate, 2),
            "margin_interest_cost_egp": total_interest,
            "daily_cost_egp": daily_cost,
            "rate_breakdown": f"CBE Lending ({cbe_rate:.2f}%) + Broker Spread ({cls.DEFAULT_MARGIN_SPREAD_PCT:.2f}%)"
        }

    @classmethod
    def evaluate_tax_loss_harvesting(
        cls,
        realized_gains_ytd_egp: float = 120_000.0,
        open_positions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Scans portfolio positions to identify loss-harvesting opportunities that offset taxable gains.
        """
        if open_positions is None:
            open_positions = [
                {"ticker": "CCAP.CA", "shares": 10_000, "entry_price": 6.10, "current_price": 5.60, "unrealized_pnl_egp": -5000.0},
                {"ticker": "BTFH.CA", "shares": 20_000, "entry_price": 3.25, "current_price": 2.98, "unrealized_pnl_egp": -5400.0},
                {"ticker": "COMI.CA", "shares": 500, "entry_price": 135.0, "current_price": 138.8, "unrealized_pnl_egp": 1900.0}
            ]

        taxable_gains_current = max(realized_gains_ytd_egp, 0.0)
        current_tax_liability_egp = round(taxable_gains_current * cls.EGX_CAPITAL_GAINS_TAX_RATE, 2)

        candidates = []
        total_harvestable_loss = 0.0

        for pos in open_positions:
            unrealized = pos.get("unrealized_pnl_egp", 0.0)
            if unrealized < -500.0:
                loss_amount = abs(unrealized)
                potential_tax_saving = round(loss_amount * cls.EGX_CAPITAL_GAINS_TAX_RATE, 2)
                candidates.append({
                    "ticker": pos.get("ticker"),
                    "shares": pos.get("shares"),
                    "unrealized_loss_egp": loss_amount,
                    "potential_tax_saving_egp": potential_tax_saving,
                    "action_ar": "حصاد ضريبي مقترح (بيع المركز لتخفيض الوعاء الضريبي ثم إعادة الشراء بعد 30 يوماً)"
                })
                total_harvestable_loss += loss_amount

        total_tax_savings = round(min(total_harvestable_loss, taxable_gains_current) * cls.EGX_CAPITAL_GAINS_TAX_RATE, 2)
        net_tax_liability = max(current_tax_liability_egp - total_tax_savings, 0.0)

        return {
            "status": "TAX_HARVESTING_EVALUATED",
            "tax_rate_pct": round(cls.EGX_CAPITAL_GAINS_TAX_RATE * 100.0, 1),
            "realized_gains_ytd_egp": realized_gains_ytd_egp,
            "current_tax_liability_egp": current_tax_liability_egp,
            "harvesting_candidates": candidates,
            "total_harvestable_loss_egp": round(total_harvestable_loss, 2),
            "potential_tax_savings_egp": total_tax_savings,
            "net_projected_tax_liability_egp": net_tax_liability,
            "recommendation_ar": (
                f"💡 فرصة توفير ضريبي: تسييل الخسائر غير المحققة يتيح توفير حتى {total_tax_savings:,.2f} ج.م من ضريبة الأرباح الرأسمالية."
                if total_tax_savings > 0 else
                "لا توجد خسائر كافية تستدعي الحصاد الضريبي حالياً."
            )
        }


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    m_cost = TaxMarginManager.calculate_margin_financing_cost(250_000, days_held=7)
    print("Margin Financing Cost (7 Days on 250,000 EGP):")
    print(json.dumps(m_cost, ensure_ascii=False, indent=2))

    t_harvest = TaxMarginManager.evaluate_tax_loss_harvesting()
    print("\nTax Loss Harvesting Evaluation:")
    print(json.dumps(t_harvest, ensure_ascii=False, indent=2))
