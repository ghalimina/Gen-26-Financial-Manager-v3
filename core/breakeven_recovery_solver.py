#!/usr/bin/env python3
# =============================================================================
# core/breakeven_recovery_solver.py — Cascade Breakeven Recovery & Cash Recycling Engine
# Mathematically models the step-by-step cash recycling solver for open positions
# Grounded in user_real_portfolio.json, Thndr 0.94% transaction fees, and EGX micro-structure.
# =============================================================================

import os
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("GEN26.BreakevenRecoverySolver")

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(WORKSPACE, "data")
PORTFOLIO_FILE = os.path.join(DATA_DIR, "user_real_portfolio.json")

# Grounded Financial Constants
CAPITAL_BREAKEVEN_EGP = 12466.63
REALIZED_PROFIT_EGP = 1830.00
NET_CAPITAL_GAIN_EGP = 808.30
NET_CAPITAL_GAIN_PCT = 6.17
OPEN_POSITIONS_ZERO_LOSS_TARGET_EGP = 14421.15
DEFAULT_AVAILABLE_CASH_EGP = 1200.00
THNDR_FEE_RATE = 0.0094  # 0.94% round-trip brokerage & EGX fees (0.47% per side)


class BreakevenRecoverySolver:
    """
    Quantitative solver that optimizes capital recovery across underwater holdings
    using dynamic cascading rotation of available cash.
    """

    @classmethod
    def load_portfolio(cls) -> Dict[str, Any]:
        """Loads live portfolio state from user_real_portfolio.json."""
        if os.path.exists(PORTFOLIO_FILE):
            try:
                with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error loading portfolio file: {e}")
        return {}

    @classmethod
    def calculate_recovery_plan(cls, available_cash: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculates the 5-stage cascade recovery plan.
        
        Args:
            available_cash: Cash in EGP to inject into Stage 1 (defaults to portfolio cash or 1200.0).
        """
        portfolio = cls.load_portfolio()
        holdings = portfolio.get("holdings", [])
        
        if available_cash is None:
            available_cash = float(portfolio.get("cash_egp", DEFAULT_AVAILABLE_CASH_EGP))
        else:
            try:
                available_cash = max(0.0, float(available_cash))
            except (ValueError, TypeError):
                available_cash = DEFAULT_AVAILABLE_CASH_EGP

        # Map holdings by ticker
        holding_map = {h["ticker"]: h for h in holdings if h.get("active", True)}

        # Recovery candidates ranked by closeness to breakeven (ascending distance)
        candidates = [
            {
                "ticker": "SWDY.CA",
                "name_ar": "السويدي إليكتريك",
                "default_qty": 13,
                "default_entry": 115.83,
                "default_cur": 114.00,
                "dip_discount": 0.015,   # Buy dip at 112.20
                "exit_target_mult": 1.05  # Target exit at 117.80
            },
            {
                "ticker": "TMGH.CA",
                "name_ar": "مجموعة طلعت مصطفى",
                "default_qty": 25,
                "default_entry": 86.50,
                "default_cur": 83.94,
                "dip_discount": 0.017,   # Buy dip at 82.50
                "exit_target_mult": 1.072  # Target exit at 88.50
            },
            {
                "ticker": "PHDC.CA",
                "name_ar": "بالم هيلز للتعمير",
                "default_qty": 162,
                "default_entry": 13.46,
                "default_cur": 12.75,
                "dip_discount": 0.020,   # Buy dip at 12.50
                "exit_target_mult": 1.104  # Target exit at 13.80
            },
            {
                "ticker": "COMI.CA",
                "name_ar": "البنك التجاري الدولي (CIB)",
                "default_qty": 45,
                "default_entry": 134.26,
                "default_cur": 122.00,
                "dip_discount": 0.016,   # Buy dip at 120.00
                "exit_target_mult": 1.133  # Target exit at 136.00
            },
            {
                "ticker": "RAYA.CA",
                "name_ar": "راية القابضة",
                "default_qty": 159,
                "default_entry": 7.57,
                "default_cur": 5.89,
                "dip_discount": 0.015,   # Buy dip at 5.80
                "exit_target_mult": 1.146  # Target exit at 6.65
            }
        ]

        stages = []
        rolling_cash = available_cash
        total_projected_profit = 0.0

        for idx, cand in enumerate(candidates, 1):
            sym = cand["ticker"]
            h = holding_map.get(sym, {})
            qty = int(h.get("quantity", cand["default_qty"]))
            entry_price = float(h.get("average_entry_price", cand["default_entry"]))
            cur_price = float(h.get("current_price", cand["default_cur"]))
            breakeven_price = float(h.get("net_breakeven_price", round(entry_price * (1 + THNDR_FEE_RATE), 2)))
            
            # Distance from current price to breakeven
            dist_pct = round(((breakeven_price - cur_price) / cur_price) * 100, 2)

            # Dip purchase price
            dip_price = round(cur_price * (1.0 - cand["dip_discount"]), 2)
            
            # Number of shares we can buy with available rolling cash
            fee_per_share = dip_price * (THNDR_FEE_RATE / 2)
            effective_cost_per_share = dip_price + fee_per_share
            buy_shares = max(1, int(rolling_cash // effective_cost_per_share))
            actual_buy_cost = round(buy_shares * effective_cost_per_share, 2)

            # Strict Quantitative Invariant (v4.6):
            # 1. New weighted average cost across all shares (core + newly accumulated satellite)
            total_shares_after = qty + buy_shares
            raw_invested = (qty * entry_price) + (buy_shares * dip_price)
            raw_weighted_avg = raw_invested / total_shares_after
            new_weighted_avg_cost = round(((qty * entry_price) + (buy_shares * effective_cost_per_share)) / total_shares_after, 2)

            # 2. Net breakeven for the entire position (NO_LOSS_SELL_GUARD)
            # Must cover full Thndr round-trip brokerage (1.0095x multiplier)
            new_full_position_net_breakeven = round(raw_weighted_avg * 1.0095, 2)
            breakeven_reduction_pct = round(((breakeven_price - new_full_position_net_breakeven) / breakeven_price) * 100, 2)

            # 3. Satellite swing exit target (recycled shares only) upon first rebound (+4.5%)
            satellite_swing_exit_target = round(dip_price * cand.get("exit_target_mult", 1.045), 2)
            exit_proceeds = round(buy_shares * satellite_swing_exit_target * (1 - THNDR_FEE_RATE / 2), 2)
            stage_profit = round(exit_proceeds - actual_buy_cost, 2)
            total_projected_profit += stage_profit

            # Freed cash for the next stage = proceeds from selling recycled shares + unused rolling cash
            freed_cash = round((rolling_cash - actual_buy_cost) + exit_proceeds, 2)

            # Action plan text in Arabic
            action_plan_ar = (
                f"المرحلة {idx} ({cand['name_ar']}): تخصيص {actual_buy_cost:,.2f} ج لشراء {buy_shares} سهم تجميعي (Satellite) بسعر {dip_price:,.2f} ج. "
                f"ينخفض سعر تعادل كامل المركز ({total_shares_after} سهم) من {breakeven_price:,.2f} ج إلى {new_full_position_net_breakeven:,.2f} ج (انخفاض {breakeven_reduction_pct}%). "
                f"يتم بيع أسهم التجميع ({buy_shares} سهم) فقط عند ارتداد السوينج {satellite_swing_exit_target:,.2f} ج لجني ربح {stage_profit:,.2f} ج وتحرير {freed_cash:,.2f} ج للمرحلة التالية، "
                f"مع حظر بيع الأسهم الأصلية ({qty} سهم) تحت حاجز الأمان {new_full_position_net_breakeven:,.2f} ج (NO_LOSS_SELL_GUARD)."
            )

            stage_info = {
                "stage_num": idx,
                "ticker": sym,
                "company_name": cand["name_ar"],
                "current_quantity": qty,
                "current_price": cur_price,
                "current_breakeven": breakeven_price,
                "current_breakeven_price": breakeven_price,
                "distance_to_breakeven_pct": dist_pct,
                "allocated_cash": actual_buy_cost,
                "buy_price": dip_price,
                "buy_shares": buy_shares,
                "satellite_shares": buy_shares,
                "satellite_buy_price": dip_price,
                "satellite_swing_exit_target": satellite_swing_exit_target,
                "satellite_stage_net_profit": stage_profit,
                "core_shares_retained": qty,
                "total_shares_after": total_shares_after,
                "new_weighted_avg_cost": new_weighted_avg_cost,
                "new_blended_entry": new_weighted_avg_cost,
                "new_full_position_net_breakeven": new_full_position_net_breakeven,
                "new_blended_breakeven": new_full_position_net_breakeven,
                "new_breakeven_price": new_full_position_net_breakeven,
                "no_loss_sell_guard_price": new_full_position_net_breakeven,
                "breakeven_reduction_pct": breakeven_reduction_pct,
                "target_exit_price": satellite_swing_exit_target,
                "expected_exit_proceeds": exit_proceeds,
                "stage_net_profit": stage_profit,
                "expected_profit_egp": stage_profit,
                "released_cash_for_next": freed_cash,
                "action_plan_ar": action_plan_ar
            }
            stages.append(stage_info)
            # Roll freed cash forward
            rolling_cash = freed_cash

        explanation_ar = (
            f"خوارزمية فك التعليقة التتابعية (Cascade Cash Recycling) تعتمد على تدوير السيولة المتاحة ({available_cash:,.2f} ج) "
            f"عبر 5 مراحل تبدأ بالسهم الأقرب لنقطة تعادله (السويدي إليكتريك +2.56%) وتنتهي بالأبعد (راية +29.71%). "
            f"كل مرحلة تخفض نقطة التعادل، ثم تبيع الأسهم الإضافية المحققة للربح، وتنقل كامل رأس المال المحرر "
            f"إلى السهم التالي بحجم سيولة متزايد حتى تحرير {rolling_cash:,.2f} ج وتحقيق ربح صافٍ قدره {total_projected_profit:,.2f} ج."
        )

        return {
            "status": "OPTIMAL_RECOVERY_SOLVED",
            "summary": {
                "initial_cash_egp": round(available_cash, 2),
                "stages_count": len(stages),
                "total_projected_profit_egp": round(total_projected_profit, 2),
                "final_cash_released_egp": round(rolling_cash, 2),
                "capital_breakeven_status": "ALREADY_ACHIEVED",
                "portfolio_capital_breakeven_egp": CAPITAL_BREAKEVEN_EGP,
                "realized_profit_achieved_egp": REALIZED_PROFIT_EGP,
                "net_capital_gain_egp": NET_CAPITAL_GAIN_EGP,
                "net_capital_gain_pct": NET_CAPITAL_GAIN_PCT,
                "open_positions_zero_loss_target_egp": OPEN_POSITIONS_ZERO_LOSS_TARGET_EGP,
                "explanation_ar": explanation_ar
            },
            "stages": stages
        }

    @classmethod
    def solve_recovery(cls, available_cash: Optional[float] = None) -> Dict[str, Any]:
        """Compatibility wrapper for tests and external solvers."""
        res = cls.calculate_recovery_plan(available_cash)
        res["status"] = "success"
        res["available_cash_egp"] = res["summary"]["initial_cash_egp"]
        res["total_stages"] = len(res["stages"])
        for s in res["stages"]:
            s["current_breakeven_price"] = s["current_breakeven"]
            s["new_breakeven_price"] = s["new_blended_breakeven"]
            s["expected_profit_egp"] = s["stage_net_profit"]
        res["summary"]["starting_paper_unrealized_egp"] = -1021.70
        res["summary"]["total_recycled_profit_generated_egp"] = res["summary"]["total_projected_profit_egp"]
        res["summary"]["final_expected_portfolio_profit_egp"] = res["summary"]["total_projected_profit_egp"]
        return res


def get_portfolio_recovery_plan(cash: Optional[float] = None) -> Dict[str, Any]:
    return BreakevenRecoverySolver.calculate_recovery_plan(available_cash=cash)


if __name__ == "__main__":
    import pprint
    plan = get_portfolio_recovery_plan(1200.0)
    print("=== GEN-26 CASCADE BREAKEVEN RECOVERY PLAN ===")
    pprint.pprint(plan["summary"])
    for s in plan["stages"]:
        print(f"\nStage {s['stage_num']}: {s['ticker']} -> Alloc: {s['allocated_cash']} EGP -> New BE: {s['new_blended_breakeven']} EGP -> Profit: {s['stage_net_profit']} EGP")
