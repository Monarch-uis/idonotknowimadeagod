"""
TTS Subtitle Generator

A tool for generating accurate SRT subtitles by aligning known text with
TTS-generated audio using forced alignment.
"""

__version__ = '0.1.0'
__author__ = 'TTS Subtitle Generator'

from .text_processor import preprocess_text, validate_text_audio_match
from .audio_processor import load_audio, extract_features
from .aligner import align_text_to_audio
from .chunker import process_long_audio
from .srt_generator import generate_srt

__all__ = [
    'preprocess_text',
    'validate_text_audio_match',
    'load_audio',
    'extract_features',
    'align_text_to_audio',
    'process_long_audio',
    'generate_srt'
]
