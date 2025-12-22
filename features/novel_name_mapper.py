"""
Novel Name Mapper - Track YouTube Upload Names vs Original Novel Names
========================================================================

This module automatically tracks the relationship between:
- Original EPUB title (from metadata)
- YouTube upload name (user-provided custom name)
- Sanitized folder name (filesystem-safe version)
- Project path and chapter ranges

Use Cases:
- Look up original novel when someone requests extra chapters
- Track all novels you've uploaded to YouTube
- Maintain a searchable database of your content
"""

import json
import os
import re
import difflib
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from core.utils import sanitize_filename, CP, logger

MAPPINGS_FILE = "novel_name_mappings.json"


class NovelNameMapper:
    """Manages mappings between original novel names and YouTube upload names"""
    
    # Common stop words to ignore during matching
    STOP_WORDS = {'the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for', 'and', 'or'}
    
    def __init__(self, mappings_file: str = MAPPINGS_FILE):
        self.mappings_file = mappings_file
        self.mappings = self._load_mappings()
    
    def _normalize(self, text: str) -> str:
        """
        Normalize text for comparison by:
        - Converting to lowercase
        - Replacing punctuation with spaces
        - Collapsing multiple spaces
        """
        if not text:
            return ""
        # Replace non-alphanumeric characters (except spaces) with space
        normalized = re.sub(r'[^\w\s]', ' ', text.lower())
        # Collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized
    
    def _tokenize(self, text: str, remove_stop_words: bool = False) -> set:
        """Convert text to a set of tokens (words)"""
        normalized = self._normalize(text)
        tokens = set(normalized.split())
        if remove_stop_words:
            tokens = tokens - self.STOP_WORDS
        return tokens
    
    def _token_match_score(self, query: str, target: str) -> float:
        """
        Calculate how many query tokens are found in target.
        Returns a score from 0.0 to 1.0
        """
        query_tokens = self._tokenize(query, remove_stop_words=True)
        target_tokens = self._tokenize(target, remove_stop_words=True)
        
        if not query_tokens:
            return 0.0
        
        matches = query_tokens & target_tokens
        return len(matches) / len(query_tokens)
    
    def _fuzzy_score(self, query: str, target: str) -> float:
        """
        Calculate fuzzy similarity score using difflib.
        Returns a score from 0.0 to 1.0
        """
        return difflib.SequenceMatcher(
            None, 
            self._normalize(query), 
            self._normalize(target)
        ).ratio()
    
    def _load_mappings(self) -> Dict:
        """Load mappings from JSON file"""
        if not os.path.exists(self.mappings_file):
            return {"mappings": [], "version": "1.0"}
        
        try:
            with open(self.mappings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load mappings: {e}")
            return {"mappings": [], "version": "1.0"}
    
    def _save_mappings(self):
        """Save mappings to JSON file with atomic write"""
        import tempfile
        
        try:
            # Write to temp file first
            dir_name = os.path.dirname(os.path.abspath(self.mappings_file)) or '.'
            fd, temp_path = tempfile.mkstemp(suffix='.json', dir=dir_name)
            
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(self.mappings, f, indent=2, ensure_ascii=False)
                
                # Atomic rename
                os.replace(temp_path, self.mappings_file)
                logger.info(f"Saved novel name mappings to {self.mappings_file}")
            except Exception as e:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                raise e
        except Exception as e:
            logger.error(f"Failed to save mappings: {e}")
    
    def save_mapping(self, original_title: str, youtube_name: str, 
                    sanitized_title: str, project_path: str, 
                    chapter_range: str = None) -> bool:
        """
        Save a new mapping or update existing one
        
        Args:
            original_title: Original EPUB title
            youtube_name: Name used for YouTube upload
            sanitized_title: Filesystem-safe folder name
            project_path: Full path to project folder
            chapter_range: e.g., "1-50" or "Ch 1-50"
        
        Returns:
            True if saved successfully
        """
        try:
            # Check if mapping already exists for this original title OR in alt_titles
            existing_idx = None
            for idx, mapping in enumerate(self.mappings["mappings"]):
                if (mapping["original_title"] == original_title or 
                    original_title in mapping.get("alt_titles", [])):
                    existing_idx = idx
                    break
            
            mapping_data = {
                "original_title": original_title,
                "youtube_name": youtube_name,
                "sanitized_title": sanitized_title,
                "project_path": project_path,
                "chapter_ranges": [chapter_range] if chapter_range else [],
                "alt_titles": [],
                "created_date": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }
            
            if existing_idx is not None:
                # Update existing mapping
                old_mapping = self.mappings["mappings"][existing_idx]
                
                # If we matched by alt_title, keep the original primary title
                if old_mapping["original_title"] != original_title:
                    mapping_data["original_title"] = old_mapping["original_title"]
                    if original_title not in old_mapping.get("alt_titles", []):
                         mapping_data["alt_titles"] = old_mapping.get("alt_titles", []) + [original_title]
                    else:
                         mapping_data["alt_titles"] = old_mapping.get("alt_titles", [])
                else:
                    mapping_data["alt_titles"] = old_mapping.get("alt_titles", [])
                
                # Merge chapter ranges
                if chapter_range and chapter_range not in old_mapping.get("chapter_ranges", []):
                    mapping_data["chapter_ranges"] = old_mapping.get("chapter_ranges", []) + [chapter_range]
                else:
                    mapping_data["chapter_ranges"] = old_mapping.get("chapter_ranges", [])
                
                # Keep original creation date
                mapping_data["created_date"] = old_mapping.get("created_date", mapping_data["created_date"])
                
                self.mappings["mappings"][existing_idx] = mapping_data
                logger.info(f"Updated mapping for: {mapping_data['original_title']}")
            else:
                # Add new mapping
                self.mappings["mappings"].append(mapping_data)
                logger.info(f"Created new mapping for: {original_title}")
            
            self._save_mappings()
            return True
        except Exception as e:
            logger.error(f"Failed to save mapping: {e}")
            return False
    
    def lookup_by_youtube_name(self, youtube_name: str, threshold: float = 0.7) -> Tuple[Optional[Dict], str, float]:
        """
        LEGENDARY SEARCH: Find original novel info by YouTube upload name.
        
        Search Priority:
        1. Exact match (normalized)
        2. Token-based match (word-order independent)
        3. Fuzzy match (handles typos)
        
        Args:
            youtube_name: Name used on YouTube
            threshold: Minimum score for fuzzy matches (0.0-1.0)
        
        Returns:
            Tuple of (mapping, match_type, score)
            - mapping: The matched mapping dict or None
            - match_type: 'exact', 'token', 'fuzzy', or 'none'
            - score: Match confidence (0.0-1.0)
        """
        if not youtube_name:
            return None, 'none', 0.0
        
        query_normalized = self._normalize(youtube_name)
        best_match = None
        best_score = 0.0
        match_type = 'none'
        
        for mapping in self.mappings["mappings"]:
            yt_name = mapping["youtube_name"]
            yt_normalized = self._normalize(yt_name)
            
            # 1. Exact match (normalized) - instant return
            if query_normalized == yt_normalized:
                return mapping, 'exact', 1.0
            
            # 2. Token-based match (word-order independent)
            token_score = self._token_match_score(youtube_name, yt_name)
            if token_score >= 0.9 and token_score > best_score:
                best_match = mapping
                best_score = token_score
                match_type = 'token'
            
            # 3. Fuzzy match (for typos)
            fuzzy_score = self._fuzzy_score(youtube_name, yt_name)
            if fuzzy_score >= threshold and fuzzy_score > best_score:
                best_match = mapping
                best_score = fuzzy_score
                match_type = 'fuzzy'
        
        return best_match, match_type, best_score
    
    def get_close_matches(self, youtube_name: str, top_n: int = 3) -> List[Tuple[Dict, float]]:
        """
        Get the top N closest matches for 'Did you mean?' suggestions.
        
        Args:
            youtube_name: The query name
            top_n: Number of suggestions to return
            
        Returns:
            List of (mapping, score) tuples sorted by score descending
        """
        scored_mappings = []
        
        for mapping in self.mappings["mappings"]:
            yt_name = mapping["youtube_name"]
            # Use a combination of token and fuzzy score
            token_score = self._token_match_score(youtube_name, yt_name)
            fuzzy_score = self._fuzzy_score(youtube_name, yt_name)
            combined_score = max(token_score, fuzzy_score)
            scored_mappings.append((mapping, combined_score))
        
        # Sort by score descending
        scored_mappings.sort(key=lambda x: x[1], reverse=True)
        return scored_mappings[:top_n]
    
    def lookup_by_original_title(self, original_title: str) -> Optional[Dict]:
        """Find YouTube name by original novel title (checks primary and alt titles)"""
        for mapping in self.mappings["mappings"]:
            if (mapping["original_title"] == original_title or 
                original_title in mapping.get("alt_titles", [])):
                return mapping
        return None
    
    def search_mappings(self, query: str) -> List[Dict]:
        """
        Fuzzy search across all fields
        
        Args:
            query: Search term
        
        Returns:
            List of matching mappings
        """
        query_lower = query.lower()
        results = []
        
        for mapping in self.mappings["mappings"]:
            # Search in all text fields
            searchable = f"{mapping['original_title']} {mapping['youtube_name']} {mapping['sanitized_title']}".lower()
            if query_lower in searchable:
                results.append(mapping)
        
        return results
    
    def list_all_mappings(self) -> List[Dict]:
        """Get all mappings"""
        return self.mappings["mappings"]
    
    def delete_mapping(self, original_title: str) -> bool:
        """Delete a mapping by original title"""
        try:
            self.mappings["mappings"] = [
                m for m in self.mappings["mappings"] 
                if m["original_title"] != original_title
            ]
            self._save_mappings()
            return True
        except Exception as e:
            logger.error(f"Failed to delete mapping: {e}")
            return False
    
    def check_for_duplicate(self, original_title: str, youtube_name: str, threshold: float = 0.85) -> Dict:
        """
        Check if a novel mapping might be a duplicate of an existing entry.
        
        This detects TWO scenarios:
        1. Same novel, different name: Reprocessing the same EPUB with a new YouTube name.
        2. Different novel, same name: Accidentally naming a different novel the same.
        
        Args:
            original_title: The original EPUB title being processed
            youtube_name: The YouTube name the user wants to use
            threshold: Similarity threshold for fuzzy matching
            
        Returns:
            Dict with keys:
            - 'is_duplicate': bool
            - 'duplicate_type': 'same_novel' | 'same_name' | 'similar_name' | None
            - 'existing_mapping': The conflicting mapping or None
            - 'similarity_score': float (0.0-1.0)
            - 'message': Human-readable explanation
        """
        result = {
            'is_duplicate': False,
            'duplicate_type': None,
            'existing_mapping': None,
            'similarity_score': 0.0,
            'message': ''
        }
        
        # 1. Check for same original title (same novel being reprocessed)
        for mapping in self.mappings["mappings"]:
            if self._normalize(mapping["original_title"]) == self._normalize(original_title):
                result['is_duplicate'] = True
                result['duplicate_type'] = 'same_novel'
                result['existing_mapping'] = mapping
                result['similarity_score'] = 1.0
                result['message'] = f"This novel was previously uploaded as: \"{mapping['youtube_name']}\""
                return result
        
        # 2. Check for exact YouTube name match (different novel, same name)
        for mapping in self.mappings["mappings"]:
            if self._normalize(mapping["youtube_name"]) == self._normalize(youtube_name):
                result['is_duplicate'] = True
                result['duplicate_type'] = 'same_name'
                result['existing_mapping'] = mapping
                result['similarity_score'] = 1.0
                result['message'] = f"This name is already used for: \"{mapping['original_title']}\""
                return result
        
        # 3. Check for similar YouTube name (fuzzy match)
        for mapping in self.mappings["mappings"]:
            score = max(
                self._fuzzy_score(youtube_name, mapping["youtube_name"]),
                self._token_match_score(youtube_name, mapping["youtube_name"])
            )
            if score >= threshold and score > result['similarity_score']:
                result['is_duplicate'] = True
                result['duplicate_type'] = 'similar_name'
                result['existing_mapping'] = mapping
                result['similarity_score'] = score
                result['message'] = f"Similar name exists ({score*100:.0f}% match): \"{mapping['youtube_name']}\""
        
        return result
    
    def sync_from_history(self, history_path: str = None) -> Tuple[int, int, List[str]]:
        """
        Synchronize mappings from the global history database.
        
        Args:
            history_path: Path to global_database.json (defaults to ~/.epub_project_history/global_database.json)
            
        Returns:
            Tuple of (added_count, skipped_count, error_messages)
        """
        if history_path is None:
            history_path = os.path.join(os.path.expanduser("~"), ".epub_project_history", "global_database.json")
        
        added = 0
        skipped = 0
        errors = []
        
        if not os.path.exists(history_path):
            errors.append(f"History file not found: {history_path}")
            return added, skipped, errors
        
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                history_data = json.load(f)
        except Exception as e:
            errors.append(f"Failed to read history: {e}")
            return added, skipped, errors
        
        # Process each book in history
        for book_key, book_data in history_data.items():
            if not isinstance(book_data, dict):
                continue
            
            original_title = book_data.get('book_title', book_key)
            youtube_name = book_data.get('display_name', original_title)
            project_path = book_data.get('project_path', '')
            chapter_ranges = book_data.get('chapters', [])
            
            # Check if already exists
            existing = self.lookup_by_original_title(original_title)
            if existing:
                skipped += 1
                continue
            
            # Add new mapping
            success = self.save_mapping(
                original_title=original_title,
                youtube_name=youtube_name,
                sanitized_title=sanitize_filename(youtube_name),
                project_path=project_path,
                chapter_range=', '.join(chapter_ranges) if chapter_ranges else None
            )
            
            if success:
                added += 1
            else:
                errors.append(f"Failed to save: {original_title}")
        
        return added, skipped, errors
    
    def sync_from_folders(self, novels_dir: str = None) -> Tuple[int, int, List[str]]:
        """
        Auto-discover novel folders and create mappings for any that are missing.
        
        Args:
            novels_dir: Base novels directory (defaults to Novels/Active Novels)
            
        Returns:
            Tuple of (added_count, skipped_count, error_messages)
        """
        if novels_dir is None:
            novels_dir = os.path.join("Novels", "Active Novels")
        
        added = 0
        skipped = 0
        errors = []
        
        if not os.path.exists(novels_dir):
            errors.append(f"Novels directory not found: {novels_dir}")
            return added, skipped, errors
        
        for folder_name in os.listdir(novels_dir):
            folder_path = os.path.join(novels_dir, folder_name)
            if not os.path.isdir(folder_path):
                continue
            
            # Check if this folder is already in mappings (by sanitized title or path)
            already_exists = False
            for mapping in self.mappings["mappings"]:
                if (self._normalize(mapping.get("sanitized_title", "")) == self._normalize(folder_name) or
                    mapping.get("project_path", "") == folder_path):
                    already_exists = True
                    break
            
            if already_exists:
                skipped += 1
                continue
            
            # Try to get info from book_profile.json if exists
            profile_path = os.path.join(folder_path, "book_profile.json")
            original_title = folder_name
            youtube_name = folder_name
            
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, 'r', encoding='utf-8') as f:
                        profile = json.load(f)
                    original_title = profile.get('original_title', folder_name)
                    youtube_name = profile.get('display_name', profile.get('title', folder_name))
                except:
                    pass
            
            # Add new mapping
            success = self.save_mapping(
                original_title=original_title,
                youtube_name=youtube_name,
                sanitized_title=folder_name,
                project_path=folder_path
            )
            
            if success:
                added += 1
            else:
                errors.append(f"Failed to save: {folder_name}")
        
        return added, skipped, errors


