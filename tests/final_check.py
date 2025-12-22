import sys
import os

print("Testing critical imports...")

try:
    print("1. Testing MoviePy...")
    from moviepy.editor import AudioFileClip, VideoFileClip
    print("   ✅ MoviePy imported")
except Exception as e:
    print(f"   ❌ MoviePy failed: {e}")

try:
    print("2. Testing Edge-TTS...")
    import edge_tts
    print("   ✅ Edge-TTS imported")
except Exception as e:
    print(f"   ❌ Edge-TTS failed: {e}")

try:
    print("3. Testing Faster-Whisper...")
    from faster_whisper import WhisperModel
    print("   ✅ Faster-Whisper imported")
except Exception as e:
    print(f"   ❌ Faster-Whisper failed: {e}")

try:
    print("4. Testing Pillow...")
    from PIL import Image, ImageDraw, ImageFont
    print("   ✅ Pillow imported")
except Exception as e:
    print(f"   ❌ Pillow failed: {e}")

print("\nImport test complete.")
