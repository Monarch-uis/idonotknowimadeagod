from PIL import Image

# --- MONKEY PATCH ---
try:
    if not hasattr(Image, 'ANTIALIAS'):
        print("🔧 Applying ANTIALIAS monkey patch...")
        Image.ANTIALIAS = Image.LANCZOS
except Exception as e:
    print(f"Patch failed: {e}")
# --------------------

try:
    print(f"Pillow version: {Image.__version__}")
    
    try:
        val = Image.ANTIALIAS
        print(f"✅ Image.ANTIALIAS is present (Value: {val})")
    except AttributeError:
        print("❌ Image.ANTIALIAS remains MISSING")
        
    # Test MoviePy resize
    from moviepy.editor import ColorClip
    clip = ColorClip(size=(100, 100), color=(255, 0, 0), duration=1)
    
    print("Testing resize...")
    clip_resized = clip.resize(width=50) 
    print("✅ MoviePy resize successful")
    
except Exception as e:
    print(f"❌ Detailed Error: {e}")
