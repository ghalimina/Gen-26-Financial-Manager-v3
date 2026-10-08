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
    # Exclude directories
    dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", ".pytest_cache", ".vscode", ".agents", "scratch"]]
    for f in files:
        if f.endswith(".pyc"):
            continue
        rel_path = os.path.relpath(os.path.join(root, f), WORKSPACE).replace("\\", "/")
        all_files.append(rel_path)

all_files.sort()

# Read content of all text files to search for references
text_search_corpus = {}
for rel in all_files:
    full_path = os.path.join(WORKSPACE, rel)
    if os.path.getsize(full_path) < 2 * 1024 * 1024: # < 2MB
        try:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as fp:
                text_search_corpus[rel] = fp.read()
        except Exception:
            pass

print(f"Total files in workspace: {len(all_files)}")
print(f"Total searchable files: {len(text_search_corpus)}")

# Let's inspect directories breakdown
breakdown = {}
for f in all_files:
    top_dir = f.split("/")[0] if "/" in f else "root"
    breakdown[top_dir] = breakdown.get(top_dir, 0) + 1

print("\nFiles per top-level folder:")
for k, v in sorted(breakdown.items()):
    print(f"  {k}: {v}")

with open(os.path.join(WORKSPACE, "reports", "all_repo_files_list.json"), "w", encoding="utf-8") as out:
    json.dumps(all_files, out, indent=2)
