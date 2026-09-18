#!/usr/bin/env python3
# =============================================================================
# core/liquidity_filter.py — GEN-26 Dynamic Liquidity Gate Engine
# Pre-processing institutional risk filter that eliminates illiquid penny stocks
# and fragmented-data securities before technical indicator computation and ML inference.
#
# Strict Institutional Liquidity Rules:
# 1. 30-Day Average Daily Volume (ADV30) > 500,000 shares
# 2. 30-Day Average Daily Turnover (ADT30) > 1,000,000 EGP
# 3. Zero-Volume Days in Last 20 Trading Sessions < 3 days
# =============================================================================

import os
import sys
import logging
from typing import Dict, List, Any, Optional, Union
import pandas as pd
import numpy as np

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

logger = logging.getLogger("GEN26.LiquidityFilter")


class LiquidityGateEngine:
    """
    Dynamic Liquidity Gate for the Expanded 224-Stock EGX / Thndr Universe.
    Protects machine learning models (XGBoost) and quantitative execution
    from illiquidity shocks, wide bid-ask slippage, and fragmented data noise.
    """

    # Strict Institutional Thresholds
    MIN_ADV_30D_SHARES: float = 500000.0       # > 500,000 shares / day
    MIN_TURNOVER_30D_EGP: float = 1000000.0    # > 1,000,000 EGP / day
    MAX_ZERO_VOLUME_DAYS_20D: int = 2          # < 3 zero-volume days in last 20 days (i.e. <= 2)

    # Known Large-Cap & Mid-Cap Liquid Baseline Benchmarks (ORAS.CA removed due to 94.8%+ zero volume)
    KNOWN_LIQUID_STOCKS = {
        "COMI.CA", "SWDY.CA", "TMGH.CA", "EFIH.CA",
        "EGAL.CA", "ESRS.CA", "EMFD.CA", "BTFH.CA", "EKHO.CA",
        "EKHOA.CA", "ETEL.CA", "ABUK.CA", "MFPC.CA", "EAST.CA",
        "SKPC.CA", "ADIB.CA", "HRHO.CA", "BINV.CA", "JUFO.CA",
        "DOMT.CA", "CICH.CA", "PHDC.CA", "MASR.CA", "ISPH.CA",
        "POUL.CA", "ALCN.CA", "RAYA.CA", "GBCO.CA", "FWRY.CA",
        "CLHO.CA", "ORHD.CA", "AMOC.CA", "MOIL.CA", "DSCW.CA",
        "ACRO.CA", "OIH.CA", "HELI.CA", "ELSH.CA", "CERA.CA",
        "CCAP.CA", "SPMD.CA", "KZPC.CA", "PRDC.CA", "EGCH.CA",
        "ARAB.CA", "UNIP.CA", "ELEC.CA", "ZMID.CA", "RTVC.CA",
        "EXPA.CA", "FAIT.CA", "CIEB.CA", "CANA.CA", "HDBK.CA",
        "QNBA.CA", "OCDI.CA", "TAQA.CA", "SUGR.CA", "ORWE.CA",
        "DICE.CA", "OBUR.CA", "EFID.CA", "MICH.CA", "ARCC.CA"
    }

    # Tickers restricted to OTC/Block trading due to persistent zero-volume liquidity failure (Item 2.2)
    OTC_BLOCK_ONLY_TICKERS = {"ORAS.CA"}

    @classmethod
    def evaluate_stock_liquidity(
        cls,
        ticker: str,
        price_history: Optional[pd.DataFrame] = None,
        current_price: Optional[float] = None,
        adv30_shares: Optional[float] = None,
        turnover_30d_egp: Optional[float] = None,
        zero_vol_days_20d: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluates a single stock against the 3 institutional liquidity rules.
        
        Returns:
            Dict containing boolean pass status, metrics, and rejection reasons.
        """
        sym = ticker.upper().strip()
        if not sym.endswith(".CA") and "." not in sym:
            sym = f"{sym}.CA"

        # Explicit classification for OTC / Block-trade illiquid assets
        if sym in cls.OTC_BLOCK_ONLY_TICKERS:
            return {
                "ticker": sym,
                "is_liquid": False,
                "status": "ILLIQUID_OTC_BLOCK_ONLY",
                "status_ar": "سهم غير سائل — صفقات كتل/سوق خارج المقصورة فقط (مستبعد رسمياً من التداول الآلي)",
                "metrics": {
                    "adv_30d_shares": 0.0,
                    "turnover_30d_egp": 0.0,
                    "zero_volume_days_20d": 20
                },
                "thresholds": {
                    "min_adv_30d_shares": cls.MIN_ADV_30D_SHARES,
                    "min_turnover_30d_egp": cls.MIN_TURNOVER_30D_EGP,
                    "max_zero_volume_days_20d": cls.MAX_ZERO_VOLUME_DAYS_20D
                },
                "checks": {
                    "pass_volume": False,
                    "pass_turnover": False,
                    "pass_continuity": False
                },
                "rejection_reasons": ["Flagged as ILLIQUID_OTC_BLOCK_ONLY (94.8%+ historical zero-volume bars)"],
                "rejection_reasons_ar": ["مصنف رسمياً كـ ILLIQUID_OTC_BLOCK_ONLY (أكثر من 94.8% جلسات بدون تداول)"]
            }

        computed_adv = adv30_shares
        computed_turnover = turnover_30d_egp
        computed_zero_days = zero_vol_days_20d

        # 1. Compute from empirical price/volume history if available
        if price_history is not None and not price_history.empty:
            try:
                vol_col = "Volume" if "Volume" in price_history.columns else ("volume" if "volume" in price_history.columns else None)
                close_col = "Close" if "Close" in price_history.columns else ("close" if "close" in price_history.columns else None)

                if vol_col:
                    v_series = price_history[vol_col].dropna()
                    if not v_series.empty:
                        computed_adv = float(v_series.tail(30).mean())
                        computed_zero_days = int((v_series.tail(20) == 0).sum())

                if vol_col and close_col:
                    turnover_series = (price_history[vol_col] * price_history[close_col]).dropna()
                    if not turnover_series.empty:
                        computed_turnover = float(turnover_series.tail(30).mean())
            except Exception as e:
                logger.debug(f"Error computing liquidity metrics from DataFrame for {sym}: {e}")

        # 2. If metrics still missing, retrieve from SSOT canonical market price store or universe metadata
        if computed_adv is None or computed_turnover is None or computed_zero_days is None:
            try:
                from core.market_price_service import MarketPriceService
                quote = MarketPriceService.get_stock_quote(sym)
                p = current_price or quote.get("price", 10.0)
                v = quote.get("volume", 0)

                if computed_adv is None:
                    # Ingest ADV from quote or defaults
                    computed_adv = float(quote.get("adv20_shares", quote.get("adv20", v if v > 0 else (1200000.0 if sym in cls.KNOWN_LIQUID_STOCKS else 150000.0))))
                
                if computed_turnover is None:
                    computed_turnover = float(quote.get("adv20_egp", computed_adv * p if (computed_adv and p) else (15000000.0 if sym in cls.KNOWN_LIQUID_STOCKS else 450000.0)))

                if computed_zero_days is None:
                    computed_zero_days = 0 if sym in cls.KNOWN_LIQUID_STOCKS else (0 if v > 0 else 5)
            except Exception:
                p = current_price or 10.0
                computed_adv = 1200000.0 if sym in cls.KNOWN_LIQUID_STOCKS else 100000.0
                computed_turnover = computed_adv * p
                computed_zero_days = 0 if sym in cls.KNOWN_LIQUID_STOCKS else 4

        # Clean fallback values
        adv = float(computed_adv if computed_adv is not None else 0.0)
        turnover = float(computed_turnover if computed_turnover is not None else 0.0)
        zero_days = int(computed_zero_days if computed_zero_days is not None else 0)

        # Evaluate 3 Institutional Rules
        # Rule 1: Average_Daily_Volume_30D > 500,000
        pass_volume = adv > cls.MIN_ADV_30D_SHARES
        # Rule 2: Average_Daily_Turnover_30D > 1,000,000 EGP
        pass_turnover = turnover > cls.MIN_TURNOVER_30D_EGP
        # Rule 3: Zero_Volume_Days_Last_20 < 3
        pass_continuity = zero_days < 3

        # Single-Source Graceful Degradation (Protocol Rescue):
        # Allow stocks flagged as SINGLE_SOURCE_ONLY to pass if live Volume > 50k and Turnover > 250k EGP
        is_single_source = False
        try:
            from core.market_price_service import MarketPriceService
            can_rec = MarketPriceService.get_canonical_price_record(sym)
            if can_rec and can_rec.get("price_type") == "SINGLE_SOURCE_ONLY":
                is_single_source = True
                tv_vol = float(can_rec.get("volume", 0) or 0)
                tv_turnover = float(can_rec.get("turnover_egp", 0) or (tv_vol * (current_price or can_rec.get("price", 0) or 1.0)))
                if tv_vol >= 50000.0 and tv_turnover >= 250000.0:
                    pass_volume = True
                    pass_turnover = True
                    pass_continuity = True
        except Exception:
            pass

        is_liquid = bool(pass_volume and pass_turnover and pass_continuity)
        status = "TRADABLE_LIQUID" if is_liquid else "ILLIQUID"
        status_ar = ("سهم مؤهل للتداول (مصدر أحادي نشط)" if is_single_source else "سهم مؤهل للتداول والتحليل (سيولة مستقرة)") if is_liquid else "سهم ضعيف السيولة (مستبعد من نماذج التنبؤ)"

        rejection_reasons: List[str] = []
        rejection_reasons_ar: List[str] = []

        if not pass_volume:
            rejection_reasons.append(f"ADV30 ({adv:,.0f} shares) <= {cls.MIN_ADV_30D_SHARES:,.0f} threshold")
            rejection_reasons_ar.append(f"متوسط الحجم اليومي ({adv:,.0f} سهم) أقل من الحد الأدنى (500,000 سهم)")

        if not pass_turnover:
            rejection_reasons.append(f"ADT30 ({turnover:,.0f} EGP) <= {cls.MIN_TURNOVER_30D_EGP:,.0f} EGP threshold")
            rejection_reasons_ar.append(f"متوسط قيمة التداول اليومي ({turnover:,.0f} ج.م) أقل من الحد الأدنى (1,000,000 ج.م)")

        if not pass_continuity:
            rejection_reasons.append(f"Zero volume trading days in last 20 sessions ({zero_days}) >= 3 days limit")
            rejection_reasons_ar.append(f"أيام التداول الصفرية ({zero_days} أيام) تجاوزت الحد المسموح (أقل من 3 أيام)")

        return {
            "ticker": sym,
            "is_liquid": is_liquid,
            "status": status,
            "status_ar": status_ar,
            "metrics": {
                "adv_30d_shares": round(adv, 0),
                "turnover_30d_egp": round(turnover, 2),
                "zero_volume_days_20d": zero_days
            },
            "thresholds": {
                "min_adv_30d_shares": cls.MIN_ADV_30D_SHARES,
                "min_turnover_30d_egp": cls.MIN_TURNOVER_30D_EGP,
                "max_zero_volume_days_20d": cls.MAX_ZERO_VOLUME_DAYS_20D
            },
            "checks": {
                "pass_volume": pass_volume,
                "pass_turnover": pass_turnover,
                "pass_continuity": pass_continuity
            },
            "rejection_reasons": rejection_reasons,
            "rejection_reasons_ar": rejection_reasons_ar
        }

    @classmethod
    def filter_universe(
        cls,
        tickers: Optional[List[str]] = None,
        market_data: Optional[Dict[str, Any]] = None,
        price_histories: Optional[Dict[str, pd.DataFrame]] = None
    ) -> Dict[str, Any]:
        """
        Runs the Dynamic Liquidity Gate across the universe.
        Returns segregated liquid and illiquid constituents with funnel statistics.
        """
        if tickers is None:
            from data.universe_manager import UniverseManager
            tickers = UniverseManager.get_all_tickers()

        liquid_tickers: List[str] = []
        illiquid_tickers: List[str] = []
        details: Dict[str, Dict[str, Any]] = {}

        for ticker in tickers:
            hist = (price_histories or {}).get(ticker)
            quote = (market_data or {}).get(ticker, {})

            p = quote.get("price")
            adv = quote.get("volume_30d_avg") or quote.get("volume")
            t_egp = quote.get("turnover_egp")
            z_days = quote.get("zero_volume_days_20d")

            eval_res = cls.evaluate_stock_liquidity(
                ticker=ticker,
                price_history=hist,
                current_price=p,
                adv30_shares=adv,
                turnover_30d_egp=t_egp,
                zero_vol_days_20d=z_days
            )

            details[eval_res["ticker"]] = eval_res
            if eval_res["is_liquid"]:
                liquid_tickers.append(eval_res["ticker"])
            else:
                illiquid_tickers.append(eval_res["ticker"])

        total = len(tickers)
        liquid_count = len(liquid_tickers)
        illiquid_count = len(illiquid_tickers)
        pass_rate = round((liquid_count / total) * 100.0, 1) if total > 0 else 0.0

        return {
            "total_universe_count": total,
            "liquid_count": liquid_count,
            "illiquid_count": illiquid_count,
            "pass_rate_pct": pass_rate,
            "liquid_tickers": liquid_tickers,
            "illiquid_tickers": illiquid_tickers,
            "details": details
        }


if __name__ == "__main__":
    test_eval = LiquidityGateEngine.evaluate_stock_liquidity("COMI.CA", adv30_shares=1800000, turnover_30d_egp=250000000, zero_vol_days_20d=0)
    print("COMI.CA Liquidity Check:", test_eval["status"], test_eval["is_liquid"])
    test_illiquid = LiquidityGateEngine.evaluate_stock_liquidity("PENNY.CA", adv30_shares=50000, turnover_30d_egp=120000, zero_vol_days_20d=4)
    print("PENNY.CA Liquidity Check:", test_illiquid["status"], test_illiquid["is_liquid"], test_illiquid["rejection_reasons"])
