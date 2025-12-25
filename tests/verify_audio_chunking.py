import unittest
from unittest.mock import MagicMock, patch
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import video_pipeline

class TestAudioChunking(unittest.TestCase):
    
    @patch('core.video_pipeline._probe_duration')
    @patch('core.video_pipeline._split_audio_into_chunks')
    @patch('core.video_pipeline._load_whisper_model')
    @patch('core.video_pipeline._transcribe_segment_with_model')
    @patch('core.video_pipeline.Progress') # Mock UI
    def test_chunking_logic_flow(self, mock_progress, mock_transcribe, mock_load_model, mock_split, mock_probe):
        # Setup
        mock_probe.return_value = 3600.0 # 1 hour audio
        mock_split.return_value = ("/tmp/mock_dir", ["chunk1.mp3", "chunk2.mp3"])
        
        # Mock transcription results
        # Chunk 1: 0-10s
        mock_transcribe.side_effect = [
            [{"text": "A", "start": 1.0, "end": 2.0}],
            [{"text": "B", "start": 1.0, "end": 2.0}] # Relative to chunk start
        ]
        
        # Mock chunk durations (probe called inside loop)
        # First call is total duration (3600)
        # Next calls are chunk durations
        mock_probe.side_effect = [3600.0, 1800.0, 1800.0] 
        
        config = {
            "video_settings": {
                "caption_language": "en"
            }
        }
        
        # Execute
        result = video_pipeline.generate_timeline_from_audio(
            "fake_audio.mp3", "test_project", config, model_size="tiny"
        )
        
        # Verify Split was called
        mock_split.assert_called_once()
        
        # Verify Transcribe was called twice
        self.assertEqual(mock_transcribe.call_count, 2)
        
        # Verify Timeline Construction (Merging)
        # Expected:
        # Word A: start 1.0, end 2.0 (Chunk 1 offset 0)
        # Word B: start 1.0+1800 = 1801.0, end 2.0+1800 = 1802.0
        
        timeline = result["timeline"]
        # Filter for captions (fragments)
        captions = [x for x in timeline if x["type"] == "caption_fragment"]
        
        # We need to dig into the generated fragments or check the "words" if fragments aggregated them
        # The fragments logic aggregates words.
        # Let's check the words inside the payload of the fragments
        
        all_words = []
        for cap in captions:
            payload_words = cap["payload"]["words"]
            all_words.extend(payload_words)
            
        print(f"Captured words: {all_words}")
        
        self.assertEqual(len(all_words), 2)
        self.assertEqual(all_words[0]["text"], "A")
        self.assertAlmostEqual(all_words[0]["start"], 1.0)
        
        self.assertEqual(all_words[1]["text"], "B")
        self.assertAlmostEqual(all_words[1]["start"], 1801.0) # Check offset application

if __name__ == '__main__':
    unittest.main()
