#!/usr/bin/env python3
"""
Quick Import Test - Verify all imports work
"""
import traceback

print("Testing imports...")
failures = []

try:
    import os
    print("✅ os")
except:
    print("❌ os")
    failures.append("os")

try:
    import sys
    print("✅ sys")
except:
    print("❌ sys")
    failures.append("sys")

try:
    import hashlib
    print("✅ hashlib")
except:
    print("❌ hashlib")
    failures.append("hashlib")

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    print("✅ PIL (Image, ImageDraw, ImageFont, ImageFilter)")
except Exception as e:
    print(f"❌ PIL: {e}")
    failures.append("PIL")

try:
    from moviepy.editor import AudioFileClip, ImageClip, CompositeAudioClip, concatenate_audioclips
    print("✅ moviepy")
except Exception as e:
    print(f"❌ moviepy: {e}")
    failures.append("moviepy")

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
    print("✅ ebooklib & beautifulsoup4")
except Exception as e:
    print(f"❌ ebooklib/bs4: {e}")
    failures.append("ebooklib/bs4")

try:
    import psutil
    print("✅ psutil (RAM monitoring)")
except:
    print("⚠️  psutil (optional - for RAM monitoring)")
    # Optional, don't add to failures

print("\n" + "="*50)
if failures:
    print(f"❌ FAILED IMPORTS: {', '.join(failures)}")
    print("="*50)
    raise ImportError(f"Missing modules: {', '.join(failures)}")
else:
    print("Import test complete!")
    print("="*50)

# Try importing the main script
print("\nTesting main script import...")
try:

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import epub_project_manager
    print("✅ epub_project_manager imports successfully!")
except Exception as e:
    print(f"❌ epub_project_manager import failed:")
    print(f"   {e}")
    traceback.print_exc()
    raise ImportError(f"epub_project_manager failed to import: {e}")
