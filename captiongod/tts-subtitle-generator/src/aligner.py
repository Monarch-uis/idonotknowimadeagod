import logging
import numpy as np
from typing import List, Dict, Tuple
from dtw import dtw
from phonemizer import phonemize
import warnings

warnings.filterwarnings('ignore', category=UserWarning)
logger = logging.getLogger(__name__)


def words_to_phonemes_with_counts(words: List[str], language: str = 'en-us') -> Tuple[List[str], List[int]]:
    """
    Convert list of words to phoneme sequence, preserving word counts.
    
    Args:
        words: List of word tokens
        language: Language code for phonemizer
    
    Returns:
        (flat_phoneme_list, phonemes_per_word_list)
    """
    flat_phonemes = []
    counts = []
    
    try:
        # Use batch processing for speed (orders of magnitude faster)
        # njobs=4 to parallelize
        logger.info(f"Phonemizing {len(words)} words in batch...")
        ph_strs = phonemize(words, language=language, backend='espeak', strip=True, with_stress=False, njobs=4)
        
        for i, ph_str in enumerate(ph_strs):
            # ph_str is the phonemized string for a single word
            if not ph_str:
                # Fallback for empty/failed phonemization (e.g. symbols)
                ph_list = [words[i]]
            else:
                ph_list = ph_str.split()
                if not ph_list:
                    ph_list = [words[i]]
            
            flat_phonemes.extend(ph_list)
            counts.append(len(ph_list))
            
        logger.debug(f"Generated {len(flat_phonemes)} phonemes for {len(words)} words")
        return flat_phonemes, counts
        
    except Exception as e:
        logger.warning(f"Batch phonemization failed, falling back to loop: {e}")
        # Fallback loop
        try:
             from tqdm import tqdm
             iterator = tqdm(words, desc="Phonemizing (fallback)", unit="word")
        except ImportError:
             iterator = words

        for word in iterator:
            try:
                ph_str = phonemize(word, language=language, backend='espeak', strip=True, with_stress=False)
                ph_list = ph_str.split()
                if not ph_list:
                    ph_list = [word]
                flat_phonemes.extend(ph_list)
                counts.append(len(ph_list))
            except:
                flat_phonemes.append(word)
                counts.append(1)
        
        return flat_phonemes, counts


def map_phonemes_to_words(words: List[str], phonemes: List[str], phoneme_counts: List[int] = None) -> List[Dict]:
    """
    Map phoneme indices back to word boundaries using explicit counts.
    """
    word_boundaries = []
    phoneme_idx = 0
    
    # If explicit counts are provided (from our new function), use them
    if phoneme_counts and len(phoneme_counts) == len(words):
        for i, word in enumerate(words):
            count = phoneme_counts[i]
            start_idx = phoneme_idx
            end_idx = phoneme_idx + count - 1
            phoneme_idx += count
            
            word_boundaries.append({
                'word': word,
                'start_phoneme_idx': start_idx,
                'end_phoneme_idx': end_idx,
                'phoneme_count': count
            })
    else:
        # Fallback to naive equal distribution (Legacy behavior, generally bad)
        logger.warning("Using naive phoneme distribution (low accuracy)")
        phonemes_per_word = len(phonemes) // len(words) if words else 0
        for i, word in enumerate(words):
            start_idx = phoneme_idx
            count = phonemes_per_word
            # Distribute remainder
            if i < len(phonemes) % len(words):
                count += 1
            
            end_idx = phoneme_idx + count - 1
            phoneme_idx += count
            
            word_boundaries.append({
                'word': word,
                'start_phoneme_idx': start_idx,
                'end_phoneme_idx': end_idx,
                'phoneme_count': count
            })
    
    return word_boundaries


