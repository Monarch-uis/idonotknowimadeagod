#!/usr/bin/env python3
"""
FFMPEG Diagnostic Script
Tests if FFMPEG is properly installed with H.264 codec support
"""

import subprocess
import sys
import os

def test_ffmpeg_basic():
    """Test if ffmpeg command exists"""
    print("=" * 60)
    print("TEST 1: FFMPEG Command Availability")
    print("=" * 60)
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            print("✅ FFMPEG is installed")
            print(f"Version: {result.stdout.split('\\n')[0]}")
            assert True
        else:
            print("❌ FFMPEG command failed")
            assert False, "FFMPEG command failed"
    except FileNotFoundError:
        print("❌ FFMPEG not found in PATH")
        print("   Install from: https://www.gyan.dev/ffmpeg/builds/")
        assert False, "FFMPEG not found in PATH"
    except Exception as e:
        print(f"❌ Error: {e}")
        assert False, f"Unexpected error: {e}"

def test_h264_codec():
    """Test if H.264 codec is available"""
    print("\n" + "=" * 60)
    print("TEST 2: H.264 Codec Availability")
    print("=" * 60)
    try:
        result = subprocess.run(['ffmpeg', '-codecs'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if 'libx264' in result.stdout:
            print("✅ libx264 encoder is available")
            # Extract the h264 line
            for line in result.stdout.split('\n'):
                if 'h264' in line.lower() and 'H.264' in line:
                    print(f"   {line.strip()}")
            assert True
        else:
            print("❌ libx264 encoder NOT found")
            print("   You need the FULL build of FFMPEG, not essentials")
            assert False, "libx264 encoder not found"
    except Exception as e:
        print(f"❌ Error checking codecs: {e}")
        assert False, f"Error checking codecs: {e}"

def test_imageio_ffmpeg():
    """Test if imageio-ffmpeg (MoviePy's fallback) works"""
    print("\n" + "=" * 60)
    print("TEST 3: imageio-ffmpeg (MoviePy's FFMPEG)")
    print("=" * 60)
    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        ffmpeg_path = get_ffmpeg_exe()
        print(f"✅ imageio-ffmpeg found at: {ffmpeg_path}")
        
        # Test if it has libx264
        result = subprocess.run([ffmpeg_path, '-codecs'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if 'libx264' in result.stdout:
            print("✅ imageio-ffmpeg has libx264 support")
            assert True
        else:
            print("⚠️  imageio-ffmpeg exists but lacks libx264")
            assert False, "imageio-ffmpeg exists but lacks libx264"
    except ImportError:
        print("❌ imageio-ffmpeg not installed")
        print("   Install: pip install imageio-ffmpeg")
        assert False, "imageio-ffmpeg not installed"
    except Exception as e:
        print(f"❌ Error: {e}")
        assert False, f"Unexpected error: {e}"

def test_moviepy():
    """Test if MoviePy can access FFMPEG"""
    print("\n" + "=" * 60)
    print("TEST 4: MoviePy Integration")
    print("=" * 60)
    try:
        from moviepy.config import get_setting
        ffmpeg_binary = get_setting("FFMPEG_BINARY")
        print(f"✅ MoviePy FFMPEG binary: {ffmpeg_binary}")
        assert True
    except Exception as e:
        print(f"⚠️  MoviePy config issue: {e}")
        assert False, f"MoviePy config issue: {e}"

def main():
    print("\n🔍 FFMPEG DIAGNOSTIC TOOL\n")
    
    results = {
        "FFMPEG Command": test_ffmpeg_basic(),
        "H.264 Codec": test_h264_codec(),
        "imageio-ffmpeg": test_imageio_ffmpeg(),
        "MoviePy": test_moviepy()
    }
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    print("\n" + "=" * 60)
    
    if all(results.values()):
        print("🎉 All tests passed! Your FFMPEG is properly configured.")
    else:
        print("⚠️  Some tests failed. See FFMPEG_FIX.md for solutions.")
        print("\nQuick fix: Install full FFMPEG build from:")
        print("https://www.gyan.dev/ffmpeg/builds/")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
