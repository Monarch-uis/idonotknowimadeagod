"""
FIXED: generate_title_card function with background image fallback
--------------------------------------------------------------
This patch adds proper error handling for missing background images.
"""

def generate_title_card(title: str, subtitle: str, bg_path: str, output_path: str):
    """Generates a title card image using Pillow with fallback for missing background."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.warning("Pillow not installed. Creating fallback title card.")
        # Create simple fallback if Pillow not available
        try:
            from PIL import Image
            img = Image.new('RGB', (1920, 1080), color=(20, 20, 20))
            img.save(output_path)
        except:
            # Last resort - copy background if exists
            if os.path.exists(bg_path):
                shutil.copy(bg_path, output_path)
            else:
                logger.error("Cannot create title card - Pillow not available and no background image")
                return False
        return True

    try:
        # Check if background image exists
        if not os.path.exists(bg_path):
            logger.warning(f"Background image not found: {bg_path}. Creating solid color background.")
            img = Image.new('RGBA', (1920, 1080), color=(20, 20, 20, 255))
        else:
            img = Image.open(bg_path).convert("RGBA")
        
        # Resize to 1920x1080 if needed
        target_size = (1920, 1080)
        if img.size != target_size:
            img = img.resize(target_size)
        
        # Add dark overlay
        overlay = Image.new("RGBA", target_size, (0, 0, 0, 160))
        img = Image.alpha_composite(img, overlay)
        
        draw = ImageDraw.Draw(img)
        
        # Load fonts - try default system fonts
        try:
            title_font = ImageFont.truetype("arial.ttf", 100)
            sub_font = ImageFont.truetype("arial.ttf", 60)
        except IOError:
            try:
                # Try other common font locations
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
                sub_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
            except IOError:
                title_font = ImageFont.load_default()
                sub_font = ImageFont.load_default()

        # Draw Title
        w, h = target_size
        
        # Simple centering logic
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
        # Fallback - create simple solid background
        try:
            from PIL import Image
            img = Image.new('RGB', (1920, 1080), color=(20, 20, 20))
            img.save(output_path)
            return True
        except:
            return False
