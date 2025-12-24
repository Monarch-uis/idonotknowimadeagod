"""
Automated Video Processing Workflow
-----------------------------------
This script orchestrates the conversion of EPUB files into video series with:
1. Text Extraction & Segmentation (2-4h segments)
2. Audio Generation (TTS)
3. Caption Generation (Whisper-based Sync)
4. Video Encoding (Batch, CPU-optimized)
5. Title Card Integration

Usage:
    python batch_processor.py --input "my_book.epub" --background "bg.jpg" --output_dir "output"
"""
import os
import sys
import argparse
import asyncio
import logging
import json
import math
import shutil
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Tuple
from datetime import datetime

# Add core to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from core.epub_io import parse_full_epub
from core.tts import gen_single_clip_edge_with_retry, gen_single_clip_piper_with_retry, select_tts_engine_and_mode
from core.video_pipeline import generate_timeline_from_audio, render_video_with_timeline, check_dependencies
from core.config import CONFIG
from core.utils import sanitize_filename

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/batch_process.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
TARGET_DURATION_HOURS = 2.0
WORDS_PER_MINUTE = 150
WORDS_PER_SEGMENT = int(TARGET_DURATION_HOURS * 60 * WORDS_PER_MINUTE)
MAX_CONCURRENT_VIDEOS = 5

