#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/telegram_notifier.py — GEN-26 Telegram Push Notification Gateway
# Delivers real-time mobile push alerts for portfolio targets, stops, and dividends.
# =============================================================================

import os
import sys
import json
import logging
import urllib.request
import urllib.parse
import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger("GEN26.TelegramNotifier")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
TELEGRAM_CONFIG_FILE = os.path.join(DATA_DIR, "telegram_config.json")


class TelegramNotifier:
    """
    Institutional Telegram Notification Gateway for GEN-26 EGX Quantitative Platform.
    """

    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """Loads Telegram Bot configuration from persistent JSON."""
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(TELEGRAM_CONFIG_FILE):
            default_cfg = {
                "bot_token": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
                "chat_id": os.environ.get("TELEGRAM_CHAT_ID", ""),
                "enabled": bool(os.environ.get("TELEGRAM_BOT_TOKEN")),
                "alert_types": {
                    "target_hits": True,
                    "stop_loss_warnings": True,
                    "dividend_reminders": True,
                    "macro_shocks": True
                },
                "last_alert_timestamp": None
            }
            cls.save_config(default_cfg)
            return default_cfg

        try:
            with open(TELEGRAM_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {
                "bot_token": "",
                "chat_id": "",
                "enabled": False,
                "alert_types": {"target_hits": True, "stop_loss_warnings": True, "dividend_reminders": True}
            }

    @classmethod
    def save_config(cls, config_data: Dict[str, Any]) -> bool:
        """Saves Telegram Bot configuration to persistent JSON."""
        os.makedirs(DATA_DIR, exist_ok=True)
        try:
            tmp = f"{TELEGRAM_CONFIG_FILE}.tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, TELEGRAM_CONFIG_FILE)
            return True
        except Exception as e:
            logger.error(f"Failed to save Telegram config: {e}")
            return False

    @classmethod
    def send_message(
        cls,
        text: str,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        parse_mode: str = "HTML",
        timeout_sec: float = 5.0
    ) -> Dict[str, Any]:
        """
        Sends an instant push message to the user's Telegram.
        """
        cfg = cls.load_config()
        token = bot_token if bot_token is not None else (cfg.get("bot_token") or os.environ.get("TELEGRAM_BOT_TOKEN", ""))
        cid = chat_id if chat_id is not None else (cfg.get("chat_id") or os.environ.get("TELEGRAM_CHAT_ID", ""))

        if not token or not cid:
            return {
                "success": False,
                "error": "لم يتم إعداد Bot Token أو Chat ID لتيليجرام. يرجى إدخالهما من الإعدادات."
            }

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": cid,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                if res_data.get("ok"):
                    return {"success": True, "message_id": res_data.get("result", {}).get("message_id")}
                return {"success": False, "error": res_data.get("description", "Unknown Telegram API error")}
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8")
            return {"success": False, "error": f"HTTP {he.code}: {err_body}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def test_connection(cls, bot_token: str, chat_id: str) -> Dict[str, Any]:
        """Sends a verification ping message to test token and chat_id."""
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        test_msg = (
            f"🏛️ <b>منظومة GEN-26 — اختبار الاتصال الناجح</b>\n\n"
            f"🟢 <b>تم تفعيل بوابة تنبيهات تيليجرام بنجاح!</b>\n"
            f"⏱️ التوقيت: <code>{now_str}</code>\n"
            f"💼 ستتلقى هنا إشعارات فورية عند تحقيق أهداف أسهمك، وتنبيهات حماية وقف الخسارة، والتوزيعات النقدية."
        )
        return cls.send_message(test_msg, bot_token=bot_token, chat_id=chat_id)

    @classmethod
    def format_morning_briefing(cls, briefing_data: Dict[str, Any]) -> str:
        """
        Formats morning briefing dictionary into an executive Telegram HTML message.
        """
        import html
        data = briefing_data or {}
        headline = html.escape(str(data.get("headline", "☀️ التقرير الصباحي والتحليل الاستراتيجي للسوق")))
        regime_ar = html.escape(str(data.get("market_regime_ar") or data.get("market_regime", "اتجاه صاعد (BULLISH)")))
        date_str = str(data.get("date", datetime.date.today().strftime("%Y-%m-%d")))
        summary = html.escape(str(data.get("summary_markdown", "استمرار الزخم الإيجابي في الأسهم القيادية مع استقرار السيولة.")))

        # Optional macro indicators
        macro_line = ""
        try:
            from core.cbe_rates_engine import CBERatesEngine
            macro = CBERatesEngine.get_latest_rates()
            corridor = float(macro.get("corridor_lending_rate", 28.25))
            inflation = float(macro.get("headline_cpi_inflation", 14.50))
            macro_line = f"\n🏛️ <b>فائدة المركزي:</b> {corridor:.2f}% | <b>التضخم:</b> {inflation:.2f}%\n"
        except Exception:
            pass

        lines = [
            f"☀️ <b>{headline}</b>",
            f"📅 التاريخ: <code>{date_str}</code>",
            f"🌐 حالة السوق: <b>{regime_ar}</b>{macro_line}",
            f"━━━━━━━━━━━━━━━━━━",
            f"📝 <b>الملخص الاستراتيجي:</b>",
            f"<i>{summary}</i>\n",
            f"🎯 <b>أبرز الترشيحات والفرص الاستثمارية:</b>"
        ]

        picks = data.get("key_recommendations", [])
        if picks and isinstance(picks, list):
            for i, p in enumerate(picks[:5], 1):
                sym = html.escape(str(p.get("ticker", "EGX")))
                name = html.escape(str(p.get("name_ar") or sym))
                price = float(p.get("current_price") or p.get("price", 0.0))
                target = float(p.get("target_price") or 0.0)
                stop = float(p.get("stop_loss") or 0.0)
                action = html.escape(str(p.get("action", "شراء وتجميع")))
                score = float(p.get("composite_score") or p.get("score", 85.0))
                lines.append(
                    f"{i}. <b>{name} ({sym})</b> — <b>{action}</b> (تقييم: {score:.1f})\n"
                    f"   💵 السعر: <code>{price:,.2f}</code> ج.م | 🎯 الهدف: <code>{target:,.2f}</code> | 🛑 الوقف: <code>{stop:,.2f}</code>"
                )
        else:
            lines.append("<i>لا توجد مراكز شراء موصى بها حالياً وفق نماذج المخاطر.</i>")

        lines.append("\n⚖️ <i>منظومة GEN-26 Institutional Trading System</i>")
        return "\n".join(lines)

    @classmethod
    def send_morning_briefing_alert(
        cls,
        briefing_data: Dict[str, Any],
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Dispatches the formatted morning briefing to Telegram.
        """
        msg_text = cls.format_morning_briefing(briefing_data)
        return cls.send_message(msg_text, bot_token=bot_token, chat_id=chat_id, parse_mode="HTML")

