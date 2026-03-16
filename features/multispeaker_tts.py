"""
Multi-Speaker TTS Generation
Handles generation of audio with multiple voices based on Gemini AI segment analysis.
"""
import os
import time
import logging
from typing import List, Dict, Tuple, Optional
from moviepy.editor import AudioFileClip, concatenate_audioclips, AudioClip
import numpy as np

from core.config import CONFIG
from core.utils import logger, CP
from core.tts import (
    gen_single_clip_piper_with_retry,
    gen_single_clip_edge_with_retry,
    gen_single_clip_chatterbox,
    CHATTERBOX_AVAILABLE
)

class MultiSpeakerTTSError(Exception):
    """Custom exception for multi-speaker TTS errors"""
    pass

def generate_silence(duration_seconds: float, sample_rate: int = 22050) -> AudioClip:
    """
    Generate a silent audio clip
    
    Args:
        duration_seconds: Duration of silence
        sample_rate: Audio sample rate
        
    Returns:
        AudioClip with silence
    """
    samples = int(duration_seconds * sample_rate)
    silent_array = np.zeros((samples, 2))  # Stereo
    
    return AudioClip(
        lambda t: silent_array[int(t * sample_rate)] if int(t * sample_rate) < samples else silent_array[-1],
        duration=duration_seconds
    )

def get_voice_config(voice_name: str) -> Dict:
    """
    Get voice configuration from config
    
    Args:
        voice_name: Voice identifier (e.g., 'piper_narrator', 'chatterbox')
        
    Returns:
        Voice configuration dict
    """
    audio_settings = CONFIG.get('audio_settings', {})
    
    if voice_name == 'chatterbox':
        return {
            'engine': 'chatterbox',
            'enabled': audio_settings.get('chatterbox_enabled', False)
        }
    
    elif voice_name.startswith('piper_'):
        # Get voice type (narrator, male, female)
        voice_type = voice_name.replace('piper_', '')
        piper_voices = audio_settings.get('piper_voices', {})
        
        voice_config = piper_voices.get(voice_type, piper_voices.get('narrator', {}))
        
        return {
            'engine': 'piper',
            'model': voice_config.get('model', audio_settings.get('piper_model_path', 'en_US-lessac-medium.onnx')),
            'speaker_id': voice_config.get('speaker_id', 0)
        }
    
    else:
        # Default to narrator
        return {
            'engine': 'piper',
            'model': audio_settings.get('piper_model_path', 'en_US-lessac-medium.onnx'),
            'speaker_id': 0
        }

def generate_segment_audio(
    segment: Dict,
    output_path: str,
    retry_attempts: int = 3
) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """
    Generate audio for a single segment using appropriate TTS engine
    
    Args:
        segment: Segment dict with 'text', 'voice', 'reasoning'
        output_path: Path to save audio file
        retry_attempts: Number of retry attempts
        
    Returns:
        (success, error_message, subtitle_data)
    """
    text = segment['text']
    voice = segment['voice']
    
    # Get voice configuration
    voice_config = get_voice_config(voice)
    engine = voice_config['engine']
    
    logger.debug(f"Generating segment with {engine} ({voice}): {text[:50]}...")
    
    # Generate based on engine
    if engine == 'chatterbox':
        if not voice_config.get('enabled', False) or not CHATTERBOX_AVAILABLE:
            logger.warning("Chatterbox not available, falling back to Piper")
            engine = 'piper'
            voice_config = get_voice_config('piper_narrator')
        else:
            return gen_single_clip_chatterbox(text, output_path)
    
    if engine == 'piper':
        model_path = voice_config.get('model')
        speaker_id = voice_config.get('speaker_id', 0)
        
        return gen_single_clip_piper_with_retry(
            text=text,
            filename=output_path,
            model_path=model_path,
            speaker_id=speaker_id,
            max_retries=retry_attempts,
            silent=True
        )
    
    elif engine == 'edge':
        # Edge TTS (if needed in future)
        return gen_single_clip_edge_with_retry(
            text=text,
            filename=output_path,
            voice=CONFIG.get('audio_settings', {}).get('voice', 'en-US-GuyNeural'),
            max_retries=retry_attempts
        )
    
    else:
        return False, f"Unknown engine: {engine}", None

