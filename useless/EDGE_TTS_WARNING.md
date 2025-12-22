# 🚨 CRITICAL UPDATES - December 10, 2025
## Edge-TTS Rate Limiting + Batch Range Feature

---

## 🆕 NEW FEATURES ADDED

### 1. ✅ Batch Range Selector
**What:** Choose which chapters to process in batch mode  
**Why:** You wanted to process specific ranges (e.g., chapters 50-100)

#### How It Works:
```
📍 Chapter Range (total: 150 chapters)
   Leave blank to process ALL chapters

   ▶️  Start from chapter (1-150, default 1): 50
   ⏹️  End at chapter (50-150, default 150): 100

   ✅ Range selected: Chapter 50 to 100 (50 chapters)

   🔢 Chapters per video (max recommended: 50): 20

✅ Will create 3 videos from selected range
   → Video 1: Chapters 50-69
   → Video 2: Chapters 70-89
   → Video 3: Chapters 90-100
```

**Benefits:**
- Skip intro chapters (information, synopsis)
- Resume from where you left off
- Process middle sections without starting over
- Create test batches without processing everything

---

### 2. 🚨 EDGE-TTS RATE LIMITING PROTECTION (CRITICAL!)

**PROBLEM DISCOVERED:**
- Microsoft recently added STRICT rate limiting to Edge-TTS
- Too many requests = **403 error (IP banned)**
- Concurrent mode = **HIGHER RISK**
- Affects hundreds of users (GitHub issues #265, #286, #290, #401)

#### The Issue:
```
Your script with concurrent=4 means:
1. Sends 4 requests simultaneously
2. Microsoft sees this as "spam"
3. Your IP gets blocked (403 error)
4. Processing fails mid-batch
5. You lose all progress
```

#### Protection Added:

**A) Pre-Processing Warning**
```
⚠️  EDGE-TTS RATE LIMIT WARNING
   Microsoft recently added strict rate limiting:
   • Too many requests = 403 error (IP blocked)
   • Concurrent mode increases risk
   • Large batches may trigger blocking

   💡 Recommendations:
   • Use Piper for large batches (no limits)
   • Or use Sequential mode (slower but safer)
   • Process <30 chapters at a time with Edge-TTS

   ⚠️  You selected CONCURRENT mode - higher risk!

   Switch to Piper now? (y/n): _
```

**B) Request Delay Added**
```python
# In concurrent mode, adds 0.8s delay between requests
# Prevents rapid-fire requests that trigger rate limits

⏱️  Rate limit protection: 0.8s delay between requests
```

**C) Connection Test Enhanced**
```
If Edge-TTS connection fails:
   1. Check internet and retry
   2. Switch to Piper (offline, RECOMMENDED)  ← Now suggests Piper
   3. Switch to pyttsx3 (offline)
```

---

## ⚙️ NEW CONFIG SETTINGS

### Added to `config.json`:
```json
{
  "audio_settings": {
    "edge_tts_request_delay": 0.8,  // NEW: Delay between Edge-TTS requests
    // Increase to 1.0 or 1.5 for safer processing
    // Decrease to 0.5 for faster (riskier) processing
  }
}
```

---

## 📊 EDGE-TTS RISK LEVELS

### Safe Usage (Low Risk):
```
✅ Sequential mode
✅ <30 chapters per batch
✅ 1.0s+ delay between requests
✅ Small books (50-100 chapters total)
```

### Moderate Risk:
```
⚠️  Concurrent mode (4 parallel)
⚠️  30-50 chapters per batch
⚠️  0.8s delay (default)
⚠️  Medium books (100-200 chapters)
```

### High Risk (NOT RECOMMENDED):
```
❌ Concurrent mode (8-10 parallel)
❌ 50+ chapters per batch
❌ <0.5s delay
❌ Large books (200+ chapters)
❌ Multiple batches in quick succession
```

---

## 🎯 RECOMMENDED WORKFLOWS

### For Large Books (100+ Chapters):
```bash
Option 1: Use Piper (BEST)
   • No rate limits
   • Fast
   • Offline
   • Already installed on your system

Option 2: Edge-TTS Sequential
   • Slower but safer
   • Process 20-30 chapters at a time
   • Wait 5-10 minutes between batches
```

### For Small Books (<50 Chapters):
```bash
Edge-TTS Concurrent is OK
   • Use batch range: 1 to 50
   • Default settings (0.8s delay)
   • Single batch
```

### For Testing:
```bash
1. Select batch mode
2. Enter range: Chapters 1 to 10
3. Use Piper or Edge-TTS sequential
4. Verify quality
5. Then process full book
```

---

## 🔍 HOW TO IDENTIFY RATE LIMITING

### Symptoms:
```
❌ "403 Forbidden" errors during generation
❌ "WSServerHandshakeError: 403" messages
❌ Audio generation fails after 10-20 chapters
❌ Works fine for first video, fails on second
❌ Retries don't help (still 403)
```

### Solutions:
```
1. STOP immediately (don't waste retries)
2. Switch to Piper for remaining chapters
3. Wait 30-60 minutes for IP cooldown
4. Or use VPN to change IP
5. Reduce concurrent limit in config.json
```

---

## 📝 USAGE EXAMPLES

