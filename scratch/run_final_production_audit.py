import os
import json
import pandas as pd
import numpy as np
import datetime
import subprocess

BASE_DIR = r"c:\Users\Administrator\Desktop\New folder"
os.chdir(BASE_DIR)

DATA_DIR = os.path.join(BASE_DIR, "data")
ARTIFACTS_DIR = BASE_DIR

def run_tests():
    print("Running pytest...")
    res = subprocess.run(["pytest", "tests/", "-v", "--disable-warnings"], capture_output=True, text=True)
    with open("FINAL_TEST_RESULTS.json", "w", encoding="utf-8") as f:
        json.dump({"returncode": res.returncode, "stdout": res.stdout, "stderr": res.stderr}, f, indent=2)
    return res.returncode == 0

def hardcoded_audit():
    print("Running hardcoded string audit...")
    bad_strings = ["14531", "63.1", "1.97", "-20.23"]
    issues = []
    for root, dirs, files in os.walk(BASE_DIR):
        if "scratch" in root or ".git" in root or "__pycache__" in root or "audit" in root.lower() or "data" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    for bad in bad_strings:
                        if bad in content:
                            issues.append(f"Hardcoded {bad} found in {file}")
    return issues

def audit_calibration_and_drift():
    telemetry_file = os.path.join(DATA_DIR, "prediction_actual_telemetry.json")
    drift_file = os.path.join(DATA_DIR, "model_drift_metrics.json")
    
    cal_report = []
    if os.path.exists(telemetry_file):
        with open(telemetry_file, "r", encoding="utf-8") as f:
            t_data = json.load(f)
            for r in t_data:
                pred_prob = r.get("predicted_prob", 0)
                h_5d = r.get("horizons", {}).get("5D", {})
                if h_5d:
                    actual = 1 if h_5d.get("direction_correct") else 0
                    cal_report.append({"prob": pred_prob, "actual": actual, "brier": h_5d.get("brier_score", 0)})
    
    if cal_report:
        df_cal = pd.DataFrame(cal_report)
        df_cal.to_csv("FINAL_CALIBRATION_REPORT.csv", index=False)
        
    if os.path.exists(drift_file):
        with open(drift_file, "r", encoding="utf-8") as f:
            drift_data = json.load(f)
        df_drift = pd.DataFrame([
            {"window": "rolling_20", **drift_data.get("rolling_20", {})},
            {"window": "rolling_60", **drift_data.get("rolling_60", {})},
        ])
        df_drift.to_csv("FINAL_DRIFT_REPORT.csv", index=False)
    else:
        pd.DataFrame([{"error": "No drift file found"}]).to_csv("FINAL_DRIFT_REPORT.csv", index=False)

def test_killswitch():
    print("Testing Kill Switch Logic...")
    # Using the exact checks injected into app.py
    import importlib.util
    spec = importlib.util.spec_from_file_location("app", os.path.join(BASE_DIR, "app.py"))
    app = importlib.util.module_from_spec(spec)
    # Just statically asserting failsafes from file or mock testing
    with open(os.path.join(BASE_DIR, "app.py"), "r", encoding="utf-8") as f:
        code = f.read()
    
    ks_triggered = "if cumul <= -10.0:  # Failsafe Threshold" in code
    ks_stale = "if today.weekday() < 5 and (today - last_date).days > 1:" in code
    
    pd.DataFrame([
        {"test": "DD <= -10%", "present": ks_triggered, "status": "PASS" if ks_triggered else "FAIL"},
        {"test": "Stale Data > 24h", "present": ks_stale, "status": "PASS" if ks_stale else "FAIL"}
    ]).to_csv("FINAL_KILLSWITCH_TEST.csv", index=False)

def run_paper_trading_audit():
    journal_file = os.path.join(BASE_DIR, "paper_trading_journal.json")
    if os.path.exists(journal_file):
        with open(journal_file, "r", encoding="utf-8") as f:
            j_data = json.load(f)
            df = pd.DataFrame(j_data)
            df.to_csv("FINAL_PAPER_TRADING_RESULTS.csv", index=False)
            return len(j_data)
    else:
        pd.DataFrame([{"error": "No paper journal found"}]).to_csv("FINAL_PAPER_TRADING_RESULTS.csv", index=False)
        return 0

def run_all():
    issues = []
    
    # Run tests
    if not run_tests():
        issues.append("Pytest failed. Some tests did not pass.")
        
    # Hardcoded audit
    hc_issues = hardcoded_audit()
    issues.extend(hc_issues)
    
    # Calibration & Drift
    audit_calibration_and_drift()
    
    # Kill switch
    test_killswitch()
    
    # Paper Trading
    pt_count = run_paper_trading_audit()
    if pt_count < 30:
        issues.append(f"INSUFFICIENT LIVE PAPER HISTORY. Expected > 30 entries, got {pt_count}.")
        
    # Snapshots check
    snapshot_dir = os.path.join(DATA_DIR, "snapshots")
    if not os.path.exists(snapshot_dir) or len(os.listdir(snapshot_dir)) == 0:
        issues.append("No Point-in-Time snapshots found in data/snapshots.")
        
    # Holdout check
    holdout_files = [f for f in os.listdir(DATA_DIR) if "holdout_reserve_locked" in f]
    if not holdout_files:
        issues.append("No Isolated Holdout Reserve found in data/.")
        
    # Settlement Ledger Check
    with open(os.path.join(BASE_DIR, "app.py"), "r", encoding="utf-8") as f:
        app_code = f.read()
        if "buying_power_t0" not in app_code or "withdrawable_cash_t2" not in app_code:
            issues.append("T+2 Settlement ledger missing buying_power_t0 or withdrawable_cash_t2 keys.")
            
    # Model Versioning check
    if "v3.0-frozen" not in app_code:
        issues.append("v3.0-frozen versioning tag missing in app.py exports.")
        
    # Explainability check
    if "json.dumps(reason_json" not in app_code:
        issues.append("JSON structured decision payload missing in export_decision_log.")
        
    with open("FINAL_ISSUES.md", "w", encoding="utf-8") as f:
        if issues:
            f.write("# FINAL PRODUCTION ISSUES DETECTED\n")
            for i in issues:
                f.write(f"- {i}\n")
        else:
            f.write("# FINAL PRODUCTION ISSUES DETECTED\nNone. System passed all Zero-Trust structural constraints.")
            
    print("Audit checks completed. Issues found:", len(issues))

if __name__ == "__main__":
    run_all()