def align_phonemes_to_audio(audio_features: np.ndarray, 
                           phonemes: List[str],
                           sample_rate: int = 22050,
                           hop_length: int = 512) -> List[Dict]:
    """
    Align phoneme sequence to audio features using DTW.
    
    Args:
        audio_features: MFCC or mel-spectrogram features (n_features, n_frames)
        phonemes: List of phonemes to align
        sample_rate: Audio sample rate
        hop_length: Hop length used in feature extraction
    
    Returns:
        List of phoneme timestamps with (phoneme, start_time, end_time)
    """
    if len(phonemes) == 0:
        logger.warning("No phonemes to align")
        return []
    
    phoneme_features = create_phoneme_features(phonemes)
    
    # Fix dimension mismatch: Audio features (39) vs Phoneme features (3)
    # Take first 3 dimensions of audio features (MFCC 1-3)
    # And normalize both to 0-1 range for better alignment
    if audio_features.shape[0] != phoneme_features.shape[0]:
        target_dim = min(audio_features.shape[0], phoneme_features.shape[0])
        audio_features_aligned = audio_features[:target_dim, :]
        phoneme_features_aligned = phoneme_features[:target_dim, :]
    else:
        audio_features_aligned = audio_features
        phoneme_features_aligned = phoneme_features

    # Normalize features
    if np.max(np.abs(audio_features_aligned)) > 0:
        audio_features_aligned = audio_features_aligned / np.max(np.abs(audio_features_aligned))
    
    if np.max(np.abs(phoneme_features_aligned)) > 0:
        phoneme_features_aligned = phoneme_features_aligned / np.max(np.abs(phoneme_features_aligned))

    try:
        alignment = dtw(
            audio_features_aligned.T,
            phoneme_features_aligned.T,
            keep_internals=True
        )
        
        path = alignment.index2s
        
        phoneme_timestamps = []
        for i in range(len(phonemes)):
            path_indices = np.where(path == i)[0]
            
            if len(path_indices) == 0:
                continue
            
            start_frame = path_indices[0]
            end_frame = path_indices[-1]
            
            start_time = start_frame * hop_length / sample_rate
            end_time = end_frame * hop_length / sample_rate
            
            phoneme_timestamps.append({
                'phoneme': phonemes[i],
                'start': start_time,
                'end': end_time,
                'duration': end_time - start_time
            })
        
        logger.debug(f"DTW alignment complete. Path length: {len(path)}")
        
        return phoneme_timestamps
        
    except Exception as e:
        logger.error(f"DTW alignment failed: {e}")
        raise


def create_phoneme_features(phonemes: List[str]) -> np.ndarray:
    """
    Create simple features from phonemes for DTW alignment.
    
    Uses a simple mapping based on phoneme characteristics.
    """
    phoneme_to_feature = {
        'aa': [1, 0, 0], 'ae': [1, 0, 1], 'ah': [1, 0, 2],
        'ao': [1, 1, 0], 'aw': [1, 1, 1], 'ay': [1, 1, 2],
        'b': [2, 0, 0], 'ch': [2, 0, 1], 'd': [2, 0, 2],
        'dh': [2, 1, 0], 'eh': [2, 1, 1], 'er': [2, 1, 2],
        'ey': [3, 0, 0], 'f': [3, 0, 1], 'g': [3, 0, 2],
        'hh': [3, 1, 0], 'ih': [3, 1, 1], 'iy': [3, 1, 2],
        'jh': [4, 0, 0], 'k': [4, 0, 1], 'l': [4, 0, 2],
        'm': [4, 1, 0], 'n': [4, 1, 1], 'ng': [4, 1, 2],
        'ow': [5, 0, 0], 'oy': [5, 0, 1], 'p': [5, 0, 2],
        'r': [5, 1, 0], 's': [5, 1, 1], 'sh': [5, 1, 2],
        't': [6, 0, 0], 'th': [6, 0, 1], 'uh': [6, 0, 2],
        'uw': [6, 1, 0], 'v': [6, 1, 1], 'w': [6, 1, 2],
        'y': [7, 0, 0], 'z': [7, 0, 1], 'zh': [7, 0, 2]
    }
    
    features = []
    for phoneme in phonemes:
        base_phoneme = phoneme.lower().rstrip('012')
        feature = phoneme_to_feature.get(base_phoneme, [0, 0, 0])
        features.append(feature)
    
    return np.array(features).T