# ============================================================================
# CLI FUNCTIONS
# ============================================================================

def display_mapping(mapping: Dict, index: int = None):
    """Display a single mapping in a formatted way"""
    prefix = f"[{index}] " if index is not None else ""
    
    print(f"\n{prefix}{'='*70}")
    print(CP(f"📺 YouTube Name: {mapping['youtube_name']}", 'cyan'))
    print(f"📖 Original Title: {mapping['original_title']}")
    print(f"📁 Folder: {mapping['sanitized_title']}")
    
    if mapping.get('chapter_ranges'):
        print(f"📑 Chapters: {', '.join(mapping['chapter_ranges'])}")
    
    if mapping.get('alt_titles'):
        print(f"🔗 Also known as: {', '.join(mapping['alt_titles'])}")
    
    print(f"📂 Path: {mapping['project_path']}")
    print(f"📅 Last Updated: {mapping.get('last_updated', 'Unknown')[:10]}")
    print("="*70)


def list_all_mappings_cli():
    """CLI command to list all mappings"""
    mapper = NovelNameMapper()
    mappings = mapper.list_all_mappings()
    
    if not mappings:
        print(CP("\nℹ️  No novel name mappings found yet.", 'yellow'))
        print("   Mappings are created automatically when you rename a novel during processing.")
        return
    
    print(CP(f"\n📚 NOVEL NAME MAPPINGS ({len(mappings)} total)", 'cyan'))
    print("="*70)
    
    for idx, mapping in enumerate(mappings, 1):
        display_mapping(mapping, idx)
    
    print(f"\n💡 Tip: Use --lookup \"YouTube Name\" to find a specific novel")


