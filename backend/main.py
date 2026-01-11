from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.api import projects, tts
import os

app = FastAPI(title="EPUB to Audiobook/Video Converter API")

# Configure CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for audio previews
os.makedirs("backend/static/previews", exist_ok=True)
app.mount("/static", StaticFiles(directory="backend/static"), name="static")

app.include_router(projects.router)
app.include_router(tts.router)

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
