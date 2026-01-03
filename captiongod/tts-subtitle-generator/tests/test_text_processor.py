import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from text_processor import (
    normalize_quotes,
    normalize_dashes,
    remove_html_artifacts,
    expand_contractions,
    split_sentences,
    number_to_words,
    validate_text_audio_match
)


class TestTextProcessor:
    
    def test_normalize_quotes(self):
        text = '“Fancy quotes” and ‘single quotes’'
        result = normalize_quotes(text)
        assert '"' in result
        assert "'" in result
        assert '“' not in result
        assert '‘' not in result
    
    def test_normalize_dashes(self):
        text = 'Long dash — and medium dash –'
        result = normalize_dashes(text)
        assert '—' not in result
        assert '–' not in result
        assert result.count('-') >= 2
    
    def test_remove_html_artifacts(self):
        text = '<p>Hello</p> and **bold** text'
        result = remove_html_artifacts(text)
        assert '<p>' not in result
        assert '</p>' not in result
        assert '**' not in result
        assert 'Hello' in result
    
    def test_expand_contractions(self):
        text = "I can't believe it's true"
        result = expand_contractions(text)
        assert 'cannot' in result
        assert ' is ' in result
    
    def test_split_sentences(self):
        text = "Hello world. How are you? I'm fine."
        sentences = split_sentences(text)
        assert len(sentences) == 3
        assert sentences[0] == "Hello world."
        assert sentences[1] == "How are you?"
    
    def test_number_to_words(self):
        assert number_to_words(0) == "zero"
        assert number_to_words(5) == "five"
        assert number_to_words(21) == "twenty one"
        assert number_to_words(100) == "one hundred"
        assert number_to_words(123) == "one hundred twenty three"
    
    def test_validate_text_audio_match(self):
        text = "Hello world " * 100
        audio_duration = 80.0
        is_valid, expected, actual = validate_text_audio_match(text, audio_duration)
        
        assert expected > 0
        assert actual == audio_duration
        assert isinstance(is_valid, bool)
