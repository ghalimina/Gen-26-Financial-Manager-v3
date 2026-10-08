#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/gdr_arbitrage_engine.py — London GDR Lead-Lag Arbitrage Engine
# Tracks Egyptian Global Depository Receipts (GDRs) traded on London Stock Exchange (LSE)
# to forecast overnight opening price gaps on EGX at 10:00 AM Cairo Time.
# =============================================================================

import os
import sys
import time
import json
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
            "cairo_currency": "USD",
            "benchmark_gdr_usd": 0.85
        }
    }

    _GDR_CACHE: Dict[str, float] = {}
    _GDR_CACHE_TIME: Dict[str, float] = {}
    CACHE_TTL_SECONDS: float = 3600.0

    @classmethod
    def fetch_live_gdr_price(cls, gdr_ticker: str) -> float:
        """
        Fetches live or latest close USD price for a London GDR via yfinance with resilient fallback and caching.
        Prioritizes authoritative 5d daily close over intraday/fast_info zero-volume anomalies.
        """
        sym_clean = gdr_ticker.upper().strip()
        now = time.time()
        if sym_clean in cls._GDR_CACHE and (now - cls._GDR_CACHE_TIME.get(sym_clean, 0.0)) < cls.CACHE_TTL_SECONDS:
            return cls._GDR_CACHE[sym_clean]

        # Fast-path fallback for delisted or illiquid GDRs
        if sym_clean in ("ETEL.L", "EKHO.L", "UNKNOWN.L"):
            for cairo_sym, meta in cls.GDR_REGISTRY.items():
                if meta["gdr_ticker"] == sym_clean:
                    val = float(meta["benchmark_gdr_usd"])
                    cls._GDR_CACHE[sym_clean] = val
                    cls._GDR_CACHE_TIME[sym_clean] = now
                    return val
            return 2.50

        try:
            import yfinance as yf
            ticker_obj = yf.Ticker(sym_clean)
            
            # 1. Primary authoritative source: 5-day daily close history
            hist = ticker_obj.history(period="5d")
            if not hist.empty and "Close" in hist.columns:
                valid_closes = hist["Close"].dropna()
                if not valid_closes.empty:
                    val = float(valid_closes.iloc[-1])
                    if val > 0:
                        val = round(val, 3)
                        cls._GDR_CACHE[sym_clean] = val
                        cls._GDR_CACHE_TIME[sym_clean] = now
                        return val

            # 2. Secondary fallback: regularMarketPreviousClose from fast_info
            fast_info = getattr(ticker_obj, "fast_info", None)
            if fast_info:
                prev_close = None
                try:
                    prev_close = fast_info.get("regularMarketPreviousClose", None)
                except Exception:
                    pass
                if prev_close and float(prev_close) > 0:
                    val = round(float(prev_close), 3)
                    cls._GDR_CACHE[sym_clean] = val
                    cls._GDR_CACHE_TIME[sym_clean] = now
                    return val
        except Exception as e:
            logger.debug(f"yfinance fetch for GDR {sym_clean} returned fallback: {e}")

        # Fallback to benchmark
        for cairo_sym, meta in cls.GDR_REGISTRY.items():
            if meta["gdr_ticker"] == sym_clean:
                val = float(meta["benchmark_gdr_usd"])
                cls._GDR_CACHE[sym_clean] = val
                cls._GDR_CACHE_TIME[sym_clean] = now
                return val

        cls._GDR_CACHE[sym_clean] = 2.50
        cls._GDR_CACHE_TIME[sym_clean] = now
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
        2. Spread (%) = ((Implied - Cairo) / Cairo) * 100 with strict currency unit parity
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
            "cairo_currency": "EGP",
            "benchmark_gdr_usd": 2.50
        })

        target_gdr = gdr_ticker or meta["gdr_ticker"]
        ratio = shares_per_gdr or meta["shares_per_gdr"]

        # 1. Fetch USD/EGP rate
        usd_rate = live_usd_egp or MacroEconomicEngine.fetch_usd_egp()
        if usd_rate <= 0:
            usd_rate = 50.20

        # Determine Cairo trading currency (handle dual-currency equities like EKHO.CA)
        canon = MarketPriceService.CANONICAL_PRICES.get(sym_clean, {})
        cairo_currency = meta.get("cairo_currency")
        if not cairo_currency:
            if sym_clean in ["EKHO.CA", "EKHOA.CA"] or canon.get("currency") == "USD" or "دولار" in canon.get("company_name", ""):
                cairo_currency = "USD"
            else:
                cairo_currency = "EGP"

        # 2. Fetch Cairo price (in its native trading currency)
        if override_cairo_price and override_cairo_price > 0:
            cairo_raw_price = float(override_cairo_price)
        else:
            cairo_raw_price = float(canon.get("price", 10.0))
            if cairo_raw_price <= 0:
                cairo_raw_price = 10.0

        # Normalise Cairo prices into both USD and EGP
        # Auto-detect if raw price is in USD (e.g. EKHO traded at $0.67 USD)
        if cairo_currency == "USD" or (cairo_raw_price < 2.5 and sym_clean.startswith("EKHO")):
            cairo_currency = "USD"
            cairo_price_usd = cairo_raw_price
            cairo_price_egp = round(cairo_raw_price * usd_rate, 2)
        else:
            cairo_price_egp = cairo_raw_price
            cairo_price_usd = round(cairo_raw_price / max(usd_rate, 1.0), 3)

        # 3. Fetch London GDR USD price
        if override_gdr_price and override_gdr_price > 0:
            gdr_usd = float(override_gdr_price)
        else:
            gdr_usd = cls.fetch_live_gdr_price(target_gdr)

        # 4. Implied Cairo price calculation per local share
        implied_usd = round(gdr_usd / max(ratio, 0.01), 3)
        implied_egp = round((gdr_usd * usd_rate) / max(ratio, 0.01), 2)

        # 5. Spread calculation with guaranteed dimensional currency parity
        if cairo_currency == "USD":
            # Direct USD vs USD comparison (both London GDR and Cairo share trade in USD)
            spread_pct = round(((implied_usd - cairo_price_usd) / cairo_price_usd) * 100.0, 2)
            cairo_display = f"{cairo_price_usd:.2f} $ (معادل {cairo_price_egp:.2f} ج.م)"
        else:
            # EGP vs EGP comparison
            spread_pct = round(((implied_egp - cairo_price_egp) / cairo_price_egp) * 100.0, 2)
            cairo_display = f"{cairo_price_egp:.2f} ج.م"

        # 6. Overnight gap classification
        if spread_pct >= 2.0:
            signal = "OVERNIGHT_GDR_BULLISH_GAP"
            sentiment = "BULLISH"
            action_ar = (
                f"🟢 فجوة صاعدة متوقعة لافتتاح القاهرة (+{spread_pct:.1f}%): شهادة لندن تتداول بعلاوة سعرية "
                f"(معادل {implied_egp:.2f} ج.م مقابل {cairo_display} في القاهرة)؛ فرصة شراء على الافتتاح."
            )
        elif spread_pct <= -2.0:
            signal = "OVERNIGHT_GDR_BEARISH_GAP"
            sentiment = "BEARISH"
            action_ar = (
                f"🔴 فجوة هابطة متوقعة لافتتاح القاهرة ({spread_pct:.1f}%): شهادة لندن تتداول بخصم سعري "
                f"(معادل {implied_egp:.2f} ج.م مقابل {cairo_display} في القاهرة)؛ يوصى بالحذر وتجنب الشراء المبكر."
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
            "cairo_price_egp": cairo_price_egp,
            "cairo_price_usd": cairo_price_usd,
            "cairo_currency": cairo_currency,
            "gdr_price_usd": round(gdr_usd, 3),
            "usd_egp_rate": round(usd_rate, 2),
            "shares_per_gdr": ratio,
            "implied_cairo_egp": implied_egp,
            "implied_cairo_usd": implied_usd,
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

    # Class method alias
    evaluate_all_gdrs = scan_all_gdr_pairs

    @classmethod
    def sync_evening_lse_gdr_closes(cls) -> Dict[str, Any]:
        """
        Evening LSE Sync (6:30 PM Cairo Time / 16:30 GMT):
        Pulls London closing prices for CBKD.L, EFGD.L, ETEL.L,
        calculates implied USD/EGP rates, arbitrage spreads, and forecasts
        the next morning (10:00 AM) Cairo opening gaps.
        """
        import datetime
        now = datetime.datetime.now()
        usd_rate = MacroEconomicEngine.fetch_usd_egp()
        gdr_pairs = cls.scan_all_gdr_pairs()

        # Build telemetry for key pairs
        evening_sync_records = []
        cairo_gap_forecasts = []

        for p in gdr_pairs:
            cairo_p = float(p.get("cairo_price_egp", 0.0))
            gdr_usd = float(p.get("gdr_price_usd", 0.0))
            ratio = float(p.get("shares_per_gdr", 1.0))

            implied_fx = round((cairo_p * ratio) / max(gdr_usd, 0.01), 2) if gdr_usd > 0 else usd_rate
            spread_pct = float(p.get("spread_pct", 0.0))

            if spread_pct >= 1.5:
                gap_dir = "BULLISH_GAP"
                gap_ar = f"فجوة افتتاح صاعدة (+{spread_pct:.1f}%)"
            elif spread_pct <= -1.5:
                gap_dir = "BEARISH_GAP"
                gap_ar = f"فجوة افتتاح هابطة ({spread_pct:.1f}%)"
            else:
                gap_dir = "NEUTRAL_OPEN"
                gap_ar = f"افتتاح مستقر ({spread_pct:+.1f}%)"

            rec = {
                "cairo_ticker": p["cairo_ticker"],
                "gdr_ticker": p["gdr_ticker"],
                "name_ar": p["name_ar"],
                "lse_close_usd": gdr_usd,
                "cairo_close_egp": cairo_p,
                "official_usd_egp": usd_rate,
                "implied_gdr_usd_egp": implied_fx,
                "arbitrage_spread_pct": spread_pct,
                "next_morning_gap_direction": gap_dir,
                "next_morning_gap_label_ar": gap_ar,
                "action_guidance_ar": p.get("action_guidance_ar")
            }
            evening_sync_records.append(rec)
            cairo_gap_forecasts.append(f"{p['name_ar']}: {gap_ar}")

        # Update historical log in data/gdr_spread_history.json
        history_path = os.path.join(WORKSPACE, "data", "gdr_spread_history.json")
        try:
            history = []
            if os.path.exists(history_path) and os.path.getsize(history_path) > 2:
                with open(history_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            history.append({
                "sync_timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                "cairo_time": "18:30:00 (LSE Evening Close)",
                "official_usd_egp": usd_rate,
                "records": evening_sync_records
            })
            # Keep latest 60 sync snapshots
            history = history[-60:]
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Could not persist gdr_spread_history: {e}")

        summary_text = (
            f"تم إغلاق جلسة لندن (6:30 م القاهرة): "
            f"سعر الصرف الرسمي {usd_rate:.2f} ج | "
            + " — ".join(cairo_gap_forecasts[:3])
        )

        return {
            "status": "SUCCESS",
            "sync_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "market_session": "LSE_POST_CLOSE_SYNC_1830",
            "official_usd_egp": usd_rate,
            "headline_summary_ar": summary_text,
            "count": len(evening_sync_records),
            "evening_records": evening_sync_records
        }
