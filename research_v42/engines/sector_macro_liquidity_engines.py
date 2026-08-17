"""
research_v42/engines/sector_engine.py + macro_engine.py + liquidity_engine.py
Combined supporting engines — GEN-26 V42

STATUS: RESEARCH / SHADOW
"""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────
# SECTOR ENGINE
# ─────────────────────────────────────────────────────────

EGX_SECTOR_MAP = {
    "COMI.CA": ("التجاري الدولي",    "BANKS"),
    "FAIT.CA": ("فيصل الإسلامي",     "BANKS"),
    "ADIB.CA": ("أبوظبي الإسلامي",   "BANKS"),
    "TMGH.CA": ("طلعت مصطفى",       "REAL_ESTATE"),
    "PHDC.CA": ("بالم هيلز",        "REAL_ESTATE"),
    "HELI.CA": ("مصر الجديدة",      "REAL_ESTATE"),
    "SWDY.CA": ("السويدي إلكتريك",  "INDUSTRIALS"),
    "ESRS.CA": ("حديد عز",         "INDUSTRIALS"),
    "ABUK.CA": ("أبو قير",         "CHEMICALS"),
    "MFPC.CA": ("موبكو",           "CHEMICALS"),
    "ETEL.CA": ("المصرية للاتصالات","TELECOM"),
    "HRHO.CA": ("EFG هيرميس",      "FINANCIAL_SERVICES"),
    "FWRY.CA": ("فوري",            "FINANCIAL_SERVICES"),
    "AMOC.CA": ("أموك",            "ENERGY"),
    "ISPH.CA": ("ابن سينا",        "HEALTHCARE"),
}

SECTOR_REGIME = {
    # Format: (score_bonus, label) — rough proxies, update periodically
    "BANKS": (10, "FAVORABLE"),
    "REAL_ESTATE": (5,  "NEUTRAL"),
    "INDUSTRIALS": (-5, "HEADWIND"),
    "CHEMICALS":   (0,  "NEUTRAL"),
    "TELECOM":     (8,  "DEFENSIVE"),
    "FINANCIAL_SERVICES": (3, "NEUTRAL"),
    "ENERGY":      (2,  "NEUTRAL"),
    "HEALTHCARE":  (10, "DEFENSIVE"),
    "UNKNOWN":     (0,  "UNKNOWN"),
}


@dataclass
class SectorProfile:
    ticker: str
    company_name: str = "UNKNOWN"
    sector: str = "UNKNOWN"
    sector_regime: str = "UNKNOWN"
    sector_score: float = 50.0
    data_quality: str = "STATIC_MAP"   # This is a static lookup, not live data
    warnings: list = field(default_factory=list)


class SectorEngine:
    def score(self, ticker: str) -> SectorProfile:
        info = EGX_SECTOR_MAP.get(ticker, (ticker, "UNKNOWN"))
        name, sector = info
        bonus, regime = SECTOR_REGIME.get(sector, SECTOR_REGIME["UNKNOWN"])

        profile = SectorProfile(
            ticker=ticker,
            company_name=name,
            sector=sector,
            sector_regime=regime,
            sector_score=round(50.0 + bonus, 1),
            data_quality="STATIC_MAP",
        )
        if sector == "UNKNOWN":
            profile.warnings.append(f"{ticker}: Sector not mapped — using neutral score")
        return profile


# ─────────────────────────────────────────────────────────
# MACRO ENGINE
# ─────────────────────────────────────────────────────────

@dataclass
class MacroProfile:
    regime: str = "UNKNOWN"           # FAVORABLE | NEUTRAL | HOSTILE | UNKNOWN
    interest_rate_cbe: float = 27.25  # CBE Overnight Rate (hardcoded proxy)
    usd_egp: Optional[float] = None
    gold_usd: Optional[float] = None
    oil_usd: Optional[float] = None
    inflation_proxy: Optional[float] = None  # NOT IMPLEMENTED — no EGX data source
    macro_score: float = 50.0
    data_quality: str = "PARTIAL"
    warnings: list = field(default_factory=list)


