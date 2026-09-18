import pytest
from dashboard.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_drift_and_observatory_endpoints(client):
    """Verifies that drift monitor endpoints return valid 7-dimension telemetry without 500 crashes."""
    res1 = client.get("/api/drift")
    assert res1.status_code == 200
    data1 = res1.get_json()
    assert "overall_drift_status" in data1
    assert "dimensions" in data1

    res2 = client.get("/api/observatory")
    assert res2.status_code == 200
    data2 = res2.get_json()
    assert data2["overall_drift_status"] == data1["overall_drift_status"]


def test_ai_quant_chat_endpoint(client):
    """Verifies interactive AI chat endpoint supports both GET status and POST user queries."""
    # GET status
    res_get = client.get("/api/chat")
    assert res_get.status_code == 200
    assert res_get.get_json()["status"] == "OPERATIONAL"

    # POST query
    res_post = client.post("/api/chat", json={"query": "ما هو تحليل سهم طلعت مصطفى؟"})
    assert res_post.status_code == 200
    data = res_post.get_json()
    assert data["status"] == "SUCCESS"
    assert "response" in data
    assert len(data["response"]) > 20


def test_portfolio_monte_carlo_resilience(client):
    """Verifies that invalid or non-integer query parameters are handled gracefully without 500 errors."""
    # Normal query
    r1 = client.get("/api/portfolio/monte_carlo?days=30&simulations=100")
    assert r1.status_code == 200

    # Malformed / string query parameters
    r2 = client.get("/api/portfolio/monte_carlo?days=INVALID_STRING&simulations=NOT_A_NUMBER&equity=NONE")
    assert r2.status_code == 200
    d2 = r2.get_json()
    assert "sample_paths" in d2 or "expected_mean_final_egp" in d2


def test_signals_ensemble_consensus(client):
    """Verifies that the 6-pillar ensemble decisions route executes cleanly and returns opportunities."""
    res1 = client.get("/api/signals-ensemble")
    assert res1.status_code == 200
    d1 = res1.get_json()
    assert d1["status"] == "SUCCESS"
    assert "top_opportunities" in d1

    res2 = client.get("/api/signals/ensemble")
    assert res2.status_code == 200


def test_self_improving_and_smart_money_routes(client):
    """Verifies self-learning agent and institutional radar routes are active and responsive."""
    res_status = client.get("/api/ai/self_improving/status")
    assert res_status.status_code == 200
    assert "evolution_scorecard" in res_status.get_json() or "total_evaluations" in res_status.get_json() or "status" in res_status.get_json()

    res_radar = client.get("/api/smart_money/radar")
    assert res_radar.status_code == 200
    data_radar = res_radar.get_json()
    assert "top_accumulated_stocks" in data_radar or "sentiment" in data_radar or "status" in data_radar


def test_friendly_get_on_post_endpoints(client):
    """Verifies that GET requests to actions return friendly JSON messages instead of 405 Method Not Allowed."""
    r_wl = client.get("/api/watchlist/remove")
    assert r_wl.status_code == 200
    assert "status" in r_wl.get_json()

    r_tg_conf = client.get("/api/notifications/telegram/config")
    assert r_tg_conf.status_code == 200

    r_tg_test = client.get("/api/notifications/telegram/test")
    assert r_tg_test.status_code == 200

    r_tg_scan = client.get("/api/notifications/telegram/scan")
    assert r_tg_scan.status_code == 200
