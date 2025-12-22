
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import epub_project_manager
from core.video_pipeline import generate_timeline_from_words

class TestCaptionIntegration(unittest.TestCase):
    def test_create_video_signature(self):
        """Verify create_video accepts word_timeline"""
        import inspect
        sig = inspect.signature(epub_project_manager.create_video)
        self.assertIn('word_timeline', sig.parameters)
        
        sig_recovery = inspect.signature(epub_project_manager.create_video_with_recovery)
        self.assertIn('word_timeline', sig_recovery.parameters)

    def test_video_pipeline_timeline_gen(self):
        """Verify generate_timeline_from_words works"""
        words = [{'text': 'Hello', 'start': 0.0, 'end': 0.5}]
        config = {'video_settings': {'caption_fragment_max_duration': 2.0}}
        with patch('core.video_pipeline._probe_duration', return_value=1.0):
            timeline = generate_timeline_from_words("dummy.mp3", "proj1", words, config)
            self.assertEqual(timeline['metadata']['source'], 'tts_timing')
            # Should have at least the caption fragment
            captions = [t for t in timeline['timeline'] if t.get('type') == 'caption_fragment']
            self.assertEqual(len(captions), 1)
            self.assertEqual(captions[0]['payload']['text'], 'Hello')

if __name__ == '__main__':
    unittest.main()