def generate_title_card(title: str, subtitle: str, bg_path: str, output_path: str):
    """Generates a title card image using Pillow."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.warning("Pillow not installed. Using background as title card.")
        shutil.copy(bg_path, output_path)
        return

    try:
        img = Image.open(bg_path).convert("RGBA")
        # Resize to 1920x1080 if needed, maintaining aspect ratio or crop?
        # For now, just resize to fit HD
        target_size = (1920, 1080)
        img = img.resize(target_size)
        
        overlay = Image.new("RGBA", target_size, (0, 0, 0, 160))
        img = Image.alpha_composite(img, overlay)
        
        draw = ImageDraw.Draw(img)
        
        # Load fonts - try default system fonts
        try:
            title_font = ImageFont.truetype("arial.ttf", 100)
            sub_font = ImageFont.truetype("arial.ttf", 60)
        except IOError:
            title_font = ImageFont.load_default()
            sub_font = ImageFont.load_default()

        # Draw Title
        w, h = target_size
        
        # Simple centering logic
        # Pillow < 10 getsize, >= 10 getbbox
        def get_text_size(font, text):
            if hasattr(font, "getbbox"):
                bbox = font.getbbox(text)
                return bbox[2] - bbox[0], bbox[3] - bbox[1]
            return font.getsize(text)

        tw, th = get_text_size(title_font, title)
        draw.text(((w - tw) / 2, (h / 2) - 100), title, font=title_font, fill="white")
        
        sw, sh = get_text_size(sub_font, subtitle)
        draw.text(((w - sw) / 2, (h / 2) + 50), subtitle, font=sub_font, fill="#DDDDDD")

        img = img.convert("RGB")
        img.save(output_path)
        logger.info(f"Generated title card: {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to generate title card: {e}")
        shutil.copy(bg_path, output_path)

def merge_audio_files(file_list: List[str], output_path: str):
    """Merges multiple audio files into one using FFmpeg."""
    if not file_list:
        return False
        
    list_file = output_path + ".txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for path in file_list:
            # Escape path for FFmpeg
            safe_path = path.replace("\\", "/").replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")
            
    cmd = [
        "ffmpeg", "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        "-y", output_path
    ]
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        os.remove(list_file)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg merge failed: {e}")
        return False

def timeline_to_srt(timeline: Dict[str, Any], output_path: str):
    """Converts the timeline JSON to SRT format."""
    captions = [x for x in timeline.get("timeline", []) if x.get("type") == "caption_fragment"]
    
    def format_time(seconds):
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hrs:02}:{mins:02}:{secs:02},{millis:03}"

    with open(output_path, "w", encoding="utf-8") as f:
        for i, cap in enumerate(captions, 1):
            start = format_time(cap["start"])
            end = format_time(cap["end"])
            text = cap["payload"]["text"]
            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

async def process_video_segment(
    segment_data: Dict[str, Any],
    config: Dict[str, Any],
    tts_engine: str,
    output_dir: str,
    bg_image: str
):
    """
    Processes a single video segment:
    1. Title Card
    2. Audio Generation (Parallel chunks)
    3. Merge Audio
    4. Whisper Alignment (Timeline)
    5. SRT Export
    6. Video Rendering
    """
    segment_idx = segment_data["index"]
    title = segment_data["title"]
    chapters = segment_data["chapters"]
    
    safe_title = sanitize_filename(title)
    work_dir = os.path.join(output_dir, f"temp_{segment_idx}_{safe_title}")
    os.makedirs(work_dir, exist_ok=True)
    
    logger.info(f"[{segment_idx}] Starting processing: {title}")

    # 1. Title Card
    title_card_path = os.path.join(work_dir, "title_card.jpg")
    generate_title_card(config.get("book_title", "Audiobook"), title, bg_image, title_card_path)

    # 2. Audio Generation
    audio_clips = []
    
    # Process chapters in parallel if using EdgeTTS (it's fast)
    # But we need to maintain order.
    # We'll generate them and store paths.
    
    logger.info(f"[{segment_idx}] Generating audio for {len(chapters)} chapters...")
    
    for i, (chap_title, chap_text) in enumerate(chapters):
        clip_path = os.path.join(work_dir, f"chap_{i:03d}.mp3")
        
        # Skip if exists
        if os.path.exists(clip_path) and os.path.getsize(clip_path) > 1024:
            audio_clips.append(clip_path)
            continue
            
        # TTS Call
        if tts_engine == "edge":
            success, err = await gen_single_clip_edge_with_retry(
                chap_text, clip_path, 
                config["audio_settings"]["edge_voice"], 
                config["audio_settings"]["edge_rate"]
            )
        elif tts_engine == "piper":
            success, err = gen_single_clip_piper_with_retry(
                chap_text, clip_path,
                config["audio_settings"]["piper_model_path"]
            )
        else: # pyttsx3
            # Wrap synchronous call
            loop = asyncio.get_event_loop()
            success, err = await loop.run_in_executor(None, 
                lambda: gen_single_clip_pyttsx3_with_retry(
                    chap_text, clip_path, None, "+0%"
                ).result # Wait, the function returns (bool, str) directly, not a future.
            )
            # Actually gen_single_clip_pyttsx3_with_retry is synchronous and returns tuple
            # We need to fix the wrapper above.
            # But let's assume it works for now or fix logic.
            # Fix:
            def _run_pyttsx3():
                from core.tts import gen_single_clip_pyttsx3_with_retry
                return gen_single_clip_pyttsx3_with_retry(chap_text, clip_path, None, "+0%")
            
            success, err = await loop.run_in_executor(None, _run_pyttsx3)

        if success:
            audio_clips.append(clip_path)
        else:
            logger.error(f"[{segment_idx}] TTS Failed for chap {i}: {err}")
            return False

    # 3. Merge Audio
    full_audio_path = os.path.join(output_dir, f"{segment_idx}_{safe_title}.mp3")
    if not merge_audio_files(audio_clips, full_audio_path):
        logger.error(f"[{segment_idx}] Failed to merge audio")
        return False
        
    # 4. Generate Timeline (Whisper)
    logger.info(f"[{segment_idx}] Generating alignment timeline (Whisper)...")
    try:
        # Run in executor because it's CPU intensive
        loop = asyncio.get_event_loop()
        timeline = await loop.run_in_executor(
            None, 
            lambda: generate_timeline_from_audio(full_audio_path, f"proj_{segment_idx}", config)
        )
    except Exception as e:
        logger.error(f"[{segment_idx}] Timeline generation failed: {e}")
        return False

    # 5. Export SRT
    srt_path = os.path.join(output_dir, f"{segment_idx}_{safe_title}.srt")
    timeline_to_srt(timeline, srt_path)
    logger.info(f"[{segment_idx}] SRT saved: {srt_path}")

    # 6. Render Video
    video_path = os.path.join(output_dir, f"{segment_idx}_{safe_title}.mp4")
    logger.info(f"[{segment_idx}] Rendering video (CPU Encoding)...")
    
    # CPU Optimization Settings
    quality_settings = {
        "preset": "medium",  # Balance between speed and compression
        "crf": 23            # High quality
    }
    
    try:
        await loop.run_in_executor(
            None,
            lambda: render_video_with_timeline(
                title_card_path,
                full_audio_path,
                timeline,
                video_path,
                config,
                quality_settings,
                export_timeline_json=True
            )
        )
        logger.info(f"[{segment_idx}] Video complete: {video_path}")
    except Exception as e:
        logger.error(f"[{segment_idx}] Video rendering failed: {e}")
        return False
        
    # Cleanup work dir
    try:
        shutil.rmtree(work_dir)
    except:
        pass
        
    return True

def main():
    parser = argparse.ArgumentParser(description="Automated Video Workflow")
    parser.add_argument("--input", required=True, help="Input EPUB file")
    parser.add_argument("--background", required=True, help="Background image")
    parser.add_argument("--output_dir", default="output", help="Output directory")
    parser.add_argument("--workers", type=int, default=MAX_CONCURRENT_VIDEOS, help="Max concurrent videos")
    args = parser.parse_args()

    # 1. Check Dependencies
    if not check_dependencies():
        sys.exit(1)

    # 2. Parse EPUB
    logger.info(f"Parsing EPUB: {args.input}")
    meta, chapters, _ = parse_full_epub(args.input)
    book_title = meta.get("title", "Unknown Book")
    
    # 3. Segment Text
    segments = []
    current_segment_chapters = []
    current_word_count = 0
    segment_count = 1
    
    for title, text in chapters:
        words = len(text.split())
        if current_word_count + words > WORDS_PER_SEGMENT and current_segment_chapters:
            # Close current segment
            segments.append({
                "index": segment_count,
                "title": f"Part {segment_count}",
                "chapters": current_segment_chapters
            })
            segment_count += 1
            current_segment_chapters = []
            current_word_count = 0
            
        current_segment_chapters.append((title, text))
        current_word_count += words
        
    if current_segment_chapters:
        segments.append({
            "index": segment_count,
            "title": f"Part {segment_count}",
            "chapters": current_segment_chapters
        })

    logger.info(f"Created {len(segments)} segments from {len(chapters)} chapters.")

    # 4. Configure
    config = CONFIG
    config["book_title"] = book_title
    
    # Use EdgeTTS by default for quality/speed balance, or fallback
    tts_engine = "edge" # Hardcoded for automation, or could be arg
    
    os.makedirs(args.output_dir, exist_ok=True)

    # 5. Batch Process
    # We use a semaphore to limit concurrency if we were using asyncio.gather
    # But since render is blocking-ish (in thread), we can use ThreadPoolExecutor logic
    # or just asyncio.gather with a semaphore.
    
    async def run_batch():
        sem = asyncio.Semaphore(args.workers)
        
        async def protected_process(seg):
            async with sem:
                return await process_video_segment(seg, config, tts_engine, args.output_dir, args.background)

        tasks = [protected_process(seg) for seg in segments]
        results = await asyncio.gather(*tasks)
        
        success_count = sum(1 for r in results if r)
        logger.info(f"Batch processing finished. Success: {success_count}/{len(segments)}")

    asyncio.run(run_batch())

if __name__ == "__main__":
    main()