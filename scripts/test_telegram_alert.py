#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.notification_gateway import NotificationEngine

if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=== Testing GEN-26 Telegram Notification Dispatch ===")
    token, chat_id = NotificationEngine.get_credentials()
    if not token or not chat_id:
        print("⚠️ Telegram credentials not set in .env (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID).")
        print("Please configure them in your .env file to enable live mobile alerts.")
    else:
        print(f"Found Token: {token[:6]}... | Chat ID: {chat_id}")
    
    res = NotificationEngine.send_system_health_alert("INFO", "🧪 رسالة تجريبية: منظومة GEN-26 متصلة ومستعدة بنجاح!")
    print("Dispatch result:", res)
