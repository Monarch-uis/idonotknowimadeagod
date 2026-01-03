import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from chunker import (
    estimate_chunks,
    split_text_into_chunks,
    merge_timestamps,
    remove_overlap_timestamps,
    format_time
)


class TestChunker:
    
    def test_estimate_chunks(self):
        assert estimate_chunks(100, 600) == 1
        assert estimate_chunks(600, 600) == 1
        assert estimate_chunks(601, 600) == 2
        assert estimate_chunks(1800, 600) == 3
    
    def test_split_text_into_chunks_single(self):
        tokens = ['word'] * 10
        chunks = split_text_into_chunks(tokens, 1)
        
        assert len(chunks) == 1
        assert len(chunks[0]) == 10
    
    def test_split_text_into_chunks_multiple(self):
        tokens = ['word'] * 100
        chunks = split_text_into_chunks(tokens, 5)
        
        assert len(chunks) == 5
        total_words = sum(len(chunk) for chunk in chunks)
        assert total_words == 100
    
    def test_split_text_into_chunks_empty(self):
        chunks = split_text_into_chunks([], 3)
        assert len(chunks) == 1
        assert chunks[0] == []
    
    def test_merge_timestamps_no_overlap(self):
        chunk_results = [
            {
                'offset': 0.0,
                'timestamps': [
                    {'word': 'Hello', 'start': 0.0, 'end': 1.0, 'duration': 1.0, 'confidence': 1.0}
                ]
            },
            {
                'offset': 2.0,
                'timestamps': [
                    {'word': 'world', 'start': 0.0, 'end': 1.0, 'duration': 1.0, 'confidence': 1.0}
                ]
            }
        ]
        
        merged = merge_timestamps(chunk_results, overlap=2.0)
        
        assert len(merged) == 2
        assert merged[0]['start'] == 0.0
        assert merged[1]['start'] == 2.0
    
    def test_merge_timestamps_empty(self):
        assert merge_timestamps([]) == []
    
    def test_remove_overlap_timestamps(self):
        timestamps = [
            {'word': 'Hello', 'start': 0.0, 'end': 2.0, 'chunk_id': 0},
            {'word': 'world', 'start': 1.5, 'end': 3.0, 'chunk_id': 1},
            {'word': 'test', 'start': 3.0, 'end': 4.0, 'chunk_id': 1},
        ]
        
        deduplicated = remove_overlap_timestamps(timestamps, overlap_threshold=2.0)
        
        assert len(deduplicated) == 3
        assert deduplicated[0]['word'] == 'Hello'
        assert deduplicated[1]['word'] == 'world'
        assert deduplicated[2]['word'] == 'test'
    
    def test_remove_overlap_timestamps_empty(self):
        assert remove_overlap_timestamps([]) == []
    
    def test_format_time(self):
        assert format_time(0) == "0:00"
        assert format_time(59) == "0:59"
        assert format_time(60) == "1:00"
        assert format_time(65) == "1:05"
        assert format_time(3661) == "1:01:01"
        assert format_time(7200) == "2:00:00"
