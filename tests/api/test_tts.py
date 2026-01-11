import pytest
from fastapi.testclient import TestClient
import sys
import os
from unittest.mock import MagicMock, patch

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.main import app

client = TestClient(app)

def test_tts_preview_success():
    with patch("backend.api.tts.gen_single_clip_edge_with_retry", return_value=True), \
         patch("os.path.exists", return_value=True):
        
        response = client.post("/api/tts/preview", json={
            "text": "Hello world",
            "voice": "en-US-GuyNeural",
            "engine": "edge-tts",
            "speed": "+0%"
        })
        assert response.status_code == 200
        assert "audio_url" in response.json()

def test_tts_preview_missing_text():
    response = client.post("/api/tts/preview", json={
        "voice": "en-US-GuyNeural",
        "engine": "edge-tts"
    })
    assert response.status_code == 422
