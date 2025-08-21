"""Health check tests"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.text == '"OK"'


def test_root_page():
    """Test root page loads"""
    response = client.get("/")
    assert response.status_code == 200
    assert "SpecMint" in response.text