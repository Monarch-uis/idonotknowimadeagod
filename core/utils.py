"""
Utility functions module
Helper functions, notifications, logging setup, text processing
"""
import os
import sys
import time
import string
import re
import logging
from logging.handlers import RotatingFileHandler
from datetime import timedelta
try:
    import PIL.Image
    if not hasattr(PIL.Image, 'ANTIALIAS'):
        PIL.Image.ANTIALIAS = PIL.Image.LANCZOS
except ImportError:
    pass

# Setup logging with rotation (2MB × 3 backups)
log_handler = RotatingFileHandler(
    'logs/epub_automation.log',
    maxBytes=2*1024*1024,  # 2MB
    backupCount=3
)
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(log_handler)
logger.addHandler(logging.StreamHandler())  # Also log to console

# === COLOR SYSTEM ===
os.system("")  # Makes colors work on Windows

def CP(text, color='white'):
    """Color Print - makes text colorful"""
    colors = {
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'purple': '\033[95m',
        'white': '\033[97m',
    }
    end = '\033[0m'
    return colors.get(color, '') + text + end

def beep_notification():
    """Cross-platform completion sound"""
    try:
        import platform
        system = platform.system()
        if system == "Windows":
            import winsound
            winsound.Beep(1000, 200)
            time.sleep(0.1)
            winsound.Beep(800, 200)
            time.sleep(0.1)
            winsound.Beep(1200, 400)
        elif system == "Darwin":  # macOS
            os.system('afplay /System/Library/Sounds/Ping.aiff')
        else:  # Linux
            os.system('paplay /usr/share/sounds/freedesktop/stereo/bell.oga 2>/dev/null || echo -e "\a"')
    except Exception as e:
        print(f"⚠️  Notification failed: {e}")

def play_critical_failure_alarm():
    """Urgent alarm for critical failures"""
    try:
        import platform
        system = platform.system()
        if system == "Windows":
            import winsound
            for _ in range(3):
                winsound.Beep(1500, 300)
                time.sleep(0.1)
        elif system == "Darwin":
            os.system('afplay /System/Library/Sounds/Sosumi.aiff')
        else:
            for _ in range(3):
                print('\a', end='', flush=True)
                time.sleep(0.3)
    except:
        pass
    
    print("\n" + "🚨" * 20)
    print("      CRITICAL FAILURE - ATTENTION REQUIRED")
    print("🚨" * 20 + "\n")

def sanitize_filename(name, max_length=200):
    """
    Properly sanitize filename for all platforms including Unicode
    
    Handles:
    - Unicode characters (Chinese, Japanese, etc.)
    - Path separators
    - Windows reserved names
    - Control characters
    - Problematic characters
    """
    if not name:
        return "untitled"
    
    # Imports inside function to avoid circular imports if any
    import unicodedata
    from pathlib import Path
    
    # Normalize Unicode to standard form
    name = unicodedata.normalize('NFKC', name)
    
    # Remove or replace path separators
    name = name.replace('/', '_').replace('\\', '_')
    
    # Remove control characters (but keep printable Unicode)
    name = ''.join(c for c in name 
                   if not unicodedata.category(c).startswith('C'))
    
    # Replace Windows/filesystem problematic characters
    # Keep Unicode letters/numbers but replace these special chars
    name = re.sub(r'[<>:"|?*]', '_', name)
    
    # Handle Windows reserved names (CON, PRN, AUX, etc.)
    reserved = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    name_upper = name.upper()
    base_name = name_upper.split('.')[0]
    if base_name in reserved:
        name = f"_{name}"
    
    # Remove leading/trailing spaces and dots (Windows doesn't allow)
    name = name.strip('. ')
    
    # Truncate if too long (but preserve extension)
    if len(name) > max_length:
        path_obj = Path(name)
        stem = path_obj.stem
        suffix = path_obj.suffix
        
        # Calculate how much to keep
        available = max_length - len(suffix) - 1  # -1 for the dot
        if available > 0:
            name = stem[:available] + suffix
        else:
            name = stem[:max_length]
    
    # Final safety check
    if not name or name in ('.', '..'):
        return "untitled"
    
    return name

