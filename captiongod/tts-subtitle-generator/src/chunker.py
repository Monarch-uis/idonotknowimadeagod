import logging
import numpy as np
from typing import List, Tuple, Dict
from tqdm import tqdm

logger = logging.getLogger(__name__)


def split_text_into_chunks(text_tokens: List[str], 
                          n_chunks: int,
                          avg_words_per_minute: float = 150.0) -> List[List[str]]:
    """
    Split text tokens into roughly equal chunks.
    
    Args:
        text_tokens: List of word tokens
        n_chunks: Number of chunks to create
        avg_words_per_minute: Average speaking rate for TTS
    
    Returns:
        List of text chunks (each is a list of tokens)
    """
    if n_chunks <= 1:
        return [text_tokens]
    
    if not text_tokens:
        return [[]]
    
    total_words = len(text_tokens)
    words_per_chunk = total_words // n_chunks
    
    chunks = []
    current_chunk = []
    word_count = 0
    
    for token in text_tokens:
        current_chunk.append(token)
        word_count += 1
        
        if word_count >= words_per_chunk and len(chunks) < n_chunks - 1:
            chunks.append(current_chunk)
            current_chunk = []
            word_count = 0
    
    if current_chunk:
        chunks.append(current_chunk)
    
    logger.debug(f"Split text into {len(chunks)} chunks")
    
    return chunks


def estimate_chunks(audio_duration: float, 
                    chunk_duration: float = 600.0) -> int:
    """
    Estimate number of chunks needed for audio duration.
    
    Args:
        audio_duration: Total audio duration in seconds
        chunk_duration: Target duration per chunk in seconds (default 10 minutes)
    
    Returns:
        Number of chunks
    """
    n_chunks = int(np.ceil(audio_duration / chunk_duration))
    return max(1, n_chunks)


def create_audio_chunks(audio_data: np.ndarray,
                        sample_rate: int,
                        n_chunks: int,
                        overlap: float = 2.0) -> List[Tuple[np.ndarray, float, float]]:
    """
    Split audio into overlapping chunks.
    
    Args:
        audio_data: Audio waveform
        sample_rate: Sample rate
        n_chunks: Number of chunks to create
        overlap: Overlap duration in seconds between chunks
    
    Returns:
        List of (chunk_audio, start_time, end_time) tuples
    """
    if n_chunks <= 1:
        return [(audio_data, 0.0, len(audio_data) / sample_rate)]
    
    total_samples = len(audio_data)
    chunk_samples = total_samples // n_chunks
    overlap_samples = int(overlap * sample_rate)
    
    chunks = []
    current_start = 0
    
    for i in range(n_chunks):
        chunk_end = min(current_start + chunk_samples + overlap_samples, total_samples)
        
        chunk_audio = audio_data[current_start:chunk_end]
        start_time = current_start / sample_rate
        end_time = chunk_end / sample_rate
        
        chunks.append((chunk_audio, start_time, end_time))
        
        current_start = chunk_end - overlap_samples
        
        if current_start >= total_samples:
            break
    
    logger.debug(f"Created {len(chunks)} audio chunks with {overlap}s overlap")
    
    return chunks


def merge_timestamps(chunk_results: List[Dict], 
                    overlap: float = 2.0) -> List[Dict]:
    """
    Merge timestamps from multiple chunks, adjusting for offsets.
    
    Args:
        chunk_results: List of dictionaries containing:
            - 'offset': Time offset for this chunk
            - 'timestamps': List of word timestamps
        overlap: Overlap duration between chunks
    
    Returns:
        Merged list of word timestamps
    """
    if not chunk_results:
        return []
    
    all_timestamps = []
    
    for i, chunk in enumerate(chunk_results):
        offset = chunk['offset']
        timestamps = chunk['timestamps']
        
        adjusted_timestamps = []
        for ts in timestamps:
            adjusted_ts = {
                'word': ts['word'],
                'start': ts['start'] + offset,
                'end': ts['end'] + offset,
                'duration': ts['duration'],
                'confidence': ts['confidence'],
                'chunk_id': i
            }
            adjusted_timestamps.append(adjusted_ts)
        
        all_timestamps.extend(adjusted_timestamps)
    
    merged = remove_overlap_timestamps(all_timestamps, overlap)
    
    logger.debug(f"Merged {len(all_timestamps)} timestamps into {len(merged)}")
    
    return merged


def remove_overlap_timestamps(timestamps: List[Dict], 
                             overlap_threshold: float = 2.0) -> List[Dict]:
    """
    Remove overlapping timestamps from chunk boundaries.
    
    Args:
        timestamps: List of all timestamps from all chunks
        overlap_threshold: Maximum allowed overlap
    
    Returns:
        Deduplicated timestamps
    """
    if not timestamps:
        return []
    
    timestamps.sort(key=lambda x: x['start'])
    
    deduplicated = []
    last_ts = None
    
    for ts in timestamps:
        if last_ts is None:
            deduplicated.append(ts)
            last_ts = ts
        else:
            overlap_start = max(last_ts['start'], ts['start'])
            overlap_end = min(last_ts['end'], ts['end'])
            overlap_duration = max(0, overlap_end - overlap_start)
            
            if overlap_duration < overlap_threshold:
                deduplicated.append(ts)
                last_ts = ts
            elif last_ts['chunk_id'] < ts['chunk_id']:
                deduplicated.append(ts)
                last_ts = ts
    
    return deduplicated


