"""
UI Menus Module
Handles complex interactive menus and pre-flight summaries.
"""
import os
import shutil
from core.config import CONFIG, ACTIVE_NOVELS_DIR, logger
from core.utils import CP, extract_smart_number
from core.epub_io import (
    calculate_epub_hash, check_duplicate_epub, get_history_summary,
    delete_book_from_history
)

def show_chapter_overview(all_chapters):
    """
    Unified chapter overview and gap detection logic.
    """
    print(f"\n{'=' * 50}")
    print(f"TOTAL CHAPTERS: {len(all_chapters)}")
    print(f"{'=' * 50}")
    print("First 30:")
    for i in range(min(30, len(all_chapters))):
        title = all_chapters[i][0]
        num = extract_smart_number(title)
        if num is not None:
            print(f"   [{i+1:3}] → Ch {num:4} | {title[:50]}")
        else:
            print(f"   [{i+1:3}] → {'':10} | {title[:60]}")
    
    if len(all_chapters) > 60:
        print("   ...")
        print("Last 30:")
        for i in range(max(len(all_chapters) - 30, 0), len(all_chapters)):
            title = all_chapters[i][0]
            num = extract_smart_number(title)
            if num is not None:
                print(f"   [{i+1:3}] → Ch {num:4} | {title[:50]}")
            else:
                print(f"   [{i+1:3}] → {'':10} | {title[:60]}")
    
    # Gap detection
    nums = [extract_smart_number(t[0]) for t in all_chapters if extract_smart_number(t[0]) is not None]
    if len(nums) > 1:
        gaps = []
        for i in range(len(nums) - 1):
            if nums[i + 1] - nums[i] > 1:
                gaps.append(f"{nums[i]+1}-{nums[i+1]-1}")
        if gaps:
            print(CP(f"\n⚠️  WARNING: Missing chapters: {', '.join(gaps)}", 'yellow'))
            print("   → Consider smaller batch sizes\n")
    
    print(f"{'=' * 50}\n")

def enforce_batch_size_limit(batch_size, max_batch):
    """Ensure batch size stays within configured limits"""
    if batch_size <= max_batch:
        return True

    warning_msg = f"Batch size {batch_size} exceeds recommended max ({max_batch})"
    print(CP(f"   ⚠️  {warning_msg}", 'yellow'))
    logger.warning(warning_msg)
    return False

def resolve_project_name_and_history(selected_path, meta, cli_args, auto_resume=False):
    """
    Consolidated project detection UI.
    Merges duplicate mapping info and previous history into one unified interface.
    Returns: (final_title, updated_meta, history_reset_performed)
    """
    from features.novel_name_mapper import NovelNameMapper, check_duplicate_interactive
    mapper = NovelNameMapper()
    
    epub_hash = calculate_epub_hash(selected_path)
    original_title = meta['title']
    mapping = mapper.lookup_by_original_title(original_title)
    
    # Check history
    dup_info = None
    if epub_hash:
        dup_info = check_duplicate_epub(selected_path)
    if not dup_info:
        search_title = mapping['youtube_name'] if mapping else original_title
        dup_info = get_history_summary(search_title)
        
    final_title = mapping['youtube_name'] if mapping else original_title
    active_title = dup_info['title'] if dup_info else final_title
    
    if dup_info or mapping:
        # Display Combined info
        print(CP(f"\n{'='*60}", 'yellow'))
        print(CP(f"⚠️  PREVIOUS PROJECT DETECTED", 'yellow'))
        print(CP(f"{'='*60}", 'yellow'))
        
        # Details (Bullet points)
        print(f"   💡 Found project details:")
        print(f"      • YouTube Name: '{active_title}'")
        print(f"      • Original EPUB: '{original_title}'")
        
        if dup_info:
            print(f"      • Last Activity: {dup_info['date']}")
            print(f"      • Progress:      Ch {dup_info['start']} - {dup_info['end']}")
        elif mapping:
            date_str = mapping.get('last_updated', mapping.get('created_date', 'Unknown'))
            if 'T' in date_str: date_str = date_str.split('T')[0]
            print(f"      • Last Sync:     {date_str}")
            
        if epub_hash:
            print(f"      • Hash:          {epub_hash[:16]}...")
        print(CP(f"{'='*60}", 'yellow'))
        
        # Options
        print(f"\n   [1] " + CP("Open Existing Project", 'green') + " (Continue where you left off)")
        print(f"   [2] " + CP("Full Reset", 'red') + "           (Wipe history and start fresh)")
        print(f"   [3] " + CP("Partial Reset", 'blue') + "        (Wipe history only for current range)")
        print(f"   [4] " + CP("Cancel", 'white'))
        
        # Handle Selection
        if cli_args and getattr(cli_args, 'auto', False):
            choice = '2'
            print(f"\n   ℹ️  Auto-selecting [2] Full Reset via CLI")
        elif auto_resume:
            choice = '1'
            print(f"\n   ℹ️  Auto-selecting [1] Open Existing Project (Resume)")
        else:
            choice = input(f"\n   {CP('👉 Select (1-4):', 'cyan')} ").strip()
            
        if choice == '1':
            final_title = active_title
            meta['title'] = final_title
            return final_title, meta, False
            
        elif choice == '2':
            if not (cli_args and getattr(cli_args, 'auto', False)):
                confirm = input(f"\n   {CP('⚠️  REALLY WIPE ALL HISTORY?', 'red')} (y/n): ").strip().lower()
                if confirm != 'y': return active_title, meta, False
            
            # Wipe
            success, count = delete_book_from_history(selected_path, title=active_title)
            if success: print(CP(f"   ✅ History Purged ({count} entries).", 'green'))
            
            # Folder wipe?
            if not (cli_args and getattr(cli_args, 'auto', False)):
                wipe_f = input(f"   {CP('🗑️  Also delete existing project files?', 'yellow')} (y/n): ").strip().lower()
                if wipe_f == 'y' and dup_info:
                    dup_path = os.path.join(ACTIVE_NOVELS_DIR, dup_info['key'])
                    if os.path.exists(dup_path):
                        try: shutil.rmtree(dup_path); print(CP("   ✅ Project folder deleted.", 'green'))
                        except Exception as e: print(CP(f"   ❌ Folder deletion failed: {e}", 'red'))
            
            # New Name
            if cli_args and getattr(cli_args, 'auto', False):
                final_title = original_title
                print(f"\n   ℹ️  Auto-keeping original title: {final_title}")
            else:
                new_title = input("\n   Enter new project name (Enter to keep original): ").strip()
                if new_title:
                    final_title = check_duplicate_interactive(original_title, new_title)
                else:
                    final_title = original_title
            
            meta['title'] = final_title
            return final_title, meta, True
            
        elif choice == '3':
            print(f"\n   ℹ️  Partial reset will trigger based on the ranges you select next.")
            meta['_partial_reset_pending'] = True
            final_title = active_title
            meta['title'] = final_title
            return final_title, meta, False
            
        else: # Cancel
            return None, None, False
    else:
        # Standard initial name prompt
        print(CP(f"\n📘 Original Title: {original_title}", 'cyan'))
        new_title = input("   Press Enter to keep, or type new name: ").strip()
        if new_title:
            final_title = check_duplicate_interactive(original_title, new_title)
            meta['title'] = final_title
        return final_title, meta, False

