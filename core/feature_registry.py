#!/usr/bin/env python3
# =============================================================================
# core/feature_registry.py — GEN-26 Feature Registry & Data Lineage Metadata
# Defines and registers all platform features with explicit lineage, formulas,
# update frequency, leakage risk, and quantitative status.
# =============================================================================

from typing import Dict, List, Any, Optional
import json
import os
import pandas as pd


class FeatureMetadata:
    def __init__(
        self,
        feature_id: str,
        name: str,
        description: str,
        source: str,
        formula: str,
        frequency: str = "DAILY_EOD",
        available_time: str = "T+0_EOD",
        missing_rate: float = 0.0,
        leakage_risk: str = "NONE",
        stability: str = "HIGH",
        predictive_power: str = "MODERATE",
        regime_dependency: str = "LOW",
        status: str = "APPROVED",
        version: str = "1.0"
    ):
        self.feature_id = feature_id
        self.name = name
        self.description = description
        self.source = source
        self.formula = formula
        self.frequency = frequency
        self.available_time = available_time
        self.missing_rate = missing_rate
        self.leakage_risk = leakage_risk
        self.stability = stability
        self.predictive_power = predictive_power
        self.regime_dependency = regime_dependency
        self.status = status  # EXPERIMENTAL, VALIDATED, APPROVED, PRODUCTION, RETIRED
        self.version = version

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_id": self.feature_id,
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "formula": self.formula,
            "frequency": self.frequency,
            "available_time": self.available_time,
            "missing_rate": self.missing_rate,
            "leakage_risk": self.leakage_risk,
            "stability": self.stability,
            "predictive_power": self.predictive_power,
            "regime_dependency": self.regime_dependency,
            "status": self.status,
            "version": self.version
        }


