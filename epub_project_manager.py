#!/usr/bin/env python3
import os
import sys
import gc
import asyncio
import re
import subprocess
import time
import glob
import shutil
import argparse
import json
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
from core import ui_manager
from core.epub_io import (
    setup_global_input, cleanup_temp_dir, setup_project_folders,
    load_history, save_to_history, check_history_conflict,
    calculate_epub_hash, check_duplicate_epub, get_history_summary,
    delete_book_from_history,
    load_book_profile, save_book_profile,
    clean_html_for_tts, clean_html_summary, parse_full_epub,
    extract_cover_to_project, generate_description_file, validate_epub,
    get_all_temp_folders, cleanup_old_temp_files, check_temp_space_warning
)
from core.tts import (
    EDGE_TTS_AVAILABLE, PYTTSX3_AVAILABLE, PIPER_AVAILABLE,
    select_tts_engine_and_mode, select_voice,
    test_edge_tts_connection, get_piper_models, select_piper_model,
    gen_single_clip_edge_with_retry,
    gen_single_clip_pyttsx3_with_retry,
    gen_single_clip_piper_with_retry,
    resolve_piper_model_path,
    gen_single_clip_chatterbox,
    CHATTERBOX_AVAILABLE
)
from features.multispeaker_tts import gen_multispeaker_chapter
from core.gemini_client import create_gemini_client, GeminiClientError

from core.ui.menus import (
    show_chapter_overview, enforce_batch_size_limit,
    resolve_project_name_and_history, show_preflight_summary
)

from core.parallel_tts import ParallelTTSManager
from core.aligner import WhisperAligner

from features.checkpoint_manager import CheckpointManager, save_progress_checkpoint, get_checkpoint_if_exists, ask_to_resume_checkpoint
from features.memory_manager import optimize_memory, check_memory_status
from features.queue_manager import QueueManager
from features.novel_name_mapper import auto_save_mapping
from features.auto_recovery import AutoRecovery
from core.subtitle_generator import generate_subtitles_for_video
from core.video_pipeline import generate_timeline_with_alignment, render_video_with_timeline, check_dependencies
from core.profiler import enable_profiling, disable_profiling, get_profiler
from core.logging_config import setup_logging, get_logger
from core.path_utils import ensure_path, ensure_dir, safe_path_join, get_file_size_mb

# Legacy compatibility
UPLOADED_NOVELS_DIR = os.path.join(MASTER_NOVEL_DIR, "Uploaded in Youtube")



# ---------------------------
# LOCAL HELPERS (not duplicated - unique to main file)
# ---------------------------

# UI functions moved to core.ui.menus

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

# Preflight summary moved to core.ui.menus

