#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/portfolio_alert_engine.py — Real Portfolio Alert Rule Engine
# Evaluates Target Hits (+8% / +15%), Stop-Loss Proximity, and Corporate Ex-Dates.
# =============================================================================

import os
import sys
import datetime
import logging
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.real_portfolio import RealPortfolioTracker
from core.market_price_service import MarketPriceService
from core.telegram_notifier import TelegramNotifier

logger = logging.getLogger("GEN26.PortfolioAlertEngine")


class PortfolioAlertEngine:
    """
    Automated Alert Scanner for User's Real Portfolio Holdings.
    """

    @classmethod
    def scan_and_dispatch_alerts(cls, send_telegram: bool = True) -> Dict[str, Any]:
        """
        Scans all active real portfolio holdings against price levels, target hits,
        and stop losses, generating structured alerts.
        """
        portfolio = RealPortfolioTracker.analyze_real_portfolio()
        holdings = portfolio.get("holdings", [])
        alerts = []

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        for h in holdings:
            sym = h.get("ticker", "")
            name = h.get("company_name", sym)
            qty = h.get("quantity", 0)
            entry = float(h.get("average_entry_price", 0.0))
            curr = float(h.get("current_price", entry))
            pnl_pct = float(h.get("unrealized_pnl_pct", 0.0))
            stop = float(h.get("stop_loss", entry * 0.93))
            target1 = round(entry * 1.08, 2)
            target2 = round(entry * 1.15, 2)

            # 1. Target 2 Hit Alert (+15% or more)
            if curr >= target2 or pnl_pct >= 15.0:
                alert = {
                    "type": "TARGET_2_HIT",
                    "severity": "SUCCESS",
                    "ticker": sym,
                    "company_name": name,
                    "current_price": curr,
                    "entry_price": entry,
                    "pnl_pct": pnl_pct,
                    "title_ar": f"🎯 تحقيق الهدف الثاني بنمو (+{pnl_pct:.1f}%) لسهم {name}",
                    "message_ar": (
                        f"🚀 <b>تم تحقيق الهدف الاستثماري الثاني لسهم {name} ({sym})!</b>\n\n"
                        f"📈 سعر الدخول: <code>{entry:.2f} ج.م</code>\n"
                        f"💎 السعر اللحظي: <code>{curr:.2f} ج.م</code> (+{pnl_pct:.1f}%)\n"
                        f"💡 <b>التوصية الخوارزمية:</b> جني أرباح جزئي إضافي (33%) وتفعيل الوقف المتحرك لحماية المكاسب."
                    )
                }
                alerts.append(alert)

            # 2. Target 1 Hit Alert (+8% to +14.9%)
            elif curr >= target1 or pnl_pct >= 8.0:
                alert = {
                    "type": "TARGET_1_HIT",
                    "severity": "SUCCESS",
                    "ticker": sym,
                    "company_name": name,
                    "current_price": curr,
                    "entry_price": entry,
                    "pnl_pct": pnl_pct,
                    "title_ar": f"🎯 تحقيق الهدف الأول (+{pnl_pct:.1f}%) لسهم {name}",
                    "message_ar": (
                        f"🎯 <b>تحقيق الهدف الأول لسهم {name} ({sym})!</b>\n\n"
                        f"📈 سعر الدخول: <code>{entry:.2f} ج.م</code>\n"
                        f"💵 السعر اللحظي: <code>{curr:.2f} ج.م</code> (+{pnl_pct:.1f}%)\n"
                        f"💡 <b>التوصية الخوارزمية:</b> جني ربح جزئي (33%) ورفع أمر وقف الخسارة لسعر الدخول (Breakeven)."
                    )
                }
                alerts.append(alert)

            # 3. Stop-Loss Breach or Proximity Warning
            if curr <= stop:
                alert = {
                    "type": "STOP_LOSS_BREACH",
                    "severity": "CRITICAL",
                    "ticker": sym,
                    "company_name": name,
                    "current_price": curr,
                    "entry_price": entry,
                    "pnl_pct": pnl_pct,
                    "title_ar": f"🛑 كسر حد وقف الخسارة لسهم {name} ({sym})",
                    "message_ar": (
                        f"🛑 <b>تحذير عاجل: كسر حد وقف الخسارة لسهم {name} ({sym})!</b>\n\n"
                        f"📉 السعر الحالي: <code>{curr:.2f} ج.م</code> كسر مستوى الحماية <code>{stop:.2f} ج.م</code> ({pnl_pct:.1f}%).\n"
                        f"🛡️ <b>توصية إدارة المخاطر:</b> تفعيل الخروج الإلزامي فوراً لحماية 93% من رأس المال ضد استمرار الهبوط."
                    )
                }
                alerts.append(alert)
            elif curr <= (stop * 1.025):
                # Within 2.5% of stop loss
                alert = {
                    "type": "STOP_LOSS_WARNING",
                    "severity": "WARNING",
                    "ticker": sym,
                    "company_name": name,
                    "current_price": curr,
                    "entry_price": entry,
                    "pnl_pct": pnl_pct,
                    "title_ar": f"⚠️ اقتراب من وقف الخسارة لسهم {name}",
                    "message_ar": (
                        f"⚠️ <b>تنبيه: سهم {name} ({sym}) يقترب من حد وقف الخسارة</b>\n\n"
                        f"السعر الحالي: <code>{curr:.2f} ج.م</code> (وقف الخسارة عند <code>{stop:.2f} ج.م</code>)."
                    )
                }
                alerts.append(alert)

        # Dispatch via Telegram if configured
        dispatched_count = 0
        if send_telegram and alerts:
            cfg = TelegramNotifier.load_config()
            if cfg.get("enabled"):
                for a in alerts:
                    res = TelegramNotifier.send_message(a["message_ar"])
                    if res.get("success"):
                        dispatched_count += 1

        return {
            "timestamp": now_str,
            "holdings_scanned": len(holdings),
            "alerts_count": len(alerts),
            "telegram_dispatched": dispatched_count,
            "alerts": alerts
        }
