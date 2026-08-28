import unittest
import os
import sys
import json
import tempfile
from unittest.mock import patch, MagicMock

os.environ['FLASK_TESTING'] = '1'

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE not in sys.path:
    sys.path.insert(0, WORKSPACE)

from core.database_engine import SQLiteDatabaseEngine
from core.risk_stress_testing_engine import RiskStressTestingEngine
from scripts.verify_ground_truth_reality import run_ground_truth_audit
from dashboard.app import app


class TestDatabaseAndStressEngine(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db_path = self.temp_db.name
        self.temp_db.close()
        self.db = SQLiteDatabaseEngine(db_path=self.temp_db_path)
        self.app = app
        self.client = self.app.test_client()

    def tearDown(self):
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except Exception:
                pass

    # =========================================================================
    # 1. DATABASE ENGINE TESTS
    # =========================================================================

    def test_database_initialization_and_tables(self):
        """Test SQLite tables and indexes exist."""
        stats = self.db.get_database_stats()
        self.assertIn("stocks_universe_count", stats)
        self.assertIn("live_prices_count", stats)
        self.assertIn("macro_indicators_count", stats)
        self.assertIn("arbitrage_pairs_count", stats)
        self.assertIn("decision_history_count", stats)

    def test_sync_universe_from_catalog(self):
        """Test populating 244 stocks from real catalog."""
        synced = self.db.sync_universe_from_catalog()
        self.assertEqual(synced, 244)
        stats = self.db.get_database_stats()
        self.assertEqual(stats["stocks_universe_count"], 244)

        # Query single stock
        cib = self.db.get_stock("COMI.CA")
        self.assertIsNotNone(cib)
        self.assertEqual(cib["symbol"], "COMI")
        self.assertEqual(cib["sector_en"], "Banking & Financial Services")

        all_stocks = self.db.get_all_stocks(active_only=False)
        self.assertEqual(len(all_stocks), 244)

        active_stocks = self.db.get_all_stocks(active_only=True)
        self.assertEqual(len(active_stocks), 229)

    def test_save_price_batch_and_queries(self):
        """Test inserting and querying live prices."""
        self.db.sync_universe_from_catalog()

        prices = [
            {
                "ticker": "COMI.CA",
                "price": 139.28,
                "previous_close": 138.50,
                "open": 139.00,
                "high": 141.00,
                "low": 138.00,
                "volume": 1500000.0,
                "turnover_egp": 208920000.0,
                "source": "UNIT_TEST_SSOT"
            },
            {
                "ticker": "SWDY.CA",
                "price": 128.00,
                "previous_close": 126.50,
                "source": "UNIT_TEST_SSOT"
            }
        ]

        saved = self.db.save_price_batch(prices)
        self.assertEqual(saved, 2)

        p_cib = self.db.get_live_price("COMI.CA")
        self.assertIsNotNone(p_cib)
        self.assertEqual(p_cib["price"], 139.28)

        # Verify joined get_stock has latest price
        stock_cib = self.db.get_stock("COMI.CA")
        self.assertEqual(stock_cib["price"], 139.28)

    def test_macro_and_arbitrage_persistence(self):
        """Test saving and retrieving macro state and arbitrage pairs."""
        macro_payload = {
            "usd_egp": 50.20,
            "interest_rate_pct": 27.25,
            "inflation_rate_pct": 26.50,
            "macro_regime": "RATE_HIKING_CYCLE",
            "macro_regime_ar": "🟢 دورة تشديد نقدي وفائدة مرتفعة"
        }
        saved_macro = self.db.save_macro_state(macro_payload)
        self.assertEqual(saved_macro, 3)

        retrieved_macro = self.db.get_macro_state()
        self.assertIn("USD_EGP", retrieved_macro)
        self.assertEqual(retrieved_macro["USD_EGP"]["value"], 50.20)

        pairs = [
            {
                "pair_id": "BANK_COMI_QNBE",
                "ticker_A": "COMI.CA",
                "ticker_B": "QNBE.CA",
                "name_A_ar": "البنك التجاري الدولي",
                "name_B_ar": "بنك قطر الوطني",
                "sector_ar": "الخدمات المالية والبنوك",
                "current_spread": 4.12,
                "mean_spread": 4.05,
                "std_spread": 0.15,
                "z_score": 0.47,
                "signal": "NEUTRAL",
                "is_actionable": False
            }
        ]
        saved_pairs = self.db.save_arbitrage_pairs(pairs)
        self.assertEqual(saved_pairs, 1)

        retrieved_pairs = self.db.get_arbitrage_pairs()
        self.assertEqual(len(retrieved_pairs), 1)
        self.assertEqual(retrieved_pairs[0]["ticker_a"], "COMI.CA")

    # =========================================================================
    # 2. RISK STRESS-TESTING & GOLD HEDGING TESTS
    # =========================================================================

    def test_simulate_stress_scenarios(self):
        """Test all standard stress scenarios and mathematical VaR outputs."""
        scenarios = ["flash_crash_15", "egp_devaluation_25", "cbe_rate_hike_300bps", "liquidity_crunch", "black_swan_20"]

        for sc in scenarios:
            res = RiskStressTestingEngine.simulate_stress_scenario(scenario=sc, initial_equity=1_000_000.0)
            self.assertEqual(res["scenario"], sc)
            self.assertIn("pre_shock_equity_egp", res)
            self.assertIn("post_shock_equity_egp", res)
            self.assertIn("risk_metrics", res)
            self.assertIn("var_95_horizon_30d_pct", res["risk_metrics"])
            self.assertIn("var_99_horizon_30d_pct", res["risk_metrics"])
            self.assertIn("cvar_99_expected_shortfall_pct", res["risk_metrics"])
            self.assertIn("gold_hedge_solution", res)
            self.assertGreater(res["risk_metrics"]["var_95_horizon_30d_pct"], 0.0)
            self.assertGreater(res["risk_metrics"]["var_99_horizon_30d_pct"], 0.0)

    def test_calculate_gold_hedge_allocation(self):
        """Test dynamic gold hedge allocation using AZG.CA."""
        hedge_bull = RiskStressTestingEngine.calculate_gold_hedge_allocation(
            regime="STRONG_BULL",
            risk_score=0.20,
            portfolio_value=1_000_000.0
        )
        self.assertEqual(hedge_bull["gold_etf_ticker"], "AZG.CA")
        self.assertGreaterEqual(hedge_bull["recommended_gold_weight_pct"], 5.0)
        self.assertLessEqual(hedge_bull["recommended_gold_weight_pct"], 20.0)
        self.assertGreater(hedge_bull["target_gold_value_egp"], 0.0)
        self.assertGreater(hedge_bull["recommended_shares_azg"], 0)

        hedge_crash = RiskStressTestingEngine.calculate_gold_hedge_allocation(
            regime="FLASH_CRASH",
            risk_score=0.95,
            portfolio_value=1_000_000.0
        )
        self.assertGreater(hedge_crash["recommended_gold_weight_pct"], hedge_bull["recommended_gold_weight_pct"])

    # =========================================================================
    # 3. GROUND-TRUTH REALITY AUDITOR TEST
    # =========================================================================

    def test_ground_truth_reality_audit(self):
        """Test running ground-truth reality audit report."""
        report = run_ground_truth_audit(export_report=False)
        self.assertIn("live_reality_match_score_pct", report)
        self.assertIn("overall_certification", report)
        self.assertIn("sections", report)

        # Verify zero mocks
        eq_sec = report["sections"]["equities_universe"]
        self.assertEqual(eq_sec["mock_artifacts_count"], 0)
        self.assertEqual(eq_sec["status"], "PASSED")

        # Verify score is high
        self.assertGreaterEqual(report["live_reality_match_score_pct"], 80.0)

    # =========================================================================
    # 4. FLASK API ENDPOINTS TEST
    # =========================================================================

    def test_flask_risk_and_audit_endpoints(self):
        """Test Flask routes /api/risk/stress_test, /api/risk/gold_hedge, /api/system/reality_audit."""
        r_stress = self.client.get("/api/risk/stress_test?scenario=flash_crash_15")
        self.assertEqual(r_stress.status_code, 200)
        data_stress = r_stress.get_json()
        self.assertEqual(data_stress["scenario"], "flash_crash_15")

        r_hedge = self.client.get("/api/risk/gold_hedge?regime=RATE_HIKING_CYCLE&risk_score=0.6")
        self.assertEqual(r_hedge.status_code, 200)
        data_hedge = r_hedge.get_json()
        self.assertEqual(data_hedge["gold_etf_ticker"], "AZG.CA")

        r_audit = self.client.get("/api/system/reality_audit")
        self.assertEqual(r_audit.status_code, 200)
        data_audit = r_audit.get_json()
        self.assertIn("live_reality_match_score_pct", data_audit)


if __name__ == "__main__":
    unittest.main()
