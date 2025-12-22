
import os
import sys
import subprocess
import json
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.utils import CP, logger
from core.video_pipeline import _escape_ffmpeg_path
from features.chapter_merger import ChapterMerger
from features.queue_manager import QueueManager, QUEUE_FILE

def test_ffmpeg_path_escaping():
    print("\n   [Test] FFmpeg Path Escaping...")
    # Windows paths with backslashes and colons are tricky in FFmpeg filters
    test_path = "C:\\Users\\Test User\\Documents\\file.jpg"
    escaped = _escape_ffmpeg_path(test_path)
    
    # In FFmpeg filters (DrawText/Subtitles), ':' needs escaping if it's not a drive letter,
    # and '\' needs escaping as '\\' or '/' needs to be used.
    # Our implementation uses .replace("\\", "/").replace(":", "\\:")
    print(f"      Original: {test_path}")
    print(f"      Escaped:  {escaped}")
    
    assert "/" in escaped or "\\\\" in escaped
    assert "\\:" in escaped
    print(CP("      ✅ Passed: FFmpeg Path Escaping", 'green'))

def test_chapter_merger_optimization():
    print("\n   [Test] ChapterMerger Optimization...")
    merger = ChapterMerger(min_word_count=100)
    
    # Test word count speed/accuracy
    text = "Word " * 50000 
    import time
    start = time.time()
    count = merger.estimate_word_count(text)
    duration = time.time() - start
    
    print(f"      Word count (50k): {count} in {duration:.4f}s")
    assert count == 50000
    assert duration < 0.1 # Should be very fast
    print(CP("      ✅ Passed: ChapterMerger Optimization", 'green'))

def test_queue_manager_lock_safety():
    print("\n   [Test] QueueManager Lock Safety...")
    qm = QueueManager()
    
    # Test if we can acquire lock multiple times sequentially (should work as we close it)
    try:
        # Creating a dummy queue file
        with open(QUEUE_FILE, 'w') as f:
            json.dump([], f)
            
        qm.save_queue()
        qm.save_queue()
        print(CP("      ✅ Passed: QueueManager Atomic/Locking", 'green'))
    except Exception as e:
        print(f"      ❌ Failed: {e}")
        raise
    finally:
        if os.path.exists(QUEUE_FILE): os.remove(QUEUE_FILE)
        if os.path.exists(QUEUE_FILE + ".lock"): os.remove(QUEUE_FILE + ".lock")

if __name__ == "__main__":
    print(CP("🚀 Starting Audit Fix Verification", 'cyan'))
    try:
        test_ffmpeg_path_escaping()
        test_chapter_merger_optimization()
        test_queue_manager_lock_safety()
        print(CP("\n✅ ALL AUDIT TESTS PASSED!", 'green'))
    except Exception as e:
        print(CP(f"\n❌ AUDIT TEST FAILED: {e}", 'red'))
        import traceback
        traceback.print_exc()
        sys.exit(1)
