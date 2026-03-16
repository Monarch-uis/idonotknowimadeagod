from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.api import projects, tts
import os

app = FastAPI(title="EPUB to Audiobook/Video Converter API")

# Configure CORS for the React frontend
allowed_origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for audio previews
os.makedirs("backend/static/previews", exist_ok=True)
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

app.include_router(projects.router)
app.include_router(tts.router)

@app.get("/api/system/options")
async def get_system_options():
    from core.config import CONFIG
    # Simplify presets for the UI
    presets = list(CONFIG["video_settings"]["quality_presets"].keys())
    
    # Static list of some popular edge-tts voices for now 
    # (In a future update, we can fetch these dynamically)
    voices = {
        "edge-tts": ["en-US-GuyNeural", "en-US-AriaNeural", "en-GB-SoniaNeural", "en-AU-ThomasNeural"],
        "piper": ["en_US-lessac-medium.onnx", "en_US-amy-medium.onnx"],
        "pyttsx3": ["default"]
    }
    
    return {
        "engines": ["edge-tts", "piper", "pyttsx3"],
        "voices": voices,
        "quality_presets": presets,
        "speeds": ["-50%", "-25%", "+0%", "+25%", "+50%", "+100%"]
    }

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
