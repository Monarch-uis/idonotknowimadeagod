"""
Subtitle Generator for Video Creation
Generates clean SRT subtitles with bad word filtering while preserving character names
"""

import os
import re
from typing import List, Tuple, Dict, Any, Optional
from .utils import censor_text_for_subtitles


class SubtitleGenerator:
    """Generate SRT subtitle files from chapter text with word filtering"""
    
    def __init__(self, config):
        """
        Initialize subtitle generator
        
        Args:
            config: Configuration dictionary with banned_words list
        """
        self.config = config
        self.banned_words = config.get("banned_words", [])
    
    def format_timestamp(self, seconds: float) -> str:
        """
        Convert seconds to SRT timestamp format (HH:MM:SS,mmm)
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    def split_into_subtitle_chunks(self, text: str, max_chars: int = 60, max_duration: float = 5.0) -> List[str]:
        """
        Split text into subtitle-sized chunks
        
        Args:
            text: Text to split
            max_chars: Maximum characters per subtitle line
            max_duration: Maximum duration per subtitle in seconds
            
        Returns:
            List of text chunks suitable for subtitles
        """
        # Split by sentences first
        sentences = re.split(r'([.!?]+\s+)', text)
        
        chunks = []
        current_chunk = ""
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            separator = sentences[i + 1] if i + 1 < len(sentences) else ""
            
            # If adding this sentence would exceed max_chars, save current chunk
            if current_chunk and len(current_chunk) + len(sentence) > max_chars:
                chunks.append(current_chunk.strip())
                current_chunk = ""
            
            current_chunk += sentence + separator
            
            # If current chunk is long enough, save it
            if len(current_chunk) > max_chars * 0.7:  # 70% of max to allow some flexibility
                chunks.append(current_chunk.strip())
                current_chunk = ""
        
        # Add any remaining text
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def estimate_reading_time(self, text: str, words_per_second: float = 2.5) -> float:
        """
        Estimate how long it takes to read text at comfortable pace
        
        Args:
            text: Text to estimate
            words_per_second: Average reading speed
            
        Returns:
            Estimated duration in seconds
        """
        word_count = len(text.split())
        return max(word_count / words_per_second, 1.5)  # Minimum 1.5 seconds per subtitle
    
    def generate_chapter_subtitles(
        self,
        chapter_text: str,
        start_time: float,
        chapter_duration: float
    ) -> List[Tuple[float, float, str]]:
        """
        Generate subtitle entries for a single chapter
        
        Args:
            chapter_text: Chapter text content
            start_time: Chapter start time in seconds
            chapter_duration: Total chapter duration in seconds
            
        Returns:
            List of (start_time, end_time, text) tuples
        """
        # Apply partial censoring for subtitles (f**k style)
        clean_text = censor_text_for_subtitles(chapter_text, self.banned_words)
        
        # Remove extra quotes and asterisks (like TTS does)
        clean_text = clean_text.replace('"', '').replace("*", "")
        
        # Split into subtitle-sized chunks
        chunks = self.split_into_subtitle_chunks(clean_text)
        
        if not chunks:
            return []
        
        subtitles = []
        chapter_end = start_time + max(chapter_duration, 0)

        if chapter_end <= start_time:
            return subtitles

        current_time = start_time
        chunk_count = len(chunks)
        min_duration = 0.6  # keep subtitles on screen briefly even for short lines
        min_gap = 0.1

        for idx, chunk in enumerate(chunks):
            remaining_chunks = chunk_count - idx - 1
            remaining_time = chapter_end - current_time

            if remaining_time <= 0.05:
                break

            reading_time = self.estimate_reading_time(chunk)
            min_time_needed_for_rest = max(0.0, remaining_chunks * (min_duration + min_gap))
            max_allocation = remaining_time - min_time_needed_for_rest

            if max_allocation <= 0:
                # Not enough space left – distribute remaining time evenly among current and future chunks
                duration = max(remaining_time / max(remaining_chunks + 1, 1), 0.2)
            else:
                duration = min(reading_time, max_allocation)
                duration = max(duration, min_duration)

            duration = min(duration, remaining_time)

            end_time = current_time + duration

            # Force last chunk to end exactly at chapter end
            if idx == chunk_count - 1 or (chapter_end - end_time) <= 0.05:
                end_time = chapter_end

            subtitles.append((current_time, end_time, chunk))
            current_time = end_time

            if idx != chunk_count - 1:
                gap = min(min_gap, chapter_end - current_time)
                current_time += gap

        # Post-process to guarantee monotonic timestamps
        cleaned = []
        last_end = start_time
        epsilon = 0.001
        for start, end, text in subtitles:
            start = max(start, last_end)
            if end <= start:
                end = start + epsilon
            cleaned.append((start, end, text))
            last_end = end

        return cleaned
    
    def generate_srt_file(
        self, 
        chapters: List[Tuple[str, str]], 
        timestamps: List[Tuple[float, str]], 
        output_path: str
    ) -> bool:
        """
        Generate complete SRT subtitle file for entire audiobook
        
        Args:
            chapters: List of (title, text) tuples
            timestamps: List of (start_time, title) tuples from TTS generation
            output_path: Path to save SRT file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            all_subtitles = []
            
            # Generate subtitles for each chapter
            for i, (title, text) in enumerate(chapters):
                # Find this chapter's timestamp
                start_time = timestamps[i][0] if i < len(timestamps) else 0
                
                # Calculate chapter duration
                if i + 1 < len(timestamps):
                    chapter_duration = timestamps[i + 1][0] - start_time
                else:
                    # Last chapter - estimate duration
                    chapter_duration = self.estimate_reading_time(text) + 5
                
                # Generate subtitles for this chapter
                chapter_subs = self.generate_chapter_subtitles(text, start_time, chapter_duration)
                all_subtitles.extend(chapter_subs)
            
            # Write SRT file
            all_subtitles.sort(key=lambda item: item[0])

            with open(output_path, 'w', encoding='utf-8') as f:
                for idx, (start, end, text) in enumerate(all_subtitles, 1):
                    f.write(f"{idx}\n")
                    f.write(f"{self.format_timestamp(start)} --> {self.format_timestamp(end)}\n")
                    f.write(f"{text}\n\n")
            
            return True
            
        except Exception as e:
            print(f"❌ Subtitle generation failed: {e}")
            return False
    
    def embed_subtitles_in_video(self, video_path: str, srt_path: str) -> bool:
        """
        Embed SRT subtitles into video file using ffmpeg
        
        Args:
            video_path: Path to video file
            srt_path: Path to SRT subtitle file
            
        Returns:
            True if successful, False otherwise
        """
        import subprocess
        
        try:
            # Get ffmpeg executable
            try:
                from imageio_ffmpeg import get_ffmpeg_exe
                ffmpeg_exe = get_ffmpeg_exe()
            except Exception:
                ffmpeg_exe = 'ffmpeg'
            
            # Create temp output path
            temp_output = video_path.replace('.mp4', '_with_subs.mp4')
            
            # FFmpeg command to add soft subtitles (can be turned on/off)
            cmd = [
                ffmpeg_exe, '-i', video_path,
                '-i', srt_path,
                '-c', 'copy',  # Copy video/audio without re-encoding
                '-c:s', 'mov_text',  # Subtitle codec for MP4
                '-metadata:s:s:0', 'language=eng',
                '-metadata:s:s:0', 'title=English',
                '-y',  # Overwrite output
                temp_output
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(temp_output):
                # Replace original with subtitled version
                os.replace(temp_output, video_path)
                print(f"   ✅ Subtitles embedded successfully")
                return True
            else:
                print(f"   ⚠️  Subtitle embedding failed: {result.stderr}")
                if os.path.exists(temp_output):
                    os.remove(temp_output)
                return False
                
        except Exception as e:
            print(f"   ⚠️  Subtitle embedding error: {e}")
            return False


def _parse_timestamp(timestamp: str) -> float:
    hours, minutes, rest = timestamp.split(':')
    seconds, milliseconds = rest.split(',')
    return (
        int(hours) * 3600
        + int(minutes) * 60
        + int(seconds)
        + int(milliseconds) / 1000.0
    )


def _format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int(round((seconds % 1) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def repair_srt_file(srt_path: str, min_duration: float = 0.6, min_gap: float = 0.05) -> bool:
    """Repair an SRT file in place enforcing monotonic timestamps."""
    if not os.path.exists(srt_path):
        return False

    entries = []
    with open(srt_path, 'r', encoding='utf-8') as handle:
        block = []
        for line in handle:
            stripped = line.rstrip('\n')
            if stripped == "":
                if block:
                    entries.append(block)
                    block = []
                continue
            block.append(stripped)
        if block:
            entries.append(block)

    repaired = []
    last_end = 0.0
    timecode_pattern = re.compile(r"^(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})$")

    for block in entries:
        if len(block) < 2:
            continue

        line_iter = iter(block)
        index_line = next(line_iter)
        time_line = next(line_iter)

        match = timecode_pattern.match(time_line)
        if not match:
            continue

        start = _parse_timestamp(match.group(1))
        end = _parse_timestamp(match.group(2))

        if start < last_end + min_gap:
            start = last_end + min_gap
        if end <= start + min_duration:
            end = start + min_duration

        last_end = end

        payload = [index_line, f"{_format_timestamp(start)} --> {_format_timestamp(end)}"]
        payload.extend(list(line_iter))
        repaired.append(payload)

    with open(srt_path, 'w', encoding='utf-8') as handle:
        for idx, block in enumerate(repaired, 1):
            handle.write(f"{idx}\n")
            for i, line in enumerate(block):
                if i == 0:
                    continue  # replaced with sequential idx
                handle.write(f"{line}\n")
            handle.write("\n")

    return True


def generate_subtitles_for_video(
    chapters: List[Tuple[str, str]],
    timestamps: List[Tuple[float, str]],
    video_path: str,
    config: dict,
    embed: bool = True
) -> bool:
    """
    Main function to generate and optionally embed subtitles in video
    
    Args:
        chapters: List of (title, text) tuples
        timestamps: List of (start_time, title) tuples
        video_path: Path to video file
        config: Configuration dictionary
        embed: Whether to embed subtitles (True) or just generate file (False)
        
    Returns:
        True if successful, False otherwise
    """
    # Generate SRT file path
    srt_path = video_path.replace('.mp4', '.srt')
    
    # Create subtitle generator
    generator = SubtitleGenerator(config)
    
    # Generate SRT file
    print(f"   📝 Generating subtitles...")
    success = generator.generate_srt_file(chapters, timestamps, srt_path)
    
    if not success:
        return False
    
    print(f"   ✅ Subtitles saved: {os.path.basename(srt_path)}")
    
    # Optionally embed in video
    if embed and os.path.exists(video_path):
        print(f"   🎬 Embedding subtitles in video...")
        return generator.embed_subtitles_in_video(video_path, srt_path)
    
    return True


# ============================================================================
# SIMPLE TTS-TIMING-BASED SUBTITLE GENERATION
# ============================================================================

def _seconds_to_ass_time(seconds: float) -> str:
    """Convert seconds to ASS timestamp format (H:MM:SS.CC)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int(round((seconds - int(seconds)) * 100))
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"


def _ass_hex_color(hex_color: str, alpha: int = 0) -> str:
    """Convert #RRGGBB to &HAABBGGRR (ASS color format)"""
    hex_color = hex_color.strip().lstrip('#')
    if len(hex_color) != 6:
        return "&H00FFFFFF"
    r = hex_color[0:2]
    g = hex_color[2:4]
    b = hex_color[4:6]
    return f"&H{alpha:02X}{b}{g}{r}"


def generate_ass_from_timestamps(
    timestamps: List[Tuple[float, str]],
    output_path: str,
    config: dict
) -> bool:
    """
    Generate ASS subtitle file directly from timestamp data.
    This is simpler and more reliable than transcription-based captions.
    
    Args:
        timestamps: List of (start_time, chapter_title) tuples from TTS generation
        output_path: Path to save the ASS file
        config: Configuration dictionary with caption_style settings
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get caption style from config
        video_settings = config.get("video_settings", {})
        style = video_settings.get("caption_style", {})
        
        # Default values
        font = style.get("font", "Arial")
        font_size = int(style.get("font_size", 70))
        bold = -1 if style.get("bold", True) else 0
        primary_color = _ass_hex_color(style.get("color", "#FFFFFF"))
        outline_color = _ass_hex_color(style.get("stroke_color", "#000000"))
        outline_width = int(style.get("stroke_width", 5))
        shadow = int(style.get("shadow", 2))
        alignment = int(style.get("alignment", 2))  # 2 = bottom center
        margin_v = int(style.get("margin_v", 50))
        margin_h = int(style.get("margin_h", 20))
        
        # Build ASS file
        with open(output_path, 'w', encoding='utf-8') as f:
            # Script Info
            f.write("[Script Info]\n")
            f.write("Title: Generated by EPUB Project Manager\n")
            f.write("ScriptType: v4.00+\n")
            f.write("PlayResX: 1920\n")
            f.write("PlayResY: 1080\n")
            f.write("\n")
            
            # Styles
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
                   "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
                   "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
                   "MarginL, MarginR, MarginV, Encoding\n")
            f.write(f"Style: Default,{font},{font_size},{primary_color},&H000000FF,{outline_color},&H00000000,"
                   f"{bold},0,0,0,100,100,0,0,1,{outline_width},{shadow},{alignment},"
                   f"{margin_h},{margin_h},{margin_v},1\n")
            f.write("\n")
            
            # Events
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
            
            # Write dialogue entries from timestamps
            for i, (start_time, title) in enumerate(timestamps):
                # Calculate end time (next chapter start or +5 seconds for last)
                if i + 1 < len(timestamps):
                    end_time = timestamps[i + 1][0]
                else:
                    end_time = start_time + 5.0  # Show last chapter title for 5 seconds
                
                # Clean and escape text
                safe_text = (
                    str(title)
                    .replace("\r\n", "\n")
                    .replace("{", r"\{")
                    .replace("}", r"\}")
                    .replace("\n", r"\N")
                    .strip()
                )
                
                if not safe_text:
                    continue
                
                start_str = _seconds_to_ass_time(start_time)
                end_str = _seconds_to_ass_time(end_time)
                
                f.write(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{safe_text}\n")
        
        return True
        
    except Exception as e:
        print(f"Error generating ASS subtitles: {e}")
        return False


def verify_subtitle_timing(caption_lines: List[Dict[str, Any]], audio_duration: float) -> None:
    """Verify subtitle timing accuracy and report any issues."""
    if not caption_lines:
        return
    
    total_caption_time = caption_lines[-1]["end"] - caption_lines[0]["start"]
    time_diff = abs(total_caption_time - audio_duration)
    
    print(f"   ⏱️  Timing verification:")
    print(f"      Audio duration: {audio_duration:.2f}s")
    print(f"      Caption span: {total_caption_time:.2f}s")
    print(f"      Difference: {time_diff:.2f}s")
    
    if time_diff > 1.0:
        print(f"   ⚠️  WARNING: Significant timing difference detected!")
    else:
        print(f"   ✅ Timing accuracy: Good")


def generate_ass_from_word_timeline(
    word_timeline: List[Dict[str, Any]],
    output_path: str,
    config: dict
) -> bool:
    """
    Generate ASS subtitle file from word-level timeline data.
    Groups words into readable caption lines.
    
    Args:
        word_timeline: List of dicts with 'start', 'end', 'text' keys (absolute time)
        output_path: Path to save the ASS file
        config: Configuration dictionary
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get caption style from config
        video_settings = config.get("video_settings", {})
        style = video_settings.get("caption_style", {})
        
        # Default values (Modern style)
        font = style.get("font", "Montserrat-Bold")
        font_size = int(style.get("font_size", 70))
        bold = -1 if style.get("bold", True) else 0
        primary_color = _ass_hex_color(style.get("color", "#FFFFFF"))
        outline_color = _ass_hex_color(style.get("stroke_color", "#000000"))
        outline_width = int(style.get("stroke_width", 5))
        shadow = int(style.get("shadow", 2))
        alignment = int(style.get("alignment", 2))  # 2 = bottom center
        margin_v = int(style.get("margin_v", 50))
        margin_h = int(style.get("margin_h", 20))
        
        # Group words into lines
        # Max duration 3s, max words 12 (similar to video_pipeline)
        max_duration = float(video_settings.get("caption_fragment_max_duration", 3.0))
        max_words = int(video_settings.get("caption_fragment_max_words", 12))
        
        caption_lines = []
        current_words = []
        current_start = None
        
        for word in word_timeline:
            text = word.get("text", "").strip()
            if not text:
                continue
                
            start = float(word.get("start", 0.0))
            end = float(word.get("end", start))
            
            if current_start is None:
                current_start = start
                
            projected_duration = end - current_start
            
            # Check if we should flush current line
            if current_words and (
                projected_duration > max_duration or 
                len(current_words) >= max_words or
                (current_words and (start - current_words[-1]["end"] > 0.5)) # Pause detection
            ):
                # Flush
                line_text = " ".join(w["text"] for w in current_words)
                line_end = current_words[-1]["end"]
                caption_lines.append({
                    "start": current_start,
                    "end": line_end,
                    "text": line_text
                })
                current_words = []
                current_start = start
            
            # Store word with properly typed timestamps
            current_words.append({
                "text": text,
                "start": start,
                "end": end
            })
        
        # Flush remaining
        if current_words and current_start is not None:
            line_text = " ".join(w["text"] for w in current_words)
            line_end = current_words[-1]["end"]
            caption_lines.append({
                "start": current_start,
                "end": line_end,
                "text": line_text
            })
            
        print(f"   📊 Generated {len(caption_lines)} caption lines from {len(word_timeline)} words")
        
        # Verify timing accuracy
        if caption_lines and word_timeline:
            audio_duration = word_timeline[-1].get("end", 0.0)
            verify_subtitle_timing(caption_lines, audio_duration)
            
        # Write ASS file
        return _write_ass_file(caption_lines, output_path, font, font_size, primary_color, outline_color, outline_width, shadow, alignment, margin_h, margin_v, bold)
        
    except Exception as e:
        print(f"Error generating ASS subtitles: {e}")
        return False

def _write_ass_file(events, output_path, font, font_size, primary, outline, outline_width, shadow, alignment, margin_h, margin_v, bold):
    """Helper to write the physical ASS file"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # Script Info
            f.write("[Script Info]\n")
            f.write("Title: Generated by EPUB Project Manager\n")
            f.write("ScriptType: v4.00+\n")
            f.write("PlayResX: 1920\n")
            f.write("PlayResY: 1080\n")
            f.write("WrapStyle: 1\n") # Smart wrapping
            f.write("\n")
            
            # Styles
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
                   "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
                   "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
                   "MarginL, MarginR, MarginV, Encoding\n")
            f.write(f"Style: Default,{font},{font_size},{primary},&H000000FF,{outline},&H00000000,"
                   f"{bold},0,0,0,100,100,0,0,1,{outline_width},{shadow},{alignment},"
                   f"{margin_h},{margin_h},{margin_v},1\n")
            f.write("\n")
            
            # Events
            f.write("[Events]\n")
            f.write("Format: Layer, Start, End, Style, Text\n")
            
            for event in events:
                start_str = _seconds_to_ass_time(event["start"])
                end_str = _seconds_to_ass_time(event["end"])
                # Ass takes text, convert newlines if any
                text = event["text"].replace("\n", "\\N")
                f.write(f"Dialogue: 0,{start_str},{end_str},Default,{text}\n")
                
        return True
    except Exception as e:
        print(f"Error writing ASS file: {e}")
        return False
