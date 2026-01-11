"""
Whisper Aligner Module
Uses faster-whisper to generate precise word-level timestamps for subtitles.
"""
import os
import time
import logging
from typing import List, Dict, Any, Optional

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

from core.utils import CP, logger

class WhisperAligner:
    """Uses Whisper to align text with audio for perfect subtitles"""
    
    def __init__(self, model_size="base", device="cpu", compute_type="int8"):
        """
        Initialize Whisper model
        
        Args:
            model_size: Model size (tiny, base, small, medium, large-v3)
            device: cpu or cuda
            compute_type: int8, float16, etc.
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        
    def _load_model(self):
        """Lazy load model to save memory until needed"""
        global WHISPER_AVAILABLE
        if self.model is None and WHISPER_AVAILABLE:
            try:
                print(CP(f"   ⏳ Loading Whisper model ({self.model_size})...", 'cyan'))
                start = time.time()
                self.model = WhisperModel(
                    self.model_size, 
                    device=self.device, 
                    compute_type=self.compute_type
                )
                duration = time.time() - start
                print(CP(f"   ✅ Whisper loaded in {duration:.1f}s", 'green'))
            except Exception as e:
                logger.error(f"Whisper load failed: {e}")
                WHISPER_AVAILABLE = False
                
    def align(self, audio_path: str, text: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate word-level timestamps for audio
        
        Args:
            audio_path: Path to audio file
            text: Optional reference text (Whisper is good at finding it)
            
        Returns:
            List of word events: [{'start': 0.0, 'end': 0.5, 'text': 'Word'}, ...]
        """
        if not WHISPER_AVAILABLE:
            return []
            
        self._load_model()
        if self.model is None:
            return []
            
        try:
            # Transcribe with word-level timestamps
            segments, info = self.model.transcribe(
                audio_path, 
                word_timestamps=True,
                initial_prompt=text[:1000] if text else None
            )
            
            word_events = []
            for segment in segments:
                if segment.words:
                    for word in segment.words:
                        word_events.append({
                            'start': word.start,
                            'end': word.end,
                            'text': word.word.strip()
                        })
            
            return word_events
        except Exception as e:
            logger.error(f"Whisper alignment failed: {e}")
            return []

    def cleanup(self):
         """Release model from memory"""
         if self.model:
             del self.model
             self.model = None
             import gc
             gc.collect()
