try:
    from moviepy.editor import AudioFileClip
    print("✅ MoviePy 1.x style import successful")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("   This confirms MoviePy 2.x is installed and incompatible with current code.")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
