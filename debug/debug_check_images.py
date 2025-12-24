"""
Debug script to trace thumbnail source during actual execution.
Run this to understand which images are being used as source.
"""
import os
from PIL import Image

def check_images_in_folder(folder_path):
    """Check all images in a folder for blank/solid colors"""
    print(f"\n=== CHECKING IMAGES IN: {folder_path} ===\n")
    
    if not os.path.exists(folder_path):
        print(f"Folder does not exist!")
        return
    
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            filepath = os.path.join(folder_path, filename)
            try:
                img = Image.open(filepath)
                extrema = img.getextrema()
                size = img.size
                mode = img.mode
                
                # Check if image is solid color (blank)
                is_blank = False
                if mode == 'RGB':
                    is_blank = all(e[0] == e[1] for e in extrema)
                elif mode == 'RGBA':
                    is_blank = all(e[0] == e[1] for e in extrema[:3])
                elif mode == 'L':
                    is_blank = extrema[0] == extrema[1]
                
                status = "🔴 BLANK" if is_blank else "✅ OK"
                print(f"{status} | {filename} | {size[0]}x{size[1]} | {mode}")
                if is_blank:
                    print(f"       Extrema: {extrema}")
                
                img.close()
            except Exception as e:
                print(f"❌ ERROR | {filename} | {e}")

if __name__ == "__main__":
    import sys
    
    # Check various folders
    base = r"C:\Users\DIBAKAR\desktop\idonotknowimadeagod\Novels\Active Novels\Naruto_ F__king Makes Me Stronger"
    
    folders_to_check = [
        base,
        os.path.join(base, "cover_images"),
        os.path.join(base, "temp"),
    ]
    
    for folder in folders_to_check:
        if os.path.exists(folder):
            check_images_in_folder(folder)
    
    # Also check the project root
    check_images_in_folder(r"C:\Users\DIBAKAR\desktop\idonotknowimadeagod")
