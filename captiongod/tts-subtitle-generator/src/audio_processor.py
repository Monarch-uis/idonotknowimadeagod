import logging
import numpy as np
from typing import Tuple, Optional
import librosa
from pydub import AudioSegment

logger = logging.getLogger(__name__)


def load_audio(audio_path: str, sample_rate: int = 22050) -> Tuple[np.ndarray, float]:
    """
    Load audio file and return audio data and duration.
    
    Args:
        audio_path: Path to audio file (MP3, WAV, etc.)
        sample_rate: Target sample rate for resampling
    
    Returns:
        (audio_data, duration) where audio_data is numpy array and duration is in seconds
    """
    try:
        audio_data, sr = librosa.load(audio_path, sr=sample_rate)
        duration = librosa.get_duration(y=audio_data, sr=sr)
        
        logger.info(f"Loaded audio: {audio_path} (duration: {format_duration(duration)})")
        
        if duration < 0.1:
            logger.warning(f"Audio duration too short: {duration:.2f}s")
        
        if np.max(np.abs(audio_data)) < 1e-6:
            logger.error("Audio appears to be silent or corrupted")
        
        return audio_data, duration
        
    except Exception as e:
        logger.error(f"Failed to load audio file {audio_path}: {e}")
        raise


def extract_mfcc(audio_data: np.ndarray, sample_rate: int = 22050, 
                  n_mfcc: int = 13, n_fft: int = 2048, hop_length: int = 512) -> np.ndarray:
    """
    Extract MFCC features from audio data.
    
    Args:
        audio_data: Audio waveform
        sample_rate: Sample rate of audio
        n_mfcc: Number of MFCC coefficients
        n_fft: FFT window size
        hop_length: Number of samples between successive frames
    
    Returns:
        MFCC features as numpy array of shape (n_mfcc, n_frames)
    """
    try:
        mfcc = librosa.feature.mfcc(
            y=audio_data,
            sr=sample_rate,
            n_mfcc=n_mfcc,
            n_fft=n_fft,
            hop_length=hop_length
        )
        
        delta_mfcc = librosa.feature.delta(mfcc)
        delta2_mfcc = librosa.feature.delta(mfcc, order=2)
        
        mfcc_features = np.vstack([mfcc, delta_mfcc, delta2_mfcc])
        
        logger.debug(f"Extracted {mfcc_features.shape[1]} MFCC frames")
        
        return mfcc_features
        
    except Exception as e:
        logger.error(f"Failed to extract MFCC features: {e}")
        raise


def extract_mel_spectrogram(audio_data: np.ndarray, sample_rate: int = 22050,
                           n_mels: int = 80, n_fft: int = 2048, hop_length: int = 512) -> np.ndarray:
    """
    Extract mel-spectrogram features from audio data.
    
    Args:
        audio_data: Audio waveform
        sample_rate: Sample rate of audio
        n_mels: Number of mel bands
        n_fft: FFT window size
        hop_length: Number of samples between successive frames
    
    Returns:
        Mel-spectrogram as numpy array of shape (n_mels, n_frames)
    """
    try:
        mel_spec = librosa.feature.melspectrogram(
            y=audio_data,
            sr=sample_rate,
            n_mels=n_mels,
            n_fft=n_fft,
            hop_length=hop_length
        )
        
        log_mel = librosa.power_to_db(mel_spec, ref=np.max)
        
        logger.debug(f"Extracted {log_mel.shape[1]} mel-spectrogram frames")
        
        return log_mel
        
    except Exception as e:
        logger.error(f"Failed to extract mel-spectrogram: {e}")
        raise


def extract_features(audio_data: np.ndarray, sample_rate: int = 22050,
                    feature_type: str = 'mfcc') -> np.ndarray:
    """
    Extract audio features for alignment.
    
    Args:
        audio_data: Audio waveform
        sample_rate: Sample rate of audio
        feature_type: Type of features ('mfcc' or 'mel')
    
    Returns:
        Feature array
    """
    if feature_type == 'mfcc':
        return extract_mfcc(audio_data, sample_rate)
    elif feature_type == 'mel':
        return extract_mel_spectrogram(audio_data, sample_rate)
    else:
        raise ValueError(f"Unknown feature type: {feature_type}")


