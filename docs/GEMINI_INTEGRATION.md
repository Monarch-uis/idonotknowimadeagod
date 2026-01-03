# Gemini AI Integration - Complete Guide

## 📋 Overview

This integration adds Google Gemini AI capabilities to automate and enhance your EPUB-to-video conversion process with:

- **Intelligent Story Analysis** - Automatic character detection, key moment identification
- **Dynamic Descriptions & Titles** - AI-generated YouTube-optimized content
- **Multi-Speaker TTS** - Context-aware voice switching (narrator, male, female, expressive)
- **Smart Intros** - Dynamic intros that adapt to each video batch

---

## 🚀 Quick Start

### 1. Installation

```bash
# Install new dependencies
pip install -r requirements_gemini.txt

# Or install manually
pip install google-generativeai>=0.3.0
```

### 2. Get Your API Key

1. Go to https://ai.google.dev/
2. Sign in with your Google account
3. Click "Get API Key"
4. Copy your API key

### 3. Configure

**Option A: Environment Variable (Recommended)**
```bash
export GEMINI_API_KEY="your_api_key_here"
```

**Option B: Config File**
Edit `config.json` and add your API key:
```json
{
    "gemini_settings": {
        "enabled": true,
        "api_key": "your_api_key_here",
        ...
    }
}
```

### 4. Enable Features

You can use the enhanced config template:
```bash
cp config_gemini_enhanced.json config.json
```

Or manually add the `gemini_settings` section to your existing `config.json`.

---

## 🎯 How It Works

### Phase 1: Story Analysis (Once Per EPUB)

When you load a new EPUB, Gemini analyzes the **entire story** (all 100 chapters) to:

1. **Identify Characters** - Names, genders, roles
2. **Find Key Moments** - Epic battles, funny scenes, emotional moments
3. **Generate Description** - Engaging 200-300 word YouTube description
4. **Create Title Options** - 5 different title styles to choose from
5. **Build Character Database** - For use in Phase 2

**Cost:** ~$0.15 per EPUB (with gemini-2.5-flash)
**Time:** 10-20 seconds

**Results saved to:** `<project_folder>/ai_metadata.json`

### Phase 2: Batch Processing (Per 20 Chapters)

For each video batch (20 chapters), Gemini:

1. **Generates Dynamic Intro**
   - First video: Engaging welcome intro
   - Subsequent videos: "Previously on..." + navigation

2. **Analyzes TTS Segments**
   - Identifies narration vs dialogue
   - Assigns appropriate voices:
     - Narrator → `piper_narrator` (default)
     - Male dialogue → `piper_male`
     - Female dialogue → `piper_female`
     - Epic moments → `chatterbox` (max 3 per batch)

**Cost:** ~$0.03 per batch × 5 batches = ~$0.15 per EPUB
**Time:** 5-8 seconds per batch

---

## ⚙️ Configuration Options

### Gemini Settings

```json
{
    "gemini_settings": {
        "enabled": true,
        "api_key": "",
        "model": "gemini-2.5-flash",
        "temperature": 0.7,
        "max_output_tokens": 8192,
        
        "features": {
            "story_analysis": true,
            "auto_description": true,
            "auto_title": true,
            "custom_intros": true,
            "dynamic_tts_switching": true,
            "character_tracking": true
        }
    }
}
```

### TTS Voice Mapping

Configure your Piper voices in `audio_settings`:

```json
{
    "audio_settings": {
        "piper_voices": {
            "narrator": {
                "model": "en_US-lessac-medium.onnx",
                "description": "Main narrator voice"
            },
            "male": {
                "model": "en_US-lessac-medium.onnx",
                "speaker_id": 0
            },
            "female": {
                "model": "en_US-amy-medium.onnx",
                "speaker_id": 0
            }
        }
    }
}
```

**Note:** You'll need to download female voice models separately if you want distinct female voices.

### TTS Switching Rules

```json
{
    "tts_switching_rules": {
        "narration_engine": "piper",
        "narration_voice": "narrator",
        "expressive_moments": {
            "engine": "chatterbox",
            "enabled": true,
            "max_per_batch": 3,
            "triggers": {
                "epic_action": true,
                "intense_emotion": true,
                "laughter": true,
                "dramatic_revelation": true
            }
        }
    }
}
```

---

## 💻 Usage Examples

### Example 1: Basic Workflow

