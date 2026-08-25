import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_get_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_get_stations():
    response = client.get("/api/stations")
    assert response.status_code == 200
    data = response.json()
    assert "stations" in data
    assert len(data["stations"]) > 0
    first_station = data["stations"][0]
    assert "has_real_data" in first_station
    assert isinstance(first_station["has_real_data"], bool)


def test_clear_buffer():
    # Fetch station buffer first
    response = client.get("/api/station_buffer/AWS_ALPHA_MOUNTAIN")
    assert response.status_code == 200

    # Clear buffer
    clear_resp = client.post("/api/clear_buffer/AWS_ALPHA_MOUNTAIN")
    assert clear_resp.status_code == 200
    assert clear_resp.json()["status"] == "success"

    # Verify buffer is empty
    buffer_resp = client.get("/api/station_buffer/AWS_ALPHA_MOUNTAIN")
    assert buffer_resp.status_code == 200
    assert len(buffer_resp.json()["buffer"]) == 0


def test_clear_buffer_invalid_station():
    response = client.post("/api/clear_buffer/INVALID_STATION_999")
    assert response.status_code == 404


def test_llm_health_endpoint():
    response = client.get("/api/llm/health")
    assert response.status_code == 200
    data = response.json()
    assert "ok" in data
    assert "configured" in data


def test_llm_complete_unconfigured(monkeypatch):
    # Ensure GROQ_API_KEY is not configured
    monkeypatch.setenv("GROQ_API_KEY", "")
    # Reset lru cache for env file parsing if needed
    from backend.app.core import llm
    llm._env_file_values.cache_clear()

    response = client.post("/api/llm/complete", json={"prompt": "Hello"})
    # Should return 503 HTTP Exception when unconfigured
    assert response.status_code == 503
