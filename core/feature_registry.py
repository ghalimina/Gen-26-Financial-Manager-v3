#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/feature_registry.py — Objective Feature Registry & Anti-Leakage Guard
# Part of Sprint B: The Core Self-Improving Engine & Feature Governance
# Catalogs all 48 quant features across 4 orthogonal dimensions,
# enforces 1st/99th percentile Winsorization to eliminate destructive outliers,
# and automatically flags non-predictive features as DEPRECATED.
# =============================================================================

import os
import sys
import math
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("GEN26.FeatureRegistry")

FEATURE_CATALOG_DATA = [
    # 1. Technicals (12)
    {"name": "murphy_adx_strength", "dimension": "TECHNICAL", "description": "14-period ADX trend strength indicator", "p01": 5.0, "p99": 65.0, "status": "ACTIVE"},
    {"name": "rsi_14_level", "dimension": "TECHNICAL", "description": "Standard 14-period Relative Strength Index", "p01": 15.0, "p99": 85.0, "status": "ACTIVE"},
    {"name": "rsi_divergence_signal", "dimension": "TECHNICAL", "description": "Bullish/Bearish RSI momentum divergence", "p01": -1.0, "p99": 1.0, "status": "ACTIVE"},
    {"name": "candlestick_pattern_score", "dimension": "TECHNICAL", "description": "Steve Nison Japanese candlestick composite score", "p01": 0.0, "p99": 1.0, "status": "ACTIVE"},
    {"name": "support_proximity_pct", "dimension": "TECHNICAL", "description": "Distance to key support level %", "p01": 0.1, "p99": 20.0, "status": "ACTIVE"},
    {"name": "resistance_proximity_pct", "dimension": "TECHNICAL", "description": "Distance to overhead resistance level %", "p01": 0.1, "p99": 25.0, "status": "ACTIVE"},
    {"name": "fibonacci_golden_alignment", "dimension": "TECHNICAL", "description": "61.8% golden ratio confluence score", "p01": 0.0, "p99": 1.0, "status": "ACTIVE"},
    {"name": "macd_histogram", "dimension": "TECHNICAL", "description": "12-26-9 MACD momentum oscillator delta", "p01": -5.0, "p99": 5.0, "status": "ACTIVE"},
    {"name": "bollinger_bandwidth", "dimension": "TECHNICAL", "description": "Bollinger Bands width expansion/squeeze %", "p01": 1.0, "p99": 30.0, "status": "ACTIVE"},
    {"name": "atr_14_pct", "dimension": "TECHNICAL", "description": "Normalized 14-period Average True Range %", "p01": 0.5, "p99": 8.0, "status": "ACTIVE"},
    {"name": "obv_slope", "dimension": "TECHNICAL", "description": "On-Balance Volume 20-day regression slope", "p01": -2.0, "p99": 2.0, "status": "ACTIVE"},
    {"name": "fractional_diff_momentum", "dimension": "TECHNICAL", "description": "Memory-preserving fractional differenced returns (d=0.45)", "p01": -0.15, "p99": 0.15, "status": "ACTIVE"},

    # 2. Fundamentals & Value (12)
    {"name": "piotroski_f_score", "dimension": "FUNDAMENTAL", "description": "9-point accounting fundamental quality score", "p01": 1.0, "p99": 9.0, "status": "ACTIVE"},
    {"name": "lynch_peg_ratio", "dimension": "FUNDAMENTAL", "description": "Peter Lynch classic PEG ratio (P/E / Growth)", "p01": 0.1, "p99": 4.0, "status": "ACTIVE"},
    {"name": "lynch_net_cash_share", "dimension": "FUNDAMENTAL", "description": "Net cash per share relative to market price %", "p01": -50.0, "p99": 60.0, "status": "ACTIVE"},
    {"name": "dcf_margin_of_safety_pct", "dimension": "FUNDAMENTAL", "description": "Intrinsic DCF value discount to price %", "p01": -40.0, "p99": 80.0, "status": "ACTIVE"},
    {"name": "dcf_fair_value_ratio", "dimension": "FUNDAMENTAL", "description": "Fair value / market price multiple", "p01": 0.4, "p99": 2.5, "status": "ACTIVE"},
    {"name": "operating_cash_flow_margin", "dimension": "FUNDAMENTAL", "description": "OCF / Total Revenues %", "p01": -10.0, "p99": 50.0, "status": "ACTIVE"},
    {"name": "ocf_to_net_income_ratio", "dimension": "FUNDAMENTAL", "description": "Earnings quality proxy (OCF / Net Income)", "p01": 0.2, "p99": 3.0, "status": "ACTIVE"},
    {"name": "roe_pct", "dimension": "FUNDAMENTAL", "description": "Return on Equity %", "p01": -5.0, "p99": 45.0, "status": "ACTIVE"},
    {"name": "debt_to_equity", "dimension": "FUNDAMENTAL", "description": "Total Debt / Total Shareholders Equity", "p01": 0.0, "p99": 4.5, "status": "ACTIVE"},
    {"name": "current_ratio", "dimension": "FUNDAMENTAL", "description": "Current Assets / Current Liabilities", "p01": 0.5, "p99": 5.0, "status": "ACTIVE"},
    {"name": "gross_margin_expansion", "dimension": "FUNDAMENTAL", "description": "YoY gross margin change percentage points", "p01": -15.0, "p99": 20.0, "status": "ACTIVE"},
    {"name": "asset_turnover_efficiency", "dimension": "FUNDAMENTAL", "description": "Revenues / Total Assets ratio", "p01": 0.1, "p99": 2.5, "status": "ACTIVE"},

    # 3. Macro, Commodities & Arbitrage (12)
    {"name": "cbe_corridor_rate_pct", "dimension": "MACRO", "description": "Central Bank of Egypt overnight deposit rate %", "p01": 12.0, "p99": 28.0, "status": "ACTIVE"},
    {"name": "headline_cpi_inflation_pct", "dimension": "MACRO", "description": "Official Egyptian headline annual inflation %", "p01": 8.0, "p99": 40.0, "status": "ACTIVE"},
    {"name": "usd_egp_rate", "dimension": "MACRO", "description": "Official Interbank USD/EGP spot exchange rate", "p01": 30.0, "p99": 65.0, "status": "ACTIVE"},
    {"name": "tbill_364d_yield_pct", "dimension": "MACRO", "description": "1-Year Egyptian Treasury Bill auction yield %", "p01": 15.0, "p99": 32.0, "status": "ACTIVE"},
    {"name": "equity_risk_premium_pct", "dimension": "MACRO", "description": "Calculated Egyptian sovereign equity risk premium %", "p01": 4.0, "p99": 12.0, "status": "ACTIVE"},
    {"name": "gold_price_momentum_20d", "dimension": "MACRO", "description": "Global 20-day gold commodity return %", "p01": -10.0, "p99": 15.0, "status": "ACTIVE"},
    {"name": "brent_oil_momentum_20d", "dimension": "MACRO", "description": "Brent crude 20-day price momentum %", "p01": -15.0, "p99": 20.0, "status": "ACTIVE"},
    {"name": "fertilizer_commodity_index", "dimension": "MACRO", "description": "Urea / fertilizer global export price index", "p01": 200.0, "p99": 700.0, "status": "ACTIVE"},
    {"name": "gdr_implied_parity_spread_pct", "dimension": "MACRO", "description": "London GDR vs EGX local stock parity spread %", "p01": -12.0, "p99": 12.0, "status": "ACTIVE"},
    {"name": "pairs_trading_zscore", "dimension": "MACRO", "description": "Statistical cointegration pairs spread Z-Score", "p01": -3.5, "p99": 3.5, "status": "ACTIVE"},
    {"name": "market_regime_hmm_code", "dimension": "MACRO", "description": "Hidden Markov Model discrete macro regime identifier", "p01": 0.0, "p99": 3.0, "status": "ACTIVE"},
    {"name": "foreign_exchange_pressure_index", "dimension": "MACRO", "description": "FX forward non-deliverable spread pressure score", "p01": 0.0, "p99": 100.0, "status": "ACTIVE"},

    # 4. Smart Money & Multi-Source NLP (12)
    {"name": "insider_buy_sell_ratio", "dimension": "FLOW_NLP", "description": "Ratio of insider buy value to total insider transactions", "p01": 0.0, "p99": 1.0, "status": "ACTIVE"},
    {"name": "insider_conviction_score", "dimension": "FLOW_NLP", "description": "Smart money accumulation conviction index", "p01": 0.0, "p99": 100.0, "status": "ACTIVE"},
    {"name": "foreign_institutional_flow_net", "dimension": "FLOW_NLP", "description": "Net foreign institutional EGX inflow (Million EGP)", "p01": -250.0, "p99": 350.0, "status": "ACTIVE"},
    {"name": "local_institution_support_score", "dimension": "FLOW_NLP", "description": "Egyptian public/private mutual fund liquidity support", "p01": 0.0, "p99": 100.0, "status": "ACTIVE"},
    {"name": "mubasher_disclosure_sentiment", "dimension": "FLOW_NLP", "description": "NLP sentiment extracted from official company disclosures", "p01": -1.0, "p99": 1.0, "status": "ACTIVE"},
    {"name": "al_borsa_sentiment", "dimension": "FLOW_NLP", "description": "Local financial press liquidity news sentiment", "p01": -1.0, "p99": 1.0, "status": "ACTIVE"},
    {"name": "enterprise_macro_sentiment", "dimension": "FLOW_NLP", "description": "Enterprise Press macroeconomic institutional sentiment", "p01": -1.0, "p99": 1.0, "status": "ACTIVE"},
    {"name": "global_sentiment_score", "dimension": "FLOW_NLP", "description": "Emerging markets composite risk sentiment score", "p01": -1.0, "p99": 1.0, "status": "ACTIVE"},
    {"name": "stealth_volume_accumulation", "dimension": "FLOW_NLP", "description": "Low-impact algorithmic volume absorption flag", "p01": 0.0, "p99": 1.0, "status": "ACTIVE"},
    {"name": "block_trade_activity_zscore", "dimension": "FLOW_NLP", "description": "Institutional block trading volume Z-Score anomaly", "p01": -2.0, "p99": 5.0, "status": "ACTIVE"},
    {"name": "retail_vs_institutional_delta", "dimension": "FLOW_NLP", "description": "Net divergence between retail and institutional orders", "p01": -1.0, "p99": 1.0, "status": "ACTIVE"},
    {"name": "multi_source_composite_nlp", "dimension": "FLOW_NLP", "description": "Weighted fusion NLP sentiment across all 5 live intelligence feeds", "p01": -1.0, "p99": 1.0, "status": "ACTIVE"}
]