def lookup_by_youtube_name_cli(youtube_name: str):
    """CLI command to lookup by YouTube name with LEGENDARY search"""
    mapper = NovelNameMapper()
    result, match_type, score = mapper.lookup_by_youtube_name(youtube_name)
    
    if result:
        # Show match confidence
        if match_type == 'exact':
            print(CP(f"\n✅ Found exact match!", 'green'))
        elif match_type == 'token':
            print(CP(f"\n✅ Found match (word-order independent, {score*100:.0f}% confidence)", 'green'))
        elif match_type == 'fuzzy':
            print(CP(f"\n🔍 Assuming you meant: \"{result['youtube_name']}\" ({score*100:.0f}% match)", 'yellow'))
        
        display_mapping(result)
        
        # Show helpful next steps
        print(f"\n💡 Next Steps:")
        print(f"   1. Navigate to: {result['project_path']}")
        print(f"   2. Check existing chapters: {', '.join(result.get('chapter_ranges', ['N/A']))}")
        print(f"   3. Process additional chapters using the original EPUB")
    else:
        print(CP(f"\n❌ No match found for: '{youtube_name}'", 'red'))
        
        # Show "Did you mean?" suggestions
        suggestions = mapper.get_close_matches(youtube_name, top_n=3)
        if suggestions and suggestions[0][1] > 0.3:  # Only show if there's some similarity
            print(CP("\n💡 Did you mean:", 'yellow'))
            for i, (mapping, sim_score) in enumerate(suggestions, 1):
                if sim_score > 0.3:
                    print(f"   [{i}] {mapping['youtube_name']} ({sim_score*100:.0f}% similar)")
            print(f"\n   Run --lookup with the correct name to get full details.")
        else:
            print("\n💡 Tips:")
            print("   • Check spelling")
            print("   • Use partial name (e.g., 'Naruto' instead of full title)")
            print("   • Run --list-mappings to see all available mappings")


