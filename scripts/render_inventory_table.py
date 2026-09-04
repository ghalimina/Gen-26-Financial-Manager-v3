import os
import sys
import json

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

with open(os.path.join(WORKSPACE, "reports", "clean_inventory_rows.json"), "r", encoding="utf-8") as f:
    rows = json.load(f)

# Sort rows by category: CONFIRMED_UNUSED, SUPERSEDED, ORPHANED, ACTIVE, then path
cat_order = {"CONFIRMED_UNUSED": 0, "SUPERSEDED": 1, "ORPHANED": 2, "ACTIVE": 3}
rows.sort(key=lambda x: (cat_order.get(x[1], 4), x[0]))

md_lines = []
md_lines.append("| File Path | Category | Evidence / Reason | Confidence |")
md_lines.append("| :--- | :---: | :--- | :---: |")

for path, cat, reason, conf in rows:
    # escape pipe characters in reason
    clean_reason = reason.replace("|", "/")
    md_lines.append(f"| `{path}` | **{cat}** | {clean_reason} | {conf} |")

md_content = "\n".join(md_lines)

with open(os.path.join(WORKSPACE, "reports", "complete_inventory_table.md"), "w", encoding="utf-8") as f:
    f.write(md_content)

print(f"Generated Markdown table with {len(rows)} rows.")
