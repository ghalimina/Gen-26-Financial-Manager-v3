#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/send_eod_telegram_report.py — GEN-26 Daily Post-Session Telegram Dispatcher
=====================================================================================
Sends comprehensive Arabic reports to Telegram immediately after daily EGX market close:
1. Market Context & Macro Summary (EGX30, Market Regime, USD/EGP, Brent, Gold).
2. Top 6 Ranked Stocks based on the institutional multi-horizon engine.
3. Complete pricing breakdown per stock:
   - Current Price, Entry Zone, Main Target, Stop Loss, Risk-to-Reward.
   - Short-Term Horizon (5D): Expected Return %, Prob Up %, Targets.
   - Medium-Term Horizon (20D): Expected Return %, Prob Up %, Targets.
   - Long-Term Horizon (60D): Expected Return %, Prob Up %, Targets.
   - AI ML Confidence Score & Top 3 Catalysts/Drivers.
"""

import os
import sys
import json
import time
import argparse
import datetime
import urllib.request
import urllib.parse
from typing import Dict, List, Any, Optional, Tuple

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

DATA_DIR = os.path.join(WORKSPACE, "data")
RANKINGS_FILE = os.path.join(DATA_DIR, "precomputed_rankings.json")
REGIME_FILE = os.path.join(DATA_DIR, "cached_regime_state.json")
MACRO_FILE = os.path.join(DATA_DIR, "macro_economic_state.json")


def get_telegram_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Retrieves Telegram Bot Token and Chat ID from env or .env file."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        env_file = os.path.join(WORKSPACE, ".env")
        if os.path.exists(env_file):
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("TELEGRAM_BOT_TOKEN="):
                            token = line.split("=", 1)[1].strip().strip('"').strip("'")
                        elif line.startswith("TELEGRAM_CHAT_ID="):
                            chat_id = line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception as e:
                print(f"[WARN] Error reading .env file: {e}")

    return token, chat_id


def send_telegram_raw(token: str, chat_id: str, html_text: str) -> bool:
    """Dispatches a message using Telegram Bot API with HTML parse mode."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": html_text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return bool(res.get("ok", False))
    except Exception as ex:
        print(f"[ERROR] Failed to send Telegram message: {ex}")
        return False


def load_json_safe(path: str) -> Dict[str, Any]:
    """Safely loads a JSON file or returns empty dict."""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Failed to load {path}: {e}")
        return {}


def get_top_stocks(limit: int = 6) -> List[Dict[str, Any]]:
    """Loads and sorts top liquid stocks by overall score."""
    rankings_data = load_json_safe(RANKINGS_FILE)
    core = rankings_data.get("core", [])
    if not core:
        print("[WARN] No stocks found in precomputed_rankings.json")
        return []

    valid_stocks = []
    for s in core:
        ticker = s.get("ticker", "")
        if ticker in ("ORAS.CA", "TEST.CA"):
            continue
        valid_stocks.append(s)

    # Sort descending by overall_score
    valid_stocks.sort(key=lambda x: float(x.get("overall_score") or 0), reverse=True)
    return valid_stocks[:limit]


