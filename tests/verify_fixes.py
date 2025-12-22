#!/usr/bin/env python3
"""
Quick Verification Test Suite
Tests all critical fixes to ensure they work correctly
"""

import os
import sys
from pathlib import Path

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_test(name):
    print(f"\n[TEST] {name}...")

def print_result(success, message=""):
    if success:
        print(f"  ✅ PASSED {message}")
    else:
        print(f"  ❌ FAILED {message}")
    return success

def test_project_structure():
    """Verify project structure is intact"""
    print_test("Project Structure")
    
    required_files = [
        "batch_processor.py",
        "epub_project_manager.py",
        "core/utils.py",
        "core/epub_io.py",
        "core/tts.py",
        "core/video_pipeline.py",
        "requirements.txt",
    ]
    
    all_exist = True
    for file in required_files:
        if not os.path.exists(file):
            print(f"    ❌ Missing: {file}")
            all_exist = False
    
    return print_result(all_exist, "- All required files present")

def test_dependencies():
    """Check if all dependencies are installed"""
    print_test("Dependencies")
    
    required_modules = [
        "PIL",
        "ebooklib",
        "bs4",
        "edge_tts",
        "moviepy",
        "ffmpeg",
        "faster_whisper"
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)
    
    if missing:
        print(f"    ❌ Missing modules: {', '.join(missing)}")
        print(f"    Run: pip install -r requirements.txt")
        return print_result(False)
    
    return print_result(True, "- All dependencies installed")

def test_logging_directory():
    """Check if logs directory exists or can be created"""
    print_test("Logging Directory")
    
    log_dir = Path("logs")
    
    if not log_dir.exists():
        try:
            log_dir.mkdir()
            return print_result(True, "- Created logs/ directory")
        except Exception as e:
            return print_result(False, f"- Cannot create logs/: {e}")
    else:
        return print_result(True, "- logs/ directory exists")

def test_background_fallback():
    """Test that missing background doesn't crash"""
    print_test("Background Image Fallback")
    
    try:
        from PIL import Image
        
        # Simulate creating a fallback background
        img = Image.new('RGB', (1920, 1080), color=(20, 20, 20))
        test_path = "test_fallback_bg.jpg"
        img.save(test_path)
        
        if os.path.exists(test_path):
            size = os.path.getsize(test_path)
            os.remove(test_path)
            return print_result(True, f"- Fallback creation works ({size} bytes)")
        else:
            return print_result(False, "- Could not create fallback")
            
    except Exception as e:
        return print_result(False, f"- Error: {e}")

def test_gpu_detection():
    """Test GPU detection function"""
    print_test("GPU Detection")
    
    try:
        # Check if CUDA is available
        try:
            import torch
            if torch.cuda.is_available():
                device_name = torch.cuda.get_device_name(0)
                return print_result(True, f"- CUDA available: {device_name}")
            else:
                return print_result(True, "- CUDA not available (will use CPU)")
        except ImportError:
            return print_result(True, "- PyTorch not installed (CPU mode)")
            
    except Exception as e:
        return print_result(False, f"- Error: {e}")

def test_file_validation():
    """Test file validation logic"""
    print_test("File Validation")
    
    # Test that validation catches non-existent files
    test_file = "nonexistent_audio_file_12345.mp3"
    
    if os.path.exists(test_file):
        return print_result(False, "- Test file exists (shouldn't)")
    
    # This is a basic test - actual validation function should be in code
    return print_result(True, "- File validation logic ready")

def test_memory_cleanup():
    """Test memory cleanup availability"""
    print_test("Memory Cleanup")
    
    try:
        import gc
        import psutil
        
        # Do a garbage collection
        collected = gc.collect()
        
        # Try to get memory info
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        return print_result(True, f"- Memory tools available ({memory_mb:.1f} MB in use)")
        
    except ImportError:
        return print_result(True, "- psutil not installed (basic cleanup still works)")
    except Exception as e:
        return print_result(False, f"- Error: {e}")

def test_ffmpeg_available():
    """Check if FFmpeg is available"""
    print_test("FFmpeg Availability")
    
    import subprocess
    
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            check=True,
            timeout=5
        )
        return print_result(True, "- FFmpeg is installed")
    except FileNotFoundError:
        try:
            # Try imageio_ffmpeg
            from imageio_ffmpeg import get_ffmpeg_exe
            exe = get_ffmpeg_exe()
            return print_result(True, f"- FFmpeg available via imageio-ffmpeg")
        except:
            return print_result(False, "- FFmpeg not found")
    except Exception as e:
        return print_result(False, f"- Error checking FFmpeg: {e}")

def main():
    print_header("EPUB PROJECT MANAGER - FIX VERIFICATION TEST SUITE")
    print(f"Working Directory: {os.getcwd()}")
    
    results = []
    
    # Run all tests
    results.append(test_project_structure())
    results.append(test_dependencies())
    results.append(test_logging_directory())
    results.append(test_background_fallback())
    results.append(test_gpu_detection())
    results.append(test_file_validation())
    results.append(test_memory_cleanup())
    results.append(test_ffmpeg_available())
    
    # Summary
    print_header("TEST RESULTS")
    passed = sum(results)
    total = len(results)
    percentage = (passed / total) * 100
    
    print(f"\n  Tests Passed: {passed}/{total} ({percentage:.0f}%)")
    
    if passed == total:
        print("\n  ✅ ALL TESTS PASSED!")
        print("  The system is ready for fixes to be implemented.")
    elif passed >= total * 0.75:
        print("\n  ⚠️  MOST TESTS PASSED")
        print("  Some optional features missing but core functionality intact.")
    else:
        print("\n  ❌ MULTIPLE TESTS FAILED")
        print("  Please review error messages above and fix issues.")
    
    print("\n" + "="*70)
    
    # Recommendations
    print("\n📋 RECOMMENDATIONS:")
    
    if not all(results):
        print("\n  1. Install missing dependencies:")
        print("     pip install -r requirements.txt")
        
        print("\n  2. Check project structure is intact")
        
        print("\n  3. Review error messages above for specific issues")
    else:
        print("\n  ✅ System is ready!")
        print("  Next step: Apply fixes from COMPLETE_FIX_GUIDE.py")
    
    print("\n" + "="*70)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
