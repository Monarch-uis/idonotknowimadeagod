#!/usr/bin/env python3
"""
Quick Novel Lookup Tool
========================
Paste a YouTube video name, get the original novel name instantly.

Usage:
    python lookup_novel.py

Then just paste the YouTube name when prompted!
"""

import os
import sys
from features.novel_name_mapper import NovelNameMapper
from core.utils import CP

def main():
    """Quick lookup interface"""
    print(CP("\n" + "="*60, 'cyan'))
    print(CP("  📺 QUICK NOVEL LOOKUP", 'cyan'))
    print(CP("="*60, 'cyan'))
    print("\nPaste the YouTube video name below:")
    print("(or type 'list' to see all mappings, 'q' to quit)\n")
    
    mapper = NovelNameMapper()
    
    while True:
        try:
            youtube_name = input(CP("👉 YouTube Name: ", 'yellow')).strip()
            
            if not youtube_name:
                continue
            
            if youtube_name.lower() == 'q':
                print(CP("\n👋 Goodbye!", 'white'))
                break
            
            if youtube_name.lower() == 'list':
                mappings = mapper.list_all_mappings()
                if not mappings:
                    print(CP("\n❌ No mappings found yet.", 'red'))
                    print("   Process a novel and rename it to create mappings.\n")
                    continue
                
                print(CP(f"\n📚 ALL NOVELS ({len(mappings)} total):", 'cyan'))
                print("="*60)
                for idx, m in enumerate(mappings, 1):
                    print(f"\n{idx}. {CP(m['youtube_name'], 'green')}")
                    print(f"   → Original: {m['original_title']}")
                    if m.get('chapter_ranges'):
                        print(f"   → Chapters: {', '.join(m['chapter_ranges'])}")
                print("\n" + "="*60 + "\n")
                continue
            
            # Lookup the novel
            result = mapper.lookup_by_youtube_name(youtube_name)
            
            if result:
                print(CP("\n✅ FOUND!", 'green'))
                print("="*60)
                print(CP(f"📖 Original Novel: {result['original_title']}", 'cyan'))
                print(f"📺 YouTube Name: {result['youtube_name']}")
                
                if result.get('chapter_ranges'):
                    print(f"📑 Processed Chapters: {', '.join(result['chapter_ranges'])}")
                
                print(f"📂 Project Path: {result['project_path']}")
                print("="*60 + "\n")
            else:
                print(CP(f"\n❌ Not found: '{youtube_name}'", 'red'))
                print("\n💡 Tips:")
                print("   • Try a shorter version (e.g., 'Naruto' instead of full title)")
                print("   • Type 'list' to see all available novels")
                print("   • Check spelling\n")
        
        except KeyboardInterrupt:
            print(CP("\n\n👋 Goodbye!", 'white'))
            break
        except EOFError:
            print(CP("\n\n👋 Goodbye!", 'white'))
            break
        except Exception as e:
            print(CP(f"\n❌ Error: {e}", 'red'))
            continue

if __name__ == "__main__":
    main()