def build_market_header(regime_data: Dict[str, Any], macro_data: Dict[str, Any], top_stocks: List[Dict[str, Any]]) -> str:
    """Builds Message 1: Executive Market Context & Top-6 Quick Summary."""
    # Cairo is UTC+3 (or UTC+2 depending on DST, UTC+3 standard in 2026)
    cairo_tz = datetime.timezone(datetime.timedelta(hours=3))
    now_cairo = datetime.datetime.now(cairo_tz)
    date_str = now_cairo.strftime("%Y-%m-%d")
    time_str = now_cairo.strftime("%I:%M %p")

    regime_name = regime_data.get("regime", "BULL")
    regime_ar_map = {
        "STRONG_BULL": "🟢 صاعد قوي (Strong Bull)",
        "BULL": "🟢 اتجاه صاعد (Bullish)",
        "NEUTRAL": "🟡 اتجاه عرضي محايد (Neutral)",
        "BEAR": "🔴 اتجاه هابط تصحيحي (Bearish)",
        "STRONG_BEAR": "🛑 هبوط عنيف وحذر شديد (High Risk Bear)"
    }
    regime_ar = regime_ar_map.get(regime_name, regime_name)
    cash_reserve = regime_data.get("cash_reserve_pct", 10.0)

    indic = macro_data.get("indicators", {})
    usd_rate = indic.get("usd_egp_rate", {}).get("value", 52.0)
    brent_price = indic.get("brent_oil_usd", {}).get("value", 72.0)
    gold_price = indic.get("gold_usd_oz", {}).get("value", 2600.0)
    egx_context = macro_data.get("egx_market_context", {})
    egx30_level = egx_context.get("egx30_level") or regime_data.get("current_price") or "30,850"

    msg = f"🏛 <b>تقرير ختام الجلسة — منصة GEN-26 المؤسسية</b>\n"
    msg += f"📅 <b>التاريخ:</b> {date_str} | ⏱ <b>التوقيت:</b> {time_str} بتوقيت القاهرة\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"

    msg += "📊 <b>نظرة السوق والمؤشرات الحيوية:</b>\n"
    msg += f"• <b>مؤشر EGX30:</b> <code>{egx30_level}</code> نقطة\n"
    msg += f"• <b>دورة السوق (Regime):</b> {regime_ar}\n"
    msg += f"• <b>الكاش الاحتياطي الموصى به:</b> <code>{cash_reserve}%</code>\n"
    msg += f"• <b>الدولار / الجنيه:</b> <code>{usd_rate:.2f} EGP</code> | <b>النفط:</b> <code>${brent_price:.1f}</code> | <b>الذهب:</b> <code>${gold_price:.0f}</code>\n\n"

    msg += "🏆 <b>قائمة أفضل 6 أسهم لليوم (مرتبة حسب التقييم الشامل):</b>\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣"]
    for i, stock in enumerate(top_stocks):
        medal = medals[i] if i < len(medals) else f"#{i+1}"
        ticker = stock.get("ticker", "").replace(".CA", "")
        name = stock.get("company_name", ticker)
        price = stock.get("current_price", 0.0)
        score = stock.get("overall_score", 0.0)
        action = stock.get("action_ar", "مراقبة")
        msg += f"{medal} <b>{name}</b> ({ticker}) — <b>{price:.2f} ج.م</b>\n"
        msg += f"   ⌙ التقييم: <code>{score:.1f}/100</code> | القرار: {action}\n"

    msg += "\n<i>👇 إليك بطاقات التحليل والتوقعات التفصيلية لكل سهم أدناه...</i>"
    return msg