def concatenate_segments_with_timing(
    segment_audio_files: List[str],
    segment_subtitles: List[Dict],
    output_path: str,
    silence_between_speakers: float = 0.2
) -> Tuple[bool, Optional[str], List[Dict]]:
    """
    Concatenate segment audio files and adjust subtitle timings
    
    Args:
        segment_audio_files: List of audio file paths
        segment_subtitles: List of subtitle data for each segment
        output_path: Output audio file path
        silence_between_speakers: Seconds of silence between different speakers
        
    Returns:
        (success, error_message, merged_subtitles)
    """
    try:
        audio_clips = []
        merged_subtitles = []
        cumulative_time = 0.0
        previous_voice = None
        
        for idx, (audio_file, subtitle_data) in enumerate(zip(segment_audio_files, segment_subtitles)):
            # Load audio clip
            clip = AudioFileClip(audio_file)
            
            # Add silence between different speakers
            current_voice = segment_subtitles[idx].get('voice', 'unknown')
            if previous_voice and previous_voice != current_voice and silence_between_speakers > 0:
                silence = generate_silence(silence_between_speakers)
                audio_clips.append(silence)
                cumulative_time += silence_between_speakers
            
            # Add audio clip
            audio_clips.append(clip)
            
            # Adjust subtitle timings
            if subtitle_data and 'events' in subtitle_data:
                for event in subtitle_data['events']:
                    merged_subtitles.append({
                        'start': event['start'] + cumulative_time,
                        'end': event['end'] + cumulative_time,
                        'text': event['text']
                    })
            
            cumulative_time += clip.duration
            previous_voice = current_voice
        
        # Concatenate all clips
        if not audio_clips:
            return False, "No audio clips to concatenate", []
        
        final_audio = concatenate_audioclips(audio_clips)
        final_audio.write_audiofile(output_path, codec='pcm_s16le', fps=22050, verbose=False, logger=None)
        
        # Close clips
        for clip in audio_clips:
            clip.close()
        
        logger.info(f"Concatenated {len(segment_audio_files)} segments into {output_path}")
        return True, None, merged_subtitles
        
    except Exception as e:
        logger.error(f"Concatenation failed: {e}")
        return False, str(e), []

def gen_multispeaker_chapter(
    segments: List[Dict],
    output_path: str,
    temp_dir: str,
    chapter_number: int
) -> Tuple[bool, Optional[str], Optional[Dict]]:
    """
    Generate audio for a chapter with multiple speakers
    
    Args:
        segments: List of segment dicts from Gemini analysis
        output_path: Final output audio path
        temp_dir: Temporary directory for segment files
        chapter_number: Chapter number (for naming temp files)
        
    Returns:
        (success, error_message, subtitle_data)
    """
    logger.info(f"Generating multi-speaker audio for chapter {chapter_number} ({len(segments)} segments)")
    
    # Create temp directory if needed
    os.makedirs(temp_dir, exist_ok=True)
    
    segment_files = []
    segment_subtitles = []
    
    # Generate each segment
    for idx, segment in enumerate(segments):
        segment_file = os.path.join(temp_dir, f"ch{chapter_number}_seg{idx}.wav")
        
        # Generate audio
        success, error, subtitle_data = generate_segment_audio(segment, segment_file)
        
        if not success:
            logger.error(f"Segment {idx} failed: {error}")
            # Continue with fallback - use narrator voice
            logger.warning(f"Retrying segment {idx} with fallback narrator voice")
            segment_fallback = segment.copy()
            segment_fallback['voice'] = 'piper_narrator'
            success, error, subtitle_data = generate_segment_audio(segment_fallback, segment_file)
            
            if not success:
                # Skip this segment
                logger.error(f"Segment {idx} failed even with fallback, skipping")
                continue
        
        segment_files.append(segment_file)
        subtitle_data_with_voice = subtitle_data.copy() if subtitle_data else {}
        subtitle_data_with_voice['voice'] = segment.get('voice', 'unknown')
        segment_subtitles.append(subtitle_data_with_voice)
    
    if not segment_files:
        return False, "No segments generated successfully", None
    
    # Concatenate segments
    success, error, merged_subtitles = concatenate_segments_with_timing(
        segment_files,
        segment_subtitles,
        output_path,
        silence_between_speakers=0.2
    )
    
    if not success:
        return False, f"Concatenation failed: {error}", None
    
    # Clean up temp files
    for seg_file in segment_files:
        try:
            os.remove(seg_file)
        except OSError:
            pass  # Temp file cleanup non-critical
    
    subtitle_result = {
        'events': merged_subtitles,
        'is_high_precision': False,
        'multi_speaker': True
    }
    
    logger.info(f"Chapter {chapter_number} complete: {len(segments)} segments, {len(merged_subtitles)} subtitle events")
    
    return True, None, subtitle_result

