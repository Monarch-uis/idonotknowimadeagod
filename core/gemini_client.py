"""
Gemini AI Client
Handles all interactions with Google's Gemini API for story analysis, 
description generation, and TTS segment analysis.
"""
import os
import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️  'google-generativeai' missing. Run: pip install google-generativeai")

from core.config import CONFIG
from core.utils import logger

class GeminiClientError(Exception):
    """Custom exception for Gemini client errors"""
    pass

class GeminiClient:
    """
    Client for interacting with Google's Gemini API
    
    Features:
    - Story analysis (Phase 1)
    - TTS segment analysis (Phase 2)
    - Error handling with retries
    - Token usage tracking
    - Cost estimation
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini client
        
        Args:
            api_key: Gemini API key (if None, reads from config)
        """
        if not GEMINI_AVAILABLE:
            raise GeminiClientError("google-generativeai library not installed")
        
        self.config = CONFIG.get('gemini_settings', {})
        
        # Get API key
        self.api_key = api_key or self.config.get('api_key', '') or os.getenv('GEMINI_API_KEY', '')
        if not self.api_key:
            raise GeminiClientError(
                "No API key found. Set in config.json or GEMINI_API_KEY environment variable.\n"
                "Get your key from: https://ai.google.dev/"
            )
        
        # Configure API
        genai.configure(api_key=self.api_key)
        
        # Model settings
        self.model_name = self.config.get('model', 'gemini-1.5-flash')
        self.temperature = self.config.get('temperature', 0.7)
        self.max_tokens = self.config.get('max_output_tokens', 8192)
        self.timeout = self.config.get('timeout_seconds', 60)
        
        # Retry settings
        self.max_retries = self.config.get('retry_attempts', 3)
        self.retry_delay = self.config.get('retry_delay', 2)
        
        # Usage tracking
        self.total_tokens_used = 0
        self.total_cost_usd = 0.0
        self.request_count = 0
        
        # Cost per 1M tokens (approximate for gemini-2.5-flash)
        self.cost_per_1m_input = 0.075  # $0.075 per 1M input tokens
        self.cost_per_1m_output = 0.30  # $0.30 per 1M output tokens
        
        logger.info(f"Gemini client initialized with model: {self.model_name}")
    
    def _create_model(self, response_mime_type: Optional[str] = None):
        """Create Gemini model instance with settings"""
        generation_config = {
            'temperature': self.temperature,
            'max_output_tokens': self.max_tokens,
        }
        
        if response_mime_type:
            generation_config['response_mime_type'] = response_mime_type
        
        return genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=generation_config
        )
    
    def _make_request(
        self, 
        prompt: str, 
        system_instruction: Optional[str] = None,
        json_mode: bool = False
    ) -> str:
        """
        Make a request to Gemini API with retry logic
        
        Args:
            prompt: The prompt to send
            system_instruction: Optional system instruction
            json_mode: If True, request JSON response
            
        Returns:
            Response text from Gemini
            
        Raises:
            GeminiClientError: If request fails after retries
        """
        for attempt in range(self.max_retries):
            try:
                # Configure JSON mode if requested
                mime_type = "application/json" if json_mode else None
                model = self._create_model(response_mime_type=mime_type)
                
                # Build request
                if system_instruction:
                    full_prompt = f"{system_instruction}\n\n{prompt}"
                else:
                    full_prompt = prompt
                
                if json_mode:
                    full_prompt += "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no preamble, no explanation."
                
                # Make request
                logger.debug(f"Making Gemini request (attempt {attempt + 1}/{self.max_retries})")
                response = model.generate_content(full_prompt)
                
                # Track usage
                self.request_count += 1
                if hasattr(response, 'usage_metadata'):
                    input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
                    output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
                    
                    self.total_tokens_used += (input_tokens + output_tokens)
                    
                    # Estimate cost
                    cost = (input_tokens / 1_000_000 * self.cost_per_1m_input + 
                           output_tokens / 1_000_000 * self.cost_per_1m_output)
                    self.total_cost_usd += cost
                    
                    logger.debug(f"Tokens used: {input_tokens} input, {output_tokens} output (cost: ${cost:.4f})")
                
                # Get response text
                if not response.text:
                    raise GeminiClientError("Empty response from Gemini")
                
                return response.text.strip()
                
            except Exception as e:
                logger.warning(f"Gemini request failed (attempt {attempt + 1}): {e}")
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise GeminiClientError(f"Failed after {self.max_retries} attempts: {e}")
    
    def _parse_json_response(self, response_text: str) -> Dict:
        """
        Parse JSON from response, handling markdown code blocks
        
        Args:
            response_text: Raw response from Gemini
            
        Returns:
            Parsed JSON dict
        """
        # Remove markdown code blocks if present
        text = response_text.strip()
        
        # Remove ```json and ``` markers
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        
        text = text.strip()
        
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {text[:500]}...")
            raise GeminiClientError(f"Invalid JSON response: {e}")
    
    # ==================== PHASE 1: STORY ANALYSIS ====================
    
    def analyze_full_story(
        self, 
        full_text: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze complete story (all chapters) for metadata
        
        Args:
            full_text: Complete EPUB text (all chapters)
            metadata: Book metadata (title, chapter count, etc.)
            
        Returns:
            Dict with story analysis, description, title options, characters
        """
        from core.gemini_prompts import PROMPT_ANALYZE_FULL_STORY
        
        logger.info("Starting full story analysis with Gemini...")
        logger.info(f"Text length: {len(full_text)} characters (~{len(full_text.split())} words)")
        
        prompt = PROMPT_ANALYZE_FULL_STORY.format(
            book_title=metadata.get('title', 'Unknown'),
            total_chapters=metadata.get('total_chapters', 'Unknown'),
            word_count=len(full_text.split()),
            full_text=full_text[:500000]  # Limit to ~500k chars to avoid token limits
        )
        
        try:
            response = self._make_request(prompt, json_mode=True)
            result = self._parse_json_response(response)
            
            # Validate required fields
            required_fields = ['story_analysis', 'description', 'title_options']
            for field in required_fields:
                if field not in result:
                    raise GeminiClientError(f"Missing required field: {field}")
            
            logger.info(f"Story analysis complete! Found {len(result['story_analysis'].get('characters', []))} characters")
            return result
            
        except Exception as e:
            logger.error(f"Story analysis failed: {e}")
            raise GeminiClientError(f"Story analysis failed: {e}")
    
    # ==================== PHASE 2: BATCH PROCESSING ====================
    
    def generate_intro(
        self,
        batch_number: int,
        total_batches: int,
        story_context: str,
        upload_date: Optional[str] = None,
        previous_batch_summary: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate intro for a video batch
        
        Args:
            batch_number: Current batch (1, 2, 3, ...)
            total_batches: Total number of batches
            story_context: Brief story summary
            upload_date: Optional upload date for context
            previous_batch_summary: Summary of previous batch (for continuation)
            
        Returns:
            Dict with 'intro_text', 'intro_type', 'voice_recommendation'
        """
        from core.gemini_prompts import PROMPT_GENERATE_INTRO_FIRST, PROMPT_GENERATE_INTRO_CONTINUATION
        
        logger.info(f"Generating intro for batch {batch_number}/{total_batches}")
        
        # Get settings
        intro_settings = self.config.get('intro_settings', {})
        channel_name = intro_settings.get('channel_name', 'Fanfiction Legend')
        max_length = intro_settings.get('max_length_seconds', 30)
        
        # Choose prompt based on batch number
        if batch_number == 1:
            prompt_template = PROMPT_GENERATE_INTRO_FIRST
            prompt = prompt_template.format(
                channel_name=channel_name,
                story_context=story_context,
                upload_date=upload_date or datetime.now().strftime('%B %Y'),
                max_length_seconds=max_length
            )
        else:
            prompt_template = PROMPT_GENERATE_INTRO_CONTINUATION
            start_chapter = (batch_number - 1) * 20 + 1
            end_chapter = batch_number * 20
            
            prompt = prompt_template.format(
                channel_name=channel_name,
                batch_number=batch_number,
                start_chapter=start_chapter,
                end_chapter=end_chapter,
                story_context=story_context,
                previous_summary=previous_batch_summary or "The story has begun...",
                max_length_seconds=max_length
            )
        
        try:
            response = self._make_request(prompt, json_mode=True)
            result = self._parse_json_response(response)
            
            # Add voice recommendation
            if intro_settings.get('use_chatterbox', True):
                result['voice_recommendation'] = 'chatterbox'
            else:
                result['voice_recommendation'] = 'piper_narrator'
            
            logger.info(f"Intro generated: {len(result.get('intro_text', ''))} characters")
            return result
            
        except Exception as e:
            logger.error(f"Intro generation failed: {e}")
            # Fallback to default
            if batch_number == 1:
                return {
                    'intro_text': CONFIG['branding']['intro'],
                    'intro_type': 'first',
                    'voice_recommendation': 'chatterbox'
                }
            else:
                return {
                    'intro_text': f"Welcome back to part {batch_number}! If you haven't watched the previous parts, check the playlist below.",
                    'intro_type': 'continuation',
                    'voice_recommendation': 'chatterbox'
                }
    
    def _chunk_text(self, text: str, max_chars: int = 4000) -> List[str]:
        """
        Split text into chunks respecting paragraph boundaries
        
        Args:
            text: Text to split
            max_chars: Maximum characters per chunk
            
        Returns:
            List of text chunks
        """
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para_len = len(para)
            if current_length + para_len + 2 > max_chars:
                # Chunk is full, save it
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_length = 0
                
                # If single paragraph is too huge, hard split it (rare)
                if para_len > max_chars:
                    for i in range(0, para_len, max_chars):
                        chunks.append(para[i:i + max_chars])
                else:
                    current_chunk.append(para)
                    current_length += para_len + 2
            else:
                current_chunk.append(para)
                current_length += para_len + 2
                
        # Append last chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            
        return chunks

    def analyze_tts_segments(
        self,
        chapter_text: str,
        chapter_number: int,
        character_list: List[Dict],
        chatterbox_used_count: int = 0
    ) -> Dict[str, Any]:
        """
        Analyze chapter text and generate TTS segment mapping
        
        Args:
            chapter_text: Full text of the chapter
            chapter_number: Chapter number
            character_list: List of known characters with genders
            chatterbox_used_count: How many times Chatterbox has been used in this batch
            
        Returns:
            Dict with 'segments' list and metadata
        """
        from core.gemini_prompts import PROMPT_ANALYZE_TTS_SEGMENTS
        
        logger.debug(f"Analyzing TTS segments for chapter {chapter_number}")
        
        # Get settings
        tts_rules = self.config.get('tts_switching_rules', {})
        max_chatterbox = tts_rules.get('expressive_moments', {}).get('max_per_batch', 3)
        chatterbox_remaining = max(0, max_chatterbox - chatterbox_used_count)
        
        # Build character reference
        character_ref = "\n".join([
            f"- {char['name']}: {char['gender']}" 
            for char in character_list[:20]  # Limit to top 20 characters
        ])
        
        # Chunk text to avoid token limits
        # Reduced to 2000 to prevent JSON syntax errors and timeouts
        chunks = self._chunk_text(chapter_text, max_chars=2000)
        logger.info(f"Split chapter {chapter_number} into {len(chunks)} chunks for AI analysis")
        
        all_segments = []
        total_chatterbox = 0
        
        try:
            for i, chunk in enumerate(chunks):
                # Calculate remaining allowance for this chunk
                # Distribute allowance across chunks mostly to the first ones if needed, 
                # or just global counter. Since we process sequentially, we just pass remaining.
                current_chatterbox_allowance = max(0, chatterbox_remaining - total_chatterbox)
                
                prompt = PROMPT_ANALYZE_TTS_SEGMENTS.format(
                    chapter_number=f"{chapter_number} (Part {i+1}/{len(chunks)})",
                    chapter_text=chunk,
                    character_reference=character_ref,
                    chatterbox_remaining=current_chatterbox_allowance,
                    narration_voice='piper_narrator',
                    male_voice='piper_male',
                    female_voice='piper_female',
                    expressive_voice='chatterbox'
                )
                
                response = self._make_request(prompt, json_mode=True)
                result = self._parse_json_response(response)
                
                # Validation
                if 'segments' not in result:
                    logger.warning(f"Chunk {i+1} analysis returned no segments")
                    all_segments.append({
                        'text': chunk,
                        'voice': 'piper_narrator',
                        'reasoning': 'fallback - empty chunk response'
                    })
                    continue
                    
                chunk_segments = result['segments']
                chunk_chatterbox = sum(1 for seg in chunk_segments if seg.get('voice') == 'chatterbox')
                
                # Transform segments to match TTSSegment schema
                mapped_segments = []
                for seg in chunk_segments:
                    raw_voice = seg.get('voice', 'piper_narrator').lower()
                    
                    # Default values
                    speaker = "Narrator"
                    gender = "Neutral"
                    engine = "piper"
                    emotion = "Normal"
                    
                    # Logic to map voice to schema fields
                    if 'narrator' in raw_voice:
                        speaker = "Narrator"
                        gender = "Neutral"
                        engine = "piper"
                    elif 'male' in raw_voice and 'female' not in raw_voice:
                        speaker = "Male Character"
                        gender = "Male"
                        engine = "piper"
                    elif 'female' in raw_voice:
                        speaker = "Female Character"
                        gender = "Female"
                        engine = "piper"
                    elif 'chatterbox' in raw_voice or 'expressive' in raw_voice:
                        speaker = "Expressive"
                        gender = "Neutral" # Or infer from text? Hard to say.
                        engine = "chatterbox"
                        emotion = "Expressive"
                    
                    # Map to schema
                    mapped_segments.append({
                        "text": seg.get('text', ''),
                        "speaker": speaker,
                        "gender": gender,
                        "emotion": emotion,
                        "suggested_engine": engine,
                        "voice_id": raw_voice # Keep track of original selection
                    })
                
                all_segments.extend(mapped_segments)
                total_chatterbox += chunk_chatterbox
                
                # Small delay to be nice to API limits if valid
                if i < len(chunks) - 1:
                    time.sleep(1)

            logger.info(f"Generated {len(all_segments)} total segments (Chatterbox: {total_chatterbox})")
            
            return {
                'segments': all_segments,
                'chatterbox_usage': total_chatterbox
            }
            
        except Exception as e:
            logger.error(f"TTS segment analysis failed: {e}")
            # Fallback: return single segment with default voice
            return {
                'segments': [{
                    'text': chapter_text,
                    'voice': 'piper_narrator',
                    'reasoning': 'fallback - analysis failed'
                }],
                'chatterbox_usage': 0
            }
    
    # ==================== UTILITY METHODS ====================
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        return {
            'total_requests': self.request_count,
            'total_tokens': self.total_tokens_used,
            'estimated_cost_usd': round(self.total_cost_usd, 4),
            'average_tokens_per_request': (
                round(self.total_tokens_used / self.request_count) 
                if self.request_count > 0 else 0
            )
        }
    
    def check_budget(self) -> Tuple[bool, str]:
        """
        Check if within budget limits
        
        Returns:
            (within_budget, message)
        """
        cost_settings = self.config.get('cost_settings', {})
        monthly_budget = cost_settings.get('monthly_budget_usd', 50.0)
        warn_threshold = cost_settings.get('warn_threshold_usd', 5.0)
        
        if self.total_cost_usd >= monthly_budget:
            return False, f"Monthly budget exceeded: ${self.total_cost_usd:.2f} / ${monthly_budget:.2f}"
        elif self.total_cost_usd >= warn_threshold:
            return True, f"⚠️  Approaching budget limit: ${self.total_cost_usd:.2f} / ${monthly_budget:.2f}"
        else:
            return True, f"Within budget: ${self.total_cost_usd:.2f} / ${monthly_budget:.2f}"
    
    def reset_usage_stats(self):
        """Reset usage statistics (e.g., at start of new month)"""
        self.total_tokens_used = 0
        self.total_cost_usd = 0.0
        self.request_count = 0
        logger.info("Usage statistics reset")


# Global cache to avoid recreating client (keeps usage stats)
_cached_gemini_client = None

def create_gemini_client(api_key: Optional[str] = None) -> Optional[GeminiClient]:
    """
    Create or retrieve cached Gemini client if enabled in config
    """
    global _cached_gemini_client
    
    config = CONFIG.get('gemini_settings', {})
    
    if not config.get('enabled', False):
        return None
    
    if not GEMINI_AVAILABLE:
        return None
    
    # Return cached if exists and no API key override provided
    if _cached_gemini_client and not api_key:
        return _cached_gemini_client
        
    try:
        client = GeminiClient(api_key)
        
        # Only cache if it's the default config-based client
        if not api_key:
            _cached_gemini_client = client
            
        return client
    except GeminiClientError as e:
        logger.error(f"Failed to create Gemini client: {e}")
        return None


def test_gemini_connection(api_key: Optional[str] = None) -> bool:
    """
    Test Gemini API connection
    
    Args:
        api_key: Optional API key to test
        
    Returns:
        True if connection successful
    """
    try:
        client = GeminiClient(api_key)
        response = client._make_request("Say 'hello' in one word.")
        return len(response) > 0
    except Exception as e:
        logger.error(f"Gemini connection test failed: {e}")
        return False