def search_mappings_cli(query: str):
    """CLI command to search mappings"""
    mapper = NovelNameMapper()
    results = mapper.search_mappings(query)
    
    if results:
        print(CP(f"\n🔍 Found {len(results)} matching novel(s):", 'green'))
        for idx, mapping in enumerate(results, 1):
            display_mapping(mapping, idx)
    else:
        print(CP(f"\n❌ No results for: '{query}'", 'red'))


# ============================================================================
# INTEGRATION HELPER
# ============================================================================

def auto_save_mapping(original_title: str, youtube_name: str, project_path: str, chapter_range: str = None):
    """
    Automatically save mapping when user renames a novel
    
    This is called from epub_project_manager.py after the user enters a new title
    """
    if not youtube_name or youtube_name == original_title:
        # User didn't rename, no need to save mapping
        return
    
    mapper = NovelNameMapper()
    sanitized = sanitize_filename(youtube_name)
    
    success = mapper.save_mapping(
        original_title=original_title,
        youtube_name=youtube_name,
        sanitized_title=sanitized,
        project_path=project_path,
        chapter_range=chapter_range
    )
    
    if success:
        print(CP(f"   💾 Saved name mapping: '{original_title}' → '{youtube_name}'", 'green'))


def sync_cli():
    """CLI command to synchronize mappings from history and folders"""
    print(CP("\n🔄 LEGENDARY SYNC ENGINE", 'cyan'))
    print("="*70)
    
    mapper = NovelNameMapper()
    
    # 1. Sync from history
    print("\n📜 Step 1: Importing from project history...")
    added_h, skipped_h, errors_h = mapper.sync_from_history()
    if errors_h:
        for err in errors_h:
            print(CP(f"   ⚠️  {err}", 'yellow'))
    else:
        print(CP(f"   ✅ Added {added_h} novels, skipped {skipped_h} (already exist)", 'green'))
    
    # 2. Sync from folders
    print("\n📂 Step 2: Auto-discovering novel folders...")
    added_f, skipped_f, errors_f = mapper.sync_from_folders()
    if errors_f:
        for err in errors_f:
            print(CP(f"   ⚠️  {err}", 'yellow'))
    else:
        print(CP(f"   ✅ Added {added_f} novels, skipped {skipped_f} (already exist)", 'green'))
    
    # Summary
    total_added = added_h + added_f
    total_mappings = len(mapper.list_all_mappings())
    
    print("\n" + "="*70)
    print(CP(f"🎉 SYNC COMPLETE!", 'green'))
    print(f"   Total novels in database: {total_mappings}")
    print(f"   New entries added: {total_added}")
    print(f"\n💡 Tip: Run --list-mappings to see all your novels")


