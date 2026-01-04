"""
EPUB I/O module
Handles EPUB parsing, history management, book profiles, and duplicate detection
"""
import os
import json
import re
import hashlib
import atexit
import shutil
import time
from datetime import datetime
import logging

try:
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ Missing libraries. Run: pip install ebooklib beautifulsoup4")
    exit(1)

from core.config import HISTORY_DIR, HISTORY_FILE, ACTIVE_NOVELS_DIR, ARCHIVED_NOVELS_DIR
from core.utils import sanitize_filename, CP, logger

def setup_global_input(input_zone, master_novel_dir, active_novels_dir, archived_novels_dir):
    """Create base directory structure"""
    dirs_to_create = [input_zone, master_novel_dir, active_novels_dir, archived_novels_dir]
    for d in dirs_to_create:
        try:
            os.makedirs(d, exist_ok=True)
        except OSError as e:
            logger.error(f"Directory creation failed for {d}: {e}")

def cleanup_temp_dir(temp_path):
    """Cleanup temp directory on exit"""
    try:
        if os.path.exists(temp_path):
            time.sleep(0.5)
            shutil.rmtree(temp_path)
            logger.info(f"Cleaned up temp: {temp_path}")
    except OSError as e:
        logger.warning(f"Temp cleanup failed: {e}")

def setup_project_folders(book_title, active_novels_dir):
    """Create project folder structure"""
    safe_title = sanitize_filename(book_title)
    base_path = os.path.join(os.getcwd(), active_novels_dir, safe_title)
    paths = {
        "root": base_path,
        "epub": os.path.join(base_path, "source_epub"),
        "audio": os.path.join(base_path, "audio"),
        "video": os.path.join(base_path, "youtubevideo"),
        "covers": os.path.join(base_path, "cover_images"),
        "desc": os.path.join(base_path, "description"),
        "temp": os.path.join(base_path, "temp_render_files")
    }
    for key, path in paths.items():
        try:
            os.makedirs(path, exist_ok=True)
        except OSError as e:
            logger.error(f"Project folder creation failed for {key}: {e}")
    atexit.register(cleanup_temp_dir, paths["temp"])
    return paths

def load_history():
    """Load processing history"""
    if not os.path.exists(HISTORY_DIR):
        try:
            os.makedirs(HISTORY_DIR, exist_ok=True)
        except OSError:
            return {}
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError, IOError) as e:
        logger.error(f"History load failed: {e}")
        return {}

def save_to_history(book_title, start_chap, end_chap, epub_hash=None):
    """Save processed range to history"""
    key = sanitize_filename(book_title)
    history = load_history()
    if key not in history:
        history[key] = []
    entry = {
        "start": int(start_chap),
        "end": int(end_chap),
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "title": book_title
    }
    if epub_hash:
        entry["epub_hash"] = epub_hash
    history[key].append(entry)
    try:
        if not os.path.exists(HISTORY_DIR):
            os.makedirs(HISTORY_DIR)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4)
        print(f"   📝 History updated: Ch {start_chap}-{end_chap}", flush=True)
        logger.info(f"Saved history for {book_title}")
    except (OSError, IOError) as e:
        logger.error(f"History save failed: {e}")

