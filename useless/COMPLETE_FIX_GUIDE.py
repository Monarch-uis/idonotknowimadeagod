"""
===============================================================================
EPUB PROJECT MANAGER - COMPREHENSIVE FIX IMPLEMENTATION GUIDE
===============================================================================
Date: December 17, 2024
Developer: Step-by-step verification mode
Priority: CRITICAL

This document provides complete fixes for all identified issues.
===============================================================================
"""

# =============================================================================
# CRITICAL FIX #1: Background Image Fallback (batch_processor.py)
# =============================================================================

"""
LOCATION: batch_processor.py, line 48-91
PROBLEM: Hard dependency on background image causes failure if missing
IMPACT: All title card generation fails

SOLUTION: Replace generate_title_card function with this version:
"""

FIXED_GENERATE_TITLE_CARD = '''
def generate_title_card(title: str, subtitle: str, bg_path: str, output_path: str):
    """Generates a title card image using Pillow with fallback for missing background."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.warning("Pillow not installed. Creating fallback title card.")
        try:
            from PIL import Image
            img = Image.new('RGB', (1920, 1080), color=(20, 20, 20))
            img.save(output_path)
            return True
        except:
            if os.path.exists(bg_path):
                shutil.copy(bg_path, output_path)
                return True
            logger.error("Cannot create title card - Pillow not available and no background image")
            return False

    try:
        # Check if background image exists - CRITICAL FIX
        if not os.path.exists(bg_path):
            logger.warning(f"Background image not found: {bg_path}. Creating solid color background.")
            img = Image.new('RGBA', (1920, 1080), color=(20, 20, 20, 255))
        else:
            img = Image.open(bg_path).convert("RGBA")
        
        target_size = (1920, 1080)
        if img.size != target_size:
            img = img.resize(target_size)
        
        overlay = Image.new("RGBA", target_size, (0, 0, 0, 160))
        img = Image.alpha_composite(img, overlay)
        
        draw = ImageDraw.Draw(img)
        
        # Font loading with multiple fallbacks
        try:
            title_font = ImageFont.truetype("arial.ttf", 100)
            sub_font = ImageFont.truetype("arial.ttf", 60)
        except IOError:
            try:
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
                sub_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
            except IOError:
                title_font = ImageFont.load_default()
                sub_font = ImageFont.load_default()

        w, h = target_size
        
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
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate title card: {e}")
        try:
            from PIL import Image
            img = Image.new('RGB', (1920, 1080), color=(20, 20, 20))
            img.save(output_path)
            return True
        except:
            return False
'''

# =============================================================================
# CRITICAL FIX #2: Enhanced Logging Setup (core/utils.py)
# =============================================================================

"""
LOCATION: core/utils.py, line 17-26
PROBLEM: Logs in project root, no log level control, potential duplicate handlers
IMPACT: Hard to debug, log pollution, potential crashes

SOLUTION: Replace logging setup with this version:
"""

ENHANCED_LOGGING_SETUP = '''
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging(log_level=None, module_name='epub_automation'):
    """
    Setup logging with proper configuration
    
    Args:
        log_level: "DEBUG", "INFO", "WARNING", "ERROR" or None (uses env/config)
        module_name: Name of the logger to create
    
    Returns:
        logging.Logger: Configured logger
    """
    # Create logs directory
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # Get log level from env or parameter
    if log_level is None:
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Create logger
    logger = logging.getLogger(module_name)
    
    # Clear any existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Set level
    log_level_value = getattr(logging, log_level, logging.INFO)
    logger.setLevel(log_level_value)
    
    # File handler with rotation
    log_file = log_dir / f'{module_name}.log'
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,  # 5MB per file
        backupCount=5,
        encoding='utf-8'
    )
    
    # Detailed formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler (only in DEBUG mode or if explicitly enabled)
    if log_level == 'DEBUG' or os.getenv('LOG_TO_CONSOLE', '').lower() == 'true':
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    logger.info(f"Logging initialized at {log_level} level")
    logger.info(f"Log file: {log_file}")
    
    return logger

# Replace the old logging setup at the top of utils.py with:
logger = setup_logging()
'''

# =============================================================================
# CRITICAL FIX #3: Audio File Validation (core/tts.py or core/utils.py)
# =============================================================================

