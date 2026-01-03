"""
GEMINI INTEGRATION - CODE SNIPPETS FOR epub_project_manager.py

This file contains code snippets showing how to integrate Gemini AI
into your main epub_project_manager.py workflow.

Copy and adapt these snippets as needed.
"""

# ============================================================
# STEP 1: ADD IMPORTS AT TOP OF FILE
# ============================================================

"""
Add these imports after your existing imports:
"""

from features.gemini_processor import (
    GeminiProcessor, 
    create_processor,
    interactive_title_selection
)
from features.multispeaker_tts import (
    gen_multispeaker_chapter,
    generate_intro_audio,
    print_segment_summary
)
from core.gemini_client import GeminiClientError

# ============================================================
# STEP 2: AFTER PARSING EPUB - ADD GEMINI ANALYSIS
# ============================================================

"""
After you've parsed the EPUB and have all chapters,
add this Phase 1 analysis code:
"""

def run_phase1_analysis(chapters, book_metadata, project_path):
    """
    Run Gemini Phase 1: Story Analysis
    
    Args:
        chapters: List of chapter dicts with 'content'
        book_metadata: Dict with 'title', 'total_chapters', etc.
        project_path: Path to project folder
        
    Returns:
        (processor, selected_title, description) or (None, None, None) if disabled/failed
    """
    # Check if Gemini is enabled
    if not CONFIG.get('gemini_settings', {}).get('enabled', False):
        print(CP("   ℹ️  Gemini AI disabled in config", 'yellow'))
        return None, None, None
    
    try:
        # Create processor
        processor = create_processor(project_path)
        if not processor:
            return None, None, None
        
        # Check if already analyzed
        if processor.story_analyzed:
            print(CP("\n✅ Story already analyzed with Gemini AI", 'green'))
            use_existing = input(CP("   Use existing analysis? [Y/n]: ", 'cyan')).strip().lower()
            
            if use_existing != 'n':
                # Use cached results
                selected_title = processor.metadata.get('user_selections', {}).get('title')
                description = processor.get_description()
                
                if not selected_title:
                    selected_title = interactive_title_selection(processor)
                
                return processor, selected_title, description
        
        # Run analysis
        print(CP("\n🤖 Running Gemini AI Story Analysis...", 'cyan'))
        
        # Combine all chapter text
        full_text = "\n\n".join([ch.get('content', '') for ch in chapters])
        
        # Analyze
        results = processor.analyze_story(
            full_text=full_text,
            book_metadata=book_metadata,
            force=False
        )
        
        # Let user select title
        selected_title = interactive_title_selection(processor)
        
        # Get description
        description = processor.get_description()
        
        print(CP("\n✅ Phase 1 Complete!", 'green'))
        print(f"   Title: {selected_title}")
        print(f"   Description: {len(description)} characters")
        
        # Show usage
        stats = processor.client.get_usage_stats()
        print(f"   Cost: ${stats['estimated_cost_usd']:.4f}")
        
        return processor, selected_title, description
        
    except GeminiClientError as e:
        print(CP(f"\n❌ Gemini analysis failed: {e}", 'red'))
        print(CP("   Continuing with manual mode...", 'yellow'))
        return None, None, None
    except Exception as e:
        logger.error(f"Unexpected error in Phase 1: {e}")
        return None, None, None


# ============================================================
# STEP 3: IN BATCH PROCESSING LOOP - ADD PHASE 2
# ============================================================

"""
When processing each batch (e.g., chapters 1-20, 21-40, etc.),
add this Phase 2 code:
"""

def process_batch_with_gemini(
    processor,
    batch_number,
    batch_chapters,
    upload_date=None
):
    """
    Process batch with Gemini AI
    
    Args:
        processor: GeminiProcessor instance (or None if disabled)
        batch_number: Batch number (1, 2, 3, ...)
        batch_chapters: List of chapter dicts
        upload_date: Optional upload date string
        
    Returns:
        batch_results dict with intro and chapter segments
    """
    if processor is None:
        print(CP("   ℹ️  Gemini disabled, using standard TTS", 'yellow'))
        return None
    
    try:
        # Extract chapter texts
        chapter_texts = [ch.get('content', '') for ch in batch_chapters]
        
        # Run Phase 2
        print(CP(f"\n🎬 Processing Batch {batch_number} with Gemini...", 'cyan'))
        
        batch_results = processor.process_batch(
            batch_number=batch_number,
            batch_chapters=chapter_texts,
            upload_date=upload_date or datetime.now().strftime('%B %Y')
        )
        
        return batch_results
        
    except Exception as e:
        logger.error(f"Batch {batch_number} Gemini processing failed: {e}")
        print(CP(f"   ⚠️  Batch processing failed, using fallback", 'yellow'))
        return None