```python
from features.gemini_processor import GeminiProcessor, interactive_title_selection
from core.epub_io import parse_full_epub

# 1. Parse EPUB
chapters, metadata = parse_full_epub("my_novel.epub")

# 2. Create processor
processor = GeminiProcessor(project_path="./Novels/My Novel")

# 3. Phase 1: Analyze story
full_text = "\n\n".join([ch['content'] for ch in chapters])
results = processor.analyze_story(full_text, metadata)

# 4. Select title interactively
selected_title = interactive_title_selection(processor)

# 5. Get description
description = processor.get_description()

# 6. Phase 2: Process first batch
batch_chapters = [ch['content'] for ch in chapters[0:20]]
batch_results = processor.process_batch(
    batch_number=1,
    batch_chapters=batch_chapters,
    upload_date="January 2025"
)

# 7. Generate audio with multi-speaker TTS
from features.multispeaker_tts import gen_multispeaker_chapter

for chapter_data in batch_results['chapters']:
    success, error, subs = gen_multispeaker_chapter(
        segments=chapter_data['segments'],
        output_path=f"audio/chapter_{chapter_data['chapter_number']}.wav",
        temp_dir="temp/segments",
        chapter_number=chapter_data['chapter_number']
    )
```

### Example 2: Manual Control

```python
# Use Gemini for analysis only, manual TTS
processor = GeminiProcessor(project_path="./project")
results = processor.analyze_story(full_text, metadata)

# Get insights
characters = results['story_analysis']['characters']
key_moments = results['story_analysis']['key_moments']

# Use your own TTS logic
# ... your custom code ...
```

### Example 3: Skip Analysis (Use Cached)

```python
# If ai_metadata.json exists, it will be loaded automatically
processor = GeminiProcessor(project_path="./project")

if processor.story_analyzed:
    print("Using cached analysis!")
    description = processor.get_description()
else:
    # Run analysis
    results = processor.analyze_story(full_text, metadata)
```

---

## 📊 Cost Breakdown

### Model: gemini-2.5-flash (Recommended)

| Task | Tokens | Cost |
|------|--------|------|
| Phase 1 (100 chapters) | ~200,000 | $0.15 |
| Phase 2 (per batch) | ~40,000 | $0.03 |
| **Total per EPUB** | ~400,000 | **~$0.30** |

### Model: gemini-2.5-pro (Not Recommended)

| Task | Tokens | Cost |
|------|--------|------|
| Phase 1 (100 chapters) | ~200,000 | $2.25 |
| Phase 2 (per batch) | ~40,000 | $0.45 |
| **Total per EPUB** | ~400,000 | **~$4.50** |

**Recommendation:** Use `gemini-2.5-flash` or `gemini-3-flash` (if available). Flash is 15× cheaper with better performance for this use case!

### Budget Management

Set limits in config:
```json
{
    "cost_settings": {
        "track_usage": true,
        "warn_threshold_usd": 5.0,
        "monthly_budget_usd": 50.0
    }
}
```

---

## 🎤 Multi-Speaker TTS

### How It Works

1. **Gemini analyzes** chapter text
2. **Segments are created** with voice assignments
3. **Each segment is generated** with appropriate TTS engine
4. **Segments are concatenated** with timing adjustments
5. **Subtitles are merged** with correct timestamps

### Voice Selection Logic

```
┌─────────────────────────────────────────┐
│  Text: "He said, 'I'm leaving.'"        │
└──────────────┬──────────────────────────┘
               │
        ┌──────▼──────┐
        │ NARRATION   │ → piper_narrator
        │ "He said,"  │
        └─────────────┘
               │
        ┌──────▼──────┐
        │ MALE VOICE  │ → piper_male
        │ "I'm leaving" │
        └─────────────┘
```

### Chatterbox Usage

Chatterbox is **SLOW but EXPRESSIVE**. Use only for peak moments:

✅ **Use For:**
- Epic battle climaxes
- Emotional breakdowns
- Genuine laughter
- Major plot twists

❌ **Don't Use For:**
- Normal narration
- Simple dialogue
- Minor actions
- Descriptions

**Limit:** Max 3 times per batch (20 chapters) by default

---

## 🔧 Troubleshooting

### Issue: "No API key found"

**Solution:**
```bash
export GEMINI_API_KEY="your_key_here"
```

Or add to config.json:
```json
{"gemini_settings": {"api_key": "your_key_here"}}
```

### Issue: "google-generativeai not installed"

**Solution:**
```bash
pip install google-generativeai
```

### Issue: Analysis fails with "Token limit exceeded"

**Solution:** The code automatically truncates text, but if issues persist:
1. Reduce `max_output_tokens` in config
2. Process fewer chapters at once
3. Split very long chapters

### Issue: Chatterbox segments fail

**Solution:**
- Ensure Chatterbox is properly configured
- Check `chatterbox_enabled: true` in audio_settings
- Fallback to Piper happens automatically

### Issue: Wrong voice assigned to character

**Solution:**
1. Check character analysis in `ai_metadata.json`
2. Gemini may have misidentified gender
3. You can manually edit `ai_metadata.json` to correct character genders
4. Re-run batch processing

---

## 📁 File Structure

