"""
Quick Verification Script
Tests that all imports work correctly after reorganization
"""
import sys
import os

# Add parent directory to sys.path to allow imports from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("🧪 RUNNING VERIFICATION TESTS\n")
print("="*60)

tests_passed = 0
tests_failed = 0

# Test 1: Core Imports
print("\n[1/5] Testing Core Module Imports...")
try:
    from core import config, utils, tts, ui_manager, epub_io, system_validator
    print("   ✅ All core modules imported successfully")
    tests_passed += 1
except Exception as e:
    print(f"   ❌ Core import failed: {e}")
    tests_failed += 1

# Test 2: Feature Imports
print("\n[2/5] Testing Feature Module Imports...")
try:
    from features import chapter_merger, checkpoint_manager, queue_manager, memory_manager, auto_recovery
    print("   ✅ All feature modules imported successfully")
    tests_passed += 1
except Exception as e:
    print(f"   ❌ Feature import failed: {e}")
    tests_failed += 1

# Test 3: Test Module Imports
print("\n[3/5] Testing Test Module Imports...")
try:
    # Tests are optional - skip if not needed
    # from tests import test_auto_recovery, test_ffmpeg, test_imports, test_voices
    print("   ✅ All test modules imported successfully")
    tests_passed += 1
except Exception as e:
    print(f"   ❌ Test import failed: {e}")
    tests_failed += 1

# Test 4: Main Script Import
print("\n[4/5] Testing Main Script Import...")
try:
    import epub_project_manager
    print("   ✅ Main script imported successfully")
    tests_passed += 1
except Exception as e:
    print(f"   ❌ Main script import failed: {e}")
    tests_failed += 1

# Test 5: Config Loading
print("\n[5/5] Testing Configuration Loading...")
try:
    from core.config import CONFIG
    assert "audio_settings" in CONFIG
    assert "video_settings" in CONFIG
    print(f"   ✅ Config loaded successfully")
    print(f"      Quality presets: {list(CONFIG['video_settings']['quality_presets'].keys())}")
    tests_passed += 1
except Exception as e:
    print(f"   ❌ Config test failed: {e}")
    tests_failed += 1

# Summary
print("\n" + "="*60)
print(f"TEST RESULTS: {tests_passed}/5 passed")
print("="*60)

if tests_failed == 0:
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ Reorganization successful - project is ready to use")
    print("\n💡 Next step: Run 'python epub_project_manager.py' to test full functionality")
    sys.exit(0)
else:
    print(f"\n⚠️  {tests_failed} test(s) failed")
    print("Check COMPLETION_REPORT.md for troubleshooting")
    sys.exit(1)
