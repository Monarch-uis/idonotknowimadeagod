"""
Gemini AI Prompt Templates
Contains all prompt templates for story analysis, description generation,
and TTS segment analysis.
"""

# ==================== PHASE 1: FULL STORY ANALYSIS ====================

PROMPT_ANALYZE_FULL_STORY = """You are an expert fanfiction analyst and content creator for YouTube audiobook channels. 
Your task is to analyze a complete fanfiction story and provide comprehensive metadata.

**STORY INFORMATION:**
- Title: {book_title}
- Total Chapters: {total_chapters}
- Approximate Word Count: {word_count}

**YOUR TASKS:**

1. **CHARACTER ANALYSIS:**
   - Identify ALL major and supporting characters
   - Determine their gender (male/female/other)
   - Classify their role (protagonist/antagonist/supporting)
   - Note any special characteristics (power level, personality traits)

2. **KEY MOMENTS DETECTION:**
   Find and categorize the most engaging moments:
   - **Overpowered/Epic:** Moments where characters display overwhelming power, epic battles, godlike abilities
   - **Funny/Comedy:** Humorous scenes, witty banter, comedic relief
   - **Emotional/Drama:** Intense emotions, character development, dramatic reveals
   - **Romantic:** Relationship development, intimate moments
   - **Plot Twist:** Unexpected revelations, shocking turns

   For each moment type, provide:
   - Chapter numbers where they occur
   - Brief description (1 sentence)
   - Intensity level (low/medium/high)

3. **STORY THEMES:**
   Identify main themes (e.g., power fantasy, friendship, redemption, revenge, romance)

4. **FANFICTION TYPE:**
   Classify the story (e.g., "Naruto AU", "Harry Potter Crossover", "Marvel SI", "Generic Isekai")

5. **TONE ANALYSIS:**
   Overall tone (e.g., "action-comedy", "dark and serious", "lighthearted adventure")

6. **YOUTUBE DESCRIPTION GENERATION:**
   Write an engaging 200-300 word YouTube description that:
   - Hooks viewers immediately (first 2 sentences are critical!)
   - Highlights the BEST moments without major spoilers
   - Mentions power levels, humor, drama as appropriate
   - Uses enthusiastic language that makes people want to listen
   - Includes relevant hashtags at the end
   - SEO-friendly (includes character names, fandom name)
   
   Style: Excited fanfiction reader talking to other fans
   Avoid: Generic descriptions, spoilers, boring summaries

7. **TITLE OPTIONS:**
   Generate 5 different title options in these styles:
   - **Mysterious/Intriguing:** Hints at the story without revealing too much
   - **Action-Packed:** Emphasizes power, battles, epic moments
   - **Clickbait-Honest:** Attention-grabbing but accurate
   - **Emotional/Character:** Focuses on character journey
   - **Power-Fantasy:** Emphasizes MC becoming overpowered/godlike

   Each title should be:
   - 60 characters or less (YouTube title limit)
   - Captivating and shareable
   - Includes character name if recognizable

8. **STORY SUMMARY:**
   Provide a 2-3 sentence summary for use in batch processing context.

**FULL STORY TEXT:**
```
{full_text}
```

**OUTPUT FORMAT:**
Respond ONLY with valid JSON in this exact structure:

{{
    "story_analysis": {{
        "characters": [
            {{
                "name": "Character Name",
                "gender": "male",
                "role": "protagonist",
                "traits": ["overpowered", "smart", "charismatic"]
            }}
        ],
        "key_moments": [
            {{
                "type": "overpowered",
                "chapters": [15, 34, 67],
                "description": "MC unlocks new power and dominates enemies",
                "intensity": "high"
            }}
        ],
        "themes": ["power fantasy", "friendship", "redemption"],
        "fanfiction_type": "Naruto AU",
        "overall_tone": "action-comedy",
        "content_warnings": ["violence", "mild language"]
    }},
    "description": "Full YouTube description here...",
    "title_options": [
        {{
            "style": "mysterious",
            "title": "The Legend No One Expected"
        }},
        {{
            "style": "action",
            "title": "Naruto's Unstoppable Rise to Power!"
        }},
        {{
            "style": "clickbait",
            "title": "They Said He Was Weak... Then THIS Happened"
        }},
        {{
            "style": "emotional",
            "title": "From Outcast to Legend: A Naruto Story"
        }},
        {{
            "style": "power",
            "title": "Overpowered Naruto Dominates EVERYONE!"
        }}
    ],
    "story_summary": "Brief 2-3 sentence summary for context..."
}}

CRITICAL: Output ONLY the JSON. No markdown code blocks, no explanation, no preamble."""

