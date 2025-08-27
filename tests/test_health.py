"""Health check tests"""
from fastapi.testclient import TestClient
from app.main import app
import httpx

client = TestClient(app)


def test_health_endpoint():
    """Test health endpoint"""
    response = httpx.get("http://localhost:8080/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == "0.1.0"
    assert data["environment"] == "development"


def test_root_page():
    """Test root page loads"""
    response = client.get("/")
    assert response.status_code == 200
    assert "SpecMint" in response.text