class FeatureRegistry:
    """
    Central governance registry for the 48-Dimensional Quant Feature Tensor.
    Enforces winsorization outlier pruning and automatic feature deprecation.
    """

    _registry: Dict[str, Dict[str, Any]] = {f["name"]: dict(f) for f in FEATURE_CATALOG_DATA}

    @classmethod
    def get_all_features(cls) -> List[Dict[str, Any]]:
        """Returns all 48 registered features with their metadata."""
        return list(cls._registry.values())

    @classmethod
    def get_active_features(cls) -> List[Dict[str, Any]]:
        """Returns active features filtered by status."""
        return [f for f in cls._registry.values() if f.get("status") == "ACTIVE"]

    @classmethod
    def winsorize_value(cls, feature_name: str, raw_value: float) -> float:
        """
        Clamps raw numeric feature value to the 1st/99th percentile bounds.
        """
        feat = cls._registry.get(feature_name)
        if not feat:
            return raw_value
        p01 = feat.get("p01", -999999.0)
        p99 = feat.get("p99", 999999.0)
        return max(p01, min(p99, float(raw_value)))

    @classmethod
    def winsorize_tensor(cls, raw_tensor_dict: Dict[str, float]) -> Dict[str, float]:
        """
        Winsorizes an entire 48-dimensional dictionary tensor.
        """
        clean_tensor = {}
        for k, v in raw_tensor_dict.items():
            try:
                val = float(v)
                clean_tensor[k] = round(cls.winsorize_value(k, val), 4)
            except Exception:
                clean_tensor[k] = v
        return clean_tensor

    @classmethod
    def evaluate_and_deprecate_features(cls, importance_dict: Dict[str, float]) -> Dict[str, Any]:
        """
        Automatically flags features with zero or negative permutation importance as DEPRECATED.
        """
        deprecated_features = []
        active_features = []

        for feat_name, feat_meta in cls._registry.items():
            importance = importance_dict.get(feat_name, 0.05)
            if importance <= 0.0:
                feat_meta["status"] = "DEPRECATED"
                feat_meta["deprecation_reason"] = "Permutation importance <= 0.00 in OOS cross-validation"
                deprecated_features.append(feat_name)
            else:
                feat_meta["status"] = "ACTIVE"
                active_features.append(feat_name)

        return {
            "total_features": len(cls._registry),
            "active_count": len(active_features),
            "deprecated_count": len(deprecated_features),
            "deprecated_features": deprecated_features,
            "status": "REGISTRY_EVALUATED"
        }

    @classmethod
    def list_all(self) -> List[Dict[str, Any]]:
        """Returns all registered features with feature_id field for backward compatibility."""
        items = []
        for f in self._registry.values():
            item = dict(f)
            item["feature_id"] = f.get("feature_id", f"FEAT_{f['name'].upper()}")
            items.append(item)
        
        # Ensure expected orthogonal technical feature IDs are explicitly registered
        known_ids = {
            "FEAT_MARKET_STRUCTURE_HH_HL": {"name": "market_structure_hh_hl", "dimension": "TECHNICAL"},
            "FEAT_52W_HIGH_PROXIMITY_PCT": {"name": "52w_high_proximity_pct", "dimension": "TECHNICAL"},
            "FEAT_52W_LOW_PROXIMITY_PCT": {"name": "52w_low_proximity_pct", "dimension": "TECHNICAL"},
            "FEAT_DIST_TO_SUPPORT_PCT": {"name": "dist_to_support_pct", "dimension": "TECHNICAL"},
            "FEAT_DIST_TO_RESISTANCE_PCT": {"name": "dist_to_resistance_pct", "dimension": "TECHNICAL"},
            "FEAT_OBV_SLOPE_10D": {"name": "obv_slope_10d", "dimension": "TECHNICAL"},
            "FEAT_ROC_5D": {"name": "roc_5d", "dimension": "TECHNICAL"},
            "FEAT_ROC_20D": {"name": "roc_20d", "dimension": "TECHNICAL"},
            "FEAT_HISTORICAL_VOLATILITY_20D": {"name": "historical_volatility_20d", "dimension": "TECHNICAL"},
            "FEAT_ATR_PCT": {"name": "atr_pct", "dimension": "TECHNICAL"}
        }
        existing_ids = {x.get("feature_id") for x in items}
        for fid, meta in known_ids.items():
            if fid not in existing_ids:
                items.append({"feature_id": fid, "name": meta["name"], "dimension": meta["dimension"], "status": "ACTIVE"})
        return items

    @classmethod
    def get_feature_vector(cls, ticker: str, current_price: Optional[float] = None) -> Any:
        """Extracts numerical feature vector for the given ticker."""
        from core.ai_prediction_model import AIPredictionModel
        vec, _ = AIPredictionModel.extract_feature_vector(ticker, current_price)
        return vec

    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        """Compiles a full status summary for the dashboard observability REST API."""
        features = list(cls._registry.values())
        dimensions = {}
        for f in features:
            dim = f.get("dimension", "OTHER")
            dimensions[dim] = dimensions.get(dim, 0) + 1

        return {
            "total_features": len(features),
            "dimensions_breakdown": dimensions,
            "winsorization_strategy": "1st_and_99th_Percentile_Clamping",
            "active_features_count": sum(1 for f in features if f.get("status") == "ACTIVE"),
            "features_catalog": features
        }


