# 📚 EPUB to Audiobook & Video Converter

> Automatically convert EPUB novels into high-quality audiobooks and YouTube-ready videos with subtitles, background music, and multi-speaker narration — powered by Piper TTS.

---

## ✨ Features

- **🎙️ Multi-Engine TTS** — Piper (primary, offline), Edge-TTS, Pyttsx3, Chatterbox, and Kokoro
- **🧠 AI-Powered Processing** — Gemini AI integration for chapter analysis, pronunciation fixes, and content enhancement
- **🎬 Video Generation** — Auto-subtitled MP4 videos with word-level timing via faster-whisper
- **⚡ Parallel TTS** — Concurrent chapter processing to maximize throughput
- **🔄 Auto-Recovery** — Resume interrupted jobs from the last checkpoint automatically
- **📋 Queue Manager** — Background job queue for batch processing multiple EPUBs
- **🗺️ Novel Name Mapper** — Smart filename normalization and mapping for consistent project organization
- **📊 Performance Profiling** — Built-in profiler with HTML reports
- **🔒 Config Validation** — JSON schema validation with descriptive error messages
- **🐳 Docker Support** — Ready-to-run container with all dependencies

---

## 🏗️ Architecture

```
epub_project_manager.py   ← Main orchestrator & CLI entry point
│
├── core/
│   ├── tts.py                ← Multi-engine TTS (Piper-first)
│   ├── tts_chatterbox.py     ← Chatterbox TTS engine
│   ├── parallel_tts.py       ← Concurrent chapter TTS
│   ├── video_pipeline.py     ← Whisper transcription → ASS subtitles → FFmpeg
│   ├── subtitle_generator.py ← Word-level subtitle timing
│   ├── epub_io.py            ← EPUB parsing & project folder setup
│   ├── gemini_client.py      ← Google Gemini AI client
│   ├── gemini_prompts.py     ← AI prompts for text enhancement
│   ├── config.py             ← Config loader & manager
│   ├── config_schema.py      ← JSON schema validation
│   ├── system_validator.py   ← Pre-flight dependency checks
│   ├── profiler.py           ← Performance profiling
│   ├── logging_config.py     ← Structured rotating log setup
│   ├── aligner.py            ← Audio/subtitle alignment
│   ├── path_utils.py         ← Safe path utilities
│   └── ui_manager.py         ← CLI UI components
│
├── features/
│   ├── queue_manager.py      ← Background job queue (file-locked)
│   ├── auto_recovery.py      ← Checkpoint-based crash recovery
│   ├── checkpoint_manager.py ← Save/restore processing state
│   ├── chapter_merger.py     ← Multi-chapter audio merging
│   ├── multispeaker_tts.py   ← Dialogue/narration voice splitting
│   ├── novel_name_mapper.py  ← EPUB filename normalization
│   ├── gemini_processor.py   ← AI text pre-processing pipeline
│   ├── memory_manager.py     ← Runtime memory monitoring
│   └── video_diagnostics.py  ← Video render health checks
│
├── backend/                  ← FastAPI REST API
│   ├── main.py               ← App entry, CORS, routing
│   └── api/
│       ├── projects.py       ← Project CRUD, queue, logs
│       └── tts.py            ← TTS preview endpoint
│
├── captiongod/               ← Caption rendering engine
├── piper/                    ← Piper TTS binary (local, not tracked by git)
├── piper_models/             ← Voice models (local, not tracked by git)
├── _NEW_EPUBS_HERE/          ← Drop EPUBs here to process
└── Novels/                   ← Output organized by status
    ├── Active Novels/
    ├── Archived Novels/
    ├── Nonactive Novels/
    └── Uploaded in Youtube/
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- FFmpeg installed and in `PATH`
- Piper TTS binary in `piper/` (downloaded separately)

### 1. Install Dependencies

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Core dependencies
pip install -r requirements.txt

# Dev dependencies (testing, linting)
pip install -r requirements-dev.txt
```

> **Note (Debian/Ubuntu):** Always use the venv. The system Python rejects direct `pip install` on modern Debian/Ubuntu.

### 2. Validate Setup

```bash
python run.py --validate-config
```

### 3. Run

```bash
# Interactive mode (guided setup)
python epub_project_manager.py

# With enhanced logging and profiling
python run.py

# With debug logging
python run.py --log-level DEBUG

# With performance profiling (saves report to logs/profiling/)
python run.py --profile
```

### 4. Docker

```bash
docker-compose up
```

---

## ⚙️ Configuration

All behavior is controlled via `config.json`. Key sections:

| Section | Controls |
|---|---|
| `audio_settings` | TTS engine, voice, speed, retry logic |
| `video_settings` | Resolution, subtitle style, quality preset |
| `tts_engines` | Per-engine config (Piper model path, Edge-TTS voice, etc.) |
| `banned_words` | Words to censor or replace before TTS |
| `pronunciation_fixes` | Custom phoneme overrides |
| `system` | Worker threads, memory limits, timeouts |
| `recovery_settings` | Checkpoint strategy, stale lock detection |

Validate after editing:
```bash
python run.py --validate-config
```

---

## 🎙️ TTS Engines

| Engine | Type | Quality | Notes |
|---|---|---|---|
| **Piper** | Offline | ⭐⭐⭐⭐⭐ | Primary engine. Fast, local, no API needed |
| **Edge-TTS** | Online | ⭐⭐⭐⭐ | Microsoft Azure voices, requires internet |
| **Chatterbox** | Offline | ⭐⭐⭐⭐ | Emotional, expressive narration |
| **Kokoro** | Offline | ⭐⭐⭐⭐ | High quality, compact model |
| **Pyttsx3** | Offline | ⭐⭐ | Fallback, uses system voices |

Piper is the primary focus. Models are stored in `piper_models/` and are not committed to Git (too large).

---

## 📦 Backend API

A FastAPI backend is available for programmatic control:

```bash
# Start the API server
uvicorn backend.main:app --reload
```

### Key Endpoints

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/projects` | List all projects |
| `POST` | `/api/projects` | Upload EPUB, create project |
| `GET` | `/api/projects/{id}` | Get project status |
| `POST` | `/api/projects/{id}/queue` | Add project to processing queue |
| `GET` | `/api/projects/{id}/logs` | Stream project logs |
| `POST` | `/api/tts/preview` | Preview TTS audio for a text snippet |

---

## 🧪 Testing

```bash
source venv/bin/activate

# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=core --cov=features --cov-report=html

# View HTML coverage report (Linux)
xdg-open htmlcov/index.html
```

---

## 📝 Logs

Logs are organized by component under `logs/` (not tracked by Git):

| Path | Contains |
|---|---|
| `logs/main/` | Main application flow |
| `logs/tts/` | TTS synthesis events |
| `logs/video/` | Video rendering events |
| `logs/errors/` | Errors only, all components |
| `logs/profiling/` | Performance timing reports |

All log files rotate at 10 MB (max 5 backups).

---

## 🔒 Security

- Bandit static analysis in CI/CD
- `pip-audit` for CVE scanning on all dependencies
- Dependabot configured for automatic dependency updates
- See [SECURITY.md](SECURITY.md) for the vulnerability reporting policy

---

## 📄 License & Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.
