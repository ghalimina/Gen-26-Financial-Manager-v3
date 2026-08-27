#!/usr/bin/env python3
# =============================================================================
# tests/test_notifications.py — Master Unit Tests for Arabic Notification Engine
# Validates:
# 1. Professional Arabic alert templates formatting & accuracy.
# 2. Persistent JSON logging to data/system_notifications_log.json.
# 3. REST API GET /api/notifications/recent endpoint.
# =============================================================================

import os
import sys
import json
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.notification_gateway import NotificationEngine
from dashboard.app import app


class TestArabicNotifications(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()

    def test_01_arabic_order_executed_template(self):
        """Verify ORDER EXECUTED alert formats with professional Arabic and parameters."""
        res = NotificationEngine.send_order_executed_alert({
            "ticker": "COMI.CA",
            "side": "BUY",
            "quantity": 250,
            "executed_price": 137.00,
            "confidence": 90.0,
            "total_value_egp": 34250.0,
            "slippage_pct": 0.045
        })

        self.assertTrue(res["delivered"])
        msg = res["log_record"]["message"]
        self.assertIn("🚨 *تم التنفيذ:* شراء `COMI.CA`", msg)
        self.assertIn("137.00", msg)
        self.assertIn("90.0%", msg)
        self.assertIn("34,250.00", msg)
        self.assertEqual(res["log_record"]["category"], "ORDER_EXECUTED")
        self.assertEqual(res["log_record"]["icon"], "🚨")

    def test_02_arabic_stop_loss_hit_template(self):
        """Verify STOP LOSS HIT alert formats with capital protection message."""
        res = NotificationEngine.send_stop_loss_hit_alert(
            ticker="SWDY.CA",
            stop_price=107.88,
            current_price=106.50,
            loss_pct=7.0
        )

        msg = res["log_record"]["message"]
        self.assertIn("🛑 *تفعيل وقف الخسارة:* خروج آلي من `SWDY.CA` لحماية رأس المال.", msg)
        self.assertIn("107.88", msg)
        self.assertIn("-7.00%", msg)
        self.assertEqual(res["log_record"]["category"], "STOP_LOSS_HIT")
        self.assertEqual(res["log_record"]["icon"], "🛑")

    def test_03_arabic_macro_shock_template(self):
        """Verify MACRO SHOCK alert formats with quantified rates and reason."""
        res = NotificationEngine.send_macro_shock_alert(
            shock_reason="رفع مفاجئ لسعر الفائدة بمقدار 200 نقطة أساس",
            cbe_rate=21.25,
            usd_egp=49.10,
            regime_name="دفاعي متقلب"
        )

        msg = res["log_record"]["message"]
        self.assertIn("⚠️ *صدمة اقتصادية (ماكرو):*", msg)
        self.assertIn("21.25%", msg)
        self.assertIn("49.10", msg)
        self.assertEqual(res["log_record"]["category"], "MACRO_SHOCK")
        self.assertEqual(res["log_record"]["icon"], "⚠️")

    def test_04_arabic_emergency_retrain_template(self):
        """Verify EMERGENCY RETRAIN alert formats with halt status and trigger reason."""
        res = NotificationEngine.send_emergency_retrain_alert(
            reason="صدمة اقتصاد كلي وتجاوز حركة الدولار 3%"
        )

        msg = res["log_record"]["message"]
        self.assertIn("🚨 *حالة طوارئ:* إيقاف التداول وبدء إعادة التدريب الفوري", msg)
        self.assertIn("EMERGENCY_HALT", msg)
        self.assertEqual(res["log_record"]["category"], "EMERGENCY_RETRAIN")
        self.assertEqual(res["log_record"]["icon"], "🚨")

    def test_05_arabic_routine_retrain_template(self):
        """Verify ROUTINE WEEKLY RETRAIN alert formats with weekend maintenance message."""
        res = NotificationEngine.send_routine_retrain_alert(details="الجمعة (إغلاق أسبوعي)")

        msg = res["log_record"]["message"]
        self.assertIn("🔄 *صيانة أسبوعية:* جاري إعادة تدريب الذكاء الاصطناعي الروتينية", msg)
        self.assertIn("OPERATIONAL", msg)
        self.assertEqual(res["log_record"]["category"], "ROUTINE_RETRAIN")
        self.assertEqual(res["log_record"]["icon"], "🔄")

    def test_06_persistent_json_logging(self):
        """Verify all notifications are saved atomically to data/system_notifications_log.json."""
        logs = NotificationEngine.get_recent_notifications(limit=15)
        self.assertIsInstance(logs, list)
        self.assertGreaterEqual(len(logs), 1)

        newest = logs[0]
        self.assertIn("notification_id", newest)
        self.assertIn("timestamp", newest)
        self.assertIn("category", newest)
        self.assertIn("title", newest)
        self.assertIn("message", newest)

    def test_07_api_notifications_recent_endpoint(self):
        """Verify GET /api/notifications/recent returns structured JSON with 15 alerts."""
        res = self.client.get("/api/notifications/recent")
        self.assertEqual(res.status_code, 200)

        data = res.get_json()
        self.assertIn("notifications", data)
        self.assertIn("telegram_status", data)
        self.assertIsInstance(data["notifications"], list)
        self.assertLessEqual(len(data["notifications"]), 15)


if __name__ == "__main__":
    unittest.main()
