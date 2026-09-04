import re
import subprocess
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

with open("dashboard/templates/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Extract script content
scripts = re.findall(r"<script(?:\s+[^>]*)?>(.*?)</script>", html, re.DOTALL)
print(f"Found {len(scripts)} script tags.")

for idx, s in enumerate(scripts):
    filename = f"scratch_script_{idx}.js"
    with open(filename, "w", encoding="utf-8") as f_out:
        f_out.write(s)
    
    # Run node --check
    res = subprocess.run(["node", "--check", filename], capture_output=True, text=True)
    if res.returncode != 0:
        print(f"❌ SYNTAX ERROR in script tag #{idx}:")
        print(res.stderr)
    else:
        print(f"✅ Script tag #{idx} syntax OK.")
    
    if os.path.exists(filename):
        os.remove(filename)
