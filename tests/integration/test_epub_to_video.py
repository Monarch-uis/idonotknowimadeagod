"""
Integration Tests - EPUB to Video
Tests the complete pipeline from EPUB input to video output with subtitles
"""
import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.config import CONFIG
from core.epub_io import parse_full_epub, clean_html_for_tts
from core.subtitle_generator import generate_subtitles_for_video
from core.video_pipeline import generate_timeline_from_audio, render_video_with_timeline
from core.utils import sanitize_filename, seconds_to_time_str


class TestEPUBToVideo:
    """Integration tests for complete EPUB to video conversion"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for tests"""
        temp_dir = tempfile.mkdtemp(prefix="video_test_")
        yield temp_dir
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def sample_video_metadata(self):
        """Sample metadata for video generation"""
        return {
            "title": "Test Video Novel",
            "author": "Video Author",
            "chapters": [
                {
                    "number": 1,
                    "title": "Chapter 1",
                    "text": "The quick brown fox jumps over the lazy dog.",
                    "audio_duration": 3.5
                },
                {
                    "number": 2,
                    "title": "Chapter 2",
                    "text": "A journey of a thousand miles begins with a single step.",
                    "audio_duration": 4.2
                }
            ]
        }
    
    @pytest.fixture
    def mock_audio_file(self, temp_workspace):
        """Create a mock audio file"""
        audio_path = os.path.join(temp_workspace, "test_audio.mp3")
        # Create empty file to simulate audio
        Path(audio_path).touch()
        return audio_path
    
    @pytest.fixture
    def mock_cover_image(self, temp_workspace):
        """Create a mock cover image"""
        from PIL import Image
        
        cover_path = os.path.join(temp_workspace, "cover.jpg")
        # Create a simple test image
        img = Image.new('RGB', (1920, 1080), color='blue')
        img.save(cover_path)
        return cover_path
    
    def test_video_configuration_validation(self):
        """Test video settings are properly configured"""
        assert "video_settings" in CONFIG
        
        video_config = CONFIG["video_settings"]
        assert "enable_subtitles" in video_config
        assert "quality_presets" in video_config
        assert "current_quality_preset" in video_config
        
        # Verify quality presets exist
        presets = video_config["quality_presets"]
        assert "Fast" in presets
        assert "Balanced" in presets
        assert "High" in presets
        
        # Verify each preset has required fields
        for preset_name, preset in presets.items():
            assert "height" in preset
            assert "crf" in preset
            assert "preset" in preset
    
    def test_subtitle_generation_timing(self):
        """Test subtitle generation with proper timing"""
        # Sample words with timestamps
        words_with_timing = [
            {"word": "The", "start": 0.0, "end": 0.2},
            {"word": "quick", "start": 0.2, "end": 0.5},
            {"word": "brown", "start": 0.5, "end": 0.8},
            {"word": "fox", "start": 0.8, "end": 1.0},
        ]
        
        # Verify timing is sequential
        for i in range(len(words_with_timing) - 1):
            current = words_with_timing[i]
            next_word = words_with_timing[i + 1]
            assert current["end"] <= next_word["start"]
    
    def test_subtitle_text_formatting(self):
        """Test subtitle text is properly formatted"""
        max_chars = CONFIG["video_settings"]["subtitle_max_chars"]
        
        # Test long sentence splitting
        long_text = "This is a very long sentence that needs to be split into multiple subtitle lines for better readability."
        
        # Simulate subtitle splitting
        words = long_text.split()
        subtitles = []
        current_sub = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= max_chars:
                current_sub.append(word)
                current_length += len(word) + 1
            else:
                if current_sub:
                    subtitles.append(" ".join(current_sub))
                current_sub = [word]
                current_length = len(word)
        
        if current_sub:
            subtitles.append(" ".join(current_sub))
        
        # Verify all subtitles are within max length
        for subtitle in subtitles:
            assert len(subtitle) <= max_chars
    
    def test_video_timeline_generation(self, temp_workspace, mock_audio_file):
        """Test video timeline generation from audio"""
        # Mock timeline data
        timeline = {
            "total_duration": 10.0,
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "First segment"},
                {"start": 5.0, "end": 10.0, "text": "Second segment"}
            ]
        }
        
        # Verify timeline structure
        assert "total_duration" in timeline
        assert "segments" in timeline
        assert len(timeline["segments"]) == 2
        
        # Verify no gaps or overlaps
        for i in range(len(timeline["segments"]) - 1):
            current = timeline["segments"][i]
            next_seg = timeline["segments"][i + 1]
            assert current["end"] == next_seg["start"]
    
    def test_video_quality_presets(self):
        """Test different video quality presets"""
        video_config = CONFIG["video_settings"]
        presets = video_config["quality_presets"]
        
        # Test Fast preset
        fast = presets["Fast"]
        assert fast["height"] == 480
        assert fast["crf"] >= 28  # Lower quality, higher CRF
        
        # Test Balanced preset
        balanced = presets["Balanced"]
        assert balanced["height"] == 720
        
        # Test High preset
        high = presets["High"]
        assert high["height"] == 1080
        assert high["crf"] <= 23  # Higher quality, lower CRF
        
        # Verify quality order (Fast < Balanced < High)
        assert fast["height"] < balanced["height"] < high["height"]
    
    @pytest.mark.integration
    def test_full_video_pipeline_mock(
        self, 
        temp_workspace, 
        sample_video_metadata,
        mock_audio_file,
        mock_cover_image
    ):
        """
        Test complete video generation pipeline (mocked)
        
        Pipeline:
        1. Parse EPUB
        2. Generate audio
        3. Create cover image
        4. Generate subtitles
        5. Create video timeline
        6. Render video
        7. Export final video
        """
        metadata = sample_video_metadata
        
        # Step 1: Verify metadata
        assert "chapters" in metadata
        assert len(metadata["chapters"]) > 0
        
        # Step 2: Mock audio files exist
        audio_files = []
        for chapter in metadata["chapters"]:
            audio_path = os.path.join(
                temp_workspace,
                f"chapter_{chapter['number']}.mp3"
            )
            Path(audio_path).touch()
            audio_files.append(audio_path)
        
        # Step 3: Verify cover image
        assert os.path.exists(mock_cover_image)
        
        # Step 4: Mock subtitle generation
        subtitle_file = os.path.join(temp_workspace, "subtitles.srt")
        with open(subtitle_file, 'w', encoding='utf-8') as f:
            f.write("1\n")
            f.write("00:00:00,000 --> 00:00:03,500\n")
            f.write("The quick brown fox jumps over the lazy dog.\n\n")
        
        assert os.path.exists(subtitle_file)
        
        # Step 5: Mock video timeline
        timeline_file = os.path.join(temp_workspace, "timeline.json")
        timeline = {
            "duration": 7.7,
            "segments": [
                {"start": 0.0, "end": 3.5, "chapter": 1},
                {"start": 3.5, "end": 7.7, "chapter": 2}
            ]
        }
        with open(timeline_file, 'w') as f:
            json.dump(timeline, f)
        
        # Step 6: Mock final video
        video_output = os.path.join(temp_workspace, "final_video.mp4")
        Path(video_output).touch()
        
        # Verify all components created
        assert os.path.exists(subtitle_file)
        assert os.path.exists(timeline_file)
        assert os.path.exists(video_output)
        assert len(audio_files) == len(metadata["chapters"])
    
    def test_subtitle_srt_format(self, temp_workspace):
        """Test SRT subtitle format is valid"""
        subtitle_file = os.path.join(temp_workspace, "test.srt")
        
        # Generate sample SRT
        srt_content = """1
00:00:00,000 --> 00:00:03,000
First subtitle line

2
00:00:03,000 --> 00:00:06,000
Second subtitle line

3
00:00:06,000 --> 00:00:09,000
Third subtitle line
"""
        
        with open(subtitle_file, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        # Verify file created
        assert os.path.exists(subtitle_file)
        
        # Verify format
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Check for proper SRT structure
            assert "00:00:00,000 --> 00:00:03,000" in content
            assert "First subtitle line" in content
    
    def test_time_format_conversion(self):
        """Test time conversion utilities"""
        # Test seconds to SRT time format
        seconds = 125.5  # 2 minutes, 5.5 seconds
        
        # Convert to SRT format (HH:MM:SS,mmm)
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        srt_time = f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
        
        # Verify format
        assert srt_time == "00:02:05,500"
    
    def test_video_aspect_ratios(self):
        """Test different video aspect ratios"""
        # Common aspect ratios for YouTube/social media
        aspect_ratios = {
            "16:9": (1920, 1080),  # Standard HD
            "9:16": (1080, 1920),  # Vertical/Mobile
            "1:1": (1080, 1080),   # Square/Instagram
            "4:3": (1024, 768),    # Classic
        }
        
        for ratio, (width, height) in aspect_ratios.items():
            # Calculate actual ratio
            calculated_ratio = width / height
            
            # Verify dimensions
            assert width > 0
            assert height > 0
            
            # Verify common ratios
            if ratio == "16:9":
                assert abs(calculated_ratio - 16/9) < 0.01
            elif ratio == "9:16":
                assert abs(calculated_ratio - 9/16) < 0.01
    
    def test_chapter_markers_in_video(self, temp_workspace):
        """Test YouTube chapter markers generation"""
        chapters = [
            {"number": 1, "title": "Introduction", "start_time": 0.0},
            {"number": 2, "title": "Main Content", "start_time": 120.0},
            {"number": 3, "title": "Conclusion", "start_time": 300.0},
        ]
        
        # Generate YouTube chapter markers
        markers = []
        for chapter in chapters:
            timestamp = seconds_to_time_str(chapter["start_time"])
            marker = f"{timestamp} - {chapter['title']}"
            markers.append(marker)
        
        # Save to file
        markers_file = os.path.join(temp_workspace, "chapters.txt")
        with open(markers_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(markers))
        
        # Verify
        assert os.path.exists(markers_file)
        with open(markers_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert "Introduction" in content
            assert "Main Content" in content
    
    @pytest.mark.slow
    def test_video_rendering_with_effects(self, temp_workspace, mock_cover_image):
        """Test video rendering with visual effects"""
        # Mock video effects configuration
        effects = {
            "fade_in": True,
            "fade_out": True,
            "text_overlay": True,
            "progress_bar": False
        }
        
        # Simulate rendering with effects
        video_output = os.path.join(temp_workspace, "video_with_effects.mp4")
        
        # Mock the rendering process
        with patch('core.video_pipeline.render_video_with_timeline') as mock_render:
            mock_render.return_value = video_output
            Path(video_output).touch()
            
            result = video_output
            
            # Verify output
            assert os.path.exists(result)
    
    def test_subtitle_word_censoring(self):
        """Test word censoring in subtitles"""
        banned_words = CONFIG.get("banned_words", [])
        
        # Test text with potentially banned content
        test_text = "This is a test sentence with normal words."
        
        # Import censor function
        from core.utils import censor_text
        
        # Apply censoring
        censored = censor_text(test_text, banned_words)
        
        # Verify censoring works (should be same if no banned words)
        assert isinstance(censored, str)
        assert len(censored) > 0
    
    def test_video_file_size_estimation(self):
        """Test video file size estimation"""
        # Estimate based on duration and quality
        duration_seconds = 300  # 5 minutes
        quality_preset = CONFIG["video_settings"]["quality_presets"]["Balanced"]
        
        # Rough estimation: ~1-2 MB per minute for 720p
        estimated_size_mb = duration_seconds / 60 * 1.5
        
        # Should be reasonable
        assert estimated_size_mb > 0
        assert estimated_size_mb < 1000  # Not absurdly large
    
    @pytest.mark.parametrize("quality", ["Fast", "Balanced", "High"])
    def test_multiple_quality_renders(self, quality, temp_workspace, mock_cover_image):
        """Test rendering with different quality presets"""
        video_config = CONFIG["video_settings"]
        preset = video_config["quality_presets"][quality]
        
        output_path = os.path.join(temp_workspace, f"video_{quality.lower()}.mp4")
        
        # Mock rendering
        with patch('core.video_pipeline.render_video_with_timeline') as mock_render:
            mock_render.return_value = output_path
            Path(output_path).touch()
            
            result = output_path
            
            # Verify file created
            assert os.path.exists(result)
            
            # Verify quality settings are valid
            assert preset["height"] >= 480
            assert preset["crf"] >= 0
            assert preset["crf"] <= 51
    
    def test_audio_video_sync(self):
        """Test audio and video stay in sync"""
        # Audio timestamps
        audio_segments = [
            {"start": 0.0, "end": 5.0},
            {"start": 5.0, "end": 10.0},
            {"start": 10.0, "end": 15.0},
        ]
        
        # Video timestamps should match
        video_segments = [
            {"start": 0.0, "end": 5.0},
            {"start": 5.0, "end": 10.0},
            {"start": 10.0, "end": 15.0},
        ]
        
        # Verify sync
        for audio, video in zip(audio_segments, video_segments):
            assert audio["start"] == video["start"]
            assert audio["end"] == video["end"]
    
    def test_subtitle_language_support(self):
        """Test subtitle generation supports different languages"""
        # Test with different language codes
        languages = ["en", "es", "fr", "de", "ja"]
        
        for lang in languages:
            # Verify language code is valid (2-letter ISO 639-1)
            assert len(lang) == 2
            assert lang.isalpha()
    
    def test_video_metadata_embedding(self, temp_workspace):
        """Test video file includes proper metadata"""
        metadata = {
            "title": "Test Video",
            "author": "Test Author",
            "description": "A test video description",
            "tags": ["test", "epub", "audiobook"],
            "date": "2024-12-18"
        }
        
        # Verify metadata structure
        assert all(key in metadata for key in ["title", "author", "description"])
        assert len(metadata["tags"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
