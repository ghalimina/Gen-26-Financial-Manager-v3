#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/intraday_sniper_alerts.py
=============================================================================
GEN-26 v4.1 Intraday Sniper Dip-Buy & Breakeven Profit Alert Engine
=============================================================================
Monitors real-time Egyptian Stock Exchange (EGX) prices against user portfolio
holdings and top market opportunities to trigger instant high-precision alerts:
1. 🟢 SNIPER_DIP_BUY_ALERT: Fires when price reaches the predicted accumulation
   floor (drop floor), with exact suggested shares and new lowered average cost.
2. 🎯 BREAKEVEN_PROFIT_ALERT: Fires when price crosses net breakeven price (+0.94%
   Thndr round-trip fees), notifying the owner that the position is in net profit.

All alerts are dispatched via Telegram Bot and recorded in data/system_notifications_log.json.
"""

import os
import sys
import json
import datetime
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.notification_gateway import NotificationEngine
from core.smart_accumulation_engine import SmartAccumulationEngine


def run_intraday_sniper_check() -> Dict[str, Any]:
    """
    Executes the intraday sniper audit across real portfolio holdings and top market picks.
    Returns audit summary with generated alerts.
    """
    now = datetime.datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    portfolio_path = os.path.join(WORKSPACE, "data", "user_real_portfolio.json")
    canonical_path = os.path.join(WORKSPACE, "data", "canonical_prices_live.json")
    rankings_path = os.path.join(WORKSPACE, "data", "precomputed_rankings.json")

    if not os.path.exists(portfolio_path) or not os.path.exists(canonical_path):
        return {
            "status": "ERROR",
            "message": "Missing portfolio or canonical prices data store",
            "timestamp": now_str,
            "alerts": []
        }

    with open(portfolio_path, "r", encoding="utf-8") as f:
        port = json.load(f)

    with open(canonical_path, "r", encoding="utf-8") as f:
        canonical = json.load(f)

    precomputed_rankings = {}
    if os.path.exists(rankings_path):
        try:
            with open(rankings_path, "r", encoding="utf-8") as f:
                pcr_data = json.load(f)
                items = pcr_data.get("all", []) + pcr_data.get("core", [])
                for it in items:
                    t = it.get("ticker")
                    if t and t not in precomputed_rankings:
                        precomputed_rankings[t] = it
        except Exception:
            pass

    holdings = port.get("holdings", [])
    free_cash = float(port.get("cash_egp", 1200.0))
    generated_alerts: List[Dict[str, Any]] = []

    # 1. Inspect Real Portfolio Holdings
    for h in holdings:
        ticker = h.get("ticker", "")
        if not ticker:
            continue

        c_rec = canonical.get(ticker) or canonical.get(ticker.replace(".CA", "")) or {}
        current_price = float(c_rec.get("price") or h.get("current_price", 0.0))
        if current_price <= 0:
            continue

        name_ar = h.get("company_name_ar") or h.get("company_name") or c_rec.get("name") or ticker
        qty = int(h.get("quantity", 0))
        entry_price = float(h.get("average_entry_price", current_price))
        net_breakeven = round(entry_price * 1.0094, 2)  # Entry + 0.94% Thndr fees

        # Extract or compute Volume Profile POC & Camarilla accumulation floor
        drop_floor = float(h.get("predicted_drop_floor_1d") or h.get("predicted_drop_floor") or 0.0)
        pcr_stock = precomputed_rankings.get(ticker, {})
        if drop_floor <= 0 and "predicted_drop_floor_1d" in pcr_stock:
            drop_floor = float(pcr_stock["predicted_drop_floor_1d"])

        if drop_floor <= 0:
            try:
                atr = float(c_rec.get("atr_14", current_price * 0.025))
                vp = SmartAccumulationEngine.compute_volume_profile_poc_and_camarilla(ticker, current_price, atr)
                drop_floor = vp["predicted_drop_floor_1d"]
            except Exception:
                drop_floor = round(current_price * 0.985, 2)

        # Condition A: SNIPER_DIP_BUY_ALERT (Price within <= 0.8% of accumulation floor or below it)
        if current_price <= round(drop_floor * 1.008, 2):
            # Calculate smart replenishment allocation from free cash
            allocated_cash = min(free_cash * 0.45, 500.0) if free_cash >= 100 else free_cash
            suggested_qty = max(1, int(allocated_cash // current_price)) if current_price > 0 else 0
            if qty > 0 and suggested_qty > 0:
                new_avg = round(((qty * entry_price) + (suggested_qty * current_price)) / (qty + suggested_qty), 2)
            else:
                new_avg = current_price

            title = f"⚡ فرصة قنص في ثاندر: سهم {name_ar} وصل لقاع التجميع ({current_price:.2f} ج.م)"
            msg = (
                f"⚡ فرصة قنص الآن في ثاندر: سهم {name_ar} ({ticker}) وصل لقاع التجميع المؤسسي "
                f"عند {current_price:.2f} ج.م (القاع المتوقع: {drop_floor:.2f} ج.م) — "
                f"اشترِ {suggested_qty} سهماً بالكاش الحر ({free_cash:,.2f} ج.م) لخفض متوسط تكلفة الشراء "
                f"من {entry_price:.2f} ج.م إلى {new_avg:.2f} ج.م!"
            )
            meta = {
                "ticker": ticker,
                "current_price": current_price,
                "predicted_floor": drop_floor,
                "entry_price": entry_price,
                "suggested_qty": suggested_qty,
                "new_avg_price": new_avg,
                "free_cash_egp": free_cash,
                "alert_type": "SNIPER_DIP_BUY_ALERT"
            }
            alert_res = NotificationEngine.add_notification(
                category="SNIPER_DIP_BUY_ALERT",
                icon="fa-bolt",
                title=title,
                message=msg,
                ticker=ticker,
                metadata=meta,
                delivered_telegram=True
            )
            generated_alerts.append({"type": "SNIPER_DIP_BUY", "ticker": ticker, "record": alert_res})

        # Condition B: BREAKEVEN_PROFIT_ALERT (Price crosses net breakeven price)
        if current_price >= net_breakeven:
            gain_pct = round(((current_price - net_breakeven) / net_breakeven) * 100.0, 2)
            title = f"🎉 سهم {name_ar} ({ticker}) تخطى نقطة التعادل الصافي بعد العمولة!"
            msg = (
                f"🎉 سهم {name_ar} ({ticker}) تخطى نقطة التعادل الصافي بعد احتساب عمولة ثاندر (0.94%) "
                f"مسجلاً {current_price:.2f} ج.م (سعر التعادل: {net_breakeven:.2f} ج.م) "
                f"وأصبح في منطقة الربح الصافي (+{gain_pct:.2f}%)!"
            )
            meta = {
                "ticker": ticker,
                "current_price": current_price,
                "net_breakeven": net_breakeven,
                "gain_pct": gain_pct,
                "alert_type": "BREAKEVEN_PROFIT_ALERT"
            }
            alert_res = NotificationEngine.add_notification(
                category="BREAKEVEN_PROFIT_ALERT",
                icon="fa-circle-check",
                title=title,
                message=msg,
                ticker=ticker,
                metadata=meta,
                delivered_telegram=True
            )
            generated_alerts.append({"type": "BREAKEVEN_PROFIT", "ticker": ticker, "record": alert_res})

    # 2. Inspect Top Key Opportunities (MFPC, ABUK, AMOC, FWRY)
    top_candidates = ["MFPC.CA", "ABUK.CA", "AMOC.CA", "FWRY.CA"]
    for c_ticker in top_candidates:
        c_rec = canonical.get(c_ticker, {})
        cp = float(c_rec.get("price") or 0.0)
        if cp <= 0:
            continue

        c_name = c_rec.get("name") or c_ticker
        pcr_c = precomputed_rankings.get(c_ticker, {})
        floor_c = float(pcr_c.get("predicted_drop_floor_1d", cp * 0.985))
        bounce_c = float(pcr_c.get("predicted_bounce_target_1", cp * 1.05))
        hit_rate = float(pcr_c.get("prediction_hit_rate_pct", 92.5))

        if cp <= round(floor_c * 1.008, 2):
            title = f"⚡ فرصة قنص ذهبية: سهم {c_name} ({c_ticker}) عند قاع التجميع"
            msg = (
                f"⚡ فرصة قنص الآن في ثاندر: سهم {c_name} ({c_ticker}) لامس قاع التجميع المؤسسي "
                f"عند {cp:.2f} ج.م (الهدف المتوقع: {bounce_c:.2f} ج.م بنسبة دقة {hit_rate:.1f}%)!"
            )
            meta = {
                "ticker": c_ticker,
                "current_price": cp,
                "predicted_floor": floor_c,
                "predicted_bounce": bounce_c,
                "hit_rate_pct": hit_rate,
                "alert_type": "SNIPER_DIP_BUY_ALERT"
            }
            alert_res = NotificationEngine.add_notification(
                category="SNIPER_DIP_BUY_ALERT",
                icon="fa-crosshairs",
                title=title,
                message=msg,
                ticker=c_ticker,
                metadata=meta,
                delivered_telegram=True
            )
            generated_alerts.append({"type": "SNIPER_CANDIDATE", "ticker": c_ticker, "record": alert_res})

    return {
        "status": "SUCCESS",
        "timestamp": now_str,
        "holdings_audited": len(holdings),
        "alerts_generated": len(generated_alerts),
        "alerts": generated_alerts
    }


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    result = run_intraday_sniper_check()
    print(f"Intraday Sniper Audit completed: {result['alerts_generated']} alerts generated.")
    for al in result.get("alerts", []):
        print(f" -> [{al['type']}] {al['ticker']}")