def phonemes_to_word_timestamps(phoneme_timestamps: List[Dict],
                                word_boundaries: List[Dict]) -> List[Dict]:
    """
    Convert phoneme timestamps to word timestamps.
    
    Args:
        phoneme_timestamps: List of phoneme timestamp dictionaries
        word_boundaries: List of word boundary dictionaries
    
    Returns:
        List of word timestamp dictionaries
    """
    word_timestamps = []
    
    for boundary in word_boundaries:
        start_idx = boundary['start_phoneme_idx']
        end_idx = boundary['end_phoneme_idx']
        
        if start_idx >= len(phoneme_timestamps):
            logger.warning(f"Word '{boundary['word']}' has no phonemes aligned")
            continue
        
        if end_idx >= len(phoneme_timestamps):
            end_idx = len(phoneme_timestamps) - 1
        
        word_start = phoneme_timestamps[start_idx]['start']
        word_end = phoneme_timestamps[end_idx]['end']
        
        word_timestamps.append({
            'word': boundary['word'],
            'start': word_start,
            'end': word_end,
            'duration': word_end - word_start,
            'confidence': 1.0
        })
    
    return word_timestamps


def smooth_timestamps(word_timestamps: List[Dict], 
                      window_size: int = 3) -> List[Dict]:
    """
    Apply smoothing to reduce jitter in timestamps.
    
    Args:
        word_timestamps: List of word timestamps
        window_size: Size of smoothing window
    
    Returns:
        Smoothed word timestamps
    """
    if len(word_timestamps) <= window_size:
        return word_timestamps
    
    smoothed = []
    
    for i, word_ts in enumerate(word_timestamps):
        half_window = window_size // 2
        start = max(0, i - half_window)
        end = min(len(word_timestamps), i + half_window + 1)
        
        window = word_timestamps[start:end]
        
        if i == 0:
            new_start = word_ts['start']
        else:
            avg_start = np.mean([w['start'] for w in window])
            new_start = (word_ts['start'] + avg_start) / 2
        
        if i == len(word_timestamps) - 1:
            new_end = word_ts['end']
        else:
            avg_end = np.mean([w['end'] for w in window])
            new_end = (word_ts['end'] + avg_end) / 2
        
        smoothed.append({
            'word': word_ts['word'],
            'start': new_start,
            'end': new_end,
            'duration': new_end - new_start,
            'confidence': word_ts['confidence']
        })
    
    return smoothed


