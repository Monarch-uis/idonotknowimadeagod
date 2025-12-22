import os
import sys
import asyncio
import re
import subprocess
import time
import glob
import shutil
import argparse
from datetime import datetime, timedelta
from rich.progress import (
    Progress, 
    SpinnerColumn, 
    TextColumn, 
    BarColumn, 
    TaskProgressColumn,
    TimeRemainingColumn,
    MofNCompleteColumn
)

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import (
    AudioFileClip, concatenate_audioclips, 
    ImageClip, CompositeAudioClip, CompositeVideoClip,
    TextClip, ColorClip
)


# ---------------------------
# MODULE IMPORTS (Clean architecture - no duplication)
# ---------------------------
from core.config import (
    CONFIG, DEFAULT_CONFIG,
    INPUT_ZONE, HISTORY_DIR, HISTORY_FILE, CONFIG_FILE,
    MASTER_NOVEL_DIR, ACTIVE_NOVELS_DIR, ARCHIVED_NOVELS_DIR
)
from core.utils import (
    CP, beep_notification, play_critical_failure_alarm,
    sanitize_filename, seconds_to_time_str, extract_smart_number,
    censor_text, fix_pronunciation, generate_smart_tags,
    logger
)
from core.epub_io import (
    setup_global_input, cleanup_temp_dir, setup_project_folders,
    load_history, save_to_history, check_history_conflict,
    calculate_epub_hash, check_duplicate_epub,
    load_book_profile, save_book_profile,
    clean_html_for_tts, clean_html_summary, parse_full_epub,
    extract_cover_to_project, generate_description_file, validate_epub
)
from core.tts import (
    EDGE_TTS_AVAILABLE, PYTTSX3_AVAILABLE, PIPER_AVAILABLE,
    select_tts_engine_and_mode, select_voice,
    test_edge_tts_connection, get_piper_models, select_piper_model,
    gen_single_clip_edge_with_retry,
    gen_single_clip_pyttsx3_with_retry,
    gen_single_clip_piper_with_retry,
    resolve_piper_model_path
)
from features.checkpoint_manager import CheckpointManager, save_progress_checkpoint, check_for_resume
from core import ui_manager
from features.auto_recovery import (
    AutoRecovery, try_auto_recover, ErrorCategory
)
from features.memory_manager import optimize_memory, check_memory_status
from features.queue_manager import QueueManager
from features.novel_name_mapper import auto_save_mapping
from core.subtitle_generator import generate_subtitles_for_video
from core.video_pipeline import generate_timeline_from_audio, render_video_with_timeline, check_dependencies
from core.profiler import enable_profiling, disable_profiling, get_profiler
from core.logging_config import setup_logging, get_logger
from core.path_utils import ensure_path, ensure_dir, safe_path_join, get_file_size_mb

# Legacy compatibility
UPLOADED_NOVELS_DIR = os.path.join(MASTER_NOVEL_DIR, "Uploaded in Youtube")



# ---------------------------
# LOCAL HELPERS (not duplicated - unique to main file)
# ---------------------------
def enforce_batch_size_limit(batch_size, max_batch):
    """Ensure batch size stays within configured limits"""
    if batch_size <= max_batch:
        return True

    warning_msg = f"Batch size {batch_size} exceeds recommended max ({max_batch})"
    print(CP(f"   ⚠️  {warning_msg}", 'yellow'))
    logger.warning(warning_msg)
    return False

# ---------------------------
# PROCESSING ENGINES (wrappers using imported functions)
# ---------------------------
# NOTE: All helper functions (sanitize_filename, seconds_to_time_str, extract_smart_number,
# setup_global_input, cleanup_temp_dir, setup_project_folders, load_history, save_to_history,
# check_history_conflict, calculate_epub_hash, check_duplicate_epub, load_book_profile,
# save_book_profile) are now imported from their respective modules.

# ---------------------------
# PREFLIGHT SYSTEM
# ---------------------------

    
    print("\n" + "=" * 60)
    
    if hasattr(mode, 'lower'): # Hack check if 'auto' passed via kwargs if we changed sig? No, cleaner to change sig.
         # Actually let's just use a kwarg in signature update
         pass

    # Note: caller must pass confirm_needed=False to bypass
    return True

def show_preflight_summary(meta, total_available, selected_total, batch_size, engine, voice, speed, use_concurrent, tts_delay, mode, auto_confirm=False):
    """Show preflight summary with risk tips before processing"""
    print("\n" + "=" * 60)
    print(CP("📋 PREFLIGHT SUMMARY", 'cyan'))
    print("=" * 60)
    
    print(f"\n📚 Book: {meta['title']}")
    print(f"   Chapters available: {total_available}")
    print(f"   Chapters selected: {selected_total}")
    print(f"   Mode: {'Batch' if mode == '1' else 'Manual'}")
    
    if mode == "1" and batch_size and selected_total:
        estimated_batches = (selected_total + batch_size - 1) // batch_size
        print(f"   Batch size: {batch_size} chapters")
        print(f"   Estimated batches: {estimated_batches}")
    
    print(f"\n🎤 TTS Settings:")
    print(f"   Engine: {engine.upper()}")
    print(f"   Voice: {voice}")
    print(f"   Speed: {speed}")
    print(f"   Concurrent: {'Yes' if use_concurrent else 'No'}")
    
    if engine == "edge":
        print(f"   Request delay: {tts_delay}s")
    
    # Risk tips based on configuration
    print(f"\n⚠️  Risk Assessment:")
    risks = []
    
    if engine == "edge" and use_concurrent:
        if tts_delay < 0.5:
            risks.append("   ⚠️  Low Edge-TTS delay may cause rate limit (403 errors)")
        else:
            risks.append("   ✅ Edge-TTS delay looks safe")
        
        if batch_size and batch_size > 30:
            risks.append("   ⚠️  Large batches with concurrent Edge-TTS may hit limits")
    
    if batch_size and batch_size > 50:
        limits = CONFIG.get("system_limits", {})
        max_batch = limits.get("max_batch_size", 50)
        if batch_size > max_batch:
            risks.append(f"   ⚠️  Batch size ({batch_size}) exceeds recommended max ({max_batch})")
    
    if engine == "edge" and not use_concurrent:
        risks.append("   ℹ️  Sequential Edge-TTS is slow but very safe")
    
    if not risks:
        risks.append("   ✅ Configuration looks good!")
    
    for risk in risks:
        print(risk)
    
    print("\n" + "=" * 60)
    
    if auto_confirm:
         print("\n👉 Proceeding automatically (auto-confirm enabled)...")
         return True
         
    proceed = input("\n👉 Proceed with processing? (y/n, default y): ").strip().lower()
    return proceed != 'n'

