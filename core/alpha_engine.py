#!/usr/bin/env python3
# =============================================================================
# core/alpha_engine.py — GEN-26 Alpha Score, Statistical Factors & Model Registry
# Computes multi-factor composite Alpha scores, manages Model Registry,
# and enforces Benjamini-Hochberg False Discovery Rate (BH-FDR) corrections.
# =============================================================================

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd


class ModelMetadata:
    def __init__(
        self,
        model_id: str,
        model_name: str,
        version: str,
        model_type: str,
        training_horizon: str = "20D",
        oos_profit_factor: float = 2.138,
        oos_win_rate: float = 56.0,
        status: str = "PRODUCTION_ANCHOR",
        description: str = "Non-ML Rule-Based Cost-Aware Momentum Baseline"
    ):
        self.model_id = model_id
        self.model_name = model_name
        self.version = version
        self.model_type = model_type
        self.training_horizon = training_horizon
        self.oos_profit_factor = oos_profit_factor
        self.oos_win_rate = oos_win_rate
        self.status = status
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "version": self.version,
            "model_type": self.model_type,
            "training_horizon": self.training_horizon,
            "oos_profit_factor": self.oos_profit_factor,
            "oos_win_rate": self.oos_win_rate,
            "status": self.status,
            "description": self.description
        }