# ============================================================
# STEP 4: GENERATE INTRO AUDIO
# ============================================================

"""
Generate intro audio for the batch:
"""

def generate_batch_intro(batch_results, output_audio_path):
    """
    Generate intro audio from batch results
    
    Args:
        batch_results: Results from process_batch_with_gemini
        output_audio_path: Where to save intro audio
        
    Returns:
        (success, audio_path or None)
    """
    if not batch_results or 'intro' not in batch_results:
        return False, None
    
    intro_data = batch_results['intro']
    intro_text = intro_data.get('intro_text', '')
    voice_rec = intro_data.get('voice_recommendation', 'chatterbox')
    
    print(CP("   🎙️  Generating intro audio...", 'cyan'))
    print(f"      Text: {intro_text[:60]}...")
    print(f"      Voice: {voice_rec}")
    
    success, error = generate_intro_audio(
        intro_text=intro_text,
        output_path=output_audio_path,
        voice_recommendation=voice_rec
    )
    
    if success:
        print(CP("   ✅ Intro generated!", 'green'))
        return True, output_audio_path
    else:
        print(CP(f"   ❌ Intro failed: {error}", 'red'))
        return False, None


# ============================================================
# STEP 5: GENERATE MULTI-SPEAKER CHAPTER AUDIO
# ============================================================

"""
Generate chapter audio with multiple voices:
"""

def generate_chapter_with_multispeaker(
    chapter_number,
    batch_results,
    output_audio_path,
    temp_dir
):
    """
    Generate chapter audio with multi-speaker TTS
    
    Args:
        chapter_number: Chapter number
        batch_results: Results from process_batch_with_gemini
        output_audio_path: Where to save audio
        temp_dir: Temp directory for segments
        
    Returns:
        (success, subtitle_data or None)
    """
    if not batch_results:
        print(CP("   ℹ️  No Gemini data, using standard TTS", 'yellow'))
        return False, None
    
    # Find chapter in results
    chapter_data = None
    for ch in batch_results.get('chapters', []):
        if ch['chapter_number'] == chapter_number:
            chapter_data = ch
            break
    
    if not chapter_data:
        print(CP(f"   ⚠️  Chapter {chapter_number} not found in batch results", 'yellow'))
        return False, None
    
    segments = chapter_data.get('segments', [])
    if not segments:
        return False, None
    
    print(CP(f"   🎤 Generating multi-speaker audio for Chapter {chapter_number}...", 'cyan'))
    print_segment_summary(segments)
    
    success, error, subtitle_data = gen_multispeaker_chapter(
        segments=segments,
        output_path=output_audio_path,
        temp_dir=temp_dir,
        chapter_number=chapter_number
    )
    
    if success:
        print(CP(f"   ✅ Chapter {chapter_number} audio complete!", 'green'))
        return True, subtitle_data
    else:
        print(CP(f"   ❌ Failed: {error}", 'red'))
        return False, None


# ============================================================
# STEP 6: FULL WORKFLOW EXAMPLE
# ============================================================

"""
Here's how to integrate everything into your main workflow:
"""

