# 🔍 Comprehensive Project Review v2
> **Date:** 2026-02-18 | **Reviewer:** Antigravity AI (Code Reviewer + Architect + Security Auditor + Python Pro)

---

## Executive Summary

| Category | Score | Trend (vs Dec 2025) |
|---|---|---|
| **Code Quality** | 6.5/10 | ⬆️ Improved (modularity) |
| **Architecture** | 5.5/10 | ➡️ Same (God function remains) |
| **Security** | 3/10 | 🔴 **CRITICAL** (API key exposed) |
| **Performance** | 7/10 | ⬆️ Improved (chunking, GPU) |
| **Testing** | 5/10 | ⬆️ Improved (test infra exists) |
| **Documentation** | 6/10 | ⬆️ Improved (docstrings added) |
| **Overall** | 5.5/10 | ⬆️ Slightly Improved |

---

## 🔴 CRITICAL: Security Vulnerabilities

### 1. Hardcoded API Key in Version Control

> [!CAUTION]
> **Severity: CRITICAL** — A live Google Gemini API key is **hardcoded** in `config_gemini_enhanced.json` (line 42) and is **tracked by Git**. This key is exposed to anyone with repository access.

**File:** `config_gemini_enhanced.json`
```json
"api_key": "AIzaSyARJTsFt6-58wsK8l5kBW5qNbJiZSqsvsk",
```

**Impact:**
- Anyone who clones this repo gets your live API key
- If pushed to GitHub, automated bots scan for exposed keys within minutes
- Could lead to unauthorized API usage and billing charges

**Fix (Immediate):**
1. **Rotate the API key** in Google Cloud Console immediately
2. Move the key to a `.env` file or environment variable
3. Add `config_gemini_enhanced.json` to `.gitignore`
4. Run `git filter-branch` or `BFG Repo Cleaner` to remove the key from Git history
5. Use `python-dotenv` to load secrets:
```python
# core/gemini_client.py
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
```

### 2. CORS Wildcard in Backend

**File:** `backend/main.py` (line 12)
```python
allow_origins=["*"],  # Adjust in production
```

**Impact:** Any website can make requests to your API. If the backend is ever exposed publicly, this is a serious vulnerability.

**Fix:** Restrict to your frontend's origin:
```python
allow_origins=["http://localhost:5173", "https://yourdomain.com"],
```

### 3. `shell=True` in Subprocess Call

**File:** `features/memory_manager.py` (line 24)
```python
output = subprocess.check_output(cmd, shell=True).decode().strip()
```

**Impact:** On Windows, if `cmd` contains user-controlled input, this could lead to command injection.

**Fix:** Use a list argument:
```python
output = subprocess.check_output(
    ["wmic", "os", "get", "FreePhysicalMemory", "/Value"],
    text=True
).strip()
```

### 4. Missing `.gitignore` for Config Files

Only `config.local.json` is gitignored. All other config files with potential secrets (`config_gemini_enhanced.json`, `config.json`) are tracked.

---

## 🟠 Architecture Issues

### 1. God Function: `main()` is 1,130 Lines

**File:** `epub_project_manager.py` (lines 2258–3388)

The `main()` function is a **monolithic 1,130-line function** that handles:
- CLI argument parsing
- Menu rendering
- File selection
- EPUB parsing
- TTS configuration
- Audio generation
- Video rendering
- Queue management
- Checkpoint management

**Impact:** Extremely difficult to test, maintain, or extend. Any change risks breaking unrelated functionality.

**Recommendation:** Extract into focused orchestrator functions:
```
main()
├── handle_new_book_flow()
├── handle_resume_flow()
├── handle_queue_flow()
├── handle_settings_flow()
└── handle_mapping_flow()
```

### 2. Recursive `main()` for Menu Navigation

**File:** `epub_project_manager.py` (lines 2385, 2391, 2395)
```python
return main()  # Recursion to main menu
```

**Impact:** Each menu return creates a new stack frame. After hundreds of menu navigations (unlikely but possible in a long session), this causes a `RecursionError`.

**Fix:** Use a `while True` loop:
```python
def main():
    while True:
        choice = show_menu()
        if choice == '6':
            break
        handle_choice(choice)
```

### 3. Main Entry Point is 3,469 Lines

The file `epub_project_manager.py` combines orchestration, audio generation, video creation, image processing, and CLI parsing in a single file. Over 10 functions exceed 100 lines each.

**Recommendation:** Extract into dedicated modules:
- `create_video()` (478 lines) → `core/video_creator.py`
- `run_audio_gen_with_timestamps()` (439 lines) → Already in `core/tts.py` area
- `configure_book_for_queue()` (292 lines) → `features/queue_configurator.py`

---

## 🟡 Code Quality Issues

### 1. Debug Print Statements in Production Code

| File | Line | Content |
|---|---|---|
| `epub_project_manager.py` | 832 | `print(f"🔍 DEBUG: enable_text_overlay = ...")` |
| `epub_project_manager.py` | 1666 | `print(f"\n   🔍 DEBUG: Project folder: ...")` |
| `epub_project_manager.py` | 1667 | `print(f"   🔍 DEBUG: Covers folder: ...")` |

**Fix:** Replace with `logger.debug()` so they're controlled by log level.

### 2. Windows-Only Font Paths

**File:** `epub_project_manager.py` (lines 840-843)
```python
font_path = "C:/Windows/Fonts/arialbd.ttf"
if not os.path.exists(font_path):
    font_path = "C:/Windows/Fonts/arial.ttf"
```

**Impact:** This fails silently on Linux/macOS and falls back to ImageFont.load_default() which looks poor.

**Fix:** Use a cross-platform font discovery function:
```python
def find_system_font():
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
        "C:/Windows/Fonts/arialbd.ttf",  # Windows
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None
```

