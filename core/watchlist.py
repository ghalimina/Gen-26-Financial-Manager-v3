import os
import json
import datetime
import threading
from typing import Dict, List, Any, Optional

from core.pit_store import HistoricalTradableUniverse


class WatchlistManager:
    """
    Persistent watchlist manager for tracking candidate securities.
    """
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    WATCHLIST_FILE = os.path.join(DATA_DIR, "user_watchlist.json")
    _WATCHLIST_LOCK = threading.RLock()

    @classmethod
    def get_initial_watchlist(cls) -> Dict[str, Any]:
        """Returns baseline default watchlist."""
        return {
            "version": "3.0.0",
            "last_updated": datetime.datetime.now().isoformat(),
            "tickers": ["COMI.CA", "SWDY.CA", "TMGH.CA", "EKHO.CA", "FWRY.CA"]
        }

    @classmethod
    def load_watchlist(cls) -> Dict[str, Any]:
        """Loads user watchlist from disk."""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        if not os.path.exists(cls.WATCHLIST_FILE):
            data = cls.get_initial_watchlist()
            cls.save_watchlist(data)
            return data
        try:
            with open(cls.WATCHLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return cls.get_initial_watchlist()

    @classmethod
    def save_watchlist(cls, data: Dict[str, Any]):
        """Saves user watchlist atomically with disk sync."""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        data["last_updated"] = datetime.datetime.now().isoformat()
        tmp_f = f"{cls.WATCHLIST_FILE}.tmp"
        with open(tmp_f, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_f, cls.WATCHLIST_FILE)

    @classmethod
    def add_to_watchlist(cls, ticker: str) -> Dict[str, Any]:
        """Adds a valid EGX ticker to the watchlist."""
        with cls._WATCHLIST_LOCK:
            t = ticker.strip().upper()
            if not t.endswith(".CA") and "." not in t:
                t += ".CA"

            # Validate ticker in universe (Supports all 50 active EGX stocks)
            from core.egx_universe_loader import EGXUniverseLoader
            from core.market_price_service import MarketPriceService
            from data.universe_manager import UniverseManager
            canonical_data = MarketPriceService.get_all_canonical_prices()
            canonical_tickers = {r["ticker"] for r in canonical_data if isinstance(r, dict) and "ticker" in r} if isinstance(canonical_data, list) else set(canonical_data.keys())
            all_valid_tickers = set(EGXUniverseLoader.ACTIVE_UNIVERSE.keys()) | canonical_tickers | set(UniverseManager.get_all_tickers())
            if t not in all_valid_tickers:
                return {"success": False, "error": f"السهم {t} غير موجود في الكون الاستثماري المعتمد لبورصة مصر."}

            data = cls.load_watchlist()
            if t in data["tickers"]:
                return {"success": False, "error": f"السهم {t} موجود بالفعل في قائمة المراقبة."}

            data["tickers"].append(t)
            cls.save_watchlist(data)
            return {"success": True, "message": f"تمت إضافة {t} إلى قائمة المراقبة بنجاح.", "tickers": data["tickers"]}

    @classmethod
    def remove_from_watchlist(cls, ticker: str) -> Dict[str, Any]:
        """Removes a ticker from the watchlist."""
        with cls._WATCHLIST_LOCK:
            t = ticker.strip().upper()
            data = cls.load_watchlist()
            if t not in data["tickers"]:
                return {"success": False, "error": f"السهم {t} غير موجود في قائمة المراقبة."}

            data["tickers"].remove(t)
            cls.save_watchlist(data)
            return {"success": True, "message": f"تم حذف {t} من قائمة المراقبة.", "tickers": data["tickers"]}

    @classmethod
    def get_watchlist_details(
        cls,
        current_prices: Optional[Dict[str, float]] = None,
        alpha_scores: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """Returns rich details for all watchlisted tickers."""
        from core.market_price_service import MarketPriceService
        data = cls.load_watchlist()
        prices = current_prices or {}
        alphas = alpha_scores or {"COMI.CA": 90.0, "SWDY.CA": 85.0, "TMGH.CA": 82.0, "EKHO.CA": 78.0, "FWRY.CA": 74.0}

        items = []
        for t in data.get("tickers", []):
            if t in prices:
                cp = prices[t]
            else:
                try:
                    cp = MarketPriceService.get_latest_price(t)
                except Exception:
                    cp = 50.0
            score = alphas.get(t, 60.0)
            target = round(cp * 1.15, 2)
            stop = round(cp * 0.93, 2)

            rec = "شراء تراجعي" if score >= 80 else ("مراقبة" if score >= 65 else "تجنب")
            items.append({
                "ticker": t,
                "current_price": cp,
                "model_score": score,
                "target_price": target,
                "stop_loss": stop,
                "expected_return_pct": 15.0,
                "recommendation": rec
            })
        return items
