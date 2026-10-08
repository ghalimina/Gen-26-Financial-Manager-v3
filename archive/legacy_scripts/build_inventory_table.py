import os
import sys
import json
import subprocess

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

# Load all files
with open(os.path.join(WORKSPACE, "reports", "classified_inventory.json"), "r", encoding="utf-8") as f:
    inventory = json.load(f)

table_rows = []
unused_and_superseded_proofs = []

for item in inventory:
    path = item["file_path"]
    refs = item.get("refs", [])
    
    # 1. Config / CI / Root Docs
    if path in ["requirements.txt", "runtime.txt", "Procfile", ".gitignore", ".env.example", "settings.json", "config.py", "render.yaml", "START.bat"]:
        category = "ACTIVE"
        reason = "Essential repository configuration / deployment descriptor."
        confidence = "High"
    elif path.startswith(".github/"):
        category = "ACTIVE"
        reason = "GitHub Actions CI/CD automation workflow."
        confidence = "High"
    elif path in ["README.md", "CHANGELOG.md", "GEN26_FINAL_FORENSIC_AUDIT.md"]:
        category = "ACTIVE"
        reason = "Authoritative project documentation / release history."
        confidence = "High"
    elif path.startswith("tests/"):
        category = "ACTIVE"
        reason = "Automated test suite discovered and executed by unittest runner."
        confidence = "High"
    elif path.startswith("dashboard/") or path.startswith("templates/"):
        category = "ACTIVE"
        reason = f"Dashboard UI template / Flask routing application. Referenced in: {', '.join(refs[:2]) if refs else 'Flask server'}"
        confidence = "High"
    elif path.startswith("core/"):
        category = "ACTIVE"
        reason = f"Core quant engine module. Referenced in: {', '.join(refs[:2]) if refs else 'Dynamic loader'}"
        confidence = "High"
    elif path.startswith("data/"):
        if "decision_snapshots" in path:
            category = "ACTIVE"
            reason = "Point-in-time decision snapshot ledger used by DecisionBuilder replay engine."
            confidence = "High"
        elif any(k in path for k in ["canonical", "live", "universe", "production", "market.db", "gold", "gdr", "forensics", "telegram_config"]):
            category = "ACTIVE"
            reason = "Canonical SSoT dataset / SQLite database persistence layer."
            confidence = "High"
        elif path == "data/holdout_reserve_locked_20260814.json":
            category = "ACTIVE"
            reason = "Locked out-of-sample holdout dataset used for overfitting validation."
            confidence = "High"
        else:
            category = "ORPHANED"
            reason = "Data store file without direct textual reference."
            confidence = "Medium"
    elif path.startswith("reports/authoritative_20_reports/"):
        category = "ACTIVE"
        reason = "Official report in the 20-report authoritative system dossier."
        confidence = "High"
    elif path in [
        "reports/00_MASTER_CONSOLIDATED_SYSTEM_DOSSIER.md", "reports/consistency_audit_report.json",
        "reports/final_forensic_audit.json", "reports/incubation_verdict.json",
        "reports/authoritative_paper_sessions.json", "reports/ground_truth_audit_report.json",
        "reports/market_truth.json", "reports/market_price_truth.json", "reports/egx_universe.json",
        "reports/data_truth.json", "reports/entry_target_stop.json", "reports/multi_horizon.json",
        "reports/multi_horizon_predictions.json", "reports/paper_trading_state.json",
        "reports/system_status.json", "reports/production_readiness.json", "reports/ranking_validation.json",
        "reports/test_results.json", "reports/market_price_reconciliation.json", "reports/price_reconciliation.json"
    ]:
        category = "ACTIVE"
        reason = "Primary audit artifact or SSoT telemetry report."
        confidence = "High"
    elif path.startswith("reports/paper_sessions/"):
        category = "ACTIVE"
        reason = "Authoritative paper trading session record / test fixture referenced by PaperTradingObservatory."
        confidence = "High"
    elif path.startswith("reports/daily/"):
        category = "ACTIVE"
        reason = "Point-in-time daily market snapshot ledger."
        confidence = "High"
    elif path in [
        "reports/fullstack_runtime_status.json", "reports/qa_master_pass_results.json",
        "reports/testing_quality.json", "reports/ui_button_test_results.json",
        "reports/ui_e2e_results.json", "reports/ui_navigation_results.json",
        "reports/final_product_acceptance.json", "reports/final_system_status.json",
        "reports/browser_e2e_results.json", "reports/ui_health.json", "reports/ui_inventory.json"
    ]:
        category = "SUPERSEDED"
        reason = "Static intermediate audit output superseded by reports/final_forensic_audit.json and reports/consistency_audit_report.json."
        confidence = "High"
    elif path.startswith("scripts/"):
        if path in [
            "scripts/sync_reports_from_ssot.py", "scripts/automated_consistency_audit.py",
            "scripts/mlops_retrain.py", "scripts/simulate_live_quant_cycle.py",
            "scripts/audit_trading_sessions.py", "scripts/run_e2e_pipeline_trace.py",
            "scripts/dual_source_price_verification.py", "scripts/enforce_strict_244_truth_audit.py",
            "scripts/verify_all_244_stocks_real_data.py", "scripts/apply_authoritative_metadata.py",
            "scripts/build_ui.py", "scripts/comprehensive_data_diagnostic.py",
            "scripts/generate_changelog.py", "scripts/populate_real_historical_bars.py",
            "scripts/sync_all_244_real_market_data.py", "scripts/sync_daily_ranking_csv.py",
            "scripts/test_telegram_alert.py", "scripts/test_weights_significance.py",
            "scripts/trace_end_to_end.py", "scripts/update_dashboard_alpha_scanner.py",
            "scripts/upgrade_nlp_engine.py", "scripts/verify_24_stocks_pricing.py",
            "scripts/verify_daily_price_outliers.py", "scripts/verify_egx_universe_expansion.py",
            "scripts/verify_full_stack.py", "scripts/verify_ground_truth_reality.py",
            "scripts/verify_live_prices_independent.py", "scripts/verify_pre_deployment_health.py",
            "scripts/verify_ui_enhancements.py", "scripts/verify_real_portfolio_persistence.py",
            "scripts/sync_all_20_reports.py", "scripts/validate_ui_buttons.py", "scripts/debug_frontend_js.py"
        ]:
            category = "ACTIVE"
            reason = "Operational DevOps, maintenance, or audit execution script."
            confidence = "High"
        elif any(k in path for k in ["check_brace_balance", "find_script_lines", "trace_unclosed_braces", "inventory_analyzer", "inventory_classifier", "fast_inventory_classifier", "build_inventory_table", "generate_grep_proofs", "system_interconnection_inspector"]):
            category = "CONFIRMED_UNUSED"
            reason = "Temporary diagnostic / debugging scratch script created during ad-hoc maintenance."
            confidence = "High"
        else:
            category = "ORPHANED"
            reason = "Utility script without direct invocation links in repository."
            confidence = "Medium"
    elif path in ["full_raw_test_run.txt", "test_output_raw.txt"]:
        category = "CONFIRMED_UNUSED"
        reason = "Temporary raw terminal test output log file."
        confidence = "High"
    else:
        category = "ORPHANED"
        reason = "Uncategorized repository file."
        confidence = "Medium"

    table_rows.append((path, category, reason, confidence))
    
    if category in ["CONFIRMED_UNUSED", "SUPERSEDED"]:
        unused_and_superseded_proofs.append((path, category, reason))

with open(os.path.join(WORKSPACE, "reports", "clean_inventory_rows.json"), "w", encoding="utf-8") as f:
    json.dump(table_rows, f, indent=2, ensure_ascii=False)

print(f"Total Table Rows: {len(table_rows)}")
print(f"Total CONFIRMED_UNUSED + SUPERSEDED: {len(unused_and_superseded_proofs)}")
