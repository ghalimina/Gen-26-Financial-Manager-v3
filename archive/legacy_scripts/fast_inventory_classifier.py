import os
import sys
import json
import time

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

# 1. Collect all files in workspace excluding .git, __pycache__, .pytest_cache, .vscode, .agents, scratch
all_files = []
for root, dirs, files in os.walk(WORKSPACE):
    dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", ".pytest_cache", ".vscode", ".agents", "scratch"]]
    for f in files:
        if f.endswith(".pyc"):
            continue
        rel_path = os.path.relpath(os.path.join(root, f), WORKSPACE).replace("\\", "/")
        all_files.append(rel_path)

all_files.sort()

# Read text content into memory dict
text_corpus = {}
for rel in all_files:
    full_path = os.path.join(WORKSPACE, rel)
    if rel.endswith((".db", ".db-wal", ".db-shm", ".pyc", ".png", ".jpg", ".ico", ".txt")):
        continue
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as fp:
            text_corpus[rel] = fp.read()
    except Exception:
        pass

print(f"Loaded {len(text_corpus)} searchable text files.")

def find_references(target_file: str):
    base_name = os.path.basename(target_file)
    name_no_ext = os.path.splitext(base_name)[0]
    mod_dot = target_file.replace("/", ".").replace(".py", "") if target_file.endswith(".py") else ""

    refs = []
    for doc_path, content in text_corpus.items():
        if doc_path == target_file:
            continue
        # Direct path, filename, or module name occurrence
        if (target_file in content) or (base_name in content) or (mod_dot and mod_dot in content):
            refs.append(doc_path)
    return refs

classified_inventory = []

