"""
research_v42/engines/valuation_engine.py

Valuation Engine — GEN-26 V42 Research Layer
Compares P/E, P/B, EV/EBITDA vs sector and historical averages.

STATUS: RESEARCH / SHADOW
DATA MODE: YFinance PROXY
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Optional

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

from data_quality_engine import DataPoint, DataQualityEngine

# EGX Sector median P/E proxies (rough proxies — update annually)
SECTOR_PE_MEDIANS = {
    "BANKS": 7.0,
    "REAL_ESTATE": 10.0,
    "INDUSTRIALS": 12.0,
    "CHEMICALS": 9.0,
    "TELECOM": 11.0,
    "CONSUMER": 14.0,
    "HEALTHCARE": 18.0,
    "ENERGY": 8.0,
    "FINANCIAL_SERVICES": 9.0,
    "UNKNOWN": 12.0,
}

SECTOR_PB_MEDIANS = {
    "BANKS": 1.5,
    "REAL_ESTATE": 1.2,
    "INDUSTRIALS": 1.8,
    "CHEMICALS": 1.5,
    "TELECOM": 2.0,
    "CONSUMER": 2.5,
    "HEALTHCARE": 3.0,
    "ENERGY": 1.3,
    "FINANCIAL_SERVICES": 1.4,
    "UNKNOWN": 1.8,
}


@dataclass
class ValuationProfile:
    ticker: str
    sector: str = "UNKNOWN"

    pe: Optional[float] = None
    pb: Optional[float] = None
    ev_ebitda: Optional[float] = None
    fcf_yield: Optional[float] = None
    dividend_yield: Optional[float] = None

    pe_vs_sector: str = "UNKNOWN"    # CHEAP | FAIR | EXPENSIVE | UNRELIABLE
    pb_vs_sector: str = "UNKNOWN"
    overall_valuation: str = "UNKNOWN"

    valuation_score: float = 50.0    # 0–100 (higher = cheaper)
    confidence: float = 0.0
    data_quality: str = "PROXY"
    warnings: list = field(default_factory=list)


class ValuationEngine:
    """
    Scores stocks based on valuation multiples.
    Higher score = cheaper (more attractive valuation).
    """

    def __init__(self):
        self._cache: dict[str, ValuationProfile] = {}

    def _safe_float(self, val) -> Optional[float]:
        if val is None:
            return None
        try:
            v = float(val)
            return None if (math.isnan(v) or math.isinf(v) or v <= 0) else v
        except (TypeError, ValueError):
            return None

    def fetch_valuation(self, ticker: str, sector: str = "UNKNOWN") -> ValuationProfile:
        if ticker in self._cache:
            return self._cache[ticker]

        profile = ValuationProfile(ticker=ticker, sector=sector)

        if not YFINANCE_AVAILABLE:
            profile.warnings.append("yfinance not available")
            profile.data_quality = "MISSING"
            return profile

        try:
            stock = yf.Ticker(ticker)
            info = stock.info or {}
        except Exception as e:
            profile.warnings.append(f"Fetch failed: {e}")
            profile.data_quality = "MISSING"
            self._cache[ticker] = profile
            return profile

        dq = DataQualityEngine()

        profile.pe = self._safe_float(info.get("trailingPE"))
        profile.pb = self._safe_float(info.get("priceToBook"))
        profile.fcf_yield = self._safe_float(info.get("freeCashflow"))
        profile.dividend_yield = self._safe_float(info.get("dividendYield"))

        # EV/EBITDA
        ev = self._safe_float(info.get("enterpriseValue"))
        ebitda = self._safe_float(info.get("ebitda"))
        if ev and ebitda and ebitda > 0:
            profile.ev_ebitda = ev / ebitda

        # Score calculation
        score = 50.0
        warns = []
        sector_pe = SECTOR_PE_MEDIANS.get(sector, SECTOR_PE_MEDIANS["UNKNOWN"])
        sector_pb = SECTOR_PB_MEDIANS.get(sector, SECTOR_PB_MEDIANS["UNKNOWN"])

        # P/E assessment
        if profile.pe is not None:
            ratio = profile.pe / sector_pe
            if ratio < 0.7:
                profile.pe_vs_sector = "CHEAP"
                score += 20
            elif ratio < 1.0:
                profile.pe_vs_sector = "FAIR"
                score += 8
            elif ratio < 1.5:
                profile.pe_vs_sector = "FAIR"
            else:
                profile.pe_vs_sector = "EXPENSIVE"
                score -= 15
                warns.append(f"P/E ({profile.pe:.1f}) >> sector median ({sector_pe:.1f})")
        else:
            profile.pe_vs_sector = "UNRELIABLE"
            warns.append("P/E not available (no earnings or negative)")

        # P/B assessment
        if profile.pb is not None:
            ratio_pb = profile.pb / sector_pb
            if ratio_pb < 0.7:
                profile.pb_vs_sector = "CHEAP"
                score += 15
            elif ratio_pb < 1.0:
                profile.pb_vs_sector = "FAIR"
                score += 5
            elif ratio_pb < 1.5:
                profile.pb_vs_sector = "FAIR"
            else:
                profile.pb_vs_sector = "EXPENSIVE"
                score -= 10
        else:
            profile.pb_vs_sector = "UNRELIABLE"
            warns.append("P/B not available")

        # EV/EBITDA
        if profile.ev_ebitda is not None:
            if profile.ev_ebitda < 6:
                score += 15
            elif profile.ev_ebitda < 10:
                score += 5
            elif profile.ev_ebitda > 20:
                score -= 10
                warns.append(f"High EV/EBITDA: {profile.ev_ebitda:.1f}")

        # FCF Yield bonus
        if profile.fcf_yield and profile.fcf_yield > 0:
            score += 5

        # Dividend Yield bonus
        if profile.dividend_yield and profile.dividend_yield > 0.03:
            score += 5

        profile.valuation_score = round(min(max(score, 0.0), 100.0), 1)
        profile.warnings = warns

        # Determine overall label
        if profile.valuation_score >= 70:
            profile.overall_valuation = "CHEAP"
        elif profile.valuation_score >= 45:
            profile.overall_valuation = "FAIR"
        else:
            profile.overall_valuation = "EXPENSIVE"

        # Confidence based on data availability
        available = sum([
            profile.pe is not None,
            profile.pb is not None,
            profile.ev_ebitda is not None,
            profile.fcf_yield is not None,
        ])
        profile.confidence = min(available / 4.0, 1.0)
        if profile.confidence < 0.5:
            profile.data_quality = "PARTIAL"

        self._cache[ticker] = profile
        return profile


if __name__ == "__main__":
    import sys
    tickers = sys.argv[1:] if len(sys.argv) > 1 else ["COMI.CA"]
    engine = ValuationEngine()
    for t in tickers:
        p = engine.fetch_valuation(t, sector="BANKS")
        print(f"\n{t}: ValuationScore={p.valuation_score:.1f}, Overall={p.overall_valuation}")
        print(f"  P/E={p.pe}, P/B={p.pb}, EV/EBITDA={p.ev_ebitda}, Confidence={p.confidence:.0%}")
        for w in p.warnings:
            print(f"  WARN: {w}")