# ---------------------------
# TEMP FILE CLEANUP SYSTEM
# ---------------------------
def get_all_temp_folders():
    """Find all temp folders across projects"""
    temp_folders = []
    try:
        if not os.path.exists(ACTIVE_NOVELS_DIR):
            return temp_folders
        
        for book_folder in os.listdir(ACTIVE_NOVELS_DIR):
            book_path = os.path.join(ACTIVE_NOVELS_DIR, book_folder)
            if not os.path.isdir(book_path):
                continue
            
            temp_path = os.path.join(book_path, "temp_render_files")
            if os.path.exists(temp_path) and os.path.isdir(temp_path):
                try:
                    total_size = 0
                    file_count = 0
                    oldest_time = time.time()
                    newest_time = 0
                    
                    for root, dirs, files in os.walk(temp_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                stat = os.stat(file_path)
                                total_size += stat.st_size
                                file_count += 1
                                oldest_time = min(oldest_time, stat.st_mtime)
                                newest_time = max(newest_time, stat.st_mtime)
                            except:
                                continue
                    
                    if file_count > 0:
                        age_days = (time.time() - oldest_time) / 86400
                        size_mb = total_size / (1024 * 1024)
                        last_active_sec = time.time() - newest_time if newest_time > 0 else 999999
                        temp_folders.append({
                            'path': temp_path,
                            'book': book_folder,
                            'age_days': age_days,
                            'size_mb': size_mb,
                            'file_count': file_count,
                            'last_active_sec': last_active_sec
                        })
                except:
                    continue
    except Exception as e:
        logger.warning(f"Temp scan failed: {e}")
    
    return temp_folders

def cleanup_old_temp_files(max_age_days=7, min_size_mb=10):
    """Clean up old temp files from previous sessions"""
    print("   🧹 Scanning for old temp files...", flush=True)
    
    temp_folders = get_all_temp_folders()
    if not temp_folders:
        print("   ✅ No old temp files found", flush=True)
        return 0, 0, 0
    
    total_size_mb = sum(f['size_mb'] for f in temp_folders)
    total_files = sum(f['file_count'] for f in temp_folders)
    print(f"   📊 Found {len(temp_folders)} folders: {total_files} files ({total_size_mb:.1f} MB)", flush=True)
    
    folders_to_clean = [
        f for f in temp_folders
        if (f['age_days'] > max_age_days or f['size_mb'] > min_size_mb) and f['last_active_sec'] > 3600
    ]
    
    if not folders_to_clean:
        print(f"   ✅ All temp files recent (< {max_age_days} days)", flush=True)
        return 0, 0, 0
    
    print(f"   🗑️  Cleaning {len(folders_to_clean)} old/large folders...", flush=True)
    
    cleaned = 0
    freed = 0
    failed = 0
    
    for folder_info in folders_to_clean:
        try:
            time.sleep(0.1)
            shutil.rmtree(folder_info['path'])
            os.makedirs(folder_info['path'])
            cleaned += 1
            freed += folder_info['size_mb']
            print(f"   ✅ {folder_info['book']}: {folder_info['size_mb']:.1f} MB", flush=True)
        except:
            failed += 1
    
    if cleaned > 0:
        print(CP(f"   ✅ Freed {freed:.1f} MB from {cleaned} folders", 'green'), flush=True)
    if failed > 0:
        print(CP(f"   ⚠️  {failed} folders locked", 'yellow'), flush=True)
    
    return cleaned, freed, failed

def check_temp_space_warning(threshold_mb=1000):
    """Warn if temp space exceeds threshold"""
    temp_folders = get_all_temp_folders()
    if not temp_folders:
        return 0
    
    total_size_mb = sum(f['size_mb'] for f in temp_folders)
    if total_size_mb > threshold_mb:
        print(CP(f"\n   ⚠️  WARNING: {total_size_mb:.1f} MB temp files!", 'yellow'), flush=True)
        print(f"      Threshold: {threshold_mb} MB\n", flush=True)
    
    return total_size_mb



# ---------------------------
# TTS ENGINE SELECTION
# ---------------------------
# ---------------------------
# TTS ENGINE SELECTION & GENERATION
# Functions imported from core.tts:
# - select_tts_engine_and_mode
# - select_voice
# - test_edge_tts_connection
# - select_piper_model
# - gen_single_clip_edge_with_retry
# - gen_single_clip_pyttsx3_with_retry
# - gen_single_clip_piper_with_retry
# ---------------------------

def handle_critical_failure(section_name, error):
    """Handle critical section failure"""
    print(f"\n🚨 CRITICAL: {section_name} failed after all retries!", flush=True)
    print(f"   Error: {error}", flush=True)
    play_critical_failure_alarm()
    input("\nPress Enter to exit...")
    sys.exit(1)

# ---------------------------
# CONCURRENT AUDIO GENERATION
# ---------------------------
async def generate_chapters_concurrently(chapters, temp_dir, voice, speed_rate, max_concurrent=10):
    """Generate all chapter audio concurrently"""
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def generate_single_chapter(i, title, text):
        async with semaphore:
            try:
                # Handle file input (from Smart Merge)
                if isinstance(text, str) and text.endswith(".html") and os.path.exists(text):
                    try:
                        with open(text, "r", encoding="utf-8") as f:
                            text = f.read()
                    except Exception as e:
                        return (i, title, None, f"Read failed: {e}")

                clean_body = text.replace('"', '').replace("*", "")
                clean_body = censor_text(clean_body, CONFIG["banned_words"])
                clean_body = fix_pronunciation(clean_body, CONFIG["pronunciation_fixes"])
                audio_text = f"{title}. . {clean_body} . "
                chap_path = os.path.join(temp_dir, f"chap_{i}.mp3")
                
                max_retries = CONFIG["audio_settings"]["retry_attempts"]
                delay = CONFIG["audio_settings"]["retry_delay"]
                
                success, error, tts_result = await gen_single_clip_edge_with_retry(
                    audio_text, chap_path, voice, speed_rate,
                    max_retries=max_retries, delay=delay, silent=True
                )
                
                if success:
                    timing_data = tts_result.get('events', [])
                    is_precision = tts_result.get('is_high_precision', False)
                    return (i, title, chap_path, None, timing_data, is_precision)
                else:
                    return (i, title, None, error, None, False)
            except Exception as e:
                return (i, title, None, str(e), None, False)
    
    print(f"   🚀 Launching {len(chapters)} concurrent generations (max {max_concurrent} parallel)...", flush=True)
    
    tasks = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeRemainingColumn(),
        expand=True
    ) as progress:
        overall_task = progress.add_task("[cyan]Generating Audio...", total=len(chapters))
        
        async def generate_single_chapter_with_progress(i, title, text):
            result = await generate_single_chapter(i, title, text)
            progress.update(overall_task, advance=1)
            return result
            
        tasks = [generate_single_chapter_with_progress(i, title, text) for i, (title, text) in enumerate(chapters)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    processed = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed.append((i, chapters[i][0], None, str(result), None, False))
        else:
            processed.append(result)
    
    return processed

# ---------------------------
# AUTO-RECOVERY WRAPPER
# ---------------------------
def gen_audio_with_recovery(text, output_path, engine, voice, speed_rate, max_retries, delay, operation_name="audio"):
    """
    Generate audio with auto-recovery on failure
    
    Returns:
        (success: bool, error: str or None, engine: str, voice: str or None)
    """
    recovery_config = CONFIG.get("recovery_settings", {})
    recovery = AutoRecovery(recovery_config)
    
    # Try with current engine
    try:
        if engine == "edge":
            success, error, tts_result = asyncio.run(gen_single_clip_edge_with_retry(
                text, output_path, voice, speed_rate,
                max_retries=max_retries, delay=delay
            ))
        elif engine == "piper":
            success, error, tts_result = gen_single_clip_piper_with_retry(
                text, output_path, voice,
                max_retries=max_retries, delay=delay
            )
        else:  # pyttsx3
            success, error, tts_result = gen_single_clip_pyttsx3_with_retry(
                text, output_path, voice, speed_rate,
                max_retries=max_retries, delay=delay
            )
        
        if success:
            return True, None, engine, voice, tts_result
        
        # Failed - try auto-recovery
        print(CP(f"\n⚠️  {operation_name} generation failed with {engine}", 'yellow'))
        
        # Create exception for recovery system
        tts_error = Exception(f"TTS generation failed: {error}")
        context = {'operation': 'tts', 'engine': engine}
        
        if recovery.can_fix(tts_error, context):
            if recovery.ask_user_permission(tts_error, context):
                fallback_engine = recovery.apply_fix(tts_error, context)
                
                if fallback_engine and fallback_engine != engine:
                    print(f"\n   🔄 Retrying with {fallback_engine}...")
                    
                    # Get fallback voice
                    fallback_voice = voice
                    if fallback_engine == "piper":
                        fallback_voice = resolve_piper_model_path()
                        if not fallback_voice:
                            print(CP("   ❌ Piper fallback unavailable (model missing)", 'red'))
                            return False, "Piper fallback unavailable", engine, voice, None
                    elif fallback_engine == "pyttsx3":
                        # Use default system voice
                        import pyttsx3
                        eng = pyttsx3.init()
                        voices = eng.getProperty('voices')
                        fallback_voice = voices[0].id if voices else None
                    
                    # Retry with fallback
                    if fallback_engine == "edge":
                        success, error, tts_result = asyncio.run(gen_single_clip_edge_with_retry(
                            text, output_path, fallback_voice, speed_rate,
                            max_retries=max_retries, delay=delay
                        ))
                    elif fallback_engine == "piper":
                        success, error, tts_result = gen_single_clip_piper_with_retry(
                            text, output_path, fallback_voice,
                            max_retries=max_retries, delay=delay
                        )
                    else:
                        success, error, tts_result = gen_single_clip_pyttsx3_with_retry(
                            text, output_path, fallback_voice, speed_rate,
                            max_retries=max_retries, delay=delay
                        )
                    
                    if success:
                        print(CP(f"   ✅ Recovery successful with {fallback_engine}!", 'green'))
                        return True, None, fallback_engine, fallback_voice, tts_result
        
        return False, error, engine, voice, None
        
    except Exception as e:
        # Handle unexpected errors with recovery
        context = {'operation': 'tts', 'engine': engine}
        
        if recovery.can_fix(e, context):
            if recovery.ask_user_permission(e, context):
                fallback_engine = recovery.apply_fix(e, context)
                if fallback_engine:
                    fallback_voice = voice
                    if fallback_engine == "piper":
                        fallback_voice = resolve_piper_model_path()
                        if not fallback_voice:
                            return False, str(e), engine, voice, None
                    elif fallback_engine == "pyttsx3":
                        import pyttsx3
                        eng = pyttsx3.init()
                        voices = eng.getProperty('voices')
                        fallback_voice = voices[0].id if voices else None
                    return False, str(e), fallback_engine, fallback_voice, None  # Signal to retry
        
        return False, str(e), engine, voice, None

# ---------------------------
# AUDIO ENGINE (MAIN)
# ---------------------------
def run_audio_gen_with_timestamps(chapters, meta, final_filename, speed_rate, temp_dir, tts_engine, tts_voice, use_concurrent=False, force_align=False, whisper_model="small", whisper_threads=4):
    """Generate complete audiobook with retry logic"""
    print(f"   🎧 Generating audio ({CONFIG['audio_settings']['retry_attempts']} retries, {CONFIG['audio_settings']['retry_delay']}s delay)...", flush=True)
    
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    timestamp_list = []
    clips_to_merge = []
    current_seconds = 0.0
    failed_chapters = []
    full_word_timeline = []  # Store absolute timing for words
    
    max_retries = CONFIG["audio_settings"]["retry_attempts"]
    delay = CONFIG["audio_settings"]["retry_delay"]
    
    try:
        # === INTRO (CRITICAL) ===
        print("   🎬 Generating intro...", flush=True)
        intro_path = os.path.join(temp_dir, "00_intro.mp3")
        
        success, error, tts_engine, tts_voice, tts_result = gen_audio_with_recovery(
            CONFIG["branding"]["intro"], intro_path, tts_engine, tts_voice, 
            speed_rate, max_retries, delay, "Introduction"
        )
        
        if not success:
            handle_critical_failure("Introduction", error)
        
        clip = AudioFileClip(intro_path)
        clips_to_merge.append(clip)
        timestamp_list.append((current_seconds, "Introduction"))
        
        # Accumulate intro timing
        if tts_result and tts_result.get('events'):
            for word in tts_result['events']:
                word['start'] += current_seconds
                word['end'] += current_seconds
                full_word_timeline.append(word)
                
        current_seconds += clip.duration
        print(CP(f"   ✅ Intro: {clip.duration:.1f}s", 'green'), flush=True)
        
        # === DELAY GAP ===
        delay_gap = CONFIG["branding"].get("intro_disclaimer_delay", 0)
        if delay_gap > 0:
            print(f"   ⏸ Adding {delay_gap}s gap after intro...", flush=True)
            silence_path = os.path.join(temp_dir, "00b_silence.mp3")
            try:
                # Generate silence using ffmpeg
                subprocess.run([
                    'ffmpeg', '-y', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', 
                    '-t', str(delay_gap), '-q:a', '9', silence_path
                ], check=True, capture_output=True)
                silence_clip = AudioFileClip(silence_path)
                clips_to_merge.append(silence_clip)
                current_seconds += delay_gap
            except Exception as e:
                print(CP(f"   ⚠️ Could not add silence gap: {e}", 'yellow'), flush=True)

        # === DISCLAIMER (CRITICAL) ===
        print("   📜 Generating disclaimer...", flush=True)
        disc_text = "Disclaimer. I do not claim ownership of this story. All rights belong to the original creators. Note: I’m constantly tweaking the settings to make it as immersive as possible!"
        disc_path = os.path.join(temp_dir, "01_disclaimer.mp3")
        
        success, error, tts_engine, tts_voice, tts_result = gen_audio_with_recovery(
            disc_text, disc_path, tts_engine, tts_voice,
            speed_rate, max_retries, delay, "Disclaimer"
        )
        
        if not success:
            handle_critical_failure("Disclaimer", error)
        
        clip = AudioFileClip(disc_path)
        clips_to_merge.append(clip)
        timestamp_list.append((current_seconds, "Disclaimer"))
        
        # Accumulate disclaimer timing
        if tts_result and tts_result.get('events'):
            for word in tts_result['events']:
                word['start'] += current_seconds
                word['end'] += current_seconds
                full_word_timeline.append(word)
                
        current_seconds += clip.duration
        print(CP(f"   ✅ Disclaimer: {clip.duration:.1f}s", 'green'), flush=True)
        
        # === TITLE (CRITICAL) ===
        print("   📖 Generating title...", flush=True)
        title_text = f"{meta['title']}."
        title_path = os.path.join(temp_dir, "02_title.mp3")
        
        success, error, tts_engine, tts_voice, tts_result = gen_audio_with_recovery(
            title_text, title_path, tts_engine, tts_voice,
            speed_rate, max_retries, delay, "Title"
        )
        
        if not success:
            handle_critical_failure("Title", error)
        
        clip = AudioFileClip(title_path)
        clips_to_merge.append(clip)
        timestamp_list.append((current_seconds, "Title"))
        
        # Accumulate title timing
        if tts_result and tts_result.get('events'):
            for word in tts_result['events']:
                word['start'] += current_seconds
                word['end'] += current_seconds
                full_word_timeline.append(word)
                
        current_seconds += clip.duration
        print(CP(f"   ✅ Title: {clip.duration:.1f}s", 'green'), flush=True)
        
        # === CHAPTERS ===
        print(f"\n   📚 Processing {len(chapters)} chapters...", flush=True)
        total = len(chapters)
        
        if tts_engine == "edge" and use_concurrent:
            # CONCURRENT MODE (FAST)
            print(f"   ⚡ CONCURRENT MODE: Generating all audio in parallel...", flush=True)
            start_time = time.time()
            
            max_concurrent = CONFIG["audio_settings"]["max_concurrent_tts"]
            generation_results = asyncio.run(generate_chapters_concurrently(
                chapters, temp_dir, tts_voice, speed_rate, max_concurrent
            ))
            
            generation_time = time.time() - start_time
            print(f"   ✅ Generation complete in {generation_time:.1f}s", flush=True)
            print(f"   📊 Loading files and calculating timestamps...", flush=True)
            
            successful_count = 0
            from rich.progress import track
            for chap_index, title, audio_path, error, timing_data, is_precision in track(
                generation_results, 
                description="[yellow]Loading clips...",
                total=total
            ):
                try:
                    if error is not None:
                        raise Exception(error)
                    if not audio_path or not os.path.exists(audio_path):
                        raise Exception("Audio file missing")
                    
                    # Crossfade logic
                    xfade = 0.5 if CONFIG["audio_settings"].get("enable_audio_crossfade", True) else 0
                    if successful_count > 0:
                        current_seconds -= xfade

                    clip = AudioFileClip(audio_path)
                    timestamp_list.append((current_seconds, title))
                    
                    # Apply fades for crossfade
                    if xfade > 0:
                        if successful_count > 0:
                            clip = clip.audio_fadein(xfade)
                        # Fade out will be handled in final assembly or by overlapping
                    
                    clips_to_merge.append(clip)
                    
                    # Accumulate timing data if available
                    if timing_data:
                        for word in timing_data:
                            word['start'] += current_seconds
                            word['end'] += current_seconds
                            full_word_timeline.append(word)
                            
                    current_seconds += clip.duration
                    successful_count += 1
                
                except Exception as e:
                    failed_chapters.append({
                        'number': chap_index + 1,
                        'title': title,
                        'error': str(e)[:60]
                    })
            
            print(CP(f"\n   ✅ Loaded {successful_count}/{total} chapters", 'green'), flush=True)
            
            if successful_count > 0:
                avg_time = generation_time / total
                estimated_sequential = total * 8
                time_saved = estimated_sequential - generation_time
                print(f"   📈 {avg_time:.2f}s per chapter (concurrent)", flush=True)
                if time_saved > 0:
                    print(f"   ⚡ Saved ~{time_saved:.0f}s vs sequential", flush=True)
        
        else:
            # SEQUENTIAL MODE (SAFE)
            from rich.progress import track
            for i, (title, text) in enumerate(track(
                chapters, 
                description="[cyan]Generating Chapters...",
                total=total
            )):
                try:
                    # Handle file input (Smart Merge)
                    if isinstance(text, str) and text.endswith(".html") and os.path.exists(text):
                        with open(text, "r", encoding="utf-8") as f:
                            text = f.read()

                    clean_body = text.replace('"', '').replace("*", "")
                    clean_body = censor_text(clean_body, CONFIG["banned_words"])
                    clean_body = fix_pronunciation(clean_body, CONFIG["pronunciation_fixes"])
                    audio_text = f"{title}. . {clean_body} . "
                    chap_path = os.path.join(temp_dir, f"chap_{i}.mp3")
                    
                    if tts_engine == "edge":
                        tts_success, tts_error, tts_result = asyncio.run(gen_single_clip_edge_with_retry(
                            audio_text, chap_path, tts_voice, speed_rate,
                            max_retries=max_retries, delay=delay, silent=True
                        ))
                    elif tts_engine == "piper":
                        tts_success, tts_error, tts_result = gen_single_clip_piper_with_retry(
                            audio_text, chap_path, tts_voice,
                            max_retries=max_retries, delay=delay
                        )
                    else:
                        tts_success, tts_error, tts_result = gen_single_clip_pyttsx3_with_retry(
                            audio_text, chap_path, tts_voice, speed_rate,
                            max_retries=max_retries, delay=delay
                        )
                    
                    if not tts_success:
                        raise Exception(f"Failed after {max_retries} retries: {tts_error}")
                    
                    tts_timing = tts_result.get('events', []) if tts_result else []
                    is_precision = tts_result.get('is_high_precision', False) if tts_result else False
                    
                    # Crossfade logic
                    xfade = 0.5 if CONFIG["audio_settings"].get("enable_audio_crossfade", True) else 0
                    if i > 0:
                        current_seconds -= xfade

                    timestamp_list.append((current_seconds, title))
                    clip = AudioFileClip(chap_path)
                    
                    # Apply fades for crossfade
                    if xfade > 0:
                        if i > 0:
                            clip = clip.audio_fadein(xfade)
                    
                    clips_to_merge.append(clip)
                    
                    # Accumulate timing data if available
                    if tts_timing:
                        for word in tts_timing:
                            word['start'] += current_seconds
                            word['end'] += current_seconds
                            full_word_timeline.append(word)
                            
                    current_seconds += clip.duration
                
                except Exception as e:
                    failed_chapters.append({
                        'number': i + 1,
                        'title': title,
                        'error': str(e)[:60]
                    })
                    # Use print instead of progress.console to avoid potential context issues, track handles it
                    print(CP(f"\n   ❌ FAILED: {title} - {str(e)[:40]}", 'red'), flush=True)
        
        # === OUTRO (CRITICAL) ===
        print("\n\n   🎬 Generating outro...", flush=True)
        outro_path = os.path.join(temp_dir, "99_outro.mp3")
        
        success, error, tts_engine, tts_voice, tts_result = gen_audio_with_recovery(
            CONFIG["branding"]["outro"], outro_path, tts_engine, tts_voice,
            speed_rate, max_retries, delay, "Outro"
        )
        
        if not success:
            handle_critical_failure("Outro", error)
        
        clip = AudioFileClip(outro_path)
        clips_to_merge.append(clip)
        timestamp_list.append((current_seconds, "Outro"))
        
        # Accumulate outro timing
        if tts_result and tts_result.get('events'):
            for word in tts_result['events']:
                word['start'] += current_seconds
                word['end'] += current_seconds
                full_word_timeline.append(word)
                
        current_seconds += clip.duration
        print(CP(f"   ✅ Outro: {clip.duration:.1f}s", 'green'), flush=True)
        
        # === VALIDATION ===
        total_chapters = len(chapters)
        successful_chapters = total_chapters - len(failed_chapters)
        success_rate = successful_chapters / total_chapters if total_chapters > 0 else 1.0
        
        print(f"\n   📊 Success: {successful_chapters}/{total_chapters} ({success_rate*100:.1f}%)", flush=True)
        
        if failed_chapters:
            print(f"\n   ⚠️  {len(failed_chapters)} chapters failed:", flush=True)
            for failed in failed_chapters[:5]:
                print(f"      • Ch {failed['number']}: {failed['title'][:40]}", flush=True)
            if len(failed_chapters) > 5:
                print(f"      ... and {len(failed_chapters) - 5} more", flush=True)
        
        if success_rate < 0.90:
            print(f"\n   🚨 FAILURE: Only {success_rate*100:.1f}% (need ≥90%)", flush=True)
            play_critical_failure_alarm()
            print("\n   Failed chapters:")
            for failed in failed_chapters:
                print(f"      • Ch {failed['number']}: {failed['title']}", flush=True)
            return False, []
        
        # === FINAL ASSEMBLY ===
        if len(clips_to_merge) == 0:
            print(CP("\n   ❌ No audio clips generated", 'red'), flush=True)
            play_critical_failure_alarm()
            return False, []
        
        print(f"\n   ✅ Threshold met (≥90%)", flush=True)
        if CONFIG["audio_settings"].get("enable_audio_crossfade", True):
            xfade = 0.5
            print(f"\n   🔗 Merging {len(clips_to_merge)} clips with {xfade}s crossfades...", flush=True)
            shifted_clips = []
            curr = 0
            for i, c in enumerate(clips_to_merge):
                if i > 0: curr -= xfade
                # Ensure fade out on all but last
                if i < len(clips_to_merge) - 1:
                    c = c.audio_fadeout(xfade)
                shifted_clips.append(c.set_start(curr))
                curr += c.duration
            final_audio = CompositeAudioClip(shifted_clips)
        else:
            print(f"\n   🔗 Merging {len(clips_to_merge)} clips...", flush=True)
            final_audio = concatenate_audioclips(clips_to_merge)
            
        final_audio.write_audiofile(final_filename, fps=44100, logger=None)
        
        total_duration = sum([c.duration for c in clips_to_merge])
        print(CP(f"   ✅ Complete: {seconds_to_time_str(total_duration)}", 'green'), flush=True)
        
        # === SUBTITLE GENERATION (IMMEDIATE) ===
        # Generate subtitles immediately after audio, using the perfect timing data
        print("   📝 Generating subtitles...", flush=True)
        ass_path = final_filename.replace(".mp3", ".ass")
        
        # Determine if we need a high-precision Whisper pass
        # CRITICAL FIX: Piper/pyttsx3 only provide estimated linear timings (is_high_precision=False)
        # which results in chapter titles showing as captions instead of actual transcribed text.
        # Force Whisper pass for any non-Edge-TTS engine to get real word-level transcription.
        needs_precision_pass = False
        if force_align:
            print("      ℹ️  Force Align enabled - enforcing Whisper for accurate captions", flush=True)
            needs_precision_pass = True
        elif not full_word_timeline:
            needs_precision_pass = True
        elif tts_engine != "edge":
            # Piper and pyttsx3 return 'is_high_precision': False
            # Their estimated timings are just linear word distribution, not actual transcription
            print("      ℹ️  Non-Edge TTS detected - using Whisper for accurate captions", flush=True)
            needs_precision_pass = True

        subtitle_generated = False
        
        # NEW: Universal Perfect Timing Logic
        if needs_precision_pass:
            print(CP("   ✨ PERFECT TIMING: Enhancing captions with Whisper...", 'cyan'), flush=True)
            try:
                from core.video_pipeline import generate_timeline_from_audio
                project_id = sanitize_filename(os.path.basename(final_filename).replace(".mp3", ""))
                
                # Run Whisper on the final merged audio
                whisper_timeline = generate_timeline_from_audio(
                    final_filename,
                    project_id=project_id,
                    config=CONFIG,
                    model_size=whisper_model,
                    cpu_threads=whisper_threads
                )
                
                # Extract word events from Whisper timeline
                whisper_words = []
                for item in whisper_timeline.get("timeline", []):
                    if item.get("type") == "caption_fragment":
                        payload = item.get("payload", {})
                        if "words" in payload:
                            whisper_words.extend(payload["words"])
                        else:
                            # If no word-level data, use fragment timing
                            whisper_words.append({
                                'start': item['start'],
                                'end': item['end'],
                                'text': payload.get('text', '')
                            })
                
                if whisper_words:
                    from core.subtitle_generator import generate_ass_from_word_timeline
                    if generate_ass_from_word_timeline(whisper_words, ass_path, CONFIG):
                         print(f"      ✅ PERFECT TIMING: Subtitles enhanced and saved", flush=True)
                         subtitle_generated = True
                         full_word_timeline = whisper_words # Update for video pass
            except Exception as whisper_err:
                print(f"      ⚠️  Perfect Timing enhancement failed: {whisper_err}", flush=True)

        if not subtitle_generated and full_word_timeline:
            print("      Found word-level timing data", flush=True)
            from core.subtitle_generator import generate_ass_from_word_timeline
            if generate_ass_from_word_timeline(full_word_timeline, ass_path, CONFIG):
                 print(f"      ✅ ASS Subtitles generated: {os.path.basename(ass_path)}", flush=True)
                 subtitle_generated = True
        
        if not subtitle_generated:
            # Fallback to timestamp-based if no word data and Whisper failed
            print("      Using chapter markers as fallback subtitles", flush=True)
            from core.subtitle_generator import generate_ass_from_timestamps
            if generate_ass_from_timestamps(timestamp_list, ass_path, CONFIG):
                print(f"      ✅ ASS Subtitles generated: {os.path.basename(ass_path)}", flush=True)
        
        return True, timestamp_list, full_word_timeline
    
    except KeyboardInterrupt:
        print(CP("\n\n   ⚠️  User cancelled", 'yellow'), flush=True)
        return False, [], []
    
    except Exception as e:
        print(f"\n   ❌ Fatal error: {e}", flush=True)
        logger.error(f"Audio generation failed: {e}")
        import traceback
        traceback.print_exc()
        play_critical_failure_alarm()
        return False, timestamp_list, []
    
    finally:
        # === CLEANUP ===
        print("   🧹 Releasing audio resources...", flush=True)
        cleanup_count = 0
        for clip in clips_to_merge:
            try:
                clip.close()
                cleanup_count += 1
            except:
                pass
        if cleanup_count > 0:
            print(f"   ✅ Released {cleanup_count} clips", flush=True)
        import gc
        gc.collect()
        time.sleep(0.5)

# ---------------------------
# IMAGE & VIDEO
# ---------------------------
def prepare_custom_image(image_path, temp_folder, unique_id, target_size=None):
    """Resize image to target resolution (default 480p)"""
    try:
        W, H = target_size if target_size else (854, 480)
        with Image.open(image_path) as img:
            img = img.convert("RGB")
            img = img.resize((W, H), Image.Resampling.LANCZOS)
            temp_filename = f"temp_thumb_{unique_id}.jpg"
            temp_path = os.path.join(temp_folder, temp_filename)
            img.save(temp_path)
            return temp_path
    except Exception as e:
        logger.error(f"Image prep failed: {e}")
        return None

def generate_pro_cover_from_file(cover_path, output_folder, unique_id, book_title=None, chapter_range=None, target_size=None):
    """Generate professional thumbnail from cover with optional text overlay"""
    try:
        with Image.open(cover_path) as original:
            original = original.convert("RGB")
            
            W, H = target_size if target_size else (854, 480)
            bg_aspect = original.width / original.height
            bg_new_height = int(W / bg_aspect)
            background = original.resize((W, max(bg_new_height, H)))
            
            left = (background.width - W) / 2
            top = (background.height - H) / 2
            background = background.crop((left, top, left + W, top + H))
            background = background.filter(ImageFilter.GaussianBlur(20))
            
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 80))
            background.paste(overlay, (0, 0), overlay)
            
            target_h = int(H * 0.90)
            ratio = target_h / original.height
            target_w = int(original.width * ratio)
            sharp = original.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            x = (W - target_w) // 2
            y = (H - target_h) // 2
            shadow = Image.new('RGBA', (target_w, target_h), (0, 0, 0, 150))
            background.paste(shadow, (x + 10, y + 10), shadow)
            background.paste(sharp, (x, y))
            
            # Add text overlay if enabled and text provided
            enable_overlay = CONFIG.get("video_settings", {}).get("enable_text_overlay", True)
            if enable_overlay and book_title:
                draw = ImageDraw.Draw(background)
                
                # Try to load a nice font, fallback to default if not available
                try:
                    # Try to use a bold system font
                    font_size = CONFIG.get("video_settings", {}).get("text_overlay_font_size", 36)
                    try:
                        # Windows font path
                        font_path = "C:/Windows/Fonts/arialbd.ttf"
                        if not os.path.exists(font_path):
                            font_path = "C:/Windows/Fonts/arial.ttf"
                        if os.path.exists(font_path):
                            title_font = ImageFont.truetype(font_path, font_size)
                            range_font = ImageFont.truetype(font_path, int(font_size * 0.7))
                        else:
                            raise FileNotFoundError
                    except:
                        # Fallback to default font
                        title_font = ImageFont.load_default()
                        range_font = ImageFont.load_default()
                except:
                    title_font = ImageFont.load_default()
                    range_font = ImageFont.load_default()
                
                # Draw semi-transparent background for text
                bottom_margin = CONFIG.get("video_settings", {}).get("text_overlay_bottom_margin", 40)
                
                # Truncate title if too long
                display_title = book_title[:40] + "..." if len(book_title) > 40 else book_title
                
                # Calculate text positions
                text_padding = 15
                title_bbox = draw.textbbox((0, 0), display_title, font=title_font)
                title_width = title_bbox[2] - title_bbox[0]
                title_height = title_bbox[3] - title_bbox[1]
                
                range_width = 0
                range_height = 0
                if chapter_range:
                    range_bbox = draw.textbbox((0, 0), chapter_range, font=range_font)
                    range_width = range_bbox[2] - range_bbox[0]
                    range_height = range_bbox[3] - range_bbox[1]
                
                total_text_height = title_height + (range_height + 10 if chapter_range else 0)
                text_bg_height = total_text_height + (text_padding * 2)
                
                # Draw text background rectangle
                text_bg = Image.new('RGBA', (W, text_bg_height), (0, 0, 0, 180))
                background.paste(text_bg, (0, H - text_bg_height - bottom_margin), text_bg)
                
                # Draw title text
                title_x = (W - title_width) // 2
                title_y = H - text_bg_height - bottom_margin + text_padding
                
                # Draw text with shadow for readability
                shadow_offset = 2
                draw.text((title_x + shadow_offset, title_y + shadow_offset), display_title, 
                         fill=(0, 0, 0, 200), font=title_font)
                draw.text((title_x, title_y), display_title, 
                         fill=(255, 255, 255), font=title_font)
                
                # Draw chapter range if provided
                if chapter_range:
                    range_x = (W - range_width) // 2
                    range_y = title_y + title_height + 10
                    draw.text((range_x + shadow_offset, range_y + shadow_offset), chapter_range,
                             fill=(0, 0, 0, 200), font=range_font)
                    draw.text((range_x, range_y), chapter_range,
                             fill=(255, 255, 100), font=range_font)
        
        temp_filename = f"temp_thumb_{unique_id}.jpg"
        out_path = os.path.join(output_folder, temp_filename)
        background.convert("RGB").save(out_path)
        return out_path
            
    except Exception as e:
        logger.error(f"Thumbnail generation failed: {e}")
        return None