### 3. Hardcoded Disclaimer Text

**File:** `epub_project_manager.py` (line 392)
```python
disc_text = "Disclaimer. I do not claim ownership of this story..."
```

This should be in `config.json` alongside `intro` and `outro` branding text.

### 4. Duplicate Import Statements

**File:** `epub_project_manager.py`
- `import gc` at line 4, then again at line 764
- `from rich.progress import track` imported at lines 471 and 519

### 5. Missing Type Hints on Main File Functions

Most functions in `epub_project_manager.py` lack type annotations, while `core/` modules have them. This inconsistency makes the main orchestrator harder to understand.

---

## 🟢 Performance Observations

### Strengths
- ✅ **Audio chunking** with configurable concurrency (`max_concurrent_tts`)
- ✅ **Whisper model auto-downgrade** based on available RAM
- ✅ **GPU detection** for CUDA/MPS acceleration
- ✅ **Long audio splitting** (>30min files split into chunks for Whisper)
- ✅ **Memory monitoring** with `MemoryManager` class
- ✅ **Audio crossfade** support for smoother transitions

### Improvement Opportunities
- **Video rendering:** Currently uses `ultrafast` preset by default. Consider adding a "Production" quality preset with `slow` or `veryslow` for final uploads.
- **Whisper model caching:** The model is loaded fresh each time. Consider keeping it cached across batches within the same session.
- **Concurrent Piper TTS:** The parallel Piper block was removed for stability. Consider reintroducing with better error isolation.
- **MoviePy resource leaks:** AudioFileClip objects are opened but only closed in `finally` blocks. Consider using context managers.

---

## 🧪 Testing Assessment

### Current Test Infrastructure
- **25+ test files** found in `tests/`, `tests/integration/`, `tests/api/`, `tests/frontend/`
- Tests cover: imports, config, EPUB parsing, FFmpeg, auto-recovery, novel name mapper, API endpoints, frontend
- Integration tests exist for EPUB-to-audiobook and EPUB-to-video flows
- A `run_integration_tests.py` script exists

### Gaps
- **No CI/CD pipeline detected** (no `.github/workflows/`, no `Makefile` with test targets)
- **No coverage reporting**
- **No mocking of external services** (Gemini API, Edge-TTS, FFmpeg) in unit tests
- **Test runner is subprocess-based** rather than using `pytest` fixtures

### Recommendations
1. Add a `pytest.ini` or `pyproject.toml` with test configuration
2. Add `pytest-cov` for coverage reports
3. Create mocks for external services
4. Add a GitHub Actions workflow for CI

---

## 💡 New Feature Suggestions

### Based on AI Engineer Skill Analysis

1. **AI-Powered Chapter Summarization**
   - Use Gemini to auto-generate chapter summaries for video descriptions
   - Could also generate "Previously on..." recaps for continuation videos

2. **Smart Voice Assignment**
   - Use AI character detection (already partially implemented) to automatically assign different Piper voices to different characters based on gender/personality

3. **Batch Processing Dashboard**
   - The frontend already exists but appears basic. Add real-time progress tracking via WebSocket, processing statistics, and a visual queue manager

4. **Audio Quality Scoring**
   - After TTS generation, use an audio quality model to score clarity and flag chapters that may need regeneration

5. **Pronunciation Dictionary Auto-builder**
   - Use Gemini to automatically detect anime/manga/fantasy names in new EPUBs and suggest pronunciation fixes

### Quick Wins
1. Add a `--dry-run` CLI flag to preview what would happen without processing
2. Add a `config.local.json` override system (partially exists in `.gitignore`)
3. Add elapsed time tracking per chapter for performance benchmarking
4. Add a `--validate` CLI flag that only runs preflight checks

---

## 📊 File Complexity Summary

| File | Lines | Functions | Concern |
|---|---|---|---|
| `epub_project_manager.py` | 3,469 | 28 | 🔴 God file |
| `video_pipeline.py` | 1,031 | 30 | ⚠️ Complex but well-structured |
| `novel_name_mapper.py` | 781 | 28 | ⚠️ Could use pagination |
| `auto_recovery.py` | 710 | 36 | ✅ Well-decomposed |
| `epub_io.py` | 715 | 22 | ✅ Clean module |
| `tts.py` | 581 | 14 | ✅ Clear responsibilities |
| `gemini_client.py` | 602 | 17 | ✅ Good API client |
| `config.py` | 507 | 15 | ✅ Typed config with validation |
| `gemini_processor.py` | 499 | 19 | ✅ Clean orchestration |

---

## ✅ Action Items (Priority Order)

| Priority | Action | Effort |
|---|---|---|
| 🔴 P0 | **Rotate and remove hardcoded API key** | 15 min |
| 🔴 P0 | **Add `.env` file support + update `.gitignore`** | 30 min |
| 🟠 P1 | Remove debug print statements | 5 min |
| 🟠 P1 | Fix recursive `main()` with while loop | 20 min |
| 🟠 P1 | Restrict CORS origins in backend | 5 min |
| 🟠 P1 | Remove `shell=True` from memory_manager | 5 min |
| 🟡 P2 | Add cross-platform font detection | 30 min |
| 🟡 P2 | Move disclaimer to config.json | 5 min |
| 🟡 P2 | Extract `main()` into sub-functions | 2-3 hours |
| 🟡 P2 | Add type hints to main file | 1 hour |
| 🟢 P3 | Add CI/CD pipeline | 1-2 hours |
| 🟢 P3 | Add coverage reporting | 30 min |
| 🟢 P3 | Implement new AI features | Multi-day |

---

*Generated by Antigravity AI using: code-reviewer, architect-review, security-auditor, python-pro, ai-engineer skills*
