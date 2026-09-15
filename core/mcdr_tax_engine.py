#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/mcdr_tax_engine.py — MCDR Clearing, Egyptian Tax & Tax-Loss Harvesting Engine
# Implements:
# 1. MCDR (مصر للمقاصة) T+0, T+1, T+2 Settlement & Custody Tracking.
# 2. Egyptian Capital Gains Tax (10% CGT) & Stamp Duty (ضريبة الدمغة).
# 3. Autonomous Tax-Loss Harvesting (جني الخسائر لتقليل الوعاء الضريبي).
# =============================================================================

import datetime
from typing import Dict, List, Any, Optional


class McdrTaxEngine:
    """
    Clearing settlement reconciliation and Egyptian Capital Gains Tax manager.
    """

    EGYPTIAN_CGT_RATE = 0.10      # 10% Capital Gains Tax
    STAMP_DUTY_RATE = 0.00125     # 0.125% (1.25 per mil) for applicable trades
    MCDR_CLEARING_FEE_RATE = 0.0001  # 1 bp MCDR fee
    FRA_FEE_RATE = 0.00005        # 0.5 bp Financial Regulatory Authority fee

    @classmethod
    def calculate_trade_settlement(
        cls,
        symbol: str,
        trade_date: str,
        shares: int,
        price: float,
        is_list_a: bool = True,
        is_same_day_trade: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates settlement date and regulatory fee schedule according to MCDR rules:
        - List A + T+0 flag: Settlement on Trade Date (T+0).
        - Standard EGX: Settlement on T+2.
        """
        t_date = datetime.datetime.strptime(trade_date, "%Y-%m-%d")

        if is_list_a and is_same_day_trade:
            settle_date = t_date
            cycle = "T+0"
        else:
            # Add 2 business days (skip Friday and Saturday in Egypt)
            days_added = 0
            curr = t_date
            while days_added < 2:
                curr += datetime.timedelta(days=1)
                if curr.weekday() not in [4, 5]:  # 4 = Friday, 5 = Saturday
                    days_added += 1
            settle_date = curr
            cycle = "T+2"

        gross_value = shares * price
        mcdr_fee = gross_value * cls.MCDR_CLEARING_FEE_RATE
        fra_fee = gross_value * cls.FRA_FEE_RATE
        stamp_duty = gross_value * cls.STAMP_DUTY_RATE

        return {
            "symbol": symbol,
            "trade_date": trade_date,
            "settlement_date": settle_date.strftime("%Y-%m-%d"),
            "settlement_cycle": cycle,
            "gross_value": round(gross_value, 2),
            "mcdr_clearing_fee": round(mcdr_fee, 2),
            "fra_regulatory_fee": round(fra_fee, 2),
            "stamp_duty": round(stamp_duty, 2),
            "total_regulatory_fees": round(mcdr_fee + fra_fee + stamp_duty, 2)
        }

    @classmethod
    def compute_fiscal_year_cgt(
        cls,
        realized_trades: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculates Egyptian 10% Capital Gains Tax liability:
        - Realized Gains offset by Realized Losses.
        - Net CGT payable = max(0, Net Realized Gain) * 10%.
        """
        total_gains = 0.0
        total_losses = 0.0

        for t in realized_trades:
            pnl = float(t.get("realized_pnl_egp", 0.0))
            if pnl > 0:
                total_gains += pnl
            else:
                total_losses += abs(pnl)

        net_gain = total_gains - total_losses
        cgt_payable = max(0.0, net_gain) * cls.EGYPTIAN_CGT_RATE

        return {
            "gross_realized_gains_egp": round(total_gains, 2),
            "gross_realized_losses_egp": round(total_losses, 2),
            "net_realized_pnl_egp": round(net_gain, 2),
            "cgt_rate_pct": cls.EGYPTIAN_CGT_RATE * 100.0,
            "estimated_cgt_liability_egp": round(cgt_payable, 2),
            "tax_shield_from_losses_egp": round(min(total_gains, total_losses) * cls.EGYPTIAN_CGT_RATE, 2)
        }

    @classmethod
    def scan_tax_loss_harvesting_opportunities(
        cls,
        current_holdings: List[Dict[str, Any]],
        realized_gains_ytd: float = 100000.0,
        loss_hurdle_pct: float = -4.0
    ) -> List[Dict[str, Any]]:
        """
        Scans portfolio for tax-loss harvesting candidates:
        - Identifies positions with unrealized loss exceeding hurdle.
        - Proposes selling to realize the loss and shield realized YTD gains.
        - Provides compliant substitute ticker to maintain market exposure.
        """
        # Substitute asset mapping for EGX (e.g. COMI <-> HRHO, FWRY <-> EFIH)
        SECTOR_SUBSTITUTES = {
            "COMI": "HRHO",
            "HRHO": "COMI",
            "FWRY": "EFIH",
            "EFIH": "FWRY",
            "ETEL": "ORWE",
            "SWDY": "EKHO"
        }

        recommendations = []
        for pos in current_holdings:
            sym = pos.get("symbol", "")
            cost = float(pos.get("avg_cost", 1.0))
            curr = float(pos.get("current_price", 1.0))
            shares = int(pos.get("shares", 0))

            unrealized_pct = ((curr - cost) / max(cost, 1e-4)) * 100.0
            if unrealized_pct <= loss_hurdle_pct and shares > 0:
                unrealized_loss_egp = abs((curr - cost) * shares)
                tax_savings = unrealized_loss_egp * cls.EGYPTIAN_CGT_RATE
                substitute = SECTOR_SUBSTITUTES.get(sym, "EGX30_ETF")

                recommendations.append({
                    "symbol": sym,
                    "shares_to_harvest": shares,
                    "current_price": curr,
                    "avg_cost": cost,
                    "unrealized_loss_pct": round(unrealized_pct, 2),
                    "harvestable_loss_egp": round(unrealized_loss_egp, 2),
                    "potential_tax_shield_egp": round(tax_savings, 2),
                    "recommended_substitute": substitute,
                    "rationale_ar": (
                        f"جني خسارة ضريبية لسهم {sym} (تراجع {unrealized_pct:.2f}%): "
                        f"يوفر درعاً ضريبياً قدره {tax_savings:.2f} ج.م مع إمكانية استبدال المركز مؤقتاً بسهم {substitute}."
                    )
                })

        recommendations.sort(key=lambda x: x["potential_tax_shield_egp"], reverse=True)
        return recommendations
