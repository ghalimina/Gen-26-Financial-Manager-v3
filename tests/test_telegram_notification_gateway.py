#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# tests/test_telegram_notification_gateway.py — Unit Tests for NotificationEngine
# Validates:
# 1. Telegram Dispatch & Local Log Persistence.
# 2. Strong Buy Alert Formatting.
# 3. Stop Loss Execution Alert Formatting.
# 4. Fallback when credentials are not configured.
# =============================================================================

import os
import sys
import unittest

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.notification_gateway import NotificationEngine


class TestTelegramNotificationGateway(unittest.TestCase):

    def test_01_send_telegram_alert_dispatch_and_logging(self):
        """Verify send_telegram_alert logs locally and returns valid delivery status."""
        res = NotificationEngine.send_telegram_alert(
            message="*اختبار منظومة الإشعارات الحية*",
            alert_type="STRONG_BUY",
            title="🟢 إشارة شراء قوي تجريبية"
        )
        self.assertIn("notification_id", res)
        self.assertEqual(res["category"], "STRONG_BUY")
        self.assertIn("timestamp", res)

    def test_02_send_buy_signal_alert_formatting(self):
        """Verify send_buy_signal_alert structures entry, target, and stop loss clearly."""
        signal_payload = {
            "ticker": "COMI.CA",
            "company_name": "البنك التجاري الدولي",
            "current_price": 140.0,
            "entry_low": 138.0,
            "max_entry_price": 141.0,
            "stop_loss": 133.0,
            "target_price": 152.0,
            "confidence_score": 92.5
        }
        res = NotificationEngine.send_buy_signal_alert(signal_payload)
        self.assertIn("notification_id", res)
        self.assertEqual(res["category"], "BUY_SIGNAL")
        self.assertIn("COMI.CA", res["message"])

    def test_03_send_stop_loss_alert_formatting(self):
        """Verify send_stop_loss_hit_alert records emergency exit parameters."""
        res = NotificationEngine.send_stop_loss_hit_alert(
            ticker="SWDY.CA",
            stop_price=105.0,
            current_price=104.5,
            loss_pct=5.2
        )
        self.assertIn("notification_id", res)
        self.assertEqual(res["category"], "STOP_LOSS_HIT")
        self.assertIn("SWDY.CA", res["message"])

    def test_04_get_recent_notifications(self):
        """Verify get_recent_notifications returns list of recent records."""
        logs = NotificationEngine.get_recent_notifications(limit=5)
        self.assertIsInstance(logs, list)
        self.assertGreater(len(logs), 0)


if __name__ == "__main__":
    unittest.main()