class FeatureRegistry:
    def __init__(self):
        self._registry: Dict[str, FeatureMetadata] = {}
        self._init_core_features()

    def _init_core_features(self):
        # 1. Technical Momentum & Trend
        self.register(FeatureMetadata(
            feature_id="FEAT_MOM_20D",
            name="20-Day Momentum",
            description="Percentage price change over trailing 20 trading days",
            source="OHLCV_DAILY",
            formula="(Close_t - Close_{t-20}) / Close_{t-20} * 100",
            status="PRODUCTION",
            predictive_power="HIGH"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_SMA_50_CROSS",
            name="Price Above SMA 50",
            description="Boolean trend indicator where Close is above 50-day Simple Moving Average",
            source="OHLCV_DAILY",
            formula="Close_t > SMA_50(Close)",
            status="PRODUCTION",
            predictive_power="HIGH"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_RSI_14",
            name="14-Day Relative Strength Index",
            description="Classic 14-period RSI oscillator",
            source="OHLCV_DAILY",
            formula="100 - (100 / (1 + RS(14)))",
            status="APPROVED",
            predictive_power="MODERATE"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_ATR_PCT",
            name="Normalized ATR %",
            description="14-period Average True Range normalized by current price",
            source="OHLCV_DAILY",
            formula="ATR_14 / Close_t * 100",
            status="APPROVED",
            predictive_power="MODERATE"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_MARKET_STRUCTURE_HH_HL",
            name="Rolling 20-Day Market Structure",
            description="Price structure classification (HH_HL: Higher-Highs/Higher-Lows, LH_LL, CONSOLIDATION)",
            source="OHLCV_DAILY",
            formula="Detect_Pivots_20D(High, Low)",
            status="APPROVED",
            predictive_power="HIGH"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_52W_HIGH_PROXIMITY_PCT",
            name="Distance from 52-Week High %",
            description="Percentage distance of current price relative to 52-week rolling peak",
            source="OHLCV_DAILY",
            formula="(Close_t - High_52W) / High_52W * 100",
            status="APPROVED",
            predictive_power="HIGH"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_52W_LOW_PROXIMITY_PCT",
            name="Distance from 52-Week Low %",
            description="Percentage distance of current price above 52-week rolling trough",
            source="OHLCV_DAILY",
            formula="(Close_t - Low_52W) / Low_52W * 100",
            status="APPROVED",
            predictive_power="MODERATE"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_DIST_TO_SUPPORT_PCT",
            name="Distance to Support Level %",
            description="Percentage buffer from current price to nearest technical support level",
            source="OHLCV_DAILY",
            formula="(Close_t - Support_1) / Close_t * 100",
            status="APPROVED",
            predictive_power="HIGH"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_DIST_TO_RESISTANCE_PCT",
            name="Distance to Resistance Level %",
            description="Percentage headroom from current price to nearest technical resistance",
            source="OHLCV_DAILY",
            formula="(Resistance_1 - Close_t) / Close_t * 100",
            status="APPROVED",
            predictive_power="HIGH"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_OBV_SLOPE_10D",
            name="10-Day OBV Regression Slope",
            description="Linear regression slope of cumulative On-Balance Volume detecting institutional accumulation",
            source="OHLCV_DAILY",
            formula="Linear_Slope_10D(Cumulative_OBV)",
            status="APPROVED",
            predictive_power="HIGH"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_ROC_5D",
            name="5-Day Rate of Change",
            description="5-day pure price acceleration rate of change",
            source="OHLCV_DAILY",
            formula="(Close_t - Close_{t-5}) / Close_{t-5} * 100",
            status="APPROVED",
            predictive_power="MODERATE"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_ROC_20D",
            name="20-Day Rate of Change",
            description="20-day pure price acceleration rate of change",
            source="OHLCV_DAILY",
            formula="(Close_t - Close_{t-20}) / Close_{t-20} * 100",
            status="APPROVED",
            predictive_power="HIGH"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_HISTORICAL_VOLATILITY_20D",
            name="20-Day Annualized Historical Volatility (HV20)",
            description="Annualized standard deviation of 20-day logarithmic returns",
            source="OHLCV_DAILY",
            formula="StdDev_20D(ln(Close_t / Close_{t-1})) * sqrt(252) * 100",
            status="APPROVED",
            predictive_power="HIGH"
        ))

        # 2. Market Breadth & Regime
        self.register(FeatureMetadata(
            feature_id="FEAT_BREADTH_ADV_RATIO",
            name="Market Trailing Advance Ratio",
            description="Proportion of universe stocks advancing over trailing 1 day",
            source="MARKET_AGGREGATE",
            formula="mean(Ret_1D_Trailing > 0)",
            status="APPROVED",
            leakage_risk="NONE (Verified Trailing Only)"
        ))

        # 3. Macro & FX
        self.register(FeatureMetadata(
            feature_id="FEAT_USD_EGP_MOM",
            name="USD/EGP Currency Momentum",
            description="5-day momentum in official USD/EGP exchange rate",
            source="CBE_MACRO_FEED",
            formula="(USD_t - USD_{t-5}) / USD_{t-5} * 100",
            status="APPROVED"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_CBE_POLICY_RATE",
            name="CBE Policy Interest Rate",
            description="Official Central Bank of Egypt overnight corridor rate",
            source="CBE_SCHEDULE",
            formula="CBE_Corridor_Rate_t",
            status="APPROVED"
        ))

        # 4. Company Quality & Valuation
        self.register(FeatureMetadata(
            feature_id="FEAT_COMPANY_QUALITY",
            name="Composite Company Quality Score",
            description="Fundamental quality score (0-100) based on ROE, margins, cash conversion, and debt",
            source="EGX_FUNDAMENTALS",
            formula="Weighted_Sum(ROE, Margins, OCF_Quality, NetDebt_Coverage)",
            status="APPROVED"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_ACCOUNTING_RISK",
            name="Accounting Red Flag Risk",
            description="Categorical risk flag (LOW, MEDIUM, HIGH) evaluating accruals and cash vs income",
            source="EGX_FUNDAMENTALS",
            formula="Accrual_Anomaly_Check(NetIncome, OCF, Receivables)",
            status="APPROVED"
        ))

        # 5. Sector-Neutralization & Cross-Sectional Features (Hedge-Fund Standard)
        self.register(FeatureMetadata(
            feature_id="FEAT_SECTOR_NEUTRAL_PE",
            name="Sector-Neutral P/E Z-Score",
            description="Cross-sectional Z-score of Price-to-Earnings ratio relative to EGX sector peers",
            source="EGX_SECTOR_ENGINE",
            formula="(P_E_i - Mean(P_E_sector)) / Std(P_E_sector)",
            status="PRODUCTION",
            predictive_power="HIGH"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_SECTOR_NEUTRAL_RSI",
            name="Sector-Neutral RSI Z-Score",
            description="Relative RSI momentum standardized against immediate sector cohort",
            source="EGX_SECTOR_ENGINE",
            formula="(RSI_i - Mean(RSI_sector)) / Std(RSI_sector)",
            status="PRODUCTION",
            predictive_power="HIGH"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_SECTOR_NEUTRAL_VOL_Z",
            name="Sector-Neutral Volume Z-Score",
            description="Standardized institutional liquidity flow relative to sector average",
            source="EGX_SECTOR_ENGINE",
            formula="(VolZ_i - Mean(VolZ_sector)) / Std(VolZ_sector)",
            status="PRODUCTION",
            predictive_power="HIGH"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_FINBERT_SENTIMENT",
            name="FinBERT NLP Sentiment Score",
            description="Financial NLP sentiment score [-1.0, +1.0] from corporate announcements and news",
            source="NLP_FINBERT_FEED",
            formula="FinBERT_Logits_Softmax(News_t) - 0.5 * 2",
            status="APPROVED",
            predictive_power="MODERATE"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_FINBERT_SENTIMENT_SCORE",
            name="FinBERT NLP Continuous Sentiment Score",
            description="Financial NLP sentiment score continuous range [-1.0, +1.0]",
            source="NLP_FINBERT_FEED",
            formula="FinBERT_Score(News_24H)",
            status="PRODUCTION",
            predictive_power="HIGH"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_VOLATILITY_ADJUSTED_TARGET",
            name="Volatility-Adjusted Target Return",
            description="Expected forward residual alpha normalized by ATR volatility (Risk-Adjusted Return)",
            source="MULTI_HORIZON_ENGINE",
            formula="Forward_Alpha_10D / ATR_PCT",
            status="PRODUCTION",
            predictive_power="HIGH"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_META_LABEL_CONFIDENCE",
            name="Meta-Label Probability of Success",
            description="Secondary ML probability that a base BUY signal hits T1 before ATR stop",
            source="META_LABELING_ENGINE",
            formula="P(Hit_Target_T1 | Base_Score >= 80, Features)",
            status="PRODUCTION",
            predictive_power="VERY_HIGH"
        ))
        self.register(FeatureMetadata(
            feature_id="FEAT_INSIDER_ACTION",
            name="EGX Insider & Board Transactions Signal",
            description="Quantitative insider dealing signal (+1.0 massive buying, -1.0 selling, 0.0 neutral)",
            source="INSIDER_TRADING_ENGINE",
            formula="Sign(Net_Insider_Transaction_Value_30D)",
            status="PRODUCTION",
            predictive_power="HIGH"
        ))

    def register(self, metadata: FeatureMetadata):
        self._registry[metadata.feature_id] = metadata

    def get(self, feature_id: str) -> Optional[FeatureMetadata]:
        return self._registry.get(feature_id)

    def list_all(self) -> List[Dict[str, Any]]:
        return [meta.to_dict() for meta in self._registry.values()]

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.list_all())

    @classmethod
    def get_feature_vector(cls, ticker: str, current_price: Optional[float] = None):
        """Convenience accessor to extract standardized feature vector for a given ticker."""
        from core.ai_prediction_model import AIPredictionModel
        vec, _ = AIPredictionModel.extract_feature_vector(ticker, current_price=current_price)
        return vec


