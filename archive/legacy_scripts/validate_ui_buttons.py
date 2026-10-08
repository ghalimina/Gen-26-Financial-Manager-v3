#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
html_path = os.path.join(WORKSPACE, "dashboard", "templates", "index.html")

with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

onclick_matches = re.findall(r'onclick=[\'"]([^\'"]+)[\'"]', content)

functions_called = set()
for oc in onclick_matches:
    # Handle multiple statements separated by semicolon
    for stmt in oc.split(";"):
        stmt = stmt.strip()
        m = re.match(r'([a-zA-Z0-9_$]+)\s*\(', stmt)
        if m:
            functions_called.add(m.group(1))

defined_funcs = set(re.findall(r'function\s+([a-zA-Z0-9_$]+)\s*\(', content))
defined_funcs |= set(re.findall(r'const\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>', content))
defined_funcs |= set(re.findall(r'window\.([a-zA-Z0-9_$]+)\s*=', content))

builtins = {'alert', 'confirm', 'prompt', 'print', 'close', 'open', 'location', 'history', 'toggleMobileMenu'}
missing = functions_called - defined_funcs - builtins

print("=" * 60)
print(f"Total onclick functions called : {len(functions_called)}")
print(f"Total Javascript functions defined: {len(defined_funcs)}")
print(f"Missing / Undefined functions    : {missing}")
print("=" * 60)

for fn in sorted(missing):
    print(f"  [MISSING FUNCTION]: {fn}")
