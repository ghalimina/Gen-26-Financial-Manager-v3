import os
import sys
import json
import re
import subprocess
from pathlib import Path

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

# 1. Collect all files in workspace excluding .git, __pycache__, .pytest_cache, .vscode, .agents
all_files = []
for root, dirs, files in os.walk(WORKSPACE):
    dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", ".pytest_cache", ".vscode", ".agents", "scratch"]]
    for f in files:
        if f.endswith(".pyc"):
            continue
        rel_path = os.path.relpath(os.path.join(root, f), WORKSPACE).replace("\\", "/")
        all_files.append(rel_path)

all_files.sort()

# Read content of all text files into corpus
text_corpus = {}
for rel in all_files:
    full_path = os.path.join(WORKSPACE, rel)
    # Skip huge binaries or db files
    if rel.endswith((".db", ".db-wal", ".db-shm", ".pyc", ".png", ".jpg", ".ico")):
        continue
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as fp:
            text_corpus[rel] = fp.read()
    except Exception:
        pass

def find_references(target_file: str):
    """Finds all files in text_corpus that reference target_file or its module name."""
    refs = []
    base_name = os.path.basename(target_file)
    name_no_ext = os.path.splitext(base_name)[0]
    
    # Generate search patterns
    patterns = [
        re.escape(target_file),
        re.escape(base_name),
    ]
    
    # If python file in core/ or dashboard/ or scripts/
    if target_file.endswith(".py"):
        mod_dot = target_file.replace("/", ".").replace(".py", "")
        patterns.append(re.escape(mod_dot))
        patterns.append(r"\b" + re.escape(name_no_ext) + r"\b")

    regex = re.compile("|".join(patterns), re.IGNORECASE)

    for doc_path, content in text_corpus.items():
        if doc_path == target_file:
            continue
        if regex.search(content):
            refs.append(doc_path)
            
    return refs

results = []

