"""
Test Novel Name Mapper
Tests the automatic mapping feature
"""
import unittest
import os
import sys
import json
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from features.novel_name_mapper import NovelNameMapper, auto_save_mapping


class TestNovelNameMapper(unittest.TestCase):
    
    def setUp(self):
        """Create temporary mappings file for testing"""
        self.test_dir = tempfile.mkdtemp()
        self.test_mappings_file = os.path.join(self.test_dir, "test_mappings.json")
        self.mapper = NovelNameMapper(self.test_mappings_file)
    
    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_save_and_lookup_mapping(self):
        """Test saving and looking up a mapping"""
        # Save a mapping
        success = self.mapper.save_mapping(
            original_title="Naruto: The Seventh Hokage Chronicles",
            youtube_name="Naruto Becomes Hokage - Epic Fanfic",
            sanitized_title="Naruto_The_Seventh_Hokage_Chronicles",
            project_path="/path/to/project",
            chapter_range="1-50"
        )
        
        self.assertTrue(success)
        
        # Lookup by YouTube name
        result, match_type, score = self.mapper.lookup_by_youtube_name("Naruto Becomes Hokage")
        self.assertIsNotNone(result)
        self.assertEqual(result["original_title"], "Naruto: The Seventh Hokage Chronicles")
        self.assertEqual(result["youtube_name"], "Naruto Becomes Hokage - Epic Fanfic")
        self.assertIn(match_type, ["exact", "token", "fuzzy"])
    
    def test_lookup_by_original_title(self):
        """Test looking up by original title"""
        self.mapper.save_mapping(
            original_title="One Piece: The Grand Adventure",
            youtube_name="One Piece Fan Story",
            sanitized_title="One_Piece_The_Grand_Adventure",
            project_path="/path/to/project"
        )
        
        result = self.mapper.lookup_by_original_title("One Piece: The Grand Adventure")
        self.assertIsNotNone(result)
        self.assertEqual(result["youtube_name"], "One Piece Fan Story")
    
    def test_search_mappings(self):
        """Test fuzzy search"""
        self.mapper.save_mapping(
            original_title="Harry Potter Fanfic",
            youtube_name="HP Magic Adventures",
            sanitized_title="Harry_Potter_Fanfic",
            project_path="/path/to/project"
        )
        
        results = self.mapper.search_mappings("Harry")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["original_title"], "Harry Potter Fanfic")
    
    def test_update_existing_mapping(self):
        """Test updating an existing mapping with new chapter range"""
        # Save initial mapping
        self.mapper.save_mapping(
            original_title="Test Novel",
            youtube_name="Test YouTube Name",
            sanitized_title="Test_Novel",
            project_path="/path/to/project",
            chapter_range="1-50"
        )
        
        # Update with new chapter range
        self.mapper.save_mapping(
            original_title="Test Novel",
            youtube_name="Test YouTube Name",
            sanitized_title="Test_Novel",
            project_path="/path/to/project",
            chapter_range="51-100"
        )
        
        result = self.mapper.lookup_by_original_title("Test Novel")
        self.assertEqual(len(result["chapter_ranges"]), 2)
        self.assertIn("1-50", result["chapter_ranges"])
        self.assertIn("51-100", result["chapter_ranges"])
    
    def test_list_all_mappings(self):
        """Test listing all mappings"""
        self.mapper.save_mapping(
            original_title="Novel 1",
            youtube_name="YouTube 1",
            sanitized_title="Novel_1",
            project_path="/path/1"
        )
        
        self.mapper.save_mapping(
            original_title="Novel 2",
            youtube_name="YouTube 2",
            sanitized_title="Novel_2",
            project_path="/path/2"
        )
        
        all_mappings = self.mapper.list_all_mappings()
        self.assertEqual(len(all_mappings), 2)
    
    def test_persistence(self):
        """Test that mappings persist across instances"""
        # Save with first instance
        self.mapper.save_mapping(
            original_title="Persistent Novel",
            youtube_name="Persistent YouTube",
            sanitized_title="Persistent_Novel",
            project_path="/path/to/project"
        )
        
        # Create new instance with same file
        new_mapper = NovelNameMapper(self.test_mappings_file)
        result = new_mapper.lookup_by_original_title("Persistent Novel")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["youtube_name"], "Persistent YouTube")


if __name__ == "__main__":
    unittest.main()