def create_video_with_recovery(audio_path, image_path, output_path, book_title=None, chapter_range=None, timestamps=None, word_timeline=None, max_retries=3, quality_preset=None):
    """
    Create video with auto-recovery on failure
    
    Returns:
        True if successful, False otherwise
    """
    recovery_config = CONFIG.get("recovery_settings", {})
    recovery = AutoRecovery(recovery_config)
    
    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                print(CP(f"\n🔄 Video creation retry {attempt}/{max_retries}...", 'yellow'))
            
            create_video(audio_path, image_path, output_path, book_title, chapter_range, timestamps, word_timeline, quality_preset)
            
            # Verify video was created
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                return True
            else:
                raise Exception("Video file not created or too small")
        
        except Exception as e:
            error_msg = str(e)
            
            # Check if we can recover
            if attempt < max_retries:
                context = {'operation': 'video', 'attempt': attempt}
                
                # Classify error
                if 'ffmpeg' in error_msg.lower() or 'codec' in error_msg.lower():
                    if recovery.can_fix(e, context):
                        if recovery.ask_user_permission(e, context):
                            fix_result = recovery.apply_fix(e, context)
                            if fix_result:
                                print("   → Retrying with suggested settings...")
                                continue
                
                elif 'winerror' in error_msg.lower() and '32' in error_msg:
                    # File lock - wait and retry
                    print(f"   ⏳ File locked, waiting {5 * attempt}s...")
                    time.sleep(5 * attempt)
                    continue
                
                else:
                    # Generic retry
                    print(f"   ⏳ Waiting {3 * attempt}s before retry...")
                    time.sleep(3 * attempt)
                    continue
            
            # Final attempt failed
            print(CP(f"\n❌ Video creation failed after {max_retries} attempts", 'red'))
            logger.error(f"Video creation failed: {e}")
            return False
    
    return False