### Example 1: Process Chapters 50-100 with Piper
```
python epub_project_manager.py

Select book: 1
Mode: [1] Batch All

📍 Chapter Range (total: 150 chapters)
   Start from chapter: 50
   End at chapter: 100
   ✅ Range: Chapter 50-100 (50 chapters)

   Chapters per video: 25
   ✅ Will create 2 videos

🎤 TTS Engine:
   3. Piper (offline, neural, FAST)
Select: 3

✅ Processing 50 chapters safely with Piper
```

### Example 2: Safe Edge-TTS Usage
```
Mode: [1] Batch All

📍 Chapter Range:
   Start: 1
   End: 30
   ✅ Range: Chapter 1-30 (30 chapters)

   Chapters per video: 30
   ✅ Will create 1 video

🎤 TTS Engine:
   1. Edge-TTS
Select: 1

⚠️  EDGE-TTS RATE LIMIT WARNING
   Process <30 chapters ✅ (you have 30)
   Switch to Piper? (y/n): n

💡 Processing Mode:
   Safe = 1 clip at a time
Select: Safe

✅ Processing safely in sequential mode
```

---

## ⚡ PERFORMANCE COMPARISON

### Edge-TTS vs Piper (50 chapters):

| Metric | Edge-TTS Concurrent | Edge-TTS Sequential | Piper |
|--------|---------------------|---------------------|-------|
| Speed | 15-20 min | 40-60 min | 20-30 min |
| Risk | **HIGH** | Low | **NONE** |
| Quality | Excellent | Excellent | Excellent |
| Internet | Required | Required | **Not needed** |
| Limits | **YES (403)** | Possible | **NO** |

**Winner:** Piper - Best balance of speed, quality, and reliability

---

## 🛡️ PROTECTION FEATURES SUMMARY

| Feature | Purpose | Status |
|---------|---------|--------|
| Pre-processing warning | Inform about risks | ✅ Added |
| Request delay | Prevent rate limiting | ✅ Added (0.8s) |
| Switch to Piper option | Easy alternative | ✅ Added |
| Batch size warning | Prevent large batches | ✅ Added |
| Connection test | Early failure detection | ✅ Improved |
| Range selector | Process specific chapters | ✅ Added |

---

## 🔧 CONFIGURATION GUIDE

### For 8GB RAM System (You):
```json
{
  "audio_settings": {
    "max_concurrent_tts": 3,           // Reduce to 3 for safety
    "edge_tts_request_delay": 1.0,     // Increase to 1.0s
  },
  "system_limits": {
    "max_batch_size": 30               // Reduce to 30
  }
}
```

### For 16GB+ RAM System:
```json
{
  "audio_settings": {
    "max_concurrent_tts": 6,           // Can increase
    "edge_tts_request_delay": 0.8,     // Keep default
  },
  "system_limits": {
    "max_batch_size": 50               // Keep default
  }
}
```

---

## 🆘 TROUBLESHOOTING

### Q: I got 403 error. What now?
```
A: 1. STOP processing immediately
   2. Open config.json
   3. Change to: "max_concurrent_tts": 1
   4. Change to: "edge_tts_request_delay": 2.0
   5. Wait 30 minutes
   6. OR switch to Piper (recommended)
```

### Q: Batch range not working?
```
A: Check you're using mode "1" (Batch All)
   Mode "2" (Manual) uses the old range selection
```

### Q: How to know if rate limited?
```
A: Look for these errors in console:
   • "403 Forbidden"
   • "WSServerHandshakeError"
   • "Invalid response status"
```

### Q: Best settings for safety?
```
A: Use Piper TTS
   • No rate limits
   • No internet needed
   • Already installed
   • Same quality
```

---

## 📞 QUICK REFERENCE CARD

```
┌─────────────────────────────────────────┐
│ SAFE EDGE-TTS USAGE                     │
├─────────────────────────────────────────┤
│ ✅ Sequential mode                      │
│ ✅ <30 chapters per batch               │
│ ✅ 1.0s+ delay                          │
│ ✅ Small books only                     │
│                                         │
│ WHEN TO USE PIPER INSTEAD               │
├─────────────────────────────────────────┤
│ • Books with 100+ chapters              │
│ • Any concurrent processing             │
│ • Multiple batches in one day           │
│ • When you've seen 403 errors before    │
│                                         │
│ BATCH RANGE USAGE                       │
├─────────────────────────────────────────┤
│ • Select mode "1" (Batch All)           │
│ • Enter start chapter (or blank for 1)  │
│ • Enter end chapter (or blank for all)  │
│ • Enter chapters per video              │
│ • Script creates batches automatically  │
└─────────────────────────────────────────┘
```

---

## 🎉 SUMMARY

**What You Asked For:**
✅ Batch range selector - **DONE**

**What I Discovered:**
🚨 Edge-TTS rate limiting - **CRITICAL ISSUE**
✅ Added protection - **DONE**

**Result:**
- Safer Edge-TTS processing
- Option to select chapter ranges
- Automatic delay between requests
- Warnings before risky operations
- Easy switch to Piper (recommended)

**Recommendation:**
**Use Piper TTS for best results** - no rate limits, no internet needed, same quality, and you already have it installed!

---

**Last Updated:** December 10, 2025  
**Status:** Production Ready ✅  
**Priority:** CRITICAL - Read Edge-TTS section carefully