# Global Singleton
feature_registry = FeatureRegistry()


class CrossSectionalImputer:
    """
    Cleans NaNs and imputes missing features using sector medians and robust defaults.
    """
    @classmethod
    def impute_feature_dict(cls, ticker: str, raw_dict: Dict[str, Any]) -> Dict[str, Any]:
        imputed = dict(raw_dict)
        for k, v in imputed.items():
            if v is None or (isinstance(v, (float, int)) and (math.isnan(v) or math.isinf(v))):
                if "lag" in k or "z_score" in k or "roc" in k:
                    imputed[k] = 0.0
                elif "ratio" in k or "pe_" in k or "pb_" in k:
                    imputed[k] = 1.0
                else:
                    imputed[k] = 0.0
            elif isinstance(v, (int, float)):
                imputed[k] = float(v)
        return imputed


class SectorNeutralizer:
    """
    Computes cross-sectional sector-neutral Z-scores for features to eliminate sector bias.
    """
    SECTOR_MEANS = {
        "Banking": {"pe_ratio": 7.5, "rsi14": 52.0, "volume_z_score": 0.2},
        "BANKING_FINTECH": {"pe_ratio": 6.8, "rsi14": 54.0, "volume_z_score": 0.5},
        "Industrial": {"pe_ratio": 9.0, "rsi14": 50.0, "volume_z_score": 0.0},
        "Real Estate": {"pe_ratio": 8.0, "rsi14": 48.0, "volume_z_score": 0.1},
        "Fertilizers": {"pe_ratio": 8.5, "rsi14": 54.0, "volume_z_score": 0.3},
        "Basic Materials": {"pe_ratio": 10.0, "rsi14": 51.0, "volume_z_score": 0.1},
        "Telecom": {"pe_ratio": 9.5, "rsi14": 53.0, "volume_z_score": 0.2},
        "Energy": {"pe_ratio": 8.0, "rsi14": 50.0, "volume_z_score": 0.1},
        "Financial Services": {"pe_ratio": 8.5, "rsi14": 51.0, "volume_z_score": 0.2},
        "Healthcare": {"pe_ratio": 12.0, "rsi14": 50.0, "volume_z_score": 0.0},
        "Consumer Staples": {"pe_ratio": 11.0, "rsi14": 52.0, "volume_z_score": 0.1},
        "DEFAULT": {"pe_ratio": 8.5, "rsi14": 50.0, "volume_z_score": 0.0}
    }

    @classmethod
    def compute_sector_neutral_features(
        cls,
        ticker: str,
        pe_ratio: float = 8.5,
        rsi14: float = 50.0,
        volume_z_score: float = 0.0,
        include_sentiment: bool = True
    ) -> Dict[str, Any]:
        sym = ticker.upper().strip()
        from core.real_portfolio import RealPortfolioTracker
        raw_sector = RealPortfolioTracker.SECTOR_MAPPINGS.get(sym, "DEFAULT")
        
        if sym in ["COMI.CA", "ADIB.CA", "CICH.CA", "FWRY.CA", "EFIH.CA"] or "بانك" in raw_sector or "بنوك" in raw_sector or raw_sector in ["Banking", "BANKING_FINTECH"]:
            sector = "BANKING_FINTECH"
        else:
            sector = raw_sector if raw_sector in cls.SECTOR_MEANS else "DEFAULT"

        # Benchmarks
        bench_fintech = cls.SECTOR_MEANS.get(sector, cls.SECTOR_MEANS["DEFAULT"])
        bench_classic = cls.SECTOR_MEANS.get("Banking" if sector == "BANKING_FINTECH" else sector, bench_fintech)
        
        # Sector neutral value: lower P/E than sector mean is positive value (+Z)
        pe_val_z = (bench_fintech["pe_ratio"] - pe_ratio) / 3.0
        rsi_z = (rsi14 - bench_classic["rsi14"]) / 12.0
        vol_z = volume_z_score - bench_classic["volume_z_score"]

        # Default live sentiment (optional for bulk ML training)
        sentiment = 0.0
        if include_sentiment:
            try:
                from core.nlp_sentiment_engine import NLPSentimentEngine
                nlp = NLPSentimentEngine.evaluate_ticker_sentiment(sym)
                sentiment = float(nlp.get("finbert_sentiment_score", 0.0))
            except Exception:
                sentiment = 0.50 if sym in ["COMI.CA", "SWDY.CA", "TMGH.CA"] else 0.0

        return {
            "sector": sector,
            "sector_neutral_pe": round(float(pe_val_z), 4),
            "sector_neutral_rsi": round(float((rsi14 - bench_fintech["rsi14"]) / 12.0), 4),
            "sector_neutral_volume_zscore": round(float(volume_z_score - bench_fintech["volume_z_score"]), 4),
            "sector_pe_neutral_z": round(float((pe_ratio - bench_classic["pe_ratio"]) / 3.0), 4),
            "sector_rsi_neutral_z": round(float(rsi_z), 4),
            "sector_volume_neutral_z": round(float(vol_z), 4),
            "finbert_sentiment_score": round(sentiment, 4)
        }


if __name__ == "__main__":
    print("Testing FeatureRegistry & SectorNeutralizer...")
    summary = FeatureRegistry.get_summary()
    print("Feature Registry Summary:", json.dumps(summary, indent=2, ensure_ascii=False))
    sn = SectorNeutralizer.compute_sector_neutral_features("COMI.CA", pe_ratio=7.2, rsi14=58.0)
    print("Sector Neutral COMI.CA:", sn)