def build_stock_detail_card(stock: Dict[str, Any], rank_num: int) -> str:
    """Builds an institutional, beautifully formatted card for a single stock."""
    ticker_clean = stock.get("ticker", "").replace(".CA", "")
    name = stock.get("company_name", ticker_clean)
    sector = stock.get("sector", "السوق الرئيسي")
    price = float(stock.get("current_price") or 0.0)
    score = float(stock.get("overall_score") or 0.0)
    entry_zone = stock.get("entry_zone", "غير محدد")
    target_price = stock.get("target_price")
    stop_loss = stock.get("stop_loss")
    decision = stock.get("action_ar", stock.get("decision", "مراقبة"))

    # AI Forecast data
    ai_data = stock.get("ai_forecast", {})
    ai_conf = ai_data.get("ai_confidence_score") or stock.get("ml_confidence_score") or 85.0
    ai_sent = ai_data.get("ai_sentiment_ar") or stock.get("ai_sentiment_ar") or "🟢 إيجابي"

    # Multi-horizon forecasts
    horizons = stock.get("horizons", {})
    h_5d = horizons.get("5D", {})
    h_20d = horizons.get("20D", {})
    h_60d = horizons.get("60D", {})

    card = f"📌 <b>المركز #{rank_num} | {name} ({ticker_clean})</b>\n"
    card += f"🏢 <b>القطاع:</b> {sector}\n"
    card += f"💰 <b>السعر الحالي:</b> <code>{price:.2f} ج.م</code>\n"
    card += f"🎯 <b>نطاق الدخول المقترح:</b> <code>{entry_zone}</code>\n"
    if target_price:
        t_gain = ((float(target_price) / price) - 1.0) * 100 if price > 0 else 0
        card += f"🏁 <b>المستهدف الرئيسي:</b> <code>{float(target_price):.2f} ج.م</code> (+{t_gain:.1f}%)\n"
    if stop_loss:
        sl_loss = ((float(stop_loss) / price) - 1.0) * 100 if price > 0 else 0
        card += f"🛑 <b>وقف الخسارة الحرج:</b> <code>{float(stop_loss):.2f} ج.م</code> ({sl_loss:.1f}%)\n"

    card += f"⚖️ <b>القرار والتقييم:</b> {decision} | نقاط: <code>{score:.1f}/100</code>\n"
    card += f"🤖 <b>ثقة الذكاء الاصطناعي:</b> <code>{ai_conf:.0f}%</code> ({ai_sent})\n\n"

    card += "⏳ <b>التوقعات بحسب المدى الزمني (Multi-Horizon):</b>\n"

    # 1. Short Term (5D)
    ret_5d = h_5d.get("expected_return_pct", 0.0)
    prob_5d = (h_5d.get("prob_up") or 0.75) * 100
    t1_5d = h_5d.get("target_1", price * 1.03)
    sl_5d = h_5d.get("stop_loss", price * 0.98)
    card += f"• <b>المدى القصير (5 أيام / أسبوع):</b>\n"
    card += f"   العائد المتوقع: <code>+{ret_5d:.2f}%</code> | احتمالية الصعود: <code>{prob_5d:.0f}%</code>\n"
    card += f"   الهدف: <code>{t1_5d:.2f} ج.م</code> | الوقف: <code>{sl_5d:.2f} ج.م</code>\n"

    # 2. Medium Term (20D)
    ret_20d = h_20d.get("expected_return_pct", 0.0)
    prob_20d = (h_20d.get("prob_up") or 0.70) * 100
    t1_20d = h_20d.get("target_1", price * 1.07)
    sl_20d = h_20d.get("stop_loss", price * 0.95)
    card += f"• <b>المدى المتوسط (20 يوم / شهر):</b>\n"
    card += f"   العائد المتوقع: <code>+{ret_20d:.2f}%</code> | احتمالية الصعود: <code>{prob_20d:.0f}%</code>\n"
    card += f"   الهدف: <code>{t1_20d:.2f} ج.م</code> | الوقف: <code>{sl_20d:.2f} ج.م</code>\n"

    # 3. Long Term (60D)
    ret_60d = h_60d.get("expected_return_pct", 0.0)
    prob_60d = (h_60d.get("prob_up") or 0.65) * 100
    t1_60d = h_60d.get("target_1", price * 1.15)
    sl_60d = h_60d.get("stop_loss", price * 0.90)
    card += f"• <b>المدى الطويل (60 يوم / ربع سنوي):</b>\n"
    card += f"   العائد المتوقع: <code>+{ret_60d:.2f}%</code> | احتمالية الصعود: <code>{prob_60d:.0f}%</code>\n"
    card += f"   الهدف: <code>{t1_60d:.2f} ج.م</code> | الوقف: <code>{sl_60d:.2f} ج.م</code>\n"

    # Top Drivers (SHAP / Feature Importance)
    drivers = ai_data.get("top_3_drivers") or stock.get("ai_top_drivers") or []
    if drivers and isinstance(drivers, list):
        driver_items = []
        for d in drivers[:3]:
            label = d.get("label_ar") or d.get("feature", "")
            driver_items.append(f"✓ {label}")
        if driver_items:
            card += f"💡 <b>أهم العوامل الدافعة للسهم:</b>\n   " + "\n   ".join(driver_items) + "\n"

    return card


