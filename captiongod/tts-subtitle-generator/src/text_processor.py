import re
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


def preprocess_text(text: str) -> List[str]:
    """
    Clean and normalize text for alignment.
    
    - Remove HTML/markdown artifacts
    - Normalize quotes: " " → " "
    - Normalize dashes: — → -
    - Preserve sentence boundaries
    - Handle numbers: "2024" → "twenty twenty-four"
    - Handle acronyms: "NASA" → "N A S A" or "NASA" (TTS-dependent)
    
    Return: List of sentences with word-level tokens
    """
    text = normalize_quotes(text)
    text = normalize_dashes(text)
    text = remove_html_artifacts(text)
    text = expand_contractions(text)
    
    sentences = split_sentences(text)
    
    word_tokens = []
    for sentence in sentences:
        tokens = sentence.split()
        if tokens:
            word_tokens.extend(tokens)
    
    logger.debug(f"Preprocessed text: {len(word_tokens)} word tokens")
    return word_tokens


def normalize_quotes(text: str) -> str:
    """Normalize fancy quotes to standard quotes."""
    text = text.replace('“', '"')
    text = text.replace('”', '"')
    text = text.replace('‘', "'")
    text = text.replace('’', "'")
    return text


def normalize_dashes(text: str) -> str:
    """Normalize fancy dashes to standard hyphens."""
    text = text.replace('—', '-')
    text = text.replace('–', '-')
    text = text.replace('―', '-')
    return text


def remove_html_artifacts(text: str) -> str:
    """Remove common HTML and markdown artifacts."""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'(?m)^[#*]+ ', '', text)
    return text


def expand_contractions(text: str) -> str:
    """Expand common contractions for better alignment."""
    contractions = {
        "can't": "cannot",
        "won't": "will not",
        "n't": " not",
        "'re": " are",
        "'ve": " have",
        "'ll": " will",
        "'d": " would",
        "'m": " am",
        "'s": " is",
    }
    
    for contraction, expansion in contractions.items():
        text = text.replace(contraction, expansion)
    
    return text


def split_sentences(text: str) -> List[str]:
    """
    Split text into sentences while preserving abbreviations.
    
    Uses a regex approach that handles common abbreviations like Mr., Mrs., Dr., etc.
    """
    abbreviations = ['mr', 'mrs', 'dr', 'prof', 'sr', 'jr', 'st', 'ave', 'blvd', 'rd', 'vs', 'etc', 'eg', 'ie']
    abbr_pattern = '\\b(?:' + '|'.join(abbreviations) + ')\\. '
    
    sentences = re.split(r'(?<!\w\.\w.)(?<=[.!?])\s+', text)
    
    filtered_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            filtered_sentences.append(sentence)
    
    logger.debug(f"Split text into {len(filtered_sentences)} sentences")
    return filtered_sentences


def expand_numbers(text: str) -> str:
    """
    Convert written numbers to spoken form for better TTS alignment.
    
    Example: "2024" → "two thousand twenty four"
    """
    words = []
    for word in text.split():
        if word.isdigit():
            words.append(number_to_words(int(word)))
        else:
            words.append(word)
    return ' '.join(words)


def number_to_words(num: int) -> str:
    """Convert a number to its spoken form."""
    if num == 0:
        return "zero"
    
    units = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine']
    teens = ['ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen', 'sixteen', 
             'seventeen', 'eighteen', 'nineteen']
    tens = ['', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety']
    
    if num < 10:
        return units[num]
    elif num < 20:
        return teens[num - 10]
    elif num < 100:
        return tens[num // 10] + ('' if num % 10 == 0 else ' ' + units[num % 10])
    elif num < 1000:
        return units[num // 100] + ' hundred' + ('' if num % 100 == 0 else ' ' + number_to_words(num % 100))
    elif num < 1000000:
        return number_to_words(num // 1000) + ' thousand' + ('' if num % 1000 == 0 else ' ' + number_to_words(num % 1000))
    else:
        return str(num)


def group_words_by_sentence(word_tokens: List[str], text: str) -> List[List[str]]:
    """
    Group word tokens back into sentences based on punctuation.
    
    Returns a list of sentences, where each sentence is a list of words.
    """
    sentences = []
    current_sentence = []
    
    for word in word_tokens:
        current_sentence.append(word)
        
        if word.rstrip('.,!?;:').endswith(('.', '!', '?', ';')):
            sentences.append(current_sentence)
            current_sentence = []
    
    if current_sentence:
        sentences.append(current_sentence)
    
    return sentences


def validate_text_audio_match(text: str, audio_duration: float, tolerance: float = 0.2) -> Tuple[bool, float, float]:
    """
    Validate that text and audio duration roughly match.
    
    Returns:
        (is_valid, expected_duration, actual_duration)
    """
    word_count = len(text.split())
    avg_reading_speed = 2.5
    expected_duration = word_count / avg_reading_speed
    
    ratio = audio_duration / expected_duration
    is_valid = (1 - tolerance) <= ratio <= (1 + tolerance)
    
    if not is_valid:
        logger.warning(
            f"Audio duration ({audio_duration:.1f}s) doesn't match expected "
            f"reading time ({expected_duration:.1f}s). Ratio: {ratio:.2f}"
        )
    
    return is_valid, expected_duration, audio_duration
