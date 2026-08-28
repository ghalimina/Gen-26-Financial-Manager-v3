#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/gdr_arbitrage_engine.py — London GDR Lead-Lag Arbitrage Engine
# Tracks Egyptian Global Depository Receipts (GDRs) traded on London Stock Exchange (LSE)
# to forecast overnight opening price gaps on EGX at 10:00 AM Cairo Time.
# =============================================================================

import os
import sys
import logging
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.market_price_service import MarketPriceService
from core.macro_economic_engine import MacroEconomicEngine

logger = logging.getLogger("GEN26.GDRArbitrageEngine")


class GDRArbitrageEngine:
    """
    London-Cairo GDR Lead-Lag Arbitrage Engine.
    Tracks LSE depository receipts and calculates USD implied EGP arbitrage parity.
    """

    # Authoritative London GDR to Cairo Equities Mapping
    GDR_REGISTRY: Dict[str, Dict[str, Any]] = {
        "COMI.CA": {
            "gdr_ticker": "CBKD.L",
            "name_ar": "البنك التجاري الدولي (CIB GDR)",
            "shares_per_gdr": 1.0,
            "currency": "USD",
            "benchmark_gdr_usd": 2.80
        },
        "ETEL.CA": {
            "gdr_ticker": "ETEL.L",
            "name_ar": "المصرية للاتصالات (Telecom Egypt GDR)",
            "shares_per_gdr": 5.0,
            "currency": "USD",
            "benchmark_gdr_usd": 3.65
        },
        "HRHO.CA": {
            "gdr_ticker": "EFGD.L",
            "name_ar": "إي إف جي هيرميس (EFG Hermes GDR)",
            "shares_per_gdr": 2.0,
            "currency": "USD",
            "benchmark_gdr_usd": 1.05
        },
        "EKHO.CA": {
            "gdr_ticker": "EKHO.L",
            "name_ar": "القابضة المصرية الكويتية (EK Holding GDR)",
            "shares_per_gdr": 1.0,
            "currency": "USD",
            "benchmark_gdr_usd": 0.85
        }
    }

    @classmethod
    def fetch_live_gdr_price(cls, gdr_ticker: str) -> float:
        """
        Fetches live or latest close USD price for a London GDR via yfinance with resilient fallback.
        """
        sym_clean = gdr_ticker.upper().strip()
        try:
            import yfinance as yf
            ticker_obj = yf.Ticker(sym_clean)
            fast_info = getattr(ticker_obj, "fast_info", None)
            if fast_info:
                last_price = getattr(fast_info, "last_price", None) or getattr(fast_info, "regular_market_price", None)
                if last_price and float(last_price) > 0:
                    return round(float(last_price), 3)

            hist = ticker_obj.history(period="5d")
            if not hist.empty and "Close" in hist.columns:
                val = hist["Close"].dropna().iloc[-1]
                if float(val) > 0:
                    return round(float(val), 3)
        except Exception as e:
            logger.debug(f"yfinance fetch for GDR {sym_clean} returned fallback: {e}")

        # Fallback to benchmark
        for cairo_sym, meta in cls.GDR_REGISTRY.items():
            if meta["gdr_ticker"] == sym_clean:
                return float(meta["benchmark_gdr_usd"])

        return 2.50

    @classmethod
    def calculate_gdr_premium(
        cls,
        cairo_ticker: str,
        gdr_ticker: Optional[str] = None,
        shares_per_gdr: Optional[float] = None,
        live_usd_egp: Optional[float] = None,
        override_cairo_price: Optional[float] = None,
        override_gdr_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculates GDR Arbitrage Parity:
        1. Implied EGP Price = (GDR_Price_USD * USD_EGP) / shares_per_gdr
        2. Spread (%) = ((Implied_EGP - Cairo_Price) / Cairo_Price) * 100
        3. Opening Gap Forecast:
           - Spread >= +2.0% -> OVERNIGHT_GDR_BULLISH_GAP
           - Spread <= -2.0% -> OVERNIGHT_GDR_BEARISH_GAP
           - Else -> GDR_PARITY_NEUTRAL
        """
        sym_clean = cairo_ticker.upper().strip()
        if not sym_clean.endswith(".CA") and "." not in sym_clean:
            sym_clean = f"{sym_clean}.CA"

        meta = cls.GDR_REGISTRY.get(sym_clean, {
            "gdr_ticker": gdr_ticker or "UNKNOWN.L",
            "name_ar": sym_clean,
            "shares_per_gdr": shares_per_gdr or 1.0,
            "currency": "USD",
            "benchmark_gdr_usd": 2.50
        })

        target_gdr = gdr_ticker or meta["gdr_ticker"]
        ratio = shares_per_gdr or meta["shares_per_gdr"]

        # 1. Fetch USD/EGP rate
        usd_rate = live_usd_egp or MacroEconomicEngine.fetch_usd_egp()
        if usd_rate <= 0:
            usd_rate = 50.20

        # 2. Fetch Cairo price
        if override_cairo_price and override_cairo_price > 0:
            cairo_price = float(override_cairo_price)
        else:
            canon = MarketPriceService.CANONICAL_PRICES.get(sym_clean, {})
            cairo_price = float(canon.get("price", 10.0))
            if cairo_price <= 0:
                cairo_price = 10.0

        # 3. Fetch London GDR USD price
        if override_gdr_price and override_gdr_price > 0:
            gdr_usd = float(override_gdr_price)
        else:
            gdr_usd = cls.fetch_live_gdr_price(target_gdr)

        # 4. Implied EGP price calculation
        implied_egp = round((gdr_usd * usd_rate) / max(ratio, 0.01), 2)

        # 5. Spread calculation
        spread_pct = round(((implied_egp - cairo_price) / cairo_price) * 100.0, 2)

        # 6. Overnight gap classification
        if spread_pct >= 2.0:
            signal = "OVERNIGHT_GDR_BULLISH_GAP"
            sentiment = "BULLISH"
            action_ar = (
                f"🟢 فجوة صاعدة متوقعة لافتتاح القاهرة (+{spread_pct:.1f}%): شهادة لندن تتداول بعلاوة سعرية "
                f"(معادل {implied_egp:.2f} ج.م مقابل {cairo_price:.2f} ج.م في القاهرة)؛ فرصة شراء على الافتتاح."
            )
        elif spread_pct <= -2.0:
            signal = "OVERNIGHT_GDR_BEARISH_GAP"
            sentiment = "BEARISH"
            action_ar = (
                f"🔴 فجوة هابطة متوقعة لافتتاح القاهرة ({spread_pct:.1f}%): شهادة لندن تتداول بخصم سعري "
                f"(معادل {implied_egp:.2f} ج.م مقابل {cairo_price:.2f} ج.م في القاهرة)؛ يوصى بالحذر وتجنب الشراء المبكر."
            )
        else:
            signal = "GDR_PARITY_NEUTRAL"
            sentiment = "NEUTRAL"
            action_ar = (
                f"⚪ توازن سعري بين بورصتي القاهرة ولندن (الفارق {spread_pct:+.1f}%): "
                f"الأسعار متطابقة مع السعر العادل لصرف العملة."
            )

        return {
            "cairo_ticker": sym_clean,
            "gdr_ticker": target_gdr,
            "name_ar": meta.get("name_ar", sym_clean),
            "cairo_price_egp": round(cairo_price, 2),
            "gdr_price_usd": round(gdr_usd, 3),
            "usd_egp_rate": round(usd_rate, 2),
            "shares_per_gdr": ratio,
            "implied_cairo_egp": implied_egp,
            "spread_pct": spread_pct,
            "arbitrage_signal": signal,
            "sentiment": sentiment,
            "action_guidance_ar": action_ar
        }

    @classmethod
    def scan_all_gdr_pairs(cls) -> List[Dict[str, Any]]:
        """
        Scans all registered Egyptian GDRs and returns comparative arbitrage opportunities.
        """
        results = []
        usd_rate = MacroEconomicEngine.fetch_usd_egp()

        for cairo_sym, meta in cls.GDR_REGISTRY.items():
            analysis = cls.calculate_gdr_premium(
                cairo_ticker=cairo_sym,
                gdr_ticker=meta["gdr_ticker"],
                shares_per_gdr=meta["shares_per_gdr"],
                live_usd_egp=usd_rate
            )
            results.append(analysis)

        return results