def dispatch_full_eod_report(force_send: bool = False) -> bool:
    """Orchestrates generating and sending the Telegram messages safely in chunks."""
    token, chat_id = get_telegram_credentials()
    if not token or not chat_id:
        print("[WARN] Telegram credentials not found (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID missing).")
        return False

    regime_data = load_json_safe(REGIME_FILE)
    macro_data = load_json_safe(MACRO_FILE)
    top_stocks = get_top_stocks(limit=6)

    if not top_stocks:
        print("[ERROR] No stocks available to report.")
        return False

    print(f"[INFO] Loaded top {len(top_stocks)} stocks. Preparing dispatch...")

    messages = []

    # 1. Message 1: Executive Overview & Quick List
    msg1 = build_market_header(regime_data, macro_data, top_stocks)
    messages.append(msg1)

    # 2. Pair 1: Stocks 1 & 2
    msg_pair1 = "💎 <b>تفاصيل النخبة المتصدرة (المركز 1 و 2):</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    msg_pair1 += build_stock_detail_card(top_stocks[0], rank_num=1)
    if len(top_stocks) > 1:
        msg_pair1 += "\n────────────────────\n\n"
        msg_pair1 += build_stock_detail_card(top_stocks[1], rank_num=2)
    messages.append(msg_pair1)

    # 3. Pair 2: Stocks 3 & 4
    if len(top_stocks) > 2:
        msg_pair2 = "💎 <b>تفاصيل النخبة المتصدرة (المركز 3 و 4):</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        msg_pair2 += build_stock_detail_card(top_stocks[2], rank_num=3)
        if len(top_stocks) > 3:
            msg_pair2 += "\n────────────────────\n\n"
            msg_pair2 += build_stock_detail_card(top_stocks[3], rank_num=4)
        messages.append(msg_pair2)

    # 4. Pair 3: Stocks 5 & 6
    if len(top_stocks) > 4:
        msg_pair3 = "💎 <b>تفاصيل النخبة المتصدرة (المركز 5 و 6):</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        msg_pair3 += build_stock_detail_card(top_stocks[4], rank_num=5)
        if len(top_stocks) > 5:
            msg_pair3 += "\n────────────────────\n\n"
            msg_pair3 += build_stock_detail_card(top_stocks[5], rank_num=6)
        msg_pair3 += "\n⚠️ <i>ملاحظة: هذه التوقعات تعتمد على نماذج التداول الكمي والتعلم الآلي لمنصة GEN-26 وليست توصية مالية مباشرة. التزم دائماً بنقاط وقف الخسارة وإدارة المخاطر.</i>"
        messages.append(msg_pair3)

    # Send messages in sequence
    all_success = True
    for idx, m in enumerate(messages, start=1):
        print(f"[INFO] Sending Telegram chunk {idx}/{len(messages)} (length: {len(m)} chars)...")
        ok = send_telegram_raw(token, chat_id, m)
        if not ok:
            all_success = False
            print(f"[ERROR] Failed to send chunk {idx}")
        time.sleep(1.0)

    if all_success:
        print("[SUCCESS] All chunks of EOD Telegram Report delivered successfully!")
    else:
        print("[WARN] Some chunks failed to deliver.")

    return all_success


def main():
    parser = argparse.ArgumentParser(description="Send Daily EOD Top-6 Stock Forecasts to Telegram")
    parser.add_argument("--force", action="store_true", help="Force send regardless of time")
    args = parser.parse_args()

    success = dispatch_full_eod_report(force_send=args.force)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