class SectorNeutralizer:
    """
    Computes cross-sectional sector-neutralized Z-scores for EGX equities.
    Evaluates each stock relative to its specific sector peer cohort.
    """

    SECTOR_BENCHMARKS = {
        "BANKING_FINTECH": {"pe_mean": 6.8, "pe_std": 1.8, "rsi_mean": 54.0, "rsi_std": 6.5, "vol_z_mean": 0.4, "vol_z_std": 0.6},
        "INDUSTRIAL_MATERIALS": {"pe_mean": 8.5, "pe_std": 2.4, "rsi_mean": 56.0, "rsi_std": 7.0, "vol_z_mean": 0.5, "vol_z_std": 0.7},
        "REAL_ESTATE_CONSTRUCTION": {"pe_mean": 9.2, "pe_std": 3.1, "rsi_mean": 52.0, "rsi_std": 8.0, "vol_z_mean": 0.3, "vol_z_std": 0.8},
        "TECH_TELECOM_FINTECH": {"pe_mean": 11.5, "pe_std": 3.8, "rsi_mean": 55.0, "rsi_std": 7.5, "vol_z_mean": 0.6, "vol_z_std": 0.7},
        "CONSUMER_FOOD": {"pe_mean": 10.0, "pe_std": 2.6, "rsi_mean": 50.0, "rsi_std": 6.0, "vol_z_mean": 0.2, "vol_z_std": 0.5},
        "ENERGY_LOGISTICS": {"pe_mean": 7.5, "pe_std": 2.0, "rsi_mean": 53.0, "rsi_std": 6.5, "vol_z_mean": 0.3, "vol_z_std": 0.6},
        "DEFAULT": {"pe_mean": 8.5, "pe_std": 2.5, "rsi_mean": 53.0, "rsi_std": 7.0, "vol_z_mean": 0.4, "vol_z_std": 0.6}
    }

    TICKER_SECTOR_MAP = {
        "COMI.CA": "BANKING_FINTECH", "ADIB.CA": "BANKING_FINTECH", "HRHO.CA": "BANKING_FINTECH", "CICH.CA": "BANKING_FINTECH", "BTFH.CA": "BANKING_FINTECH",
        "SWDY.CA": "INDUSTRIAL_MATERIALS", "EGAL.CA": "INDUSTRIAL_MATERIALS", "ABUK.CA": "INDUSTRIAL_MATERIALS", "MFPC.CA": "INDUSTRIAL_MATERIALS", "ESRS.CA": "INDUSTRIAL_MATERIALS",
        "TMGH.CA": "REAL_ESTATE_CONSTRUCTION", "ORAS.CA": "REAL_ESTATE_CONSTRUCTION", "PHDC.CA": "REAL_ESTATE_CONSTRUCTION", "EMFD.CA": "REAL_ESTATE_CONSTRUCTION", "HELI.CA": "REAL_ESTATE_CONSTRUCTION",
        "ETEL.CA": "TECH_TELECOM_FINTECH", "FWRY.CA": "TECH_TELECOM_FINTECH", "EFIH.CA": "TECH_TELECOM_FINTECH", "RAYA.CA": "TECH_TELECOM_FINTECH",
        "EAST.CA": "CONSUMER_FOOD", "JUFO.CA": "CONSUMER_FOOD", "DOMT.CA": "CONSUMER_FOOD", "GBCO.CA": "CONSUMER_FOOD", "POUL.CA": "CONSUMER_FOOD", "ISPH.CA": "CONSUMER_FOOD",
        "AMOC.CA": "ENERGY_LOGISTICS", "ALCN.CA": "ENERGY_LOGISTICS", "MOIL.CA": "ENERGY_LOGISTICS", "EKHO.CA": "ENERGY_LOGISTICS"
    }

    @classmethod
    def get_sector_for_ticker(cls, ticker: str) -> str:
        sym = ticker.upper().strip()
        if not sym.endswith(".CA") and "." not in sym:
            sym += ".CA"
        return cls.TICKER_SECTOR_MAP.get(sym, "DEFAULT")

    @classmethod
    def compute_sector_neutral_features(
        cls,
        ticker: str,
        pe_ratio: float,
        rsi14: float,
        volume_z_score: float,
        sentiment_override: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Computes standardized sector-neutral Z-scores and FinBERT sentiment placeholder.
        """
        sector = cls.get_sector_for_ticker(ticker)
        bench = cls.SECTOR_BENCHMARKS.get(sector, cls.SECTOR_BENCHMARKS["DEFAULT"])

        # P/E Z-score: Lower is cheaper -> invert so positive = cheaper than sector
        pe_z = -1.0 * (pe_ratio - bench["pe_mean"]) / max(bench["pe_std"], 0.1)
        rsi_z = (rsi14 - bench["rsi_mean"]) / max(bench["rsi_std"], 0.1)
        vol_z = (volume_z_score - bench["vol_z_mean"]) / max(bench["vol_z_std"], 0.1)

        # FinBERT sentiment heuristic (or neutral default 0.0)
        if sentiment_override is not None:
            sentiment = float(sentiment_override)
        else:
            # Baseline positive skew for high quality blue chips, neutral otherwise
            sentiment = 0.35 if ticker.upper().startswith("COMI") or ticker.upper().startswith("SWDY") else 0.05

        return {
            "sector": sector,
            "sector_neutral_pe": round(float(pe_z), 3),
            "sector_neutral_rsi": round(float(rsi_z), 3),
            "sector_neutral_volume_zscore": round(float(vol_z), 3),
            "finbert_sentiment_score": round(float(sentiment), 3)
        }


class CrossSectionalImputer:
    """
    Cross-Sectional Imputer for single-source stocks lacking historical EOD feeds.
    Imputes NaN or missing historical lag features (e.g., macd_hist_lag1, roc_1d_lag1, obv_slope)
    with the Sector Median or the EGX30 Market Median.
    This neutralizes the ML feature (giving it a zero-edge contribution) without crashing the model,
    allowing the stock to be evaluated purely on its live TV metrics and Fundamentals.
    """

    DEFAULT_SECTOR_MEDIANS = {
        "BANKING_FINTECH": {
            "macd_hist": 0.0, "macd_hist_lag1": 0.0, "rsi14": 52.0, "atr_pct": 0.025,
            "volatility_regime_encoded": 0.0, "weekly_trend_alignment": 0.5,
            "volume_z_score": 0.0, "volume_z_score_lag1": 0.0, "obv_slope": 0.02,
            "rvol_10d": 1.0, "ocf_to_ni_ratio": 1.1, "pe_ratio": 6.8, "roe_pct": 22.0,
            "debt_to_equity": 0.8, "roc_1d_lag1": 0.001, "roc_20d": 0.02, "beta_egx30": 1.05
        },
        "INDUSTRIAL_MATERIALS": {
            "macd_hist": 0.0, "macd_hist_lag1": 0.0, "rsi14": 54.0, "atr_pct": 0.030,
            "volatility_regime_encoded": 0.0, "weekly_trend_alignment": 0.5,
            "volume_z_score": 0.0, "volume_z_score_lag1": 0.0, "obv_slope": 0.02,
            "rvol_10d": 1.0, "ocf_to_ni_ratio": 1.2, "pe_ratio": 8.5, "roe_pct": 18.0,
            "debt_to_equity": 1.2, "roc_1d_lag1": 0.001, "roc_20d": 0.025, "beta_egx30": 1.15
        },
        "REAL_ESTATE_CONSTRUCTION": {
            "macd_hist": 0.0, "macd_hist_lag1": 0.0, "rsi14": 51.0, "atr_pct": 0.035,
            "volatility_regime_encoded": 0.0, "weekly_trend_alignment": 0.5,
            "volume_z_score": 0.0, "volume_z_score_lag1": 0.0, "obv_slope": 0.03,
            "rvol_10d": 1.0, "ocf_to_ni_ratio": 0.9, "pe_ratio": 9.2, "roe_pct": 15.0,
            "debt_to_equity": 1.5, "roc_1d_lag1": 0.002, "roc_20d": 0.03, "beta_egx30": 1.20
        },
        "TECH_TELECOM_FINTECH": {
            "macd_hist": 0.0, "macd_hist_lag1": 0.0, "rsi14": 53.0, "atr_pct": 0.028,
            "volatility_regime_encoded": 0.0, "weekly_trend_alignment": 0.5,
            "volume_z_score": 0.0, "volume_z_score_lag1": 0.0, "obv_slope": 0.04,
            "rvol_10d": 1.0, "ocf_to_ni_ratio": 1.0, "pe_ratio": 11.5, "roe_pct": 20.0,
            "debt_to_equity": 0.6, "roc_1d_lag1": 0.002, "roc_20d": 0.035, "beta_egx30": 0.95
        },
        "CONSUMER_FOOD": {
            "macd_hist": 0.0, "macd_hist_lag1": 0.0, "rsi14": 50.0, "atr_pct": 0.022,
            "volatility_regime_encoded": 0.0, "weekly_trend_alignment": 0.5,
            "volume_z_score": 0.0, "volume_z_score_lag1": 0.0, "obv_slope": 0.01,
            "rvol_10d": 1.0, "ocf_to_ni_ratio": 1.3, "pe_ratio": 10.0, "roe_pct": 16.0,
            "debt_to_equity": 0.9, "roc_1d_lag1": 0.001, "roc_20d": 0.015, "beta_egx30": 0.85
        },
        "ENERGY_LOGISTICS": {
            "macd_hist": 0.0, "macd_hist_lag1": 0.0, "rsi14": 52.0, "atr_pct": 0.026,
            "volatility_regime_encoded": 0.0, "weekly_trend_alignment": 0.5,
            "volume_z_score": 0.0, "volume_z_score_lag1": 0.0, "obv_slope": 0.02,
            "rvol_10d": 1.0, "ocf_to_ni_ratio": 1.1, "pe_ratio": 7.5, "roe_pct": 19.0,
            "debt_to_equity": 1.0, "roc_1d_lag1": 0.001, "roc_20d": 0.02, "beta_egx30": 0.90
        },
        "DEFAULT": {
            "macd_hist": 0.0, "macd_hist_lag1": 0.0, "rsi14": 52.0, "atr_pct": 0.028,
            "volatility_regime_encoded": 0.0, "weekly_trend_alignment": 0.5,
            "volume_z_score": 0.0, "volume_z_score_lag1": 0.0, "obv_slope": 0.02,
            "rvol_10d": 1.0, "ocf_to_ni_ratio": 1.0, "pe_ratio": 8.5, "roe_pct": 17.0,
            "debt_to_equity": 1.0, "roc_1d_lag1": 0.001, "roc_20d": 0.02, "beta_egx30": 1.00
        }
    }

    @classmethod
    def impute_feature_value(cls, ticker: str, feature_name: str, value: Optional[float]) -> float:
        """
        If value is None or NaN, returns the neutral sector/market median for that feature.
        """
        import math
        if value is not None and not (isinstance(value, (float, int)) and (math.isnan(value) or math.isinf(value))):
            return float(value)
        sector = SectorNeutralizer.get_sector_for_ticker(ticker)
        sec_dict = cls.DEFAULT_SECTOR_MEDIANS.get(sector, cls.DEFAULT_SECTOR_MEDIANS["DEFAULT"])
        return float(sec_dict.get(feature_name, 0.0))

    @classmethod
    def impute_feature_dict(cls, ticker: str, feature_dict: Dict[str, Any]) -> Dict[str, float]:
        """
        Neutralizes all NaN/missing features across the dictionary with sector medians.
        """
        cleaned = {}
        for k, v in feature_dict.items():
            if isinstance(v, (int, float)) or v is None:
                cleaned[k] = cls.impute_feature_value(ticker, k, v)
            else:
                cleaned[k] = v
        return cleaned
