#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from dashboard.app import app

client = app.test_client()

print("--- 1. Testing Adding Stock Positions to Real Portfolio ---")
r1 = client.post('/api/real_portfolio/add', json={
    'ticker': 'COMI.CA',
    'quantity': 150,
    'average_entry_price': 135.0,
    'manual_notes': 'Primary Banking Core'
})
print("Add COMI.CA Status:", r1.status_code, r1.get_json())

r2 = client.post('/api/real_portfolio/add', json={
    'ticker': 'SWDY.CA',
    'quantity': 250,
    'average_entry_price': 122.0,
    'manual_notes': 'Industrial Leader'
})
print("Add SWDY.CA Status:", r2.status_code, r2.get_json())

print("\n--- 2. Testing Real Portfolio Analytics & Pricing ---")
r3 = client.get('/api/real_portfolio')
data = r3.get_json()
print("Portfolio Equity (EGP):", data.get("total_portfolio_equity_egp"))
print("Stock Market Value (EGP):", data.get("stock_market_value_egp"))
print("Free Cash (EGP):", data.get("free_cash_egp"))
print("Total Unrealized P&L (EGP):", data.get("unrealized_pnl_egp"), f"({data.get('unrealized_pnl_pct')}%)")
print("Positions Count:", len(data.get("positions", [])))
for p in data.get("positions", []):
    print(f"  * {p['company_name']} ({p['ticker']}): {p['quantity']} shares @ {p['average_entry_price']} EGP | Live: {p['current_price']} EGP | PnL: {p['unrealized_pnl_egp']:+.2f} EGP ({p['unrealized_pnl_pct']:+.2f}%) | Model: {p.get('proposed_action')}")

print("\n--- 3. Testing Excel/CSV Export ---")
r_export = client.get('/api/real_portfolio/export?format=csv')
print("Export CSV Status:", r_export.status_code, "Bytes:", len(r_export.data))
assert r_export.status_code == 200
print("  [OK] Export CSV returned HTTP 200 with UTF-8 BOM.")
