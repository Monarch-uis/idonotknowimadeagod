import argparse
import logging
import sys
from pathlib import Path

from text_processor import preprocess_text, validate_text_audio_match
from audio_processor import load_audio, extract_features, validate_audio, format_duration
from aligner import align_text_to_audio, calculate_alignment_confidence
from chunker import process_long_audio
from srt_generator import generate_srt, validate_srt_format, calculate_caption_stats

DEFAULT_CONFIG = {
    'max_words_per_line': 12,
    'max_lines_per_caption': 2,
    'max_caption_duration': 7.0,
    'min_caption_duration': 1.0,
    'chunk_duration': 600,
    'word_timing_tolerance': 0.1,
    'break_on_punctuation': ['.', '!', '?', ';'],
    'pause_threshold': 0.3
}


def setup_logging(verbose: bool):
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )


def generate_subtitles(text_path: str,
                       audio_path: str,
                       output_path: str,
                       config: dict,
                       verbose: bool = False) -> bool:
    """
    Main pipeline: generate SRT subtitles from text and audio.
    
    Args:
        text_path: Path to text file
        audio_path: Path to audio file
        output_path: Path for output SRT file
        config: Configuration dictionary
        verbose: Enable verbose logging
    
    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=" * 60)
        logger.info("TTS Subtitle Generator")
        logger.info("=" * 60)
        
        if not Path(text_path).exists():
            logger.error(f"Text file not found: {text_path}")
            return False
        
        if not Path(audio_path).exists():
            logger.error(f"Audio file not found: {audio_path}")
            return False
        
        logger.info(f"Input text: {text_path}")
        logger.info(f"Input audio: {audio_path}")
        logger.info(f"Output: {output_path}")
        
        is_valid, error_msg = validate_audio(audio_path)
        if not is_valid:
            logger.error(f"Invalid audio file: {error_msg}")
            return False
        
        logger.info("Reading text file...")
        with open(text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        if not text.strip():
            logger.error("Text file is empty")
            return False
        
        logger.info("Preprocessing text...")
        word_tokens = preprocess_text(text)
        
        if not word_tokens:
            logger.error("No valid words found in text")
            return False
        
        logger.info(f"Extracted {len(word_tokens)} words from text")
        
        logger.info("Loading audio...")
        audio_data, audio_duration = load_audio(audio_path)
        
        is_match, expected_duration, actual_duration = validate_text_audio_match(
            text, audio_duration, tolerance=0.2
        )
        
        if not is_match:
            logger.warning(
                f"\nWARNING: Audio duration ({format_duration(actual_duration)}) "
                f"doesn't match expected reading time ({format_duration(expected_duration)}).\n"
                f"Possible causes:\n"
                f"  - Wrong audio file\n"
                f"  - Text contains content not in audio\n"
                f"  - TTS speech rate is much faster/slower than expected\n\n"
                f"Suggestion: Verify audio file and text match.\n"
            )
        
        logger.info("Extracting audio features...")
        
        if audio_duration <= config['chunk_duration']:
            audio_features = extract_features(audio_data)
            
            logger.info("Performing forced alignment...")
            word_timestamps = align_text_to_audio(word_tokens, audio_features)
        else:
            logger.info(f"Long audio detected ({format_duration(audio_duration)}). Processing in chunks...")
            
            def align_func(words, features):
                return align_text_to_audio(words, features, smooth=True)
            
            def extract_func(audio):
                return extract_features(audio)
            
            word_timestamps = process_long_audio(
                word_tokens, audio_data, 22050, audio_duration,
                chunk_duration=config['chunk_duration'],
                aligner_func=align_func,
                feature_extractor_func=extract_func,
                verbose=verbose
            )
        
        if not word_timestamps:
            logger.error("Alignment failed: no word timestamps generated")
            return False
        
        logger.info(f"Generated {len(word_timestamps)} word timestamps")
        
        confidence = calculate_alignment_confidence(word_timestamps, audio_duration)
        logger.info(f"Alignment confidence: {confidence:.2%}")
        
        if confidence < 0.5:
            logger.warning("Low alignment confidence detected. Results may be inaccurate.")
        
        if output_path.lower().endswith('.ass'):
            logger.info("Generating ASS captions...")
            from ass_generator import generate_ass
            content = generate_ass(word_timestamps, config)
            format_name = "ASS"
        else:
            logger.info("Generating SRT captions...")
            content = generate_srt(word_timestamps, config)
            format_name = "SRT"
        
        if not content:
            logger.error(f"Failed to generate {format_name} content")
            return False
        
        if format_name == "SRT":
            if not validate_srt_format(content):
                logger.warning("Generated SRT has format issues, but writing anyway")
            
            stats = calculate_caption_stats(content)
            logger.info(f"Caption statistics:")
            logger.info(f"  Total captions: {stats['total_captions']}")
            logger.info(f"  Total words: {stats['total_words']}")
            logger.info(f"  Avg caption duration: {stats['avg_caption_duration']:.2f}s")
            logger.info(f"  Avg words per caption: {stats['avg_caption_length']:.1f}")
        
        logger.info(f"Writing output: {output_path}")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info("=" * 60)
        logger.info("Done! Subtitles generated successfully.")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error generating subtitles: {e}", exc_info=verbose)
        return False


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description='Generate SRT subtitles by aligning text with TTS-generated audio',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  tts-subtitles input.txt input.mp3 -o output.srt
  
  # With custom settings
  tts-subtitles input.txt input.mp3 --output output.srt --max-duration 8 --verbose
  
  # Long audio with smaller chunks
  tts-subtitles input.txt long_audio.mp3 --chunk-size 300
        """
    )
    
    parser.add_argument('text_file', help='Path to text file')
    parser.add_argument('audio_file', help='Path to audio file (MP3, WAV)')
    parser.add_argument('-o', '--output', help='Output SRT file path (default: subtitles.srt)', 
                        default='subtitles.srt')
    parser.add_argument('--max-words-per-line', type=int, default=12,
                        help='Maximum words per caption line (default: 12)')
    parser.add_argument('--max-duration', type=float, default=7.0,
                        help='Maximum caption duration in seconds (default: 7.0)')
    parser.add_argument('--chunk-size', type=int, default=600,
                        help='Chunk duration in seconds for long audio (default: 600)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose logging')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    config = DEFAULT_CONFIG.copy()
    config['max_words_per_line'] = args.max_words_per_line
    config['max_caption_duration'] = args.max_duration
    config['chunk_duration'] = args.chunk_size
    
    success = generate_subtitles(
        args.text_file,
        args.audio_file,
        args.output,
        config,
        args.verbose
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
