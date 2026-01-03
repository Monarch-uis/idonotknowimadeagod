import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from srt_generator import (
    format_caption_text,
    format_srt_time,
    parse_srt_time,
    validate_srt_format,
    calculate_caption_stats
)


class TestSRTGenerator:
    
    def test_format_caption_text_short(self):
        words = ['Hello', 'world']
        config = {
            'max_words_per_line': 12,
            'max_lines_per_caption': 2
        }
        
        text = format_caption_text(words, config)
        
        assert text == 'Hello world'
        assert '\n' not in text
    
    def test_format_caption_text_long(self):
        words = ['This', 'is', 'a', 'very', 'long', 'caption', 'that', 'needs', 'to', 'be', 'split', 'into', 'two', 'lines']
        config = {
            'max_words_per_line': 7,
            'max_lines_per_caption': 2
        }
        
        text = format_caption_text(words, config)
        
        assert '\n' in text
        assert len(text.split('\n')) <= 2
    
    def test_format_srt_time(self):
        assert format_srt_time(0) == "00:00:00,000"
        assert format_srt_time(1.5) == "00:00:01,500"
        assert format_srt_time(61.75) == "00:01:01,750"
        assert format_srt_time(3661.25) == "01:01:01,250"
    
    def test_parse_srt_time(self):
        assert parse_srt_time("00:00:00,000") == 0.0
        assert parse_srt_time("00:00:01,500") == 1.5
        assert parse_srt_time("00:01:01,750") == 61.75
        assert parse_srt_time("01:01:01,250") == 3661.25
    
    def test_parse_srt_time_roundtrip(self):
        for seconds in [0, 1.5, 61.75, 3661.25, 7234.123]:
            formatted = format_srt_time(seconds)
            parsed = parse_srt_time(formatted)
            assert abs(parsed - seconds) < 0.001
    
    def test_validate_srt_format_valid(self):
        srt_content = """1
00:00:00,000 --> 00:00:05,000
First caption text

2
00:00:05,000 --> 00:00:10,000
Second caption text"""
        
        assert validate_srt_format(srt_content) == True
    
    def test_validate_srt_format_invalid(self):
        srt_content = """Invalid caption
00:00:00,000 --> 00:00:05,000
Text"""
        
        assert validate_srt_format(srt_content) == False
    
    def test_validate_srt_format_empty(self):
        assert validate_srt_format("") == False
        assert validate_srt_format("   ") == False
    
    def test_calculate_caption_stats(self):
        srt_content = """1
00:00:00,000 --> 00:00:05,000
First caption text

2
00:00:05,000 --> 00:00:10,000
Second caption text here"""
        
        stats = calculate_caption_stats(srt_content)
        
        assert stats['total_captions'] == 2
        assert stats['total_words'] == 7
        assert stats['total_duration'] == 10.0
        assert stats['avg_caption_duration'] == 5.0
        assert stats['avg_caption_length'] == 3.5
    
    def test_calculate_caption_stats_empty(self):
        stats = calculate_caption_stats("")
        
        assert stats['total_captions'] == 0
        assert stats['total_words'] == 0
        assert stats['total_duration'] == 0.0