# ==================== PHASE 2: INTRO GENERATION ====================

PROMPT_GENERATE_INTRO_FIRST = """You are a YouTube content creator for "{channel_name}", an audiobook channel focused on fanfiction.

**TASK:** Generate an engaging intro for the FIRST video of a new fanfiction series.

**CONTEXT:**
- Channel: {channel_name}
- Upload Date: {upload_date}
- Story Context: {story_context}
- Maximum Length: {max_length_seconds} seconds (approximately 75-90 words)

**INTRO REQUIREMENTS:**
1. Start with energy - hook viewers immediately
2. Welcome back regular viewers
3. Briefly tease what makes THIS story special (without spoilers)
4. Build excitement and anticipation
5. Encourage engagement (likes, comments, subscribes)
6. Match the channel's "legends" branding and enthusiastic tone

**STYLE GUIDELINES:**
- Energetic and passionate
- Talk TO the audience, not AT them
- Use "we" language (we're in this together)
- Sound like an excited friend recommending a great story
- Keep it natural - avoid corporate/formal language

**OUTPUT FORMAT:**
Respond ONLY with valid JSON:

{{
    "intro_type": "first",
    "intro_text": "Yo legends! Welcome back to Fanfiction Legend! This {upload_date}, we're diving into...",
    "estimated_duration_seconds": 25,
    "tone": "energetic and welcoming"
}}

CRITICAL: The intro_text should be speakable, natural, and enthusiastic. No robotic language!"""

PROMPT_GENERATE_INTRO_CONTINUATION = """You are a YouTube content creator for "{channel_name}", an audiobook channel focused on fanfiction.

**TASK:** Generate an intro for a CONTINUATION video (part {batch_number}) of an ongoing series.

**CONTEXT:**
- Channel: {channel_name}
- Batch Number: {batch_number}
- Chapters in This Video: {start_chapter}-{end_chapter}
- Story Context: {story_context}
- Previous Batch Summary: {previous_summary}
- Maximum Length: {max_length_seconds} seconds (approximately 60-75 words)

**INTRO REQUIREMENTS:**
1. Welcome viewers back
2. Clearly state which chapters this video covers
3. IMPORTANT: Direct new viewers to watch previous parts first (mention playlist)
4. Optionally include a brief "previously on..." recap (1 sentence max)
5. Build anticipation for what's coming in THIS batch
6. Keep energy high

**STYLE GUIDELINES:**
- Brief but impactful
- Clear navigation cues for viewers
- Maintain series continuity
- Sound excited about the story progression

**OUTPUT FORMAT:**
Respond ONLY with valid JSON:

{{
    "intro_type": "continuation",
    "intro_text": "Yo legends! You're jumping into chapters {start_chapter} through {end_chapter}. If you haven't watched Part 1...",
    "estimated_duration_seconds": 20,
    "includes_recap": true,
    "tone": "welcoming but directive"
}}

CRITICAL: Make it clear that new viewers should start from Part 1. This protects your earlier video views!"""

# ==================== PHASE 2: TTS SEGMENT ANALYSIS ====================

