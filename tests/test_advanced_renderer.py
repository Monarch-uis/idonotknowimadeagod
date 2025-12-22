import sys
import os

# Test 1: Check faster-whisper
print("=" * 60)
print("TEST 1: faster-whisper availability")
print("=" * 60)
try:
    from faster_whisper import WhisperModel
    print("✅ faster-whisper imported successfully")
    
    # Try to create a model
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    print("✅ WhisperModel created successfully")
except Exception as e:
    print(f"❌ faster-whisper error: {e}")

# Test 2: Check subprocess FFmpeg
print("\n" + "=" * 60)
print("TEST 2: FFmpeg subprocess")
print("=" * 60)
try:
    import subprocess
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ FFmpeg subprocess works")
        print(f"   Version: {result.stdout.split()[2]}")
    else:
        print(f"❌ FFmpeg failed: {result.stderr}")
except Exception as e:
    print(f"❌ Subprocess error: {e}")

# Test 3: Check config
print("\n" + "=" * 60)
print("TEST 3: Config settings")
print("=" * 60)
try:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from core.config import load_config
    config = load_config()
    
    use_advanced = config.get("video_settings", {}).get("use_advanced_renderer", False)
    enable_subs = config.get("video_settings", {}).get("enable_subtitles", False)
    
    print(f"use_advanced_renderer: {use_advanced}")
    print(f"enable_subtitles: {enable_subs}")
    
    if use_advanced and enable_subs:
        print("✅ Config is correct for advanced rendering")
    else:
        print("❌ Config issue detected")
except Exception as e:
    print(f"❌ Config error: {e}")

# Test 4: Try importing render function
print("\n" + "=" * 60)
print("TEST 4: Import render_video_with_timeline")
print("=" * 60)
try:
    from core.video_pipeline import render_video_with_timeline
    print("✅ render_video_with_timeline imported successfully")
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
