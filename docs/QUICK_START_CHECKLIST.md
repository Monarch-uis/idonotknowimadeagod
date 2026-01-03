# ✅ Gemini Integration - Quick Start Checklist

## 📋 Pre-Flight Checklist (Before You Start)

### 1. Dependencies
- [ ] Python 3.8+ installed
- [ ] Existing project working (can generate videos without AI)
- [ ] FFmpeg installed and in PATH
- [ ] Piper TTS working

### 2. API Setup
- [ ] Visit https://ai.google.dev/
- [ ] Sign in with Google account
- [ ] Click "Get API Key" → Create new key
- [ ] Copy API key (starts with "AI...")
- [ ] Save key somewhere secure

### 3. Piper Voice Models
- [ ] Check which models you have: `ls piper_models/`
- [ ] Download female voice if needed for distinct female characters
- [ ] Note exact model filenames (e.g., `en_US-lessac-medium.onnx`)

---

## 🚀 Installation Steps (15 minutes)

### Step 1: Install New Dependencies
```bash
cd /home/dibakar/Desktop/idonotknowimadeagod

# Install Gemini library
pip install google-generativeai>=0.3.0

# Or use requirements file
pip install -r requirements_gemini.txt
```

- [ ] Command executed successfully
- [ ] No error messages
- [ ] `google-generativeai` appears in `pip list`

### Step 2: Configure API Key

**Option A: Environment Variable (Recommended)**
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export GEMINI_API_KEY="YOUR_KEY_HERE"' >> ~/.bashrc
source ~/.bashrc

# Verify
echo $GEMINI_API_KEY
```

**Option B: Config File**
```bash
# Edit config.json
nano config.json
# Add your key in gemini_settings.api_key
```

- [ ] API key configured
- [ ] Key verified (can echo or see in config)

### Step 3: Update Configuration

```bash
# Backup current config
cp config.json config.json.backup

# Option 1: Use enhanced config template (recommended)
cp config_gemini_enhanced.json config.json

