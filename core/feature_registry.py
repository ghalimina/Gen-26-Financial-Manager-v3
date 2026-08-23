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

    def register(self, metadata: FeatureMetadata):
        self._registry[metadata.feature_id] = metadata

    def get(self, feature_id: str) -> Optional[FeatureMetadata]:
        return self._registry.get(feature_id)

    def list_all(self) -> List[Dict[str, Any]]:
        return [meta.to_dict() for meta in self._registry.values()]

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(self.list_all())
