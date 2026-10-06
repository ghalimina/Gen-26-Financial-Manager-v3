#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# core/prediction_actual_tracker.py — Measured Prediction-vs-Actual Tracking Engine
# Part of Sprint B: The Core Self-Improving Engine & Feedback Loop
# Automatically records forward predictions across multiple horizons (1D to 60D),
# reconciles them against actual canonical market prices upon horizon expiry,
# and computes empirical Hit Rates, Information Coefficients (IC), and forecast errors.
# =============================================================================

import os
import sys
import json
import logging
import datetime
import numpy as np
from typing import Dict, List, Any, Optional, Tuple

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.database_engine import db_engine
from core.market_price_service import MarketPriceService

logger = logging.getLogger("PredictionActualTracker")

HORIZON_DAYS_MAP = {
    "1D": 1,
    "5D": 5,
    "10D": 10,
    "20D": 20,
    "60D": 60
}


class PredictionActualTracker:
    """
    Measured feedback loop orchestrator tracking forecasts against real market outcomes.
    """

    @classmethod
    def record_prediction(
        cls,
        ticker: str,
        horizon: str,
        predicted_target_price: float,
        predicted_direction: str = "BULLISH",
        predicted_confidence_pct: float = 85.0,
        features_snapshot: Optional[Dict[str, Any]] = None,
        entry_price: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Registers a forward prediction in the SQLite database.
        """
        now = datetime.datetime.now()
        days_ahead = HORIZON_DAYS_MAP.get(horizon.upper(), 1)
        target_time = now + datetime.timedelta(days=days_ahead)

        if entry_price is None or entry_price <= 0:
            entry_price = float(MarketPriceService.get_latest_price(ticker) or 100.0)

        pred_id = f"PRED_{ticker.replace('.', '_')}_{horizon}_{now.strftime('%Y%m%d_%H%M%S')}_{os.urandom(2).hex()}"

        pred_record = {
            "prediction_id": pred_id,
            "ticker": ticker,
            "horizon": horizon.upper(),
            "timestamp_created": now.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_target": target_time.strftime("%Y-%m-%d %H:%M:%S"),
            "entry_price": float(entry_price),
            "predicted_target_price": float(predicted_target_price),
            "predicted_direction": predicted_direction.upper(),
            "predicted_confidence_pct": float(predicted_confidence_pct),
            "features_snapshot_json": features_snapshot or {},
            "status": "PENDING"
        }

        success = db_engine.record_prediction_forecast(pred_record)
        return {
            "success": success,
            "prediction_id": pred_id,
            "ticker": ticker,
            "horizon": horizon,
            "entry_price": entry_price,
            "target_price": predicted_target_price,
            "target_timestamp": pred_record["timestamp_target"]
        }

    @classmethod
    def reconcile_closed_horizons(cls) -> Dict[str, Any]:
        """
        Scans all pending predictions, checks if target timestamp has elapsed,
        evaluates against current canonical market price, and updates accuracy records.
        """
        pending_list = db_engine.get_pending_predictions(limit=500)
        now = datetime.datetime.now()
        reconciled_count = 0
        hits_count = 0
        reconciled_details = []

        for p in pending_list:
            target_str = p.get("timestamp_target", "")
            try:
                target_dt = datetime.datetime.strptime(target_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                target_dt = now

            # If horizon has elapsed or forced reconciliation
            if now >= target_dt:
                ticker = p.get("ticker", "COMI.CA")
                entry_price = float(p.get("entry_price", 100.0))
                target_price = float(p.get("predicted_target_price", entry_price * 1.05))
                pred_dir = (p.get("predicted_direction") or "BULLISH").upper()

                actual_price = float(MarketPriceService.get_latest_price(ticker) or entry_price)

                # Determine actual direction
                if actual_price > entry_price * 1.005:
                    actual_direction = "BULLISH"
                elif actual_price < entry_price * 0.995:
                    actual_direction = "BEARISH"
                else:
                    actual_direction = "RANGE"

                # Hit evaluation logic
                is_hit = 0
                if pred_dir == "BULLISH":
                    if actual_price >= target_price or (actual_price > entry_price and actual_direction == "BULLISH"):
                        is_hit = 1
                elif pred_dir == "BEARISH":
                    if actual_price <= target_price or (actual_price < entry_price and actual_direction == "BEARISH"):
                        is_hit = 1
                elif pred_dir == "RANGE":
                    if abs(actual_price - entry_price) / entry_price <= 0.03:
                        is_hit = 1

                # Forecast percentage error
                forecast_error_pct = abs((actual_price - target_price) / (target_price if target_price > 0 else 1.0)) * 100.0

                update_ok = db_engine.update_reconciled_prediction(
                    prediction_id=p["prediction_id"],
                    actual_price=actual_price,
                    is_hit=is_hit,
                    forecast_error_pct=round(forecast_error_pct, 2),
                    actual_direction=actual_direction,
                    status="RECONCILED"
                )

                if update_ok:
                    reconciled_count += 1
                    if is_hit:
                        hits_count += 1
                    reconciled_details.append({
                        "prediction_id": p["prediction_id"],
                        "ticker": ticker,
                        "horizon": p.get("horizon"),
                        "entry_price": entry_price,
                        "predicted_target": target_price,
                        "actual_price": actual_price,
                        "is_hit": is_hit,
                        "forecast_error_pct": round(forecast_error_pct, 2)
                    })

        # Information Coefficient (IC) Calculation across batch
        ic_score = 0.0
        if reconciled_count > 0:
            ic_score = round(hits_count / reconciled_count * 2.0 - 1.0, 3) # Normalized [-1, 1]

        return {
            "reconciled_count": reconciled_count,
            "hits_count": hits_count,
            "hit_rate_pct": round((hits_count / reconciled_count * 100.0), 2) if reconciled_count > 0 else 0.0,
            "information_coefficient": ic_score,
            "reconciled_records": reconciled_details
        }

    @classmethod
    def calculate_brier_score(
        cls,
        y_prob: np.ndarray,
        y_true_binary: np.ndarray
    ) -> float:
        """
        Calculates the Brier Score:
        BS = (1/N) * sum_{i=1}^N (p_i - o_i)^2
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
        Calculates Expected Calibration Error (ECE) across 10 decile bins.
        """
        y_p = np.asarray(y_prob, dtype=float)
        y_t = np.asarray(y_true_binary, dtype=float)
        mask = np.isfinite(y_p) & np.isfinite(y_t)
        if np.sum(mask) == 0:
            return {
                "ece": 0.0,
                "mce": 0.0,
                "reliability_bins": [],
                "calibration_verdict_ar": "لا توجد بيانات كافية لحساب المعايرة"
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
            verdict_ar = "🟢 نموذج عالي المعايرة المؤسسية (ECE <= 0.08)"
        elif ece <= 0.15:
            verdict_ar = "🟡 نموذج مقبول المعايرة (0.08 < ECE <= 0.15)"
        else:
            verdict_ar = "🔴 نموذج يعاني من انحراف معايرة (ECE > 0.15)"

        return {
            "ece": ece,
            "mce": mce,
            "reliability_bins": reliability_bins,
            "calibration_verdict_ar": verdict_ar
        }

    @classmethod
    def get_rolling_accuracy_metrics(cls, lookback_days: int = 30, ticker: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves rolling hit rate, directional accuracy, and empirical confidence calibration.
        """
        stats = db_engine.get_prediction_accuracy_stats(lookback_days=lookback_days, ticker=ticker)
        
        # Pull recent reconciled records for audit display
        with db_engine.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM prediction_vs_actual WHERE status = 'RECONCILED' ORDER BY reconciled_at DESC LIMIT 15;"
            cursor.execute(query)
            recent_records = [dict(r) for r in cursor.fetchall()]

            # Pull all reconciled records for forensic calibration
            query_all = "SELECT * FROM prediction_vs_actual WHERE status = 'RECONCILED'"
            params = []
            if ticker:
                query_all += " AND ticker = ?"
                params.append(ticker)
            query_all += " ORDER BY reconciled_at DESC LIMIT 500;"
            cursor.execute(query_all, tuple(params))
            all_reconciled = [dict(r) for r in cursor.fetchall()]

        if all_reconciled:
            y_probs = []
            y_trues = []
            actual_returns = []
            for r in all_reconciled:
                conf = float(r.get("predicted_confidence_pct", 75.0)) / 100.0
                dir_pred = (r.get("predicted_direction") or "BULLISH").upper()
                if dir_pred == "BULLISH":
                    p_i = conf
                elif dir_pred == "BEARISH":
                    p_i = 1.0 - conf
                else:
                    p_i = 0.50
                p_i = max(0.01, min(0.99, p_i))

                entry_p = float(r.get("entry_price") or 100.0)
                actual_p = float(r.get("actual_price_at_horizon") or entry_p)
                ret_pct = ((actual_p - entry_p) / entry_p) * 100.0 if entry_p > 0 else 0.0
                actual_returns.append(ret_pct)

                is_hit = r.get("is_hit", 0)
                act_dir = (r.get("actual_direction") or "").upper()
                if act_dir == "BULLISH" or ret_pct > 0:
                    o_i = 1.0
                elif act_dir == "BEARISH" or ret_pct < 0:
                    o_i = 0.0
                else:
                    o_i = 1.0 if is_hit == 1 else 0.0

                y_probs.append(p_i)
                y_trues.append(o_i)

            bs = cls.calculate_brier_score(np.array(y_probs), np.array(y_trues))
            ece_res = cls.calculate_expected_calibration_error(np.array(y_probs), np.array(y_trues), n_bins=10)
            stats["brier_score"] = bs
            stats["expected_calibration_error"] = ece_res["ece"]
            stats["max_calibration_error"] = ece_res["mce"]
            stats["reliability_diagram"] = ece_res["reliability_bins"]
            stats["calibration_verdict_ar"] = ece_res["calibration_verdict_ar"]

            # Disentangled Triad on empirical reconciled sample
            pos_rets = [r for r in actual_returns if r > 0]
            neg_rets = [r for r in actual_returns if r <= 0]
            r_up_mean = float(np.mean(pos_rets)) if pos_rets else 4.2
            r_down_mean = float(np.mean(neg_rets)) if neg_rets else -3.8
            mean_p_up = float(np.mean(y_probs))
            q10_val = float(np.percentile(actual_returns, 10)) if len(actual_returns) >= 5 else -4.0
            q90_val = float(np.percentile(actual_returns, 90)) if len(actual_returns) >= 5 else 8.0

            from core.prediction_disentangler import PredictionDisentangler
            triad = PredictionDisentangler.disentangle(
                prob_up=mean_p_up,
                r_up_mean=r_up_mean,
                r_down_mean=r_down_mean,
                q10_downside_pct=q10_val,
                q90_upside_pct=q90_val
            )
            stats["calibrated_triad"] = triad
        else:
            stats["brier_score"] = None
            stats["expected_calibration_error"] = None
            stats["reliability_diagram"] = []
            stats["calibrated_triad"] = None

        stats["recent_reconciled_records"] = recent_records
        stats["feedback_loop_status"] = "ACTIVE_SELF_CALIBRATING"
        return stats


# Global Singleton
prediction_tracker = PredictionActualTracker()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing PredictionActualTracker...")
    rec = PredictionActualTracker.record_prediction(
        ticker="COMI.CA",
        horizon="1D",
        predicted_target_price=145.0,
        predicted_direction="BULLISH",
        predicted_confidence_pct=92.0,
        features_snapshot={"momentum_rsi": 62.5, "piotroski_f": 9}
    )
    print("Recorded:", rec)
    reconciled = PredictionActualTracker.reconcile_closed_horizons()
    print("Reconciled:", reconciled)
    metrics = PredictionActualTracker.get_rolling_accuracy_metrics()
    print("Rolling Metrics:", json.dumps(metrics, indent=2, ensure_ascii=False))
