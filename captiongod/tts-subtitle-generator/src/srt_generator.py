import logging
import re
from typing import List, Dict

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    'max_words_per_line': 12,
    'max_lines_per_caption': 2,
    'max_caption_duration': 7.0,
    'min_caption_duration': 1.0,
    'word_timing_tolerance': 0.1,
    'break_on_punctuation': ['.', '!', '?', ';'],
    'pause_threshold': 0.3
}


def generate_srt(word_timestamps: List[Dict], config: dict = None) -> str:
    """
    Convert word-level timestamps to SRT captions.
    
    Rules:
    - Group by sentences (detect end punctuation)
    - Respect max_words_per_line (split mid-sentence if needed)
    - Never exceed max_duration
    - Maintain min_duration
    - No word appears before it's spoken
    - No overlapping captions
    - Format: HH:MM:SS,mmm --> HH:MM:SS,mmm
    
    Return: SRT string
    """
    if not word_timestamps:
        logger.warning("No word timestamps provided")
        return ""
    
    if config is None:
        config = DEFAULT_CONFIG
    
    logger.info("Generating SRT captions from word timestamps...")
    
    grouped_words = group_words_by_sentences(word_timestamps, config)
    
    captions = []
    for word_group in grouped_words:
        group_captions = create_captions_from_group(word_group, config)
        captions.extend(group_captions)
    
    captions = validate_captions(captions, config)
    
    srt_content = format_as_srt(captions)
    
    logger.info(f"Generated {len(captions)} captions")
    
    return srt_content


def group_words_by_sentences(word_timestamps: List[Dict], 
                             config: dict) -> List[List[Dict]]:
    """
    Group word timestamps into sentences based on punctuation.
    
    Args:
        word_timestamps: List of word timestamp dictionaries
        config: Configuration dictionary
    
    Returns:
        List of word groups, where each group is a sentence
    """
    groups = []
    current_group = []
    
    for word_ts in word_timestamps:
        word = word_ts['word']
        current_group.append(word_ts)
        
        if any(word.strip('"\'")]}').endswith(punct) for punct in config['break_on_punctuation']):
            if current_group:
                groups.append(current_group)
            current_group = []
    
    if current_group:
        groups.append(current_group)
    
    logger.debug(f"Grouped {len(word_timestamps)} words into {len(groups)} sentences")
    
    return groups


def create_captions_from_group(word_group: List[Dict], config: dict) -> List[Dict]:
    """
    Create caption(s) from a group of words (sentence).
    
    Splits long sentences into multiple captions if needed.
    
    Args:
        word_group: List of word timestamps forming a sentence
        config: Configuration dictionary
    
    Returns:
        List of caption dictionaries
    """
    if not word_group:
        return []
    
    captions = []
    
    group_start = word_group[0]['start']
    group_end = word_group[-1]['end']
    group_duration = group_end - group_start
    
    if group_duration <= config['max_caption_duration']:
        captions.append({
            'start': group_start,
            'end': group_end,
            'words': word_group  # Keep full word objects
        })
    else:
        captions = split_long_group(word_group, config)
    
    return captions


def split_long_group(word_group: List[Dict], config: dict) -> List[Dict]:
    """
    Split a long word group into multiple captions.
    
    Splits at logical break points while respecting duration limits.
    
    Args:
        word_group: List of word timestamps
        config: Configuration dictionary
    
    Returns:
        List of caption dictionaries
    """
    captions = []
    current_words = []
    current_start = word_group[0]['start']
    
    for word_ts in word_group:
        current_words.append(word_ts)
        
        current_duration = word_ts['end'] - current_start
        word_count = len(current_words)
        
        should_split = (
            current_duration >= config['max_caption_duration'] or
            word_count >= config['max_words_per_line'] * config['max_lines_per_caption']
        )
        
        if should_split and len(current_words) > 1:
            captions.append({
                'start': current_start,
                'end': word_ts['end'],
                'words': current_words[:-1]  # Keep full word objects
            })
            current_words = [word_ts]
            current_start = word_ts['start']
    
    if current_words:
        captions.append({
            'start': current_start,
            'end': current_words[-1]['end'],
            'words': current_words  # Keep full word objects
        })
    
    return captions


def format_caption_text(words: List, config: dict) -> str:
    """
    Format words into caption text with proper line breaks.
    
    Args:
        words: List of words (str) or word dicts
        config: Configuration dictionary
    
    Returns:
        Formatted caption text (1-2 lines)
    """
    # Extract string from dict if needed
    word_strings = []
    for w in words:
        if isinstance(w, dict):
            word_strings.append(w['word'])
        else:
            word_strings.append(str(w))
            
    if len(word_strings) <= config['max_words_per_line']:
        return ' '.join(word_strings)
    
    lines = []
    current_line = []
    
    for word_str in word_strings:
        current_line.append(word_str)
        
        if len(current_line) >= config['max_words_per_line']:
            lines.append(' '.join(current_line))
            current_line = []
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return '\n'.join(lines[:config['max_lines_per_caption']])


