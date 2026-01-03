import logging
import datetime
from typing import List, Dict

from srt_generator import (
    group_words_by_sentences, 
    create_captions_from_group, 
    validate_captions
)

logger = logging.getLogger(__name__)

ASS_HEADER = """[Script Info]
Title: TTS Subtitles Generated
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 1

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Montserrat-Bold,70,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,5,0,2,20,20,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def generate_ass(word_timestamps: List[Dict], config: dict = None) -> str:
    """
    Convert word-level timestamps to ASS captions with Karaoke tags.
    """
    if not word_timestamps:
        return ""

    if config is None:
        # Default config if none provided (should match srt_generator defaults essentially)
        from srt_generator import DEFAULT_CONFIG
        config = DEFAULT_CONFIG

    logger.info("Generating ASS captions with Karaoke tags...")

    # Reuse grouping logic from SRT generator
    grouped_words = group_words_by_sentences(word_timestamps, config)
    
    captions = []
    for word_group in grouped_words:
        group_captions = create_captions_from_group(word_group, config)
        captions.extend(group_captions)
    
    captions = validate_captions(captions, config)
    
    ass_content = format_as_ass(captions)
    
    return ass_content

def format_time_ass(seconds: float) -> str:
    """
    Format seconds to H:MM:SS.cs (centiseconds)
    Example: 1:02:30.55
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"

def format_as_ass(captions: List[Dict]) -> str:
    """
    Format captions into ASS Events.
    """
    events = []
    
    for caption in captions:
        start_time = caption['start']
        end_time = caption['end']
        words = caption['words'] # List[Dict]
        
        ass_start = format_time_ass(start_time)
        ass_end = format_time_ass(end_time)
        
        # Build Karaoke text
        # Logic: 
        # Current time tracker = start_time
        # For each word:
        #   gap = word.start - tracker
        #   if gap > 0: add {\k<gap_cs>} for space
        #   dur = word.end - word.start
        #   add {\k<dur_cs>}word.text
        #   tracker = word.end
        
        # Also need to handle line breaking if create_captions_from_group split it?
        # Actually create_captions_from_group already broke it down so one caption object = one screen presence.
        # But inside that caption object there might be multiple visual lines due to word wrapping?
        # ASS handles wrapping automatically if we don't force breaks, 
        # but for specific Karaoke we might want to just let it flow.
        
        k_text = ""
        tracker = start_time
        
        for w in words:
            word_obj = w if isinstance(w, dict) else {'word': str(w), 'start': tracker, 'end': tracker}
            
            w_start = word_obj.get('start', tracker)
            w_end = word_obj.get('end', tracker)
            w_text = word_obj.get('word', "")
            
            # Handle gap (silence before word)
            gap = w_start - tracker
            if gap > 0.01: # 10ms tolerance
                gap_cs = int(gap * 100)
                # Add a space with karaoke duration for the gap to ensure sync
                if gap_cs > 0:
                     k_text += f"{{\k{gap_cs}}} "
            elif gap < -0.01:
                # Overlap correction (shouldn't happen with validate_captions but safety first)
                pass
                
            # Word duration
            dur = w_end - w_start
            dur_cs = int(dur * 100)
            if dur_cs < 0: dur_cs = 0
            
            # Escape special ASS chars
            clean_text = w_text.replace('{','(').replace('}',')')
            
            k_text += f"{{\k{dur_cs}}}{clean_text} "
            
            tracker = w_end

        # Trim last space
        k_text = k_text.strip()
        
        event_line = f"Dialogue: 0,{ass_start},{ass_end},Default,,0,0,0,,{k_text}"
        events.append(event_line)

    return ASS_HEADER + "\n".join(events)