def show_preflight_summary(meta, total_available, selected_total, batch_size, engine, voice, speed, use_concurrent, tts_delay, mode, auto_confirm=False):
    """Show preflight summary with risk tips before processing"""
    print("\n" + "=" * 60)
    print(CP("📋 PREFLIGHT SUMMARY", 'cyan'))
    print("=" * 60)
    
    print(f"\n📚 Book: {meta['title']}")
    print(f"   Chapters available: {total_available}")
    print(f"   Chapters selected: {selected_total}")
    print(f"   Mode: {'Batch' if mode == '1' else 'Manual'}")
    
    if mode == "1" and batch_size and selected_total:
        estimated_batches = (selected_total + batch_size - 1) // batch_size
        print(f"   Batch size: {batch_size} chapters")
        print(f"   Estimated batches: {estimated_batches}")
    
    print(f"\n🎤 TTS Settings:")
    print(f"   Engine: {engine.upper()}")
    print(f"   Voice: {voice}")
    print(f"   Speed: {speed}")
    print(f"   Concurrent: {'Yes' if use_concurrent else 'No'}")
    
    if engine == "edge":
        print(f"   Request delay: {tts_delay}s")
    
    # Risk tips based on configuration
    print(f"\n⚠️  Risk Assessment:")
    risks = []
    
    if engine == "edge" and use_concurrent:
        if tts_delay < 0.5:
            risks.append("   ⚠️  Low Edge-TTS delay may cause rate limit (403 errors)")
        else:
            risks.append("   ✅ Edge-TTS delay looks safe")
        
        if batch_size and batch_size > 30:
            risks.append("   ⚠️  Large batches with concurrent Edge-TTS may hit limits")
    
    if batch_size and batch_size > 50:
        limits = CONFIG.get("system_limits", {})
        max_batch = limits.get("max_batch_size", 50)
        if batch_size > max_batch:
            risks.append(f"   ⚠️  Batch size ({batch_size}) exceeds recommended max ({max_batch})")
    
    if engine == "edge" and not use_concurrent:
        risks.append("   ℹ️  Sequential Edge-TTS is slow but very safe")
    
    if not risks:
        risks.append("   ✅ Configuration looks good!")
    
    for risk in risks:
        print(risk)
    
    print("\n" + "=" * 60)
    
    if auto_confirm:
         print("\n👉 Proceeding automatically (auto-confirm enabled)...")
         return True
         
    proceed = input("\n👉 Proceed with processing? (y/n, default y): ").strip().lower()
    return proceed != 'n'
