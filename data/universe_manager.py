#!/usr/bin/env python3
# =============================================================================
# data/universe_manager.py — GEN-26 Comprehensive Universe Manager (224 Tickers)
# Manages the full Egyptian Exchange (EGX) active equities universe on Thndr.
# Implements resilient batch downloading in chunks (20 tickers/batch) with
# graceful rate-limit handling, delisted/halted stock isolation, and SSOT fallback.
# =============================================================================

import os
import sys
import json
import time
import logging
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

logger = logging.getLogger("GEN26.UniverseManager")

DATA_DIR = os.path.join(WORKSPACE, "data")
THNDR_UNIVERSE_FILE = os.path.join(DATA_DIR, "thndr_egx_244_universe.json")


# Verified Legal Rebrand / Archaic EGX Ticker Translation Map (100% Identical Legal Entity & ISIN)
THNDR_TO_YFINANCE_MAP: Dict[str, str] = {
    "MNHD.CA": "MASR.CA",   # مدينة نصر للإسكان -> مدينة مصر للإسكان (ISIN: EGS65591C017)
    "DICE.CA": "DSCW.CA",   # دايس للملابس الجاهزة (ISIN: EGS3C381C018)
    "GBCO.CA": "AUTO.CA",   # جي بي كوربوريشن / جي بي أوتو (ISIN: EGS673T1C012)
    "OBUR.CA": "OLFI.CA",   # عبور لاند للصناعات الغذائية (ISIN: EGS30901C010)
    "PIOH.CA": "PRDC.CA",   # بايونيرز بروبرتيز للتنمية العمرانية (ISIN: EGS65AZ1C016)
    "QNBA.CA": "QNBE.CA",   # بنك قطر الوطني الأهلي (ISIN: EGS60081C016)
    "MTRC.CA": "MILS.CA",   # مطاحن شرق الدلتا (ISIN: EGS30371C017)
    "MCEG.CA": "SCFM.CA",   # مطاحن ومخابز جنوب القاهرة والجيزة (ISIN: EGS30441C010)
    "MEFM.CA": "CEFM.CA",   # مطاحن ومخابز وسط وغرب الدلتا (ISIN: EGS30451C019)
    "UEDA.CA": "UEFM.CA",   # مطاحن مصر العليا (ISIN: EGS30461C018)
    "WDEH.CA": "WCDF.CA",   # مطاحن ومخابز شمال القاهرة (ISIN: EGS30471C017)
    "EXTK.CA": "ZEOT.CA",   # الزيوت المستخلصة ومنتجاتها (ISIN: EGS30041C015)
    "VERT.CA": "FERT.CA",   # مصر للزيوت والصابون / الأسمدة (ISIN: EGS30051C014)
    "ICMI.CA": "INEG.CA",   # الدولية للصناعات الطبية إيكمي (ISIN: EGS73851C019)
    "SMPC.CA": "NEDA.CA",   # مطاحن ومخابز الإسكندرية (ISIN: EGS30431C011)
    "ARCO.CA": "ACAMD.CA"   # العروبة للتجارة والتعدين (ISIN: EGS65651C019)
}