def generate_intro_audio(
    intro_text: str,
    output_path: str,
    voice_recommendation: str = 'chatterbox'
) -> Tuple[bool, Optional[str]]:
    """
    Generate intro audio with recommended voice
    
    Args:
        intro_text: Intro text to speak
        output_path: Output audio path
        voice_recommendation: Recommended voice ('chatterbox' or 'piper_narrator')
        
    Returns:
        (success, error_message)
    """
    logger.info(f"Generating intro audio with {voice_recommendation}")
    
    # Use recommended voice
    if voice_recommendation == 'chatterbox' and CHATTERBOX_AVAILABLE:
        success, error, _ = gen_single_clip_chatterbox(intro_text, output_path)
    else:
        # Fallback to Piper narrator
        success, error, _ = gen_single_clip_piper_with_retry(
            text=intro_text,
            filename=output_path,
            model_path=CONFIG.get('audio_settings', {}).get('piper_model_path', 'en_US-lessac-medium.onnx'),
            speaker_id=0,
            max_retries=3,
            silent=False
        )
    
    if success:
        logger.info(f"Intro audio generated: {output_path}")
    else:
        logger.error(f"Intro audio generation failed: {error}")
    
    return success, error

# ==================== STATISTICS & MONITORING ====================

def analyze_voice_distribution(segments: List[Dict]) -> Dict[str, int]:
    """
    Analyze voice distribution in segments
    
    Args:
        segments: List of segment dicts
        
    Returns:
        Dict mapping voice names to usage counts
    """
    distribution = {}
    for segment in segments:
        voice = segment.get('voice', 'unknown')
        distribution[voice] = distribution.get(voice, 0) + 1
    
    return distribution

def estimate_generation_time(segments: List[Dict]) -> float:
    """
    Estimate total generation time for segments
    
    Args:
        segments: List of segment dicts
        
    Returns:
        Estimated time in seconds
    """
    total_time = 0.0
    
    for segment in segments:
        voice = segment.get('voice', 'piper_narrator')
        text_length = len(segment.get('text', ''))
        
        # Time estimates (rough)
        if 'chatterbox' in voice:
            # Chatterbox is slow - ~3 seconds per 100 chars
            total_time += (text_length / 100) * 3
        elif 'piper' in voice:
            # Piper is fast - ~0.5 seconds per 100 chars
            total_time += (text_length / 100) * 0.5
        else:
            # Default estimate
            total_time += (text_length / 100) * 1
    
    return total_time

def print_segment_summary(segments: List[Dict]):
    """Print a summary of segments for debugging"""
    print(CP("\n📊 SEGMENT SUMMARY:", 'cyan'))
    
    distribution = analyze_voice_distribution(segments)
    for voice, count in sorted(distribution.items()):
        print(f"   {voice}: {count} segments")
    
    estimated_time = estimate_generation_time(segments)
    print(f"   ⏱️  Estimated generation time: {estimated_time:.1f}s ({estimated_time/60:.1f}m)")
    
    total_chars = sum(len(s.get('text', '')) for s in segments)
    print(f"   📝 Total characters: {total_chars:,}")
