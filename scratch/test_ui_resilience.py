import ast
import os

app_file = r"c:\Users\Administrator\Desktop\New folder\app.py"
with open(app_file, "r", encoding="utf-8") as f:
    source = f.read()

tree = ast.parse(source)

# Let's find all function definitions
funcs = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

print("1. Functions without try/except blocks:")
for f in funcs:
    has_try = any(isinstance(node, ast.Try) for node in ast.walk(f))
    if not has_try:
        print(f"  - {f.name}")

# Find missing data handling (checking empty dataframes before using them)
print("\n2. Potential DataFrame empty crashes (using iloc or accessing columns without .empty check):")
for node in ast.walk(tree):
    if isinstance(node, ast.Subscript):
        # Very rudimentary check for potential df index access
        pass

# Check format strings
print("\n3. Currency formatting issues (checking for missing commas in format strings):")
import re
formats = re.findall(r'f"\{[^}]*:[^}]*f\}"', source)
for fmt in formats:
    if ',' not in fmt and ('EGP' in fmt or 'ج.م' in fmt):
        print(f"  - Missing comma in monetary format: {fmt}")

print("\n4. Download button encoding:")
dl_lines = [l for l in source.split('\n') if 'st.download_button' in l]
for l in dl_lines:
    if 'utf-8-sig' not in l:
        print(f"  - Missing utf-8-sig encoding in download: {l.strip()}")

print("\n5. Session State Keys Analysis:")
state_keys = re.findall(r"st\.session_state\['([^']+)'\]", source)
print(f"  - Keys found: {set(state_keys)}")
