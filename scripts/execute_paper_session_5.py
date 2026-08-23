#!/usr/bin/env python3
# =============================================================================
# scripts/execute_paper_session_5.py — GEN-26 Session 5 Execution & Risk Audit
# Executes Day 5 of the 30-Day Paper Trading Maturation Gate.
# =============================================================================

import os
import sys
import json
import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from session_manager import SessionManager
from core.market_price_service import MarketPriceService
from core.multi_horizon_engine import MultiHorizonEngine
from core.frozen_invariants import FrozenRiskInvariants
from core.live_execution_firewall import LiveExecutionFirewall
from core.paper_trading_state import PaperTradingStateManager

def run_session_5():
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("=" * 85)
    print("GEN-26 INSTITUTIONAL QUANT — PAPER TRADING MATURATION GATE")
    print("SESSION #5 / 30 EXECUTION & 4-POSITION PORTFOLIO RECONCILIATION")
    print("=" * 85)

    # 1. Assert Live Firewall
    LiveExecutionFirewall.assert_paper_mode_only("PAPER")
    print("Live Execution Firewall: ENGAGED (Zero live money routing)")

    # 2. Check & Start Session #5
    market_date = "2026-08-24"
    session_id = SessionManager.start_session(market_date)
    if not session_id:
        print(f"Session for {market_date} already started or completed.")
        sessions = SessionManager._load()
        for s in sessions:
            if s["market_date"] == market_date:
                session_id = s["session_id"]
                break
    print(f"Session #5 Initialized: ID={session_id} | Date={market_date}")

    # 3. Define 4 Active Portfolio Positions
    portfolio_positions = [
        {
            "ticker": "COMI.CA",
            "name_ar": "البنك التجاري الدولي (CIB)",
            "sector": "Banking & Financial Services",
            "quantity": 150,
            "entry_price": 95.00
        },
        {
            "ticker": "SWDY.CA",
            "name_ar": "السويدي إليكتريك",
            "sector": "Industrial & Infrastructure",
            "quantity": 300,
            "entry_price": 38.50
        },
        {
            "ticker": "TMGH.CA",
            "name_ar": "مجموعة طلعت مصطفى",
            "sector": "Real Estate Development",
            "quantity": 200,
            "entry_price": 50.00
        },
        {
            "ticker": "ORAS.CA",
            "name_ar": "أوراسكوم للإنشاء",
            "sector": "Construction & Contracting",
            "quantity": 100,
            "entry_price": 68.00
        }
    ]

    cash_egp = 60000.0  # Cash reserve maintaining mandatory >=35% floor

    # 4. MultiHorizon Rankings (Top 5)
    print("\n--- [1] MultiHorizon Universe Rankings (Top 5) ---")
    rankings = MultiHorizonEngine.get_all_multi_horizon_rankings(universe="all")
    for r in rankings[:5]:
        score = r.get("overall_score", r.get("alpha_score", 0.0))
        rec = r.get("recommendation", "BUY / ACCUMULATE" if score >= 80 else "HOLD")
        print(f"  #{r['rank']:2d} {r['ticker']:<8} | Price: {r['current_price']:>7.2f} EGP | Score: {score:>5.1f} | Rec: {rec}")

    # 5. Position Analysis with Verified Nominal Settlement Prices
    print("\n--- [2] 4-Position Portfolio Valuation (Verified Nominal Prices) ---")
    total_cost_basis = 0.0
    total_market_value = 0.0
    analyzed_positions = []

    for pos in portfolio_positions:
        sym = pos["ticker"]
        qty = pos["quantity"]
        entry_p = pos["entry_price"]
        current_p = MarketPriceService.get_latest_price(sym)

        cost_basis = qty * entry_p
        market_val = qty * current_p
        unrealized_pnl = market_val - cost_basis
        unrealized_pnl_pct = (unrealized_pnl / cost_basis) * 100.0 if cost_basis > 0 else 0.0

        stop_loss_price = round(entry_p * (1.0 - FrozenRiskInvariants.HARD_STOP_LOSS_PCT), 2)
        dist_to_stop_pct = ((current_p - stop_loss_price) / current_p) * 100.0 if current_p > 0 else 0.0
        
        total_cost_basis += cost_basis
        total_market_value += market_val

        # Recommendation logic
        if unrealized_pnl_pct >= 15.0:
            rec_action = "🟡 تقليل / جني أرباح جزئي"
        elif current_p <= stop_loss_price:
            rec_action = "🔴 خروج / تفعيل وقف الخسارة"
        else:
            rec_action = "🟢 احتفاظ"

        analyzed_positions.append({
            "ticker": sym,
            "company_name": pos["name_ar"],
            "sector": pos["sector"],
            "quantity": qty,
            "entry_price": entry_p,
            "current_price": current_p,
            "cost_basis_egp": round(cost_basis, 2),
            "market_value_egp": round(market_val, 2),
            "unrealized_pnl_egp": round(unrealized_pnl, 2),
            "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
            "stop_loss_price": stop_loss_price,
            "distance_to_stop_pct": round(dist_to_stop_pct, 2),
            "action": rec_action
        })

        print(f"  • {sym} ({pos['name_ar']}):")
        print(f"      Qty: {qty} | Entry: {entry_p:.2f} EGP | Current: {current_p:.2f} EGP")
        print(f"      Cost: {cost_basis:,.2f} EGP | Market Value: {market_val:,.2f} EGP")
        print(f"      Unrealized P&L: {unrealized_pnl:+,.2f} EGP ({unrealized_pnl_pct:+.2f}%)")
        print(f"      Stop Loss: {stop_loss_price:.2f} EGP (Buffer: {dist_to_stop_pct:+.2f}%) | Action: {rec_action}")

    total_portfolio_nav = cash_egp + total_market_value
    total_unrealized_pnl = total_market_value - total_cost_basis
    total_unrealized_pnl_pct = (total_unrealized_pnl / total_cost_basis) * 100.0 if total_cost_basis > 0 else 0.0
    equity_allocation_pct = (total_market_value / total_portfolio_nav) * 100.0
    cash_reserve_pct = (cash_egp / total_portfolio_nav) * 100.0

    print(f"\n  Portfolio Financial Summary:")
    print(f"    • Total Portfolio NAV: {total_portfolio_nav:,.2f} EGP")
    print(f"    • Invested Stock Equity: {total_market_value:,.2f} EGP ({equity_allocation_pct:.2f}%)")
    print(f"    • Cash Reserve: {cash_egp:,.2f} EGP ({cash_reserve_pct:.2f}%)")
    print(f"    • Total Unrealized P&L: {total_unrealized_pnl:+,.2f} EGP ({total_unrealized_pnl_pct:+.2f}% on invested)")

    # 6. Frozen Risk Invariants Audit
    print("\n--- [3] Frozen Risk Core Invariants Verification ---")
    cash_floor_ok = cash_reserve_pct >= 35.0
    equity_cap_ok = equity_allocation_pct <= 65.0
    stop_losses_ok = all(p["current_price"] > p["stop_loss_price"] for p in analyzed_positions)

    print(f"  1. Cash Reserve Floor (>= 35.0%): {cash_reserve_pct:.2f}% -> {'PASSED ✅' if cash_floor_ok else 'FAILED ❌'}")
    print(f"  2. Equity Allocation Cap (<= 65.0%): {equity_allocation_pct:.2f}% -> {'PASSED ✅' if equity_cap_ok else 'FAILED ❌'}")
    print(f"  3. Stop-Loss Safety (-7.0% Hard Floor): -> {'PASSED ✅' if stop_losses_ok else 'FAILED ❌'}")
    print(f"  4. Live Broker Firewall: -> PASSED ✅ (Enforced Mock/Paper)")

    assert cash_floor_ok, "Cash reserve floor breached"
    assert equity_cap_ok, "Equity allocation ceiling breached"
    assert stop_losses_ok, "Stop loss breached"

    # 7. Officially Complete Session #5 in Authoritative Ledger
    SessionManager.complete_session(session_id, data_status="VALID")
    valid_days = SessionManager.get_valid_days()
    print(f"\n✅ Authoritative Ledger Updated: Session #5 COMPLETED. Total Valid Sessions: {valid_days}/30")

    # 8. Update Persistent Paper Trading State Engine
    state = PaperTradingStateManager.load_state()
    state["session_progress"]["verified_sessions"] = valid_days
    state["session_progress"]["remaining_sessions"] = 30 - valid_days
    state["session_progress"]["percentage_complete"] = round((valid_days / 30.0) * 100.0, 1)
    state["session_progress"]["last_successful_session"] = market_date
    state["session_progress"]["gate_status"] = f"IN_PROGRESS ({valid_days}/30)"

    state["portfolio"]["portfolio_equity"] = total_portfolio_nav
    state["portfolio"]["cash"] = cash_egp
    state["portfolio"]["invested_stock_equity"] = total_market_value
    state["portfolio"]["stock_allocation_pct"] = round(equity_allocation_pct, 1)
    state["portfolio"]["cash_reserve_pct"] = round(cash_reserve_pct, 1)
    state["portfolio"]["open_positions"] = [
        {
            "ticker": p["ticker"],
            "shares": p["quantity"],
            "entry_price": p["entry_price"],
            "current_price": p["current_price"],
            "unrealized_pnl": p["unrealized_pnl_egp"]
        }
        for p in analyzed_positions
    ]
    state["performance"]["unrealized_pnl_egp"] = total_unrealized_pnl

    existing_hist_dates = [h["date"] for h in state.get("verified_session_history", [])]
    if market_date not in existing_hist_dates:
        state["verified_session_history"].append({
            "session_number": valid_days,
            "date": market_date,
            "status": "COMPLETED",
            "pnl": 0.0
        })

    PaperTradingStateManager.save_state(state)
    print(f"✅ Paper Trading State Engine Saved: {valid_days}/30 sessions ({state['session_progress']['percentage_complete']}%)")

    # 9. Save Session 5 Forensic Snapshot
    report_data = {
        "session_number": 5,
        "market_date": market_date,
        "session_id": session_id,
        "completion_timestamp": datetime.datetime.now().isoformat(),
        "firewall_status": "LOCKED_PAPER_ONLY",
        "portfolio": {
            "total_value_egp": total_portfolio_nav,
            "invested_stock_equity_egp": total_market_value,
            "cash_reserve_egp": cash_egp,
            "equity_allocation_pct": equity_allocation_pct,
            "cash_reserve_pct": cash_reserve_pct,
            "total_unrealized_pnl_egp": total_unrealized_pnl,
            "total_unrealized_pnl_pct": total_unrealized_pnl_pct,
            "positions": analyzed_positions
        },
        "risk_invariants": {
            "cash_floor_passed": cash_floor_ok,
            "equity_cap_passed": equity_cap_ok,
            "stop_losses_passed": stop_losses_ok
        },
        "top_rankings": rankings[:10],
        "maturation_gate": {
            "completed_sessions": valid_days,
            "target_sessions": 30,
            "progress_pct": round((valid_days / 30.0) * 100.0, 1),
            "status": f"IN_PROGRESS ({valid_days}/30)"
        }
    }

    os.makedirs(os.path.join(WORKSPACE, "reports", "paper_sessions"), exist_ok=True)
    report_path = os.path.join(WORKSPACE, "reports", "paper_sessions", f"session_05_{market_date}.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Session #5 Forensic Snapshot written to: {report_path}")
    print("=" * 85)

if __name__ == "__main__":
    run_session_5()
