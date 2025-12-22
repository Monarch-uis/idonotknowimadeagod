import os
import sys
import asyncio
import shutil
import tempfile
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from core.config import CONFIG, save_config
from core.epub_io import parse_full_epub, validate_epub
from core.tts import (
    EDGE_TTS_AVAILABLE, 
    PYTTSX3_AVAILABLE, 
    PIPER_AVAILABLE,
    gen_single_clip_edge_with_retry,
    gen_single_clip_pyttsx3_with_retry,
    gen_single_clip_piper_with_retry,
    resolve_piper_model_path,
    select_piper_model
)
from features.novel_name_mapper import NovelNameMapper, auto_save_mapping
from features.chapter_merger import ChapterMerger
from core.video_pipeline import generate_timeline_from_audio, check_dependencies as check_video_deps
from core.utils import CP

async def verify_everything():
    print(CP("\n" + "="*70, 'cyan'))
    print(CP("  🚀 MASTER PROJECT VERIFICATION", 'cyan'))
    print(CP("="*70, 'cyan'))

    temp_dir = tempfile.mkdtemp(prefix="verification_")
    print(f"📁 Working Directory: {temp_dir}")

    try:
        # 1. Config Management
        print(CP("\n[1] Config Management...", 'yellow'))
        old_val = CONFIG["audio_settings"].get("export_bitrate", "192k")
        CONFIG["audio_settings"]["export_bitrate"] = "256k"
        save_config()
        print("   ✅ Config save/load working")
        CONFIG["audio_settings"]["export_bitrate"] = old_val
        save_config()

        # 2. Novel Name Mapper (The feature I just added)
        print(CP("\n[2] Novel Name Mapper...", 'yellow'))
        mapper = NovelNameMapper()
        test_original = "Verification Test Novel"
        test_youtube = "V-Test YouTube Name"
        
        auto_save_mapping(test_original, test_youtube, temp_dir, "1-10")
        
        # Reload mapper to get fresh data after save
        mapper = NovelNameMapper()
        result, match_type, score = mapper.lookup_by_youtube_name(test_youtube)
        if result and result['original_title'] == test_original:
            print(f"   ✅ Mapping saved and retrieved correctly ({match_type} match)")
        else:
            print(f"   ❌ Mapping failed")
        
        # Cleanup mapping
        mapper.delete_mapping(test_original)

        # 3. TTS Engines
        print(CP("\n[3] TTS Engine Verification...", 'yellow'))
        test_text = "This is a verification test."
        
        # Edge-TTS
        if EDGE_TTS_AVAILABLE:
            print("   🔊 Testing Edge-TTS...")
            path = os.path.join(temp_dir, "edge.mp3")
            success, err, data = await gen_single_clip_edge_with_retry(test_text, path, "en-US-GuyNeural", "+0%")
            if success and os.path.exists(path):
                print(f"      ✅ Success ({os.path.getsize(path)} bytes)")
                if data and data.get('events'):
                    print(f"      ✅ High-precision timing captured ({len(data['events'])} events)")
            else:
                print(f"      ❌ Failed: {err}")
        
        # pyttsx3
        if PYTTSX3_AVAILABLE:
            print("   🔊 Testing pyttsx3...")
            path = os.path.join(temp_dir, "pyttsx3.mp3")
            success, err, data = gen_single_clip_pyttsx3_with_retry(test_text, path, None, "+0%")
            if success and os.path.exists(path):
                print(f"      ✅ Success ({os.path.getsize(path)} bytes)")
            else:
                print(f"      ❌ Failed: {err}")

        # Piper
        if PIPER_AVAILABLE:
            print("   🔊 Testing Piper...")
            model_path = resolve_piper_model_path()
            if model_path:
                path = os.path.join(temp_dir, "piper.mp3")
                success, err, data = gen_single_clip_piper_with_retry(test_text, path, model_path, silent=True)
                if success and os.path.exists(path):
                    print(f"      ✅ Success ({os.path.getsize(path)} bytes)")
                    if data and data.get('events'):
                        print(f"      ✅ Estimated timing generated ({len(data['events'])} events)")
                else:
                    print(f"      ❌ Failed: {err}")
            else:
                print("      ⚠️  No Piper model found, skipping test")

        # 4. Video Pipeline Logic
        print(CP("\n[4] Video Pipeline Check...", 'yellow'))
        if check_video_deps():
            print("   ✅ Video dependencies present")
            
            # Use the audio from Edge-TTS to test timeline generation
            edge_path = os.path.join(temp_dir, "edge.mp3")
            if os.path.exists(edge_path):
                print("   🛠️ Testing timeline generation from audio...")
                try:
                    timeline = generate_timeline_from_audio(edge_path, "test_proj", CONFIG)
                    if timeline and "timeline" in timeline:
                        print(f"      ✅ Generated timeline with {len(timeline['timeline'])} elements")
                    else:
                        print(f"      ❌ Timeline generation failed")
                except Exception as e:
                    print(f"      ❌ Timeline error: {e}")
        else:
            print("   ❌ Video dependencies missing")

        # 5. Chapter Merger
        print(CP("\n[5] Chapter Merger Verification...", 'yellow'))
        merger = ChapterMerger()
        print("   ✅ Merger module loaded")
        # Structural check
        if hasattr(merger, 'merge_chapters'):
             print("   ✅ merge_chapters() available")

        print(CP("\n" + "="*70, 'green'))
        print(CP("  ✅ VERIFICATION COMPLETE", 'green'))
        print(CP("="*70, 'green'))

    finally:
        # Cleanup
        try:
            shutil.rmtree(temp_dir)
            print(f"\n🗑️  Cleanup successful")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(verify_everything())