def seconds_to_time_str(seconds):
    """Convert seconds to HH:MM:SS format"""
    return str(timedelta(seconds=int(seconds)))

def extract_smart_number(text):
    """Extract chapter number from text"""
    if not text:
        return None
    try:
        match = re.search(r"(?:Chapter|Ch|Episode|Ep|c)\.?\s*(\d+)", text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        match_start = re.match(r"\s*(\d+)", text)
        if match_start:
            return int(match_start.group(1))
        nums = re.findall(r"\d+", text)
        if nums:
            return int(nums[-1])
    except (ValueError, IndexError):
        pass
    return None

def censor_text(text, banned_words):
    """Remove banned words from text (for TTS audio)"""
    if not text:
        return ""
    clean_text = text
    for pattern in banned_words:
        try:
            clean_text = re.sub(pattern, "...", clean_text, flags=re.IGNORECASE)
        except re.error:
            pass
    return clean_text

def partial_censor_word(word):
    """Censor word keeping first and last letter visible
    Examples:
        fuck -> f**k
        fucking -> f**king
        shit -> s**t
        bitch -> b**ch
    """
    if len(word) <= 2:
        return '*' * len(word)
    elif len(word) == 3:
        return word[0] + '*' + word[-1]
    else:
        # Keep first letter, censor middle, keep last letter
        middle_length = len(word) - 2
        return word[0] + ('*' * min(middle_length, 2)) + word[-1]

def censor_text_for_subtitles(text, banned_words):
    """Censor text with partial masking for better readability in subtitles
    
    Examples:
        "fuck" -> "f**k"
        "fucking" -> "f**king" 
        "shit" -> "s**t"
        "motherfucker" -> "m**ker"
    
    Args:
        text: Text to censor
        banned_words: List of regex patterns to censor
        
    Returns:
        Partially censored text
    """
    if not text:
        return ""
    
    clean_text = text
    
    for pattern in banned_words:
        try:
            # Find all matches
            matches = list(re.finditer(pattern, clean_text, flags=re.IGNORECASE))
            
            # Process matches in reverse to maintain indices
            for match in reversed(matches):
                matched_word = match.group(0)
                censored_word = partial_censor_word(matched_word)
                
                # Replace the matched word with censored version
                start, end = match.span()
                clean_text = clean_text[:start] + censored_word + clean_text[end:]
                
        except re.error:
            pass
    
    return clean_text

def fix_pronunciation(text, pronunciation_fixes):
    """Fix pronunciation of specific words"""
    if not text:
        return ""
    fixed_text = text
    for word, replacement in pronunciation_fixes.items():
        pattern = r"\b" + re.escape(word) + r"\b"
        fixed_text = re.sub(pattern, replacement, fixed_text, flags=re.IGNORECASE)
    return fixed_text

def generate_smart_tags(title, summary, fandom_tags):
    """Generate hashtags based on content"""
    text_to_scan = (title + " " + summary).lower()
    tags = ["#Audiobook", "#WebNovel", "#FanFiction"]
    for key, values in fandom_tags.items():
        if key in text_to_scan:
            tags.extend(values)
    unique_tags = list(set(tags))
    return " ".join(unique_tags)

def simple_resize_image(input_path, output_path, target_size=(1280, 720)):
    """Simple resize and center-crop without any effects/blur"""
    from PIL import Image
    try:
        with Image.open(input_path) as img:
            img = img.convert("RGB")
            W, H = target_size
            
            # 1. Resize maintaining aspect ratio to cover the target area
            img_aspect = img.width / img.height
            target_aspect = W / H
            
            if img_aspect > target_aspect:
                # Image is wider than target
                new_h = H
                new_w = int(H * img_aspect)
            else:
                # Image is taller than target
                new_w = W
                new_h = int(W / img_aspect)
                
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # 2. Center crop
            left = (img.width - W) // 2
            top = (img.height - H) // 2
            img = img.crop((left, top, left + W, top + H))
            
            # 3. Save
            img.save(output_path, "JPEG", quality=95)
            return True
    except Exception as e:
        logger.error(f"Simple resize failed: {e}")
        return False

