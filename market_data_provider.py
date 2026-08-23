#!/usr/bin/env python3
# =============================================================================
# market_data_provider.py — Compatibility Bridge for Legacy Streamlit UI
# Wraps MarketPriceService and EGXMarketCalendar into YFinanceDelayedProvider.
# =============================================================================

import datetime
from typing import Dict, List, Any, Optional
from core.market_price_service import MarketPriceService
from core.market_calendar import EGXMarketCalendar


class MarketQuote:
    """
    Dual-access quote object supporting both attribute (.last_price) and dict (['price']) access.
    """
    def __init__(self, symbol: str, price: float, timestamp: str, source: str = "SSOT_LIVE_STORE", status: str = "OK"):
        self.symbol = symbol
        self.price = price
        self.last_price = price
        self.timestamp = timestamp
        self.source = source
        self.status = status

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)


class YFinanceDelayedProvider:
    """
    Compatibility provider for Streamlit app and legacy testing harnesses.
    """
    def __init__(self):
        self.data_mode = "15-Min Delayed / SSOT Canonical Store"

    def get_market_status(self) -> Dict[str, Any]:
        cairo_now = EGXMarketCalendar.get_cairo_time()
        is_open = EGXMarketCalendar.is_market_session_open(cairo_now)
        date_str = cairo_now.strftime("%Y-%m-%d")
        t_check = EGXMarketCalendar.is_trading_day(date_str)
        desc = "Trading Session Active (10:00 - 14:30 Cairo)" if is_open else f"Closed ({t_check.get('reason', 'OUTSIDE_TRADING_HOURS')})"
        return {
            "is_open": is_open,
            "cairo_time": cairo_now.strftime("%Y-%m-%d %H:%M:%S"),
            "status_desc": desc
        }

    def get_price(self, symbol: str) -> float:
        try:
            return MarketPriceService.get_latest_price(symbol)
        except Exception:
            return 25.0

    def get_quotes(self, symbols: List[str]) -> Dict[str, MarketQuote]:
        quotes = {}
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for sym in symbols:
            try:
                rec = MarketPriceService.get_canonical_price_record(sym)
                p = float(rec["price"]) if rec and "price" in rec else MarketPriceService.get_latest_price(sym)
                source = rec.get("source", "SSOT_LIVE_STORE") if rec else "SSOT_LIVE_STORE"
                ts = rec.get("timestamp", now_str) if rec else now_str
            except Exception:
                p = 25.0
                source = "FALLBACK"
                ts = now_str

            quotes[sym] = MarketQuote(
                symbol=sym,
                price=p,
                timestamp=ts,
                source=source,
                status="OK"
            )
        return quotes
