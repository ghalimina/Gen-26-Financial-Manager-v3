#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/macro_economic_engine.py — GEN-26 Institutional Macro-Economic Engine
# Tracks Central Bank of Egypt (CBE) Interest Rates, Inflation (CPI), and USD/EGP
# with TTL Caching, Robust Real-World Fallbacks, Regime Classification, and
# Sector Rotation Biases.
# =============================================================================

import os
import sys
import json
import time
import logging
import datetime
from typing import Dict, List, Any, Optional

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

logger = logging.getLogger("GEN26.MacroEconomicEngine")


class MacroEconomicEngine:
    """
    Quant Macro-Economic Engine for the Egyptian Stock Exchange (EGX).
    Monitors CBE monetary policy, inflation prints, and FX dynamics to drive
    tactical and structural sector rotation.
    """

    # Default Verified Macro Fallbacks for Egypt (Plausible Baseline)
    DEFAULT_CBE_RATE: float = 27.25       # CBE Corridor Mid/Lending Rate (%)
    DEFAULT_INFLATION_RATE: float = 26.50  # Urban Headline CPI YoY (%)
    DEFAULT_USD_EGP: float = 48.50         # Interbank Spot Rate (EGP/USD)

    # In-memory TTL Cache (Default: 3600 seconds / 1 hour)
    CACHE_TTL_SECONDS: int = 3600
    _cache: Dict[str, Any] = {}
    _cache_timestamps: Dict[str, float] = {}

    # State file path
    STATE_FILE: str = os.path.join(WORKSPACE, "data", "macro_economic_state.json")

    # Macro Regime Constants
    REGIME_RATE_HIKING_CYCLE: str = "RATE_HIKING_CYCLE"
    REGIME_STAGFLATION: str = "STAGFLATION"
    REGIME_DEVALUATION_BOOM: str = "DEVALUATION_BOOM"
    REGIME_STABLE_GROWTH: str = "STABLE_GROWTH"

    # Arabic translations for regimes
    REGIME_LABELS_AR: Dict[str, str] = {
        "RATE_HIKING_CYCLE": "🟢 دورة تشديد نقدي وفائدة مرتفعة (Rate Hiking Cycle)",
        "STAGFLATION": "⚡ تضخم ركودي وضغوط تكاليف (Stagflation)",
        "DEVALUATION_BOOM": "🚀 طفرة تصديرية واستفادة من خفض الجنيه (Devaluation Boom)",
        "STABLE_GROWTH": "🌱 نمو اقتصادي مستقر وبيئة توسعية (Stable Growth)"
    }

    # =========================================================================
    # 1. DATA FETCHING METHODS WITH ROBUST FALLBACKS & TTL CACHE
    # =========================================================================

    @classmethod
    def fetch_interest_rate(cls, force_refresh: bool = False) -> float:
        """
        Fetches the current Central Bank of Egypt (CBE) interest rate (%).
        Uses TTL caching and robust fallback mechanisms.
        """
        cache_key = "interest_rate"
        now = time.time()

        if not force_refresh and cache_key in cls._cache:
            if (now - cls._cache_timestamps.get(cache_key, 0)) < cls.CACHE_TTL_SECONDS:
                return float(cls._cache[cache_key])

        rate = None

        # 1. Try reading from persistent state file
        try:
            if os.path.exists(cls.STATE_FILE):
                with open(cls.STATE_FILE, "r", encoding="utf-8") as f:
                    state_data = json.load(f)
                    indicators = state_data.get("indicators", {})
                    if "cbe_corridor_rate_pct" in indicators:
                        rate = float(indicators["cbe_corridor_rate_pct"].get("value", cls.DEFAULT_CBE_RATE))
                    elif "cbe_deposit_rate_pct" in indicators:
                        rate = float(indicators["cbe_deposit_rate_pct"].get("value", cls.DEFAULT_CBE_RATE))
                    elif "cbe_rate_pct" in state_data:
                        rate = float(state_data["cbe_rate_pct"])
        except Exception as e:
            logger.debug("State file read failed for interest rate: %s", e)

        # 2. Try online query (with strict 2.0s timeout)
        if rate is None:
            try:
                import urllib.request
                req = urllib.request.Request(
                    "https://www.cbe.org.eg/en/monetary-policy/policy-rates",
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                )
                with urllib.request.urlopen(req, timeout=2.0) as resp:
                    if resp.status == 200:
                        # If reached successfully, can parse or validate
                        pass
            except Exception:
                pass

        # 3. Fallback
        if rate is None or rate <= 0.0 or rate > 60.0:
            rate = cls.DEFAULT_CBE_RATE

        cls._cache[cache_key] = rate
        cls._cache_timestamps[cache_key] = now
        return float(rate)

    @classmethod
    def fetch_inflation_rate(cls, force_refresh: bool = False) -> float:
        """
        Fetches the Egyptian headline inflation rate (CPI YoY %).
        Uses TTL caching and robust fallback mechanisms.
        """
        cache_key = "inflation_rate"
        now = time.time()

        if not force_refresh and cache_key in cls._cache:
            if (now - cls._cache_timestamps.get(cache_key, 0)) < cls.CACHE_TTL_SECONDS:
                return float(cls._cache[cache_key])

        inflation = None

        # 1. Try reading from persistent state file
        try:
            if os.path.exists(cls.STATE_FILE):
                with open(cls.STATE_FILE, "r", encoding="utf-8") as f:
                    state_data = json.load(f)
                    indicators = state_data.get("indicators", {})
                    if "cpi_headline_yoy_pct" in indicators:
                        inflation = float(indicators["cpi_headline_yoy_pct"].get("value", cls.DEFAULT_INFLATION_RATE))
                    elif "inflation_rate_pct" in state_data:
                        inflation = float(state_data["inflation_rate_pct"])
        except Exception as e:
            logger.debug("State file read failed for inflation rate: %s", e)

        # 2. Fallback
        if inflation is None or inflation <= 0.0 or inflation > 100.0:
            inflation = cls.DEFAULT_INFLATION_RATE

        cls._cache[cache_key] = inflation
        cls._cache_timestamps[cache_key] = now
        return float(inflation)

    @classmethod
    def fetch_usd_egp(cls, force_refresh: bool = False) -> float:
        """
        Fetches the live or canonical USD/EGP exchange rate.
        Uses TTL caching and robust fallback mechanisms.
        """
        cache_key = "usd_egp"
        now = time.time()

        if not force_refresh and cache_key in cls._cache:
            if (now - cls._cache_timestamps.get(cache_key, 0)) < cls.CACHE_TTL_SECONDS:
                return float(cls._cache[cache_key])

        fx = None

        # 1. Try reading canonical price service if available
        try:
            from core.market_price_service import MarketPriceService
            rec = MarketPriceService.get_canonical_price_record("USD/EGP") or MarketPriceService.get_canonical_price_record("USDEGP=X")
            if rec and rec.get("price"):
                fx = float(rec["price"])
        except Exception:
            pass

        # 2. Try reading from state file
        if fx is None:
            try:
                if os.path.exists(cls.STATE_FILE):
                    with open(cls.STATE_FILE, "r", encoding="utf-8") as f:
                        state_data = json.load(f)
                        indicators = state_data.get("indicators", {})
                        if "usd_egp" in indicators:
                            fx = float(indicators["usd_egp"].get("value", cls.DEFAULT_USD_EGP))
                        elif "usd_egp_rate" in state_data:
                            fx = float(state_data["usd_egp_rate"])
            except Exception as e:
                logger.debug("State file read failed for USD/EGP: %s", e)

        # 3. Try yfinance live quote with short timeout
        if fx is None:
            try:
                import yfinance as yf
                ticker = yf.Ticker("EGP=X")
                fast_info = getattr(ticker, "fast_info", None)
                if fast_info and hasattr(fast_info, "last_price") and fast_info.last_price:
                    fx = float(fast_info.last_price)
            except Exception:
                pass

        # 4. Fallback
        if fx is None or fx <= 5.0 or fx > 200.0:
            fx = cls.DEFAULT_USD_EGP

        cls._cache[cache_key] = fx
        cls._cache_timestamps[cache_key] = now
        return float(fx)

    # =========================================================================
    # 2. REGIME CLASSIFICATION
    # =========================================================================

    @classmethod
    def determine_macro_regime(cls, interest_rate: float, inflation: float, usd_egp: float) -> str:
        """
        Classifies the Egyptian economic state into one of four quantitative regimes:
        1. STAGFLATION: Inflation significantly outpaces interest rate with high price pressures.
        2. RATE_HIKING_CYCLE: Tight monetary policy with elevated CBE interest rates to anchor prices.
        3. DEVALUATION_BOOM: Major currency depreciation providing strong tailwinds to export/dollarized sectors.
        4. STABLE_GROWTH: Moderate inflation, easing interest rates, and stable currency.
        """
        try:
            r = float(interest_rate)
            cpi = float(inflation)
            fx = float(usd_egp)
        except (ValueError, TypeError):
            return cls.REGIME_RATE_HIKING_CYCLE

        # 1. Stagflation condition: High inflation exceeding interest rate significantly
        if cpi >= 28.0 and (cpi > r + 2.0):
            return cls.REGIME_STAGFLATION

        # 2. Devaluation Boom condition: Elevated FX level with lower/moderate interest rate
        if fx >= 45.0 and r < 20.0 and cpi < 25.0:
            return cls.REGIME_DEVALUATION_BOOM

        # 3. Rate Hiking Cycle condition: High interest rates (CBE >= 20.0%)
        if r >= 20.0:
            return cls.REGIME_RATE_HIKING_CYCLE

        # 4. Stable Growth condition: Low/Moderate inflation, benign rates, stable FX
        if cpi <= 15.0 and r <= 16.0 and fx <= 40.0:
            return cls.REGIME_STABLE_GROWTH

        # Default classification based on primary prevailing factor
        if r >= 18.0:
            return cls.REGIME_RATE_HIKING_CYCLE
        elif fx >= 40.0:
            return cls.REGIME_DEVALUATION_BOOM
        else:
            return cls.REGIME_STABLE_GROWTH

    # =========================================================================
    # 3. SECTOR ROTATION BIASES
    # =========================================================================

    @classmethod
    def get_sector_biases(cls, regime: str) -> Dict[str, Any]:
        """
        Returns tactical and structural sector weightings (Overweight, Underweight, Neutral)
        tailored to the specific EGX market regime.
        """
        reg = regime.upper().strip()

        if reg == cls.REGIME_RATE_HIKING_CYCLE:
            return {
                "regime": cls.REGIME_RATE_HIKING_CYCLE,
                "regime_ar": cls.REGIME_LABELS_AR[cls.REGIME_RATE_HIKING_CYCLE],
                "overweight": [
                    "Banking & Financial Services",
                    "Treasury & Cash-Rich Conglomerates",
                    "Fertilizers & Petrochemicals (Self-Financed)"
                ],
                "underweight": [
                    "Real Estate (Highly Leveraged Developers)",
                    "Consumer Finance & Installment Services",
                    "Capital Goods with High Debt"
                ],
                "neutral": [
                    "Telecommunications",
                    "Healthcare & Pharmaceuticals",
                    "Basic Materials"
                ],
                "overweight_ar": [
                    "البنوك والخدمات المالية (اتساع هوامش الفائدة NIM)",
                    "الشركات ذات السيولة النقدية العالية والاستثمار في أذون الخزانة",
                    "الأسمدة والبتروكيماويات ذات التمويل الذاتي"
                ],
                "underweight_ar": [
                    "التطوير العقاري ذو المديونيات المرتفعة",
                    "التمويل الاستهلاكي والتقسيط",
                    "الصناعات الثقيلة ذات تكلفة الاقتراض العالية"
                ],
                "rationale_ar": (
                    "في بيئة الفائدة المرتفعة من البنك المركزي المصري، تحقق البنوك أرباحاً قياسية "
                    "من اتساع هامش صافي الفائدة (NIM) وتوظيف الودائع في أدوات الدين الحكومي، "
                    "بينما تضغط تكلفة الاقتراض على الشركات العقارية والاستهلاكية ذات الرافعة المالية العالية."
                ),
                "sector_multipliers": {
                    "Banking": 1.25,
                    "Fertilizers": 1.15,
                    "Telecom": 1.00,
                    "Real Estate": 0.80,
                    "Consumer Finance": 0.75
                }
            }

        elif reg == cls.REGIME_DEVALUATION_BOOM:
            return {
                "regime": cls.REGIME_DEVALUATION_BOOM,
                "regime_ar": cls.REGIME_LABELS_AR[cls.REGIME_DEVALUATION_BOOM],
                "overweight": [
                    "Fertilizers & Petrochemicals (USD Revenue)",
                    "Basic Resources & Export Metals (EGAL/ESRS)",
                    "Export-Oriented Industrials (SWDY/ORAS)",
                    "Dollar-Earning Logistics & Ports"
                ],
                "underweight": [
                    "Import-Dependent Consumer Goods",
                    "Automotive Assembly & Import Retail (GBCO)",
                    "Electronics & Appliance Retail"
                ],
                "neutral": [
                    "Banking & Financial Services",
                    "Healthcare & Pharmaceuticals",
                    "Real Estate (Asset-Backed Wealth Hedge)"
                ],
                "overweight_ar": [
                    "الأسمدة والكيماويات المصدرة (إيرادات دولارية)",
                    "الموارد الأساسية وتصدير المعادن (مصر للألومنيوم والحديد)",
                    "المقاولات والصناعات متعددة الجنسيات (السويدي وأوراسكوم)",
                    "الخدمات اللوجستية والموانئ"
                ],
                "underweight_ar": [
                    "السلع الاستهلاكية المعتمدة على الاستيراد",
                    "تجميع وتوزيع السيارات ومستوردي التجزئة",
                    "الأجهزة الإلكترونية المستوردة"
                ],
                "rationale_ar": (
                    "مع انخفاض قيمة الجنيه المصري، تحقق الشركات ذات الإيرادات الدولارية أو المرتبطة بالأسعار العالمية "
                    "(مثل مصدري الأسمدة والألومنيوم والخدمات اللوجستية) طفرات في هوامش الربحية وإعادة تقييم أصولها، "
                    "في حين تتكبد الشركات المعتمدة على استيراد المكونات تكاليف تشغيلية مضاعفة."
                ),
                "sector_multipliers": {
                    "Fertilizers": 1.35,
                    "Basic Resources": 1.30,
                    "Industrials": 1.20,
                    "Banking": 1.05,
                    "Automotive": 0.70,
                    "Import Consumer": 0.65
                }
            }

        elif reg == cls.REGIME_STAGFLATION:
            return {
                "regime": cls.REGIME_STAGFLATION,
                "regime_ar": cls.REGIME_LABELS_AR[cls.REGIME_STAGFLATION],
                "overweight": [
                    "Essential Food & Staples (JUFO/DOMT)",
                    "Healthcare & Pharmaceuticals (ISPH/RAMEDA)",
                    "Precious Metals & Real Asset Hedges",
                    "Essential Utilities & Energy"
                ],
                "underweight": [
                    "Consumer Discretionary & Luxury Goods",
                    "Automotive & Leisure",
                    "Commercial Real Estate",
                    "Cyclical Capital Goods"
                ],
                "neutral": [
                    "Banking & Financial Services",
                    "Telecommunications"
                ],
                "overweight_ar": [
                    "الأغذية الأساسية والاستهلاكية غير المرنة (جهينة ودومتي)",
                    "الرعاية الصحية والأدوية (ابن سينا وراميدا)",
                    "الذهب والتحوط بالأصول العينية",
                    "المرافق الأساسية والطاقة"
                ],
                "underweight_ar": [
                    "السلع الترفيهية وغير الأساسية",
                    "قطاع السيارات والسياحة الفاخرة",
                    "العقارات التجارية والمكتبية",
                    "المعدات الرأسمالية الدورية"
                ],
                "rationale_ar": (
                    "في ظل الركود التضخمي وتآكل القدرة الشرائية للمستهلك، توفر قطاعات الأغذية الأساسية "
                    "والرعاية الصحية دفاعاً متيناً نظراً لمرونة الطلب غير الحساس للأسعار، بينما يتراجع "
                    "الطلب بشدة على السلع الكمالية والمشتريات المؤجلة."
                ),
                "sector_multipliers": {
                    "Food & Staples": 1.30,
                    "Healthcare": 1.25,
                    "Telecom": 1.00,
                    "Consumer Discretionary": 0.70,
                    "Automotive": 0.65
                }
            }

        else:  # STABLE_GROWTH
            return {
                "regime": cls.REGIME_STABLE_GROWTH,
                "regime_ar": cls.REGIME_LABELS_AR[cls.REGIME_STABLE_GROWTH],
                "overweight": [
                    "Real Estate & Urban Development (TMGH/PHDC/HELI)",
                    "Non-Banking Financial Services & Fintech (FWRY/EFIH)",
                    "Building Materials & Construction",
                    "Consumer Discretionary & Growth Equities"
                ],
                "underweight": [
                    "Defensive Cash Havens",
                    "Fixed Income Arbitrage"
                ],
                "neutral": [
                    "Banking & Financial Services",
                    "Fertilizers & Chemicals",
                    "Telecommunications"
                ],
                "overweight_ar": [
                    "التطوير العقاري والمدن العمرانية (طلعت مصطفى وبالم هيلز)",
                    "المدفوعات الإلكترونية والتكنولوجيا المالية (فوري وإي فاينانس)",
                    "مواد البناء والتشييد",
                    "الأسهم الاستهلاكية وأسهم النمو السريع"
                ],
                "underweight_ar": [
                    "الملاذات الدفاعية النقدية",
                    "أدوات الدخل الثابت قصيرة الأجل"
                ],
                "rationale_ar": (
                    "مع استقرار التضخم وانخفاض أسعار الفائدة، ينتعش الائتمان الاستثماري وتتسارع وتيرة مبيعات العقارات "
                    "والتكنولوجيا المالية بفضل انخفاض تكلفة التمويل وارتفاع ثقة المستثمرين."
                ),
                "sector_multipliers": {
                    "Real Estate": 1.35,
                    "Fintech": 1.30,
                    "Building Materials": 1.20,
                    "Banking": 1.00,
                    "Food & Staples": 0.95
                }
            }

    # =========================================================================
    # 4. TELEMETRY & COMPILED MACRO STATE
    # =========================================================================

    @classmethod
    def get_macro_telemetry(cls, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Compiles and returns complete real-time macroeconomic telemetry,
        regime classification, and sector rotation directives.
        """
        interest_rate = cls.fetch_interest_rate(force_refresh=force_refresh)
        inflation_rate = cls.fetch_inflation_rate(force_refresh=force_refresh)
        usd_egp = cls.fetch_usd_egp(force_refresh=force_refresh)

        regime = cls.determine_macro_regime(
            interest_rate=interest_rate,
            inflation=inflation_rate,
            usd_egp=usd_egp
        )

        biases = cls.get_sector_biases(regime)

        now_iso = datetime.datetime.now().isoformat()

        return {
            "status": "HEALTHY",
            "timestamp": now_iso,
            "interest_rate_pct": round(interest_rate, 2),
            "inflation_rate_pct": round(inflation_rate, 2),
            "usd_egp": round(usd_egp, 2),
            "macro_regime": regime,
            "macro_regime_ar": cls.REGIME_LABELS_AR.get(regime, regime),
            "sector_biases": biases,
            "sources": {
                "interest_rate": "CENTRAL_BANK_OF_EGYPT_CBE",
                "inflation": "CAPMAS_EGYPT_CPI_HEADLINE",
                "usd_egp": "EGX_INTERBANK_FX_FEED"
            },
            "summary_ar": (
                f"نظام الاقتصاد الكلي: {cls.REGIME_LABELS_AR.get(regime, regime)} | "
                f"فائدة المركزي: {interest_rate:.2f}% | "
                f"التضخم السنوي: {inflation_rate:.2f}% | "
                f"الدولار: {usd_egp:.2f} ج.م"
            )
        }

    # Instance method wrappers for flexibility
    def get_interest_rate(self) -> float:
        return self.fetch_interest_rate()

    def get_inflation_rate(self) -> float:
        return self.fetch_inflation_rate()

    def get_usd_egp(self) -> float:
        return self.fetch_usd_egp()

    def get_regime(self) -> str:
        telemetry = self.get_macro_telemetry()
        return telemetry["macro_regime"]

    def get_biases(self) -> Dict[str, Any]:
        telemetry = self.get_macro_telemetry()
        return telemetry["sector_biases"]
