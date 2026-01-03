"""
AI Schemas
Defines structured data models for AI analysis results.
"""
from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field

class Character(BaseModel):
    name: str
    gender: Literal["Male", "Female", "Neutral"]
    role: Literal["Protagonist", "Antagonist", "Support", "Narrator"]
    voice_preference: Optional[str] = None

class StoryAnalysis(BaseModel):
    description: str
    title_options: List[str]
    characters: List[Character]
    story_summary: str
    key_moments: List[str]
    style_guide: Optional[str] = None

class TTSSegment(BaseModel):
    text: str
    speaker: str
    gender: Literal["Male", "Female", "Neutral"]
    emotion: Optional[str] = "Normal"
    suggested_engine: Literal["piper", "edge", "chatterbox"]
    voice_id: Optional[str] = None

class TTSBatchScript(BaseModel):
    segments: List[TTSSegment]
    metadata: Optional[Dict[str, str]] = {}

class IntroData(BaseModel):
    intro_text: str
    intro_type: Literal["first", "continuation"]
    voice_recommendation: str

class AIAnalysisResult(BaseModel):
    version: str = "1.0"
    generated_at: str
    model_used: str
    epub_hash: str
    story_analysis: StoryAnalysis
    user_selections: Optional[Dict[str, str]] = {}