class MacroEngine:
    """
    Evaluates macro environment.
    Interest rate: hardcoded to CBE corridor (update manually).
    FX/Commodity: fetched via YFinance.
    Inflation: NOT IMPLEMENTED (no real-time EGX data source).
    """

    def get_macro(self) -> MacroProfile:
        profile = MacroProfile()
        try:
            import yfinance as yf
            usd = yf.download("USDEGP=X", period="5d", progress=False, auto_adjust=True)
            gold = yf.download("GC=F", period="5d", progress=False, auto_adjust=True)
            oil = yf.download("BZ=F", period="5d", progress=False, auto_adjust=True)

            def last_close(df):
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.droplevel(1)
                return float(df["Close"].dropna().iloc[-1]) if not df.empty else None

            profile.usd_egp = last_close(usd)
            profile.gold_usd = last_close(gold)
            profile.oil_usd = last_close(oil)
        except Exception as e:
            profile.warnings.append(f"Macro fetch partial: {e}")

        # Score based on interest rate regime
        score = 50.0
        rate = profile.interest_rate_cbe
        if rate > 25:
            score -= 15   # Very high rates = hostile for growth
            profile.regime = "HOSTILE"
            profile.warnings.append(f"CBE rate very high ({rate}%) — negative for leveraged companies")
        elif rate > 18:
            score -= 5
            profile.regime = "NEUTRAL"
        elif rate < 12:
            score += 10
            profile.regime = "FAVORABLE"
        else:
            profile.regime = "NEUTRAL"

        # EGP depreciation pressure
        if profile.usd_egp and profile.usd_egp > 50:
            score -= 10
            profile.warnings.append(f"EGP under pressure: 1 USD = {profile.usd_egp:.2f} EGP")

        profile.macro_score = round(min(max(score, 0.0), 100.0), 1)
        profile.warnings.append("INFLATION = NOT IMPLEMENTED (no real EGX data source)")
        return profile

    def company_fx_sensitivity(self, ticker: str) -> str:
        """Very rough proxy for FX sensitivity by sector."""
        sector_fx = {
            "INDUSTRIALS": "HIGH_IMPORT",   # Import costs in USD
            "CHEMICALS": "HIGH_IMPORT",
            "ENERGY": "USD_DENOMINATED",
            "REAL_ESTATE": "EGP_LOCAL",
            "BANKS": "MIXED",
            "TELECOM": "LOW",
            "HEALTHCARE": "MIXED_IMPORT",
        }
        info = EGX_SECTOR_MAP.get(ticker, (ticker, "UNKNOWN"))
        sector = info[1]
        return sector_fx.get(sector, "UNKNOWN")


# ─────────────────────────────────────────────────────────
# LIQUIDITY ENGINE
# ─────────────────────────────────────────────────────────

@dataclass
class LiquidityProfile:
    ticker: str
    avg_daily_volume: Optional[float] = None       # shares
    avg_daily_value_egp: Optional[float] = None    # EGP traded
    days_to_liquidate: Optional[float] = None      # assumes 25% of ADV
    liquidity_score: float = 50.0                  # 0–100
    liquidity_label: str = "UNKNOWN"               # HIGH | MEDIUM | LOW | ILLIQUID
    data_quality: str = "PROXY"
    warnings: list = field(default_factory=list)


class LiquidityEngine:
    """
    Scores stock liquidity for EGX.
    Minimum tradeable threshold: EGP 500,000 / day.
    """
    MIN_EGP_DAILY = 500_000      # Below this = ILLIQUID
    TARGET_EGP_DAILY = 5_000_000 # Above this = HIGH

    def score(self, ticker: str, df: Optional[pd.DataFrame] = None) -> LiquidityProfile:
        profile = LiquidityProfile(ticker=ticker)

        if df is None:
            try:
                import yfinance as yf
                raw = yf.download(ticker, period="3mo", progress=False, auto_adjust=True)
                if isinstance(raw.columns, pd.MultiIndex):
                    raw.columns = raw.columns.droplevel(1)
                df = raw
            except Exception as e:
                profile.warnings.append(f"Fetch failed: {e}")
                return profile

        if df.empty or "Volume" not in df or "Close" not in df:
            profile.warnings.append("Insufficient data for liquidity analysis")
            return profile

        close = df["Close"].ffill()
        vol = df["Volume"].ffill()

        # 20-day averages
        profile.avg_daily_volume = float(vol.iloc[-20:].mean())
        avg_price = float(close.iloc[-20:].mean())
        profile.avg_daily_value_egp = profile.avg_daily_volume * avg_price

        # Days to liquidate (assume position = 5% of 30d ADV)
        position_assumption = profile.avg_daily_volume * 30 * 0.05
        if profile.avg_daily_volume > 0:
            profile.days_to_liquidate = position_assumption / (profile.avg_daily_volume * 0.25)

        # Score
        adv = profile.avg_daily_value_egp or 0
        if adv >= self.TARGET_EGP_DAILY:
            profile.liquidity_score = 85.0
            profile.liquidity_label = "HIGH"
        elif adv >= self.MIN_EGP_DAILY * 2:
            profile.liquidity_score = 65.0
            profile.liquidity_label = "MEDIUM"
        elif adv >= self.MIN_EGP_DAILY:
            profile.liquidity_score = 40.0
            profile.liquidity_label = "LOW"
            profile.warnings.append(f"Low liquidity: EGP {adv:,.0f}/day")
        else:
            profile.liquidity_score = 10.0
            profile.liquidity_label = "ILLIQUID"
            profile.warnings.append(f"ILLIQUID: EGP {adv:,.0f}/day — avoid or reduce size")

        return profile


if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "COMI.CA"
    print("=== SECTOR ===")
    s = SectorEngine().score(ticker)
    print(f"{ticker}: Sector={s.sector}, Score={s.sector_score}, Regime={s.sector_regime}")

    print("\n=== MACRO ===")
    m = MacroEngine().get_macro()
    print(f"Regime={m.regime}, Rate={m.interest_rate_cbe}%, USD/EGP={m.usd_egp}, Score={m.macro_score}")

    print("\n=== LIQUIDITY ===")
    liq = LiquidityEngine().score(ticker)
    print(f"{ticker}: ADV={liq.avg_daily_value_egp:,.0f} EGP, Label={liq.liquidity_label}, Score={liq.liquidity_score}")
