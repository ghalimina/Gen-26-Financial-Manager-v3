import re
import sys

with open("dashboard/templates/index.html", "r", encoding="utf-8") as f:
    content = f.read()

scripts = list(re.finditer(r"<script(?:\s+[^>]*)?>(.*?)</script>", content, re.DOTALL))
script_content = scripts[4].group(1)
start_pos = scripts[4].start()
start_line = content[:start_pos].count("\n") + 1

lines = script_content.split("\n")

stack = [] # tuples of (line_no, line_content)

for idx, line in enumerate(lines):
    line_no = start_line + idx
    # Remove string literals and comments simply
    cleaned = re.sub(r"'(?:\\.|[^'])*'", "''", line)
    cleaned = re.sub(r'"(?:\\.|[^"])*"', '""', cleaned)
    cleaned = re.sub(r"`(?:\\.|[^`])*`", "``", cleaned)
    cleaned = re.sub(r"//.*$", "", cleaned)

    for ch in cleaned:
        if ch == '{':
            stack.append((line_no, line.strip()))
        elif ch == '}':
            if stack:
                stack.pop()
            else:
                print(f"Extra closing brace at line {line_no}: {line.strip()}")

print(f"Unclosed braces count: {len(stack)}")
for item in stack[-10:]:
    print(f"  Line {item[0]}: {item[1]}")