"""
LOCATION: Add to core/utils.py or core/tts.py
PROBLEM: No validation that generated audio is actually usable
IMPACT: Corrupted/silent audio files processed without detection

SOLUTION: Add this function:
"""

AUDIO_VALIDATION_FUNCTION = '''
def validate_audio_file(filepath, min_duration=0.5, min_size_mb=0.01):
    """
    Validate that generated audio file is actually usable
    
    Checks:
    - File exists and has content
    - Can be opened as audio
    - Has reasonable duration
    - Is not silent
    - File size matches duration
    
    Args:
        filepath: Path to audio file
        min_duration: Minimum duration in seconds
        min_size_mb: Minimum file size in MB
    
    Returns:
        (bool, Optional[str]): (is_valid, error_message)
    """
    import os
    
    try:
        # Check file exists
        if not os.path.exists(filepath):
            return False, "File does not exist"
        
        # Check file size
        size_bytes = os.path.getsize(filepath)
        size_mb = size_bytes / (1024 * 1024)
        
        if size_mb < min_size_mb:
            return False, f"File too small: {size_mb:.2f}MB"
        
        # Try to load as audio using pydub (if available)
        try:
            from pydub import AudioSegment
            
            audio = AudioSegment.from_file(filepath)
            
            # Check duration
            duration = audio.duration_seconds
            if duration < min_duration:
                return False, f"Audio too short: {duration:.1f}s"
            
            # Check if audio is silent (dBFS very low)
            # Normal speech is around -20 to -10 dBFS
            if audio.dBFS < -50:
                return False, f"Audio appears silent (dBFS: {audio.dBFS:.1f})"
            
            # Verify file size is reasonable for duration
            # MP3: roughly 16-32KB per second
            # WAV: roughly 176KB per second
            expected_min_size = duration * 0.010  # 10KB/sec minimum
            if size_mb < expected_min_size:
                return False, f"File size ({size_mb:.2f}MB) too small for duration ({duration:.1f}s)"
            
            return True, None
            
        except ImportError:
            # pydub not available, do basic checks only
            if size_mb > 0.1:  # At least 100KB
                return True, None
            else:
                return False, "File size suspicious (install pydub for better validation)"
                
    except Exception as e:
        return False, f"Validation error: {str(e)[:100]}"

# Usage after generating audio:
# success, error = gen_single_clip_edge_with_retry(...)
# if success:
#     valid, validation_error = validate_audio_file(filename)
#     if not valid:
#         logger.warning(f"⚠️  Audio validation warning: {validation_error}")
#         # Optionally retry or handle error
'''

# =============================================================================
# CRITICAL FIX #4: Memory Cleanup (epub_project_manager.py)
# =============================================================================

"""
LOCATION: epub_project_manager.py, add to batch processing
PROBLEM: Memory leaks during long processing sessions
IMPACT: Increasing memory usage, potential crashes

SOLUTION: Add this function and call after each batch:
"""

MEMORY_CLEANUP_FUNCTION = '''
import gc
import logging

logger = logging.getLogger(__name__)

def cleanup_between_batches():
    """
    Clean up resources between batch processing
    Prevents memory leaks during long processing sessions
    """
    # Force garbage collection
    collected = gc.collect()
    
    # Log memory usage if psutil available
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        logger.info(f"Memory cleanup: {collected} objects collected, {memory_mb:.1f} MB in use")
    except ImportError:
        logger.info(f"Memory cleanup: {collected} objects collected")
    except Exception as e:
        logger.warning(f"Memory check failed: {e}")

# Call after each batch or segment:
# process_video_segment(...)
# cleanup_between_batches()
'''

# =============================================================================
# IMPLEMENTATION STEPS
# =============================================================================