def calculate_epub_hash(epub_path):
    """Calculate SHA256 hash of EPUB file for duplicate detection"""
    try:
        hash_sha256 = hashlib.sha256()
        with open(epub_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    except Exception as e:
        logger.error(f"EPUB hash calculation failed: {e}")
        return None

def check_duplicate_epub(epub_path):
    """Check if EPUB was already processed using hash"""
    epub_hash = calculate_epub_hash(epub_path)
    if not epub_hash:
        return None
    
    history = load_history()
    for book_key, entries in history.items():
        # Check if ANY entry for this book matches the hash
        hash_match = False
        for entry in entries:
            if entry.get("epub_hash") == epub_hash:
                hash_match = True
                break
        
        if hash_match:
            # Aggregate all stats for this book
            min_start = float('inf')
            max_end = -1
            latest_date = "1970-01-01"
            title = book_key
            
            for entry in entries:
                # Update title to latest if available
                if entry.get("title"):
                    title = entry.get("title")
                
                # Update date
                e_date = entry.get("date", "1970-01-01")
                if e_date > latest_date:
                    latest_date = e_date
                
                # Update ranges
                try:
                    s = int(entry.get("start", 0))
                    e = int(entry.get("end", 0))
                    if s < min_start: min_start = s
                    if e > max_end: max_end = e
                except:
                    pass

            if min_start == float('inf'): min_start = "?"
            if max_end == -1: max_end = "?"
            
            return {
                "key": book_key,
                "title": title,
                "date": latest_date,
                "start": min_start,
                "end": max_end
            }
    return None

def get_history_summary(search_title):
    """Search history by title and return aggregated summary"""
    history = load_history()
    search_key = sanitize_filename(search_title)
    
    # Try exact key match first
    if search_key in history:
        entries = history[search_key]
        min_start = float('inf')
        max_end = -1
        latest_date = "1970-01-01"
        title = search_title
        
        for entry in entries:
            if entry.get("title"): title = entry.get("title")
            e_date = entry.get("date", "1970-01-01")
            if e_date > latest_date: latest_date = e_date
            try:
                s, e = int(entry.get("start", 0)), int(entry.get("end", 0))
                if s < min_start: min_start = s
                if e > max_end: max_end = e
            except: pass
            
        return {
            "key": search_key, "title": title, "date": latest_date,
            "start": min_start if min_start != float('inf') else "?",
            "end": max_end if max_end != -1 else "?"
        }
        
    # Try fuzzy title match
    for book_key, entries in history.items():
        if not entries: continue
        # Check title of first entry as representative
        if search_title.lower() in entries[0].get('title', '').lower():
            min_start = float('inf')
            max_end = -1
            latest_date = "1970-01-01"
            title = entries[0].get('title', book_key)
            
            for entry in entries:
                e_date = entry.get("date", "1970-01-01")
                if e_date > latest_date: latest_date = e_date
                try:
                    s, e = int(entry.get("start", 0)), int(entry.get("end", 0))
                    if s < min_start: min_start = s
                    if e > max_end: max_end = e
                except: pass
                
            return {
                "key": book_key, "title": title, "date": latest_date,
                "start": min_start if min_start != float('inf') else "?",
                "end": max_end if max_end != -1 else "?"
            }
            
    return None

def delete_book_from_history(epub_path, title=None, chapters=None):
    """
    Remove entry from history.
    If chapters is None: removes all entries for this book.
    If chapters is (start, end): removes only overlapping ranges.
    Matches by epub_hash (primary) or title (fallback).
    Returns: (bool, int) - (Success, number of entries removed)
    """
    epub_hash = calculate_epub_hash(epub_path) if epub_path else None
    
    history = load_history()
    removed_count = 0
    updated_history = {}
    
    # Target title for fallback matching
    target_key = sanitize_filename(title) if title else None
    
    for book_key, entries in history.items():
        new_entries = []
        # book_key is the sanitized title in our history structure
        title_matches = (target_key and book_key == target_key)
        
        for entry in entries:
            # Check if this entry matches by hash or title
            hash_matches = (epub_hash and entry.get("epub_hash") == epub_hash)
            
            if hash_matches or title_matches:
                if chapters is None:
                    # Full book reset - remove this entry
                    removed_count += 1
                    continue
                else:
                    # Partial reset - check for overlap
                    new_start, new_end = chapters
                    old_start = int(entry.get("start", 0))
                    old_end = int(entry.get("end", 0))
                    
                    # Overlap if max(start) <= min(end)
                    if max(new_start, old_start) <= min(new_end, old_end):
                        removed_count += 1
                        continue # Skip (remove) this entry
            
            new_entries.append(entry)
            
        if new_entries:
            updated_history[book_key] = new_entries
            
    if removed_count > 0:
        try:
            if not os.path.exists(HISTORY_DIR):
                os.makedirs(HISTORY_DIR)
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(updated_history, f, indent=4)
            logger.info(f"Removed {removed_count} history entries (Hash: {epub_hash}, Title: {title})")
            return True, removed_count
        except (OSError, IOError) as e:
            logger.error(f"History deletion failed: {e}")
            return False, 0
            
    return False, 0

def load_book_profile(project_root):
    """Load saved settings from book_profile.json"""
    profile_path = os.path.join(project_root, "book_profile.json")
    if not os.path.exists(profile_path):
        return None
    
    try:
        with open(profile_path, "r", encoding="utf-8") as f:
            profile = json.load(f)
        logger.info(f"Loaded book profile from {profile_path}")
        return profile
    except Exception as e:
        logger.warning(f"Failed to load book profile: {e}")
        return None

def save_book_profile(project_root, engine, voice, speed, concurrent=None):
    """Save current settings to book_profile.json"""
    profile_path = os.path.join(project_root, "book_profile.json")
    profile = {
        "engine": engine,
        "voice": voice,
        "speed": speed,
        "concurrent": concurrent,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2)
        logger.info(f"Saved book profile to {profile_path}")
    except Exception as e:
        logger.error(f"Failed to save book profile: {e}")

def check_history_conflict(book_title, new_start, new_end):
    """Check if chapter range conflicts with existing history
    Returns: (conflict_type, message) where conflict_type is:
             - False: no conflict
             - True: significant overlap (2+ chapters)
             - "boundary": single chapter boundary overlap
    """
    history = load_history()
    key = sanitize_filename(book_title)
    if key not in history:
        return False, None
    
    for entry in history[key]:
        old_start = int(entry.get("start", 0))
        old_end = int(entry.get("end", 0))
        
        # Check for actual overlap
        # Overlap exists if ranges share chapters
        overlap_start = max(new_start, old_start)
        overlap_end = min(new_end, old_end)
        if overlap_start <= overlap_end:
            # There's an overlap
            overlap_size = overlap_end - overlap_start + 1
            # Allow single-chapter boundary overlaps (e.g., 41-60 and 60-79)
            # Only flag if there's significant overlap (2+ chapters)
            if overlap_size > 1:
                return True, f"Ch {old_start}-{old_end} (on {entry.get('date', 'unknown')}) - overlaps by {overlap_size} chapters"
            elif overlap_size == 1:
                # Single chapter overlap - return special flag for warning
                return "boundary", f"Ch {old_start}-{old_end} (on {entry.get('date', 'unknown')}) - shares chapter {overlap_start}"
    return False, None

def clean_html_for_tts(html_content):
    """Extract clean text from HTML for TTS"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style
    for script in soup(["script", "style"]):
        script.decompose()
    
    h1 = soup.find('h1')
    if h1:
        title = h1.get_text().strip()
    else:
        title = soup.get_text().split('\n')[0][:50].strip()
    
    text_parts = []
    paras = soup.find_all('p')
    if paras:
        for p in paras:
            text_parts.append(p.get_text().strip())
    else:
        text_parts.append(soup.get_text())
    
    full_text = "\n\n".join(t for t in text_parts if t)
    
    lower = title.lower()
    if "information" in lower or "introduction" in lower or "synopsis" in lower:
        return title, full_text
    
    match = re.search(r"(Chapter|Ch|Episode|Page)\.?\s*(\d+)", full_text[:500], re.IGNORECASE)
    if match:
        real_label = match.group(0)
        if match.group(2) not in title:
            title = real_label
    
    return title, full_text

def clean_html_summary(html_summary):
    """Clean HTML summary to plain text"""
    if not html_summary:
        return ""
    soup = BeautifulSoup(html_summary, 'html.parser')
    return soup.get_text(separator="\n").strip()

def parse_full_epub(epub_path):
    """Parse EPUB and extract metadata + chapters"""
    print(CP(f"\n📖 Analyzing EPUB structure...", 'cyan'))
    try:
        book = epub.read_epub(epub_path)
    except Exception as e:
        logger.error(f"EPUB read failed: {e}")
        return None, None, None
    
    meta = {"title": "Unknown", "author": "Unknown", "summary": "", "tags": []}
    
    try:
        meta["title"] = book.get_metadata('DC', 'title')[0][0]
    except:
        pass
    try:
        meta["author"] = book.get_metadata('DC', 'creator')[0][0]
    except:
        pass
    try:
        raw = book.get_metadata('DC', 'description')[0][0]
        meta["summary"] = clean_html_summary(raw)
    except:
        pass
    try:
        subjects = book.get_metadata('DC', 'subject')
        meta["tags"] = [s[0] for s in subjects]
    except:
        pass
    
    chapters = []
    for i, item_id in enumerate(book.spine):
        item = book.get_item_with_id(item_id[0])
        if item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue
        
        content = item.get_content().decode('utf-8')
        chap_title, chap_text = clean_html_for_tts(content)
        
        if i < 10:
            lower = chap_title.lower()
            if any(x in lower for x in ["info", "intro", "desc", "synopsis", "about"]):
                # If we don't have a good summary yet, use this text
                current_summary = meta.get("summary", "")
                if not current_summary or current_summary == "No summary available." or len(current_summary) < 50:
                    print(f"   📝 Using front-matter as summary: '{chap_title}'")
                    meta["summary"] = chap_text
                else:
                    print(f"   ℹ️ Skipping front-matter/info page: '{chap_title}'")
                continue
        
        if len(chap_text) < 50:
            continue
        
        chapters.append((chap_title, chap_text))
    
    if not meta["summary"]:
        meta["summary"] = "No summary available."
    
    return meta, chapters, book

def extract_cover_to_project(book, paths, book_title):
    """Extract embedded cover from EPUB"""
    try:
        cover_item = None
        for item in book.get_items_of_type(ebooklib.ITEM_IMAGE):
            if 'cover' in item.get_name().lower() or 'cover' in item.get_id().lower():
                cover_item = item
                break
        
        if cover_item:
            ext = cover_item.get_name().split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'gif']:
                ext = 'jpg' # Fallback extension
                
            safe_title = sanitize_filename(book_title)
            filename = f"{safe_title}_internal_cover.{ext}"
            save_path = os.path.join(paths["covers"], filename)
            
            content = cover_item.get_content()
            
            # Save to archive folder
            with open(save_path, "wb") as f:
                f.write(content)
            
            # Feature: Standardized fallback in root
            root_fallback = os.path.join(paths["root"], f"cover.{ext}")
            try:
                with open(root_fallback, "wb") as f:
                    f.write(content)
                logger.info(f"Standardized cover saved to root: cover.{ext}")
            except Exception as e:
                logger.warning(f"Failed to save root fallback cover: {e}")
                
            print(CP(f"   ✅ Cover extracted: {filename}", 'green'), flush=True)
            return save_path
        else:
            print(f"   ℹ️  No embedded cover found", flush=True)
            return None
    except Exception as e:
        logger.error(f"Cover extraction failed: {e}")
        return None

def generate_description_file(meta, range_name, paths, timestamps, config):
    """Generate YouTube description file"""
    from core.utils import generate_smart_tags, seconds_to_time_str
    
    print("   📝 Generating description...", flush=True)
    
    generated_hashtags = generate_smart_tags(meta['title'], meta['summary'], config["fandom_tags"])
    ts_text = "⏱️ TIMESTAMPS:\n"
    for seconds, title in timestamps:
        ts_text += f"{seconds_to_time_str(seconds)} - {title}\n"
    
    tagline = config["branding"]["tagline"]
    
    content = f"""{meta['summary']}

{ts_text}

---
📜 DISCLAIMER & CREDITS
I do not claim ownership of this story, the characters, or the world they inhabit. This is a fan-made project created solely for entertainment and accessibility purposes. All rights and credit belong to the original creators and rights holders.

**{tagline}**

Fair Use Notice:
This video is a transformative work. We believe this constitutes a 'fair use' of any such copyrighted material as provided for in section 107 of the US Copyright Law.

🚫 COPYRIGHT HOLDERS:
If you are the rights holder and wish for this content to be removed, please do not issue a copyright strike. Please check the **Channel Description (About Page)** for my contact email. Message me, and I will delete the video immediately.

---
{generated_hashtags}
"""
    
    file_name = f"{range_name} - Description.txt"
    file_path = os.path.join(paths["desc"], file_name)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Description saved: {file_name}")
    except (OSError, IOError) as e:
        logger.error(f"Description save failed: {e}")


def validate_epub(epub_path):
    """
    Validate EPUB file before processing to avoid wasting time
    
    Checks:
    - File is readable
    - Has required metadata
    - Has parseable chapters
    - First chapter can be parsed
    
    Returns:
        (bool, Optional[str]): (is_valid, error_message)
    """
    try:
        # Check file exists and is readable
        if not os.path.exists(epub_path):
            return False, "File not found"
        
        if os.path.getsize(epub_path) == 0:
            return False, "File is empty"
        
        # Try to open as EPUB
        try:
            book = epub.read_epub(epub_path)
        except Exception as e:
            return False, f"Cannot read EPUB: {str(e)[:100]}"
        
        # Check for required metadata
        title = book.get_metadata('DC', 'title')
        if not title:
            return False, "Missing title metadata"
        
        # Get chapters
        chapters = [item for item in book.get_items() 
                   if item.get_type() == ebooklib.ITEM_DOCUMENT]
        
        if not chapters:
            return False, "No chapters found in EPUB"
        
        # Try to parse first chapter
        try:
            first_chapter = chapters[0]
            html_content = first_chapter.get_content()
            
            # Verify it's valid HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Check if we can extract text
            text = soup.get_text()
            if not text.strip():
                return False, "First chapter has no text"
                
        except Exception as e:
            return False, f"Cannot parse first chapter: {str(e)[:100]}"
        
        # All checks passed
        return True, None
        
    except Exception as e:
        return False, f"Validation error: {str(e)[:100]}"

