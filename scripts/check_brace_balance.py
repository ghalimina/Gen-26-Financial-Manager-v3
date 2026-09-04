import re
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

with open("dashboard/templates/index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Find the 5th script tag (index 4)
scripts = list(re.finditer(r"<script(?:\s+[^>]*)?>(.*?)</script>", content, re.DOTALL))
if len(scripts) > 4:
    script_content = scripts[4].group(1)
    start_pos = scripts[4].start()
    start_line = content[:start_pos].count("\n") + 1
    print(f"Script #4 starts at line {start_line}")

    # Count braces
    open_curly = 0
    open_paren = 0
    open_square = 0

    lines = script_content.split("\n")
    for idx, l in enumerate(lines):
        line_no = start_line + idx
        # Strip comments & strings roughly for inspection
        # Just simple counting
        for ch in l:
            if ch == '{': open_curly += 1
            elif ch == '}': open_curly -= 1
            elif ch == '(': open_paren += 1
            elif ch == ')': open_paren -= 1
            elif ch == '[': open_square += 1
            elif ch == ']': open_square -= 1
        
        if open_curly < 0 or open_paren < 0 or open_square < 0:
            print(f"Negative balance at line {line_no}: curly={open_curly}, paren={open_paren}, square={open_square}")
            print(f"  Line: {l}")
            break

    print(f"Final balance: curly={open_curly}, paren={open_paren}, square={open_square}")