def create_video(audio_path, image_path, output_path, book_title=None, chapter_range=None, timestamps=None, word_timeline=None, quality_preset=None):
    """Create video from audio + image with optional loudness normalization and chapter markers"""
    # Ensure MoviePy objects are available locally
    print(f"   🎬 Rendering: {os.path.basename(output_path)}", flush=True)
    
    # Feature 3: Image check and regeneration resilience
    if not image_path or not os.path.exists(image_path):
        print(CP(f"   ⚠️  Warning: Thumbnail missing at {image_path}", 'yellow'))
        print(f"   → Attempting to recover/regenerate...", flush=True)
        
        try:
            # Resolve book root and temp dir
            book_root = os.path.dirname(os.path.dirname(output_path))
            temp_dir = os.path.join(book_root, "temp_render_files")
            archive_dir = os.path.join(book_root, "cover_images")
            
            # 1. Search for archived thumbnail (Best match)
            recovered = False
            if chapter_range:
                archive_name = f"{sanitize_filename(chapter_range)}.jpg"
                archive_path = os.path.join(archive_dir, archive_name)
                if os.path.exists(archive_path):
                    print(CP(f"   ✅ Recovered from archive: {archive_name}", 'green'), flush=True)
                    image_path = archive_path
                    recovered = True
            
            if not recovered:
                # 2. Extract unique_id if possible for naming
                uid = 0
                if image_path:
                    match = re.search(r'temp_thumb_(\d+)', image_path)
                    if match: uid = match.group(1)
                
                # 3. Search for original cover/fallback candidates
                cover_candidates = [
                    os.path.join(book_root, "cover.jpg"),
                    os.path.join(book_root, "cover.png"),
                    os.path.join(book_root, "thumbnail.jpg"),
                    os.path.join(archive_dir, "cover.jpg"), # Older estrutura
                    os.path.join(archive_dir, "cover.png")
                ]
                
                orig_cover = None
                for c in cover_candidates:
                    if os.path.exists(c):
                        orig_cover = c
                        break
                
                if orig_cover:
                    print(f"   → Regenerating from {os.path.basename(orig_cover)}...", flush=True)
                    os.makedirs(temp_dir, exist_ok=True)
                    recovered_path = generate_pro_cover_from_file(orig_cover, temp_dir, uid, 
                                                            book_title=book_title, 
                                                            chapter_range=chapter_range)
                    if recovered_path and os.path.exists(recovered_path):
                        image_path = recovered_path
                        recovered = True
                
                if not recovered:
                    print(f"   ⚠️  No cover found, generating generic placeholder...", flush=True)
                    os.makedirs(temp_dir, exist_ok=True)
                    dummy = Image.new('RGB', (1280, 720), (30, 30, 30))
                    image_path = os.path.join(temp_dir, f"recovered_thumb_{uid}.jpg")
                    dummy.save(image_path)
                    
        except Exception as e:
            logger.error(f"Image recovery failed: {e}")
            # Ensure we have SOME image path even on error to avoid downstream crash
            if not image_path:
                 raise RuntimeError(f"Critical image missing and recovery failed: {e}")

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Critical image missing: {image_path}")

    # Resolve Quality Settings
    video_conf = CONFIG.get("video_settings", {})
    preset_name = quality_preset if quality_preset else video_conf.get("current_quality_preset", "Balanced")
    presets = video_conf.get("quality_presets", {})
    q_settings = presets.get(preset_name, presets.get("Balanced", {"height": 720, "crf": 23, "preset": "medium"}))

    crf = str(q_settings.get("crf", 23))
    # Preference: rendering_preset from config, then preset from quality settings
    enc_preset = CONFIG.get("video_settings", {}).get("rendering_preset", q_settings.get("preset", "medium"))
    # Note: Resolution is handled during image generation, but we can verify image size matches if needed

    tts_clip = None
    bg_clip = None
    final_audio = None
    video_clip = None
    normalized_audio_path = None
    render_audio_tmp = None
    advanced_render_enabled = video_conf.get("use_advanced_renderer", False)
    advanced_render_succeeded = False
    normalization_applied = False
    background_applied = False

    try:
        # Load TTS audio
        tts_clip = AudioFileClip(audio_path)
        expected_duration = tts_clip.duration
        print(f"   ⏱️  Audio: {seconds_to_time_str(expected_duration)}", flush=True)
        
        # Apply loudness normalization if enabled
        enable_normalization = CONFIG.get("audio_settings", {}).get("enable_loudness_normalization", False)
        if enable_normalization:
            print(f"   🔊 Applying loudness normalization...", flush=True)
            try:
                # Create temporary normalized audio file
                normalized_audio_path = audio_path.replace('.mp3', '_normalized.mp3')
                
                # Use ffmpeg loudnorm filter for audio normalization
                # import subprocess (Removed: using global import)
                cmd = [
                    'ffmpeg', '-i', audio_path,
                    '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
                    '-y', normalized_audio_path
                ]
                
                # Try to find ffmpeg in common locations or PATH
                ffmpeg_path = None
                try:
                    from imageio_ffmpeg import get_ffmpeg_exe
                    ffmpeg_path = get_ffmpeg_exe()
                except:
                    pass
                
                if ffmpeg_path:
                    cmd[0] = ffmpeg_path
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if os.path.exists(normalized_audio_path) and os.path.getsize(normalized_audio_path) > 1000:
                    tts_clip.close()
                    tts_clip = AudioFileClip(normalized_audio_path)
                    print(f"   ✅ Loudness normalized", flush=True)
                    normalization_applied = True
                else:
                    print(f"   ⚠️  Normalization failed, using original", flush=True)
                    if os.path.exists(normalized_audio_path):
                        os.remove(normalized_audio_path)
            except Exception as e:
                print(f"   ⚠️  Normalization error: {str(e)[:50]}, using original", flush=True)
                if normalized_audio_path and os.path.exists(normalized_audio_path):
                    try:
                        os.remove(normalized_audio_path)
                    except:
                        pass
        
        final_audio = tts_clip
        
        # Mix background music (use configured path)
        bg_music_path = CONFIG["audio_settings"].get("background_music_path", "background.mp3")
        if os.path.exists(bg_music_path):
            print(f"   🎶 Mixing background ({os.path.basename(bg_music_path)})...", flush=True)
            try:
                bg_clip = AudioFileClip(bg_music_path)
                
                if bg_clip.duration < expected_duration:
                    loop_count = int(expected_duration / bg_clip.duration) + 1
                    bg_clip = concatenate_audioclips([bg_clip] * loop_count)
                
                bg_clip = bg_clip.subclip(0, expected_duration)
                vol = CONFIG["audio_settings"]["background_volume"]
                bg_clip = bg_clip.volumex(vol)
                print(f"   🔊 Volume: {int(vol * 100)}%", flush=True)

                final_audio = CompositeAudioClip([tts_clip, bg_clip])
                final_audio.fps = 44100  # Fix: CompositeAudioClip needs explicit fps
                background_applied = True
            except Exception as e:
                print(f"   ⚠️  Background failed: {e}", flush=True)
                final_audio = tts_clip
        
        # Duration validation
        actual_duration = final_audio.duration
        duration_diff = abs(actual_duration - expected_duration)
        
        if duration_diff > 0.1:
            print(CP(f"   ⚠️  Duration mismatch!", 'yellow'), flush=True)
            print(f"      Expected: {expected_duration:.3f}s", flush=True)
            print(f"      Actual: {actual_duration:.3f}s", flush=True)
            print(f"      Diff: {duration_diff:.3f}s", flush=True)
            
            if actual_duration < expected_duration:
                print(f"   ⚠️  Composite SHORTER - possible loss!", flush=True)
            
            final_duration = actual_duration
            print(f"   ✅ Using actual: {seconds_to_time_str(final_duration)}", flush=True)
        else:
            final_duration = expected_duration
            final_audio = final_audio.set_duration(expected_duration)
            print(f"   ✅ Duration OK: {seconds_to_time_str(final_duration)}", flush=True)

        # Prepare ffmpeg parameters for MoviePy fallback
        ffmpeg_params = ['-crf', crf, '-preset', enc_preset]

        # Generate chapter file if needed (but don't inject into moviepy)
        chapter_file = None
        enable_chapters = CONFIG.get("video_settings", {}).get("enable_chapter_markers", True)
        if enable_chapters and timestamps and len(timestamps) > 0:
            print(f"   📑 Preparing {len(timestamps)} chapter markers...", flush=True)
            try:
                chapter_file = output_path.replace('.mp4', '_chapters.txt')
                with open(chapter_file, 'w', encoding='utf-8') as f:
                    for i, (timestamp, title) in enumerate(timestamps):
                        start_time = timestamp
                        end_time = timestamps[i+1][0] if i+1 < len(timestamps) else final_duration
                        # Format: [CHAPTER] TIMEBASE=1/1000 START=ms END=ms title=title
                        start_ms = int(start_time * 1000)
                        end_ms = int(end_time * 1000)
                        # Escape title for ffmpeg chapter metadata
                        safe_title = title.replace('=', '\\=').replace(';', '\\;').replace('#', '\\#')
                        f.write(f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={start_ms}\nEND={end_ms}\ntitle={safe_title}\n\n")
            except Exception as e:
                print(f"   ⚠️  Chapter prep failed: {str(e)[:50]}", flush=True)
                if chapter_file and os.path.exists(chapter_file):
                    os.remove(chapter_file)
                chapter_file = None

        # Advanced renderer path
        if advanced_render_enabled:
            try:
                # Quick health check before rendering
                # If we have word_timeline, we don't need faster-whisper!
                from features.video_diagnostics import validate_ffmpeg_subprocess
                ffmpeg_ok, ffmpeg_msg = validate_ffmpeg_subprocess()
                if not ffmpeg_ok:
                    raise RuntimeError(f"FFmpeg not ready: {ffmpeg_msg}")
                
                # Only check faster-whisper if we DON'T have word_timeline (fallback path)
                if not word_timeline or len(word_timeline) == 0:
                    from features.video_diagnostics import validate_faster_whisper
                    fw_ok, fw_msg = validate_faster_whisper()
                    if not fw_ok:
                        raise RuntimeError(f"faster-whisper not ready: {fw_msg}")
                
                render_audio_tmp = os.path.splitext(audio_path)[0] + "_render_mix.mp3"
                if os.path.exists(render_audio_tmp):
                    os.remove(render_audio_tmp)
                final_audio.write_audiofile(
                    render_audio_tmp,
                    bitrate="192k",
                    verbose=False,
                    logger=None
                )

                project_id = sanitize_filename(os.path.splitext(os.path.basename(output_path))[0])
                # Use Word Timeline from TTS if available (FASTER & MORE ACCURATE)
                if word_timeline and len(word_timeline) > 0:
                    print(f"   ⚡ Using high-precision TTS timing data for captions...", flush=True)
                    from core.video_pipeline import generate_timeline_from_words
                    timeline_data = generate_timeline_from_words(
                        render_audio_tmp,
                        project_id=project_id,
                        words=word_timeline,
                        config=CONFIG
                    )
                else:
                    # Fallback to Whisper (SLOW)
                    print(f"   🧮 Generating caption timeline ({video_conf.get('caption_model_size', 'small')})...", flush=True)
                    timeline_data = generate_timeline_from_audio(
                        render_audio_tmp,
                        project_id=project_id,
                        config=CONFIG
                    )

                print(f"   🎥 Advanced rendering via FFmpeg ({preset_name}, CRF {crf})...", flush=True)
                render_video_with_timeline(
                    image_path=image_path,
                    audio_path=render_audio_tmp,
                    timeline_data=timeline_data,
                    output_path=output_path,
                    config=CONFIG,
                    quality_settings=q_settings,
                )
                advanced_render_succeeded = True
            except RuntimeError as advanced_err:
                print(f"   ⚠️  Advanced renderer unavailable ({advanced_err}). Falling back to MoviePy.", flush=True)
                import traceback
                traceback.print_exc()
            except Exception as advanced_err:
                print(f"   ⚠️  Advanced rendering failed: {advanced_err}. Falling back to MoviePy.", flush=True)
                import traceback
                traceback.print_exc()

        # === SUBTITLE HANDLING ===
        subtitle_file = None
        # Check for pre-generated subtitles (from audio gen phase)
        ass_path = output_path.replace('.mp4', '.ass')
        srt_path = output_path.replace('.mp4', '.srt')
        
        if os.path.exists(ass_path):
            subtitle_file = ass_path
            print(f"   ✅ Found pre-generated subtitles: {os.path.basename(ass_path)}", flush=True)
        elif os.path.exists(srt_path):
            subtitle_file = srt_path
            print(f"   ✅ Found pre-generated subtitles: {os.path.basename(srt_path)}", flush=True)
            
        # Fallback: Generate from timestamps if missing and valid timestamps exist
        if not subtitle_file and not advanced_render_succeeded and timestamps and len(timestamps) > 0:
            enable_subtitles = CONFIG.get("video_settings", {}).get("enable_subtitles", True)
            if enable_subtitles:
                try:
                    print(f"   📝 Generating subtitles from TTS timing ({len(timestamps)} chapters)...", flush=True)
                    from core.subtitle_generator import generate_ass_from_timestamps
                    
                    subtitle_file = ass_path
                    success = generate_ass_from_timestamps(timestamps, subtitle_file, CONFIG)
                    
                    if success and os.path.exists(subtitle_file):
                        print(f"   ✅ Subtitles generated: {os.path.basename(subtitle_file)}", flush=True)
                    else:
                        print(f"   ⚠️  Subtitle generation failed", flush=True)
                        subtitle_file = None
                except Exception as sub_err:
                    print(f"   ⚠️  Subtitle generation error: {sub_err}", flush=True)
                    subtitle_file = None

        if not advanced_render_succeeded:
            print(f"   🎥 Encoding ({preset_name}, H.264, CRF {crf})...", flush=True)
            video_clip = ImageClip(image_path).set_duration(final_duration)
            video_clip = video_clip.set_audio(final_audio)

            # Prepare ffmpeg parameters
            ffmpeg_params_list = ffmpeg_params.copy()
            
            # Add subtitle filter if subtitle file was generated
            if subtitle_file and os.path.exists(subtitle_file):
                print(f"   🔤 Burning subtitles into video...", flush=True)
                # Windows path escaping for FFmpeg filter syntax
                subtitle_path_escaped = str(subtitle_file).replace("\\", "/").replace(":", r"\:")
                # Add subtitle filter to ffmpeg params
                ffmpeg_params_list.extend(['-vf', f"subtitles='{subtitle_path_escaped}'"])

            video_clip.write_videofile(
                output_path,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                audio_bitrate="128k",
                ffmpeg_params=ffmpeg_params_list,
                verbose=False,
                logger='bar',
                threads=4,
                preset='ultrafast'
            )
            advanced_render_succeeded = True

        if advanced_render_succeeded:
            print(CP(f"\n   ✅ Video saved!", 'green'), flush=True)
            logger.info(f"Video created: {output_path}")

        # Post-process: Add chapters if successfully generated
        if chapter_file and os.path.exists(chapter_file) and os.path.exists(output_path):
            print(f"   📑 Embedding chapters into video...", flush=True)
            try:
                temp_output = output_path.replace('.mp4', '_final.mp4')
                cmd = [
                    'ffmpeg', '-y',
                    '-i', output_path,
                    '-i', chapter_file,
                    '-map_metadata', '1',
                    '-codec', 'copy',
                    temp_output
                ]
                
                # Use system ffmpeg or imageio ffmpeg
                ffmpeg_exe = 'ffmpeg'
                try:
                    from imageio_ffmpeg import get_ffmpeg_exe
                    ffmpeg_exe = get_ffmpeg_exe()
                except:
                    pass
                cmd[0] = ffmpeg_exe
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and os.path.exists(temp_output):
                    # Replace original with new file
                    os.replace(temp_output, output_path)
                    print(f"   ✅ Chapters embedded", flush=True)
                else:
                    print(f"   ⚠️  Chapter embedding failed (ffmpeg error)", flush=True)
                    logger.warning(f"Chapter embed error: {result.stderr}")
                    if os.path.exists(temp_output):
                        os.remove(temp_output)
            except Exception as e:
                print(f"   ⚠️  Chapter embedding error: {e}", flush=True)
            finally:
                # Cleanup chapter file
                try:
                    os.remove(chapter_file)
                except:
                    pass
        
        print(CP(f"\n   ✅ Video saved!", 'green'), flush=True)
        logger.info(f"Video created: {output_path}")
    
    except OSError as e:
        if hasattr(e, 'winerror') and e.winerror == 6:
            print(f"\n   ✅ Saved (pipe error ignored)", flush=True)
        else:
            print(CP(f"\n   ❌ Video error: {e}", 'red'), flush=True)
            logger.error(f"Video creation failed: {e}")
    
    except Exception as e:
        print(CP(f"\n   ❌ Video error: {e}", 'red'), flush=True)
        logger.error(f"Video creation failed: {e}")
    
    finally:
        # Cleanup
        print("   🧹 Releasing video resources...", flush=True)
        released = []
        
        if video_clip:
            try:
                video_clip.close()
                released.append("video")
            except:
                pass
        
        if final_audio and final_audio != tts_clip:
            try:
                final_audio.close()
                released.append("composite")
            except:
                pass
        
        if bg_clip:
            try:
                bg_clip.close()
                released.append("background")
            except:
                pass
        
        if tts_clip:
            try:
                tts_clip.close()
                released.append("TTS")
            except:
                pass
        
        if released:
            print(f"   ✅ Released: {', '.join(released)}", flush=True)
        
        # Clean up normalized audio if created
        if normalized_audio_path and os.path.exists(normalized_audio_path):
            try:
                os.remove(normalized_audio_path)
            except:
                pass
        if render_audio_tmp and os.path.exists(render_audio_tmp):
            try:
                os.remove(render_audio_tmp)
            except:
                pass
        
        time.sleep(0.3)

# ---------------------------
# MAIN FLOW
# ---------------------------


def parse_cli_args():
    """Parse command-line arguments for non-interactive mode"""
    parser = argparse.ArgumentParser(
        description="EPUB to Audiobook/Video Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use saved profile, interactive for other settings:
  python epub_project_manager.py

  # Full automation:
  python epub_project_manager.py --engine piper --voice en_US-amy-medium --range 1-50 --batch-size 10

  # Override just engine and voice:
  python epub_project_manager.py --engine edge --voice en-US-JennyNeural
        """
    )
    
    parser.add_argument("--engine", choices=["edge", "pyttsx3", "piper"],
                       help="TTS engine to use (edge/pyttsx3/piper)")
    parser.add_argument("--voice", type=str,
                       help="Voice name (e.g., en-US-GuyNeural for Edge, model name for Piper)")
    parser.add_argument("--range", type=str,
                       help="Chapter range (e.g., 1-100)")
    parser.add_argument("--batch-size", type=int,
                       help="Chapters per video batch")
    parser.add_argument("--preview", action="store_true", 
                       help="Generate only first 3 chapters")
    parser.add_argument("--merge", action="store_true",
                       help="Auto-merge small chapters (<1500 words)")
    parser.add_argument("--concurrent", choices=["yes", "no"],
                       help="Use concurrent processing for Edge-TTS (yes/no)")
    parser.add_argument("--speed", type=str,
                       help="TTS speed (e.g., +0%%, +10%%)")
    parser.add_argument("--input", type=str,
                       help="Input EPUB file path or filename within input folder")
    parser.add_argument("--auto", action="store_true",
                       help="Run in fully automated mode (skip confirmations)")
    parser.add_argument("--force-align", action="store_true",
                       help="Force Whisper alignment even if TTS provides timing data")
    parser.add_argument("--whisper-model", type=str, default="small",
                       help="Whisper model size (tiny, base, small, medium, large)")
    parser.add_argument("--whisper-threads", type=int, default=4,
                       help="Number of threads for Whisper CPU inference")
    
    # Novel Name Mapper commands
    parser.add_argument("--sync", action="store_true",
                       help="Sync novel mappings from history and folders")
    parser.add_argument("--lookup", type=str, metavar="NAME",
                       help="Look up a novel by YouTube name")
    parser.add_argument("--list-mappings", action="store_true",
                       help="List all novel name mappings")
    parser.add_argument("--search-mappings", type=str, metavar="QUERY",
                       help="Search novel mappings")
    
    return parser.parse_args()

def process_batch_queue(qm):
    """Process all pending jobs in the queue"""
    jobs = qm.get_pending_jobs()
    if not jobs:
        print("\n   ⚠️  No pending jobs found.")
        return

    print(f"\n🚀 STARTING BATCH PROCESSING: {len(jobs)} Jobs")
    
    from rich.progress import track
    for i, job in enumerate(track(
        jobs, 
        description="[bold green]Batch Processing...",
        total=len(jobs)
    )):
        print(f"\n{'='*60}")
        print(f"📦 BATCH JOB {i+1}/{len(jobs)}: {job['title']}")
        print(f"{'='*60}")
        
        try:
            process_from_queue_job(job)
            qm.mark_completed(job['id'], success=True)
            print(CP(f"\n✅ JOB COMPLETED: {job['title']}", 'green'))
            
            # Optimization between jobs
            import gc
            gc.collect()
            if i < len(jobs) - 1:
                print("   ⏳ Cooldown (5s)...")
                time.sleep(5)
                
        except Exception as e:
            logger.error(f"Batch Job Failed: {e}")
            print(CP(f"\n❌ JOB FAILED: {job['title']} - {e}", 'red'))
            qm.mark_completed(job['id'], success=False)
            
    print(f"\n{CP('🎉 BATCH QUEUE COMPLETED!', 'green')}")
    beep_notification()
    input("Press Enter to continue...")

def process_from_queue_job(job):
    """Execute a single job from the queue (Non-interactive)"""
    settings = job['settings']
    epub_path = job['path']
    
    print(f"   📂 Loading: {epub_path}")
    if not os.path.exists(epub_path):
        raise FileNotFoundError(f"EPUB not found: {epub_path}")
        
    # 1. Parse EPUB
    valid, error = validate_epub(epub_path)
    if not valid:
        raise ValueError(f"Invalid EPUB: {error}")
    
    meta, all_chapters, book_obj = parse_full_epub(epub_path)
    if not all_chapters:
        raise ValueError("No chapters found in EPUB")
        
    # 2. Setup Project
    paths = setup_project_folders(meta['title'], ACTIVE_NOVELS_DIR)
    
    # 3. Execution Data
    
    # Apply Smart Merge if enabled in settings
    # This must re-run to match the indices stored in raw_batches
    if settings.get('merge'):
        print("   🔄 Applying Smart Chapter Merge (Batch)...", flush=True)
        try:
            from chapter_merger import ChapterMerger
            merger = ChapterMerger()
            # Note: We pass book_obj but the new merger ignores it and uses text content directly
            all_chapters = merger.merge_chapters(all_chapters, book_obj, paths["temp"])
        except Exception as e:
            logger.error(f"Batch merge failed: {e}")
            # Continue with unmerged chapters? Indices might be wrong.
            # Ideally we should fail, but let's try to proceed.
            print(f"   ⚠️  Merge failed: {e}. Usage of batch ranges might be incorrect.", flush=True)

    raw_batches = settings.get('raw_batches', [])
    execution_queue = []
    
    # Re-construct execution queue (Phase 1 Logic - Simplified)
    print("   ⚙️  Preparing batches...")
    for idx, (start_i, end_i) in enumerate(raw_batches):
        selected_batch = all_chapters[start_i:end_i]
        
        first_title = selected_batch[0][0]
        last_title = selected_batch[-1][0]
        real_start = extract_smart_number(first_title)
        real_end = extract_smart_number(last_title)
        
        if real_start is not None and real_end is not None:
            range_label = f"Ch {real_start}-{real_end}"
            check_start, check_end = real_start, real_end
        else:
            range_label = f"Part {start_i+1}-{end_i}"
            check_start, check_end = start_i + 1, end_i

        # Auto-Generate Cover (Default behavior for batch)
        # We always extract from EPUB or use placeholder
        
        # Resolve Quality
        batch_preset_name = settings.get("quality_preset", CONFIG["video_settings"].get("current_quality_preset", "Balanced"))
        batch_presets = CONFIG["video_settings"].get("quality_presets", {})
        batch_q_conf = batch_presets.get(batch_preset_name, batch_presets.get("Balanced", {"height": 720}))
        target_h = batch_q_conf.get("height", 720)
        # Assuming 16:9 aspect ratio standard for YouTube/Video
        target_w = int(target_h * 16 / 9)
        # Ensure even numbers
        if target_w % 2 != 0: target_w += 1
        
        img_path_for_batch = None
        extracted = extract_cover_to_project(book_obj, paths, meta['title'])
        if extracted:
            img_path_for_batch = generate_pro_cover_from_file(extracted, paths["temp"], idx, 
                                                                book_title=meta['title'], 
                                                                chapter_range=range_label,
                                                                target_size=(target_w, target_h))
        else:
            # Fallback placeholder
            placeholder = Image.new('RGB', (target_w, target_h), (20, 20, 20))
            temp = os.path.join(paths["temp"], f"placeholder_{idx}.jpg")
            placeholder.save(temp)
            img_path_for_batch = temp
            
        execution_queue.append({
            "batch": selected_batch,
            "label": range_label,
            "image": img_path_for_batch,
            "start_chk": check_start,
            "end_chk": check_end,
            "quality_preset": batch_preset_name # Pass preset to execution loop
        })
        
    # 4. Processing Phase (Phase 2 Logic)
    tts_engine = settings.get('engine', 'edge')
    tts_voice = settings.get('voice', 'en-US-ChristopherNeural')
    speed = settings.get('speed', '+0%')
    use_concurrent = settings.get('concurrent', 'yes') == "yes"
    
    # IMPORTANT: Enforce Memory Limits in Batch Mode
    from features.memory_manager import check_memory_status, optimize_memory
    
    print(f"   🚀 Processing {len(execution_queue)} videos...")
    
    for i, item in enumerate(execution_queue):
        range_name = f"{sanitize_filename(meta['title'])} ({item['label']})"
        audio_file = os.path.join(paths["audio"], f"{range_name}.mp3")
        video_file = os.path.join(paths["video"], f"{range_name}.mp4")
        
        if os.path.exists(video_file):
            print(f"      ⏭️  Skipping existing: {item['label']}")
            continue
            
        print(f"      ▶️  Generating: {item['label']}")
        
        # Audio
        # Audio
        success, timestamps, word_timeline = run_audio_gen_with_timestamps(
            item["batch"], meta, audio_file, speed, paths["temp"],
            tts_engine, tts_voice, use_concurrent
        )
        
        if not success or not os.path.exists(audio_file):
             # Try auto-recover?
             print(f"      ❌ Audio generation failed for {item['label']}")
             # In batch mode, we might want to continue to next batch or fail job
             # We'll throw exception to fail the job for now, or continue?
             # Let's fail the job to be safe
             raise RuntimeError(f"Audio generation failed for {item['label']}")

        # Video
        generate_description_file(meta, range_name, paths, timestamps, CONFIG)
        video_success = create_video_with_recovery(
            audio_file, item["image"], video_file,
            book_title=meta['title'],
            chapter_range=item['label'],
            timestamps=timestamps,
            word_timeline=word_timeline,
            max_retries=3
        )
        
        if video_success:
             # Save history
             # We need to calculate hash, simplified here
             save_to_history(meta['title'], item["start_chk"], item["end_chk"], "BATCH_Process")
             optimize_memory()
        else:
             raise RuntimeError(f"Video generation failed for {item['label']}")





def main():
    # Parse CLI arguments
    cli_args = parse_cli_args()
    
    # Handle Novel Name Mapper commands (early exit)
    from features.novel_name_mapper import (
        sync_cli, lookup_by_youtube_name_cli, 
        list_all_mappings_cli, search_mappings_cli
    )
    
    if cli_args.sync:
        sync_cli()
        return
    
    if cli_args.lookup:
        lookup_by_youtube_name_cli(cli_args.lookup)
        return
    
    if cli_args.list_mappings:
        list_all_mappings_cli()
        return
    
    if cli_args.search_mappings:
        search_mappings_cli(cli_args.search_mappings)
        return
    
    ui_manager.print_rainbow_banner()

    # Preflight Check for Dependencies
    check_dependencies()
    
    # === VIDEO RENDERER DIAGNOSTICS ===
    if CONFIG.get("video_settings", {}).get("use_advanced_renderer", False):
        from features.video_diagnostics import diagnose_advanced_renderer, auto_fix_renderer_issues
        
        print("\n🔍 VIDEO RENDERER DIAGNOSTICS")
        print("=" * 50)
        
        diagnostic_result = diagnose_advanced_renderer(CONFIG)
        
        if not diagnostic_result.healthy:
            print("\n⚠️  Video renderer issues detected. Attempting auto-recovery...")
            
            # Try to fix issues automatically
            if auto_fix_renderer_issues(diagnostic_result, CONFIG):
                print("✅ Auto-recovery successful!")
                
                # Save updated config if fixes were applied
                if diagnostic_result.fixes_applied:
                    try:
                        from core.config import save_config
                        save_config(CONFIG)
                        print("💾 Config saved with fixes")
                    except Exception as e:
                        print(f"⚠️  Could not save config: {e}")
            else:
                print("❌ Some issues could not be auto-fixed")
                print("   Advanced video rendering may not work correctly")
                print("   Falling back to basic MoviePy rendering")
        print()
    
    setup_global_input(INPUT_ZONE, MASTER_NOVEL_DIR, ACTIVE_NOVELS_DIR, ARCHIVED_NOVELS_DIR)
    
    # === STARTUP CLEANUP ===
    cleanup_config = CONFIG.get("cleanup_settings", {})
    auto_cleanup = cleanup_config.get("auto_cleanup_on_startup", True)
    
    if auto_cleanup:
        print("\n🧹 STARTUP CLEANUP")
        print("=" * 50)
        
        max_age = cleanup_config.get("max_temp_age_days", 7)
        min_size = cleanup_config.get("min_size_for_cleanup_mb", 10)
        warn_threshold = cleanup_config.get("warn_threshold_mb", 1000)
        
        cleaned, freed, failed = cleanup_old_temp_files(max_age, min_size)
        if cleaned > 0 or failed > 0:
            print(f"   📊 Summary: {cleaned} cleaned, {freed:.1f} MB freed\n", flush=True)
        
        check_temp_space_warning(warn_threshold)
    
    
    # === MAIN MENU ===
    qm = QueueManager()
    
    print("\n" + "="*50)
    print("MAIN MENU")
    print("="*50)
    print(f"{CP('[1]', 'cyan')} Process a New Book")
    print(f"{CP('[2]', 'cyan')} Manage Batch Queue ({len(qm.get_pending_jobs())})")
    print(f"{CP('[3]', 'cyan')} Resume Previous Session")
    curr_q = CONFIG["video_settings"].get("current_quality_preset", "Balanced")
    print(f"{CP('[4]', 'cyan')} Video Quality: {curr_q}")
    
    # Resume check
    resume_data = check_for_resume()
    if resume_data:
         print(f"{CP('NOTE:', 'yellow')} Checkpoint found. Select [3] to resume.")
    
    if cli_args.input:
        main_choice = "1"
        print(f"\n   ℹ️  Auto-selecting [1] via CLI")
    else:
        main_choice = input("\n👉 Select option (default 1): ").strip()
    
    if main_choice == '2':
        ui_manager.handle_queue_menu(qm, process_batch_queue)
        print("\n👇 Returning to book selection...")
    elif main_choice == '4':
        ui_manager.handle_video_quality_menu()
        print("\n👇 Returning to book selection...")
    elif main_choice == '3':
        # Resume handled by check_for_resume() logic below
        pass
        
    # === FILE SELECTION ===
    
    # Check for resume (Legacy check, but we kept it consistent)
    if resume_data and main_choice != '3':
         pass # Skip if they didn't choose resume explicitly, or handle automagically
    
    epub_files = glob.glob(os.path.join(INPUT_ZONE, "*.epub"))
    if not epub_files:
        print(f"\nℹ️  No files in '{INPUT_ZONE}'.")
        input("Press Enter to exit...")
        return
    
    print(CP(f"\n📚 Found {len(epub_files)} books:", 'cyan'))
    for i, f in enumerate(epub_files):
        print(f"   [{i+1}] {os.path.basename(f)}")
    
    
    selected_path = None
    
    # CLI Bypass for file selection
    if cli_args.input:
        # Check if full path or just filename
        if os.path.exists(cli_args.input):
             selected_path = cli_args.input
        else:
             # Check in input zone
             potential_path = os.path.join(INPUT_ZONE, cli_args.input)
             if os.path.exists(potential_path):
                 selected_path = potential_path
        
        if selected_path:
             print(f"\n   ℹ️  Auto-selected input: {os.path.basename(selected_path)}")
        else:
             print(f"\n   ❌ Input file not found: {cli_args.input}")
             return

    # Interactive selection if not set by CLI
    while not selected_path:
        try:
            choice = int(input("\n👉 Select book: "))
            if 1 <= choice <= len(epub_files):
                selected_path = epub_files[choice - 1]
                break
        except (KeyboardInterrupt, EOFError):
            print("\n⚠️  Input interrupted. Exiting.")
            sys.exit(1)
        except:
            pass
    
    # === EPUB PARSING ===
    valid, error = validate_epub(selected_path)
    if not valid:
        print(CP(f"❌ Invalid EPUB: {error}", 'red'))
        return

    meta, all_chapters, book_obj = parse_full_epub(selected_path)
    if not all_chapters:
        print(CP("❌ No chapters found.", 'red'))
        return
    
    # Phase 2: Check for duplicate EPUB
    epub_hash = calculate_epub_hash(selected_path)
    if epub_hash:
        dup_info = check_duplicate_epub(selected_path)
        if dup_info:
            print(CP(f"\n{'='*50}", 'yellow'))
            print(CP(f"⚠️  DUPLICATE EPUB DETECTED (DANGER ZONE)", 'yellow'))
            print(CP(f"{'='*50}", 'yellow'))
            print(f"   Book: {dup_info['title']}")
            print(f"   📅 Last Activity: {dup_info['date']}")
            print(f"   📑 Finished Chapters: {dup_info['start']} - {dup_info['end']}")
            print(f"   Hash: {epub_hash[:16]}...")
            print(CP(f"{'='*50}", 'yellow'))
            
            print(f"\n   [1] " + CP("Open Existing Project", 'green') + " (Continue where you left off)")
            print(f"   [2] " + CP("Full Reset", 'red') + "           (Wipe history for this book)")
            print(f"   [3] " + CP("Partial Reset", 'blue') + "        (Wipe history only for current range)")
            print(f"   [4] " + CP("Abogen / Exit", 'white'))
            
            if cli_args.auto:
                choice = '2'
                print(f"\n   ℹ️  Auto-selecting [2] Full Reset via CLI")
            else:
                choice = input(f"\n   {CP('👉 Select (1-4):', 'cyan')} ").strip()
            
            if choice == '1':
                duplicate_key = dup_info['key']
                duplicate_title = dup_info['title']
                existing_path = os.path.join(ACTIVE_NOVELS_DIR, duplicate_key)
                if os.path.exists(existing_path):
                    print(CP(f"\n   ✅ Switching context to existing project...", 'green'))
                    meta['title'] = duplicate_title
                else:
                    print(CP(f"\n   ℹ️  Existing project folder not found. Creating new instance.", 'yellow'))
                    meta['title'] = f"{meta['title']} (Resumed)"
            elif choice == '2':
                if cli_args.auto:
                    confirm = 'y'
                else:
                    confirm = input(f"\n   {CP('⚠️  REALLY WIPE ALL HISTORY?', 'red')} (y/n): ").strip().lower()
                if confirm == 'y':
                    from core.epub_io import delete_book_from_history
                    success, count = delete_book_from_history(selected_path, chapters=None)
                    if success:
                        print(CP(f"   ✅ History Purged: {count} entries removed.", 'green'))
                        
                        if cli_args.auto:
                            wipe_folder = 'y'
                        else:
                            wipe_folder = input(f"   {CP('🗑️  Also delete existing project files?', 'yellow')} (y/n): ").strip().lower()
                        if wipe_folder == 'y':
                            dup_path = os.path.join(ACTIVE_NOVELS_DIR, dup_info['key'])
                            if os.path.exists(dup_path):
                                try:
                                    shutil.rmtree(dup_path)
                                    print(CP("   ✅ Project folder deleted.", 'green'))
                                except Exception as e:
                                    print(CP(f"   ❌ Folder deletion failed: {e}", 'red'))
                    else:
                        print(CP("   ❌ History reset failed or no entries found.", 'red'))
            elif choice == '3':
                print(f"\n   ℹ️  Partial reset will trigger based on the ranges you select next.")
                meta['_partial_reset_pending'] = True
            else:
                print(CP("\n   👋 Exiting.", 'white'))
                return
    
    original_epub_title = meta['title']  # Save original for mapping
    print(CP(f"\n📘 Title: {meta['title']}", 'cyan'))
    
    new_title = ""
    if not cli_args.auto:
        new_title = input("   Press Enter to keep, or type new name: ").strip()
        
    if new_title:
        # Check for duplicates before accepting the new title
        from features.novel_name_mapper import check_duplicate_interactive
        final_title = check_duplicate_interactive(original_epub_title, new_title)
        meta['title'] = final_title
    else:
        final_title = meta['title']
    
    print(CP("\n🏗️  Initializing project...", 'cyan'))
    book_title = meta['title']
    paths = setup_project_folders(book_title, ACTIVE_NOVELS_DIR)
    
    # Auto-save novel name mapping if user renamed it
    if new_title and final_title != original_epub_title:
        auto_save_mapping(
            original_title=original_epub_title,
            youtube_name=final_title,
            project_path=paths["root"]
        )
    
    # Phase 2: Load book profile if it exists
    book_profile = load_book_profile(paths["root"])
    if book_profile:
        print(CP("\n💾 Loaded saved settings from book_profile.json", 'cyan'))
        print(f"   Engine: {book_profile.get('engine', 'N/A')}")
        print(f"   Voice: {book_profile.get('voice', 'N/A')}")
        print(f"   Speed: {book_profile.get('speed', 'N/A')}")
        
        use_profile = 'y'
        if not cli_args.auto:
             use_profile = input("\n   Use saved settings? (y/n, default y): ").strip().lower()
             
        if use_profile != 'n':
            cli_args.engine = cli_args.engine or book_profile.get('engine')
            cli_args.voice = cli_args.voice or book_profile.get('voice')
            cli_args.speed = cli_args.speed or book_profile.get('speed')
            cli_args.concurrent = cli_args.concurrent or ("yes" if book_profile.get('concurrent') else "no")
    
    final_epub_path = os.path.join(paths["epub"], os.path.basename(selected_path))
    if not os.path.exists(final_epub_path):
        shutil.copy2(selected_path, final_epub_path)
    
    # Feature 6: Smart Chapter Merging
    # We do this before Overview so user sees the merged structure
    if cli_args.merge:
        print(CP("\n🧩 Smart Merging enabled...", 'cyan'))
        from features.chapter_merger import ChapterMerger
        # Default 1500 words to ensure decent chapter length
        merger = ChapterMerger(1500)
        # Process
        count_before = len(all_chapters)
        all_chapters = merger.merge_chapters(all_chapters, book_obj, paths["temp"])
        if len(all_chapters) < count_before:
             print(f"   Structure optimized: {count_before} -> {len(all_chapters)} chapters")
             # Reload gap detection or re-verify? 
             # Merging might fix gaps or create weirdness, but usually fine.
    
    # === CHAPTER OVERVIEW ===
    print(f"\n{'=' * 50}")
    print(f"TOTAL CHAPTERS: {len(all_chapters)}")
    print(f"{'=' * 50}")
    print("First 30:")
    for i in range(min(30, len(all_chapters))):
        title = all_chapters[i][0]
        num = extract_smart_number(title)
        if num is not None:
            print(f"   [{i+1:3}] → Ch {num:4} | {title[:50]}")
        else:
            print(f"   [{i+1:3}] → {'':10} | {title[:60]}")
    
    if len(all_chapters) > 60:
        print("   ...")
        print("Last 30:")
        for i in range(max(len(all_chapters) - 30, 0), len(all_chapters)):
            title = all_chapters[i][0]
            num = extract_smart_number(title)
            if num is not None:
                print(f"   [{i+1:3}] → Ch {num:4} | {title[:50]}")
            else:
                print(f"   [{i+1:3}] → {'':10} | {title[:60]}")
    
    # Gap detection
    nums = [extract_smart_number(t[0]) for t in all_chapters if extract_smart_number(t[0]) is not None]
    if len(nums) > 1:
        gaps = []
        for i in range(len(nums) - 1):
            if nums[i + 1] - nums[i] > 1:
                gaps.append(f"{nums[i]+1}-{nums[i+1]-1}")
        if gaps:
            print(CP(f"\n⚠️  WARNING: Missing chapters: {', '.join(gaps)}", 'yellow'))
            print("   → Consider smaller batch sizes\n")
    
    print(f"{'=' * 50}\n")
    
    # === BATCH CREATION ===
    raw_batches = []
    batch_size = None
    selected_total = 0

    # === MODE SELECTION ===
    print("⚙️  Mode: [1] Batch All  [2] Manual Ranges  [3] Quick Preview")
    
    if cli_args.preview:
        mode = "3"
        print("   ℹ️  Preview Mode enabled via CLI")
    elif cli_args.range:
        mode = "2" # Implied manual range
        print("   ℹ️  Manual range enabled via CLI")
    elif cli_args.batch_size:
        mode = "1" # Implied batch
        print("   ℹ️  Batch mode enabled via CLI")
    else:
        if cli_args.auto:
            mode = "1" # Default to Batch All in auto mode
            print(f"   ℹ️  Auto-selecting Mode [1] via CLI")
        else:
            mode = input("   👉 Select: ").strip()

    
    if mode == "3":
        # Preview Mode Configuration
        start_chapter = 1
        end_chapter = min(3, len(all_chapters))
        batch_size = 3
        print(f"   ⚡ PREVIEW MODE: Setup chapters {start_chapter}-{end_chapter}")
        
        # Override raw_batches logic
        start_idx = 0
        end_idx = end_chapter
        raw_batches.append((start_idx, end_idx))
        selected_total = end_idx - start_idx
        
        # Skip batch sizing logic below...
        # We need to jump over the standard selection block
        # Skip batch sizing logic below...
        # We need to jump over the standard selection block
        # The simplest way is to handle mode 3 separately
        pass
        
    # Initialize default speed
    speed = "+0%"
    if cli_args.speed:
        speed = cli_args.speed
        print(f"\n⚡ Speed: {speed} (from CLI)")
    else:
        if cli_args.auto:
             spd = "" # Use default +0% in auto mode if not specified
        else:
             spd = input(f"\n⚡ Speed (default {speed}): ").strip()
        
        if spd:
            if not spd.startswith(("+", "-")):
                spd = "+" + spd
            speed = spd if "%" in spd else f"{spd}%"
    
    # === TTS ENGINE ===
    if cli_args.engine:
        # Use CLI argument
        tts_engine = cli_args.engine
        if cli_args.concurrent:
            use_concurrent = cli_args.concurrent.lower() == "yes"
        else:
            # Default behavior based on engine
            use_concurrent = (tts_engine == "edge" and not cli_args.concurrent)
        
        print(f"\n🎤 TTS Engine: {tts_engine.upper()} (from CLI)")
        if tts_engine == "edge" and use_concurrent:
            print("   Concurrent mode: Yes")
    else:
        tts_engine, use_concurrent = select_tts_engine_and_mode()
        
    # VALIDATE ENGINE AVAILABILITY
    from core.tts import EDGE_TTS_AVAILABLE, PYTTSX3_AVAILABLE, PIPER_AVAILABLE
    if tts_engine == "edge" and not EDGE_TTS_AVAILABLE:
        print(CP("\n❌ Error: Edge-TTS selected but not available (missing library or connection).", 'red'))
        print("   Run: pip install edge-tts")
        sys.exit(1)
    if tts_engine == "pyttsx3" and not PYTTSX3_AVAILABLE:
        print(CP("\n❌ Error: pyttsx3 selected but not available.", 'red'))
        sys.exit(1)
    if tts_engine == "piper" and not PIPER_AVAILABLE:
        print(CP("\n❌ Error: Piper selected but not available.", 'red'))
        sys.exit(1)

    
    # === TTS VOICE ===
    if cli_args.voice:
        tts_voice = cli_args.voice
        print(f"\n🔊 Voice: {tts_voice} (from CLI)")
        # Validate voice for engine
        if tts_engine == "piper":
            # Normalize path separators (Windows backslash to forward slash)
            tts_voice = tts_voice.replace('\\', '/')
            
            # Check if it's already a full path
            if os.path.exists(tts_voice):
                found = True
                print(f"   ✅ Found model at: {tts_voice}")
            # Check if it ends with .onnx (model name provided)
            elif tts_voice.endswith('.onnx'):
                # Try to find it in standard locations
                model_paths = ["./piper_models", os.path.expanduser("~/.local/share/piper/models")]
                found = False
                for base_path in model_paths:
                    full_path = os.path.join(base_path, tts_voice)
                    if os.path.exists(full_path):
                        tts_voice = full_path
                        found = True
                        print(f"   ✅ Found model: {tts_voice}")
                        break
                if not found:
                    print(CP(f"   ⚠️  Warning: Piper model '{tts_voice}' not found, may fail", 'yellow'))
            else:
                # Assume it's a model name without extension
                model_paths = ["./piper_models", os.path.expanduser("~/.local/share/piper/models")]
                found = False
                for base_path in model_paths:
                    full_path = os.path.join(base_path, f"{tts_voice}.onnx")
                    if os.path.exists(full_path):
                        tts_voice = full_path
                        found = True
                        print(f"   ✅ Found model: {tts_voice}")
                        break
                if not found:
                    print(CP(f"   ⚠️  Warning: Piper model '{tts_voice}' not found, may fail", 'yellow'))
    else:
        tts_voice = select_voice(tts_engine)
    
    # === CONNECTION TEST ===
    if tts_engine == "edge":
        if not asyncio.run(test_edge_tts_connection()):
            proceed = input("\n   ⚠️  Edge-TTS test failed. Continue anyway? (y/n): ").strip().lower()
            if proceed != 'y':
                print("   Exiting...")
                return
    
    # Phase 2: Get TTS delay for preflight
    tts_delay = CONFIG["audio_settings"].get("edge_tts_request_delay", 0.8) if tts_engine == "edge" else 0
    
    # === BATCH CREATION (Initialized above) ===
    
    if mode == "3":
        # Preview Mode Logic
        start_idx = 0
        end_idx = min(3, len(all_chapters))
        raw_batches.append((start_idx, end_idx))
        selected_total = end_idx - start_idx
        batch_size = 3
        print(f"   ⚡ PREVIEW MODE: Selected Ch 1-{end_idx} (Single Batch)")
        
    elif mode == "1":
        # Ask for chapter range first
        print(f"\n📊 Total chapters available: 1-{len(all_chapters)}")
        
        start_chapter = 1
        end_chapter = len(all_chapters)
        
        # Phase 2: Check CLI args for range
        if cli_args.range:
            range_input = cli_args.range
            print(f"\n   📍 Range: {range_input} (from CLI)")
        else:
            range_input = input(f"\n   📍 Enter range (e.g. 1-100) or press Enter for all: ").strip()
        
        if range_input:
            try:
                if "-" in range_input:
                    parts = range_input.split("-")
                    start_chapter = int(parts[0].strip())
                    end_chapter = int(parts[1].strip())
                    
                    # Validate range
                    if start_chapter < 1:
                        start_chapter = 1
                    if end_chapter > len(all_chapters):
                        end_chapter = len(all_chapters)
                    if start_chapter > end_chapter:
                        print("   ⚠️  Invalid range, using all chapters")
                        start_chapter = 1
                        end_chapter = len(all_chapters)
            except:
                print("   ⚠️  Invalid format, using all chapters")
        
        # Convert to 0-indexed
        start_idx = start_chapter - 1
        end_idx = end_chapter
        
        selected_chapters = all_chapters[start_idx:end_idx]
        print(f"   ✅ Selected: Chapter {start_chapter} to {end_chapter} ({len(selected_chapters)} chapters)")
        
        # Now ask for batch size
        if cli_args.batch_size:
            batch_size = cli_args.batch_size
            print(f"\n   🔢 Chapters per video: {batch_size} (from CLI)")
            # Phase 1: Enforce system limits
            limits = CONFIG.get("system_limits", {})
            max_batch = limits.get("max_batch_size", 50)
            if not enforce_batch_size_limit(batch_size, max_batch):
                print("   Batch size too large, please adjust")
                return
        else:
            while True:
                try:
                    batch_size = int(input(f"\n   🔢 Chapters per video: "))
                    if batch_size > 0:
                        # Phase 1: Enforce system limits
                        limits = CONFIG.get("system_limits", {})
                        max_batch = limits.get("max_batch_size", 50)
                        if not enforce_batch_size_limit(batch_size, max_batch):
                            print("   Please enter a smaller batch size")
                            continue
                        break
                except:
                    pass
        
        # Create batches from selected range
        selected_total = len(selected_chapters)
        for i in range(0, len(selected_chapters), batch_size):
            actual_start_idx = start_idx + i
            actual_end_idx = start_idx + min(i + batch_size, len(selected_chapters))
            raw_batches.append((actual_start_idx, actual_end_idx))
    else:
        print("\n📝 Manual Selection")
        if cli_args.auto and cli_args.range:
            # Handle range automatically in manual mode if specified via CLI
            try:
                if "-" in cli_args.range:
                    parts = cli_args.range.split("-")
                    s_idx = int(parts[0].strip()) - 1
                    e_idx = int(parts[1].strip())
                    if 0 <= s_idx < e_idx <= len(all_chapters):
                        raw_batches.append((s_idx, e_idx))
                        selected_total += (e_idx - s_idx)
                        print(f"   ✅ Auto-selected range: {cli_args.range}")
            except Exception as e:
                print(f"   ⚠️  Failed to auto-parse range: {e}")
        
        while not raw_batches:
            try:
                s_in = input(f"   ▶️  Start (1-{len(all_chapters)}): ").strip()
                if not s_in:
                    break
                s_idx = int(s_in) - 1
                e_in = input(f"   ⏹️  Stop ({s_idx+1}-{len(all_chapters)}): ").strip()
                if not e_in:
                    break
                e_idx = int(e_in)
                if 0 <= s_idx < e_idx <= len(all_chapters):
                    raw_batches.append((s_idx, e_idx))
                    selected_total += (e_idx - s_idx)
                    more = input("      ➕ Another? (y/n): ").strip().lower()
                    if more != 'y':
                        break
            except (KeyboardInterrupt, EOFError):
                print("\n⚠️  Input interrupted. Exiting.")
                sys.exit(1)
            except:
                pass
    
    # Phase 2: Show preflight summary before processing
    if not show_preflight_summary(meta, len(all_chapters), selected_total, batch_size if mode == "1" else None, 
                                   tts_engine, tts_voice, speed, use_concurrent, tts_delay, mode, auto_confirm=cli_args.auto):
        print("\n   Processing cancelled by user.")
        return
    
    # Phase 2: Save book profile after user confirms settings
    save_book_profile(paths["root"], tts_engine, tts_voice, speed, use_concurrent)
    
    # === QUEUE OR PROCESS? ===
    print("\n" + "=" * 50)
    print("🚀 READY TO START")
    print("=" * 50)
    print(f"   Book: {meta['title']}")
    print(f"   Chapters: {selected_total} (in {len(raw_batches) if 'raw_batches' in locals() else 'N/A'} batches)")
    print(f"   Settings: {tts_engine} ({tts_voice}) @ {speed}")
    print("-" * 50)
    
    if cli_args.auto:
        q_choice = 'P'
        print(f"\n   ℹ️  Auto-selecting [P] via CLI")
    else:
        q_choice = input(f"   [P] Process Now  [Q] Add to Batch Queue: ").strip().upper()
    
    if q_choice == 'Q':
        settings = {
            "engine": tts_engine,
            "voice": tts_voice,
            "speed": speed,
            "concurrent": use_concurrent,
            "mode": mode,
            "batch_size": batch_size if mode == "1" else None,
            "raw_batches": raw_batches # Saving specific batches for manual mode support
        }
        qm = QueueManager()
        qm.add_to_queue(selected_path, settings)
        print(CP(f"\n✅ Added to queue! ({len(qm.get_pending_jobs())} jobs pending)", 'green'))
        print("   Returning to main menu...")
        return # Or main() to loop if we wrapped it
        
    # === PHASE 1: THUMBNAIL CONFIGURATION ===
    print("\n" + "=" * 50)
    print("🎨 PHASE 1: THUMBNAIL CONFIGURATION")
    print("=" * 50)
    
    execution_queue = []
    last_img_path = None
    
    for idx, (start_i, end_i) in enumerate(raw_batches):
        selected_batch = all_chapters[start_i:end_i]
        
        first_title = selected_batch[0][0]
        last_title = selected_batch[-1][0]
        real_start = extract_smart_number(first_title)
        real_end = extract_smart_number(last_title)
        
        if real_start is not None and real_end is not None:
            range_label = f"Ch {real_start}-{real_end}"
            check_start, check_end = real_start, real_end
        else:
            range_label = f"Part {start_i+1}-{end_i}"
            check_start, check_end = start_i + 1, end_i
        
        conflict, msg = check_history_conflict(meta['title'], check_start, check_end)
        if conflict:
            if meta.get('_partial_reset_pending'):
                print(CP(f"   🔄 Partial Reset: Clearing existing history for {range_label}...", 'blue'))
                from core.epub_io import delete_book_from_history
                success, count = delete_book_from_history(selected_path, chapters=(check_start, check_end))
                if success:
                    print(CP(f"   ✅ Cleared {count} overlapping entries.", 'green'))
                    # Continue as if no conflict
                else:
                    print(CP(f"   ⚠️  Partial reset failed, keeping conflict safety.", 'yellow'))
                    if mode != "2": 
                        print(f"   Skipping {range_label}")
                        continue
            elif conflict == "boundary":
                # Single chapter boundary overlap - warn but allow
                print(CP(f"⚠️  Boundary overlap: {range_label} ({msg})", 'yellow'))
                print("   ℹ️  This range shares 1 chapter with a previous batch.")
                if mode == "2":
                    proceed = input("   Proceed anyway? (y/n): ").strip().lower()
                    if proceed != 'y':
                        print(f"   Skipping {range_label}")
                        continue
                else:
                    # In batch mode, allow boundary overlaps automatically
                    print("   ✅ Allowing boundary overlap (batch mode)")
            else:
                # Significant overlap - block it
                print(CP(f"⚠️  Conflict: {range_label} ({msg})", 'red'))
                if mode == "2":
                    proceed = input("   Proceed anyway? (y/n): ").strip().lower()
                    if proceed != 'y':
                        print(f"   Skipping {range_label}")
                        continue
                else:
                    print(f"   Skipping {range_label} (use manual mode to override)")
                    continue
        
        print(f"\n[{idx+1}/{len(raw_batches)}] Setup: {range_label}")
        print("   🖼️  Drag image (or Enter for previous):")
        
        custom_img = ""
        if not cli_args.auto:
             custom_img = input("   👉 ").strip().replace('"', '').replace("'", "")
        
        img_path_for_batch = None
        if custom_img == "" and last_img_path:
            print("   ↳ Using previous")
            img_path_for_batch = last_img_path
        elif custom_img and os.path.exists(custom_img):
            print("   ↳ Processing new image...")
            img_path_for_batch = prepare_custom_image(custom_img, paths["temp"], idx)
            last_img_path = img_path_for_batch
        else:
            print("   ↳ Using EPUB cover")
            print("   ↳ Using EPUB cover")
            extracted = extract_cover_to_project(book_obj, paths, meta['title'])
            if extracted:
                # Resolve Quality for Manual Mode Pre-setup (Phase 1)
                # This uses the current setting for manual setup
                curr_q = CONFIG["video_settings"].get("current_quality_preset", "Balanced")
                presets = CONFIG["video_settings"].get("quality_presets", {})
                q_conf = presets.get(curr_q, presets.get("Balanced", {"height": 720}))
                target_h = q_conf.get("height", 720)
                target_w = int(target_h * 16 / 9)
                if target_w % 2 != 0: target_w += 1
                
                img_path_for_batch = generate_pro_cover_from_file(extracted, paths["temp"], idx, 
                                                                   book_title=meta['title'], 
                                                                   chapter_range=range_label,
                                                                   target_size=(target_w, target_h))
            else:
                img_path_for_batch = None # Fallback logic below handles placeholder
                
            if not img_path_for_batch:
                # Resolve quality for fallback
                curr_q = CONFIG["video_settings"].get("current_quality_preset", "Balanced")
                presets = CONFIG["video_settings"].get("quality_presets", {})
                q_conf = presets.get(curr_q, presets.get("Balanced", {"height": 720}))
                target_h = q_conf.get("height", 720)
                target_w = int(target_h * 16 / 9)
                if target_w % 2 != 0: target_w += 1
                
                placeholder = Image.new('RGB', (target_w, target_h), (20, 20, 20))
                temp = os.path.join(paths["temp"], f"placeholder_{idx}.jpg")
                placeholder.save(temp)
                img_path_for_batch = temp
            last_img_path = img_path_for_batch
        
        if img_path_for_batch and os.path.exists(img_path_for_batch):
            archive_name = f"{sanitize_filename(range_label)}.jpg"
            archive_path = os.path.join(paths["covers"], archive_name)
            try:
                shutil.copy2(img_path_for_batch, archive_path)
                print(f"   ✅ Archived: {archive_name}")
            except:
                pass
        
        execution_queue.append({
            "batch": selected_batch,
            "label": range_label,
            "image": img_path_for_batch,
            "start_chk": check_start,
            "end_chk": check_end
        })
    
    # === PHASE 2: EXECUTION ===
    print("\n" + "=" * 50)
    print(f"🚀 PHASE 2: PROCESSING {len(execution_queue)} VIDEOS")
    print("=" * 50)
    
    # Feature 2: ETA Calculation
    processing_start_time = time.time()
    chapter_times = []
    
    for i, item in enumerate(execution_queue):
        print("\n" + "═" * 80)
        
        # Calculate ETA
        elapsed_total = time.time() - processing_start_time
        avg_time = sum(chapter_times) / len(chapter_times) if chapter_times else 0
        
        eta_str = "Calculating..."
        if avg_time > 0:
            remaining = len(execution_queue) - i
            eta_seconds = avg_time * remaining
            # Better avg calculation
            if i > 0:
                 avg_time = elapsed_total / i
                 eta_seconds = avg_time * remaining
                 eta_str = str(timedelta(seconds=int(eta_seconds)))
        
        # Feature 3: Memory Status
        mem_status = check_memory_status()
        
        print(f"   PROCESSING VIDEO {i+1}/{len(execution_queue)} → {item['label']}")
        print(f"   ⏱️  ETA: {eta_str} | {mem_status}")
        chapter_start_time = time.time()
        print("═" * 80)
        
        base_name = sanitize_filename(meta['title'])
        range_name = f"{base_name} ({item['label']})"
        audio_file = os.path.join(paths["audio"], f"{range_name}.mp3")
        video_file = os.path.join(paths["video"], f"{range_name}.mp4")
        
        # Resume capability - skip if video exists
        if os.path.exists(video_file):
            print(f"   ⏭️  Video already exists! Skipping...", flush=True)
            continue
        
        # === AUDIO GENERATION ===
        print(f"\n   🎵 AUDIO GENERATION", flush=True)
        print(f"   Target: {audio_file}", flush=True)
        
        success, timestamps, word_timeline = run_audio_gen_with_timestamps(
            item["batch"], meta, audio_file, speed, paths["temp"],
            tts_engine, tts_voice, use_concurrent, force_align=cli_args.force_align,
            whisper_model=cli_args.whisper_model, whisper_threads=cli_args.whisper_threads
        )
        
        # === CRITICAL VERIFICATION ===
        print(f"\n   🔍 AUDIO VERIFICATION", flush=True)
        
        audio_exists = os.path.exists(audio_file)
        print(f"   File exists: {audio_exists}", flush=True)
        
        if not audio_exists:
            print(CP(f"   ❌ FATAL: Audio file not created!", 'red'), flush=True)
            print(f"   Expected: {audio_file}", flush=True)
            
            # Check temp folder
            print(f"\n   📂 Checking temp folder...", flush=True)
            if os.path.exists(paths["temp"]):
                temp_files = [f for f in os.listdir(paths["temp"]) if f.endswith('.mp3')]
                print(f"   Temp MP3 files: {len(temp_files)}", flush=True)
                for tf in temp_files[:10]:
                    tfpath = os.path.join(paths["temp"], tf)
                    tfsize = os.path.getsize(tfpath)
                    print(f"      • {tf}: {tfsize:,} bytes", flush=True)
            
            play_critical_failure_alarm()
            response = input("\n   Continue to next video (c) or Exit (e)? ").strip().lower()
            if response == 'e':
                sys.exit(1)
            else:
                continue
        
        audio_size = os.path.getsize(audio_file)
        print(f"   Size: {audio_size:,} bytes ({audio_size/1024/1024:.2f} MB)", flush=True)
        
        if audio_size < 10000:
            print(CP(f"   ⚠️  WARNING: Suspiciously small audio file!", 'yellow'), flush=True)
            response = input("   Continue anyway? (y/n): ").strip().lower()
            if response != 'y':
                continue
        
        # Test audio readability
        try:
            test_clip = AudioFileClip(audio_file)
            duration = test_clip.duration
            test_clip.close()
            print(f"   Duration: {seconds_to_time_str(duration)}", flush=True)
            print(CP(f"   ✅ Audio file validated!", 'green'), flush=True)
        except Exception as e:
            print(CP(f"   ❌ Audio file corrupted: {e}", 'red'), flush=True)
            play_critical_failure_alarm()
            response = input("\n   Continue to next video (c) or Exit (e)? ").strip().lower()
            if response == 'e':
                sys.exit(1)
            else:
                continue
        
        # === DESCRIPTION & VIDEO ===
        if success:
            generate_description_file(meta, range_name, paths, timestamps, CONFIG)
            print("   ⏳ Stabilizing (5s)...", flush=True)
            time.sleep(5)
            
            print(f"\n   🎬 VIDEO GENERATION", flush=True)
            video_success = create_video_with_recovery(
                audio_file, item["image"], video_file,
                book_title=meta['title'],
                chapter_range=item['label'],
                timestamps=timestamps,
                word_timeline=word_timeline,
                max_retries=3
            )
            
            # Verify video was created
            if video_success and os.path.exists(video_file):
                video_size = os.path.getsize(video_file)
                print(CP(f"   ✅ Video created: {video_size/1024/1024:.1f} MB", 'green'), flush=True)
                
                # Phase 2: Save EPUB hash with history
                save_to_history(meta['title'], item["start_chk"], item["end_chk"], epub_hash)
                
                # Checkpoint: Save progress
                save_progress_checkpoint(
                    meta['title'],
                    i + 1,
                    len(execution_queue),
                    [x['label'] for x in execution_queue[:i+1]]
                )
                
                # Feature 2: Record timing
                chapter_times.append(time.time() - chapter_start_time)
                
                # Feature 3: Low Memory Mode - Force GC and Optimize
                optimize_memory()
            else:
                print(CP(f"   ❌ Video file not created!", 'red'), flush=True)
        else:
            print(CP("   ❌ Audio generation reported failure", 'red'), flush=True)
    
    # === CLEANUP PROMPT ===
    print("\n" + "═" * 80)
    print(CP("🧹 CLEANUP OPTIONS", 'cyan'))
    print("═" * 80)
    
    # Check what files exist
    epub_exists = os.path.exists(selected_path)
    temp_folders_exist = len(get_all_temp_folders()) > 0
    
    if epub_exists:
        epub_size = os.path.getsize(selected_path) / (1024 * 1024)
        print(f"\n📚 Source EPUB: {os.path.basename(selected_path)}")
        print(f"   Location: {INPUT_ZONE}")
        print(f"   Size: {epub_size:.1f} MB")
        print(f"   Status: ✅ Backed up in project folder")
        
        delete_epub = input("\n   Delete source EPUB from input folder? (y/n): ").strip().lower()
        
        if delete_epub == 'y':
            print("\n   🗑️  Deleting source EPUB...", flush=True)
            deleted = False
            for attempt in range(1, 8):
                try:
                    os.remove(selected_path)
                    logger.info(f"Removed input: {selected_path}")
                    print(CP("   ✅ Source EPUB deleted from input folder", 'green'), flush=True)
                    deleted = True
                    break
                except PermissionError:
                    if attempt < 7:
                        print(f"   ⏳ Retry {attempt}/7 in 3 sec (file may be locked)...", flush=True)
                        time.sleep(3)
                    else:
                        print(CP(f"   ⚠️  Could not delete (file locked)", 'yellow'), flush=True)
                        print(f"   Please close any programs using it and delete manually:")
                        print(f"   {selected_path}", flush=True)
                except Exception as e:
                    logger.error(f"EPUB deletion failed: {e}")
                    print(CP(f"   ❌ Deletion failed: {e}", 'red'), flush=True)
                    break
            
            if not deleted:
                print("\n   💡 Tip: EPUB is safe in your project folder at:")
                print(f"      {final_epub_path}")
        else:
            print(CP("   ℹ️  Keeping source EPUB in input folder", 'cyan'), flush=True)
    
    # Temp folder cleanup
    if temp_folders_exist:
        print(f"\n🗂️  Temporary Files: Found in {len(get_all_temp_folders())} projects")
        clean_temps = input("   Clean up all temporary files now? (y/n): ").strip().lower()
        
        if clean_temps == 'y':
            print("\n   🧹 Cleaning temporary files...", flush=True)
            cleaned, freed, failed = cleanup_old_temp_files(max_age_days=0, min_size_mb=0)
            if cleaned > 0:
                print(CP(f"   ✅ Freed {freed:.1f} MB from {cleaned} folders", 'green'), flush=True)
    
    print("\n" + "═" * 80)
    
    # Rainbow celebration
    celebration = "🎉 ALL TASKS COMPLETED!"
    colors = ['\033[91m', '\033[93m', '\033[92m', '\033[96m', '\033[94m', '\033[95m']
    rainbow = ""
    for i, char in enumerate(celebration):
        if char not in [' ', '🎉']:
            rainbow += colors[i % len(colors)] + char
        else:
            rainbow += char
    print("\n" + rainbow + '\033[0m')
    print(f"   📂 Location: {paths['root']}")
    beep_notification()
    
    # Clear checkpoint on success
    CheckpointManager().clear_checkpoint()
    
    input("Press Enter to exit...")

if __name__ == "__main__":
    # Parse CLI arguments for novel name mapping commands
    if len(sys.argv) > 1:
        if sys.argv[1] == '--lookup' and len(sys.argv) > 2:
            from features.novel_name_mapper import lookup_by_youtube_name_cli
            lookup_by_youtube_name_cli(' '.join(sys.argv[2:]))
            sys.exit(0)
        elif sys.argv[1] == '--list-mappings':
            from features.novel_name_mapper import list_all_mappings_cli
            list_all_mappings_cli()
            sys.exit(0)
        elif sys.argv[1] == '--search-mappings' and len(sys.argv) > 2:
            from features.novel_name_mapper import search_mappings_cli
            search_mappings_cli(' '.join(sys.argv[2:]))
            sys.exit(0)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        try:
            input("\nPress Enter to exit...")
        except:
            pass
        sys.exit(1)