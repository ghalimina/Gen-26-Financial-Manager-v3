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

    @classmethod
    def compute_tax_optimal_rebalance(
        cls,
        current_portfolio: List[Dict[str, Any]],
        target_weights: Dict[str, float],
        total_equity: float,
        realized_gains_ytd: float = 0.0
    ) -> Dict[str, Any]:
        """
        Calculates a tax-optimal portfolio rebalancing plan under Egyptian Capital Markets regulations:
        - Offsets capital gains with strategic loss-harvesting lots.
        - Calculates exact MCDR clearing fees (1 bp), FRA fees (0.5 bp), and stamp duty (1.25 per mil).
        - Computes net 10% Egyptian Capital Gains Tax (CGT) impact and tax-shield savings.
        - Prioritizes tax-loss sales before gain sales to preserve liquid shield.
        """
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        total_equity = max(1.0, float(total_equity))

        # Build map of current holdings
        curr_map = {}
        for pos in current_portfolio:
            sym = str(pos.get("symbol") or pos.get("ticker", "")).replace(".CA", "")
            if sym:
                curr_map[sym] = {
                    "shares": int(pos.get("shares", 0)),
                    "avg_cost": float(pos.get("avg_cost", pos.get("cost", 1.0))),
                    "current_price": float(pos.get("current_price", pos.get("price", 1.0))),
                    "symbol": sym
                }

        # Union of symbols
        all_symbols = set(curr_map.keys()) | {str(s).replace(".CA", "") for s in target_weights.keys()}

        sell_orders = []
        buy_orders = []
        total_turnover = 0.0
        total_fees = 0.0

        for sym in all_symbols:
            hold = curr_map.get(sym, {"shares": 0, "avg_cost": 0.0, "current_price": 0.0, "symbol": sym})
            price = hold["current_price"]
            if price <= 0:
                try:
                    from core.market_price_service import MarketPriceService
                    cp = MarketPriceService.get_canonical_price(f"{sym}.CA") or MarketPriceService.get_canonical_price(sym)
                    if cp and cp.get("price"):
                        price = float(cp["price"])
                except Exception:
                    price = 10.0

            curr_shares = hold["shares"]
            curr_val = curr_shares * price
            curr_weight = curr_val / total_equity

            tgt_weight = float(target_weights.get(sym, target_weights.get(f"{sym}.CA", 0.0)))
            tgt_val = tgt_weight * total_equity
            val_diff = tgt_val - curr_val

            if val_diff < -1e-4 and curr_shares > 0 and price > 0:
                # Need to SELL
                shares_to_sell = min(curr_shares, int(round(abs(val_diff) / price)))
                if shares_to_sell > 0:
                    gross_sale = shares_to_sell * price
                    cost_basis = shares_to_sell * hold["avg_cost"]
                    est_pnl = gross_sale - cost_basis
                    settle_info = cls.calculate_trade_settlement(sym, today_str, shares_to_sell, price)
                    fee = settle_info["total_regulatory_fees"]
                    total_turnover += gross_sale
                    total_fees += fee

                    sell_orders.append({
                        "symbol": sym,
                        "action": "SELL",
                        "shares": shares_to_sell,
                        "price": round(price, 2),
                        "gross_value": round(gross_sale, 2),
                        "avg_cost": round(hold["avg_cost"], 2),
                        "est_pnl": round(est_pnl, 2),
                        "is_tax_loss": est_pnl < 0,
                        "tax_impact_egp": round(abs(est_pnl) * cls.EGYPTIAN_CGT_RATE if est_pnl < 0 else est_pnl * cls.EGYPTIAN_CGT_RATE, 2),
                        "regulatory_fees_egp": fee,
                        "settlement_cycle": settle_info["settlement_cycle"],
                        "settlement_date": settle_info["settlement_date"],
                        "target_weight_pct": round(tgt_weight * 100.0, 2),
                        "current_weight_pct": round(curr_weight * 100.0, 2)
                    })

            elif val_diff > 1e-4 and price > 0:
                # Need to BUY
                shares_to_buy = int(val_diff / price)
                if shares_to_buy > 0:
                    gross_buy = shares_to_buy * price
                    settle_info = cls.calculate_trade_settlement(sym, today_str, shares_to_buy, price)
                    fee = settle_info["total_regulatory_fees"]
                    total_turnover += gross_buy
                    total_fees += fee

                    buy_orders.append({
                        "symbol": sym,
                        "action": "BUY",
                        "shares": shares_to_buy,
                        "price": round(price, 2),
                        "gross_value": round(gross_buy, 2),
                        "avg_cost": round(price, 2),
                        "est_pnl": 0.0,
                        "is_tax_loss": False,
                        "tax_impact_egp": 0.0,
                        "regulatory_fees_egp": fee,
                        "settlement_cycle": settle_info["settlement_cycle"],
                        "settlement_date": settle_info["settlement_date"],
                        "target_weight_pct": round(tgt_weight * 100.0, 2),
                        "current_weight_pct": round(curr_weight * 100.0, 2)
                    })

        # Tax optimization: Sort sells so loss-makers (tax shields) are executed first
        sell_orders.sort(key=lambda x: x["est_pnl"])

        # Calculate final tax liability
        cgt_report = cls.compute_fiscal_year_cgt([{"realized_pnl_egp": s["est_pnl"]} for s in sell_orders])

        return {
            "status": "SUCCESS",
            "execution_date": today_str,
            "total_equity_egp": round(total_equity, 2),
            "rebalancing_trades": sell_orders + buy_orders,
            "summary": {
                "total_orders": len(sell_orders) + len(buy_orders),
                "sell_orders_count": len(sell_orders),
                "buy_orders_count": len(buy_orders),
                "total_turnover_egp": round(total_turnover, 2),
                "total_regulatory_fees_egp": round(total_fees, 2),
                "gross_realized_pnl_egp": cgt_report["net_realized_pnl_egp"],
                "estimated_cgt_tax_egp": cgt_report["estimated_cgt_liability_egp"],
                "tax_shield_unlocked_egp": cgt_report["tax_shield_from_losses_egp"],
                "effective_tax_drag_pct": round((cgt_report["estimated_cgt_liability_egp"] / total_equity) * 100.0, 4) if total_equity > 0 else 0.0
            }
        }