def main_with_gemini_integration():
    """
    Complete workflow with Gemini integration
    """
    
    # ... your existing EPUB selection code ...
    
    # Parse EPUB
    print(CP("📖 Parsing EPUB...", 'cyan'))
    chapters, metadata = parse_full_epub(epub_path)
    
    book_metadata = {
        'title': metadata.get('title', 'Unknown'),
        'total_chapters': len(chapters),
        'author': metadata.get('author', 'Unknown')
    }
    
    # Setup project folders
    project_path = setup_project_folders(book_metadata['title'], ACTIVE_NOVELS_DIR)
    
    # ====== PHASE 1: STORY ANALYSIS ======
    print("\n" + "=" * 60)
    print(CP("PHASE 1: STORY ANALYSIS", 'cyan'))
    print("=" * 60)
    
    processor, selected_title, description = run_phase1_analysis(
        chapters, 
        book_metadata, 
        project_path
    )
    
    if processor:
        print(f"\n✅ Using AI-generated title: {selected_title}")
        print(f"✅ Using AI-generated description")
    else:
        print("\n⏩ Continuing with manual mode")
        selected_title = metadata.get('title', 'Unknown')
        description = "Manual description"
    
    # ... your existing batch configuration ...
    
    # ====== PHASE 2: BATCH PROCESSING ======
    batch_size = 20
    total_batches = (len(chapters) + batch_size - 1) // batch_size
    
    for batch_num in range(1, total_batches + 1):
        print("\n" + "=" * 60)
        print(CP(f"PROCESSING BATCH {batch_num}/{total_batches}", 'cyan'))
        print("=" * 60)
        
        # Get batch chapters
        start_idx = (batch_num - 1) * batch_size
        end_idx = min(start_idx + batch_size, len(chapters))
        batch_chapters = chapters[start_idx:end_idx]
        
        # Process with Gemini
        batch_results = process_batch_with_gemini(
            processor,
            batch_num,
            batch_chapters,
            upload_date="January 2025"
        )
        
        # Generate intro
        intro_path = os.path.join(project_path, f"audio/batch{batch_num}_intro.wav")
        if batch_results:
            generate_batch_intro(batch_results, intro_path)
        
        # Generate chapter audio
        for idx, chapter in enumerate(batch_chapters):
            chapter_num = start_idx + idx + 1
            audio_path = os.path.join(project_path, f"audio/chapter_{chapter_num}.wav")
            temp_dir = os.path.join(project_path, f"temp/segments/ch{chapter_num}")
            
            print(f"\n📝 Chapter {chapter_num}:")
            
            # Try multi-speaker
            if batch_results:
                success, subtitle_data = generate_chapter_with_multispeaker(
                    chapter_num,
                    batch_results,
                    audio_path,
                    temp_dir
                )
                
                if success:
                    # Use subtitle_data for video generation
                    # ... your video generation code ...
                    continue
            
            # Fallback to standard TTS
            print(CP("   Using standard TTS (fallback)", 'yellow'))
            # ... your existing TTS code ...
        
        # ... your existing video generation code ...
    
    # Final summary
    if processor:
        processor.print_summary()
    
    print(CP("\n✅ All batches complete!", 'green'))


# ============================================================
# STEP 7: OPTIONAL - STANDALONE TESTING
# ============================================================

"""
Test Gemini integration separately:
"""

def test_gemini_integration():
    """Test Gemini integration with a sample EPUB"""
    
    from core.gemini_client import test_gemini_connection
    
    print("Testing Gemini connection...")
    
    if test_gemini_connection():
        print(CP("✅ Gemini API connection successful!", 'green'))
    else:
        print(CP("❌ Gemini API connection failed", 'red'))
        return
    
    # Test with sample text
    processor = GeminiProcessor("./test_project")
    
    sample_text = """
    Chapter 1: The Beginning
    
    Naruto stood atop the Hokage monument, gazing over the village. 
    "I'll prove them all wrong," he said with determination.
    Sakura approached from behind. "Naruto-kun, wait!" she called out.
    
    The sun set over Konoha as destiny began to unfold.
    """
    
    metadata = {
        'title': 'Test Novel',
        'total_chapters': 1
    }
    
    try:
        # Test Phase 1
        print("\nTesting Phase 1...")
        results = processor.analyze_story(sample_text, metadata)
        print(f"Characters found: {len(results['story_analysis']['characters'])}")
        print(f"Title options: {len(results['title_options'])}")
        
        # Test Phase 2
        print("\nTesting Phase 2...")
        batch_results = processor.process_batch(
            batch_number=1,
            batch_chapters=[sample_text],
            upload_date="Test Date"
        )
        print(f"Segments generated: {len(batch_results['chapters'][0]['segments'])}")
        
        processor.print_summary()
        
        print(CP("\n✅ All tests passed!", 'green'))
        
    except Exception as e:
        print(CP(f"\n❌ Test failed: {e}", 'red'))


if __name__ == "__main__":
    # Run test
    test_gemini_integration()
