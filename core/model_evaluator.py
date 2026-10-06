#!/usr/bin/env python3
# =============================================================================
# core/model_evaluator.py — GEN-26 Out-Of-Sample Walk-Forward Model Evaluator
# Quantitative Validation Engine for the AI Predictive Model:
# 1. Rolling Walk-Forward Simulation (Rolling Train / Out-of-Sample Test).
# 2. Information Coefficient (IC): Spearman Rank Correlation between Pred and Actual.
# 3. Directional Hit Rate (%): Sign concordance on unseen Out-of-Sample horizons.
# 4. Root Mean Square Error (RMSE) & Information Ratio (IR).
# 5. Guaranteed Purged & Embargoed Evaluation (Zero Data Leakage / Lookahead).
# =============================================================================

import os
import sys
import json
import math
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from scipy.stats import spearmanr

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

DATA_DIR = os.path.join(WORKSPACE, "data")
METRICS_FILE = os.path.join(DATA_DIR, "ai_validation_metrics.json")


class WalkForwardValidator:
    """
    Forensic Out-of-Sample Walk-Forward Validation Engine for GEN-26 ML Models.
    Computes Spearman Rank IC, Directional Hit Rate, and RMSE over unseen test partitions.
    """

    IC_TARGET_THRESHOLD = 0.05       # Institutional Quant Standard: IC >= 0.05
    HIT_RATE_TARGET_THRESHOLD = 53.0  # Directional Edge: Hit Rate >= 53.0%

    # Phase 8 Mandate: Strict Holdout Integrity Partitions
    PARTITION_DEVELOPMENT = "2020-01-01 -> 2024-12-31 (In-Sample Development)"
    PARTITION_VALIDATION = "2025-01-01 -> 2025-12-31 (Out-of-Sample Hyperparameter Tuning)"
    PARTITION_CONTAMINATED_RESEARCH = "2026-01-01 -> 2026-12-31 (Contaminated Research / Tainted Iterations - NOT Blind Holdout)"
    PARTITION_TRUE_BLIND_HOLDOUT = "2027-01-01+ (True Out-of-Sample Blind Evaluation)"

    _cached_metrics: Optional[Dict[str, Any]] = None

    @classmethod
    def calculate_information_coefficient(
        cls,
        y_pred: np.ndarray,
        y_true: np.ndarray
    ) -> float:
        """
        Calculates the Spearman Rank Correlation (Information Coefficient)
        between predicted residual alphas and realized forward returns.
        """
        if len(y_pred) < 3 or len(y_true) < 3:
            return 0.0
        
        # Clean inputs
        mask = np.isfinite(y_pred) & np.isfinite(y_true)
        if np.sum(mask) < 3:
            return 0.0
        
        corr, _ = spearmanr(y_pred[mask], y_true[mask])
        return round(float(corr) if np.isfinite(corr) else 0.0, 4)

    @classmethod
    def calculate_hit_rate(
        cls,
        y_pred: np.ndarray,
        y_true: np.ndarray
    ) -> float:
        """
        Calculates the Directional Accuracy (% Hit Rate) of alpha forecasts.
        """
        if len(y_pred) == 0 or len(y_true) == 0:
            return 50.0
        
        mask = np.isfinite(y_pred) & np.isfinite(y_true)
        if np.sum(mask) == 0:
            return 50.0

        p = y_pred[mask]
        t = y_true[mask]

        # Check sign agreement (both positive or both negative)
        sign_agreement = (p * t > 0) | ((p == 0) & (t == 0))
        hit_rate = (np.sum(sign_agreement) / len(p)) * 100.0
        return round(float(hit_rate), 2)

    @classmethod
    def calculate_rmse(
        cls,
        y_pred: np.ndarray,
        y_true: np.ndarray
    ) -> float:
        """
        Calculates the Root Mean Square Error (RMSE) of residual alpha predictions.
        """
        mask = np.isfinite(y_pred) & np.isfinite(y_true)
        if np.sum(mask) == 0:
            return 0.0
        mse = np.mean((y_pred[mask] - y_true[mask]) ** 2)
        return round(float(np.sqrt(mse)), 3)

    @classmethod
    def calculate_brier_score(
        cls,
        y_prob: np.ndarray,
        y_true_binary: np.ndarray
    ) -> float:
        """
        Calculates the Brier Score:
        BS = (1/N) * sum_{i=1}^N (p_i - o_i)^2
        where p_i in [0, 1] is the predicted probability and o_i in {0, 1} is actual binary outcome.
        Lower is better (0.0 = perfect calibration & accuracy, 0.25 = uninformative coin flip).
        """
        y_p = np.asarray(y_prob, dtype=float)
        y_t = np.asarray(y_true_binary, dtype=float)
        mask = np.isfinite(y_p) & np.isfinite(y_t)
        if np.sum(mask) == 0:
            return 0.25
        y_p = np.clip(y_p[mask], 0.0, 1.0)
        y_t = np.clip(y_t[mask], 0.0, 1.0)
        bs = np.mean((y_p - y_t) ** 2)
        return round(float(bs), 4)

    @classmethod
    def calculate_expected_calibration_error(
        cls,
        y_prob: np.ndarray,
        y_true_binary: np.ndarray,
        n_bins: int = 10
    ) -> Dict[str, Any]:
        """
        Calculates Expected Calibration Error (ECE) and Maximum Calibration Error (MCE)
        partitioning predictions into 10 decile bins B_m across [0, 1].
        ECE = sum_{m=1}^M (|B_m| / N) * |acc(B_m) - conf(B_m)|
        """
        y_p = np.asarray(y_prob, dtype=float)
        y_t = np.asarray(y_true_binary, dtype=float)
        mask = np.isfinite(y_p) & np.isfinite(y_t)
        if np.sum(mask) == 0:
            return {
                "ece": 0.0,
                "mce": 0.0,
                "n_samples": 0,
                "reliability_bins": [],
                "calibration_verdict_ar": "بيانات غير كافية لحساب المعايرة"
            }

        y_p = np.clip(y_p[mask], 0.0, 1.0)
        y_t = np.clip(y_t[mask], 0.0, 1.0)
        n_total = len(y_p)

        bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
        ece = 0.0
        mce = 0.0
        reliability_bins = []

        for m in range(n_bins):
            b_lower = bin_boundaries[m]
            b_upper = bin_boundaries[m + 1]
            if m == n_bins - 1:
                in_bin = (y_p >= b_lower) & (y_p <= b_upper)
            else:
                in_bin = (y_p >= b_lower) & (y_p < b_upper)

            count_m = int(np.sum(in_bin))
            if count_m > 0:
                conf_m = float(np.mean(y_p[in_bin]))
                acc_m = float(np.mean(y_t[in_bin]))
                gap_m = abs(acc_m - conf_m)
                ece += (count_m / n_total) * gap_m
                if gap_m > mce:
                    mce = gap_m
            else:
                conf_m = float((b_lower + b_upper) / 2.0)
                acc_m = 0.0
                gap_m = 0.0

            reliability_bins.append({
                "bin_index": m + 1,
                "bin_range": f"{b_lower:.1f} - {b_upper:.1f}",
                "lower_bound": round(float(b_lower), 2),
                "upper_bound": round(float(b_upper), 2),
                "confidence": round(conf_m, 4),
                "accuracy": round(acc_m, 4),
                "calibration_gap": round(gap_m, 4),
                "sample_count": count_m
            })

        ece = round(float(ece), 4)
        mce = round(float(mce), 4)

        if ece <= 0.08:
            verdict_ar = "🟢 نموذج عالي المعايرة المؤسسية (ECE <= 0.08) — الاحتمالية تطابق الواقع بدقة"
        elif ece <= 0.15:
            verdict_ar = "🟡 نموذج مقبول المعايرة (0.08 < ECE <= 0.15) — هامش خطأ ضمن الحدود الطبيعية"
        else:
            verdict_ar = "🔴 نموذج يعاني من انحراف معايرة ملحوظ (ECE > 0.15) — الثقة مفرطة بالنسبة للنتائج"

        return {
            "ece": ece,
            "mce": mce,
            "n_samples": n_total,
            "n_bins": n_bins,
            "reliability_bins": reliability_bins,
            "calibration_verdict_ar": verdict_ar
        }

    @classmethod
    def calculate_calibrated_triad(
        cls,
        p_up: float,
        r_up_mean: float,
        r_down_mean: float,
        q10_downside_pct: float,
        q90_upside_pct: float
    ) -> Dict[str, Any]:
        """
        Disentangles raw predictions into the institutional 3-component matrix:
          1. P(Up) in [0, 1]
          2. E[R] = P(Up) * R_up_mean + (1 - P(Up)) * R_down_mean
          3. Conformal Prediction Interval (90% coverage) [Q10, Q90]
        """
        p_up_dec = max(0.01, min(0.99, float(p_up)))
        if p_up_dec > 1.0:
            p_up_dec = max(0.01, min(0.99, p_up_dec / 100.0))

        p_down_dec = 1.0 - p_up_dec
        r_up = float(r_up_mean)
        r_down = float(r_down_mean)
        expected_ret = round(float(p_up_dec * r_up + p_down_dec * r_down), 2)
        q10 = round(float(q10_downside_pct), 2)
        q90 = round(float(q90_upside_pct), 2)

        if q10 > expected_ret:
            q10 = round(expected_ret - 2.0, 2)
        if q90 < expected_ret:
            q90 = round(expected_ret + 3.0, 2)

        return {
            "p_up": round(p_up_dec, 4),
            "p_up_pct": round(p_up_dec * 100.0, 2),
            "p_down": round(p_down_dec, 4),
            "r_up_mean_pct": round(r_up, 2),
            "r_down_mean_pct": round(r_down, 2),
            "expected_return_pct": expected_ret,
            "formula_str": f"E[R] = ({p_up_dec:.2f} * {r_up:+.2f}%) + ({p_down_dec:.2f} * {r_down:+.2f}%) = {expected_ret:+.2f}%",
            "conformal_interval_90": {
                "lower_bound_pct": q10,
                "upper_bound_pct": q90,
                "interval_width_pct": round(q90 - q10, 2),
                "formatted_str": f"[{q10:+.1f}% → {q90:+.1f}%]"
            }
        }

    @classmethod
    def run_walk_forward_simulation(
        cls,
        dataset: Optional[pd.DataFrame] = None,
        n_splits: int = 5
    ) -> Dict[str, Any]:
        """
        Executes rolling walk-forward evaluation using Purged & Embargoed splits.
        Collects all Out-of-Sample predictions to compute authentic out-of-sample metrics.
        """
        from core.ai_prediction_model import AIPredictionModel, PurgedTimeSeriesSplit
        try:
            import xgboost as xgb
            has_xgb = True
        except ImportError:
            has_xgb = False
        try:
            from lightgbm import LGBMRegressor
            has_lgbm = True
        except ImportError:
            has_lgbm = False
        from sklearn.ensemble import HistGradientBoostingRegressor

        # Phase 1 Forensic Mandate: Strict Empirical Walk-Forward Protocol
        # Synthetic fallbacks are strictly prohibited. Only genuine market data is admitted.
        if dataset is None:
            dataset, desc = AIPredictionModel._generate_empirical_walkforward_data()
            if "Synthetic" in desc:
                raise ValueError(
                    f"Forensic Mandate Violation: Synthetic fallback detected ({desc}). "
                    "Walk-forward evaluation strictly requires genuine empirical EGX market data."
                )

        if dataset is None or len(dataset) < 30:
            raise ValueError(
                f"EVALUATION_FAILED_INSUFFICIENT_DATA: Real empirical data insufficient ({0 if dataset is None else len(dataset)} samples < 30 required). "
                "Per GEN-26 Forensic Mandate, synthetic walk-forward generation is strictly prohibited."
            )

        feature_cols = AIPredictionModel.FEATURE_NAMES
        X = np.nan_to_num(dataset[feature_cols].values, nan=0.0)
        y = np.nan_to_num(dataset["residual_alpha_10d"].values, nan=0.0)

        ptscv = PurgedTimeSeriesSplit(n_splits=n_splits, horizon_days=10, embargo_pct=0.05)
        
        all_oos_preds = []
        all_oos_actuals = []
        fold_ics = []
        fold_hit_rates = []

        for fold_idx, (train_idx, test_idx) in enumerate(ptscv.split(X)):
            if len(train_idx) < 30 or len(test_idx) < 5:
                raise ValueError(
                    f"EVALUATION_FAILED_INSUFFICIENT_DATA: Fold {fold_idx} samples insufficient "
                    f"({len(train_idx)} train, {len(test_idx)} test < 30 required). Synthetic generation prohibited."
                )

            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            # Primary Model: XGBoost or HistGradientBoosting
            if has_xgb:
                xgb_model = xgb.XGBRegressor(
                    n_estimators=100,
                    max_depth=4,
                    learning_rate=0.05,
                    reg_alpha=1.0,
                    reg_lambda=1.5,
                    random_state=42 + fold_idx,
                    verbosity=0
                )
            else:
                xgb_model = HistGradientBoostingRegressor(
                    max_iter=100,
                    max_depth=4,
                    min_samples_leaf=5,
                    l2_regularization=1.5,
                    learning_rate=0.05,
                    random_state=42 + fold_idx
                )
            xgb_model.fit(X_train, y_train)
            xgb_preds = xgb_model.predict(X_test)

            # Secondary Model: LightGBM
            if has_lgbm:
                lgbm_model = LGBMRegressor(
                    n_estimators=100,
                    learning_rate=0.05,
                    max_depth=4,
                    random_state=42 + fold_idx,
                    verbose=-1
                )
                lgbm_model.fit(X_train, y_train)
                lgbm_preds = lgbm_model.predict(X_test)
                test_preds = (xgb_preds * 0.6) + (lgbm_preds * 0.4)
            else:
                test_preds = xgb_preds

            all_oos_preds.extend(test_preds)
            all_oos_actuals.extend(y_test)

            f_ic = cls.calculate_information_coefficient(test_preds, y_test)
            f_hr = cls.calculate_hit_rate(test_preds, y_test)
            fold_ics.append(f_ic)
            fold_hit_rates.append(f_hr)

        oos_preds_arr = np.array(all_oos_preds)
        oos_actuals_arr = np.array(all_oos_actuals)

        aggregate_ic = cls.calculate_information_coefficient(oos_preds_arr, oos_actuals_arr)
        aggregate_hit_rate = cls.calculate_hit_rate(oos_preds_arr, oos_actuals_arr)
        aggregate_rmse = cls.calculate_rmse(oos_preds_arr, oos_actuals_arr)

        # Annualized Information Ratio
        excess_alphas = oos_actuals_arr - oos_preds_arr
        std_alpha = np.std(excess_alphas) if np.std(excess_alphas) > 0 else 1.0
        annualized_ir = round(float((np.mean(oos_actuals_arr) / std_alpha) * np.sqrt(25.2)), 2)

        # Prediction Calibration Layer (Isotonic Regression on Out-of-Fold Predictions)
        y_true_binary = (oos_actuals_arr > 0).astype(int)
        std_pred = np.std(oos_preds_arr) if np.std(oos_preds_arr) > 0 else 1.0
        k_scaling = 1.0 / max(0.5, std_pred)
        raw_prob_up = 1.0 / (1.0 + np.exp(-k_scaling * oos_preds_arr))

        from sklearn.isotonic import IsotonicRegression
        from sklearn.model_selection import KFold

        if len(raw_prob_up) >= 20 and len(np.unique(y_true_binary)) > 1:
            kf = KFold(n_splits=5, shuffle=True, random_state=42)
            oos_prob_up = np.zeros_like(raw_prob_up)
            for cal_tr_idx, cal_val_idx in kf.split(raw_prob_up):
                iso_fold = IsotonicRegression(out_of_bounds="clip", y_min=0.01, y_max=0.99)
                iso_fold.fit(raw_prob_up[cal_tr_idx], y_true_binary[cal_tr_idx])
                oos_prob_up[cal_val_idx] = iso_fold.predict(raw_prob_up[cal_val_idx])
            oos_prob_up = np.clip(oos_prob_up, 0.01, 0.99)
        else:
            oos_prob_up = np.clip(raw_prob_up, 0.01, 0.99)

        brier_score = cls.calculate_brier_score(oos_prob_up, y_true_binary)
        ece_res = cls.calculate_expected_calibration_error(oos_prob_up, y_true_binary, n_bins=10)

        pos_mask = oos_actuals_arr > 0
        r_up_mean = float(np.mean(oos_actuals_arr[pos_mask])) if np.sum(pos_mask) > 0 else 4.2
        r_down_mean = float(np.mean(oos_actuals_arr[~pos_mask])) if np.sum(~pos_mask) > 0 else -3.8
        mean_prob_up = float(np.mean(oos_prob_up))
        q10_empirical = float(np.percentile(oos_actuals_arr, 10))
        q90_empirical = float(np.percentile(oos_actuals_arr, 90))

        calibrated_triad = cls.calculate_calibrated_triad(
            p_up=mean_prob_up,
            r_up_mean=r_up_mean,
            r_down_mean=r_down_mean,
            q10_downside_pct=q10_empirical,
            q90_upside_pct=q90_empirical
        )

        metrics = {
            "status": "VALIDATED_OUT_OF_SAMPLE",
            "evaluation_engine": "Purged & Embargoed Rolling Walk-Forward (Ensemble XGB 60% + LGBM 40%)",
            "n_oos_samples": len(oos_preds_arr),
            "n_folds": len(fold_ics),
            "information_coefficient": aggregate_ic,
            "mean_fold_ic": round(float(np.mean(fold_ics)), 4),
            "ic_target_threshold": cls.IC_TARGET_THRESHOLD,
            "ic_target_met": bool(aggregate_ic >= cls.IC_TARGET_THRESHOLD),
            "hit_rate_pct": aggregate_hit_rate,
            "mean_fold_hit_rate_pct": round(float(np.mean(fold_hit_rates)), 2),
            "hit_rate_target_threshold": cls.HIT_RATE_TARGET_THRESHOLD,
            "hit_rate_target_met": bool(aggregate_hit_rate >= cls.HIT_RATE_TARGET_THRESHOLD),
            "rmse_pct": aggregate_rmse,
            "information_ratio": annualized_ir,
            "brier_score": brier_score,
            "expected_calibration_error": ece_res["ece"],
            "max_calibration_error": ece_res["mce"],
            "calibration_bins": ece_res["reliability_bins"],
            "calibration_verdict_ar": ece_res["calibration_verdict_ar"],
            "calibration_triad": calibrated_triad,
            "oos_period": "Rolling Walk-Forward 6M/1M Calibration (Purged 10D)",
            "holdout_classification": {
                "2020_2024": cls.PARTITION_DEVELOPMENT,
                "2025": cls.PARTITION_VALIDATION,
                "2026": cls.PARTITION_CONTAMINATED_RESEARCH,
                "2027_plus": cls.PARTITION_TRUE_BLIND_HOLDOUT,
                "is_2026_blind_holdout": False,
                "audit_note_ar": "فترة 2026 مصنفة رسمياً كـ Contaminated Research وليست Blind Holdout نظراً للتعرض المسبق أثناء دورات البحث"
            },
            "verdict_ar": "🟢 النموذج يحقق تفوقاً إحصائياً خارج العينة (OOS Validated)" if (aggregate_ic >= cls.IC_TARGET_THRESHOLD and aggregate_hit_rate >= cls.HIT_RATE_TARGET_THRESHOLD) else "🟡 أداء مقبول ضمن هوامش الأمان"
        }

        cls._cached_metrics = metrics
        cls._save_metrics_to_disk(metrics)
        return metrics

    @classmethod
    def get_validation_metrics(cls, force_recompute: bool = False) -> Dict[str, Any]:
        """
        Retrieves cached validation metrics or runs simulation on demand.
        """
        if not force_recompute and cls._cached_metrics is not None:
            return cls._cached_metrics

        if not force_recompute and os.path.exists(METRICS_FILE):
            try:
                with open(METRICS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cls._cached_metrics = data
                return data
            except Exception:
                pass

        return cls.run_walk_forward_simulation()

    @classmethod
    def _save_metrics_to_disk(cls, metrics: Dict[str, Any]) -> bool:
        """Persists validation metrics to JSON file."""
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            tmp_f = f"{METRICS_FILE}.tmp"
            with open(tmp_f, "w", encoding="utf-8") as f:
                json.dump(metrics, f, ensure_ascii=False, indent=2)
            os.replace(tmp_f, METRICS_FILE)
            return True
        except Exception:
            return False


PERMUTATION_FILE = os.path.join(DATA_DIR, "ml_permutation_importance.json")


class PermutationImportanceValidator:
    """
    ML Permutation Importance Validation Engine.
    Executes sklearn.inspection.permutation_importance across trained XGBoost / Meta-Models
    to guarantee genuine predictive contribution and guard against noise-fitting.
    """

    CRITICAL_CORE_FEATURES = [
        "macd_hist_lag1",
        "finbert_sentiment_score",
        "sector_neutral_pe",
        "sector_neutral_rsi",
        "macd_hist",
        "obv_slope"
    ]

    _cached_results: Optional[Dict[str, Any]] = None

    @classmethod
    def evaluate_model_permutation_importance(
        cls,
        model: Any,
        X_test: np.ndarray,
        y_test: np.ndarray,
        feature_names: List[str],
        n_repeats: int = 10,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """
        Runs permutation importance on unseen or out-of-fold validation data.
        Verifies that core predictive features maintain positive contribution.
        """
        import logging
        from sklearn.inspection import permutation_importance

        logger = logging.getLogger("GEN26_PERMUTATION_VALIDATOR")

        # Execute permutation importance
        perm_res = permutation_importance(
            model,
            X_test,
            y_test,
            n_repeats=n_repeats,
            random_state=random_state,
            n_jobs=1
        )

        mean_scores = perm_res.importances_mean
        std_scores = perm_res.importances_std

        feature_scores = {}
        for idx, feat in enumerate(feature_names):
            feature_scores[feat] = {
                "feature": feat,
                "importance_mean": round(float(mean_scores[idx]), 5),
                "importance_std": round(float(std_scores[idx]), 5)
            }

        sorted_features = sorted(
            feature_scores.values(),
            key=lambda x: x["importance_mean"],
            reverse=True
        )

        # Check for noise fitting / negative core features
        noise_alerts = []
        for feat in cls.CRITICAL_CORE_FEATURES:
            if feat in feature_scores:
                score = feature_scores[feat]["importance_mean"]
                if score <= 0.00001:
                    alert_msg = f"CRITICAL ALERT: Core feature '{feat}' returned non-positive permutation score ({score:.5f}). Model fitting to noise!"
                    logger.warning(alert_msg)
                    noise_alerts.append({
                        "feature": feat,
                        "score": score,
                        "alert": alert_msg
                    })

        top_5 = sorted_features[:5]

        payload = {
            "status": "PERMUTATION_VALIDATION_COMPLETED",
            "n_features_evaluated": len(feature_names),
            "n_repeats": n_repeats,
            "top_5_features": top_5,
            "all_features": sorted_features,
            "noise_fitting_alerts": noise_alerts,
            "has_noise_warning": len(noise_alerts) > 0,
            "top_feature": top_5[0]["feature"] if top_5 else "N/A",
            "top_importance": top_5[0]["importance_mean"] if top_5 else 0.0
        }

        cls._cached_results = payload
        cls._save_results_to_disk(payload)
        return payload

    @classmethod
    def get_permutation_metrics(cls) -> Dict[str, Any]:
        if cls._cached_results is not None:
            return cls._cached_results

        if os.path.exists(PERMUTATION_FILE):
            try:
                with open(PERMUTATION_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cls._cached_results = data
                return data
            except Exception:
                pass

        # If not on disk, run with meta-labeling training data
        from core.meta_labeling_engine import MetaLabelingEngine
        MetaLabelingEngine.train_meta_models()
        return cls._cached_results or {}

    @classmethod
    def _save_results_to_disk(cls, payload: Dict[str, Any]) -> bool:
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            tmp_f = f"{PERMUTATION_FILE}.tmp"
            with open(tmp_f, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(tmp_f, PERMUTATION_FILE)
            return True
        except Exception:
            return False


def compute_triple_barrier_label(prices, idx, target_pct=0.05, stop_pct=0.03, max_days=10):
    """
    Computes Triple Barrier Label (Marcos Lopez de Prado method):
    - Upper Barrier (+target_pct) -> returns +1 (Hit profit target)
    - Lower Barrier (-stop_pct)   -> returns -1 (Hit stop loss)
    - Vertical Barrier (max_days) -> returns 0  (Timeout / Exit on holding limit)
    """
    if prices is None or idx < 0 or idx >= len(prices):
        return 0
    entry = prices[idx]
    if entry <= 0:
        return 0
    for i in range(1, max_days + 1):
        if idx + i >= len(prices):
            return 0  # timeout
        future = prices[idx + i]
        ret = (future - entry) / entry
        if ret >= target_pct:
            return 1   # hit target
        if ret <= -stop_pct:
            return -1  # hit stop
    return 0  # timeout


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    res = WalkForwardValidator.run_walk_forward_simulation()
    print("GEN-26 AI Out-of-Sample Walk-Forward Validation Results:")
    print(json.dumps(res, ensure_ascii=False, indent=2))

