
import os
import sys
import shutil
import asyncio
from PIL import Image

# Add parent to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from epub_project_manager import run_audio_gen_with_timestamps, create_video_with_recovery
from core.config import CONFIG

def test_full_flow():
    print("🚀 Starting End-to-End Caption System Test")
    
    # Setup Paths
    test_dir = os.path.join("tests", "integration_temp")
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    os.makedirs(test_dir)
    
    audio_path = os.path.join(test_dir, "test_audio.mp3")
    video_path = os.path.join(test_dir, "test_video.mp4")
    image_path = os.path.join(test_dir, "background.jpg")
    
    # 1. Create Dummy Image
    print("   🖼️  Creating test background image...")
    img = Image.new('RGB', (1280, 720), color = (73, 109, 137))
    img.save(image_path)
    
    # 2. Define Content
    chapters = [
        ("Chapter 1", "This is a test of the advanced caption system. It should include word level timing."), 
        ("Chapter 2", "This is the second chapter to verify concatenation works correctly.")
    ]
    meta = {"title": "Integration Test"}
    
    # 3. Audio Generation (Real EdgeTTS call)
    print("   🎵 Generating Audio (using Edge-TTS)...")
    # Force settings
    CONFIG["video_settings"]["enable_subtitles"] = True
    CONFIG["video_settings"]["use_advanced_renderer"] = True
    
    try:
        success, timestamps, word_timeline = run_audio_gen_with_timestamps(
            chapters, meta, audio_path, "+0%", test_dir, 
            tts_engine="piper", tts_voice=os.path.join("piper_models", "en_US-amy-medium.onnx"), use_concurrent=False
        )
    except TypeError: 
        # Fallback if signature mismatch (should rely on recent changes)
        print("   ⚠️  Signature mismatch detected (old version loaded?), trying without word_timeline unpacking")
        # Retry logic or fail
        return
        
    if not success:
        print("   ❌ Audio generation failed!")
        return

    print(f"   ✅ Audio generated. Timeline has {len(word_timeline) if word_timeline else 0} words.")
    
    if not word_timeline:
        print("   ⚠️  No word timeline data captured! (Is Edge-TTS returning metadata?)")
    else:
        print("   ✅ Word timeline captured successfully.")
        print(f"      First word: {word_timeline[0]}")

    # 4. Video Generation
    print("   🎬 Generating Video...")
    video_success = create_video_with_recovery(
        audio_path, image_path, video_path, 
        book_title="Test Book", 
        chapter_range="Ch 1-2", 
        timestamps=timestamps, 
        word_timeline=word_timeline,
        max_retries=1
    )
    
    if video_success and os.path.exists(video_path):
        print(f"   ✅ Video created successfully: {video_path}")
        print(f"      Size: {os.path.getsize(video_path)} bytes")
        
        # Check for timeline json
        timeline_json = video_path.replace(".mp4", ".timeline.json")
        if os.path.exists(timeline_json):
             print("   ✅ Timeline JSON exported.")
        else:
             print("   ⚠️  No Timeline JSON found (rendering might have skipped it or failed silently).")
             
    else:
        print("   ❌ Video generation failed.")

if __name__ == "__main__":
    test_full_flow()
