import pytest
from fastapi.testclient import TestClient
import sys
import os
from unittest.mock import MagicMock, patch

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.main import app

client = TestClient(app)

def test_get_projects_empty():
    # Mock ACTIVE_NOVELS_DIR and ARCHIVED_NOVELS_DIR to be empty
    with patch("os.path.exists", return_value=True), \
         patch("os.listdir", return_value=[]):
        response = client.get("/api/projects")
        assert response.status_code == 200
        assert response.json() == {"active": [], "archived": []}

def test_get_projects_with_data():
    # Mock some folders
    def mock_listdir(path):
        if "Active" in path:
            return ["Project A"]
        if "Archived" in path:
            return ["Project B"]
        return []

    with patch("os.path.exists", return_value=True), \
         patch("os.listdir", side_effect=mock_listdir), \
         patch("os.path.isdir", return_value=True):
        response = client.get("/api/projects")
        assert response.status_code == 200
        data = response.json()
        assert "Project A" in [p["title"] for p in data["active"]]
        assert "Project B" in [p["title"] for p in data["archived"]]

def test_create_project_fail_no_file():
    response = client.post("/api/projects")
    assert response.status_code == 422 # FastAPI validation error for missing field

def test_create_project_success():
    with patch("backend.api.projects.parse_full_epub", return_value=({"title": "Test Book", "author": "Author"}, [], None)), \
         patch("backend.api.projects.setup_project_folders", return_value={"root": "/tmp/Test Book", "epub": "/tmp/Test Book/epub"}), \
         patch("shutil.copyfileobj"), \
         patch("shutil.move"), \
         patch("builtins.open", MagicMock()), \
         patch("os.makedirs"):
        
        files = {"file": ("test.epub", b"fake epub content", "application/epub+zip")}
        response = client.post("/api/projects", files=files)
        assert response.status_code == 201
        assert response.json()["title"] == "Test Book"