for f in all_files:
    refs = find_references(f)
    base = os.path.basename(f)
    category = "ACTIVE"
    confidence = "High"
    reason = ""

    # Check protected rules
    is_protected_data = f.startswith("data/") and any(k in f for k in ["canonical", "live", "universe", "production", "market.db", "gold", "gdr", "forensics"])
    is_test = f.startswith("tests/")
    is_config = f in ["requirements.txt", "runtime.txt", "Procfile", ".gitignore", ".env.example", "settings.json", "config.py", "render.yaml"]
    is_ci = f.startswith(".github/")
    is_core = f.startswith("core/")
    is_dashboard = f.startswith("dashboard/") or f.startswith("templates/")
    is_root_doc = f in ["README.md", "CHANGELOG.md", "GEN26_FINAL_FORENSIC_AUDIT.md", "START.bat"]

    if is_config:
        category = "ACTIVE"
        reason = f"Essential project infrastructure/config file."
        confidence = "High"
    elif is_ci:
        category = "ACTIVE"
        reason = f"CI/CD workflow automation."
        confidence = "High"
    elif is_test:
        category = "ACTIVE"
        reason = f"Test suite file discovered and executed by unittest / pytest."
        confidence = "High"
    elif is_dashboard:
        category = "ACTIVE"
        reason = f"Frontend UI template / Flask application module. Used by: {', '.join(refs[:3]) if refs else 'Flask server'}"
        confidence = "High"
    elif is_root_doc:
        category = "ACTIVE"
        reason = f"Root project documentation / entry point. Referenced in: {', '.join(refs[:3]) if refs else 'Project root'}"
        confidence = "High"
    elif is_core:
        if refs:
            category = "ACTIVE"
            reason = f"Core quant engine imported by: {', '.join(refs[:3])} (and {len(refs)-3} others)" if len(refs) > 3 else f"Core quant engine imported by: {', '.join(refs)}"
            confidence = "High"
        else:
            category = "ORPHANED"
            reason = "Core engine file with no direct import detected in text search."
            confidence = "Medium"
    elif f.startswith("data/"):
        if is_protected_data or refs:
            category = "ACTIVE"
            reason = f"Data store / SSoT catalog. Read by: {', '.join(refs[:3]) if refs else 'Database engine'}"
            confidence = "High"
        else:
            # Check if older snapshot
            if "snapshot" in f or "backup" in f or "old" in f:
                category = "SUPERSEDED"
                reason = "Historical snapshot replaced by live canonical data."
                confidence = "High"
            else:
                category = "ORPHANED"
                reason = "Data file without direct text reference."
                confidence = "Medium"
    elif f.startswith("scripts/"):
        if refs or f in ["scripts/sync_reports_from_ssot.py", "scripts/automated_consistency_audit.py", "scripts/mlops_retrain.py", "scripts/simulate_live_quant_cycle.py", "scripts/audit_trading_sessions.py", "scripts/run_e2e_pipeline_trace.py"]:
            category = "ACTIVE"
            reason = f"Operational maintenance / verification script. Used by: {', '.join(refs[:3]) if refs else 'DevOps / Manual audit'}"
            confidence = "High"
        else:
            # Check scratch/debug scripts
            if any(k in f for k in ["find_script", "check_brace", "trace_unclosed", "debug_frontend", "inventory"]):
                category = "CONFIRMED_UNUSED"
                reason = "One-off diagnostic / debugging scratch script created during maintenance."
                confidence = "High"
            else:
                category = "ORPHANED"
                reason = "Script not explicitly referenced in other files."
                confidence = "Medium"
    elif f.startswith("reports/"):
        # Check authoritative reports
        if f.startswith("reports/authoritative_20_reports/"):
            category = "ACTIVE"
            reason = f"Official authoritative report in 20-report system dossier. Referenced in: {', '.join(refs[:3]) if refs else '00_MASTER_CONSOLIDATED_SYSTEM_DOSSIER.md'}"
            confidence = "High"
        elif f in ["reports/00_MASTER_CONSOLIDATED_SYSTEM_DOSSIER.md", "reports/consistency_audit_report.json", "reports/final_forensic_audit.json", "reports/incubation_verdict.json"]:
            category = "ACTIVE"
            reason = f"Master consolidated report / primary audit output. Referenced in: {', '.join(refs[:3]) if refs else 'Core SSoT'}"
            confidence = "High"
        elif f.startswith("reports/paper_sessions/session_98") or f.startswith("reports/paper_sessions/session_99"):
            category = "SUPERSEDED"
            reason = "Outdated mock paper session files replaced by canonical daily session logs (session_04, session_05)."
            confidence = "High"
        elif refs:
            category = "ACTIVE"
            reason = f"Audit artifact / telemetry report. Referenced in: {', '.join(refs[:3])}"
            confidence = "High"
        else:
            category = "CONFIRMED_UNUSED" if ("qa_" in f or "testing_quality" in f or "fullstack_runtime" in f or "ui_e2e" in f) else "ORPHANED"
            reason = "Temporary / static audit log artifact superseded by live automated audit reports."
            confidence = "High" if category == "CONFIRMED_UNUSED" else "Medium"
    elif f in ["full_raw_test_run.txt", "test_output_raw.txt"]:
        category = "CONFIRMED_UNUSED"
        reason = "Temporary raw terminal output capture file."
        confidence = "High"
    else:
        if refs:
            category = "ACTIVE"
            reason = f"Referenced by: {', '.join(refs[:3])}"
            confidence = "High"
        else:
            category = "ORPHANED"
            reason = "No references found."
            confidence = "Medium"

    results.append({
        "file_path": f,
        "category": category,
        "reason": reason,
        "confidence": confidence,
        "refs_count": len(refs)
    })

# Save results JSON
with open(os.path.join(WORKSPACE, "reports", "complete_file_inventory_classification.json"), "w", encoding="utf-8") as out:
    json.dump(results, out, indent=2, ensure_ascii=False)

# Summary counts
cats = {}
for r in results:
    c = r["category"]
    cats[c] = cats.get(c, 0) + 1

print("\nClassification Summary:")
for k, v in sorted(cats.items()):
    print(f"  {k}: {v}")

print(f"\nTotal files classified: {len(results)}")
