"""
Gemini Processor
High-level orchestration of Gemini AI integration for EPUB processing.
Handles Phase 1 (story analysis) and Phase 2 (batch processing).
"""
import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from core.config import CONFIG
from core.utils import logger, sanitize_filename, CP
from core.gemini_client import GeminiClient, create_gemini_client, GeminiClientError

class GeminiProcessor:
    """
    Orchestrates Gemini AI integration for EPUB-to-video conversion
    
    Phases:
    1. Story Analysis (once per EPUB) - Description, titles, character analysis
    2. Batch Processing (per 20 chapters) - Intros, TTS segment mapping
    """
    
    def __init__(self, project_path: str, api_key: Optional[str] = None):
        """
        Initialize processor
        
        Args:
            project_path: Path to the project folder (where metadata will be stored)
            api_key: Optional Gemini API key override
        """
        self.project_path = project_path
        self.metadata_path = os.path.join(project_path, 'ai_metadata.json')
        
        # Create Gemini client
        self.client = create_gemini_client(api_key)
        if not self.client:
            raise GeminiClientError("Failed to create Gemini client. Check configuration.")
        
        # Load or initialize metadata
        self.metadata = self._load_metadata()
        
        # Track state
        self.story_analyzed = self.metadata.get('story_analyzed', False)
        self.current_batch = 0
        self.chatterbox_usage_current_batch = 0
        
        logger.info(f"Gemini processor initialized for project: {project_path}")
    
    # ==================== METADATA MANAGEMENT ====================
    
    def _load_metadata(self) -> Dict:
        """Load existing AI metadata or create new"""
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                logger.info(f"Loaded existing AI metadata (version {metadata.get('version', '1.0')})")
                return metadata
            except Exception as e:
                logger.warning(f"Failed to load metadata: {e}, creating new")
        
        return {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'story_analyzed': False,
            'phase1_results': None,
            'phase2_batches': {},
            'user_selections': {}
        }
    
    def _save_metadata(self):
        """Save metadata to file"""
        try:
            with open(self.metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            logger.debug("AI metadata saved")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def get_metadata(self) -> Dict:
        """Get current metadata"""
        return self.metadata.copy()
    
    def clear_metadata(self):
        """Clear all AI metadata (force regeneration)"""
        self.metadata = {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'story_analyzed': False,
            'phase1_results': None,
            'phase2_batches': {},
            'user_selections': {}
        }
        self._save_metadata()
        logger.info("AI metadata cleared")
    
    # ==================== PHASE 1: STORY ANALYSIS ====================
    
    def analyze_story(
        self,
        full_text: str,
        book_metadata: Dict,
        force: bool = False
    ) -> Dict:
        """
        Run Phase 1: Analyze complete story
        
        Args:
            full_text: Complete EPUB text (all chapters)
            book_metadata: Book metadata (title, chapter count, etc.)
            force: Force regeneration even if cached
            
        Returns:
            Story analysis results
        """
        # Check if already analyzed
        if not force and self.metadata.get('story_analyzed', False):
            logger.info("Story already analyzed (cached)")
            return self.metadata['phase1_results']
        
        logger.info("=" * 60)
        logger.info("PHASE 1: ANALYZING FULL STORY WITH GEMINI")
        logger.info("=" * 60)
        
        print(CP("\n🤖 Analyzing your story with Gemini AI...", 'cyan'))
        print(f"   📖 Title: {book_metadata.get('title', 'Unknown')}")
        print(f"   📚 Chapters: {book_metadata.get('total_chapters', 'Unknown')}")
        print(f"   📝 Words: ~{len(full_text.split()):,}")
        print(f"   ⏳ This may take 10-20 seconds...")
        
        try:
            # Call Gemini API
            results = self.client.analyze_full_story(full_text, book_metadata)
            
            # Save results
            self.metadata['phase1_results'] = results
            self.metadata['story_analyzed'] = True
            self.metadata['analyzed_at'] = datetime.now().isoformat()
            self.metadata['model_used'] = self.client.model_name
            self._save_metadata()
            
            # Print summary
            print(CP("\n✅ Story analysis complete!", 'green'))
            
            characters = results['story_analysis'].get('characters', [])
            print(f"   👥 Found {len(characters)} characters")
            if characters:
                print(f"   🎭 Main characters: {', '.join([c['name'] for c in characters[:5]])}")
            
            print(f"   📝 Description: {len(results.get('description', ''))} characters")
            print(f"   🎬 Title options: {len(results.get('title_options', []))}")
            
            key_moments = results['story_analysis'].get('key_moments', [])
            if key_moments:
                moment_types = set(m['type'] for m in key_moments)
                print(f"   ⚡ Key moments: {', '.join(moment_types)}")
            
            # Show usage stats
            stats = self.client.get_usage_stats()
            print(f"   💰 Cost estimate: ${stats['estimated_cost_usd']:.4f}")
            
            logger.info("Phase 1 complete")
            return results
            
        except Exception as e:
            logger.error(f"Phase 1 failed: {e}")
            print(CP(f"\n❌ Story analysis failed: {e}", 'red'))
            raise
    
    def get_title_options(self) -> List[Dict]:
        """Get generated title options"""
        if not self.story_analyzed:
            raise GeminiClientError("Story not analyzed yet. Run analyze_story() first.")
        
        return self.metadata['phase1_results'].get('title_options', [])
    
    def get_description(self) -> str:
        """Get generated description"""
        if not self.story_analyzed:
            raise GeminiClientError("Story not analyzed yet. Run analyze_story() first.")
        
        return self.metadata['phase1_results'].get('description', '')
    
    def select_title(self, title_index: int) -> str:
        """
        Select a title from options
        
        Args:
            title_index: Index of selected title (0-based)
            
        Returns:
            Selected title text
        """
        options = self.get_title_options()
        if not (0 <= title_index < len(options)):
            raise ValueError(f"Invalid title index: {title_index}")
        
        selected = options[title_index]
        self.metadata['user_selections']['title'] = selected['title']
        self.metadata['user_selections']['title_style'] = selected['style']
        self._save_metadata()
        
        logger.info(f"Title selected: {selected['title']}")
        return selected['title']
    
    def set_custom_title(self, custom_title: str):
        """Set a custom title (not from generated options)"""
        self.metadata['user_selections']['title'] = custom_title
        self.metadata['user_selections']['title_style'] = 'custom'
        self._save_metadata()
        logger.info(f"Custom title set: {custom_title}")
    
    # ==================== PHASE 2: BATCH PROCESSING ====================
    
    def process_batch(
        self,
        batch_number: int,
        batch_chapters: List[str],
        upload_date: Optional[str] = None
    ) -> Dict:
        """
        Run Phase 2: Process a batch of chapters
        
        Args:
            batch_number: Batch number (1, 2, 3, ...)
            batch_chapters: List of chapter texts for this batch
            upload_date: Optional upload date for intro context
            
        Returns:
            Batch processing results (intro, tts segments per chapter)
        """
        if not self.story_analyzed:
            logger.warning("Story not analyzed yet, running analysis first...")
            # Cannot proceed without Phase 1
            raise GeminiClientError("Must run analyze_story() before processing batches")
        
        logger.info("=" * 60)
        logger.info(f"PHASE 2: PROCESSING BATCH {batch_number}")
        logger.info("=" * 60)
        
        self.current_batch = batch_number
        self.chatterbox_usage_current_batch = 0
        
        # Get story context from Phase 1
        story_context = self.metadata['phase1_results'].get('story_summary', '')
        character_list = self.metadata['phase1_results']['story_analysis'].get('characters', [])
        
        # Check if batch already processed
        batch_key = f"batch_{batch_number}"
        if batch_key in self.metadata.get('phase2_batches', {}):
            logger.info(f"Batch {batch_number} already processed (cached)")
            use_cached = input(CP("   Use cached batch data? [Y/n]: ", 'yellow')).strip().lower()
            if use_cached != 'n':
                return self.metadata['phase2_batches'][batch_key]
        
        print(CP(f"\n🎬 Processing Batch {batch_number}...", 'cyan'))
        print(f"   📚 Chapters: {len(batch_chapters)}")
        
        results = {
            'batch_number': batch_number,
            'processed_at': datetime.now().isoformat(),
            'intro': None,
            'chapters': []
        }
        
        # Step 1: Generate intro
        print(CP("   📢 Generating intro...", 'cyan'))
        try:
            # Get previous batch summary if available
            previous_summary = None
            if batch_number > 1:
                prev_batch_key = f"batch_{batch_number - 1}"
                if prev_batch_key in self.metadata.get('phase2_batches', {}):
                    # Could extract summary from previous batch, for now use generic
                    previous_summary = "The story continues..."
            
            intro_data = self.client.generate_intro(
                batch_number=batch_number,
                total_batches=5,  # Estimate, adjust based on your typical EPUB size
                story_context=story_context,
                upload_date=upload_date,
                previous_batch_summary=previous_summary
            )
            results['intro'] = intro_data
            
            print(CP(f"   ✅ Intro generated ({intro_data.get('estimated_duration_seconds', 0)}s)", 'green'))
            logger.info(f"Intro: {intro_data.get('intro_text', '')[:100]}...")
            
        except Exception as e:
            logger.error(f"Intro generation failed: {e}")
            print(CP(f"   ⚠️  Intro generation failed, using default", 'yellow'))
            results['intro'] = {
                'intro_text': CONFIG['branding']['intro'],
                'intro_type': 'first' if batch_number == 1 else 'continuation',
                'voice_recommendation': 'chatterbox'
            }
        
        # Step 2: Analyze TTS segments for each chapter
        print(CP("   🎤 Analyzing TTS segments...", 'cyan'))
        
        for idx, chapter_text in enumerate(batch_chapters, 1):
            chapter_num = (batch_number - 1) * 20 + idx
            
            print(f"      Chapter {chapter_num}...", end='', flush=True)
            
            try:
                segment_data = self.client.analyze_tts_segments(
                    chapter_text=chapter_text,
                    chapter_number=chapter_num,
                    character_list=character_list,
                    chatterbox_used_count=self.chatterbox_usage_current_batch
                )
                
                # Update chatterbox usage
                chatterbox_count = segment_data.get('chatterbox_usage', 0)
                self.chatterbox_usage_current_batch += chatterbox_count
                
                results['chapters'].append({
                    'chapter_number': chapter_num,
                    'segments': segment_data['segments'],
                    'chatterbox_usage': chatterbox_count
                })
                
                print(f" ✅ ({len(segment_data['segments'])} segments, {chatterbox_count} expressive)")
                
            except Exception as e:
                logger.error(f"Chapter {chapter_num} TTS analysis failed: {e}")
                print(CP(f" ⚠️  Failed, using fallback", 'yellow'))
                
                # Fallback: single segment with narrator voice
                results['chapters'].append({
                    'chapter_number': chapter_num,
                    'segments': [{
                        'text': chapter_text,
                        'voice': 'piper_narrator',
                        'reasoning': 'fallback - analysis failed'
                    }],
                    'chatterbox_usage': 0
                })
        
        # Save batch results
        self.metadata['phase2_batches'][batch_key] = results
        self._save_metadata()
        
        # Summary
        print(CP(f"\n✅ Batch {batch_number} processing complete!", 'green'))
        print(f"   📊 Total segments: {sum(len(ch['segments']) for ch in results['chapters'])}")
        print(f"   🎭 Chatterbox usage: {self.chatterbox_usage_current_batch} times")
        
        # Show usage stats
        stats = self.client.get_usage_stats()
        print(f"   💰 Total cost so far: ${stats['estimated_cost_usd']:.4f}")
        
        logger.info(f"Batch {batch_number} complete")
        return results
    
    def get_batch_results(self, batch_number: int) -> Optional[Dict]:
        """Get cached results for a batch"""
        batch_key = f"batch_{batch_number}"
        return self.metadata.get('phase2_batches', {}).get(batch_key)
    
    # ==================== UTILITY METHODS ====================
    
    def print_summary(self):
        """Print a summary of current state"""
        print("\n" + "=" * 60)
        print(CP("GEMINI AI INTEGRATION SUMMARY", 'cyan'))
        print("=" * 60)
        
        # Phase 1
        if self.story_analyzed:
            print(CP("\n✅ Phase 1: Story Analysis", 'green'))
            results = self.metadata['phase1_results']
            print(f"   Model: {self.metadata.get('model_used', 'unknown')}")
            print(f"   Analyzed: {self.metadata.get('analyzed_at', 'unknown')}")
            print(f"   Characters: {len(results['story_analysis'].get('characters', []))}")
            print(f"   Title options: {len(results.get('title_options', []))}")
            
            if 'title' in self.metadata.get('user_selections', {}):
                print(f"   Selected title: {self.metadata['user_selections']['title']}")
        else:
            print(CP("\n⏳ Phase 1: Not yet analyzed", 'yellow'))
        
        # Phase 2
        batches = self.metadata.get('phase2_batches', {})
        if batches:
            print(CP(f"\n✅ Phase 2: {len(batches)} batches processed", 'green'))
            for batch_key in sorted(batches.keys()):
                batch_data = batches[batch_key]
                print(f"   Batch {batch_data['batch_number']}: {len(batch_data['chapters'])} chapters")
        else:
            print(CP("\n⏳ Phase 2: No batches processed yet", 'yellow'))
        
        # Usage stats
        stats = self.client.get_usage_stats()
        print(CP("\n💰 Usage Statistics:", 'cyan'))
        print(f"   Total requests: {stats['total_requests']}")
        print(f"   Total tokens: {stats['total_tokens']:,}")
        print(f"   Estimated cost: ${stats['estimated_cost_usd']:.4f}")
        
        within_budget, budget_msg = self.client.check_budget()
        if within_budget:
            print(CP(f"   {budget_msg}", 'green'))
        else:
            print(CP(f"   {budget_msg}", 'red'))
        
        print("=" * 60 + "\n")
    
    def export_metadata(self, output_path: str):
        """Export metadata to a specific path"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"Metadata exported to: {output_path}")
        except Exception as e:
            logger.error(f"Failed to export metadata: {e}")


# ==================== CONVENIENCE FUNCTIONS ====================

def create_processor(project_path: str, api_key: Optional[str] = None) -> Optional[GeminiProcessor]:
    """
    Create a Gemini processor if enabled
    
    Args:
        project_path: Path to project folder
        api_key: Optional API key override
        
    Returns:
        GeminiProcessor instance or None if disabled
    """
    config = CONFIG.get('gemini_settings', {})
    
    if not config.get('enabled', False):
        logger.info("Gemini integration disabled in config")
        return None
    
    try:
        processor = GeminiProcessor(project_path, api_key)
        return processor
    except GeminiClientError as e:
        logger.error(f"Failed to create Gemini processor: {e}")
        return None


def interactive_title_selection(processor: GeminiProcessor) -> str:
    """
    Interactive title selection from generated options
    
    Args:
        processor: GeminiProcessor instance
        
    Returns:
        Selected title
    """
    options = processor.get_title_options()
    
    print("\n" + "=" * 60)
    print(CP("📝 GENERATED TITLE OPTIONS", 'cyan'))
    print("=" * 60)
    
    for idx, option in enumerate(options, 1):
        print(f"\n{idx}. [{option['style'].upper()}]")
        print(f"   {CP(option['title'], 'yellow')}")
    
    print(f"\n{len(options) + 1}. [CUSTOM] Enter your own title")
    print("=" * 60)
    
    while True:
        try:
            choice = input(CP("\n👉 Select title (1-{}): ".format(len(options) + 1), 'cyan')).strip()
            
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(options):
                selected_title = processor.select_title(choice_num - 1)
                print(CP(f"\n✅ Selected: {selected_title}", 'green'))
                return selected_title
            
            elif choice_num == len(options) + 1:
                custom_title = input(CP("   Enter custom title: ", 'cyan')).strip()
                if custom_title:
                    processor.set_custom_title(custom_title)
                    print(CP(f"\n✅ Custom title set: {custom_title}", 'green'))
                    return custom_title
                else:
                    print(CP("   ⚠️  Title cannot be empty", 'yellow'))
            
            else:
                print(CP("   ⚠️  Invalid choice", 'yellow'))
                
        except ValueError:
            print(CP("   ⚠️  Please enter a number", 'yellow'))
        except KeyboardInterrupt:
            print(CP("\n\n⚠️  Selection cancelled", 'yellow'))
            return options[0]['title']  # Return first option as default
