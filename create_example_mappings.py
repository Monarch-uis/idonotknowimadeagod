"""
Create Example Novel Mappings
Demonstrates the novel name mapping feature with sample data
"""

import os
import sys
from features.novel_name_mapper import NovelNameMapper

def create_example_mappings():
    """Create sample mappings for demonstration"""
    print("Creating example novel mappings...\n")
    
    mapper = NovelNameMapper()
    
    # Example 1: Naruto fanfic
    mapper.save_mapping(
        original_title="Naruto: The Seventh Hokage Chronicles",
        youtube_name="Naruto Becomes Hokage - Epic Fanfic",
        sanitized_title="Naruto_Becomes_Hokage_Epic_Fanfic",
        project_path=os.path.join(os.getcwd(), "active_novels", "Naruto_Becomes_Hokage_Epic_Fanfic"),
        chapter_range="1-50"
    )
    print("✅ Created: Naruto mapping")
    
    # Add second chapter range
    mapper.save_mapping(
        original_title="Naruto: The Seventh Hokage Chronicles",
        youtube_name="Naruto Becomes Hokage - Epic Fanfic",
        sanitized_title="Naruto_Becomes_Hokage_Epic_Fanfic",
        project_path=os.path.join(os.getcwd(), "active_novels", "Naruto_Becomes_Hokage_Epic_Fanfic"),
        chapter_range="51-100"
    )
    print("✅ Updated: Naruto mapping (added chapters 51-100)")
    
    # Example 2: One Piece fanfic
    mapper.save_mapping(
        original_title="One Piece: The Grand Adventure",
        youtube_name="One Piece Fan Story - Luffy's Journey",
        sanitized_title="One_Piece_Fan_Story_Luffys_Journey",
        project_path=os.path.join(os.getcwd(), "active_novels", "One_Piece_Fan_Story_Luffys_Journey"),
        chapter_range="1-75"
    )
    print("✅ Created: One Piece mapping")
    
    # Example 3: Harry Potter fanfic
    mapper.save_mapping(
        original_title="Harry Potter and the Magical Realms",
        youtube_name="HP Magic Adventures - Year 8",
        sanitized_title="HP_Magic_Adventures_Year_8",
        project_path=os.path.join(os.getcwd(), "active_novels", "HP_Magic_Adventures_Year_8"),
        chapter_range="1-30"
    )
    print("✅ Created: Harry Potter mapping")
    
    # Example 4: Attack on Titan fanfic
    mapper.save_mapping(
        original_title="Attack on Titan: Beyond the Walls",
        youtube_name="AOT Fanfic - Eren's New Path",
        sanitized_title="AOT_Fanfic_Erens_New_Path",
        project_path=os.path.join(os.getcwd(), "active_novels", "AOT_Fanfic_Erens_New_Path"),
        chapter_range="1-40"
    )
    print("✅ Created: Attack on Titan mapping")
    
    print(f"\n🎉 Created {len(mapper.list_all_mappings())} example mappings!")
    print("\nNow you can test the lookup tool:")
    print("  python lookup_novel.py")
    print("\nTry searching for:")
    print("  • Naruto")
    print("  • One Piece")
    print("  • HP Magic")
    print("  • AOT")

if __name__ == "__main__":
    create_example_mappings()
