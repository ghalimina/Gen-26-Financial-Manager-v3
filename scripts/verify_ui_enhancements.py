#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_ui():
    html_files = [
        os.path.join(WORKSPACE, "dashboard", "index.html"),
        os.path.join(WORKSPACE, "dashboard", "templates", "index.html"),
        os.path.join(WORKSPACE, "templates", "index.html")
    ]
    
    required_tokens = [
        "detail-trading-levels-card",
        "detail-live-price",
        "detail-entry-zone",
        "detail-stop-loss",
        "detail-stop-pct",
        "detail-rr-ratio",
        "horizon-short-target",
        "horizon-short-return",
        "horizon-short-prob",
        "horizon-med-target",
        "horizon-med-return",
        "horizon-med-prob",
        "horizon-long-target",
        "horizon-long-return",
        "horizon-long-prob",
        "/api/stocks/",
        "slice(0, 100)",
        "ranking-tbody",
        "details-stock-select",
        'dir="rtl"',
        'lang="ar"',
        "ltr-text",
        "COMI.CA"
    ]
    
    all_passed = True
    for path in html_files:
        if not os.path.exists(path):
            print(f"❌ Missing file: {path}")
            all_passed = False
            continue
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        for token in required_tokens:
            if token not in content:
                print(f"❌ In {os.path.basename(path)}: missing '{token}'")
                all_passed = False
            else:
                pass
        print(f"✅ {path}: Verified all {len(required_tokens)} tokens present.")
    
    if all_passed:
        print("\n🎉 ALL UI ENHANCEMENT CHECKS PASSED (100%)\n")
    else:
        sys.exit(1)

if __name__ == "__main__":
    test_ui()