def smooth_chunk_transitions(timestamps: List[Dict],
                             overlap: float = 2.0) -> List[Dict]:
    """
    Smooth timestamps at chunk boundaries to prevent jumps.
    
    Args:
        timestamps: List of merged timestamps
        overlap: Overlap duration used in chunking
    
    Returns:
        Smoothed timestamps
    """
    if len(timestamps) < 3:
        return timestamps
    
    smoothed = timestamps.copy()
    
    for i in range(1, len(timestamps)):
        prev_ts = smoothed[i - 1]
        curr_ts = smoothed[i]
        
        if curr_ts['start'] < prev_ts['end']:
            transition_point = (prev_ts['end'] + curr_ts['start']) / 2
            prev_ts['end'] = transition_point
            curr_ts['start'] = transition_point
    
    return smoothed


def process_long_audio(text_tokens: List[str],
                       audio_data: np.ndarray,
                       sample_rate: int,
                       audio_duration: float,
                       chunk_duration: float = 600.0,
                       overlap: float = 2.0,
                       aligner_func=None,
                       feature_extractor_func=None,
                       verbose: bool = False) -> List[Dict]:
    """
    Process audio in chunks to prevent drift and memory issues.
    
    Steps:
    1. Split text into roughly equal chunks (by word count)
    2. Estimate time per chunk based on average TTS rate
    3. Extract audio segments with 2-second overlap
    4. Align each chunk independently
    5. Merge timestamps, adjusting for chunk offsets
    6. Smooth transitions at chunk boundaries
    
    Log each chunk: "Processing chunk 3/12 (10:00-20:00)..."
    
    Args:
        text_tokens: List of word tokens
        audio_data: Audio waveform
        sample_rate: Sample rate
        audio_duration: Total audio duration
        chunk_duration: Target chunk duration in seconds
        overlap: Overlap between chunks in seconds
        aligner_func: Function to perform alignment
        feature_extractor_func: Function to extract audio features
        verbose: Whether to show progress bar
    
    Returns:
        List of word timestamps
    """
    n_chunks = estimate_chunks(audio_duration, chunk_duration)
    
    if n_chunks == 1:
        logger.info("Processing single chunk (audio < 10 minutes)")
        
        if feature_extractor_func is None or aligner_func is None:
            raise ValueError("Both feature_extractor_func and aligner_func must be provided")
        
        audio_features = feature_extractor_func(audio_data)
        word_timestamps = aligner_func(text_tokens, audio_features)
        
        return word_timestamps
    
    logger.info(f"Processing audio in {n_chunks} chunks ({chunk_duration}s each)")
    
    text_chunks = split_text_into_chunks(text_tokens, n_chunks)
    audio_chunks = create_audio_chunks(audio_data, sample_rate, n_chunks, overlap)
    
    chunk_results = []
    
    iterator = range(n_chunks)
    if verbose:
        iterator = tqdm(iterator, desc="Processing chunks", unit="chunk")
    
    for i in iterator:
        chunk_start = audio_chunks[i][1]
        chunk_end = audio_chunks[i][2]
        
        logger.info(f"Processing chunk {i+1}/{n_chunks} ({format_time(chunk_start)} - {format_time(chunk_end)})")
        
        chunk_audio = audio_chunks[i][0]
        chunk_text = text_chunks[i] if i < len(text_chunks) else text_chunks[-1]
        
        if feature_extractor_func is None or aligner_func is None:
            raise ValueError("Both feature_extractor_func and aligner_func must be provided")
        
        try:
            audio_features = feature_extractor_func(chunk_audio)
            chunk_timestamps = aligner_func(chunk_text, audio_features)
            
            chunk_results.append({
                'offset': chunk_start,
                'timestamps': chunk_timestamps
            })
            
            logger.debug(f"Chunk {i+1} aligned: {len(chunk_timestamps)} words")
            
        except Exception as e:
            logger.error(f"Error processing chunk {i+1}: {e}")
            raise
    
    word_timestamps = merge_timestamps(chunk_results, overlap)
    word_timestamps = smooth_chunk_transitions(word_timestamps, overlap)
    
    logger.info(f"Chunk processing complete. Total: {len(word_timestamps)} words")
    
    return word_timestamps


def format_time(seconds: float) -> str:
    """
    Format time in seconds to MM:SS or HH:MM:SS.
    
    Args:
        seconds: Time in seconds
    
    Returns:
        Formatted time string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def validate_chunk_consistency(chunk_results: List[Dict],
                               expected_word_count: int,
                               tolerance: float = 0.1) -> bool:
    """
    Validate that all chunks were processed consistently.
    
    Args:
        chunk_results: Results from all chunks
        expected_word_count: Expected total word count
        tolerance: Allowed deviation in word count
    
    Returns:
        True if consistent, False otherwise
    """
    total_words = sum(len(chunk['timestamps']) for chunk in chunk_results)
    
    ratio = total_words / expected_word_count
    is_valid = (1 - tolerance) <= ratio <= (1 + tolerance)
    
    if not is_valid:
        logger.warning(
            f"Word count mismatch: expected {expected_word_count}, "
            f"got {total_words} (ratio: {ratio:.2f})"
        )
    
    return is_valid
