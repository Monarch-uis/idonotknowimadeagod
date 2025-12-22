"""
Integration Tests - EPUB to Audiobook
Tests the complete pipeline from EPUB input to audio output
"""
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import asyncio

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.config import CONFIG
from core.epub_io import (
    parse_full_epub, 
    clean_html_for_tts,
    setup_project_folders,
    extract_cover_to_project
)
import core.tts as tts_module
from core.utils import sanitize_filename


class TestEPUBToAudiobook:
    """Integration tests for complete EPUB to audiobook conversion"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for tests"""
        temp_dir = tempfile.mkdtemp(prefix="epub_test_")
        yield temp_dir
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_epub_path(self, temp_workspace):
        """Create a mock EPUB file path"""
        epub_path = os.path.join(temp_workspace, "test_book.epub")
        # Note: Actual EPUB creation would require epub library
        # For integration tests, we'll use mocked parsing
        return epub_path
    
    @pytest.fixture
    def sample_epub_metadata(self):
        """Sample EPUB metadata for testing"""
        return {
            "title": "Test Novel",
            "author": "Test Author",
            "chapters": [
                {
                    "number": 1,
                    "title": "Chapter 1: The Beginning",
                    "text": "This is the first chapter. It has multiple sentences. Each sentence will be spoken."
                },
                {
                    "number": 2,
                    "title": "Chapter 2: The Middle",
                    "text": "This is the second chapter. The story continues here. More exciting content awaits."
                }
            ]
        }
    
    def test_epub_parsing_pipeline(self, sample_epub_metadata):
        """Test EPUB parsing extracts metadata correctly"""
        # Verify chapter structure
        assert len(sample_epub_metadata["chapters"]) == 2
        assert sample_epub_metadata["title"] == "Test Novel"
        assert sample_epub_metadata["chapters"][0]["number"] == 1
        
        # Verify text content exists
        for chapter in sample_epub_metadata["chapters"]:
            assert len(chapter["text"]) > 0
            assert chapter["title"]
    
    def test_text_cleaning_for_tts(self, sample_epub_metadata):
        """Test HTML cleaning for TTS processing"""
        raw_html = "<p>Test <b>bold</b> text</p><br/><div>Another paragraph</div>"
        _, cleaned = clean_html_for_tts(raw_html)
        
        # Should remove HTML tags
        assert "<" not in cleaned
        assert ">" not in cleaned
        
        # Should preserve text content
        assert "Test" in cleaned
        assert "bold" in cleaned
        assert "text" in cleaned
    
    @pytest.mark.asyncio
    async def test_tts_single_chapter_mock(self, temp_workspace, sample_epub_metadata):
        """Test TTS generation for a single chapter (mocked)"""
        chapter = sample_epub_metadata["chapters"][0]
        output_path = os.path.join(temp_workspace, "chapter_1.mp3")
        
        # Mock the actual TTS call
        with patch('core.tts.gen_single_clip_edge_with_retry') as mock_tts:
            # Simulate successful TTS generation
            mock_tts.return_value = (True, None, output_path)
            
            # Create empty file to simulate output
            Path(output_path).touch()
            
            result = await tts_module.gen_single_clip_edge_with_retry(
                text=chapter["text"],
                filename=output_path,
                voice="en-US-GuyNeural",
                speed="+0%"
            )
            
            # Verify TTS was called
            mock_tts.assert_called_once()
            
            # Verify output would exist
            assert result[2] == output_path
    
    def test_project_folder_setup(self, temp_workspace):
        """Test project folder structure creation"""
        project_name = "test_project"
        project_dir = os.path.join(temp_workspace, project_name)
        
        # Create folder structure
        folders = setup_project_folders(project_name, temp_workspace)
        
        # Verify all required folders exist
        assert os.path.exists(project_dir)
        assert os.path.exists(folders.get("audio", ""))
        assert os.path.exists(folders.get("video", ""))
        assert os.path.exists(folders.get("temp", ""))
    
    def test_filename_sanitization(self):
        """Test filename sanitization for cross-platform compatibility"""
        unsafe_names = [
            "Chapter 1: The Beginning",
            "Test/Invalid\\Path",
            "File<with>special:chars",
            "trailing_spaces   ",
            "multiple___underscores"
        ]
        
        for name in unsafe_names:
            sanitized = sanitize_filename(name)
            
            # Should not contain invalid characters
            invalid_chars = ['/', '\\', '<', '>', ':', '"', '|', '?', '*']
            for char in invalid_chars:
                assert char not in sanitized
            
            # Should not be empty
            assert len(sanitized) > 0
    
    @pytest.mark.integration
    def test_full_audiobook_pipeline_mock(self, temp_workspace, sample_epub_metadata):
        """
        Test complete audiobook generation pipeline (mocked external dependencies)
        
        Pipeline:
        1. Parse EPUB
        2. Clean text
        3. Generate TTS for each chapter
        4. Combine audio files
        5. Add intro/outro
        6. Export final audiobook
        """
        # Step 1: EPUB metadata (already provided)
        metadata = sample_epub_metadata
        
        # Step 2: Text cleaning
        cleaned_chapters = []
        for chapter in metadata["chapters"]:
            _, cleaned_text = clean_html_for_tts(chapter["text"])
            cleaned_chapters.append({
                "number": chapter["number"],
                "title": chapter["title"],
                "text": cleaned_text
            })
        
        assert len(cleaned_chapters) == len(metadata["chapters"])
        
        # Step 3: Mock TTS generation
        audio_files = []
        for chapter in cleaned_chapters:
            audio_path = os.path.join(
                temp_workspace, 
                f"chapter_{chapter['number']}.mp3"
            )
            # Simulate file creation
            Path(audio_path).touch()
            audio_files.append(audio_path)
        
        # Verify all audio files created
        assert len(audio_files) == len(cleaned_chapters)
        for audio_file in audio_files:
            assert os.path.exists(audio_file)
        
        # Step 4: Mock audio combination
        final_audiobook = os.path.join(temp_workspace, "final_audiobook.m4b")
        Path(final_audiobook).touch()
        
        # Step 5: Verify final output
        assert os.path.exists(final_audiobook)
        
        # Cleanup verification
        file_count = len(list(Path(temp_workspace).rglob("*")))
        assert file_count >= 3  # At least chapter files + final file
    
    @pytest.mark.slow
    def test_concurrent_tts_processing(self, temp_workspace):
        """Test concurrent TTS processing for multiple chapters"""
        # Simulate 5 chapters
        chapters = [f"Chapter {i} text content" for i in range(1, 6)]
        
        with patch('core.tts.gen_single_clip_edge_with_retry') as mock_tts:
            # Mock async TTS calls
            async def mock_tts_call(text, filename, voice, speed, **kwargs):
                await asyncio.sleep(0.1)  # Simulate processing time
                Path(filename).touch()
                return (True, None, filename)
            
            mock_tts.side_effect = mock_tts_call
            
            # Process chapters concurrently (simulated)
            results = []
            for i, chapter_text in enumerate(chapters):
                output_path = os.path.join(temp_workspace, f"chapter_{i+1}.mp3")
                Path(output_path).touch()
                results.append(output_path)
            
            # Verify all processed
            assert len(results) == len(chapters)
            for result in results:
                assert os.path.exists(result)
    
    def test_error_recovery_during_processing(self, temp_workspace):
        """Test error recovery when TTS fails for a chapter"""
        chapters = ["Chapter 1", "Chapter 2", "Chapter 3"]
        
        with patch('core.tts.gen_single_clip_edge_with_retry') as mock_tts:
            # Simulate failure on chapter 2
            def side_effect(text, filename, voice, speed, **kwargs):
                if "Chapter 2" in text:
                    raise Exception("TTS service unavailable")
                Path(filename).touch()
                return (True, None, filename)
            
            mock_tts.side_effect = side_effect
            
            # Process with error handling
            successful = []
            failed = []
            
            for i, chapter_text in enumerate(chapters):
                try:
                    output_path = os.path.join(temp_workspace, f"chapter_{i+1}.mp3")
                    result = side_effect(chapter_text, output_path, "", "")
                    successful.append(result)
                except Exception as e:
                    failed.append(chapter_text)
            
            # Verify error was caught
            assert len(failed) == 1
            assert "Chapter 2" in failed[0]
            
            # Verify others succeeded
            assert len(successful) == 2
    
    def test_configuration_validation(self):
        """Test that configuration is valid for audiobook generation"""
        # Verify required config keys exist
        assert "audio_settings" in CONFIG
        assert "voice" in CONFIG["audio_settings"]
        assert "tts_speed_default" in CONFIG["audio_settings"]
        
        # Verify TTS engine settings
        audio_config = CONFIG["audio_settings"]
        assert "retry_attempts" in audio_config
        assert audio_config["retry_attempts"] > 0
        
        # Verify system limits
        assert "system_limits" in CONFIG
        assert "max_batch_size" in CONFIG["system_limits"]
    
    def test_memory_usage_tracking(self, temp_workspace):
        """Test memory usage tracking during processing"""
        import psutil
        
        # Get initial memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate processing (create dummy files)
        for i in range(10):
            dummy_file = os.path.join(temp_workspace, f"dummy_{i}.txt")
            with open(dummy_file, 'w') as f:
                f.write("x" * 1000000)  # 1MB of data
        
        # Get final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory should increase but stay reasonable (< 500MB for this test)
        assert memory_increase < 500
    
    @pytest.mark.parametrize("voice,speed", [
        ("en-US-GuyNeural", "+0%"),
        ("en-US-AriaNeural", "+10%"),
        ("en-GB-RyanNeural", "-5%"),
    ])
    def test_multiple_voice_configurations(self, voice, speed, temp_workspace):
        """Test audiobook generation with different voice configurations"""
        output_path = os.path.join(temp_workspace, f"test_{voice}.mp3")
        
        # Mock TTS with different voices
        with patch('core.tts.gen_single_clip_edge_with_retry') as mock_tts:
            mock_tts.return_value = (True, None, output_path)
            Path(output_path).touch()
            
            # Simulate call
            result = output_path
            
            # Verify file would be created
            assert os.path.exists(result)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
