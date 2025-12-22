"""
Tests for EPUB parsing functionality

Tests cover:
- EPUB file loading and validation
- Chapter extraction
- HTML to text conversion
- Pronunciation fixes application
- Banned word filtering
"""

import pytest
import sys
from pathlib import Path
from bs4 import BeautifulSoup

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.epub_io import parse_full_epub, clean_html_for_tts
from core.utils import fix_pronunciation, censor_text


@pytest.mark.unit
def test_extract_text_from_html_basic():
    """Test basic HTML to text conversion"""
    html = """
    <html>
        <body>
            <h1>Chapter Title</h1>
            <p>This is a paragraph.</p>
            <p>Another paragraph here.</p>
        </body>
    </html>
    """
    
    title, text = clean_html_for_tts(html)
    
    assert "Chapter Title" in title
    assert "This is a paragraph" in text
    assert "Another paragraph" in text
    assert "<h1>" not in text  # HTML tags should be removed
    assert "<p>" not in text


@pytest.mark.unit
def test_extract_text_removes_scripts_and_styles():
    """Test that script and style tags are removed"""
    html = """
    <html>
        <head>
            <style>body { color: red; }</style>
            <script>alert('test');</script>
        </head>
        <body>
            <p>Visible text</p>
        </body>
    </html>
    """
    
    _, text = clean_html_for_tts(html)
    
    assert "Visible text" in text
    assert "color: red" not in text
    assert "alert" not in text


@pytest.mark.unit
def test_apply_pronunciation_fixes():
    """Test pronunciation fixes are applied correctly"""
    pronunciation_map = {
        "Naruto": "Na-roo-toe",
        "Sasuke": "Soss-kay",
        "Hokage": "Ho-kah-gay"
    }
    
    text = "Naruto and Sasuke went to see the Hokage."
    fixed_text = fix_pronunciation(text, pronunciation_map)
    
    assert "Na-roo-toe" in fixed_text
    assert "Soss-kay" in fixed_text
    assert "Ho-kah-gay" in fixed_text
    assert "Naruto" not in fixed_text


@pytest.mark.unit
def test_apply_pronunciation_fixes_case_insensitive():
    """Test pronunciation fixes work regardless of case"""
    pronunciation_map = {
        "test": "tehst"
    }
    
    text = "This is a Test and another TEST."
    fixed_text = fix_pronunciation(text, pronunciation_map)
    
    # Should replace all variations
    assert "tehst" in fixed_text.lower()


@pytest.mark.unit
def test_filter_banned_words():
    """Test banned words are filtered out"""
    banned_patterns = [r"\btest\b", r"\bbad\w*"]
    
    text = "This is a test sentence with bad words and badness."
    filtered_text = censor_text(text, banned_patterns)
    
    assert "test" not in filtered_text.lower()
    assert "bad" not in filtered_text.lower()
    assert "This is a" in filtered_text  # Other words remain


@pytest.mark.unit
def test_filter_banned_words_preserves_partial_matches():
    """Test that partial word matches are not filtered"""
    banned_patterns = [r"\btest\b"]  # Only exact word "test"
    
    text = "This is a test of testing and testament."
    filtered_text = censor_text(text, banned_patterns)
    
    assert "test" not in filtered_text.split()  # Exact word removed
    assert "testing" in filtered_text  # Partial match preserved
    assert "testament" in filtered_text


@pytest.mark.integration
def test_parse_epub_basic(mock_epub_file):
    """Test basic EPUB parsing"""
    if not mock_epub_file:
        pytest.skip("EPUB file creation not available")
    
    try:
        meta, chapters, _ = parse_full_epub(str(mock_epub_file))
        
        assert chapters is not None
        assert len(chapters) > 0
        assert isinstance(chapters, list)
        
        # Check first chapter structure
        first_chapter = chapters[0]
        assert len(first_chapter) == 2 # (title, text)
    except Exception as e:
        pytest.fail(f"EPUB parsing failed: {e}")


@pytest.mark.unit
def test_extract_text_handles_empty_html():
    """Test handling of empty HTML"""
    html = "<html><body></body></html>"
    _, text = clean_html_for_tts(html)
    
    assert isinstance(text, str)
    assert len(text.strip()) == 0


@pytest.mark.unit
def test_extract_text_handles_malformed_html():
    """Test handling of malformed HTML"""
    html = "<html><body><p>Unclosed paragraph<div>Nested content</body></html>"
    
    try:
        _, text = clean_html_for_tts(html)
        assert isinstance(text, str)
        assert "Unclosed paragraph" in text
        assert "Nested content" in text
    except Exception as e:
        pytest.fail(f"Should handle malformed HTML gracefully: {e}")


@pytest.mark.unit
def test_pronunciation_fixes_empty_map():
    """Test pronunciation fixes with empty map"""
    text = "Original text"
    fixed_text = fix_pronunciation(text, {})
    
    assert fixed_text == text


@pytest.mark.unit
def test_filter_banned_words_empty_list():
    """Test banned word filtering with empty list"""
    text = "Original text"
    filtered_text = censor_text(text, [])
    
    assert filtered_text == text


@pytest.mark.unit
def test_filter_banned_words_invalid_regex():
    """Test handling of invalid regex patterns"""
    banned_patterns = [r"\btest\b", r"[invalid(regex"]  # Second pattern is invalid
    
    text = "This is a test sentence."
    
    try:
        filtered_text = censor_text(text, banned_patterns)
        # Should handle gracefully, filtering valid patterns only
        assert isinstance(filtered_text, str)
    except Exception as e:
        pytest.fail(f"Should handle invalid regex gracefully: {e}")
