import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the project root to sys.path to allow importing the backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

def test_api_health_endpoint_exists():
    try:
        from backend.main import app
        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    except ImportError:
        pytest.fail("FastAPI app 'backend.main' not found")
