"""
research_v42/engines/fundamental_engine.py

Fundamental Analysis Engine — GEN-26 V42 Research Layer
DATA MODE: YFinance PROXY (NOT real EGX filings)
Point-in-Time: +45 day publication delay applied

STATUS: RESEARCH / SHADOW — Does NOT affect V4.1 execution
"""
from __future__ import annotations
import math
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

from data_quality_engine import DataPoint, DataQualityEngine

PUBLICATION_LAG_DAYS = 45  # EGX legal disclosure lag


@dataclass
class FundamentalProfile:
    ticker: str
    # Scores (0–100)
    growth_score: float = 50.0
    profitability_score: float = 50.0
    balance_sheet_score: float = 50.0
    cash_flow_score: float = 50.0
    earnings_quality_score: float = 50.0
    # Composite
    fundamental_score: float = 50.0
    # Raw metrics
    metrics: dict = field(default_factory=dict)
    data_quality: str = "PROXY"
    warnings: list = field(default_factory=list)
    missing_metrics: list = field(default_factory=list)


class FundamentalEngine:
    """
    Fetches and scores stock fundamentals.
    All data labeled PROXY since YFinance data for EGX may be incomplete.
    Point-in-Time: publication_date = period_end + 45 days
    """

    WEIGHTS = {
        "growth": 0.25,
        "profitability": 0.30,
        "balance_sheet": 0.20,
        "cash_flow": 0.15,
        "earnings_quality": 0.10,
    }

    def __init__(self):
        self._cache: dict[str, FundamentalProfile] = {}

    def _get_scalar(self, df, row_key: str) -> Optional[float]:
        """Extract most-recent value from quarterly/annual financials df."""
        if df is None or df.empty:
            return None
        if row_key not in df.index:
            return None
        try:
            vals = df.loc[row_key].dropna()
            if vals.empty:
                return None
            return float(vals.iloc[0])
        except Exception:
            return None

    def fetch_raw_metrics(self, ticker: str) -> dict[str, DataPoint]:
        """
        Fetch fundamentals from YFinance.
        Returns dict of metric_name -> DataPoint.
        ALL values labeled as PROXY.
        """
        if not YFINANCE_AVAILABLE:
            return {"error": DataPoint("error", None, quality="MISSING", source="yfinance_unavailable")}

        dq = DataQualityEngine()
        try:
            stock = yf.Ticker(ticker)
            qf = stock.quarterly_financials
            qs = stock.quarterly_balance_sheet
            qc = stock.quarterly_cashflow
            info = stock.info or {}

            # Fallback to annual if quarterly empty
            if qf is None or qf.empty:
                qf = stock.financials
            if qs is None or qs.empty:
                qs = stock.balance_sheet
            if qc is None or qc.empty:
                qc = stock.cashflow

        except Exception as e:
            return {"fetch_error": DataPoint("fetch_error", str(e), quality="MISSING")}

        def wrap(val, name):
            return dq.validate_fundamental(name, val)

        m = {}
        # Income Statement
        m["Revenue"]          = wrap(self._get_scalar(qf, "Total Revenue"), "Revenue")
        m["NetIncome"]        = wrap(self._get_scalar(qf, "Net Income"), "NetIncome")
        m["EPS"]              = wrap(self._get_scalar(qf, "Basic EPS"), "EPS")
        m["GrossProfit"]      = wrap(self._get_scalar(qf, "Gross Profit"), "GrossProfit")
        m["OperatingIncome"]  = wrap(self._get_scalar(qf, "Operating Income"), "OperatingIncome")
        m["EBITDA"]           = wrap(self._get_scalar(qf, "EBITDA"), "EBITDA")

        # Balance Sheet
        m["TotalAssets"]      = wrap(self._get_scalar(qs, "Total Assets"), "TotalAssets")
        m["TotalDebt"]        = wrap(self._get_scalar(qs, "Total Debt"), "TotalDebt")
        m["Equity"]           = wrap(self._get_scalar(qs, "Stockholders Equity"), "Equity")
        m["Cash"]             = wrap(self._get_scalar(qs, "Cash And Cash Equivalents"), "Cash")
        m["CurrentAssets"]    = wrap(self._get_scalar(qs, "Current Assets"), "CurrentAssets")
        m["CurrentLiab"]      = wrap(self._get_scalar(qs, "Current Liabilities"), "CurrentLiab")

        # Cash Flow
        m["OperatingCF"]      = wrap(self._get_scalar(qc, "Operating Cash Flow"), "OperatingCF")
        m["CapEx"]            = wrap(self._get_scalar(qc, "Capital Expenditure"), "CapEx")

        # Derived: FCF
        ocf = m["OperatingCF"].value
        capex = m["CapEx"].value
        if ocf is not None and capex is not None:
            m["FreeCashFlow"] = DataPoint("FreeCashFlow", ocf + capex, quality="PROXY",
                                          source="YFinance_Derived", confidence=0.5)
        else:
            m["FreeCashFlow"] = DataPoint("FreeCashFlow", None, quality="MISSING")

        # From info dict
        m["PE_Trailing"]      = wrap(info.get("trailingPE"), "PE_Trailing")
        m["PB"]               = wrap(info.get("priceToBook"), "PB")
        m["ROE"]              = wrap(info.get("returnOnEquity"), "ROE")
        m["ROA"]              = wrap(info.get("returnOnAssets"), "ROA")
        m["DividendYield"]    = wrap(info.get("dividendYield"), "DividendYield")
        m["MarketCap"]        = wrap(info.get("marketCap"), "MarketCap")

        return m

    def _score_growth(self, m: dict) -> tuple[float, list[str]]:
        score, warns = 50.0, []
        ni = m.get("NetIncome")
        rev = m.get("Revenue")

        if ni and ni.is_usable():
            if ni.value > 0:
                score += 20
            else:
                score -= 25
                warns.append("Negative net income")
        else:
            score -= 5
            warns.append("Net income missing")

        if rev and rev.is_usable():
            if rev.value > 0:
                score += 10
            # Growth trend would need multi-period — mark as TODO
            warns.append("Revenue growth trend: needs multi-period data (TODO)")
        else:
            warns.append("Revenue missing")

        return min(max(score, 0.0), 100.0), warns

    def _score_profitability(self, m: dict) -> tuple[float, list[str]]:
        score, warns = 50.0, []
        roe = m.get("ROE")
        roa = m.get("ROA")
        ebitda = m.get("EBITDA")
        rev = m.get("Revenue")

        if roe and roe.is_usable():
            if roe.value > 0.15:
                score += 25
            elif roe.value > 0.08:
                score += 10
            elif roe.value < 0:
                score -= 20
                warns.append(f"Negative ROE: {roe.value:.1%}")

        if roa and roa.is_usable():
            if roa.value > 0.05:
                score += 10
            elif roa.value < 0:
                score -= 10

        # EBITDA Margin
        if ebitda and rev and ebitda.is_usable() and rev.is_usable() and rev.value > 0:
            margin = ebitda.value / rev.value
            if margin > 0.20:
                score += 15
            elif margin > 0.10:
                score += 5
            elif margin < 0:
                score -= 15
                warns.append(f"Negative EBITDA margin: {margin:.1%}")

        return min(max(score, 0.0), 100.0), warns

    def _score_balance_sheet(self, m: dict) -> tuple[float, list[str]]:
        score, warns = 50.0, []
        debt = m.get("TotalDebt")
        equity = m.get("Equity")
        current_a = m.get("CurrentAssets")
        current_l = m.get("CurrentLiab")
        cash = m.get("Cash")

        if debt and equity and debt.is_usable() and equity.is_usable() and equity.value > 0:
            de = debt.value / equity.value
            if de < 0.3:
                score += 25
            elif de < 1.0:
                score += 10
            elif de > 2.0:
                score -= 20
                warns.append(f"High D/E ratio: {de:.2f}")

        if current_a and current_l and current_a.is_usable() and current_l.is_usable() and current_l.value > 0:
            cr = current_a.value / current_l.value
            if cr > 2.0:
                score += 15
            elif cr < 1.0:
                score -= 15
                warns.append(f"Low current ratio: {cr:.2f}")

        return min(max(score, 0.0), 100.0), warns

    def _score_cash_flow(self, m: dict) -> tuple[float, list[str]]:
        score, warns = 50.0, []
        ocf = m.get("OperatingCF")
        fcf = m.get("FreeCashFlow")
        ni = m.get("NetIncome")

        if ocf and ocf.is_usable():
            if ocf.value > 0:
                score += 25
            else:
                score -= 20
                warns.append("Negative operating cash flow")

        if fcf and fcf.is_usable():
            if fcf.value > 0:
                score += 15
            else:
                warns.append("Negative FCF")

        # Earnings quality: OCF vs Net Income
        if ocf and ni and ocf.is_usable() and ni.is_usable() and ni.value != 0:
            ocf_ni_ratio = ocf.value / abs(ni.value)
            if ocf_ni_ratio < 0.5:
                score -= 10
                warns.append(f"Low OCF/NI ratio ({ocf_ni_ratio:.2f}) — possible earnings manipulation risk")
            elif ocf_ni_ratio > 1.5:
                score += 10  # Cash-generative

        return min(max(score, 0.0), 100.0), warns

    def _score_earnings_quality(self, m: dict) -> tuple[float, list[str]]:
        """Simple proxy: OCF > NetIncome indicates real earnings."""
        score, warns = 50.0, []
        ocf = m.get("OperatingCF")
        ni = m.get("NetIncome")

        if not (ocf and ni and ocf.is_usable() and ni.is_usable()):
            warns.append("Cannot assess earnings quality — missing OCF or NI")
            return 40.0, warns

        if ni.value > 0 and ocf.value > ni.value:
            score = 80.0  # Strong: cash exceeds reported earnings
        elif ni.value > 0 and ocf.value > 0:
            score = 65.0  # OK
        elif ni.value > 0 and ocf.value < 0:
            score = 25.0  # Red flag: profit reported but cash burning
            warns.append("CAUTION: Positive NI but negative OCF — possible non-cash income")
        else:
            score = 40.0

        return score, warns

    def score(self, ticker: str) -> FundamentalProfile:
        if ticker in self._cache:
            return self._cache[ticker]

        profile = FundamentalProfile(ticker=ticker)
        metrics = self.fetch_raw_metrics(ticker)
        profile.metrics = {k: v.to_dict() for k, v in metrics.items()}

        all_warns = []

        g_score, g_warns = self._score_growth(metrics)
        p_score, p_warns = self._score_profitability(metrics)
        b_score, b_warns = self._score_balance_sheet(metrics)
        c_score, c_warns = self._score_cash_flow(metrics)
        eq_score, eq_warns = self._score_earnings_quality(metrics)

        profile.growth_score = g_score
        profile.profitability_score = p_score
        profile.balance_sheet_score = b_score
        profile.cash_flow_score = c_score
        profile.earnings_quality_score = eq_score

        composite = (
            g_score  * self.WEIGHTS["growth"] +
            p_score  * self.WEIGHTS["profitability"] +
            b_score  * self.WEIGHTS["balance_sheet"] +
            c_score  * self.WEIGHTS["cash_flow"] +
            eq_score * self.WEIGHTS["earnings_quality"]
        )
        profile.fundamental_score = round(composite, 1)

        missing = [k for k, v in metrics.items()
                   if isinstance(v, DataPoint) and not v.is_usable()]
        profile.missing_metrics = missing
        profile.warnings = g_warns + p_warns + b_warns + c_warns + eq_warns

        # Penalize if too many metrics missing
        if len(missing) > 8:
            profile.fundamental_score = max(profile.fundamental_score - 15, 10.0)
            profile.data_quality = "PARTIAL"
        else:
            profile.data_quality = "PROXY"

        self._cache[ticker] = profile
        return profile


if __name__ == "__main__":
    import sys
    tickers = sys.argv[1:] if len(sys.argv) > 1 else ["COMI.CA"]
    engine = FundamentalEngine()
    for t in tickers:
        p = engine.score(t)
        print(f"\n{'='*60}")
        print(f"Ticker: {t}")
        print(f"Fundamental Score: {p.fundamental_score:.1f} / 100")
        print(f"  Growth:          {p.growth_score:.1f}")
        print(f"  Profitability:   {p.profitability_score:.1f}")
        print(f"  Balance Sheet:   {p.balance_sheet_score:.1f}")
        print(f"  Cash Flow:       {p.cash_flow_score:.1f}")
        print(f"  Earnings Quality:{p.earnings_quality_score:.1f}")
        print(f"  Data Quality:    {p.data_quality}")
        print(f"  Missing Metrics: {len(p.missing_metrics)}")
        if p.warnings:
            print(f"  Warnings:")
            for w in p.warnings[:5]:
                print(f"    - {w}")
