"""
Pytest configuration and shared fixtures for EPUB converter tests
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from typing import Dict, Any


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup after test
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Provide a mock configuration dictionary"""
    return {
        "audio_settings": {
            "voice": "en-US-GuyNeural",
            "background_volume": 0.1,
            "tts_speed_default": "+0%",
            "max_concurrent_tts": 4,
            "retry_attempts": 3,
            "retry_delay": 2,
            "edge_tts_request_delay": 0.5,
            "min_audio_size_mb": 0.5,
            "piper_model_path": "en_US-lessac-medium.onnx",
            "piper_speaker_id": 0,
            "piper_noise_scale": 0.667,
            "piper_length_scale": 1.0
        },
        "system_limits": {
            "max_batch_size": 50,
            "ram_warning_threshold_mb": 1500,
            "enable_memory_monitoring": True,
            "min_disk_space_gb": 2.0,
            "max_chapter_length_chars": 50000
        },
        "branding": {
            "intro": "Test intro",
            "outro": "Test outro",
            "tagline": "Test tagline"
        },
        "video_settings": {
            "enable_text_overlay": True,
            "enable_chapter_markers": True,
            "enable_subtitles": True,
            "embed_subtitles": True,
            "subtitle_max_chars": 60,
            "subtitle_reading_speed_wps": 2.5,
            "text_overlay_font_size": 36,
            "use_advanced_renderer": True,
            "current_quality_preset": "Fast",
            "quality_presets": {
                "Fast": {"height": 480, "crf": 30, "preset": "ultrafast"},
                "Balanced": {"height": 720, "crf": 23, "preset": "medium"},
                "High": {"height": 1080, "crf": 20, "preset": "slow"}
            },
            "caption_style": {
                "preset": "Modern",
                "font": "Arial",
                "font_size": 70,
                "bold": True,
                "color": "#FFFFFF",
                "stroke_color": "#000000",
                "stroke_width": 5
            }
        },
        "cleanup_settings": {
            "auto_cleanup_on_startup": False,
            "max_temp_age_days": 5,
            "min_size_for_cleanup_mb": 5
        },
        "recovery_settings": {
            "enable_auto_recovery": False,
            "auto_approve_safe_fixes": False,
            "max_recovery_attempts": 3
        },
        "banned_words": ["\\btest\\b"],
        "pronunciation_fixes": {
            "test": "tehst"
        },
        "fandom_tags": {
            "test": ["#Test"]
        }
    }


@pytest.fixture
def config_file(temp_dir, mock_config):
    """Create a temporary config.json file"""
    config_path = temp_dir / "config.json"
    with open(config_path, 'w') as f:
        json.dump(mock_config, f, indent=2)
    return config_path


@pytest.fixture
def sample_epub_content():
    """Provide sample EPUB chapter content"""
    return {
        "title": "Test Chapter",
        "content": """
        <html>
        <head><title>Test Chapter</title></head>
        <body>
            <h1>Chapter 1: The Beginning</h1>
            <p>This is a test paragraph with some content.</p>
            <p>Another paragraph with more text to process.</p>
        </body>
        </html>
        """
    }


@pytest.fixture
def sample_text():
    """Provide sample text for TTS testing"""
    return "This is a sample text for testing text-to-speech synthesis."


@pytest.fixture
def mock_audio_file(temp_dir):
    """Create a mock audio file for testing"""
    audio_path = temp_dir / "test_audio.mp3"
    # Create a minimal valid MP3 file (silence)
    # This is a minimal MP3 header + frame
    mp3_data = bytes([
        0xFF, 0xFB, 0x90, 0x00,  # MP3 sync word + header
        0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00,
    ] * 100)  # Repeat to make it larger
    
    with open(audio_path, 'wb') as f:
        f.write(mp3_data)
    
    return audio_path


@pytest.fixture
def mock_subtitle_file(temp_dir):
    """Create a mock SRT subtitle file"""
    srt_path = temp_dir / "test_subtitles.srt"
    srt_content = """1
00:00:00,000 --> 00:00:05,000
This is the first subtitle

2
00:00:05,000 --> 00:00:10,000
This is the second subtitle
"""
    with open(srt_path, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    
    return srt_path


@pytest.fixture
def mock_image_file(temp_dir):
    """Create a mock image file for video testing"""
    try:
        from PIL import Image
        
        img_path = temp_dir / "test_image.jpg"
        # Create a simple 1920x1080 image
        img = Image.new('RGB', (1920, 1080), color=(73, 109, 137))
        img.save(img_path, 'JPEG')
        
        return img_path
    except ImportError:
        pytest.skip("Pillow not installed")


@pytest.fixture(autouse=True)
def setup_logging():
    """Setup logging for tests"""
    import logging
    logging.basicConfig(
        level=logging.WARNING,  # Reduce noise in test output
        format='%(levelname)s: %(message)s'
    )


@pytest.fixture
def mock_epub_file(temp_dir):
    """Create a minimal mock EPUB file structure"""
    try:
        import zipfile
        
        epub_path = temp_dir / "test_book.epub"
        
        # Create EPUB structure
        with zipfile.ZipFile(epub_path, 'w') as epub:
            # mimetype file (must be first, uncompressed)
            epub.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
            
            # META-INF/container.xml
            container_xml = '''<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
            epub.writestr('META-INF/container.xml', container_xml)
            
            # OEBPS/content.opf
            content_opf = '''<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0">
  <metadata>
    <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">Test Book</dc:title>
    <dc:creator xmlns:dc="http://purl.org/dc/elements/1.1/">Test Author</dc:creator>
  </metadata>
  <manifest>
    <item id="chapter1" href="chapter1.html" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="chapter1"/>
  </spine>
</package>'''
            epub.writestr('OEBPS/content.opf', content_opf)
            
            # OEBPS/chapter1.html
            chapter_html = '''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>Chapter 1</title>
</head>
<body>
  <h1>Chapter 1: Test Chapter</h1>
  <p>This is a test chapter with some sample content.</p>
  <p>It contains multiple paragraphs for testing purposes.</p>
</body>
</html>'''
            epub.writestr('OEBPS/chapter1.html', chapter_html)
        
        return epub_path
    except ImportError:
        pytest.skip("Required libraries for EPUB creation not available")
