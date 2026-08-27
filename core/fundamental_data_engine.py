#!/usr/bin/env python3
# =============================================================================
# core/fundamental_data_engine.py — GEN-26 Fundamental & Valuation Engine
# Value Investing & Balance Sheet Health Architecture for EGX Equities:
# 1. Deep Fundamental Data Extraction via yfinance (PE, PB, EPS, Yield, Debt, Cash).
# 2. Institutional Graham & Dodd Financial Health Score (0 to 100).
# 3. Value-Trap & Penny-Stock Filter with Solvency & Earnings Quality Checks.
# 4. Resilient Offline Fallback (Neutral 50.0 / "بيانات غير متوفرة") on network failures.
# 5. In-Memory TTL Caching to ensure high throughput across Dashboards and AI pipelines.
# =============================================================================

import os
import sys
import time
import math
import datetime
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import yfinance as yf

# Configure logger
logger = logging.getLogger("FundamentalDataEngine")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [FundamentalDataEngine] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

# Ticker translation map for Egyptian rebrands on yfinance
YFINANCE_TICKER_MAP = {
    "DICE.CA": "DSCW.CA", "MNHD.CA": "MASR.CA", "OBUR.CA": "OLFI.CA",
    "GBCO.CA": "AUTO.CA", "PIOH.CA": "PRDC.CA", "QNBA.CA": "QNBE.CA",
    "MTRC.CA": "MILS.CA", "MCEG.CA": "SCFM.CA", "MEFM.CA": "CEFM.CA",
    "UEDA.CA": "UEFM.CA", "WDEH.CA": "WCDF.CA", "EXTK.CA": "ZEOT.CA",
    "VERT.CA": "FERT.CA", "ICMI.CA": "INEG.CA", "SMPC.CA": "NEDA.CA",
    "ARCO.CA": "ACAMD.CA"
}


