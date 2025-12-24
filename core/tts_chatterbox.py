
import logging
import time
import re
from pathlib import Path
from typing import Optional, List
import os
import subprocess

# Setup logging
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MODEL = "ResembleAI/chatterbox-turbo"

class ChatterboxTTSClient:
    """
    Wrapper for Chatterbox TTS engine (Resemble AI).
    Supports partial model loading to save resources when not in use.
    """
    
    _instance = None
    _model = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ChatterboxTTSClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize client but do NOT load model yet (lazy loading)."""
        if not hasattr(self, "initialized"):
            self.initialized = True
            self.model_name = DEFAULT_MODEL
            self.model_loaded = False

    def load_model(self, model_name: str = DEFAULT_MODEL):
        """Explicitly load the model into memory."""
        if self.model_loaded and self._model:
            return

        logger.info(f"Loading Chatterbox TTS model: {model_name}...")
        try:
            # Import here to avoid heavy dependencies on startup if not used
            from chatterbox import ChatterboxTTS
            
            # Using from_pretrained as discovered during prototyping
            # It seems to take device as argument and loads default model?
            self._model = ChatterboxTTS.from_pretrained(device="cpu")
            self.model_name = model_name
            self.model_loaded = True
            logger.info("Chatterbox TTS model loaded successfully.")
        except ImportError as e:
            logger.error(f"Failed to import Chatterbox dependencies: {e}")
            raise RuntimeError("Chatterbox dependencies missing. Please install 'chatterbox-tts' and requirements.")
        except Exception as e:
            logger.error(f"Failed to load Chatterbox model: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Chatterbox model load failed: {e}")

    def generate_audio(self, text: str, output_path: str):
        """
        Generate audio from text and save to output_path.
        Supports automatic chunking for long text to avoid IndexError.
        
        Args:
            text (str): Input text
            output_path (str): Path to save the generated .wav file
        """
        if not self.model_loaded:
            self.load_model()

        # Chatterbox has a limit on input length (likely around 250-500 tokens/chars)
        # We'll use a conservative limit of 250 characters per chunk
        MAX_CHUNK_LEN = 250
        
        if len(text) <= MAX_CHUNK_LEN:
            self._generate_single_chunk(text, output_path)
        else:
            logger.info(f"Text too long ({len(text)} chars). Chunking for Chatterbox...")
            # Split text into sentences or chunks
            chunks = self._split_text(text, MAX_CHUNK_LEN)
            temp_files = []
            
            try:
                for i, chunk in enumerate(chunks):
                    temp_chunk_path = f"{output_path}_chunk_{i}.wav"
                    logger.info(f"Generating chunk {i+1}/{len(chunks)}...")
                    self._generate_single_chunk(chunk, temp_chunk_path)
                    temp_files.append(temp_chunk_path)
                
                # Merge chunks
                self._merge_audio_files(temp_files, output_path)
                logger.info(f"Successfully merged {len(temp_files)} chunks into {output_path}")
                
            finally:
                # Cleanup temp files
                for f in temp_files:
                    try:
                        os.remove(f)
                    except:
                        pass

    def _generate_single_chunk(self, text: str, output_path: str):
        """Internal helper for single generation."""
        logger.info(f"Generating Chatterbox audio for chunk: '{text[:50]}...'")
        start_time = time.time()
        
        try:
            audio = self._model.generate(text)
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            if hasattr(audio, 'save'):
                audio.save(output_path)
            else:
                import soundfile as sf
                # Handle unexpected audio formats if necessary
                pass 
            
            duration = time.time() - start_time
            logger.info(f"Chunk generation complete. Time: {duration:.2f}s")
        except Exception as e:
            logger.error(f"Chatterbox chunk generation error: {e}")
            raise

    def _split_text(self, text: str, max_len: int) -> List[str]:
        """Split text into chunks by sentences or max length."""
        # Simple splitting by sentences (punctuation followed by space)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_len:
                current_chunk += (sentence + " ")
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # If a single sentence is longer than max_len, force split it
                if len(sentence) > max_len:
                    for i in range(0, len(sentence), max_len):
                        chunks.append(sentence[i:i+max_len].strip())
                    current_chunk = ""
                else:
                    current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        return chunks

    def _merge_audio_files(self, file_list: List[str], output_path: str):
        """Merge WAV files using ffmpeg."""
        if not file_list:
            return
        
        if len(file_list) == 1:
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(file_list[0], output_path)
            return

        # Create a concat list for ffmpeg
        list_file = f"{output_path}_list.txt"
        with open(list_file, 'w', encoding='utf-8') as f:
            for file in file_list:
                # ffmpeg expects escaped paths or relative paths in the list
                abs_path = os.path.abspath(file).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")
        
        try:
            cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0', 
                '-i', list_file, '-c', 'copy', output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
        finally:
            if os.path.exists(list_file):
                os.remove(list_file)

    def warm_up(self):
        """Perform a small generation to warn up the model."""
        try:
            self.generate_audio("Test.", "temp_warmup.wav")
            Path("temp_warmup.wav").unlink(missing_ok=True)
        except Exception:
            pass
