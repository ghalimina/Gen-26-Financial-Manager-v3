import unittest
import os
import json

os.environ['FLASK_TESTING'] = '1'
from dashboard.app import app


class TestDashboardQuantWidgets(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_macro_telemetry_endpoints(self):
        """Test /api/macro and /api/macro/telemetry return expected data structure."""
        resp = self.client.get('/api/macro')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('macro_telemetry', data)
        self.assertIn('interest_rate_pct', data['macro_telemetry'])
        self.assertIn('inflation_rate_pct', data['macro_telemetry'])
        self.assertIn('usd_egp', data['macro_telemetry'])
        self.assertIn('macro_regime', data['macro_telemetry'])
        self.assertIn('sector_biases', data)

        resp2 = self.client.get('/api/macro/telemetry')
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.get_json()
        self.assertIn('macro_regime', data2)

    def test_insider_trading_endpoints(self):
        """Test /api/insider and /api/insider/market_deals return valid list structure."""
        resp = self.client.get('/api/insider')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('deals', data)
        self.assertIsInstance(data['deals'], list)

        resp2 = self.client.get('/api/insider/market_deals')
        self.assertEqual(resp2.status_code, 200)
        data2 = resp2.get_json()
        self.assertIn('deals', data2)

    def test_arbitrage_pairs_endpoint(self):
        """Test /api/arbitrage/pairs returns all 5 canonical EGX pairs."""
        resp = self.client.get('/api/arbitrage/pairs')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('opportunities', data)
        self.assertIn('total_pairs_monitored', data)
        self.assertEqual(data['total_pairs_monitored'], 5)
        self.assertEqual(len(data['opportunities']), 5)

        for opp in data['opportunities']:
            self.assertIn('pair_id', opp)
            self.assertIn('ticker_A', opp)
            self.assertIn('ticker_B', opp)
            self.assertIn('z_score', opp)
            self.assertIn('trade_recommendation_ar', opp)
            self.assertIn('is_actionable', opp)

    def test_dashboard_html_elements(self):
        """Test index.html contains all required UI telemetry widgets, tabs, and print hooks."""
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        html = resp.get_data(as_text=True)

        # 1. Macro Live Barometer
        self.assertIn('id="macro-risk-banner"', html)
        self.assertIn('id="macro-usd-val"', html)
        self.assertIn('id="macro-cbe-val"', html)
        self.assertIn('id="macro-inflation-val"', html)
        self.assertIn('id="macro-regime-val"', html)

        # 2. Insider Trading Radar Tab & Table
        self.assertIn('id="tab-insider_radar"', html)
        self.assertIn('id="insider-deals-tbody"', html)
        self.assertIn('id="nav-insider_radar"', html)

        # 3. Statistical Arbitrage Tab & Cards
        self.assertIn('id="tab-arbitrage_monitor"', html)
        self.assertIn('id="arbitrage-pairs-container"', html)
        self.assertIn('id="nav-arbitrage_monitor"', html)

        # 4. Export PDF / Print Button & Print Styles
        self.assertIn('exportDailyReportPDF()', html)
        self.assertIn('@media print', html)


if __name__ == '__main__':
    unittest.main()