```
your_project/
├── config.json                    # Main config (add gemini_settings)
├── config_gemini_enhanced.json   # Enhanced template (NEW)
├── requirements_gemini.txt       # Updated requirements (NEW)
│
├── core/
│   ├── gemini_client.py          # Gemini API client (NEW)
│   ├── gemini_prompts.py         # Prompt templates (NEW)
│   └── tts.py                    # Existing TTS
│
├── features/
│   ├── gemini_processor.py       # High-level orchestration (NEW)
│   └── multispeaker_tts.py       # Multi-speaker TTS (NEW)
│
└── <Novel Project>/
    └── ai_metadata.json          # Cached AI analysis (AUTO-GENERATED)
```

---

## 🎯 Best Practices

### 1. Always Review Generated Content
- Check title options before selecting
- Review description for accuracy
- Verify character genders in metadata

### 2. Cache Everything
- Don't regenerate unless EPUB changes
- Phase 1 results are expensive - reuse them!
- Batch results can be regenerated if needed

### 3. Monitor Costs
```python
stats = processor.client.get_usage_stats()
print(f"Total cost: ${stats['estimated_cost_usd']:.4f}")
```

### 4. Use Appropriate Model
- Development/Testing: `gemini-2.5-flash`
- Production: `gemini-2.5-flash` or `gemini-3-flash`
- Never use Pro unless you need complex reasoning

### 5. Optimize Chatterbox Usage
- Keep max_per_batch low (2-3)
- Only for truly impactful moments
- Balance quality vs. speed

---

## 🔄 Migration Guide

### From Manual to AI-Assisted

**Before:**
```python
# Manual process
chapters = parse_epub("novel.epub")
for ch in chapters:
    audio = generate_tts(ch['content'])
    # ... generate video
```

**After:**
```python
# AI-assisted process
processor = GeminiProcessor(project_path)

# One-time analysis
results = processor.analyze_story(full_text, metadata)
title = interactive_title_selection(processor)

# Per-batch processing
for batch_num in range(1, 6):
    batch_results = processor.process_batch(batch_num, batch_chapters)
    
    # Generate with multi-speaker
    for ch in batch_results['chapters']:
        gen_multispeaker_chapter(ch['segments'], output_path, ...)
```

### Updating Existing Projects

1. Backup existing project folders
2. Install new dependencies
3. Update config.json
4. AI analysis will run on first use
5. Existing chapters can be regenerated with new system

---

## 📚 API Reference

### GeminiClient

```python
from core.gemini_client import GeminiClient

client = GeminiClient(api_key="optional")

# Story analysis
results = client.analyze_full_story(full_text, metadata)

# Intro generation
intro = client.generate_intro(
    batch_number=1,
    total_batches=5,
    story_context="...",
    upload_date="January 2025"
)

# TTS segment analysis
segments = client.analyze_tts_segments(
    chapter_text="...",
    chapter_number=1,
    character_list=[...],
    chatterbox_used_count=0
)

# Usage statistics
stats = client.get_usage_stats()
```

### GeminiProcessor

```python
from features.gemini_processor import GeminiProcessor

processor = GeminiProcessor(project_path="./Novels/MyNovel")

# Phase 1
results = processor.analyze_story(full_text, metadata, force=False)
titles = processor.get_title_options()
description = processor.get_description()
processor.select_title(0)  # Select first option

# Phase 2
batch_results = processor.process_batch(
    batch_number=1,
    batch_chapters=[...],
    upload_date="January 2025"
)

# Utility
processor.print_summary()
processor.clear_metadata()  # Force regeneration
```

### MultiSpeaker TTS

```python
from features.multispeaker_tts import gen_multispeaker_chapter, generate_intro_audio

# Generate chapter with multiple voices
success, error, subs = gen_multispeaker_chapter(
    segments=[{"text": "...", "voice": "piper_narrator"}],
    output_path="audio/chapter1.wav",
    temp_dir="temp/segments",
    chapter_number=1
)

# Generate intro
success, error = generate_intro_audio(
    intro_text="Yo legends! Welcome back...",
    output_path="audio/intro.wav",
    voice_recommendation="chatterbox"
)
```

---

## 🧪 Testing

Run tests:
```bash
# Test Gemini connection
python -c "from core.gemini_client import test_gemini_connection; print(test_gemini_connection())"

# Run full test suite
pytest tests/test_gemini_*.py -v
```

---

## 📝 Changelog

### Version 1.0.0 (Initial Release)
- ✅ Phase 1: Full story analysis
- ✅ Phase 2: Batch processing with TTS segmentation
- ✅ Multi-speaker TTS support
- ✅ Dynamic intro generation
- ✅ Cost tracking and budgeting
- ✅ Metadata caching
- ✅ Error handling and fallbacks

---

## 🤝 Support

If you encounter issues:

1. Check this documentation
2. Review error logs
3. Verify API key is valid
4. Check budget limits
5. Try with `force=True` to regenerate

For bugs or feature requests, check the project repository.

---

## 📄 License

Same as main project.