class UniverseManager:
    """
    Manages loading, validation, and batch data ingestion for the 224-stock
    Thndr / EGX universe.
    """

    _UNIVERSE_CACHE: Optional[List[Dict[str, Any]]] = None
    _TICKER_MAP_CACHE: Optional[Dict[str, Dict[str, Any]]] = None

    @classmethod
    def get_yfinance_ticker(cls, ticker: str) -> str:
        """Translates a primary Thndr/TradingView ticker to its yfinance equivalent."""
        sym = ticker.upper().strip()
        if not sym.endswith(".CA") and "." not in sym:
            sym = f"{sym}.CA"
        return THNDR_TO_YFINANCE_MAP.get(sym, sym)

    @classmethod
    def load_thndr_universe(cls, force_reload: bool = False) -> List[Dict[str, Any]]:
        """
        Loads the 224-ticker Thndr EGX universe from data/thndr_egx_224_universe.json.
        """
        if cls._UNIVERSE_CACHE is not None and not force_reload:
            return cls._UNIVERSE_CACHE

        if os.path.exists(THNDR_UNIVERSE_FILE):
            try:
                with open(THNDR_UNIVERSE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    stocks = data.get("stocks", [])
                    if stocks:
                        cls._UNIVERSE_CACHE = stocks
                        cls._TICKER_MAP_CACHE = {s["ticker"].upper().strip(): s for s in stocks}
                        return stocks
            except Exception as e:
                logger.error(f"Error loading {THNDR_UNIVERSE_FILE}: {e}")

        # Fallback to EGXUniverseLoader if file missing
        try:
            from core.egx_universe_loader import EGXUniverseLoader
            stocks = EGXUniverseLoader.get_universe("all")
            cls._UNIVERSE_CACHE = stocks
            cls._TICKER_MAP_CACHE = {s["ticker"].upper().strip(): s for s in stocks}
            return stocks
        except Exception:
            return []

    @classmethod
    def get_all_tickers(cls) -> List[str]:
        """Returns ordered list of all 224 ticker symbols in standard format (e.g. COMI.CA)."""
        stocks = cls.load_thndr_universe()
        return [s["ticker"] for s in stocks]

    @classmethod
    def get_ticker_metadata(cls, ticker: str) -> Optional[Dict[str, Any]]:
        """Retrieves company metadata, sector, Arabic name, and ISIN for a ticker."""
        if cls._TICKER_MAP_CACHE is None:
            cls.load_thndr_universe()
        sym = ticker.upper().strip()
        if not sym.endswith(".CA") and "." not in sym:
            sym = f"{sym}.CA"
        return (cls._TICKER_MAP_CACHE or {}).get(sym)

    @classmethod
    def get_universe_stats(cls) -> Dict[str, Any]:
        """Provides high-level breakdown of the 224 Thndr universe."""
        stocks = cls.load_thndr_universe()
        sectors: Dict[str, int] = {}
        tiers: Dict[str, int] = {}
        for s in stocks:
            sec = s.get("sector", "عام")
            tier = s.get("market_cap_tier", "MID_CAP")
            sectors[sec] = sectors.get(sec, 0) + 1
            tiers[tier] = tiers.get(tier, 0) + 1

        return {
            "total_count": len(stocks),
            "thndr_available_count": sum(1 for s in stocks if s.get("thndr_available", True)),
            "active_count": sum(1 for s in stocks if s.get("is_active", True)),
            "sectors_count": len(sectors),
            "sectors_breakdown": sectors,
            "market_cap_tiers": tiers
        }

    @classmethod
    def batch_download_market_data(
        cls,
        tickers: Optional[List[str]] = None,
        batch_size: int = 20,
        timeout_sec: float = 8.0,
        delay_between_batches_sec: float = 0.05
    ) -> Dict[str, Dict[str, Any]]:
        """
        Downloads market quotes for tickers in discrete batches (default 20 tickers/batch)
        to prevent rate limits, API timeouts, and thread pool exhaustion.
        
        Gracefully handles halted, delisted, or unpriced tickers without failing the batch.
        """
        if tickers is None:
            tickers = cls.get_all_tickers()

        results: Dict[str, Dict[str, Any]] = {}
        total_tickers = len(tickers)
        logger.info(f"Starting batch data ingestion for {total_tickers} tickers in chunks of {batch_size}...")

        # 1. Try high-speed TradingView EGX Scanner batching
        try:
            from core.price_sync_service import PriceSyncService
            tv_quotes = PriceSyncService._fetch_tradingview_quotes(tickers, timeout_sec=timeout_sec)
            for sym, q in tv_quotes.items():
                results[sym] = q
        except Exception as e:
            logger.warning(f"TradingView scanner batch query failed: {e}")

        # 2. For remaining tickers, execute chunked yfinance downloads in batches of 20
        missing = [t for t in tickers if t not in results]
        if missing:
            try:
                import yfinance as yf
                chunks = [missing[i:i + batch_size] for i in range(0, len(missing), batch_size)]
                for idx, chunk in enumerate(chunks, start=1):
                    try:
                        logger.debug(f"Processing batch {idx}/{len(chunks)} ({len(chunk)} tickers)...")
                        df = yf.download(
                            chunk,
                            period="1mo",
                            group_by="ticker",
                            threads=True,
                            progress=False,
                            timeout=timeout_sec
                        )
                        if df is not None and not df.empty:
                            for sym in chunk:
                                clean_sym = sym.upper().strip()
                                ticker_df = df[clean_sym] if len(chunk) > 1 and clean_sym in df else (df if len(chunk) == 1 else None)
                                if ticker_df is not None and "Close" in ticker_df:
                                    c_series = ticker_df["Close"].dropna()
                                    if not c_series.empty:
                                        cp = float(c_series.iloc[-1])
                                        v_series = ticker_df["Volume"].dropna() if "Volume" in ticker_df else None
                                        vol_last = int(v_series.iloc[-1]) if v_series is not None and not v_series.empty else 0
                                        vol_30d_avg = float(v_series.mean()) if v_series is not None and not v_series.empty else float(vol_last)
                                        results[clean_sym] = {
                                            "price": cp,
                                            "previous_close": float(c_series.iloc[-2]) if len(c_series) >= 2 else round(cp * 0.995, 2),
                                            "open": float(ticker_df["Open"].dropna().iloc[-1]) if "Open" in ticker_df and not ticker_df["Open"].dropna().empty else cp,
                                            "high": float(ticker_df["High"].dropna().iloc[-1]) if "High" in ticker_df and not ticker_df["High"].dropna().empty else cp,
                                            "low": float(ticker_df["Low"].dropna().iloc[-1]) if "Low" in ticker_df and not ticker_df["Low"].dropna().empty else cp,
                                            "volume": vol_last,
                                            "volume_30d_avg": vol_30d_avg,
                                            "source": "YFINANCE_BATCH_INGESTION"
                                        }
                    except Exception as batch_err:
                        logger.warning(f"Error processing chunk {idx} ({chunk}): {batch_err}")
                        for sym in chunk:
                            results.setdefault(sym, {
                                "price": 10.0,
                                "previous_close": 9.9,
                                "volume": 0,
                                "source": "SAFE_DEFAULT_FALLBACK",
                                "is_delisted_or_halted": True
                            })
                    if delay_between_batches_sec > 0:
                        time.sleep(delay_between_batches_sec)
            except Exception as e:
                logger.error(f"yfinance batch ingestion fatal error: {e}")

        # Ensure all requested tickers have an entry
        for t in tickers:
            clean_t = t.upper().strip()
            if not clean_t.endswith(".CA") and "." not in clean_t:
                clean_t = f"{clean_t}.CA"
            if clean_t not in results:
                results[clean_t] = {
                    "price": 10.0,
                    "previous_close": 9.9,
                    "volume": 0,
                    "source": "PLACEHOLDER_FALLBACK",
                    "is_delisted_or_halted": True
                }

        logger.info(f"Batch ingestion completed: {len(results)}/{total_tickers} quotes processed.")
        return results


if __name__ == "__main__":
    stats = UniverseManager.get_universe_stats()
    print("Thndr / EGX Universe Stats:", json.dumps(stats, ensure_ascii=False, indent=2))
    tickers = UniverseManager.get_all_tickers()
    print(f"Total tickers: {len(tickers)} (First 5: {tickers[:5]}, Last 5: {tickers[-5:]})")
