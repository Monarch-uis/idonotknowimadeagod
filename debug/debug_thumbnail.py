"""
Debug script to test thumbnail generation in isolation.
Run this to verify if the thumbnail generation works correctly.
"""
import os
import sys
from PIL import Image, ImageFilter, ImageDraw, ImageFont

def test_thumbnail_generation(cover_path, output_path):
    """Test thumbnail generation with detailed logging"""
    print(f"\n=== THUMBNAIL DEBUG TEST ===")
    print(f"Input: {cover_path}")
    print(f"Output: {output_path}")
    
    # Step 1: Check input file
    if not os.path.exists(cover_path):
        print(f"ERROR: Input file does not exist!")
        return False
    
    print(f"Input file size: {os.path.getsize(cover_path)} bytes")
    
    # Step 2: Open and verify the image
    try:
        original_img = Image.open(cover_path)
        print(f"Original mode: {original_img.mode}")
        print(f"Original size: {original_img.size}")
        
        # Check if image has content
        extrema = original_img.getextrema()
        print(f"Extrema (min/max values): {extrema}")
        
        # Convert and copy
        original = original_img.convert("RGB").copy()
        original_img.close()
        print(f"After convert+copy - size: {original.size}, mode: {original.mode}")
        
    except Exception as e:
        print(f"ERROR opening image: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Create background
    W, H = 1280, 720
    print(f"\nTarget size: {W}x{H}")
    
    try:
        bg_aspect = original.width / original.height
        bg_new_height = int(W / bg_aspect)
        print(f"BG aspect: {bg_aspect:.2f}, new height: {bg_new_height}")
        
        background = original.resize((W, max(bg_new_height, H)), Image.Resampling.LANCZOS).copy()
        print(f"Background after resize: {background.size}")
        
        left = (background.width - W) // 2
        top = (background.height - H) // 2
        background = background.crop((int(left), int(top), int(left + W), int(top + H)))
        print(f"Background after crop: {background.size}")
        
        background = background.filter(ImageFilter.GaussianBlur(20))
        print(f"Background after blur: {background.size}")
        
        # Check background content
        bg_extrema = background.getextrema()
        print(f"Background extrema: {bg_extrema}")
        
    except Exception as e:
        print(f"ERROR creating background: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Create foreground
    try:
        target_h = int(H * 0.90)
        ratio = target_h / original.height
        target_w = int(original.width * ratio)
        sharp = original.resize((target_w, target_h), Image.Resampling.LANCZOS)
        print(f"Sharp foreground: {sharp.size}")
        
        x = (W - target_w) // 2
        y = (H - target_h) // 2
        print(f"Paste position: ({x}, {y})")
        
        # Convert background to RGBA for compositing
        background = background.convert("RGBA")
        
        # Paste foreground
        sharp_rgba = sharp.convert("RGBA")
        background.paste(sharp_rgba, (x, y), sharp_rgba)
        print(f"After paste: {background.size}, mode: {background.mode}")
        
    except Exception as e:
        print(f"ERROR creating foreground: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 5: Save
    try:
        final_rgb = background.convert("RGB")
        print(f"Final image: {final_rgb.size}, mode: {final_rgb.mode}")
        
        # Check final content
        final_extrema = final_rgb.getextrema()
        print(f"Final extrema: {final_extrema}")
        
        # Check if image is blank (all channels have same min/max = solid color)
        is_blank = all(e[0] == e[1] for e in final_extrema)
        if is_blank:
            print("WARNING: Final image appears to be a solid color (blank)!")
        
        final_rgb.save(output_path, 'JPEG', quality=95)
        print(f"Saved to: {output_path}")
        print(f"Output file size: {os.path.getsize(output_path)} bytes")
        
        # Cleanup
        original.close()
        background.close()
        final_rgb.close()
        
    except Exception as e:
        print(f"ERROR saving: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n=== TEST COMPLETE ===")
    return True


if __name__ == "__main__":
    # Check for command line argument first
    if len(sys.argv) > 1:
        cover_path = sys.argv[1]
        output = os.path.join(os.path.dirname(cover_path) or ".", "DEBUG_THUMBNAIL_TEST.jpg")
        test_thumbnail_generation(cover_path, output)
    else:
        # Try to find a cover image automatically
        test_folders = [
            r"C:\Users\DIBAKAR\desktop\idonotknowimadeagod\Novels\Active Novels",
            r"C:\Users\DIBAKAR\desktop\idonotknowimadeagod",
        ]
        
        cover_found = None
        for folder in test_folders:
            if os.path.exists(folder):
                for root, dirs, files in os.walk(folder):
                    for f in files:
                        if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                            cover_found = os.path.join(root, f)
                            break
                    if cover_found:
                        break
            if cover_found:
                break
        
        if cover_found:
            output = os.path.join(os.path.dirname(cover_found), "DEBUG_THUMBNAIL_TEST.jpg")
            test_thumbnail_generation(cover_found, output)
        else:
            print("No image found to test with!")
            print("Please provide a path as argument:")
            print(f"  python {sys.argv[0]} <path_to_cover_image>")
