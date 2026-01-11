import pytest
import os
from unittest.mock import patch, MagicMock

@pytest.mark.asyncio
async def test_full_gui_backend_flow():
    # We use the FastAPI TestClient for E2E-style backend testing
    from backend.main import app
    from fastapi.testclient import TestClient
    
    with TestClient(app) as client:
        # 1. Health Check
        resp = client.get("/api/health")
        assert resp.status_code == 200
        
        # 2. Get Projects (Empty)
        with patch("os.path.exists", return_value=True), patch("os.listdir", return_value=[]):
            resp = client.get("/api/projects")
            assert resp.status_code == 200
            assert resp.json()["active"] == []

        # 3. Create Project
        with patch("backend.api.projects.parse_full_epub", return_value=({'title': 'E2E Book', 'author': 'Tester'}, [], None)), \
             patch("backend.api.projects.setup_project_folders", return_value={'root': '/tmp/E2E Book', 'epub': '/tmp/E2E Book/epub'}), \
             patch("shutil.copyfileobj"), \
             patch("shutil.move"), \
             patch("builtins.open", MagicMock()), \
             patch("os.makedirs"):
            
            files = {"file": ("test.epub", b"content", "application/epub+zip")}
            resp = client.post("/api/projects", files=files)
            assert resp.status_code == 201
            assert resp.json()["title"] == "E2E Book"

        # 4. Get Logs for the new project
        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=["E2E Book"]), \
             patch("os.path.isdir", return_value=True), \
             patch("builtins.open", MagicMock(return_value=MagicMock(__enter__=lambda s: MagicMock(readlines=lambda: ["Error in E2E Book: something went wrong"])))):
            
            project_id = resp.json()["id"]
            resp = client.get(f"/api/projects/{project_id}/logs")
            assert resp.status_code == 200
            assert len(resp.json()["logs"]) > 0