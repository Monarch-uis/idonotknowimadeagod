
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
            self.assertEqual(len(captions), 1)
            self.assertEqual(captions[0]['payload']['text'], 'Hello')

    @patch('core.video_pipeline._probe_duration')
    @patch('core.video_pipeline._split_audio_into_chunks')
    @patch('core.video_pipeline._load_whisper_model')
    @patch('core.video_pipeline._transcribe_segment_with_model')
    @patch('core.video_pipeline.Progress') # Mock UI
    def test_chunking_logic_flow(self, mock_progress, mock_transcribe, mock_load_model, mock_split, mock_probe):
        """Verify audio chunking when video > 30 minutes"""
        from core import video_pipeline
        
        # Setup
        mock_probe.return_value = 3600.0 # 1 hour audio
        mock_split.return_value = ("/tmp/mock_dir", ["chunk1.mp3", "chunk2.mp3"])
        
        # Mock transcription results
        mock_transcribe.side_effect = [
            [{"text": "A", "start": 1.0, "end": 2.0}],
            [{"text": "B", "start": 1.0, "end": 2.0}] # Relative to chunk start
        ]
        
        # Sequence of probe calls: Total, then Chunk 1, then Chunk 2
        mock_probe.side_effect = [3600.0, 1800.0, 1800.0] 
        
        config = {
            "video_settings": {
                "caption_language": "en"
            }
        }
        
        # Execute
        video_pipeline.generate_timeline_from_audio(
            "fake_audio.mp3", "test_project", config, model_size="tiny"
        )
        
        # Verify Split was called
        mock_split.assert_called_once()
        
        # Verify Transcribe was called twice (once per chunk)
        self.assertEqual(mock_transcribe.call_count, 2)

if __name__ == '__main__':
    unittest.main()