class AlphaEngine:
    """
    Computes explainable composite Alpha scores and manages hypothesis testing rigor.
    """

    def __init__(self):
        self.model_registry: Dict[str, ModelMetadata] = {}
        self._init_core_models()

    def _init_core_models(self):
        self.model_registry["BL3_MOMENTUM_V1"] = ModelMetadata(
            model_id="BL3_MOMENTUM_V1",
            model_name="Tier 1 Cost-Aware Momentum Anchor",
            version="1.0.0",
            model_type="RULE_BASED_MOMENTUM",
            training_horizon="20D",
            oos_profit_factor=2.138,
            oos_win_rate=56.0,
            status="PRODUCTION_ANCHOR",
            description="Verified rule: Mom_20D > 0 and Close > SMA_50 with 0.90% cost model"
        )
        self.model_registry["P2_BREADTH_MOM_V2"] = ModelMetadata(
            model_id="P2_BREADTH_MOM_V2",
            model_name="Phase 2.5 Clean Breadth Momentum",
            version="2.5.0",
            model_type="REGIME_FILTERED_MOMENTUM",
            training_horizon="20D",
            oos_profit_factor=2.197,
            oos_win_rate=57.2,
            status="CONDITIONAL_RESEARCH",
            description="BL3_Momentum + Trailing Breadth Advance Ratio > 0.50"
        )
        self.model_registry["HIST_GBM_ENSEMBLE_T6"] = ModelMetadata(
            model_id="HIST_GBM_ENSEMBLE_T6",
            model_name="Tier 6 HistGBM Multi-Asset Classifier",
            version="4.2.0",
            model_type="MACHINE_LEARNING_ENSEMBLE",
            training_horizon="20D",
            oos_profit_factor=2.55,
            oos_win_rate=58.1,
            status="SHADOW_ADVISORY_ONLY",
            description="ML ensemble operating in shadow research mode"
        )

    @staticmethod
    def compute_composite_alpha_score(
        quality_score: float,
        valuation_score: float,
        momentum_score: float,
        sector_score: float,
        event_score: float,
        liquidity_score: float,
        macro_alignment_score: float = 75.0
    ) -> Dict[str, Any]:
        """
        Computes composite Alpha Score (0 to 100) with detailed explainability attribution.
        """
        # Multi-factor weights
        weights = {
            "momentum": 0.30,
            "quality": 0.20,
            "valuation": 0.15,
            "sector": 0.15,
            "liquidity": 0.10,
            "event": 0.05,
            "macro": 0.05
        }

        contributions = {
            "momentum": round(momentum_score * weights["momentum"], 1),
            "quality": round(quality_score * weights["quality"], 1),
            "valuation": round(valuation_score * weights["valuation"], 1),
            "sector": round(sector_score * weights["sector"], 1),
            "liquidity": round(liquidity_score * weights["liquidity"], 1),
            "event": round(event_score * weights["event"], 1),
            "macro": round(macro_alignment_score * weights["macro"], 1)
        }

        composite_alpha = sum(contributions.values())
        composite_alpha = round(max(0.0, min(100.0, composite_alpha)), 1)

        # Confidence calculation
        agreement_std = float(np.std([quality_score, valuation_score, momentum_score, sector_score, liquidity_score]))
        confidence_pct = round(max(40.0, min(95.0, 100.0 - agreement_std)), 1)

        return {
            "alpha_score": composite_alpha,
            "confidence_pct": confidence_pct,
            "contributions": contributions,
            "weights": weights
        }

    @staticmethod
    def compute_sub_scores(
        tech_features: Dict[str, float],
        fund_features: Dict[str, float],
        val_features: Dict[str, float],
        event_features: Dict[str, float],
        regime_features: Dict[str, float],
        liq_features: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Computes granular explainable sub-scores (0-100 scale) across each investment dimension.
        """
        # 1. Technical Alpha (Momentum, Trend, RSI)
        mom = tech_features.get("mom_20d", 0.0)
        rsi = tech_features.get("rsi_14", 50.0)
        trend_above_sma = 1.0 if tech_features.get("close_gt_sma50", True) else 0.0
        tech_score = max(0.0, min(100.0, 50.0 + (mom * 150.0) + (trend_above_sma * 20.0) - abs(rsi - 55.0) * 0.5))

        # 2. Fundamental Alpha (ROE, Net Margin, Cash Conversion)
        roe = fund_features.get("roe", 15.0)
        ocf_ratio = fund_features.get("ocf_net_income_ratio", 1.0)
        fund_score = max(0.0, min(100.0, (roe * 2.0) + (min(2.0, max(0.0, ocf_ratio)) * 25.0)))

        # 3. Valuation Alpha (Margin of Safety, PE/PB percentiles)
        mos = val_features.get("margin_of_safety_pct", 10.0)
        val_score = max(0.0, min(100.0, 50.0 + (mos * 1.5)))

        # 4. Event Alpha (Materiality & Sentiment)
        ev_dir = event_features.get("direction_score", 0.0) # -1 to +1
        ev_score = max(0.0, min(100.0, 50.0 + (ev_dir * 30.0)))

        # 5. Regime Alpha (Market Breadth & Risk Sentiment)
        breadth = regime_features.get("breadth_ratio", 0.5)
        regime_score = max(0.0, min(100.0, breadth * 100.0))

        # 6. Liquidity Score (ADV & Volume Z-score)
        adv_egp = liq_features.get("adv_20d_egp", 10_000_000)
        liq_score = min(100.0, max(20.0, np.log10(max(1.0, adv_egp)) * 12.5))

        # 7. Risk Score (Lower is safer, inverted for risk-adjusted score)
        vol_score = tech_features.get("gk_volatility", 0.02) * 1000.0
        risk_score = max(10.0, min(100.0, 30.0 + vol_score))

        return {
            "TECHNICAL_ALPHA": round(tech_score, 1),
            "FUNDAMENTAL_ALPHA": round(fund_score, 1),
            "VALUATION_ALPHA": round(val_score, 1),
            "EVENT_ALPHA": round(ev_score, 1),
            "REGIME_ALPHA": round(regime_score, 1),
            "LIQUIDITY_SCORE": round(liq_score, 1),
            "RISK_SCORE": round(risk_score, 1)
        }

    @staticmethod
    def calculate_alpha_decay_ic(
        signal_series: pd.Series,
        forward_returns_dict: Dict[str, pd.Series]
    ) -> Dict[str, float]:
        """
        Computes Information Coefficient (Spearman Rank Correlation) across forward horizons:
        1D, 3D, 5D, 10D, 20D, 30D to measure signal half-life and alpha decay.
        """
        ic_results = {}
        for horizon, fwd_ret in forward_returns_dict.items():
            valid = pd.concat([signal_series, fwd_ret], axis=1).dropna()
            if len(valid) > 10:
                ic = valid.iloc[:, 0].corr(valid.iloc[:, 1], method="spearman")
                ic_results[horizon] = round(float(ic), 4)
            else:
                ic_results[horizon] = 0.0
        return ic_results

    @staticmethod
    def compute_cross_sectional_ranks(df_scores: pd.DataFrame, score_col: str = "total_score") -> pd.DataFrame:
        """
        Computes cross-sectional percentile ranks and z-scores for eligible universe stocks.
        """
        df_out = df_scores.copy()
        if score_col in df_out.columns and len(df_out) > 0:
            df_out["rank_percentile"] = df_out[score_col].rank(pct=True) * 100.0
            mean_val = df_out[score_col].mean()
            std_val = df_out[score_col].std()
            df_out["rank_zscore"] = (df_out[score_col] - mean_val) / (std_val if std_val > 1e-6 else 1.0)
            df_out["rank_position"] = df_out[score_col].rank(ascending=False).astype(int)
        return df_out

    @staticmethod
    def apply_bh_fdr_correction(p_values: List[float], alpha: float = 0.05) -> List[bool]:
        """
        Applies Benjamini-Hochberg False Discovery Rate (FDR) control for multiple hypothesis tests.
        Returns boolean list indicating which discoveries remain statistically significant.
        """
        n = len(p_values)
        if n == 0:
            return []

        sorted_indices = np.argsort(p_values)
        sorted_p = np.array(p_values)[sorted_indices]
        significant = np.zeros(n, dtype=bool)

        thresholds = (np.arange(1, n + 1) / n) * alpha
        valid_below_threshold = np.where(sorted_p <= thresholds)[0]

        if len(valid_below_threshold) > 0:
            max_k = valid_below_threshold.max()
            significant[sorted_indices[:max_k + 1]] = True

        return list(significant)
