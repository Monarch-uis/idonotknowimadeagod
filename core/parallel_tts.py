"""
Parallel TTS Module
Handles multi-process generation for CPU-bound TTS engines like Piper.
"""
import os
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from typing import List, Tuple, Dict, Any, Optional

from core.config import CONFIG, logger
from core.utils import CP, censor_text, fix_pronunciation
from core.tts import gen_single_clip_piper_with_retry

def _piper_worker(args):
    """
    Standalone worker function for ProcessPoolExecutor.
    Must be top-level for pickling.
    """
    index, title, text, output_path, model_path, config = args
    
    try:
        # Pre-process text (same as in concurrently generator)
        clean_body = text.replace('"', '').replace("*", "")
        clean_body = censor_text(clean_body, config.get("banned_words", []))
        clean_body = fix_pronunciation(clean_body, config.get("pronunciation_fixes", {}))
        audio_text = f"{title}. . {clean_body} . "
        
        # Piper generation
        max_retries = config.get("audio_settings", {}).get("retry_attempts", 3)
        delay = config.get("audio_settings", {}).get("retry_delay", 1)
        
        success, error, tts_result = gen_single_clip_piper_with_retry(
            audio_text, output_path, model_path,
            max_retries=max_retries, delay=delay, silent=True
        )
        
        if success:
            return (index, title, output_path, None, tts_result.get('events', []), tts_result.get('is_high_precision', False))
        else:
            return (index, title, None, error, None, False)
            
    except Exception as e:
        return (index, title, None, str(e), None, False)

class ParallelTTSManager:
    """Manages parallel TTS generation across CPU processes"""
    
    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or max(1, multiprocessing.cpu_count() - 1)
        
    def process_piper_batch(self, chapters: List[Tuple[str, str]], temp_dir: str, model_path: str):
        """
        Process a batch of chapters using Piper TTS in parallel processes.
        Yields results as they complete: (index, title, audio_path, error, events, is_precision)
        """
        print(CP(f"   🚀 Launching {len(chapters)} parallel Piper processes (max {self.max_workers})...", 'cyan'))
        
        # Prepare arguments for workers
        prepared_args = []
        for i, (title, text) in enumerate(chapters):
            output_path = os.path.join(temp_dir, f"chap_{i}.wav")
            prepared_args.append((i, title, text, output_path, model_path, CONFIG))
            
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            from concurrent.futures import as_completed
            futures = [executor.submit(_piper_worker, args) for args in prepared_args]
            
            for future in as_completed(futures):
                yield future.result()