def check_duplicate_interactive(original_title: str, youtube_name: str) -> str:
    """
    Check for duplicates during novel processing and get user decision.
    
    Args:
        original_title: The EPUB's original title
        youtube_name: The YouTube name the user wants to use
        
    Returns:
        The final YouTube name to use (may be the existing one or the new one)
    """
    mapper = NovelNameMapper()
    dup_check = mapper.check_for_duplicate(original_title, youtube_name)
    
    if not dup_check['is_duplicate']:
        return youtube_name
    
    existing = dup_check['existing_mapping']
    dup_type = dup_check['duplicate_type']
    
    print("\n" + "="*70)
    print(CP("⚠️  DUPLICATE DETECTION WARNING", 'yellow'))
    print("="*70)
    
    if dup_type == 'same_novel':
        print(f"\n📚 This novel was previously processed!")
        print(f"   Original Title: {existing['original_title']}")
        print(CP(f"   Existing YouTube Name: \"{existing['youtube_name']}\"", 'cyan'))
        if existing.get('chapter_ranges'):
            print(f"   Chapters already done: {', '.join(existing['chapter_ranges'])}")
        
        print("\n🔧 Options:")
        print(f"   [1] Use existing name: \"{existing['youtube_name']}\" (RECOMMENDED for adding chapters)")
        print(f"   [2] Create new entry with: \"{youtube_name}\"")
        print(f"   [3] Enter a different name")
        
    elif dup_type == 'same_name':
        print(f"\n🚫 This YouTube name is already used for a DIFFERENT novel!")
        print(f"   Your novel: {original_title}")
        print(CP(f"   Existing novel: {existing['original_title']}", 'red'))
        print(f"   Both would use: \"{youtube_name}\"")
        
        print("\n🔧 Options:")
        print(f"   [1] Use a different name (RECOMMENDED)")
        print(f"   [2] Replace the old novel with this one (DANGER)")
        print(f"   [3] Associate with existing: \"{existing['original_title']}\" (Link them)")
        print(f"   [4] Abort / Exit processing")
        
    elif dup_type == 'similar_name':
        score = dup_check['similarity_score']
        print(f"\n🔍 Similar name detected ({score*100:.0f}% match)!")
        print(f"   You entered: \"{youtube_name}\"")
        print(CP(f"   Existing: \"{existing['youtube_name']}\"", 'cyan'))
        print(f"   Original novel: {existing['original_title']}")
        
        print("\n🔧 Options:")
        print(f"   [1] Use existing: \"{existing['youtube_name']}\"")
        print(f"   [2] Keep my name: \"{youtube_name}\"")
        print(f"   [3] Enter a different name")
    
    print("="*70)
    
    while True:
        choice = input("\n👉 Your choice (1/2/3): ").strip()
        
        if dup_type == 'same_novel':
            if choice == '1':
                print(CP(f"\n✅ Using existing name: \"{existing['youtube_name']}\"", 'green'))
                return existing['youtube_name']
            elif choice == '2':
                print(CP(f"\n⚠️  Creating new entry with: \"{youtube_name}\"", 'yellow'))
                return youtube_name
            elif choice == '3':
                new_name = input("   Enter new YouTube name: ").strip()
                if new_name:
                    return check_duplicate_interactive(original_title, new_name)
                    
        elif dup_type == 'same_name':
            if choice == '1':
                new_name = input("   Enter a different YouTube name: ").strip()
                if new_name:
                    return check_duplicate_interactive(original_title, new_name)
            elif choice == '2':
                confirm = input(CP("   ⚠️  This will REPLACE the old mapping. Type 'REPLACE' to confirm: ", 'red')).strip()
                if confirm == 'REPLACE':
                    return youtube_name
            elif choice == '3':
                print(CP(f"\n✅ Linking \"{original_title}\" as an alias for \"{existing['original_title']}\"", 'green'))
                # We need to manually link here if save_mapping is not enough
                if 'alt_titles' not in existing: existing['alt_titles'] = []
                if original_title not in existing['alt_titles']:
                    existing['alt_titles'].append(original_title)
                mapper._save_mappings()
                return existing['youtube_name']
            elif choice == '4':
                print(CP("\n👋 Exiting due to name conflict.", 'white'))
                sys.exit(0)
                    
        elif dup_type == 'similar_name':
            if choice == '1':
                print(CP(f"\n✅ Using existing name: \"{existing['youtube_name']}\"", 'green'))
                return existing['youtube_name']
            elif choice == '2':
                print(CP(f"\n✅ Keeping your name: \"{youtube_name}\"", 'green'))
                return youtube_name
            elif choice == '3':
                new_name = input("   Enter new YouTube name: ").strip()
                if new_name:
                    return check_duplicate_interactive(original_title, new_name)
        
        print(CP("   Invalid choice, please try again.", 'red'))
