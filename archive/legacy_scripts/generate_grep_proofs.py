import os
import sys
import json
import subprocess

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

with open(os.path.join(WORKSPACE, "reports", "clean_inventory_rows.json"), "r", encoding="utf-8") as f:
    rows = json.load(f)

proof_targets = [r for r in rows if r[1] in ["CONFIRMED_UNUSED", "SUPERSEDED"]]

proof_reports = []

for item in proof_targets:
    path, cat, reason, conf = item
    base = os.path.basename(path)
    
    # Run git grep or ripgrep across the repo
    cmd = f'git grep -n "{base}"'
    try:
        proc = subprocess.run(
            ["git", "grep", "-n", base],
            cwd=WORKSPACE,
            capture_output=True,
            text=True
        )
        out = proc.stdout.strip()
        err = proc.stderr.strip()
        raw_output = out if out else (err if err else "[No matches found across entire repository]")
    except Exception as e:
        raw_output = f"[Error executing search: {e}]"

    proof_reports.append({
        "file_path": path,
        "category": cat,
        "reason": reason,
        "search_command": cmd,
        "raw_search_output": raw_output
    })

with open(os.path.join(WORKSPACE, "reports", "grep_proofs.json"), "w", encoding="utf-8") as f:
    json.dump(proof_reports, f, indent=2, ensure_ascii=False)

print(f"Generated grep proofs for {len(proof_reports)} files.")
for p in proof_reports:
    print(f"\n--- File: {p['file_path']} [{p['category']}] ---")
    print(f"Command: {p['search_command']}")
    print(f"Output:\n{p['raw_search_output'][:300]}")
