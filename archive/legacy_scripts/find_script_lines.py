import re

with open("dashboard/templates/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

script_starts = []
for i, line in enumerate(lines):
    if "<script" in line:
        script_starts.append(i + 1)

print("Script tags start at lines:", script_starts)
