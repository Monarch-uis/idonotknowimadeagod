import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from aligner import (
    simple_word_alignment,
    validate_timestamps,
    smooth_timestamps,
    calculate_alignment_confidence
)


class TestAligner:
    
    def test_simple_word_alignment(self):
        words = ['Hello', 'world', 'how', 'are', 'you']
        audio_features = np.random.rand(13, 100)
        
        timestamps = simple_word_alignment(words, audio_features)
        
        assert len(timestamps) == len(words)
        assert all('word' in ts for ts in timestamps)
        assert all('start' in ts for ts in timestamps)
        assert all('end' in ts for ts in timestamps)
        assert all(ts['end'] > ts['start'] for ts in timestamps)
    
    def test_validate_timestamps(self):
        timestamps = [
            {'word': 'Hello', 'start': 0.0, 'end': 1.0, 'duration': 1.0},
            {'word': 'world', 'start': 1.5, 'end': 2.0, 'duration': 0.5},
        ]
        
        validated = validate_timestamps(timestamps)
        
        assert len(validated) == len(timestamps)
        assert all(ts['end'] > ts['start'] for ts in validated)
    
    def test_validate_empty_timestamps(self):
        assert validate_timestamps([]) == []
    
    def test_smooth_timestamps(self):
        timestamps = [
            {'word': 'Hello', 'start': 0.0, 'end': 1.0, 'duration': 1.0},
            {'word': 'world', 'start': 1.0, 'end': 2.0, 'duration': 1.0},
        ]
        
        smoothed = smooth_timestamps(timestamps)
        
        assert len(smoothed) == len(timestamps)
        assert smoothed[0]['start'] == timestamps[0]['start']
        assert smoothed[-1]['end'] == timestamps[-1]['end']
    
    def test_calculate_alignment_confidence(self):
        audio_duration = 3.0
        timestamps = [
            {'word': 'Hello', 'start': 0.0, 'end': 1.0, 'duration': 1.0},
            {'word': 'world', 'start': 1.0, 'end': 2.0, 'duration': 1.0},
            {'word': 'test', 'start': 2.0, 'end': 3.0, 'duration': 1.0},
        ]
        
        confidence = calculate_alignment_confidence(timestamps, audio_duration)
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.8
    
    def test_calculate_confidence_empty(self):
        confidence = calculate_alignment_confidence([], 10.0)
        assert confidence == 0.0