PROMPT_ANALYZE_TTS_SEGMENTS = """You are an expert audio producer specializing in multi-voice narration for audiobooks.

**TASK:** Analyze this chapter text and break it into TTS segments with appropriate voice assignments.

**CHAPTER INFO:**
- Chapter Number: {chapter_number}

**AVAILABLE VOICES:**
1. **{narration_voice}** (Piper - Fast, Clear) - Use for: Standard narration, descriptions, scene-setting
2. **{male_voice}** (Piper - Male Voice) - Use for: Male character dialogue
3. **{female_voice}** (Piper - Female Voice) - Use for: Female character dialogue
4. **{expressive_voice}** (Chatterbox - Slow but VERY expressive) - Use for: ONLY the most impactful moments

**KNOWN CHARACTERS:**
{character_reference}

**VOICE ASSIGNMENT RULES:**

1. **NARRATION ({narration_voice}):**
   - All descriptive text
   - Scene descriptions
   - Action descriptions ("He walked to the door")
   - Internal thoughts UNLESS they're emotional

2. **DIALOGUE:**
   - Male characters → {male_voice}
   - Female characters → {female_voice}
   - Include dialogue tags in the narration voice, not the character voice
   - Example: NARRATION: "He said," → MALE_VOICE: "I'm leaving."

3. **{expressive_voice} (SPARINGLY - Max {chatterbox_remaining} times in this chapter):**
   Use ONLY for these situations:
   - Epic battle moments with intense action
   - Dramatic emotional breakdowns (crying, rage)
   - Genuine laughter (not just "he chuckled")
   - Major plot revelations with high emotional impact
   - Death scenes or life-threatening moments
   
   MINIMUM LENGTH: Each {expressive_voice} segment must be at least 50 characters
   CRITICAL: Do NOT overuse! Save it for PEAK moments only.

4. **SEGMENT BOUNDARIES:**
   - Split at natural pauses (paragraphs, dialogue changes)
   - Each segment should be a complete thought
   - Aim for 100-500 characters per segment for smooth audio
   - Don't split mid-sentence unless absolutely necessary

**CHAPTER TEXT:**
```
{chapter_text}
```

**OUTPUT FORMAT:**
Respond ONLY with valid JSON:

{{
    "segments": [
        {{
            "text": "The sun rose over the village, casting golden light across the rooftops.",
            "voice": "{narration_voice}",
            "reasoning": "scene description"
        }},
        {{
            "text": "I'll become the strongest ninja ever!",
            "voice": "{male_voice}",
            "reasoning": "Naruto speaking (male protagonist)"
        }},
        {{
            "text": "Naruto-kun, wait!",
            "voice": "{female_voice}",
            "reasoning": "Hinata speaking (female character)"
        }},
        {{
            "text": "RASENGAN! The massive sphere of chakra exploded on impact, sending shockwaves through the battlefield. His enemies flew backward, utterly defeated.",
            "voice": "{expressive_voice}",
            "reasoning": "epic battle climax - high emotional intensity"
        }}
    ],
    "chatterbox_usage": 1,
    "emotional_peaks": [4],
    "segment_count": 4,
    "notes": "Used Chatterbox once for the major battle moment at segment 4"
}}

**CRITICAL RULES:**
1. If a character's gender is unknown, use {narration_voice}
2. NEVER use {expressive_voice} for minor moments - it's TOO SLOW
3. Keep {narration_voice} and dialogue voices roughly balanced
4. Maintain narrative flow - don't over-segment
5. Dialogue tags stay in narration voice: NARRATION: "she said," → FEMALE: "actual words"

Output ONLY the JSON. No explanation, no markdown blocks."""

# ==================== UTILITY PROMPTS ====================

PROMPT_DETECT_CHARACTERS = """Analyze this text excerpt and identify all characters mentioned, along with their likely gender.

**TEXT:**
```
{text_excerpt}
```

**OUTPUT FORMAT:**
{{
    "characters": [
        {{
            "name": "Character Name",
            "gender": "male/female/unknown",
            "confidence": "high/medium/low",
            "context": "Brief context clue from text"
        }}
    ]
}}

Output ONLY the JSON."""

PROMPT_SUMMARIZE_BATCH = """Summarize what happened in these chapters in 1-2 sentences for use in the next batch's intro.

**CHAPTERS:**
```
{chapter_texts}
```

**OUTPUT:**
A concise 1-2 sentence summary of the main events, suitable for a "previously on..." recap.
Keep it spoiler-light but informative."""

# ==================== SYSTEM INSTRUCTIONS ====================

SYSTEM_INSTRUCTION_STORY_ANALYST = """You are an expert fanfiction analyst with deep knowledge of:
- Popular fandoms (Naruto, Harry Potter, Marvel, DC, Dragon Ball, One Piece, etc.)
- Fanfiction tropes and conventions
- YouTube content optimization
- Audience engagement strategies

You provide detailed, actionable analysis that helps content creators produce engaging audiobook content."""

SYSTEM_INSTRUCTION_AUDIO_PRODUCER = """You are an expert audio producer specializing in multi-voice narration.
You understand:
- Voice performance and emotion
- Audio pacing and rhythm
- When to use different vocal styles
- How to balance cost (processing time) vs. impact

You make smart decisions about voice assignment that create immersive listening experiences."""