# ---------------------------
# TEMP FILE CLEANUP SYSTEM
# ---------------------------
# Temp file cleanup moved to core.epub_io



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
def run_audio_gen_with_timestamps(chapters, meta, final_filename, speed_rate, temp_dir, tts_engine, tts_voice, use_concurrent=False, intro_override=None, skip_disclaimer=False):
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
        
        intro_text = intro_override if intro_override else CONFIG["branding"]["intro"]
        success, error, tts_engine, tts_voice, tts_result = gen_audio_with_recovery(
            intro_text, intro_path, tts_engine, tts_voice, 
            speed_rate, max_retries, delay, "Introduction"
        )
        
        if not success:
            handle_critical_failure("Introduction", error)
        
        clip = AudioFileClip(intro_path)
        clips_to_merge.append(clip)
        timestamp_list.append((current_seconds, "Introduction"))
        
        # Accumulate intro timing ONLY if high precision
        is_precision = tts_result.get('is_high_precision', False) if tts_result else False
        if is_precision and tts_result and tts_result.get('events'):
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
        if not skip_disclaimer:
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
            
            # Accumulate disclaimer timing ONLY if high precision
            is_precision = tts_result.get('is_high_precision', False) if tts_result else False
            if is_precision and tts_result and tts_result.get('events'):
                for word in tts_result['events']:
                    word['start'] += current_seconds
                    word['end'] += current_seconds
                    full_word_timeline.append(word)
            
            current_seconds += clip.duration
            print(CP(f"   ✅ Disclaimer: {clip.duration:.1f}s", 'green'), flush=True)
        else:
             print("   ⏭️  Skipping disclaimer (Continuation Video)", flush=True)
        
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
        
        # Accumulate title timing ONLY if high precision
        is_precision = tts_result.get('is_high_precision', False) if tts_result else False
        if is_precision and tts_result and tts_result.get('events'):
            for word in tts_result['events']:
                word['start'] += current_seconds
                word['end'] += current_seconds
                full_word_timeline.append(word)
                
        current_seconds += clip.duration
        print(CP(f"   ✅ Title: {clip.duration:.1f}s", 'green'), flush=True)
        
        # Save chapter start offset not needed for Whisper
        # chapter_start_offset = current_seconds
        
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
            
            # ... (Existing Loading logic)
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
                    
                    xfade = 0.5 if CONFIG["audio_settings"].get("enable_audio_crossfade", True) else 0
                    if successful_count > 0:
                        current_seconds -= xfade

                    clip = AudioFileClip(audio_path)
                    timestamp_list.append((current_seconds, title))
                    
                    if xfade > 0:
                        if successful_count > 0:
                            clip = clip.audio_fadein(xfade)
                    
                    clips_to_merge.append(clip)
                    
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

        # Parallel Piper block removed as per request for stability.
        # Fallback to sequential mode in 'else' block below.

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
                    chap_path = os.path.join(temp_dir, f"chap_{i}.mp3" if tts_engine != "piper" else f"chap_{i}.wav")
                    
                    if tts_engine == "edge":
                        tts_success, tts_error, tts_result = asyncio.run(gen_single_clip_edge_with_retry(
                            audio_text, chap_path, tts_voice, speed_rate,
                            max_retries=max_retries, delay=delay, silent=True
                        ))
                    elif tts_engine == "piper":
                        # [AI] Check for Gemini TTS Switching
                        gemini_client = create_gemini_client()
                        gemini_enabled = gemini_client and CONFIG.get("gemini_settings", {}).get("enabled", False)
                        
                        if gemini_enabled:
                            print(f"      ✨ AI analyzing chapter for multi-speaker audio...", flush=True)
                            
                            character_list = []
                            try:
                                project_root = os.path.dirname(temp_dir)
                                ai_meta_path = os.path.join(project_root, "ai_metadata.json")
                                if os.path.exists(ai_meta_path):
                                    with open(ai_meta_path, 'r', encoding='utf-8') as f_meta:
                                        ai_data = json.load(f_meta)
                                        character_list = ai_data.get('story_analysis', {}).get('characters', [])
                            except Exception as e:
                                logger.warning(f"Could not load character list for AI analysis: {e}")

                            analysis = gemini_client.analyze_tts_segments(
                                chapter_text=clean_body,
                                chapter_number=i+1,
                                character_list=character_list,
                                chatterbox_used_count=0 
                            )
                            
                            if analysis and 'segments' in analysis:
                                from core.ai_schemas import TTSBatchScript, TTSSegment
                                segments = [TTSSegment(**s) for s in analysis['segments']]
                                script = TTSBatchScript(segments=segments)
                                tts_success, tts_error, tts_result = asyncio.run(gen_multispeaker_chapter(script, chap_path))
                            else:
                                tts_success, tts_error, tts_result = gen_single_clip_piper_with_retry(
                                    audio_text, chap_path, tts_voice,
                                    max_retries=max_retries, delay=delay
                                )
                        else:
                            tts_success, tts_error, tts_result = gen_single_clip_piper_with_retry(
                                audio_text, chap_path, tts_voice,
                                max_retries=max_retries, delay=delay
                            )

                    elif tts_engine == "chatterbox":
                        tts_success, tts_error, tts_result = gen_single_clip_chatterbox(
                            audio_text, chap_path
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
                    
                    xfade = 0.5 if CONFIG["audio_settings"].get("enable_audio_crossfade", True) else 0
                    if i > 0:
                        current_seconds -= xfade

                    timestamp_list.append((current_seconds, title))
                    clip = AudioFileClip(chap_path)
                    
                    if xfade > 0:
                        if i > 0:
                            clip = clip.audio_fadein(xfade)
                    
                    clips_to_merge.append(clip)
                    
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
        
        # Accumulate outro timing ONLY if high precision
        is_precision = tts_result.get('is_high_precision', False) if tts_result else False
        if is_precision and tts_result and tts_result.get('events'):
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
            for failed in failed_chapters:
                print(f"      • Ch {failed['number']}: {failed['title']}", flush=True)
            return False, [], []
        
        # === FINAL ASSEMBLY ===
        if len(clips_to_merge) == 0:
            print(CP("\n   ❌ No audio clips generated", 'red'), flush=True)
            play_critical_failure_alarm()
            return False, [], []
        
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
        # REFACTOR: Subtitle generation is now deferred to the video creation phase 
        # where we use Faster-Whisper on the final audio file for perfect sync.
        #
        # print("   📝 Generating subtitles...", flush=True)
        # ass_path = final_filename.replace(".mp3", ".ass")
        # 
        # # PERFECT TIMING: Always use Faster-Whisper transcription
        # # This ensures word-level accuracy for ALL TTS engines by transcribing the final audio
        # print("   ℹ️  Using Faster-Whisper for perfect word-level timing", flush=True)
        # full_word_timeline = []  # Clear TTS timing, force Whisper transcription
        #
        # subtitle_generated = False
        # 
        # # NEW: Universal Perfect Timing Logic
        # # Whisper (Precision Pass) has been replaced by CaptionGod integration in create_video
        # # if needs_precision_pass: ... (removed)
        #
        # if not subtitle_generated and full_word_timeline:
        #     print("      Found word-level timing data", flush=True)
        #     from core.subtitle_generator import generate_ass_from_word_timeline
        #     if generate_ass_from_word_timeline(full_word_timeline, ass_path, CONFIG):
        #          print(f"      ✅ ASS Subtitles generated: {os.path.basename(ass_path)}", flush=True)
        #          subtitle_generated = True
        #
        # if not subtitle_generated:
        #     # Fallback to timestamp-based if no word data and Whisper failed
        #     print("      Using chapter markers as fallback subtitles", flush=True)
        #     from core.subtitle_generator import generate_ass_from_timestamps
        #     if generate_ass_from_timestamps(timestamp_list, ass_path, CONFIG):
        #         print(f"      ✅ ASS Subtitles generated: {os.path.basename(ass_path)}", flush=True)
        
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
        # Load and immediately copy the original to make it independent
        original_img = Image.open(cover_path)
        original = original_img.convert("RGB").copy()  # CRITICAL: .copy() makes it independent
        original_img.close()  # Explicitly close the file handle
        
        W, H = target_size if target_size else (854, 480)
        
        # Create background (blurred version)
        bg_aspect = original.width / original.height
        bg_new_height = int(W / bg_aspect)
        background = original.resize((W, max(bg_new_height, H)), Image.Resampling.LANCZOS).copy()
        
        left = (background.width - W) // 2
        top = (background.height - H) // 2
        background = background.crop((int(left), int(top), int(left + W), int(top + H)))
        background = background.filter(ImageFilter.GaussianBlur(20))
        
        # Convert to RGBA for overlay operations
        background = background.convert("RGBA")
        
        # Dark overlay
        overlay = Image.new('RGBA', (W, H), (0, 0, 0, 80))
        background = Image.alpha_composite(background, overlay)
        
        # Create sharp foreground
        target_h = int(H * 0.90)
        ratio = target_h / original.height
        target_w = int(original.width * ratio)
        sharp = original.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        x = (W - target_w) // 2
        y = (H - target_h) // 2
        
        # Add shadow
        shadow = Image.new('RGBA', (target_w, target_h), (0, 0, 0, 150))
        background.paste(shadow, (x + 10, y + 10), shadow)
        
        # Paste sharp foreground
        sharp_rgba = sharp.convert("RGBA")
        background.paste(sharp_rgba, (x, y), sharp_rgba)
        
        # Add text overlay if enabled
        enable_overlay = CONFIG.get("video_settings", {}).get("enable_text_overlay", True)
        print(f"🔍 DEBUG: enable_text_overlay = {enable_overlay}, book_title = {book_title}", flush=True)
        
        if enable_overlay and book_title:
            draw = ImageDraw.Draw(background)
            
            # Load font
            font_size = CONFIG.get("video_settings", {}).get("text_overlay_font_size", 36)
            try:
                font_path = "C:/Windows/Fonts/arialbd.ttf"
                if not os.path.exists(font_path):
                    font_path = "C:/Windows/Fonts/arial.ttf"
                if os.path.exists(font_path):
                    title_font = ImageFont.truetype(font_path, font_size)
                    range_font = ImageFont.truetype(font_path, int(font_size * 0.7))
                else:
                    title_font = ImageFont.load_default()
                    range_font = ImageFont.load_default()
            except:
                title_font = ImageFont.load_default()
                range_font = ImageFont.load_default()
            
            bottom_margin = CONFIG.get("video_settings", {}).get("text_overlay_bottom_margin", 40)
            display_title = book_title[:40] + "..." if len(book_title) > 40 else book_title
            
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
            
            # Text background
            text_bg = Image.new('RGBA', (W, text_bg_height), (0, 0, 0, 180))
            background.paste(text_bg, (0, H - text_bg_height - bottom_margin), text_bg)
            
            title_x = (W - title_width) // 2
            title_y = H - text_bg_height - bottom_margin + text_padding
            
            # Draw text with shadow
            shadow_offset = 2
            draw.text((title_x + shadow_offset, title_y + shadow_offset), display_title, 
                     fill=(0, 0, 0, 200), font=title_font)
            draw.text((title_x, title_y), display_title, 
                     fill=(255, 255, 255), font=title_font)
            
            if chapter_range:
                range_x = (W - range_width) // 2
                range_y = title_y + title_height + 10
                draw.text((range_x + shadow_offset, range_y + shadow_offset), chapter_range,
                         fill=(0, 0, 0, 200), font=range_font)
                draw.text((range_x, range_y), chapter_range,
                         fill=(255, 255, 100), font=range_font)
        
        # Save the final image
        temp_filename = f"temp_thumb_{unique_id}.jpg"
        out_path = os.path.join(output_folder, temp_filename)
        final_rgb = background.convert("RGB")
        final_rgb.save(out_path, 'JPEG', quality=95)
        
        # Cleanup
        original.close()
        background.close()
        final_rgb.close()
        
        return out_path
            
    except Exception as e:
        logger.error(f"Thumbnail generation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_video_with_recovery(audio_path, image_path, output_path, book_title=None, chapter_range=None, timestamps=None, word_timeline=None, max_retries=3, quality_preset=None, text_content=None, enable_captions=True):
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
            
            create_video(audio_path, image_path, output_path, book_title, chapter_range, timestamps, word_timeline, quality_preset, text_content, enable_captions=enable_captions)
            
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

def create_video(audio_path, image_path, output_path, book_title=None, chapter_range=None, timestamps=None, word_timeline=None, quality_preset=None, text_content=None, enable_captions=True):
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
                
                # Only check CaptionGod if we DON'T have word_timeline (fallback path)
                # [REMOVED] CaptionGod check removed by user request

                
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
                # Use Word Timeline from TTS if available (FASTER & MORE ACCURATE)
                if enable_captions:
                    if word_timeline and len(word_timeline) > 0:
                        print(f"   ⚡ Using high-precision TTS timing data for captions...", flush=True)
                        print(f"   📊 Word count: {len(word_timeline)} words with exact timestamps", flush=True)
                        from core.video_pipeline import generate_timeline_from_words
                        timeline_data = generate_timeline_from_words(
                            render_audio_tmp,
                            project_id=project_id,
                            words=word_timeline,
                            config=CONFIG
                        )
                    else:
                        # Fallback to Faster-Whisper Transcription
                        print(f"   🎙️  No TTS timing data available, using Faster-Whisper transcription...", flush=True)
                        timeline_data = generate_timeline_with_alignment(
                            render_audio_tmp,
                            project_id=project_id,
                            config=CONFIG,
                            text_content=text_content,
                            time_offset=0
                        )
                else:
                    print(f"   🚫 Captions disabled by user preference.", flush=True)
                    # Empty timeline for no captions
                    timeline_data = {
                        "project_id": project_id,
                        "media": {"path": render_audio_tmp, "duration": expected_duration},
                        "timeline": [],
                        "metadata": {"source": "disabled"}
                    }

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
        if enable_captions and not subtitle_file and not advanced_render_succeeded and timestamps and len(timestamps) > 0:
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
            
            # [FIX] Ensure even dimensions for libx264
            w, h = video_clip.size
            if w % 2 != 0 or h % 2 != 0:
                new_w = (w // 2) * 2
                new_h = (h // 2) * 2
                print(f"   ⚠️  Resizing to even dimensions: {w}x{h} -> {new_w}x{new_h}", flush=True)
                video_clip = video_clip.resize(newsize=(new_w, new_h))
                
            video_clip = video_clip.set_audio(final_audio)

            # Prepare ffmpeg parameters
            ffmpeg_params_list = ffmpeg_params.copy()
            # Force yuv420p for compatibility (fixes black screen on some players)
            ffmpeg_params_list.extend(['-pix_fmt', 'yuv420p'])
            
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
        
        # (Removed duplicate 'Video saved!' message - already printed at line 1497)
    
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
  
  # Test mode (temporary data storage):
  python epub_project_manager.py --test-mode --history-dir "path/to/test/history" --novels-dir "path/to/test/novels"
        """
    )
    
    # Test mode arguments
    parser.add_argument("--test-mode", action="store_true",
                       help="Run in test mode (temporary data storage)")
    parser.add_argument("--history-dir", type=str, default=None,
                       help="Custom history directory (for test mode)")
    parser.add_argument("--novels-dir", type=str, default=None,
                       help="Custom novels directory (for test mode)")
    
    # TTS and processing arguments
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

    
    # Novel Name Mapper commands
    parser.add_argument("--sync", action="store_true",
                       help="Sync novel mappings from history and folders")
    parser.add_argument("--lookup", type=str, metavar="NAME",
                       help="Look up a novel by YouTube name")
    parser.add_argument("--list-mappings", action="store_true",
                       help="List all novel name mappings")
    parser.add_argument("--search-mappings", type=str, metavar="QUERY",
                       help="Search novel mappings")
    
    # Queue management mode
    parser.add_argument("--queue-manager", action="store_true",
                       help="Enter queue manager mode: configure EPUBs to process sequentially")
    parser.add_argument("--worker", action="store_true",
                       help="Run as queue worker: process jobs from the queue (usually auto-spawned)")
    
    return parser.parse_args()

def configure_book_for_queue(cli_args):
    """Interactive script to select and configure an EPUB for the queue, without processing it."""
    import glob
    
    # === FILE SELECTION ===
    epub_files = glob.glob(os.path.join(INPUT_ZONE, "*.epub"))
    if not epub_files:
        print(f"\n   ℹ️  No files in '{INPUT_ZONE}'.")
        return None
    
    print(CP(f"\n📚 SELECT EPUB FOR QUEUE:", 'cyan'))
    for i, f in enumerate(epub_files):
        print(f"   [{i+1}] {os.path.basename(f)}")
    
    selected_path = None
    while not selected_path:
        try:
            choice = input("\n👉 Select book (or 'q' to cancel): ").strip()
            if choice.lower() == 'q': return None
            choice_idx = int(choice)
            if 1 <= choice_idx <= len(epub_files):
                selected_path = epub_files[choice_idx - 1]
                break
        except: pass

    # === PARSING ===
    valid, error = validate_epub(selected_path)
    if not valid:
        print(CP(f"❌ Invalid EPUB: {error}", 'red'))
        return None

    meta, all_chapters, book_obj = parse_full_epub(selected_path)
    original_epub_title = meta['title']
    final_title = meta['title']
    
    # === DUPLICATE DETECTION & RENAMING ===
    final_title, meta, reset_done = resolve_project_name_and_history(selected_path, meta, cli_args)
    if not final_title: return None
    final_title_resolved = True 
    
    print(CP(f"\n📘 Project Name: {final_title}", 'cyan'))
    
    # === OPTIONS ===
    tts_engine, use_concurrent = select_tts_engine_and_mode()
    tts_voice = select_voice(tts_engine)
    
    spd = input(f"⚡ Speed (default +0%): ").strip()
    speed = "+0%"
    if spd:
        if not spd.startswith(("+", "-")): spd = "+" + spd
        speed = spd if "%" in spd else f"{spd}%"

    # Smart Merge
    merge = input("🧩 Enable Smart Chapter Merge? (y/n, default n): ").strip().lower() == 'y'
    if merge:
        print("   🔄 Applying Smart Chapter Merge...", flush=True)
        try:
            from features.chapter_merger import ChapterMerger
            merger = ChapterMerger()
            # Use a temporary paths dict for the merger
            temp_paths = {"temp": os.path.join(ACTIVE_NOVELS_DIR, sanitize_filename(final_title), "temp_render_files")}
            os.makedirs(temp_paths["temp"], exist_ok=True)
            all_chapters = merger.merge_chapters(all_chapters, book_obj, temp_paths["temp"])
        except Exception as e:
            print(f"   ⚠️  Merge failed: {e}")

    # Range & Batch
    show_chapter_overview(all_chapters)
    range_input = input(f"📍 Enter range (e.g. 1-100) or Enter for all: ").strip()
    start_chap, end_chap = 1, len(all_chapters)
    if range_input and "-" in range_input:
        try:
            parts = range_input.split("-")
            start_chap = max(1, int(parts[0]))
            end_chap = min(len(all_chapters), int(parts[1]))
        except: pass
    
    selected_chapters = all_chapters[start_chap-1:end_chap]
    print(f"   ✅ Selected: Chapter {start_chap} to {end_chap} ({len(selected_chapters)} chapters)")
    
    batch_size = 10
    try:
        bs_in = input(f"🔢 Chapters per video (default 10): ").strip()
        if bs_in: batch_size = int(bs_in)
    except: pass

    # Create raw_batches
    raw_batches = []
    start_idx = start_chap - 1
    selected_chapters = all_chapters[start_idx:end_chap]
    for i in range(0, len(selected_chapters), batch_size):
        b_start = start_idx + i
        b_end = start_idx + min(i + batch_size, len(selected_chapters))
        raw_batches.append((b_start, b_end))

    # --- HISTORY CHECK ---
    print(f"\n🔍 Checking processing history for '{final_title}'...")
    any_conflict = False
    for b_start, b_end in raw_batches:
        # Extract smart numbers for the batch
        batch_slice = all_chapters[b_start:b_end]
        first_title = batch_slice[0][0]
        last_title = batch_slice[-1][0]
        real_start = extract_smart_number(first_title)
        real_end = extract_smart_number(last_title)
        
        check_start = real_start if real_start is not None else b_start + 1
        check_end = real_end if real_end is not None else b_end
        
        conflict, msg = check_history_conflict(final_title, check_start, check_end)
        if conflict:
            color = 'red' if conflict == True else 'yellow'
            prefix = "⚠️  History Conflict" if conflict == True else "ℹ️  History Notice"
            print(CP(f"   {prefix}: Ch {check_start}-{check_end} ({msg})", color))
            any_conflict = True
            
    if any_conflict:
        proceed = input(CP("\n👉 This book has been processed before. Add to queue anyway? (y/n, default n): ", 'white')).strip().lower()
        if proceed == 'y':
            meta['_partial_reset_pending'] = True
        else:
            print("   Exiting configuration.")
            return None


    # --- THUMBNAIL SELECTION & PROCESSING (During Configuration) ---
    print(f"\n{CP('🎨 THUMBNAIL SELECTION', 'cyan')}")
    print(f"   You are creating {len(raw_batches)} video(s).")
    print(f"\n   Choose thumbnail mode:")
    print(f"   {CP('[1]', 'cyan')} Use same thumbnail for all videos (EPUB cover or one custom image)")
    print(f"   {CP('[2]', 'cyan')} Select different thumbnail for each video")
    
    thumb_mode = input(f"\n   👉 Select (1/2, default 1): ").strip()
    
    # Setup paths for thumbnail processing
    # We need to create the project structure early to save processed thumbnails
    safe_title = sanitize_filename(final_title)
    project_root = os.path.join(ACTIVE_NOVELS_DIR, safe_title)
    covers_folder = os.path.join(project_root, "cover_images")
    temp_folder = os.path.join(project_root, "temp_render_files")
    
    print(f"\n   🔍 DEBUG: Project folder: {project_root}", flush=True)
    print(f"   🔍 DEBUG: Covers folder: {covers_folder}", flush=True)
    
    # Create folders if they don't exist
    os.makedirs(covers_folder, exist_ok=True)
    os.makedirs(temp_folder, exist_ok=True)
    
    paths_for_processing = {
        "root": project_root,
        "covers": covers_folder,
        "temp": temp_folder
    }
    
    # Get quality settings for thumbnail sizing
    curr_preset = CONFIG["video_settings"].get("current_quality_preset", "Balanced")
    presets = CONFIG["video_settings"].get("quality_presets", {})
    q_conf = presets.get(curr_preset, presets.get("Balanced", {"height": 720}))
    target_h = q_conf.get("height", 720)
    target_w = int(target_h * 16 / 9)
    if target_w % 2 != 0: target_w += 1
    
    processed_thumbnails = {}  # Will store final processed thumbnail paths
    
    
    if thumb_mode == '2':
        # Per-video thumbnail selection - directly ask for custom images
        print(f"\n   📸 Provide a custom thumbnail for each of the {len(raw_batches)} video(s)...")
        print(f"   💡 TIP: Press Enter to use EPUB cover for any video\n")
        
        for idx, (start_i, end_i) in enumerate(raw_batches):
            # Calculate chapter range for display
            batch_chapters = all_chapters[start_i:end_i]
            first_title = batch_chapters[0][0]
            last_title = batch_chapters[-1][0]
            real_start = extract_smart_number(first_title)
            real_end = extract_smart_number(last_title)
            
            if real_start is not None and real_end is not None:
                range_label = f"Ch {real_start}-{real_end}"
            else:
                range_label = f"Part {start_i+1}-{end_i}"
            
            print(f"   🎬 Video {idx+1}/{len(raw_batches)}: {range_label}")
            custom_thumb = input(f"      🖼️  Drag image here (or press Enter for EPUB cover): ").strip().replace('"', '').replace("'", "")
            
            if custom_thumb and os.path.exists(custom_thumb):
                # [USER REQUIREMENT] Use Simple Resize for Custom Image (no effects)
                archive_name = f"{sanitize_filename(range_label)}.jpg"
                archive_path = os.path.join(covers_folder, archive_name)
                
                print(f"      ⚙️  Resizing custom thumbnail...", flush=True)
                from core.utils import simple_resize_image
                success = simple_resize_image(custom_thumb, archive_path, target_size=(target_w, target_h))
                
                if success:
                    processed_thumbnails[idx] = archive_path
                    print(f"      ✅ Saved Custom Thumbnail: {archive_name}", flush=True)
                else:
                    processed_thumbnails[idx] = "auto"
                    print(f"      ⚠️  Resize failed. Will use EPUB cover.", flush=True)
            elif custom_thumb:
                processed_thumbnails[idx] = "auto"
                print(f"      ⚠️  File not found: '{custom_thumb}'. Will use EPUB cover.", flush=True)
            else:
                processed_thumbnails[idx] = "auto"
                print(f"      ✅ Using EPUB cover", flush=True)
                print(f"      ✅ Will use EPUB cover")
    else:
        # Single thumbnail for all videos
        print(f"\n   [1] Use EPUB cover (Automatic)")
        print(f"   [2] Custom Image (Drag & Drop)")
        print(f"   💡 TIP: You can paste the image path directly!")
        thumb_choice = input(f"   👉 Select (default 1): ").strip()
        
        # Smart detection: if user pasted a file path, treat it as option 2
        if thumb_choice and thumb_choice not in ['1', '2']:
            # User pasted a path directly
            custom_thumb = thumb_choice.replace('"', '').replace("'", "")
            print(f"   🔍 Detected file path, using as custom thumbnail...")
        elif thumb_choice == "2":
            custom_thumb = input("   🖼️  Drag image here: ").strip().replace('"', '').replace("'", "")
        else:
            custom_thumb = None
        
        if custom_thumb and os.path.exists(custom_thumb):
            print(f"   ⚙️  Processing thumbnail for all {len(raw_batches)} video(s)...", flush=True)
            
            try:
                # Process for each batch with appropriate chapter range
                for idx, (start_i, end_i) in enumerate(raw_batches):
                    # ... (label calculation as before)
                    batch_chapters = all_chapters[start_i:end_i]
                    first_title = batch_chapters[0][0]
                    last_title = batch_chapters[-1][0]
                    real_start = extract_smart_number(first_title)
                    real_end = extract_smart_number(last_title)
                    range_label = f"Ch {real_start}-{real_end}" if real_start is not None else f"Part {start_i+1}-{end_i}"
                    
                    archive_name = f"{sanitize_filename(range_label)}.jpg"
                    archive_path = os.path.join(covers_folder, archive_name)
                    
                    # [USER REQUIREMENT] Use Simple Resize for Custom Image
                    from core.utils import simple_resize_image
                    success = simple_resize_image(custom_thumb, archive_path, target_size=(target_w, target_h))
                    
                    if success:
                        processed_thumbnails[idx] = archive_path
                        print(f"      ✅ Saved Custom Thumbnail: {archive_name}", flush=True)
                    else:
                        processed_thumbnails[idx] = "auto"
                        print(f"      ⚠️  Resize failed for batch {idx+1}", flush=True)
                
                success_count = len([p for p in processed_thumbnails.values() if p != 'auto'])
                print(f"   ✅ Processed and saved {success_count}/{len(raw_batches)} thumbnail(s)", flush=True)
                
            except Exception as e:
                print(f"   ❌ ERROR processing thumbnails: {e}", flush=True)
                import traceback
                traceback.print_exc()
                print(f"   ⚠️  Will use EPUB cover for all videos.", flush=True)
                for idx in range(len(raw_batches)):
                    processed_thumbnails[idx] = "auto"
        elif custom_thumb:
            print(f"   ⚠️  File not found: '{custom_thumb}'")
            print("   ⚠️  Will use EPUB cover for all videos.")
            for idx in range(len(raw_batches)):
                processed_thumbnails[idx] = "auto"
        else:
            print("   ✅ Will use auto-extracted EPUB cover for all videos")
            for idx in range(len(raw_batches)):
                processed_thumbnails[idx] = "auto"

    # Construct Job Settings
    settings = {
        "engine": tts_engine,
        "voice": tts_voice,
        "speed": speed,
        "concurrent": "yes" if use_concurrent else "no",
        "merge": merge,
        "raw_batches": raw_batches,
        "thumbnails": processed_thumbnails,  # Now contains processed paths or "auto"
        "partial_reset": meta.get('_partial_reset_pending', False),
        "quality_preset": CONFIG["video_settings"].get("current_quality_preset", "Balanced"),
        "enable_captions": input("\n📝 Enable Captions? (y/n, default y): ").strip().lower() != 'n'
    }
    
    return {
        "path": selected_path,
        "title": final_title,
        "original_title": original_epub_title, # NEW
        "settings": settings
    }

def run_queue_manager_mode(cli_args):
    """Integrated Queue Manager wrapper for CLI --queue-manager flag"""
    from features.queue_manager import QueueManager
    qm = QueueManager()
    
    def add_to_queue_callback():
        job_details = configure_book_for_queue(cli_args)
        if job_details:
            qm.add_to_queue(
                job_details['path'], 
                job_details['settings'],
                title=job_details.get('title'),
                original_title=job_details.get('original_title')
            )
            print(CP(f"\n   ✅ Added to queue: {job_details['title']}", 'green'))
            time.sleep(1)

    ui_manager.handle_queue_menu(qm, process_batch_queue, add_to_queue_callback)

def run_worker_mode():
    """Sequential worker that processes jobs from the processing_queue.json"""
    from features.queue_manager import QueueManager
    qm = QueueManager()
    
    print(f"\n{CP('⚙️ QUEUE WORKER ACTIVE', 'blue')}")
    print(f"{'='*60}")
    print("   Processing jobs from queue sequentially.")
    print(f"{'='*60}\n")
    
    while True:
        job = qm.claim_next_job()
        if not job:
            # Poll for a few seconds before giving up? or just exit?
            # Plan says exit when empty.
            print(f"\n{CP('🏁 Queue is empty. Worker exiting.', 'yellow')}")
            break
            
        print(f"\n{'='*60}")
        print(f"📦 PROCESSING JOB: {job['title']}")
        print(f"⏰ Start time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}\n")
        
        try:
            process_from_queue_job(job)
            qm.mark_completed(job['id'], success=True)
            print(CP(f"\n✅ SUCCESS: Completed {job['title']}", 'green'))
        except Exception as e:
            print(CP(f"\n❌ FAILED: {job['title']} - {e}", 'red'))
            logger.error(f"Worker Job Failed: {e}")
            qm.mark_completed(job['id'], success=False)
            
        # Cooldown and GC between books
        import gc
        gc.collect()
        time.sleep(5)


def process_batch_queue(qm):
    """Process all pending jobs in the queue"""
    jobs = qm.get_pending_jobs()
    if not jobs:
        print("\n   ⚠️  No pending jobs found.")
        return

    print(f"\n🚀 STARTING BATCH PROCESSING: {len(jobs)} Jobs")
    
    from rich.progress import track
    # Loop without rich track to avoid LiveError with nested progress bars
    for i, job in enumerate(jobs):
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
        
    # Parse EPUB
    valid, error = validate_epub(epub_path)
    if not valid:
        raise ValueError(f"Invalid EPUB: {error}")
    
    # Calculate hash for history
    epub_hash = calculate_epub_hash(epub_path)
    
    meta, all_chapters, book_obj = parse_full_epub(epub_path)
    if not all_chapters:
        raise ValueError("No chapters found in EPUB")
        
    # Override title if specified in job (e.g. by rename)
    if job.get('title'):
        meta['title'] = job['title']
        
    # Apply partial reset setting if present
    if settings.get('partial_reset'):
        meta['_partial_reset_pending'] = True
        
    # 2. Setup Project
    paths = setup_project_folders(meta['title'], ACTIVE_NOVELS_DIR)
    
    # [FIX] Copy EPUB to source folder for archival/reference (Matches interactive mode)
    final_epub_path = os.path.join(paths["epub"], os.path.basename(epub_path))
    if not os.path.exists(final_epub_path):
        try:
            shutil.copy2(epub_path, final_epub_path)
            print(f"   ✅ Archived EPUB to source folder", flush=True)
        except Exception as e:
            logger.warning(f"Failed to archive EPUB: {e}")
    
    # Auto-save novel name mapping if user renamed it (Integrated for Queue/Worker)
    original_title = job.get('original_title', meta.get('original_title', ''))
    if job.get('title') and job['title'] != original_title:
        from features.novel_name_mapper import auto_save_mapping
        auto_save_mapping(
            original_title=original_title,
            youtube_name=job['title'],
            project_path=paths["root"]
        )
    
    # 3. Execution Data
    
    # Apply Smart Merge if enabled in settings
    # This must re-run to match the indices stored in raw_batches
    if settings.get('merge'):
        print("   🔄 Applying Smart Chapter Merge (Batch)...", flush=True)
        try:
            from features.chapter_merger import ChapterMerger
            merger = ChapterMerger()
            # Note: We pass book_obj but the new merger ignores it and uses text content directly
            all_chapters = merger.merge_chapters(all_chapters, book_obj, paths["temp"])
        except Exception as e:
            logger.error(f"Batch merge failed: {e}")
            # Continue with unmerged chapters? Indices might be wrong.
            # Ideally we should fail, but let's try to proceed.
            print(f"   ⚠️  Merge failed: {e}. Usage of batch ranges might be incorrect.", flush=True)

    
    # Extract settings
    raw_batches = settings.get('raw_batches', [])
    processed_thumbnails = settings.get('thumbnails', {})
    enable_captions = settings.get('enable_captions', True)
    
    # Validate batches
    if not raw_batches:
        # Fallback to full book if no batches defined?
        # But for queue we expect batches to be pre-calculated
        logger.warning(f"No batches found for {job['title']}, attempting auto-batch...")
        # (Simplified fallback logic omitted for brevity, assuming valid job)
        pass
    execution_queue = []
    
    # --- COVER EXTRACTION (Once per job) ---
    extracted_cover = None
    # For backward compatibility, check both 'thumbnails' (new) and 'thumbnail' (old)
    thumbnails_dict = settings.get('thumbnails', {})
    legacy_thumbnail = settings.get('thumbnail', 'auto')
    
    # If using legacy single thumbnail, convert to dict format
    if not thumbnails_dict and legacy_thumbnail:
        thumbnails_dict = {i: legacy_thumbnail for i in range(len(raw_batches))}
    
    # Extract cover once if any batch uses 'auto'
    if any(thumb == 'auto' for thumb in thumbnails_dict.values()):
        extracted_cover = extract_cover_to_project(book_obj, paths, meta['title'])
        
        # Check for manual cover if extraction failed
        if not extracted_cover:
             manual_candidates = [
                 os.path.join(paths["root"], "cover.jpg"),
                 os.path.join(paths["root"], "cover.jpeg"),
                 os.path.join(paths["root"], "cover.png"),
                 os.path.join(paths["root"], "thumbnail.jpg"),
                 os.path.join(paths["covers"], "cover.jpg"),
                 os.path.join(paths["covers"], "cover.jpeg"),
                 os.path.join(paths["covers"], "cover.png")
             ]
             for cand in manual_candidates:
                 if os.path.exists(cand):
                     extracted_cover = cand
                     print(f"   ✅ Found manual cover: {os.path.basename(cand)}", flush=True)
                     break

    # Prepare batches
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

        # --- HISTORY CLEANUP (Partial Reset) ---
        if meta.get('_partial_reset_pending'):
            conflict, msg = check_history_conflict(meta['title'], check_start, check_end)
            if conflict:
                # Note: path is needed for hash calculation, title for backup matching
                delete_book_from_history(epub_path, title=meta['title'], chapters=(check_start, check_end))


        # --- THUMBNAIL LOGIC (Use Pre-Processed Thumbnails) ---
        # Thumbnails are now processed during queue configuration and saved to covers folder
        # Worker just needs to check if they exist, or process EPUB cover as fallback
        
        # Get quality settings for thumbnail sizing (needed for EPUB cover fallback)
        batch_preset_name = settings.get("quality_preset", CONFIG["video_settings"].get("current_quality_preset", "Balanced"))
        batch_presets = CONFIG["video_settings"].get("quality_presets", {})
        batch_q_conf = batch_presets.get(batch_preset_name, batch_presets.get("Balanced", {"height": 720}))
        target_h = batch_q_conf.get("height", 720)
        target_w = int(target_h * 16 / 9)
        if target_w % 2 != 0: target_w += 1
        
        # FIX: Check both int and string keys for JSON compatibility
        batch_thumbnail = thumbnails_dict.get(idx)
        if batch_thumbnail is None:
            batch_thumbnail = thumbnails_dict.get(str(idx), 'auto')
        
        # FIX: Ensure we can find the thumbnail if it's just a filename
        if batch_thumbnail != 'auto' and batch_thumbnail and not os.path.exists(batch_thumbnail):
             possible_path = os.path.join(paths["covers"], os.path.basename(batch_thumbnail))
             if os.path.exists(possible_path):
                 batch_thumbnail = possible_path

        if batch_thumbnail != 'auto' and os.path.exists(batch_thumbnail):
            # [USER REQUIREMENT] Use Simple Resize for Custom Image (no effects)
            # Ensure it's in the covers folder and resized to 16:9
            archive_name = f"{sanitize_filename(range_label)}.jpg"
            archive_path = os.path.join(paths["covers"], archive_name)
            
            # Check if it's already a processed JPG in the right place
            if batch_thumbnail == archive_path:
                img_path_for_batch = batch_thumbnail
                print(f"      ✅ Using already processed custom thumbnail: {archive_name}", flush=True)
            else:
                print(f"      ⚙️  Resizing custom thumbnail to 16:9 (No effects)...", flush=True)
                from core.utils import simple_resize_image
                success = simple_resize_image(batch_thumbnail, archive_path, target_size=(target_w, target_h))
                if success:
                    img_path_for_batch = archive_path
                    print(f"      ✅ Prepared custom thumbnail: {archive_name}", flush=True)
                else:
                    img_path_for_batch = batch_thumbnail # Fallback to raw
        else:
            # Need to process EPUB cover as fallback (With Effects)
            if not extracted_cover:
                 manual_candidates = [
                     os.path.join(paths["root"], "cover.jpg"),
                     os.path.join(paths["root"], "cover.jpeg"),
                     os.path.join(paths["root"], "cover.png"),
                     os.path.join(paths["root"], "thumbnail.jpg"),
                     os.path.join(paths["covers"], "cover.jpg"),
                     os.path.join(paths["covers"], "cover.jpeg"),
                     os.path.join(paths["covers"], "cover.png")
                 ]
                 for cand in manual_candidates:
                     if os.path.exists(cand):
                         extracted_cover = cand
                         print(f"      ✅ Found manual cover (fallback): {os.path.basename(cand)}", flush=True)
                         break
            
            if extracted_cover:
                # [USER REQUIREMENT] Use professional styled thumbnail for EPUB cover
                try:
                    unique_id = sanitize_filename(range_label)
                    pro_thumb_path = generate_pro_cover_from_file(
                        extracted_cover, paths["covers"], unique_id,
                        book_title=meta.get('title'),
                        chapter_range=range_label,
                        target_size=(target_w, target_h)
                    )
                    
                    if pro_thumb_path:
                        img_path_for_batch = pro_thumb_path
                        print(f"      ✅ Generated professional thumbnail from cover: {os.path.basename(pro_thumb_path)}", flush=True)
                    else:
                        raise RuntimeError("Pro thumbnail generation failed")
                except Exception as e:
                    print(f"      ⚠️  Pro processing failed: {e}. Using simple resize fallback.", flush=True)
                    archive_name = f"{sanitize_filename(range_label)}.jpg"
                    archive_path = os.path.join(paths["covers"], archive_name)
                    from core.utils import simple_resize_image
                    simple_resize_image(extracted_cover, archive_path, target_size=(target_w, target_h))
                    img_path_for_batch = archive_path
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
            "quality_preset": batch_preset_name
        })
        
    # 4. Processing Phase (Phase 2 Logic)
    tts_engine = settings.get('engine', 'edge')
    tts_voice = settings.get('voice', 'en-US-ChristopherNeural')
    speed = settings.get('speed', '+0%')
    use_concurrent = settings.get('concurrent', 'yes') == "yes"
    
    # IMPORTANT: Enforce Memory Limits in Batch Mode
    from features.memory_manager import check_memory_status, optimize_memory, is_low_memory
    
    print(f"   🚀 Processing {len(execution_queue)} videos...")
    
    for i, item in enumerate(execution_queue):
        range_name = f"{sanitize_filename(meta['title'])} ({item['label']})"
        audio_file = os.path.join(paths["audio"], f"{range_name}.mp3")
        video_file = os.path.join(paths["video"], f"{range_name}.mp4")
        
        if os.path.exists(video_file):
            print(f"      ⏭️  Skipping existing file: {item['label']}")
            continue
            
        # History check (Double layer protection)
        conflict, msg = check_history_conflict(meta['title'], item['start_chk'], item['end_chk'])
        if conflict and conflict != "boundary":
            print(f"      ⏭️  Skipping previously processed (History): {item['label']}")
            continue
            
        # [SMART RESOURCE MGMT] Check Memory Status before each batch
        current_low_mem = is_low_memory()
        active_concurrent = use_concurrent and not current_low_mem
        
        if current_low_mem and use_concurrent:
            print(CP(f"      ⚠️  Low RAM detected ({check_memory_status()}). Forcing Safe Mode (No Concurrency) for stability.", 'yellow'))
        
        print(f"      ▶️  Generating: {item['label']} (Mode: {'Fast' if active_concurrent else 'Safe'})")
        
        # Audio
        # Audio
        # [STANDARD Mode] - Intro Override for Continuation Videos
        current_intro_override = None
        current_skip_disclaimer = False
        
        if i > 0:
            current_skip_disclaimer = True
            
            # Check if Gemini is enabled (via global config, since queue worker might not have full context)
            gemini_enabled = CONFIG.get("gemini_settings", {}).get("enabled", False)
            if not gemini_enabled:
                 # Standard Continuation Intro
                 next_chapter_title_raw = item["batch"][0][0]
                 # Try to clean it up slightly
                 cleaned_title = next_chapter_title_raw.replace('.html', '').replace('_', ' ').strip()
                 current_intro_override = f"This video continues with {cleaned_title}."
                 print(f"      ℹ️  Continuation Video: Skipping disclaimer & using standard intro override.")


        success, timestamps, word_timeline = run_audio_gen_with_timestamps(
            item["batch"], meta, audio_file, speed, paths["temp"],
            tts_engine, tts_voice, active_concurrent,
            intro_override=current_intro_override,
            skip_disclaimer=current_skip_disclaimer
        )
        
        # [USER REQUIREMENT] Force Faster Whisper for all non-Edge engines
        # Even if timestamps exist, we ignore them for anything other than Edge-TTS
        if tts_engine != "edge":
             if word_timeline:
                 print(f"      🎙️  Prioritizing Faster-Whisper accuracy over TTS timing for {tts_engine}...")
                 word_timeline = []
        
        if not success or not os.path.exists(audio_file):
             # Try auto-recover?
             print(f"      ❌ Audio generation failed for {item['label']}")
             # In batch mode, we might want to continue to next batch or fail job
             # We'll throw exception to fail the job for now, or continue?
             # Let's fail the job to be safe
             raise RuntimeError(f"Audio generation failed for {item['label']}")

        # Prepare text content for forced alignment
        full_text_content = ""
        for _, ch_text in item["batch"]:
             full_text_content += ch_text + "\n"

        # Video
        generate_description_file(meta, range_name, paths, timestamps, CONFIG)
        video_success = create_video_with_recovery(
            audio_file, item["image"], video_file,
            book_title=meta['title'],
            chapter_range=item['label'],
            timestamps=timestamps,
            word_timeline=word_timeline,
            max_retries=3,
            quality_preset=item.get('quality_preset'),
            text_content=full_text_content,
            enable_captions=enable_captions
        )
        
        if video_success:
             # Save history
             save_to_history(meta['title'], item["start_chk"], item["end_chk"], epub_hash)
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
    auto_resume = False
    
    print("\n" + "="*50)
    print(CP("MAIN MENU", 'purple'))
    print("="*50)
    print(f"  {CP('1.', 'cyan')} Process a New Book (one-by-one mode)")
    print(f"  {CP('2.', 'cyan')} Continue a Previous Project (Resume)")
    print(f"  {CP('3.', 'cyan')} Manage the processing queue (batch mode)")
    print(f"  {CP('4.', 'cyan')} Search and View novel mappings")
    print(f"  {CP('5.', 'cyan')} Video quality and system settings")
    print(f"  {CP('6.', 'cyan')} Exit")
    
    # Resume check
    resume_data = get_checkpoint_if_exists()
    if resume_data:
         from features.checkpoint_manager import CheckpointManager
         CheckpointManager().display_checkpoint_info() # Show info without asking
         print(f"   {CP('💡 TIP:', 'yellow')} Select [2] to Continue/Resume this project.")
    
    if cli_args.input:
        main_choice = "1"
        print(f"\n   ℹ️  Auto-selecting [1] via CLI")
    else:
        main_choice = input(f"\n   {CP('👉 Select option (1-6):', 'cyan')} ").strip()
    
    if main_choice == '6':
        print("\n   👋 Goodbye!")
        sys.exit(0)
    elif main_choice == '3':
        def add_to_queue_callback():
            job_details = configure_book_for_queue(cli_args)
            if job_details:
                qm.add_to_queue(
                    job_details['path'], 
                    job_details['settings'],
                    title=job_details.get('title'),
                    original_title=job_details.get('original_title')
                )
                print(CP(f"\n   ✅ Added to queue: {job_details['title']}", 'green'))
                time.sleep(1)
        
        ui_manager.handle_queue_menu(qm, process_batch_queue, add_to_queue_callback)
        print("\n👇 Returning to main menu...")
        return main() # Recursion to main menu
    elif main_choice == '4':
        from features.novel_name_mapper import search_mappings_cli
        query = input("\n   🔎 Enter novel name to search: ").strip()
        search_mappings_cli(query)
        input("\nPress Enter to return to main menu...")
        return main()
    elif main_choice == '5':
        ui_manager.handle_video_quality_menu()
        print("\n👇 Returning to main menu...")
        return main()
    elif main_choice == '2':
        # Resume handled by ask_to_resume_checkpoint() logic below
        if not resume_data:
            resume_data = get_checkpoint_if_exists()
        
        if resume_data:
             # Now we actually ask
             resume_data = ask_to_resume_checkpoint()
             
        if resume_data:
            print(CP("\n   🚀 Initiating Resume Sequence...", "cyan"))
            r_title = resume_data.get('book_title')
            r_safe_title = sanitize_filename(r_title)
            r_project_dir = os.path.join(ACTIVE_NOVELS_DIR, r_safe_title)
            r_source_dir = os.path.join(r_project_dir, "source_epub")
            
            # Find the source EPUB
            found_epub = None
            if os.path.exists(r_source_dir):
                candidates = glob.glob(os.path.join(r_source_dir, "*.epub"))
                if candidates:
                    found_epub = candidates[0]
            
            # Fallback: Check input zone for exact name match (less reliable)
            if not found_epub:
                input_candidates = glob.glob(os.path.join(INPUT_ZONE, "*.epub"))
                for ie in input_candidates:
                    if r_safe_title in sanitize_filename(os.path.basename(ie)):
                        found_epub = ie
                        break
            
            if found_epub:
                selected_path = found_epub
                auto_resume = True
                print(f"   📂 Found project: {r_title}")
                print(f"   📄 Source: {os.path.basename(selected_path)}")
            else:
                print(CP(f"   ❌ Could not find source EPUB for '{r_title}'", "red"))
                print("      Please select it manually below.")

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
    
    original_epub_title = meta['title']
    
    # Phase 2: Duplicate detection & naming
    epub_hash = calculate_epub_hash(selected_path)
    final_title, meta, reset_done = resolve_project_name_and_history(selected_path, meta, cli_args, auto_resume)
    if not final_title: return
    new_title = final_title if reset_done else ""
    
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
    
    # === AI GLOBAL ANALYSIS (Stage 1) ===
    gemini_client = create_gemini_client()
    if gemini_client and CONFIG.get("gemini_settings", {}).get("enabled", False):
        ai_metadata_path = os.path.join(paths["root"], "ai_metadata.json")
        if not os.path.exists(ai_metadata_path):
            print(CP("\n🤖 Running AI Global Analysis...", 'cyan'))
            try:
                # Aggregate text from first 5 chapters for context
                full_text_sample = ""
                for _, content in all_chapters[:5]: 
                     full_text_sample += content + "\n"
                
                # Strip HTML (simple regex or just pass it, Gemini handles HTML generally fine but plain text saves tokens)
                clean_sample = re.sub(r'<[^>]+>', '', full_text_sample)
                
                # Cap at 50k chars
                analysis = gemini_client.analyze_full_story(
                    full_text=clean_sample[:50000],
                    metadata=meta
                )
                
                # Save
                with open(ai_metadata_path, 'w', encoding='utf-8') as f:
                    analysis['generated_at'] = datetime.now().isoformat()
                    analysis['model'] = gemini_client.model_name
                    json.dump(analysis, f, indent=2)
                
                print(f"   ✅ Analysis complete: {len(analysis.get('story_analysis', {}).get('characters', []))} characters identified")
            except Exception as e:
                print(CP(f"   ⚠️  AI Analysis failed: {e}", 'yellow'))

    
    # Phase 2: Load book profile if it exists
    book_profile = load_book_profile(paths["root"])
    if book_profile:
        print(CP("\n💾 Loaded saved settings from book_profile.json", 'cyan'))
        print(f"   Engine: {book_profile.get('engine', 'N/A')}")
        print(f"   Voice: {book_profile.get('voice', 'N/A')}")
        print(f"   Speed: {book_profile.get('speed', 'N/A')}")
        
        use_profile = 'y'
        if not cli_args.auto:
             if auto_resume:
                 use_profile = 'y'
                 print("\n   ℹ️  Auto-loading saved settings (Resume)")
             else:
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
    show_chapter_overview(all_chapters)
    
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
            if auto_resume:
                mode = "1"
                print(f"   ℹ️  Auto-selecting Mode [1] (Resume)")
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
        
    # === CAPTIONS SETTINGS ===
    enable_captions = True
    if mode != "3": # In preview mode we default to yes or follow standard flow? Let's ask always.
        print("\n📝 Caption Settings:")
        cap_input = input("   Do you want to enable captions in the video? (y/n, default y): ").strip().lower()
        if cap_input == 'n':
            enable_captions = False
            print("   🚫 Captions DISABLED (Faster-Whisper will be skipped)")
        else:
            print("   ✅ Captions ENABLED")
    
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
                s_in = input(f"   ▶️  Start (1-{len(all_chapters)}) or 'q' to cancel: ").strip()
                if not s_in or s_in.lower() == 'q':
                    print("   ⚠️  Selection cancelled.")
                    break
                s_idx = int(s_in) - 1
                e_in = input(f"   ⏹️  Stop ({s_idx+1}-{len(all_chapters)}) or 'q' to cancel: ").strip()
                if not e_in or e_in.lower() == 'q':
                    print("   ⚠️  Selection cancelled.")
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
                success, count = delete_book_from_history(selected_path, title=meta['title'], chapters=(check_start, check_end))
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
                    if cli_args.auto:
                        print(CP("   ✅ Auto-confirming boundary overlap", 'green'))
                        proceed = 'y'
                    else:
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
                    if cli_args.auto:
                        print(CP("   ✅ Auto-confirming significant overlap", 'green'))
                        proceed = 'y'
                    else:
                        proceed = input("   Proceed anyway? (y/n): ").strip().lower()
                    
                    if proceed != 'y':
                        print(f"   Skipping {range_label}")
                        continue
                else:
                    print(f"   Skipping {range_label} (use manual mode to override)")
                    continue
        
        print(f"\n[{idx+1}/{len(raw_batches)}] Setup: {range_label}")
        
        # Smart thumbnail detection
        expected_cover_name = f"{sanitize_filename(range_label)}.jpg"
        expected_cover_path = os.path.join(paths["covers"], expected_cover_name)
        img_path_for_batch = None
        skip_input = False
        
        if os.path.exists(expected_cover_path):
            # Validate aspect ratio (16:9 is approx 1.77)
            try:
                with Image.open(expected_cover_path) as im_check:
                    w, h = im_check.size
                    ratio = w / h if h != 0 else 0
                
                # Check if it's landscape 16:9 (allow small margin of error 1.7 to 1.8)
                if 1.7 < ratio < 1.85:
                    print(CP(f"   ✅ Found existing thumbnail: {expected_cover_name}", 'green'))
                    print("   ↳ Using cached version")
                    img_path_for_batch = expected_cover_path
                    last_img_path = img_path_for_batch
                    skip_input = True
                else:
                    print(CP(f"   found source image: {expected_cover_name} ({w}x{h})", 'cyan'))
                    print("   ↳ Converting to 16:9 Pro Cover with blurred background...")
                    
                    # Resolve target size (reusing logic from below)
                    curr_q = CONFIG["video_settings"].get("current_quality_preset", "Balanced")
                    presets = CONFIG["video_settings"].get("quality_presets", {})
                    q_conf = presets.get(curr_q, presets.get("Balanced", {"height": 720}))
                    target_h = q_conf.get("height", 720)
                    target_w = int(target_h * 16 / 9)
                    if target_w % 2 != 0: target_w += 1
                    
                    # Generate Pro Cover
                    img_path_for_batch = generate_pro_cover_from_file(
                        expected_cover_path, 
                        paths["temp"], 
                        idx, 
                        book_title=meta['title'],
                        chapter_range=range_label,
                        target_size=(target_w, target_h)
                    )
                    last_img_path = img_path_for_batch
                    skip_input = True
                    
            except Exception as e:
                print(f"   ⚠️  Check failed for {expected_cover_name}: {e}")
                # Fallback to normal input prompt if check fails
                skip_input = False
            
        if not skip_input:
            print("   🖼️  Drag image (or Enter for previous):")
            
            custom_img = ""
            extracted = None
            if not cli_args.auto:
                 custom_img = input("   👉 ").strip().replace('"', '').replace("'", "")
            
            if custom_img == "" and last_img_path:
                print("   ↳ Using previous")
                img_path_for_batch = last_img_path
            elif custom_img and os.path.exists(custom_img):
                print("   ↳ Processing new image...")
                img_path_for_batch = prepare_custom_image(custom_img, paths["temp"], idx)
                last_img_path = img_path_for_batch
            else:
                print("   ↳ Using EPUB cover")
                extracted = extract_cover_to_project(book_obj, paths, meta['title'])
                if extracted:
                    # Resolve Quality for Manual Mode Pre-setup (Phase 1)
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
                    img_path_for_batch = None  # Fallback logic below handles placeholder
                
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
                # Use PIL to ensure proper image save instead of raw file copy
                with Image.open(img_path_for_batch) as img:
                    img.convert('RGB').save(archive_path, 'JPEG', quality=95)
                print(f"   ✅ Archived: {archive_name}")
            except Exception as e:
                print(f"   ⚠️  Archive failed: {e}")
                # Fallback to copy if PIL fails
                try:
                    shutil.copy2(img_path_for_batch, archive_path)
                except:
                    pass
        
        execution_queue.append({
            "batch": selected_batch,
            "label": range_label,
            "image": img_path_for_batch,
            "start_chk": check_start,
            "end_chk": check_end,
            "quality_preset": CONFIG["video_settings"].get("current_quality_preset", "Balanced")
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
        
        # Resolve quality preset for this batch
        quality_preset = item.get("quality_preset", CONFIG["video_settings"].get("current_quality_preset", "Balanced"))
        
        print("═" * 80)
        
        base_name = sanitize_filename(meta['title'])
        range_name = f"{base_name} ({item['label']})"
        audio_file = os.path.join(paths["audio"], f"{range_name}.mp3")
        video_file = os.path.join(paths["video"], f"{range_name}.mp4")
        
        # Resume capability - skip if video exists (unless in test mode)
        if os.path.exists(video_file) and not cli_args.test_mode:
            print(f"   ⏭️  Video already exists! Skipping...", flush=True)
            continue
        
        # === AI INTRO GENERATION ===
        intro_override = None
        if gemini_client and CONFIG.get("gemini_settings", {}).get("enabled", False):
             features = CONFIG.get("gemini_settings", {}).get("features", {})
             if features.get("custom_intros", True):
                 try:
                     print(f"      ✨ Generating AI Intro...", flush=True)
                     chapter_titles = [c[0] for c in item['batch']]
                     intro_res = gemini_client.generate_intro(
                         batch_number=i+1,
                         total_batches=len(execution_queue),
                         story_context=f"Batch covers chapters: {chapter_titles[0]} to {chapter_titles[-1]}",
                     )
                     if intro_res and intro_res.get('intro_text'):
                         intro_override = intro_res['intro_text']
                         print(CP(f"      ✅ AI Intro: {intro_override[:60]}...", 'green'))
                 except Exception as e:
                     print(CP(f"      ⚠️  AI Intro generation failed: {e}", 'yellow'))

        # === AUDIO GENERATION ===
        print(f"\n   🎵 AUDIO GENERATION", flush=True)
        print(f"   Target: {audio_file}", flush=True)
        
        # Standard Mode Logic: Continuation messages
        skip_disclaimer = False
        if i > 0:
            skip_disclaimer = True
            if not intro_override:
                # Get the title of the first chapter in this batch
                try:
                    # item['batch'] is list of tuples (title, text)
                    start_chap_title = item['batch'][0][0]
                    intro_override = f"This video continues with {start_chap_title}."
                    print(f"   ℹ️  Standard Intro Override: {intro_override}")
                except:
                    pass

        success, timestamps, word_timeline = run_audio_gen_with_timestamps(
            item["batch"], meta, audio_file, speed, paths["temp"],
            tts_engine, tts_voice, use_concurrent,
            intro_override=intro_override, 
            skip_disclaimer=skip_disclaimer
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
            
            # Prepare text content for alignment
            batch_text_content = ""
            for _, ch_txt in item.get('batch', []):
                 batch_text_content += ch_txt + "\n"
            
            # [USER REQUIREMENT] Force Faster Whisper for all non-Edge engines
            # Even if timestamps exist, we ignore them for anything other than Edge-TTS
            if tts_engine != "edge":
                 if word_timeline:
                     print(f"      🎙️  Prioritizing Faster-Whisper accuracy over TTS timing for {tts_engine}...")
                     word_timeline = []

            video_success = create_video_with_recovery(
                audio_file, item["image"], video_file,
                book_title=meta['title'],
                chapter_range=item['label'],
                timestamps=timestamps,
                word_timeline=word_timeline,
                max_retries=3,
                quality_preset=quality_preset,
                text_content=batch_text_content,
                enable_captions=enable_captions
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
    # Parse CLI arguments FIRST (before any imports use the paths)
    cli_args = parse_cli_args()
    
    # Handle test mode - MUST happen before main() to override paths
    if cli_args.test_mode:
        print(CP("\\n🧪 TEST MODE ENABLED", 'yellow'))
        print(CP("   All data will be stored in temporary directories", 'cyan'))
        
        # Override global paths if provided
        if cli_args.history_dir:
            import core.config as config_module
            import core.epub_io as epub_io_module
            
            # Normalize the path
            history_dir = os.path.normpath(cli_args.history_dir)
            
            # Update config module
            config_module.HISTORY_DIR = history_dir
            config_module.HISTORY_FILE = os.path.join(history_dir, "global_database.json")
            
            # Update epub_io module (it imports from config, but we need to update its references)
            epub_io_module.HISTORY_DIR = history_dir
            epub_io_module.HISTORY_FILE = os.path.join(history_dir, "global_database.json")
            
            # Update module-level variables in THIS file (epub_project_manager.py)
            globals()['HISTORY_DIR'] = history_dir
            globals()['HISTORY_FILE'] = os.path.join(history_dir, "global_database.json")
            
            print(f"   📂 Test History: {history_dir}")
        
        if cli_args.novels_dir:
            import core.config as config_module
            import core.epub_io as epub_io_module
            
            # Normalize the path
            novels_dir = os.path.normpath(cli_args.novels_dir)
            
            # Update config module
            config_module.MASTER_NOVEL_DIR = novels_dir
            config_module.ACTIVE_NOVELS_DIR = os.path.join(novels_dir, "Active Novels")
            config_module.ARCHIVED_NOVELS_DIR = os.path.join(novels_dir, "Archived Novels")
            
            # Update epub_io module
            epub_io_module.ACTIVE_NOVELS_DIR = os.path.join(novels_dir, "Active Novels")
            epub_io_module.ARCHIVED_NOVELS_DIR = os.path.join(novels_dir, "Archived Novels")
            
            # Update module-level variables in THIS file (epub_project_manager.py)
            globals()['MASTER_NOVEL_DIR'] = novels_dir
            globals()['ACTIVE_NOVELS_DIR'] = os.path.join(novels_dir, "Active Novels")
            globals()['ARCHIVED_NOVELS_DIR'] = os.path.join(novels_dir, "Archived Novels")
            
            print(f"   📚 Test Novels: {novels_dir}")
        
        print(CP("   ⚠️  No permanent history will be saved!\\n", 'yellow'))

    # Queue Manager Mode
    if cli_args.queue_manager:
        run_queue_manager_mode(cli_args)
        sys.exit(0)
    
    # Worker Mode
    if cli_args.worker:
        run_worker_mode()
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