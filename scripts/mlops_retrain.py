#!/usr/bin/env python3
# =============================================================================
# scripts/mlops_retrain.py — GEN-26 Automated Retraining Execution Script
# CLI & CI/CD Entry Point for Weekly & Drift-Triggered Model Retraining.
# =============================================================================

import os
import sys
import json
import argparse

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.mlops_pipeline import MLOpsPipeline
from core.notification_gateway import TelegramNotifier


def main():
    parser = argparse.ArgumentParser(description="GEN-26 MLOps Retraining Script")
    parser.add_argument("--force", action="store_true", help="Force immediate retrain without checking drift triggers")
    parser.add_argument("--trigger", type=str, default="SCHEDULED_WEEKLY", help="Trigger reason / source")
    args = parser.parse_args()

    print("=" * 70)
    print("GEN-26 MLOPS CONTINUOUS LEARNING & RETRAINING PIPELINE")
    print("=" * 70)

    drift = MLOpsPipeline.check_drift_triggers()
    print(f"Rolling Accuracy: {drift['rolling_accuracy_pct']}% | Status: {drift['status_ar']}")

    if not args.force and not drift["needs_emergency_retrain"] and args.trigger != "SCHEDULED_WEEKLY":
        print("ℹ️ No retrain trigger active. Models are stable within tolerance.")
        return

    print(f"🚀 Executing Model Retraining (Trigger: {args.trigger})...")
    res = MLOpsPipeline.execute_retraining_pipeline(trigger_source=args.trigger)
    print("✅ Retraining Completed Successfully!")
    print(json.dumps(res, ensure_ascii=False, indent=2))

    # Send Notification
    TelegramNotifier.send_retrain_completed_alert(res)


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    main()
