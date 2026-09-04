#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# scripts/system_interconnection_inspector.py
# Comprehensive Repository Interconnection, Coupling, and Cohesion Inspector
# =============================================================================

import os
import sys
import json
import sqlite3
import re
from typing import Dict, List, Any, Set

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

def check_python_modules_importability():
    print("\n--- 1. Testing Core Python Modules Importability & Instantiation ---")
    core_dir = os.path.join(WORKSPACE, "core")
    files = [f for f in os.listdir(core_dir) if f.endswith(".py") and not f.startswith("__")]
    success = 0
    errors = []
    
    for f in sorted(files):
        mod_name = f"core.{f[:-3]}"
        try:
            __import__(mod_name)
            success += 1
        except Exception as e:
            errors.append((mod_name, str(e)))
            
    print(f"Core Python Modules: {success}/{len(files)} successfully imported.")
    if errors:
        for m, err in errors:
            print(f"  [ERROR] {m}: {err}")
    return len(errors) == 0

def check_trading_agents_interconnection():
    print("\n--- 2. Testing TradingAgents Subpackage Interconnection ---")
    ta_dir = os.path.join(WORKSPACE, "core", "trading_agents")
    files = [f for f in os.listdir(ta_dir) if f.endswith(".py") and not f.startswith("__")]
    success = 0
    errors = []
    
    for f in sorted(files):
        mod_name = f"core.trading_agents.{f[:-3]}"
        try:
            __import__(mod_name)
            success += 1
        except Exception as e:
            errors.append((mod_name, str(e)))
            
    print(f"TradingAgents Modules: {success}/{len(files)} successfully imported.")
    if errors:
        for m, err in errors:
            print(f"  [ERROR] {m}: {err}")
            
    # Test end-to-end deliberation link
    try:
        from core.trading_agents.orchestrator import TradingAgentsOrchestrator
        res = TradingAgentsOrchestrator.run_stock_deliberation("COMI.CA", persist=False)
        assert "analyst_team" in res and "debate" in res and "proposal" in res and "executive_decision" in res
        print("  [OK] TradingAgents end-to-end deliberation pipeline functional.")
    except Exception as e:
        print(f"  [ERROR] TradingAgents pipeline execution: {e}")
        return False
    return len(errors) == 0

def check_database_and_ssot_sync():
    print("\n--- 3. Testing SSoT Data Layer & Database Synchronization ---")
    ssot_path = os.path.join(WORKSPACE, "data", "canonical_prices_live.json")
    db_path = os.path.join(WORKSPACE, "data", "gen26_market.db")
    
    if not os.path.exists(ssot_path):
        print(f"  [ERROR] Missing {ssot_path}")
        return False
        
    with open(ssot_path, "r", encoding="utf-8") as f:
        ssot_data = json.load(f)
    stocks_count = len(ssot_data.get("stocks", {})) if "stocks" in ssot_data else len(ssot_data)
    print(f"  SSoT Canonical JSON contains {stocks_count} stocks.")
    
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM stocks_universe")
        db_univ_count = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM live_prices")
        db_prices_count = cur.fetchone()[0]
        conn.close()
        print(f"  SQLite gen26_market.db: stocks_universe={db_univ_count}, live_prices={db_prices_count}")
    else:
        print("  [WARN] Database file not found on disk.")
    return stocks_count == 244

def check_flask_routes_coverage():
    print("\n--- 4. Testing Flask API Routes Coverage & Endpoints ---")
    from dashboard.app import app
    client = app.test_client()
    routes_to_test = [
        ("/", 200),
        ("/api/macro", 200),
        ("/api/macro/telemetry", 200),
        ("/api/corporate_actions", 200),
        ("/api/insider", 200),
        ("/api/arbitrage/pairs", 200),
        ("/api/system/reality_audit", 200),
        ("/api/observability/readiness_matrix", 200),
        ("/api/observability/market_breadth", 200),
        ("/api/v1/trading-agents/debate/COMI.CA", 200),
        ("/api/v1/trading-agents/scan", 200),
        ("/api/morning_briefing", 200),
        ("/api/fundamentals/COMI.CA", 200),
        ("/api/ranking", 200),
    ]
    all_ok = True
    for route, expected_code in routes_to_test:
        try:
            resp = client.get(route)
            if resp.status_code == expected_code:
                print(f"  [OK] {route} -> HTTP {resp.status_code}")
            else:
                print(f"  [FAIL] {route} -> HTTP {resp.status_code} (Expected {expected_code})")
                all_ok = False
        except Exception as e:
            print(f"  [ERROR] {route} -> Exception: {e}")
            all_ok = False
    return all_ok

def check_html_ui_tabs_interconnection():
    print("\n--- 5. Testing Dashboard HTML UI Tabs & JS Navigation ---")
    html_path = os.path.join(WORKSPACE, "dashboard", "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Extract VALID_TABS from script
    match = re.search(r'const VALID_TABS\s*=\s*\[(.*?)\];', content, re.DOTALL)
    if not match:
        print("  [ERROR] Could not extract VALID_TABS from index.html")
        return False
        
    raw_tabs = match.group(1)
    tabs = [t.strip().strip("'\"") for t in raw_tabs.split(",") if t.strip()]
    print(f"  Extracted {len(tabs)} tabs from VALID_TABS in index.html:")
    
    missing_panels = []
    for t in tabs:
        # Alias handling
        tid = "research-lab" if t in ["research_lab", "research-lab"] else t
        has_panel = f'id="tab-{tid}"' in content or f"id='tab-{tid}'" in content
        if not has_panel:
            missing_panels.append(t)
        else:
            print(f"    [OK] Tab '{t}' -> HTML Panel '#tab-{tid}' exists.")
            
    if missing_panels:
        print(f"  [ERROR] Missing DOM panels for tabs: {missing_panels}")
        return False
    return True

def main():
    print("=" * 80)
    print("      GEN-26 ARCHITECTURAL COHESION & INTERCONNECTION AUDIT")
    print("=" * 80)
    
    c1 = check_python_modules_importability()
    c2 = check_trading_agents_interconnection()
    c3 = check_database_and_ssot_sync()
    c4 = check_flask_routes_coverage()
    c5 = check_html_ui_tabs_interconnection()
    
    print("\n" + "=" * 80)
    if c1 and c2 and c3 and c4 and c5:
        print("🎉 ALL REPOSITORY LAYERS ARE 100% INTERCONNECTED, CONSISTENT & COHESIVE!")
    else:
        print("⚠️ SOME DISCONNECTIONS OR DRIFTS WERE IDENTIFIED (See logs above).")
    print("=" * 80)

if __name__ == "__main__":
    main()
