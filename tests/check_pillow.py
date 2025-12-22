from PIL import Image
try:
    # This checks if ANTIALIAS is available (removed in Pillow 10)
    # MoviePy 1.0.3 uses Image.ANTIALIAS
    print(f"Pillow version: {Image.__version__}")
    
    try:
        _ = Image.ANTIALIAS
        print("✅ Image.ANTIALIAS is present.")
    except AttributeError:
        print("❌ Image.ANTIALIAS is MISSING (This will break MoviePy 1.0.3)")
        
    # Test MoviePy resize (which uses ANTIALIAS)
    from moviepy.editor import ColorClip
    clip = ColorClip(size=(100, 100), color=(255, 0, 0), duration=1)
    
    print("Testing resize...")
    # This typically triggers the ANTIALIAS error
    clip_resized = clip.resize(width=50) 
    print("✅ MoviePy resize successful")
    
except Exception as e:
    print(f"❌ Detailed Error: {e}")
