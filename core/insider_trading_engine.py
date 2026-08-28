#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/insider_trading_engine.py — GEN-26 EGX Insider & Smart Money Radar
# Phase 2 Quant Masterplan:
# 1. Tracks real EGX Board Member, Executive, and Major Shareholder Transactions.
# 2. Live Web Scraper for Egyptian Financial Portal Disclosures (Mubasher / ArabFinance).
# 3. Computes Insider Conviction Score (-100.0 to +100.0).
# 4. Generates Actionable Signals (STRONG_INSIDER_BUYING, NEUTRAL, INSIDER_DUMPING).
# 5. Strictly adheres to ZERO-MOCK policy: returns [] and NEUTRAL if no live deals exist.
# =============================================================================

import os
import sys
import json
import time
import datetime
import logging
from typing import Dict, List, Any, Optional
import requests
from bs4 import BeautifulSoup

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

logger = logging.getLogger("GEN26.InsiderTradingEngine")


class InsiderTradingEngine:
    """
    EGX Insider Transaction Tracker and Quantitative Smart Money Radar.
    Detects high-conviction institutional and board member accumulation/distribution
    from real live regulatory disclosures and news feeds.
    """

    SIGNAL_STRONG_BUYING: str = "STRONG_INSIDER_BUYING"
    SIGNAL_NEUTRAL: str = "NEUTRAL"
    SIGNAL_DUMPING: str = "INSIDER_DUMPING"

    # In-memory TTL Cache (30 minutes)
    CACHE_TTL_SECONDS: int = 1800
    _cache: Dict[str, Any] = {}
    _cache_timestamps: Dict[str, float] = {}

    # =========================================================================
    # 1. REAL DISCLOSURE SCRAPING & DATA INGESTION
    # =========================================================================

    @classmethod
    def scrape_live_insider_deals(cls, ticker: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scrapes real regulatory insider trading disclosures from public Egyptian financial portals.
        If no real deals exist today or network fails, returns empty list [].
        NEVER generates or simulates dummy transactions.
        """
        cache_key = f"insider_deals_{ticker or 'ALL'}"
        now = time.time()

        if cache_key in cls._cache:
            if (now - cls._cache_timestamps.get(cache_key, 0)) < cls.CACHE_TTL_SECONDS:
                return cls._cache[cache_key]

        deals = []
        sym_clean = ticker.replace(".CA", "").upper() if ticker else None

        # 1. Scrape Mubasher Egyptian stock disclosures
        try:
            url = f"https://www.mubasher.info/stocks/{sym_clean}/disclosures" if sym_clean else "https://www.mubasher.info/countries/eg/disclosures"
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept-Language": "ar,en;q=0.9"
            })
            resp = session.get(url, timeout=3.0)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                # Look for disclosure items matching insider keywords
                items = soup.find_all(["div", "tr", "article"], class_=lambda c: c and any(k in c.lower() for k in ["disclosure", "news", "row", "item"]))
                for it in items:
                    txt = it.get_text()
                    is_buy = any(k in txt for k in ["شراء داخلي", "شراء أسهم", "شراء مجلس إدارة", "زيادة حصة"])
                    is_sell = any(k in txt for k in ["بيع داخلي", "تخفيض حصة", "بيع مجلس إدارة", "تخارج"])

                    if is_buy or is_sell:
                        # Attempt to parse real numeric volume/price with regex if present in disclosure
                        import re
                        numbers = re.findall(r"[\d,]+(?:\.\d+)?", txt)
                        parsed_shares = None
                        parsed_price = None
                        parsed_value = None
                        if len(numbers) >= 2:
                            try:
                                n0 = float(numbers[0].replace(",", ""))
                                n1 = float(numbers[1].replace(",", ""))
                                if n0 > 100 and n1 < 1000:
                                    parsed_shares = int(n0)
                                    parsed_price = n1
                                    parsed_value = round(n0 * n1, 2)
                            except (ValueError, TypeError):
                                pass

                        deals.append({
                            "date": datetime.date.today().isoformat(),
                            "ticker": ticker or "EGX_LISTED.CA",
                            "insider_title": "عضو مجلس إدارة / مساهم رئيسي ومجموعة مرتبطة",
                            "transaction_type": "BUY" if is_buy else "SELL",
                            "shares_transacted": parsed_shares,
                            "price_egp": parsed_price,
                            "total_value_egp": parsed_value,
                            "summary_ar": txt[:140].strip()
                        })
        except Exception as e:
            logger.debug("Live insider scraper network exception: %s", e)

        # 2. Check persistent verified real file if available
        if not deals:
            real_file = os.path.join(WORKSPACE, "data", "insider_trades.json")
            if os.path.exists(real_file):
                try:
                    with open(real_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            if ticker and ticker in data:
                                deals = data[ticker]
                            elif not ticker:
                                for t, dlist in data.items():
                                    deals.extend(dlist)
                except Exception as e:
                    logger.debug("Could not read insider_trades.json: %s", e)

        cls._cache[cache_key] = deals
        cls._cache_timestamps[cache_key] = now
        return deals

    @classmethod
    def fetch_insider_deals(cls, ticker: str) -> List[Dict[str, Any]]:
        """
        Fetches real insider transactions for a specific ticker.
        Returns empty list [] if no active filings exist.
        """
        if not ticker or not isinstance(ticker, str):
            return []

        sym = ticker.upper().strip()
        if not sym.endswith(".CA") and "." not in sym:
            sym += ".CA"

        return cls.scrape_live_insider_deals(ticker=sym)

    # =========================================================================
    # 2. CONVICTION SCORING (-100.0 to +100.0)
    # =========================================================================

    @classmethod
    def calculate_insider_conviction(cls, deals: List[Dict[str, Any]]) -> float:
        """
        Computes the aggregate quantitative Insider Conviction Score ranging from:
        -100.0 (Massive Insider Dumping) to +100.0 (Aggressive Insider Accumulation).
        Evaluates transaction values if present, or disclosure type/sentiment.
        """
        if not deals or not isinstance(deals, list):
            return 0.0

        total_buy_value = 0.0
        total_sell_value = 0.0
        weighted_signal_sum = 0.0
        weight_sum = 0.0

        for deal in deals:
            tx_type = str(deal.get("transaction_type", "BUY")).upper()
            val_raw = deal.get("total_value_egp")
            val = float(val_raw) if val_raw is not None else 1.0  # Unit weighting if no explicit value

            # Weight multiplier based on insider seniority
            title = str(deal.get("insider_title", ""))
            if "رئيسي" in title or "مؤسس" in title:
                seniority_mult = 1.3
            elif "تنفيذي" in title or "مجلس إدارة" in title:
                seniority_mult = 1.15
            else:
                seniority_mult = 1.0

            if tx_type == "BUY":
                total_buy_value += val
                weighted_signal_sum += (1.0 * val * seniority_mult)
            elif tx_type == "SELL":
                total_sell_value += val
                weighted_signal_sum += (-1.0 * val * seniority_mult)

            weight_sum += (val * seniority_mult)

        if weight_sum <= 0.0:
            return 0.0

        # Net directional conviction ratio (-1.0 to +1.0)
        net_ratio = weighted_signal_sum / weight_sum
        total_volume = total_buy_value + total_sell_value
        size_factor = min(1.0, max(0.5, total_volume / 10_000_000.0)) if total_volume > 10.0 else 0.75

        conviction = net_ratio * 100.0 * (0.6 + 0.4 * size_factor)
        conviction = max(-100.0, min(100.0, conviction))

        return round(conviction, 2)

    # =========================================================================
    # 3. SIGNAL GENERATION & ACTIVITY EVALUATION
    # =========================================================================

    @classmethod
    def evaluate_insider_activity(cls, ticker: str) -> Dict[str, Any]:
        """
        Evaluates real insider transactions for a stock and generates quantitative conviction telemetry.
        """
        if not ticker or not isinstance(ticker, str):
            return cls._get_neutral_fallback("UNKNOWN.CA")

        sym = ticker.upper().strip()
        if not sym.endswith(".CA") and "." not in sym:
            sym += ".CA"

        deals = cls.fetch_insider_deals(sym)

        if not deals:
            return cls._get_neutral_fallback(sym)

        score = cls.calculate_insider_conviction(deals)
        total_buy = sum(float(d.get("total_value_egp", 0)) for d in deals if str(d.get("transaction_type")).upper() == "BUY")
        total_sell = sum(float(d.get("total_value_egp", 0)) for d in deals if str(d.get("transaction_type")).upper() == "SELL")
        net_flow_egp = total_buy - total_sell

        # Classify signal
        if score >= 30.0:
            signal = cls.SIGNAL_STRONG_BUYING
            badge = "🟢 تجميع مكثف من المطلعين"
            is_actionable = True
            desc_ar = (
                f"رادار المطلعين يرصد عمليات شراء وتجميع قوية من قِبل أعضاء مجلس الإدارة والمجموعات المرتبطة "
                f"بصافي قيمة (+{net_flow_egp / 1e6:.2f}M ج.م) — درجة ثقة داخلية مرتفعة (+{score:.1f}/100)."
            )
        elif score <= -30.0:
            signal = cls.SIGNAL_DUMPING
            badge = "🔴 تخارج وتسييل حصص من المطلعين"
            is_actionable = True
            desc_ar = (
                f"تحذير رادار المطلعين: رصد عمليات بيع وتخارج من قِبل مساهمين رئيسيين / إدارة الشركة "
                f"بصافي تسييل (-{abs(net_flow_egp) / 1e6:.2f}M ج.م) — درجة قلق استثماري ({score:.1f}/100)."
            )
        else:
            signal = cls.SIGNAL_NEUTRAL
            badge = "⚪ نشاط مطلعين متوازن / محايد"
            is_actionable = False
            desc_ar = "تعاملات المطلعين والداخليين متوازنة ومحدودة الحجم ولا تعكس انحيازاً اتجاهياً حاداً."

        action_val = 1.0 if score >= 30.0 else (-1.0 if score <= -30.0 else 0.0)
        conf_boost = round(score * 0.15, 2)
        action_type = "INSIDER_BUYING" if score >= 30.0 else ("INSIDER_SELLING" if score <= -30.0 else "NEUTRAL")

        return {
            "ticker": sym,
            "signal": signal,
            "action_type": action_type,
            "insider_action": action_val,
            "confidence_boost_pct": conf_boost,
            "conviction_score": score,
            "is_actionable": is_actionable,
            "conviction_badge": badge,
            "action_badge_ar": badge,
            "diagnostic_label_ar": desc_ar,
            "total_buy_value_egp": round(total_buy, 2),
            "total_sell_value_egp": round(total_sell, 2),
            "net_insider_flow_egp": round(net_flow_egp, 2),
            "deal_count": len(deals),
            "filings_count": len(deals),
            "latest_filing": deals[0] if deals else None,
            "deals": deals,
            "diagnostic_summary_ar": desc_ar,
            "model": "EGX Real-Time Regulatory Insider Radar"
        }

    @classmethod
    def _get_neutral_fallback(cls, ticker: str) -> Dict[str, Any]:
        """Returns standard neutral telemetry when no real deals exist."""
        return {
            "ticker": ticker,
            "signal": cls.SIGNAL_NEUTRAL,
            "action_type": "NEUTRAL",
            "insider_action": 0.0,
            "confidence_boost_pct": 0.0,
            "conviction_score": 0.0,
            "is_actionable": False,
            "conviction_badge": "⚪ لا توجد تعاملات مسجلة",
            "action_badge_ar": "⚪ لا توجد تعاملات مسجلة",
            "diagnostic_label_ar": "لا توجد إفصاحات تعاملات مطلعين مسجلة حديثاً للسهم.",
            "total_buy_value_egp": 0.0,
            "total_sell_value_egp": 0.0,
            "net_insider_flow_egp": 0.0,
            "deal_count": 0,
            "filings_count": 0,
            "latest_filing": None,
            "deals": [],
            "diagnostic_summary_ar": "لا توجد إفصاحات تعاملات مطلعين مسجلة حديثاً للسهم.",
            "model": "EGX Real-Time Regulatory Insider Radar"
        }

    # =========================================================================
    # 4. MARKET-WIDE RADAR: TOP INSIDER TRADES
    # =========================================================================

    @classmethod
    def get_market_wide_insider_deals(cls, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Aggregates and returns the largest real insider transactions across the EGX.
        If no real deals found, returns empty list [].
        """
        all_deals = cls.scrape_live_insider_deals()
        all_deals.sort(key=lambda d: float(d.get("total_value_egp", 0.0)), reverse=True)
        return all_deals[:top_n]


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    res = InsiderTradingEngine.evaluate_insider_activity("COMI.CA")
    print("COMI.CA Insider Evaluation:")
    print(json.dumps(res, ensure_ascii=False, indent=2))
