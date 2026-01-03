import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import html2text
import re
import sys

def epub_to_text(epub_path, output_path, start_chapter, end_chapter):
    try:
        book = epub.read_epub(epub_path)
    except Exception as e:
        print(f"Error reading EPUB: {e}")
        return

    text_content = []
    
    # Filter for chapter-like items (this heuristic might need adjustment based on specific EPUB structure)
    # Often chapters are in items of type ITEM_DOCUMENT
    documents = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))
    
    # Simple heuristic: filter out navigation, cover, etc., by name or size if needed.
    # For now, we'll try to use all documents and rely on manual inspection or improvement if it fails.
    # A better approach for specific books is to look at the TOC (Table of Contents).
    
    # Let's try to follow the spine, which determines reading order
    spine_ids = [item[0] for item in book.spine]
    chapters = []
    
    for item_id in spine_ids:
        item = book.get_item_with_id(item_id)
        if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
            chapters.append(item)

    print(f"Found {len(chapters)} document sections in the spine.")

    # Extract text from the specified range
    # Note: start_chapter and end_chapter are 1-based indices for the user, so we adjust.
    # We slice carefully to avoid index errors.
    
    start_idx = max(0, start_chapter - 1)
    end_idx = min(len(chapters), end_chapter)
    
    selected_chapters = chapters[start_idx:end_idx]
    
    print(f"Extracting text from section {start_idx + 1} to {end_idx}...")

    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    h.ignore_emphasis = True
    
    full_text = ""
    
    for chapter in selected_chapters:
        soup = BeautifulSoup(chapter.get_body_content(), 'html.parser')
        
        # Extract text using html2text for better formatting preservation (like paragraph breaks)
        # or just simple soup.get_text() if we want raw text.
        # Let's use simple get_text with some cleaning for this alignment task.
        
        raw_text = soup.get_text(separator=' ', strip=True)
        
        # Simple cleaning
        clean_text = re.sub(r'\s+', ' ', raw_text).strip()
        
        if clean_text:
            full_text += clean_text + "\n\n"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_text)
    
    print(f"Successfully saved extracted text to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python extract_epub.py <epub_file> <output_txt> <start_chapter> <end_chapter>")
    else:
        epub_to_text(sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