for f in all_files:
    refs = find_references(f)
    base = os.path.basename(f)
    
    # Classification rules
    is_protected_data = f.startswith("data/") and any(k in f for k in ["canonical", "live", "universe", "production", "market.db", "gold", "gdr", "forensics"])
    is_test = f.startswith("tests/")
    is_config = f in ["requirements.txt", "runtime.txt", "Procfile", ".gitignore", ".env.example", "settings.json", "config.py", "render.yaml"]
    is_ci = f.startswith(".github/")
    is_core = f.startswith("core/")
    is_dashboard = f.startswith("dashboard/") or f.startswith("templates/")
    is_root_doc = f in ["README.md", "CHANGELOG.md", "GEN26_FINAL_FORENSIC_AUDIT.md", "START.bat"]

    if is_config:
        category = "ACTIVE"
        reason = f"Essential repository configuration and deployment descriptor."
        confidence = "High"
    elif is_ci:
        category = "ACTIVE"
        reason = f"GitHub Actions automated CI/CD workflow pipeline."
        confidence = "High"
    elif is_test:
        category = "ACTIVE"
        reason = f"Automated test suite discovered and executed by unittest / pytest runner."
        confidence = "High"
    elif is_dashboard:
        category = "ACTIVE"
        reason = f"Web application dashboard template/runtime. Referenced in: {', '.join(refs[:3]) if refs else 'Flask server'}"
        confidence = "High"
    elif is_root_doc:
        category = "ACTIVE"
        reason = f"Authoritative root documentation and execution entrypoint. Referenced in: {', '.join(refs[:3]) if refs else 'Project root'}"
        confidence = "High"
    elif is_core:
        if refs:
            category = "ACTIVE"
            reason = f"Core quantitative engine module. Imported by: {', '.join(refs[:3])} (total {len(refs)} references)"
            confidence = "High"
        else:
            category = "ORPHANED"
            reason = "Core engine module with no direct textual import reference in repository."
            confidence = "Medium"
    elif f.startswith("data/"):
        if is_protected_data or refs:
            category = "ACTIVE"
            reason = f"Canonical SSoT dataset / database persistence store. Accessed by: {', '.join(refs[:3]) if refs else 'SQLite / Market services'}"
            confidence = "High"
        else:
            if "snapshot" in f or "backup" in f or "old" in f:
                category = "SUPERSEDED"
                reason = "Historical snapshot replaced by data/canonical_prices_live.json and data/gen26_market.db."
                confidence = "High"
            else:
                category = "ORPHANED"
                reason = "Data file without direct code reference."
                confidence = "Medium"
    elif f.startswith("scripts/"):
        if refs or f in ["scripts/sync_reports_from_ssot.py", "scripts/automated_consistency_audit.py", "scripts/mlops_retrain.py", "scripts/simulate_live_quant_cycle.py", "scripts/audit_trading_sessions.py", "scripts/run_e2e_pipeline_trace.py", "scripts/dual_source_price_verification.py", "scripts/enforce_strict_244_truth_audit.py", "scripts/verify_all_244_stocks_real_data.py"]:
            category = "ACTIVE"
            reason = f"Operational DevOps, maintenance, or audit execution script. Referenced in: {', '.join(refs[:3]) if refs else 'Manual / CI execution'}"
            confidence = "High"
        elif any(k in f for k in ["find_script", "check_brace", "trace_unclosed", "debug_frontend", "inventory"]):
            category = "CONFIRMED_UNUSED"
            reason = "Temporary diagnostic script created during maintenance sessions."
            confidence = "High"
        else:
            category = "ORPHANED"
            reason = "Stand-alone maintenance utility script not referenced by other modules."
            confidence = "Medium"
    elif f.startswith("reports/"):
        if f.startswith("reports/authoritative_20_reports/"):
            category = "ACTIVE"
            reason = f"Official authoritative report in 20-report system dossier. Referenced in: {', '.join(refs[:3]) if refs else '00_MASTER_CONSOLIDATED_SYSTEM_DOSSIER.md'}"
            confidence = "High"
        elif f in ["reports/00_MASTER_CONSOLIDATED_SYSTEM_DOSSIER.md", "reports/consistency_audit_report.json", "reports/final_forensic_audit.json", "reports/incubation_verdict.json", "reports/authoritative_paper_sessions.json"]:
            category = "ACTIVE"
            reason = f"Master consolidated report or live audit output. Referenced in: {', '.join(refs[:3]) if refs else 'SSoT audit suite'}"
            confidence = "High"
        elif f in ["reports/paper_sessions/session_98.json", "reports/paper_sessions/session_98.md", "reports/paper_sessions/session_99.json", "reports/paper_sessions/session_99.md"]:
            category = "SUPERSEDED"
            reason = "Legacy mock paper sessions replaced by canonical daily session logs (reports/paper_sessions/session_04_2026-08-21.json, session_05_2026-08-24.json)."
            confidence = "High"
        elif refs:
            category = "ACTIVE"
            reason = f"Audit telemetry report artifact. Referenced in: {', '.join(refs[:3])}"
            confidence = "High"
        elif any(k in f for k in ["qa_master_pass", "testing_quality", "fullstack_runtime", "ui_e2e_results", "ui_button_test", "ui_navigation_results"]):
            category = "SUPERSEDED"
            reason = "Static audit log artifact superseded by reports/final_forensic_audit.json and reports/consistency_audit_report.json."
            confidence = "High"
        else:
            category = "ORPHANED"
            reason = "Historical report artifact without active inbound links."
            confidence = "Medium"
    elif f in ["full_raw_test_run.txt", "test_output_raw.txt"]:
        category = "CONFIRMED_UNUSED"
        reason = "Temporary raw terminal test output log."
        confidence = "High"
    else:
        if refs:
            category = "ACTIVE"
            reason = f"Referenced by: {', '.join(refs[:3])}"
            confidence = "High"
        else:
            category = "ORPHANED"
            reason = "No references found in repository."
            confidence = "Medium"

    classified_inventory.append({
        "file_path": f,
        "category": category,
        "reason": reason,
        "confidence": confidence,
        "refs_count": len(refs),
        "refs": refs[:5]
    })

# Save JSON
with open(os.path.join(WORKSPACE, "reports", "classified_inventory.json"), "w", encoding="utf-8") as out:
    json.dump(classified_inventory, out, indent=2, ensure_ascii=False)

# Summary
cats = {}
for r in classified_inventory:
    c = r["category"]
    cats[c] = cats.get(c, 0) + 1

print("\n=== CLASSIFICATION SUMMARY ===")
for k, v in sorted(cats.items()):
    print(f"  {k}: {v}")

print(f"\nTotal files classified: {len(classified_inventory)}")

# Print CONFIRMED_UNUSED and SUPERSEDED files
print("\n=== SUPERSEDED & CONFIRMED_UNUSED FILES ===")
for r in classified_inventory:
    if r["category"] in ["SUPERSEDED", "CONFIRMED_UNUSED"]:
        print(f"[{r['category']}] {r['file_path']} -> {r['reason']}")