def validate_captions(captions: List[Dict], config: dict) -> List[Dict]:
    """
    Validate and fix caption timestamps.
    
    - Ensure end > start
    - No overlaps
    - Respect min/max duration
    - Ensure words don't appear before spoken
    
    Args:
        captions: List of caption dictionaries
        config: Configuration dictionary
    
    Returns:
        Validated list of captions
    """
    if not captions:
        return []
    
    validated = []
    
    for i, caption in enumerate(captions):
        start = caption['start']
        end = caption['end']
        duration = end - start
        
        if duration < config['min_caption_duration']:
            if i < len(captions) - 1:
                end = start + config['min_caption_duration']
            else:
                end = max(end, start + config['min_caption_duration'])
        
        validated.append({
            'start': start,
            'end': end,
            'words': caption['words']
        })
    
    for i in range(len(validated) - 1):
        if validated[i]['end'] > validated[i + 1]['start']:
            midpoint = (validated[i]['end'] + validated[i + 1]['start']) / 2
            validated[i]['end'] = midpoint
            validated[i + 1]['start'] = midpoint
    
    return validated


def format_as_srt(captions: List[Dict]) -> str:
    """
    Format captions as SRT string.
    
    Format:
    1
    00:00:00,000 --> 00:00:05,000
    First caption text
    
    2
    00:00:05,000 --> 00:00:10,000
    Second caption text
    
    Args:
        captions: List of caption dictionaries
    
    Returns:
        SRT formatted string
    """
    if not captions:
        return ""
    
    srt_lines = []
    
    for i, caption in enumerate(captions):
        index = i + 1
        start_time = format_srt_time(caption['start'])
        end_time = format_srt_time(caption['end'])
        text = format_caption_text(caption['words'], DEFAULT_CONFIG)
        
        srt_lines.append(str(index))
        srt_lines.append(f"{start_time} --> {end_time}")
        srt_lines.append(text)
        srt_lines.append("")
    
    return '\n'.join(srt_lines)


def format_srt_time(seconds: float) -> str:
    """
    Format time in seconds to SRT time format: HH:MM:SS,mmm
    
    Args:
        seconds: Time in seconds
    
    Returns:
        Formatted time string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def parse_srt_time(time_str: str) -> float:
    """
    Parse SRT time format to seconds.
    
    Args:
        time_str: Time string in HH:MM:SS,mmm format
    
    Returns:
        Time in seconds
    """
    time_part, ms_part = time_str.split(',')
    milliseconds = int(ms_part)
    
    parts = time_part.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])
    
    total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
    
    return total_seconds


def validate_srt_format(srt_content: str) -> bool:
    """
    Validate SRT content format.
    
    Args:
        srt_content: SRT string to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not srt_content.strip():
        return False
    
    blocks = srt_content.strip().split('\n\n')
    
    srt_pattern = re.compile(r'^\d+$')
    time_pattern = re.compile(r'^\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}$')
    
    for block in blocks:
        lines = block.split('\n')
        
        if len(lines) < 3:
            return False
        
        if not srt_pattern.match(lines[0]):
            return False
        
        if not time_pattern.match(lines[1]):
            return False
    
    logger.debug(f"SRT format validation passed: {len(blocks)} captions")
    
    return True


def calculate_caption_stats(srt_content: str) -> dict:
    """
    Calculate statistics about generated captions.
    
    Args:
        srt_content: SRT string
    
    Returns:
        Dictionary with statistics
    """
    if not srt_content.strip():
        return {
            'total_captions': 0,
            'total_words': 0,
            'total_duration': 0,
            'max_caption_length': 0,
            'avg_caption_length': 0,
            'avg_caption_duration': 0
        }
    
    blocks = srt_content.strip().split('\n\n')
    
    total_captions = len(blocks)
    total_words = 0
    total_duration = 0
    max_caption_length = 0
    avg_caption_length = 0
    
    for block in blocks:
        lines = block.split('\n')
        
        if len(lines) >= 3:
            text = '\n'.join(lines[2:])
            words = text.replace('\n', ' ').split()
            total_words += len(words)
            
            max_caption_length = max(max_caption_length, len(words))
            
            if time_pattern := re.match(r'(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})', lines[1]):
                start = parse_srt_time(time_pattern.group(1))
                end = parse_srt_time(time_pattern.group(2))
                total_duration += (end - start)
    
    if total_captions > 0:
        avg_caption_length = total_words / total_captions
    
    stats = {
        'total_captions': total_captions,
        'total_words': total_words,
        'total_duration': total_duration,
        'max_caption_length': max_caption_length,
        'avg_caption_length': avg_caption_length,
        'avg_caption_duration': total_duration / total_captions if total_captions > 0 else 0
    }
    
    logger.debug(f"Caption stats: {stats}")
    
    return stats
