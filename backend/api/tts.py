from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
import uuid
from core.tts import (
    gen_single_clip_edge_with_retry,
    gen_single_clip_pyttsx3_with_retry,
    gen_single_clip_piper_with_retry,
    resolve_piper_model_path
)

router = APIRouter(prefix="/api/tts", tags=["tts"])

class TTSPreviewRequest(BaseModel):
    text: str
    voice: str
    engine: str
    speed: Optional[str] = "+0%"

class TTSPreviewResponse(BaseModel):
    audio_url: str

@router.post("/preview", response_model=TTSPreviewResponse)
async def tts_preview(request: TTSPreviewRequest):
    preview_id = str(uuid.uuid4())
    filename = f"preview_{preview_id}.mp3"
    static_dir = "backend/static/previews"
    os.makedirs(static_dir, exist_ok=True)
    file_path = os.path.join(static_dir, filename)
    
    try:
        if request.engine == "edge-tts":
            await gen_single_clip_edge_with_retry(
                request.text, file_path, request.voice, request.speed
            )
        elif request.engine == "piper":
            # For piper, we need to resolve the model path
            model_path = resolve_piper_model_path(request.voice)
            if not model_path:
                raise HTTPException(status_code=400, detail=f"Piper model not found: {request.voice}")
            gen_single_clip_piper_with_retry(
                request.text, file_path, model_path
            )
        elif request.engine == "pyttsx3":
            # speed in pyttsx3 is an integer rate
            try:
                speed_rate = int(request.speed.replace("+", "").replace("%", ""))
                # default rate is 200, so +0% = 200
                speed_rate = 200 + (speed_rate * 2) 
            except:
                speed_rate = 200
            gen_single_clip_pyttsx3_with_retry(
                request.text, file_path, request.voice, speed_rate
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported engine: {request.engine}")
            
        if not os.path.exists(file_path):
             raise HTTPException(status_code=500, detail="TTS generation failed - file not created")
             
        return TTSPreviewResponse(audio_url=f"/static/previews/{filename}")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