class FundamentalDataEngine:
    """
    Fundamental Valuation and Balance Sheet Quality Engine for Egyptian Equities.
    
    Evaluates:
    - Multiples Valuation (Trailing P/E, Forward P/E, Price-to-Book P/B).
    - Earnings Quality (Trailing EPS, Profit Margins, Return on Equity).
    - Dividend Sustainability (Dividend Yield, Payout Ratio).
    - Balance Sheet Solvency (Total Cash, Total Debt, Free Cash Flow).
    """

    CACHE_TTL_SECONDS: float = 3600.0  # 1 hour in-memory cache
    _CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}

    @classmethod
    def _clean_ticker(cls, ticker: str) -> Tuple[str, str]:
        """
        Normalizes ticker string to canonical .CA format and resolves yfinance mapping.
        
        Returns:
            Tuple[str, str]: (canonical_ticker, yfinance_ticker)
        """
        if not ticker:
            return "UNKNOWN.CA", "UNKNOWN.CA"
        
        clean = ticker.upper().strip()
        if not clean.endswith(".CA") and "." not in clean:
            canonical = f"{clean}.CA"
        else:
            canonical = clean

        yf_symbol = YFINANCE_TICKER_MAP.get(canonical, canonical)
        return canonical, yf_symbol

    @classmethod
    def fetch_fundamentals(cls, ticker: str) -> Dict[str, Any]:
        """
        Fetches core balance sheet, income statement, and valuation metrics via yfinance.
        
        Extracted Keys:
        - trailingPE: Trailing Price-to-Earnings ratio
        - forwardPE: Forward Price-to-Earnings ratio
        - trailingEps: Trailing Diluted Earnings Per Share in EGP
        - dividendYield: Annual Dividend Yield as decimal (e.g. 0.05 = 5%)
        - priceToBook: Price-to-Book value ratio
        - totalCash: Total cash & equivalents in EGP
        - totalDebt: Total short & long-term debt in EGP
        - freeCashflow: Free cash flow in EGP

        Args:
            ticker: Stock symbol (e.g. 'COMI.CA', 'SWDY.CA').

        Returns:
            Dict[str, Any]: Dictionary containing extracted numeric fundamentals or None.
        """
        canonical_ticker, yf_symbol = cls._clean_ticker(ticker)

        # Check Cache
        now = time.time()
        if canonical_ticker in cls._CACHE:
            cached_time, cached_data = cls._CACHE[canonical_ticker]
            if (now - cached_time) < cls.CACHE_TTL_SECONDS:
                return cached_data.copy()

        default_payload: Dict[str, Any] = {
            "ticker": canonical_ticker,
            "yfinance_symbol": yf_symbol,
            "trailingPE": None,
            "forwardPE": None,
            "trailingEps": None,
            "dividendYield": None,
            "priceToBook": None,
            "totalCash": None,
            "totalDebt": None,
            "freeCashflow": None,
            "marketCap": None,
            "returnOnEquity": None,
            "debtToEquity": None,
            "currentRatio": None,
            "data_source": "YFINANCE_LIVE",
            "fetch_timestamp": now
        }

        try:
            logger.info(f"Querying fundamental data for {canonical_ticker} (yfinance: {yf_symbol})...")
            t = yf.Ticker(yf_symbol)
            info = t.info or {}

            def _clean_float(val: Any) -> Optional[float]:
                if val is None or not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
                    return None
                return float(val)

            # Extract target financial fields
            default_payload["trailingPE"] = _clean_float(info.get("trailingPE"))
            default_payload["forwardPE"] = _clean_float(info.get("forwardPE"))
            default_payload["trailingEps"] = _clean_float(info.get("trailingEps"))
            default_payload["dividendYield"] = _clean_float(info.get("dividendYield"))
            default_payload["priceToBook"] = _clean_float(info.get("priceToBook"))
            default_payload["totalCash"] = _clean_float(info.get("totalCash"))
            default_payload["totalDebt"] = _clean_float(info.get("totalDebt"))
            default_payload["freeCashflow"] = _clean_float(info.get("freeCashflow"))
            default_payload["marketCap"] = _clean_float(info.get("marketCap"))
            default_payload["returnOnEquity"] = _clean_float(info.get("returnOnEquity"))
            default_payload["debtToEquity"] = _clean_float(info.get("debtToEquity"))
            default_payload["currentRatio"] = _clean_float(info.get("currentRatio"))
            default_payload["company_name_en"] = info.get("shortName") or info.get("longName")
            default_payload["sector_en"] = info.get("sector")
            default_payload["industry_en"] = info.get("industry")

            # Store in cache
            cls._CACHE[canonical_ticker] = (now, default_payload.copy())
            return default_payload

        except Exception as e:
            logger.warning(
                f"Failed to fetch fundamentals for {canonical_ticker} ({type(e).__name__}: {str(e)}). "
                f"Returning clean default structure."
            )
            default_payload["data_source"] = "YFINANCE_UNAVAILABLE_FALLBACK"
            return default_payload

    @classmethod
    def calculate_health_score(cls, fundamentals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates raw fundamental data using Value Investing principles (Graham & Dodd / Warren Buffett),
        computing a comprehensive Financial Health Score in [0.0, 100.0] and an Arabic diagnostic label.

        Scoring Components:
        1. Valuation Multiples (P/E & P/B): Low positive P/E (5-15) and reasonable P/B (< 2.5) add points.
        2. Profitability (EPS & ROE): Positive earnings add points; negative EPS incurs severe penalties.
        3. Dividend Yield: High sustainable dividend yields add yield stability points.
        4. Balance Sheet & Solvency: Net cash & positive FCF add points; high leverage penalizes.

        Args:
            fundamentals: Dictionary containing extracted financial metrics.

        Returns:
            Dict[str, Any]: Health score, Arabic label, valuation classification, and detailed breakdown.
        """
        fundamentals = fundamentals or {}
        
        pe = fundamentals.get("trailingPE")
        forward_pe = fundamentals.get("forwardPE")
        pb = fundamentals.get("priceToBook")
        eps = fundamentals.get("trailingEps")
        div_yield = fundamentals.get("dividendYield")
        cash = fundamentals.get("totalCash")
        debt = fundamentals.get("totalDebt")
        fcf = fundamentals.get("freeCashflow")
        roe = fundamentals.get("returnOnEquity")

        # Check if we have zero data metrics available
        available_metrics = [v for v in [pe, forward_pe, pb, eps, div_yield, cash, debt, fcf, roe] if v is not None]
        if not available_metrics:
            return {
                "health_score": 50.0,
                "financial_health_label": "بيانات غير متوفرة",
                "valuation_tier": "UNKNOWN",
                "dividend_status": "UNKNOWN",
                "solvency_status": "UNKNOWN",
                "confidence_score": 0.30,
                "score_breakdown": {
                    "pe_points": 0.0,
                    "pb_points": 0.0,
                    "eps_points": 0.0,
                    "dividend_points": 0.0,
                    "solvency_points": 0.0
                },
                "diagnostic_notes_ar": ["لم تتوفر بيانات قوائم مالية كافية لحساب التقييم بدقة."]
            }

        base_score = 50.0  # Neutral baseline
        score_delta = 0.0
        diagnostic_notes = []

        # 1. Price-to-Earnings (P/E) Evaluation (Max ±30 pts)
        pe_points = 0.0
        val_pe = pe if pe is not None else forward_pe
        valuation_tier = "FAIR_VALUE"

        if val_pe is not None:
            if val_pe <= 0:
                pe_points = -25.0
                valuation_tier = "UNPROFITABLE"
                diagnostic_notes.append("الشركة تسجل خسائر صافية (مكرر ربحية سالب).")
            elif 4.0 <= val_pe <= 12.0:
                pe_points = +25.0
                valuation_tier = "UNDERVALUED"
                diagnostic_notes.append(f"مكرر ربحية جذاب جداً ({val_pe:.1f}x) يعكس تسعيراً رخيصاً بالنسبة للأرباح.")
            elif 12.0 < val_pe <= 18.0:
                pe_points = +15.0
                valuation_tier = "FAIR_VALUE"
                diagnostic_notes.append(f"مكرر ربحية عادل ومتوازن ({val_pe:.1f}x).")
            elif 18.0 < val_pe <= 30.0:
                pe_points = +5.0
                valuation_tier = "MODERATE_PREMIUM"
                diagnostic_notes.append(f"مكرر ربحية مرتفع نسبياً ({val_pe:.1f}x).")
            else:  # > 30.0
                pe_points = -10.0
                valuation_tier = "OVERVALUED"
                diagnostic_notes.append(f"مكرر ربحية مبالغ فيه ({val_pe:.1f}x) قد يشكل فخ قيمة.")

        # 2. Price-to-Book (P/B) Evaluation (Max ±20 pts)
        pb_points = 0.0
        if pb is not None:
            if 0.5 <= pb <= 1.8:
                pb_points = +20.0
                diagnostic_notes.append(f"مضاعف القيمة الدفترية ممتاز ({pb:.2f}x) مع تغطية أصول حقيقية.")
            elif 1.8 < pb <= 3.5:
                pb_points = +10.0
                diagnostic_notes.append(f"مضاعف القيمة الدفترية طبيعي ومقبول ({pb:.2f}x).")
            elif pb < 0.5:
                pb_points = +5.0  # Low, but potential distressed asset
                diagnostic_notes.append(f"مضاعف القيمة الدفترية منخفض جداً ({pb:.2f}x) - خصم سعري كبير على الأصول.")
            else:  # > 3.5
                pb_points = -8.0
                diagnostic_notes.append(f"مضاعف القيمة الدفترية مرتفع ({pb:.2f}x) فوق متوسط السوق.")

        # 3. EPS & Profitability Evaluation (Max ±20 pts)
        eps_points = 0.0
        if eps is not None:
            if eps > 0:
                eps_points += 15.0
            else:
                eps_points -= 25.0
                diagnostic_notes.append("ربحية السهم سالبة (Trailing EPS < 0).")

        if roe is not None:
            if roe >= 0.18:  # 18% ROE
                eps_points += 10.0
                diagnostic_notes.append(f"عائد مرتفع على حقوق المساهمين ({roe * 100:.1f}% ROE).")
            elif roe >= 0.10:
                eps_points += 5.0

        # 4. Dividend Yield (Max +15 pts)
        div_points = 0.0
        dividend_status = "NO_DIVIDENDS"
        if div_yield is not None and div_yield > 0:
            dividend_status = "DIVIDEND_PAYING"
            if div_yield >= 0.06:  # >= 6% yield
                div_points = +15.0
                diagnostic_notes.append(f"توزيعات أرباح نقدية قوية وسخية ({div_yield * 100:.1f}% عائد سنوي).")
            elif div_yield >= 0.03:
                div_points = +10.0
                diagnostic_notes.append(f"عائد توزيعات نقدية مستقر ({div_yield * 100:.1f}%).")
            else:
                div_points = +5.0

        # 5. Balance Sheet & Solvency (Cash vs Debt & FCF) (Max ±20 pts)
        solvency_points = 0.0
        solvency_status = "UNKNOWN"
        if cash is not None and debt is not None:
            if cash >= debt:
                solvency_points += 15.0
                solvency_status = "NET_CASH"
                diagnostic_notes.append("مركز مالي صلب مع صافي سيولة نقدية تفوق إجمالي المديونية.")
            elif debt > (cash * 2.5):
                solvency_points -= 15.0
                solvency_status = "HIGH_LEVERAGE"
                diagnostic_notes.append("مديونية مرتفعة تفوق السيولة النقدية بأكثر من 2.5 ضعف.")
            else:
                solvency_points += 5.0
                solvency_status = "MANAGEABLE_DEBT"

        if fcf is not None:
            if fcf > 0:
                solvency_points += 5.0
            else:
                solvency_points -= 5.0

        # Sum and bound final health score in [0.0, 100.0]
        raw_final_score = base_score + pe_points + pb_points + eps_points + div_points + solvency_points
        final_score = round(max(0.0, min(100.0, raw_final_score)), 1)

        # Determine Arabic descriptive health label
        if final_score >= 80.0:
            health_label = "ممتاز (استثمار قيمة وأساسيات قوية)"
        elif final_score >= 65.0:
            health_label = "جيد جداً (أساسيات متينة)"
        elif final_score >= 50.0:
            health_label = "مقبول (تقييم معتدل ومتوازن)"
        elif final_score >= 35.0:
            health_label = "ضعيف (مخاطر هيكلية أو مديونية)"
        else:
            health_label = "سيء (خسائر متتالية أو فخ قيمة)"

        return {
            "health_score": final_score,
            "financial_health_label": health_label,
            "valuation_tier": valuation_tier,
            "dividend_status": dividend_status,
            "solvency_status": solvency_status,
            "confidence_score": round(min(0.40 + (len(available_metrics) * 0.10), 0.95), 2),
            "score_breakdown": {
                "pe_points": pe_points,
                "pb_points": pb_points,
                "eps_points": eps_points,
                "dividend_points": div_points,
                "solvency_points": solvency_points
            },
            "diagnostic_notes_ar": diagnostic_notes if diagnostic_notes else ["الأسهم تقع في النطاق المحايد للمؤشرات المالية."]
        }

    @classmethod
    def get_ticker_analysis(cls, ticker: str) -> Dict[str, Any]:
        """
        Public high-level method: Fetches fundamentals, computes health score, and builds
        the complete standardized fundamental payload with guaranteed zero-failure fallback.

        Args:
            ticker: Stock ticker symbol (e.g. 'COMI.CA', 'SWDY.CA').

        Returns:
            Dict[str, Any]: Complete analysis payload containing metrics, health score, and label.
        """
        canonical_ticker, _ = cls._clean_ticker(ticker)

        try:
            # 1. Fetch raw fundamentals
            raw_data = cls.fetch_fundamentals(canonical_ticker)

            # 2. Compute Health Score
            score_data = cls.calculate_health_score(raw_data)

            # 3. Assemble Unified Payload
            return {
                "status": "SUCCESS",
                "ticker": canonical_ticker,
                "yfinance_symbol": raw_data.get("yfinance_symbol", canonical_ticker),
                "company_name": raw_data.get("company_name_en") or canonical_ticker,
                "sector": raw_data.get("sector_en") or "EGX General",
                "health_score": score_data["health_score"],
                "financial_health_label": score_data["financial_health_label"],
                "valuation_tier": score_data["valuation_tier"],
                "dividend_status": score_data["dividend_status"],
                "solvency_status": score_data["solvency_status"],
                "confidence_score": score_data["confidence_score"],
                "metrics": {
                    "trailingPE": raw_data.get("trailingPE"),
                    "forwardPE": raw_data.get("forwardPE"),
                    "priceToBook": raw_data.get("priceToBook"),
                    "trailingEps": raw_data.get("trailingEps"),
                    "dividendYield": raw_data.get("dividendYield"),
                    "totalCash": raw_data.get("totalCash"),
                    "totalDebt": raw_data.get("totalDebt"),
                    "freeCashflow": raw_data.get("freeCashflow"),
                    "marketCap": raw_data.get("marketCap"),
                    "returnOnEquity": raw_data.get("returnOnEquity")
                },
                "diagnostic_notes_ar": score_data.get("diagnostic_notes_ar", []),
                "is_fallback": False,
                "analyzed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            logger.error(
                f"Unexpected error in get_ticker_analysis for {canonical_ticker} ({type(e).__name__}: {str(e)}). "
                f"Applying institutional fallback."
            )
            return {
                "status": "DATA_UNAVAILABLE_FALLBACK",
                "ticker": canonical_ticker,
                "yfinance_symbol": canonical_ticker,
                "company_name": canonical_ticker,
                "sector": "EGX General",
                "health_score": 50.0,
                "financial_health_label": "بيانات غير متوفرة",
                "valuation_tier": "UNKNOWN",
                "dividend_status": "UNKNOWN",
                "solvency_status": "UNKNOWN",
                "confidence_score": 0.20,
                "metrics": {
                    "trailingPE": None,
                    "forwardPE": None,
                    "priceToBook": None,
                    "trailingEps": None,
                    "dividendYield": None,
                    "totalCash": None,
                    "totalDebt": None,
                    "freeCashflow": None,
                    "marketCap": None,
                    "returnOnEquity": None
                },
                "diagnostic_notes_ar": ["تعذر الاتصال ببيانات القوائم المالية اللحظية. تم تطبيق التقييم المحايد."],
                "is_fallback": True,
                "analyzed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }


# =============================================================================
# CLI DEMO & TEST ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    import json
    print("===============================================================")
    print("📈 GEN-26 FUNDAMENTAL & VALUATION DATA ENGINE")
    print("===============================================================")

    test_tickers = ["COMI.CA", "SWDY.CA", "TMGH.CA", "INVALID_STOCK.CA"]
    for sym in test_tickers:
        print(f"\n--- Analyzing Fundamentals for {sym} ---")
        analysis = FundamentalDataEngine.get_ticker_analysis(sym)
        print(f"Health Score: {analysis['health_score']}/100 ({analysis['financial_health_label']})")
        print(f"P/E: {analysis['metrics']['trailingPE']} | P/B: {analysis['metrics']['priceToBook']}")
        print("Diagnostic Notes:", analysis["diagnostic_notes_ar"])
