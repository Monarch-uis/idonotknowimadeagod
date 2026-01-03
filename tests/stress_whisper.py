
import os
import sys
import logging
import time
import subprocess
from core.caption_client import generate_word_timestamps, is_available

# Configure logging
logging.basicConfig(level=logging.INFO)

def create_dummy_file(filename, size=0):
    with open(filename, 'wb') as f:
        f.write(b'\0' * size)
    return filename

def create_silence(filename, duration=1):
    # Use ffmpeg to create silence
    cmd = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=24000:cl=mono",
        "-t", str(duration), "-q:a", "9", "-acodec", "libmp3lame", filename
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return filename

def create_speech(filename, text="Hello world this is a test."):
    cmd = [
        "edge-tts", "--text", text, "--write-media", filename
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return filename

def run_test(name, test_func):
    print(f"\n🧪 TEST: {name}")
    try:
        test_func()
        print(f"   ✅ PASS")
    except Exception as e:
        print(f"   ❌ FAIL: {e}")
        # print stack trace?
        import traceback
        traceback.print_exc()

def test_missing_file():
    print("   Testing non-existent file...")
    try:
        generate_word_timestamps("non_existent_ghost.mp3")
        raise RuntimeError("Should have failed")
    except FileNotFoundError:
        print("   ✅ Properly caught FileNotFoundError")

def test_empty_file():
    print("   Testing 0-byte file...")
    fname = "test_empty.mp3"
    create_dummy_file(fname)
    try:
        generate_word_timestamps(fname)
        raise RuntimeError("Should have failed")
    except ValueError as e:
        print(f"   ✅ Properly caught ValueError: {e}")
    except Exception as e:
        print(f"   ⚠️  Caught unexpected exception: {type(e).__name__}: {e}")
    finally:
        if os.path.exists(fname): os.remove(fname)

def test_silence():
    print("   Testing silence (1s)...")
    fname = "test_silence.mp3"
    create_silence(fname, duration=2)
    try:
        words = generate_word_timestamps(fname)
        print(f"   Result: {words}")
        # Expecting either empty list or error
    except ValueError as e:
        print(f"   ✅ Properly caught ValueError (no words): {e}")
    finally:
        if os.path.exists(fname): os.remove(fname)

def test_valid_speech():
    print("   Testing valid speech...")
    fname = "test_speech.mp3"
    create_speech(fname, "This is a robust system test.")
    try:
        words = generate_word_timestamps(fname)
        if len(words) > 0:
            print(f"   ✅ Success: Extracted {len(words)} words: {[w['text'] for w in words]}")
        else:
            raise RuntimeError("Failed to extract words from valid speech")
    finally:
        if os.path.exists(fname): os.remove(fname)

def main():
    print("🚀 STARTING WHISPER ROBUSTNESS TEST")
    if not is_available():
        print("❌ Faster-Whisper NOT available. Skipping tests.")
        return

    run_test("Missing File", test_missing_file)
    run_test("Empty File", test_empty_file)
    run_test("Silence", test_silence)
    run_test("Valid Speech", test_valid_speech)

if __name__ == "__main__":
    main()
