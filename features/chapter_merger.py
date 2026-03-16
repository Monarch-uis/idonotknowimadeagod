"""
Chapter Merger - Optimize book structure by combining small chapters.
Helps in reducing file count and context switching overhead.
"""
from typing import List, Tuple, Any
import os
import re

class ChapterMerger:
    """Merges small chapters into larger chunks"""
    
    def __init__(self, min_word_count: int = 1000):
        self.min_words = min_word_count
        
    def estimate_word_count(self, text: str) -> int:
        """Fast estimate of words using regex or split"""
        if not text: return 0
        return len(text.split())

    def merge_chapters(self, all_chapters: List[Tuple[str, str]], book_obj: Any, temp_dir: str) -> List[Tuple[str, str]]:
        """
        Scan list of chapters and merge small ones with next chapter.
        Returns (title, text_content_or_filepath).
        """
        if not all_chapters:
            return []
            
        merged_chapters = []
        buffer_titles = []
        buffer_contents = []
        buffer_word_count = 0
        
        count_input = len(all_chapters)
        
        from rich.progress import track
        for i, (title, content) in enumerate(track(all_chapters, description="[bold blue]Analyzing chapters...", total=count_input)):
            try:
                # Handle potential path vs text
                text_to_check = content
                if isinstance(content, str) and content.endswith((".html", ".txt")) and os.path.exists(content):
                    try:
                        with open(content, "r", encoding="utf-8") as f:
                            text_to_check = f.read()
                    except (OSError, IOError):
                        pass  # File read failed, use string as-is
                
                words = self.estimate_word_count(text_to_check)
                
                if buffer_word_count > 0 or words < self.min_words:
                    buffer_titles.append(title)
                    buffer_contents.append(text_to_check)
                    buffer_word_count += words
                    
                    if buffer_word_count >= self.min_words:
                        combined_title = " & ".join(buffer_titles)
                        combined_content = "\n\n".join(buffer_contents)
                        merged_path = self._save_temp(combined_title, combined_content, temp_dir)
                        merged_chapters.append((combined_title, merged_path))
                        
                        buffer_titles = []
                        buffer_contents = []
                        buffer_word_count = 0
                else:
                    merged_chapters.append((title, content))
                        
            except Exception as e:
                print(f"   ⚠️  Merge skipping {title}: {e}")
                merged_chapters.append((title, content))
                
        # Flush remaining buffer
        if buffer_contents:
             combined_title = " & ".join(buffer_titles)
             combined_content = "\n\n".join(buffer_contents)
             merged_path = self._save_temp(combined_title, combined_content, temp_dir)
             merged_chapters.append((combined_title, merged_path))
             
        if len(merged_chapters) < count_input:
            print(f"   📉 Smart Merge: Reduced {count_input} chapters to {len(merged_chapters)} (Threshold: {self.min_words} words)")
            return merged_chapters
        return all_chapters

    def _save_temp(self, title: str, content: str, temp_dir: str) -> str:
        """Save string content to a temp file with safe naming"""
        import hashlib
        # Hash title for uniqueness but keep segment of title for readability
        safe_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', title).strip('_')[:30]
        unique_id = hashlib.md5(title.encode()).hexdigest()[:8]
        filename = f"merged_{safe_name}_{unique_id}.html"
        path = os.path.join(temp_dir, filename)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return path
                

