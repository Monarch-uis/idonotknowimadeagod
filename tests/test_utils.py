import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.utils import sanitize_filename, seconds_to_time_str, extract_smart_number

class TestUtils(unittest.TestCase):
    
    def test_sanitize_filename(self):
        # Basic cases
        self.assertEqual(sanitize_filename("CleanName"), "CleanName")
        self.assertEqual(sanitize_filename("Space Name"), "Space Name")
        
        # Illegal characters
        self.assertEqual(sanitize_filename("Bad/Name"), "Bad_Name")
        self.assertEqual(sanitize_filename("Bad\\Name"), "Bad_Name")
        self.assertEqual(sanitize_filename("Name*"), "Name_")
        
        # Length limit (utils truncates to 60)
        long_name = "a" * 100
        sanitized = sanitize_filename(long_name, max_length=60)
        self.assertLessEqual(len(sanitized), 60)

    def test_seconds_to_time_str(self):
        self.assertEqual(seconds_to_time_str(30), "0:00:30")
        self.assertEqual(seconds_to_time_str(60), "0:01:00")
        self.assertEqual(seconds_to_time_str(3661), "1:01:01")

    def test_extract_smart_number(self):
        # Standard formats
        self.assertEqual(extract_smart_number("Chapter 1"), 1)
        self.assertEqual(extract_smart_number("Ch 10"), 10)
        self.assertEqual(extract_smart_number("Episode 5"), 5)
        
        # Weird formats
        self.assertEqual(extract_smart_number("c.3"), 3)
        self.assertEqual(extract_smart_number("12. The Beginning"), 12)
        
        # No number
        self.assertIsNone(extract_smart_number("Prologue"))
        self.assertIsNone(extract_smart_number("The End"))

if __name__ == '__main__':
    unittest.main()
