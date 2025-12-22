import unittest
import os
import sys
import shutil
import tempfile

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from features.chapter_merger import ChapterMerger

class TestChapterMerger(unittest.TestCase):
    def setUp(self):
        self.merger = ChapterMerger(min_word_count=50)
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_estimate_word_count(self):
        text = "word " * 10
        self.assertEqual(self.merger.estimate_word_count(text), 10)

    def test_merge_small_chapters(self):
        """Test merging 3 small chapters into 1"""
        # 20 words each, total 60 (threshold 50)
        chaps = [
            ("Ch1", "word " * 20),
            ("Ch2", "word " * 20),
            ("Ch3", "word " * 20)
        ]
        
        # Note: ChapterMerger handles the saving to temp file
        merged = self.merger.merge_chapters(chaps, None, self.test_dir)
        
        self.assertEqual(len(merged), 1)
        self.assertTrue("Ch1" in merged[0][0])
        self.assertTrue("Ch2" in merged[0][0])
        self.assertTrue("Ch3" in merged[0][0])
        
        # Check if file was created
        path = merged[0][1]
        self.assertTrue(os.path.exists(path))

    def test_no_merge_needed(self):
        """Test chapters above threshold are kept as is"""
        chaps = [
            ("Ch1", "word " * 100),
            ("Ch2", "word " * 100)
        ]
        merged = self.merger.merge_chapters(chaps, None, self.test_dir)
        
        self.assertEqual(len(merged), 2)
        # Content should remain as text, not a filepath
        self.assertEqual(merged[0][1], chaps[0][1])

    def test_mixed_merge(self):
        """Test small chapters merging until threshold, then starting new"""
        # Threshold 50
        # Ch1(20) + Ch2(20) + Ch3(20) = 60 -> Merge
        # Ch4(100) -> Keep
        chaps = [
            ("Ch1", "word " * 20),
            ("Ch2", "word " * 20),
            ("Ch3", "word " * 20),
            ("Ch4", "word " * 100)
        ]
        
        merged = self.merger.merge_chapters(chaps, None, self.test_dir)
        
        # Should result in 2 chapters: {Ch1+Ch2+Ch3} and {Ch4}
        self.assertEqual(len(merged), 2)
        self.assertTrue("Ch1" in merged[0][0])
        self.assertEqual(merged[1][0], "Ch4")

if __name__ == '__main__':
    unittest.main()
