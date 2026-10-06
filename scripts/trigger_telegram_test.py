#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/trigger_telegram_test.py
=================================
Independent Telegram Dispatch Runner and Verification Gateway.
1. Checks for TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in environment or .env.
2. If configured, dispatches the full authoritative EOD executive report to the user's phone.
3. If not configured, prints clear setup instructions and outputs the complete mobile preview.
"""

import os
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from scripts.send_eod_telegram_report import (
    get_telegram_credentials,
    dispatch_full_eod_report,
    build_concise_reports,
    load_json_safe,
    get_top_stocks,
    REGIME_FILE,
    MACRO_FILE
)


def run_telegram_test():
    print("=" * 70)
    print("🏛️ GEN-26 TELEGRAM DISPATCH RUNNER & VERIFICATION GATEWAY")
    print("=" * 70)

    token, chat_id = get_telegram_credentials()
    is_valid_token = bool(token and token.strip() and not token.startswith("your_"))
    is_valid_chat = bool(chat_id and chat_id.strip() and not chat_id.startswith("your_"))

    if is_valid_token and is_valid_chat:
        print(f"[*] تم اكتشاف بيانات التيليجرام:")
        masked_token = token[:8] + "..." + token[-4:] if len(token) > 12 else "***"
        print(f"    • Bot Token: {masked_token}")
        print(f"    • Chat ID:   {chat_id}")
        print("[*] جاري توليد وإرسال التقرير التنفيذي المباشر إلى التيليجرام...")
        
        try:
            success = dispatch_full_eod_report(force_send=True)
            if success:
                print("\n" + "=" * 70)
                print("✅ تم إرسال التقرير بنجاح إلى هاتفك عبر التيليجرام!")
                print("=" * 70)
                return True
            else:
                print("\n[❌] فشل إرسال التقرير إلى التيليجرام (يرجى مراجعة صلاحية التوكن والـ Chat ID).")
                return False
        except Exception as e:
            print(f"\n[❌] حدث خطأ أثناء الإرسال: {e}")
            return False

    else:
        print("\n" + "=" * 70)
        print("⚠️ تنبيه: بيانات بوت التيليجرام غير مضافة في ملف .env المحلي")
        print("=" * 70)
        print("لتفعيل الإرسال المباشر إلى هاتفك المحمول، أنشئ ملفاً باسم .env في المجلد الرئيسي:")
        print("ضع به السطرين التاليين بعد استبدال القيم ببيانات البوت الخاص بك:\n")
        print("TELEGRAM_BOT_TOKEN=your_bot_token_here")
        print("TELEGRAM_CHAT_ID=your_chat_id_here\n")
        print("📌 ملاحظة: في السحابة على GitHub Actions، يتم جلب المفاتيح تلقائياً من GitHub Secrets")
        print("=" * 70)
        print("\n📱 معاينة حية للتقرير التنفيذي الكامل المولد للموبايل (Full Message Preview):\n")

        regime_data = load_json_safe(REGIME_FILE)
        macro_data = load_json_safe(MACRO_FILE)
        top_stocks = get_top_stocks(limit=6)

        messages = build_concise_reports(regime_data, macro_data, top_stocks)
        for idx, msg in enumerate(messages, start=1):
            print(f"--- [رسالة {idx} من {len(messages)} | الطول: {len(msg)} حرف] ---")
            print(msg)
            print("-" * 70)

        print("\n[INFO] التقرير سليم وجاهز للتسليم الفوري فور حفظ المتغيرات في .env أو تشغيل GitHub Actions.")
        return True


if __name__ == "__main__":
    success = run_telegram_test()
    sys.exit(0 if success else 1)
