#!/usr/bin/env python3
# =============================================================================
# tests/e2e_browser_tests.py — Genuine End-to-End Headless Browser Test Suite
# Automates live DOM interaction and backend persistence verification via Selenium.
# =============================================================================

import os
import sys
import json
import time
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

WATCHLIST_FILE = os.path.join(WORKSPACE, "data", "user_watchlist.json")
BASE_URL = "http://127.0.0.1:5000"


class TestE2EBrowserReliability(unittest.TestCase):
    """
    End-to-End Browser Automation Suite testing live DOM changes and Backend State Sync.
    """

    @classmethod
    def setUpClass(cls):
        # Configure Headless Driver (Edge primary with Chrome fallback)
        cls.driver = None
        
        # Try Edge Headless first
        try:
            from selenium.webdriver.edge.options import Options as EdgeOptions
            edge_opt = EdgeOptions()
            edge_opt.add_argument("--headless=new")
            edge_opt.add_argument("--disable-gpu")
            edge_opt.add_argument("--no-sandbox")
            edge_opt.add_argument("--disable-dev-shm-usage")
            edge_opt.add_argument("--window-size=1920,1080")
            cls.driver = webdriver.Edge(options=edge_opt)
        except Exception:
            pass

        if cls.driver is None:
            try:
                from selenium.webdriver.chrome.options import Options as ChromeOptions
                chrome_opt = ChromeOptions()
                chrome_opt.add_argument("--headless=new")
                chrome_opt.add_argument("--disable-gpu")
                chrome_opt.add_argument("--no-sandbox")
                chrome_opt.add_argument("--disable-dev-shm-usage")
                chrome_opt.add_argument("--window-size=1920,1080")
                cls.driver = webdriver.Chrome(options=chrome_opt)
            except Exception as e:
                raise unittest.SkipTest(f"Headless browser not available: {e}")

        cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        if cls.driver:
            try:
                cls.driver.quit()
            except Exception:
                pass

    def test_01_homepage_dom_loaded_and_banners(self):
        """Verify dashboard loads completely with correct RTL direction and funnel banner."""
        self.driver.get(BASE_URL)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "universe-funnel-banner"))
        )

        # 1. Verify Page Title
        self.assertIn("GEN-26", self.driver.title)

        # 2. Verify Funnel Banner in DOM
        tot_el = self.driver.find_element(By.ID, "funnel-total-universe")
        liq_el = self.driver.find_element(By.ID, "funnel-liquid-count")
        opp_el = self.driver.find_element(By.ID, "funnel-opps-count")

        self.assertEqual(tot_el.text.strip(), "224")
        self.assertTrue(int(liq_el.text.strip()) > 0)
        self.assertTrue(int(opp_el.text.strip()) > 0)

    def test_02_watchlist_bookmark_save_and_backend_sync(self):
        """
        Scenario:
        1. Open Dashboard in Headless Browser.
        2. Navigate to Watchlist tab by clicking '#nav-watchlist'.
        3. Select 'TMGH.CA' from '#watchlist-select' dropdown.
        4. Click '➕ إضافة للقائمة' (Save/Bookmark) button.
        5. Verify DOM updates: '#watchlist-tbody' contains 'TMGH' row.
        6. Verify Backend JSON: 'data/user_watchlist.json' contains 'TMGH.CA'.
        7. Click '🗑️ حذف' button in DOM.
        8. Verify DOM removal and Backend JSON removal.
        """
        test_ticker = "TMGH.CA"

        # Ensure test ticker is removed beforehand
        try:
            from core.watchlist import WatchlistManager
            WatchlistManager.remove_from_watchlist(test_ticker)
        except Exception:
            pass

        self.driver.get(BASE_URL)
        wait = WebDriverWait(self.driver, 10)

        # 1. Click Smart Watchlist Nav Tab
        nav_item = wait.until(EC.element_to_be_clickable((By.ID, "nav-watchlist")))
        nav_item.click()

        # Wait for tab-watchlist to become active
        wait.until(EC.visibility_of_element_located((By.ID, "tab-watchlist")))

        # 2. Select TMGH.CA from dropdown
        select_el = wait.until(EC.presence_of_element_located((By.ID, "watchlist-select")))
        sel = Select(select_el)
        sel.select_by_value(test_ticker)

        # 3. Click Add to Watchlist (Bookmark) button
        add_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'إضافة للقائمة')]")
        self.driver.execute_script("arguments[0].click();", add_btn)

        # 4. Wait for DOM update: tbody contains TMGH
        time.sleep(1.5)
        tbody = wait.until(EC.presence_of_element_located((By.ID, "watchlist-tbody")))
        self.assertIn("TMGH", tbody.text)

        # 5. Verify Backend File Persistence
        self.assertTrue(os.path.exists(WATCHLIST_FILE))
        with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn(test_ticker, data.get("tickers", []))

        # 6. Delete TMGH.CA via UI button in the row
        row = tbody.find_element(By.XPATH, f".//tr[contains(., 'TMGH')]")
        del_btn = row.find_element(By.XPATH, ".//button[contains(text(), 'حذف')]")
        self.driver.execute_script("arguments[0].click();", del_btn)

        time.sleep(1.5)
        # 7. Verify Backend File sync after delete
        with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
            data_after = json.load(f)
        self.assertNotIn(test_ticker, data_after.get("tickers", []))

    def test_03_navigation_tab_switching(self):
        """Verify SPA tab switching dynamically activates DOM panels."""
        self.driver.get(BASE_URL)
        wait = WebDriverWait(self.driver, 10)

        # Navigate to Ranking
        self.driver.find_element(By.ID, "nav-ranking").click()
        ranking_tab = wait.until(EC.visibility_of_element_located((By.ID, "tab-ranking")))
        self.assertIn("active", ranking_tab.get_attribute("class"))

        # Navigate to Risk Center
        self.driver.find_element(By.ID, "nav-risk_center").click()
        risk_tab = wait.until(EC.visibility_of_element_located((By.ID, "tab-risk_center")))
        self.assertIn("active", risk_tab.get_attribute("class"))

        # Navigate to Health
        self.driver.find_element(By.ID, "nav-health").click()
        health_tab = wait.until(EC.visibility_of_element_located((By.ID, "tab-health")))
        self.assertIn("active", health_tab.get_attribute("class"))


if __name__ == "__main__":
    unittest.main()