def frame_to_time(frame_idx: int, hop_length: int = 512, sample_rate: int = 22050) -> float:
    """
    Convert frame index to time in seconds.
    
    Args:
        frame_idx: Frame index
        hop_length: Hop length used in feature extraction
        sample_rate: Sample rate of audio
    
    Returns:
        Time in seconds
    """
    return frame_idx * hop_length / sample_rate


def time_to_frame(time_seconds: float, hop_length: int = 512, sample_rate: int = 22050) -> int:
    """
    Convert time in seconds to frame index.
    
    Args:
        time_seconds: Time in seconds
        hop_length: Hop length used in feature extraction
        sample_rate: Sample rate of audio
    
    Returns:
        Frame index
    """
    return int(time_seconds * sample_rate / hop_length)


def detect_silence(audio_data: np.ndarray, sample_rate: int = 22050,
                  threshold_db: float = -40, min_duration: float = 0.3) -> list:
    """
    Detect silent regions in audio.
    
    Args:
        audio_data: Audio waveform
        sample_rate: Sample rate of audio
        threshold_db: Silence threshold in dB
        min_duration: Minimum silence duration to report
    
    Returns:
        List of (start_time, end_time) tuples for silent regions
    """
    intervals = librosa.effects.split(audio_data, top_db=abs(threshold_db))
    
    if len(intervals) < 2:
        return []
    
    silent_regions = []
    for i in range(len(intervals) - 1):
        gap_start = intervals[i][1]
        gap_end = intervals[i + 1][0]
        duration = (gap_end - gap_start) / sample_rate
        
        if duration >= min_duration:
            start_time = gap_start / sample_rate
            end_time = gap_end / sample_rate
            silent_regions.append((start_time, end_time))
    
    if silent_regions:
        logger.info(f"Detected {len(silent_regions)} silent regions")
    
    return silent_regions


def normalize_audio(audio_data: np.ndarray) -> np.ndarray:
    """
    Normalize audio to [-1, 1] range.
    
    Args:
        audio_data: Audio waveform
    
    Returns:
        Normalized audio
    """
    max_val = np.max(np.abs(audio_data))
    if max_val > 0:
        return audio_data / max_val
    return audio_data


def trim_audio(audio_data: np.ndarray, sample_rate: int = 22050,
              trim_db: float = 60) -> Tuple[np.ndarray, float, float]:
    """
    Trim leading and trailing silence from audio.
    
    Args:
        audio_data: Audio waveform
        sample_rate: Sample rate of audio
        trim_db: Threshold in dB below reference power to consider as silence
    
    Returns:
        (trimmed_audio, start_time, end_time) in seconds
    """
    trimmed_audio, start_idx = librosa.effects.trim(audio_data, top_db=trim_db)
    end_idx = start_idx + len(trimmed_audio)
    
    start_time = start_idx / sample_rate
    end_time = end_idx / sample_rate
    
    logger.debug(f"Trimmed audio: {start_time:.2f}s to {end_time:.2f}s")
    
    return trimmed_audio, start_time, end_time


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
    
    Returns:
        Formatted string like "1:23:45" or "12:34"
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def get_audio_info(audio_path: str) -> dict:
    """
    Get information about an audio file without loading it fully.
    
    Args:
        audio_path: Path to audio file
    
    Returns:
        Dictionary with audio metadata
    """
    try:
        audio = AudioSegment.from_file(audio_path)
        
        info = {
            'duration': len(audio) / 1000.0,
            'channels': audio.channels,
            'sample_rate': audio.frame_rate,
            'sample_width': audio.sample_width,
            'format': audio_path.split('.')[-1].lower()
        }
        
        logger.debug(f"Audio info: {info}")
        
        return info
        
    except Exception as e:
        logger.error(f"Failed to get audio info: {e}")
        raise


def validate_audio(audio_path: str) -> Tuple[bool, Optional[str]]:
    """
    Validate audio file.
    
    Args:
        audio_path: Path to audio file
    
    Returns:
        (is_valid, error_message)
    """
    try:
        info = get_audio_info(audio_path)
        
        if info['duration'] < 0.1:
            return False, "Audio duration too short"
        
        if info['duration'] > 86400:
            return False, "Audio duration too long (>24 hours)"
        
        if info['sample_rate'] < 8000:
            return False, f"Sample rate too low: {info['sample_rate']}Hz"
        
        return True, None
        
    except Exception as e:
        return False, str(e)