# Option 2: Manually add gemini_settings section
nano config.json
```

**Minimum required in config.json:**
```json
{
    "gemini_settings": {
        "enabled": true,
        "api_key": "YOUR_KEY_OR_LEAVE_EMPTY_IF_USING_ENV_VAR",
        "model": "gemini-2.5-flash"
    }
}
```

- [ ] Config updated
- [ ] `enabled: true`
- [ ] Model set to `gemini-2.5-flash`

### Step 4: Configure Piper Voices

In `config.json`, update `audio_settings.piper_voices`:

```json
{
    "audio_settings": {
        "piper_voices": {
            "narrator": {
                "model": "en_US-lessac-medium.onnx"
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

- [ ] Voice models configured
- [ ] Model files exist in `piper_models/`
- [ ] Female voice available (or set to same as male if not)

---

## 🧪 Testing (10 minutes)

### Test 1: API Connection

```bash
python -c "
from core.gemini_client import test_gemini_connection
print('✅ Success!' if test_gemini_connection() else '❌ Failed')
"
```

**Expected Output:**
```
✅ Gemini API connection successful!
✅ Success!
```

- [ ] Connection test passed
- [ ] No error messages

### Test 2: Full Integration Test

```bash
# Run standalone test
python docs/INTEGRATION_EXAMPLES.py
```

**Expected Output:**
```
Testing Gemini connection...
✅ Gemini API connection successful!

Testing Phase 1...
🤖 Analyzing your story with Gemini AI...
✅ Story analysis complete!
Characters found: 2
Title options: 5

Testing Phase 2...
🎬 Processing Batch 1...
✅ Batch 1 processing complete!
Segments generated: 4

✅ All tests passed!
```

- [ ] Phase 1 test passed
- [ ] Phase 2 test passed
- [ ] No errors

### Test 3: Process Small Sample

```bash
# Use a small test EPUB (1-2 chapters)
python epub_project_manager.py
# Select a small EPUB
# Enable Gemini when prompted
```

- [ ] EPUB parsed successfully
- [ ] Gemini analysis completed
- [ ] Title options displayed
- [ ] Batch processed successfully
- [ ] Audio generated

---

## 🎯 First Real Use (30-60 minutes)

### Step 1: Prepare Your EPUB
- [ ] EPUB file ready
- [ ] Place in `_NEW_EPUBS_HERE/` folder
- [ ] Backup existing config (already done above)

### Step 2: Run with Gemini Enabled

```bash
python epub_project_manager.py
```

**What will happen:**

1. **EPUB Selection**
   - [ ] Your EPUB appears in list
   - [ ] Select it

2. **Phase 1: Story Analysis**
   ```
   🤖 Analyzing your story with Gemini AI...
      📖 Title: Your Book Title
      📚 Chapters: 100
      📝 Words: ~150,000
      ⏳ This may take 10-20 seconds...
   ```
   - [ ] Analysis completes (~15 seconds)
   - [ ] Characters found
   - [ ] Description generated

3. **Title Selection**
   ```
   📝 GENERATED TITLE OPTIONS
   1. [MYSTERIOUS] ...
   2. [ACTION] ...
   3. [CLICKBAIT] ...
   4. [EMOTIONAL] ...
   5. [POWER] ...
   6. [CUSTOM] Enter your own
   ```
   - [ ] 5 options displayed
   - [ ] Select one (or enter custom)

4. **Batch Configuration**
   - [ ] Configure batches (20 chapters recommended)
   - [ ] Confirm settings

5. **Phase 2: Batch Processing**
   ```
   🎬 Processing Batch 1 with Gemini...
      📢 Generating intro...
      🎤 Analyzing TTS segments...
   ```
   - [ ] Intro generated
   - [ ] TTS mapping created
   - [ ] Voice distribution shown

6. **Audio Generation**
   ```
   🎤 Generating multi-speaker audio for Chapter 1...
      piper_narrator: 45 segments
      piper_male: 12 segments
      piper_female: 8 segments
      chatterbox: 2 segments
   ```
   - [ ] Multi-speaker audio generating
   - [ ] Progress shown
   - [ ] No errors

7. **Video Generation**
   - [ ] Videos created successfully
   - [ ] Subtitles embedded
   - [ ] Check output folder

### Step 3: Review Results

**Check these files:**

1. `<Novel_Project>/ai_metadata.json`
   - [ ] File exists
   - [ ] Contains story_analysis
   - [ ] Contains phase1_results
   - [ ] Contains phase2_batches

2. `<Novel_Project>/audio/`
   - [ ] Intro audio files
   - [ ] Chapter audio files
   - [ ] Good audio quality

3. `<Novel_Project>/output/`
   - [ ] Video files created
   - [ ] Correct titles
   - [ ] Subtitles working

4. **Cost Check:**
   ```python
   # In Python console
   from features.gemini_processor import GeminiProcessor
   processor = GeminiProcessor("./path/to/project")
   processor.print_summary()
   ```
   - [ ] Cost displayed
   - [ ] Within budget (~$0.30 per EPUB)

---

## 📊 Success Metrics

After your first complete run, verify:

### Quality Checks
- [ ] **Description**: Engaging, SEO-friendly, no spoilers
- [ ] **Title**: Catchy and appropriate
- [ ] **Intro**: Natural, welcoming, correct batch info
- [ ] **Voice Switching**: Characters have distinct voices
- [ ] **Chatterbox Usage**: 2-3 times per batch (not overused)
- [ ] **Subtitles**: Properly synced

### Technical Checks
- [ ] **No errors** in logs
- [ ] **Audio quality** is good
- [ ] **File sizes** are normal
- [ ] **Processing time** acceptable

### Cost Checks
- [ ] **Phase 1 cost**: ~$0.15
- [ ] **Phase 2 cost**: ~$0.15 (all batches)
- [ ] **Total cost**: ~$0.30 per EPUB
- [ ] Within your budget

---

## 🔧 Troubleshooting

### Issue: "No API key found"
**Fix:**
```bash
export GEMINI_API_KEY="your_key_here"
# Or add to config.json
```
- [ ] Issue resolved

### Issue: "google-generativeai not installed"
**Fix:**
```bash
pip install google-generativeai
```
- [ ] Issue resolved

### Issue: "Chatterbox not available"
**Fix:**
- This is normal if you don't have Chatterbox installed
- System will use Piper for all voices
- [ ] Accepted/Resolved

### Issue: Wrong character genders
**Fix:**
1. Open `<project>/ai_metadata.json`
2. Edit `phase1_results.story_analysis.characters`
3. Change gender values
4. Reprocess batch (delete batch cache)
- [ ] Issue resolved

### Issue: Cost too high
**Fix:**
1. Check model in config: should be `gemini-2.5-flash`
2. If using `pro`, switch to `flash`
3. Verify: `processor.client.model_name`
- [ ] Issue resolved

---

## ✅ Final Checklist

Before considering integration complete:

### Documentation
- [ ] Read `docs/GEMINI_INTEGRATION.md`
- [ ] Reviewed `docs/INTEGRATION_EXAMPLES.py`
- [ ] Understood cost structure
- [ ] Know how to troubleshoot

### Testing
- [ ] Connection test passed
- [ ] Integration test passed
- [ ] Processed sample EPUB successfully
- [ ] Processed full EPUB successfully

### Configuration
- [ ] API key configured
- [ ] Gemini enabled
- [ ] Piper voices configured
- [ ] TTS switching rules understood

### Workflow
- [ ] Know how to run Phase 1
- [ ] Know how to select titles
- [ ] Know how to process batches
- [ ] Know how to check costs

### Results
- [ ] Happy with AI-generated descriptions
- [ ] Happy with title options
- [ ] Happy with voice switching
- [ ] Happy with audio quality

---

## 🎉 You're Done!

If all checkboxes are checked, your Gemini integration is:
- ✅ **Installed** correctly
- ✅ **Configured** properly  
- ✅ **Tested** thoroughly
- ✅ **Ready** for production use

**Next Steps:**
1. Process your backlog of EPUBs
2. Monitor costs with `processor.print_summary()`
3. Fine-tune prompts if needed (in `core/gemini_prompts.py`)
4. Adjust Chatterbox limits based on preference

**Need Help?**
- Check `docs/GEMINI_INTEGRATION.md` for detailed guide
- Review error logs in `logs/` directory
- Test with small EPUBs first

---

**Congratulations! Your AI-powered EPUB-to-video system is ready! 🚀**

**Estimated time saved per EPUB:** 2-3 hours (description writing, title creation, voice planning)
**Cost per EPUB:** ~$0.30
**Quality improvement:** Consistent, professional, SEO-optimized content

**Worth it? Absolutely! 💯**