def align_text_to_audio(words: List[str], 
                        audio_features: np.ndarray,
                        sample_rate: int = 22050,
                        hop_length: int = 512,
                        smooth: bool = True) -> List[Dict]:
    """
    Core alignment function.
    
    Input:
    - words: List[str] - word tokens from text
    - audio_features: np.array - MFCC/mel-spectrogram
    
    Output:
    - word_timestamps: List[Dict] with structure:
      {
          'word': str,
          'start': float,  # seconds
          'end': float,
          'confidence': float
      }
    
    Algorithm:
    1. Convert words → phonemes
    2. Create phoneme sequence
    3. DTW alignment between phoneme sequence and audio features
    4. Map phoneme times back to word boundaries
    5. Apply smoothing to avoid jitter
    """
    if len(words) == 0:
        logger.warning("No words to align")
        return []
    
    logger.info(f"Aligning {len(words)} words to audio...")
    
    # 1. Get word structure (phoneme counts as weights)
    phonemes, counts = words_to_phonemes_with_counts(words)
    
    # 2. Extract energy profile from MFCCs (0th coeff is approx log energy)
    # features shape: (n_features, n_frames)
    if audio_features.shape[0] > 0:
        energy = audio_features[0, :]
        # Normalize energy
        if np.max(energy) != np.min(energy):
            energy = (energy - np.min(energy)) / (np.max(energy) - np.min(energy))
        else:
            energy = np.ones_like(energy)
    else:
        logger.warning("Empty audio features")
        return []

    # 3. Detect speech regions (simple thresholding)
    # TTS is usually clean, so simple threshold works well
    threshold = 0.3  # Conservative threshold
    is_speech = energy > threshold
    
    # Fill short gaps (smoothing)
    # A gap of < 0.2s (approx 8-10 frames at default hop) should be filled
    gap_limit_frames = int(0.2 * sample_rate / hop_length) 
    
    # Simple gap filling
    last_speech = -gap_limit_frames
    for i in range(len(is_speech)):
        if is_speech[i]:
            if i - last_speech < gap_limit_frames:
                is_speech[last_speech:i] = True
            last_speech = i
            
    # Count speech frames
    total_speech_frames = np.sum(is_speech)
    total_weight = sum(counts)
    
    if total_speech_frames == 0 or total_weight == 0:
         logger.warning("No speech detected or no text. Falling back to simple linear.")
         return simple_word_alignment(words, audio_features, sample_rate, hop_length)

    # 4. Allocating frames to words
    frames_per_weight = total_speech_frames / total_weight
    
    word_timestamps = []
    
    # Find start/end of speech roughly
    # We want to map the sequence of words to the sequence of speech frames
    
    # Create list of speech frame indices
    speech_indices = np.where(is_speech)[0]
    
    # If we have disparate islands of speech, this linear mapping over speech indices 
    # handles jumping over silence automatically!
    
    current_speech_idx = 0
    
    for i, word in enumerate(words):
        weight = counts[i]
        frames_needed = weight * frames_per_weight
        
        start_speech_idx = int(current_speech_idx)
        end_speech_idx = int(current_speech_idx + frames_needed)
        
        # Ensure we don't go out of bounds
        if end_speech_idx >= len(speech_indices):
            end_speech_idx = len(speech_indices) - 1
            
        start_frame = speech_indices[start_speech_idx]
        end_frame = speech_indices[end_speech_idx]
        
        start_time = start_frame * hop_length / sample_rate
        end_time = end_frame * hop_length / sample_rate
        
        word_timestamps.append({
            'word': word,
            'start': start_time,
            'end': end_time,
            'duration': end_time - start_time,
            'confidence': 0.8
        })
        
        current_speech_idx += frames_needed
        
    word_timestamps = validate_timestamps(word_timestamps)
    logger.info(f"Alignment complete (Energy-based). Generated {len(word_timestamps)} word timestamps")
    return word_timestamps


def simple_word_alignment(words: List[str],
                         audio_features: np.ndarray,
                         sample_rate: int = 22050,
                         hop_length: int = 512) -> List[Dict]:
    """
    Fallback alignment: distribute words evenly across audio duration.
    
    Used when phonemization fails or for very short clips.
    """
    n_frames = audio_features.shape[1]
    audio_duration = n_frames * hop_length / sample_rate
    
    time_per_word = audio_duration / len(words)
    
    word_timestamps = []
    for i, word in enumerate(words):
        start = i * time_per_word
        end = (i + 1) * time_per_word
        word_timestamps.append({
            'word': word,
            'start': start,
            'end': end,
            'duration': end - start,
            'confidence': 0.5
        })
    
    return word_timestamps


def validate_timestamps(word_timestamps: List[Dict]) -> List[Dict]:
    """
    Validate and fix timestamp issues.
    
    - Ensure timestamps don't go backwards
    - Ensure end > start
    - Remove overlapping timestamps
    """
    if not word_timestamps:
        return []
    
    validated = []
    current_end = 0
    
    for i, ts in enumerate(word_timestamps):
        if ts['start'] < current_end:
            ts['start'] = current_end
        
        if ts['end'] <= ts['start']:
            ts['end'] = ts['start'] + 0.1
        
        validated.append(ts)
        current_end = ts['end']
    
    return validated


def calculate_alignment_confidence(word_timestamps: List[Dict],
                                   audio_duration: float) -> float:
    """
    Calculate overall confidence score for alignment.
    
    Based on coverage and duration consistency.
    """
    if not word_timestamps:
        return 0.0
    
    total_duration = sum(ts['duration'] for ts in word_timestamps)
    coverage = total_duration / audio_duration
    
    durations = [ts['duration'] for ts in word_timestamps]
    avg_duration = np.mean(durations)
    duration_variance = np.var(durations) / (avg_duration ** 2) if avg_duration > 0 else 0
    
    confidence = coverage * (1 - min(duration_variance, 1))
    
    return confidence
