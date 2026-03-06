"""Smoke tests for the health endpoint."""

from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_health_returns_ok():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