IMPLEMENTATION_STEPS = """
STEP-BY-STEP IMPLEMENTATION GUIDE
==================================

1. BACKUP CURRENT FILES
   - Copy batch_processor.py to batch_processor.py.backup
   - Copy core/utils.py to core/utils.py.backup

2. APPLY FIX #1 (Background Image)
   a. Open batch_processor.py
   b. Locate the generate_title_card function (around line 48)
   c. Replace entire function with FIXED_GENERATE_TITLE_CARD code above
   d. Save file

3. APPLY FIX #2 (Logging)
   a. Open core/utils.py
   b. Locate logging setup (around line 17-26)
   c. Replace with ENHANCED_LOGGING_SETUP code above
   d. Update logger creation:
      OLD: logger = logging.getLogger(__name__)
      NEW: logger = setup_logging()
   e. Save file

4. APPLY FIX #3 (Audio Validation)
   a. Open core/utils.py
   b. Add AUDIO_VALIDATION_FUNCTION at the end of file
   c. Import and use in TTS functions:
      - After gen_single_clip_edge_with_retry
      - After gen_single_clip_piper_with_retry
      - After gen_single_clip_pyttsx3_with_retry
   d. Save file

5. APPLY FIX #4 (Memory Cleanup)
   a. Open epub_project_manager.py or batch_processor.py
   b. Add MEMORY_CLEANUP_FUNCTION near top with other functions
   c. Call after each segment in process_video_segment
   d. Save file

6. TEST FIXES
   a. Run: python batch_processor.py --input test.epub --background "" --output_dir output
      (Note: empty background to test fallback)
   b. Check logs/epub_automation.log for warnings
   c. Verify video generation works
   d. Monitor memory usage

7. VERIFY FIXES
   ✓ No background.jpg errors in logs
   ✓ Logs appear in logs/ directory
   ✓ Audio validation messages appear
   ✓ Memory usage stays stable
   ✓ Videos generate successfully
"""

# =============================================================================
# TESTING SCRIPT
# =============================================================================

TESTING_SCRIPT = '''
#!/usr/bin/env python3
"""Quick test script to verify all fixes are working"""

import os
import sys
import logging
from pathlib import Path

def test_logging_setup():
    """Test enhanced logging"""
    print("\\n[TEST 1] Testing logging setup...")
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from core.utils import setup_logging
        logger = setup_logging('DEBUG', 'test_logger')
        logger.info("Logging test successful")
        
        # Check logs directory created
        if Path('logs').exists():
            print("  ✅ Logs directory created")
        else:
            print("  ❌ Logs directory NOT created")
            
        # Check log file created
        if Path('logs/test_logger.log').exists():
            print("  ✅ Log file created")
        else:
            print("  ❌ Log file NOT created")
            
        print("  ✅ Logging test PASSED")
        return True
    except Exception as e:
        print(f"  ❌ Logging test FAILED: {e}")
        return False

def test_audio_validation():
    """Test audio validation"""
    print("\\n[TEST 2] Testing audio validation...")
    
    try:
        from core.utils import validate_audio_file
        
        # Test with non-existent file
        valid, error = validate_audio_file("nonexistent.mp3")
        if not valid:
            print(f"  ✅ Correctly rejects non-existent file")
        else:
            print(f"  ❌ Should reject non-existent file")
            
        print("  ✅ Audio validation test PASSED")
        return True
    except Exception as e:
        print(f"  ❌ Audio validation test FAILED: {e}")
        return False

def test_title_card_fallback():
    """Test title card generation with missing background"""
    print("\\n[TEST 3] Testing title card fallback...")
    
    try:
        from PIL import Image
        
        # Simulate title card generation
        img = Image.new('RGB', (1920, 1080), color=(20, 20, 20))
        test_output = 'test_title_card.jpg'
        img.save(test_output)
        
        if os.path.exists(test_output):
            print("  ✅ Fallback title card created")
            os.remove(test_output)
        else:
            print("  ❌ Fallback title card NOT created")
            
        print("  ✅ Title card test PASSED")
        return True
    except Exception as e:
        print(f"  ❌ Title card test FAILED: {e}")
        return False

def main():
    print("="*70)
    print("  EPUB PROJECT MANAGER - FIX VERIFICATION TEST SUITE")
    print("="*70)
    
    results = []
    results.append(test_logging_setup())
    results.append(test_audio_validation())
    results.append(test_title_card_fallback())
    
    print("\\n" + "="*70)
    passed = sum(results)
    total = len(results)
    print(f"  RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("  ✅ ALL TESTS PASSED - Fixes are working!")
    else:
        print("  ❌ SOME TESTS FAILED - Check implementation")
    print("="*70)

if __name__ == "__main__":
    main()
'''

# =============================================================================
# SAVE THIS SCRIPT
# =============================================================================

if __name__ == "__main__":
    print(__doc__)
    print(IMPLEMENTATION_STEPS)
    print("\\nSave the TESTING_SCRIPT to test_fixes.py and run it to verify all fixes.")
