# Subagents — EPUB-to-Audiobook/Video

Dispatch these subagents for specialized tasks. Each has specific skills, scope, and responsibilities.

---

## `tts-engineer`

**Role**: TTS engine specialist. Works on `core/tts.py`, `core/tts_chatterbox.py`, `core/parallel_tts.py`, and `core/tts_chatterbox.py`.

**When to dispatch**:
- Adding new TTS engines
- Fixing TTS quality issues (robotic audio, timing errors)
- Optimizing TTS generation speed
- Adding voices or tuning engine parameters
- Debugging edge-tts, Piper, Kokoro, Pocket TTS, or Chatterbox issues

**Skills to load**:
- `voice-ai-engine-development` — TTS architecture patterns
- `python-performance-optimization` — TTS speed tuning
- `systematic-debugging` — Root cause analysis
- `error-handling-patterns` — Retry logic

**Key files**:
- `core/tts.py` (958 lines — multi-engine TTS)
- `core/tts_chatterbox.py`
- `core/parallel_tts.py`
- `config.json` → `audio_settings`

**Constraints**:
- Never hold full audio in memory — stream to disk
- Always use retry logic (7 retries with delay)
- Check library availability at module load
- Set `HF_HUB_OFFLINE=1` for local engines
- Capture timing data for subtitle generation

---

## `video-renderer`

**Role**: Video pipeline specialist. Works on `core/video_pipeline.py`, `captiongod/`, and FFmpeg rendering.

**When to dispatch**:
- Fixing subtitle timing or display issues
- Adding video effects or transitions
- Optimizing FFmpeg encoding speed/quality
- Fixing ASS subtitle generation
- Adding new video quality presets

**Skills to load**:
- `videodb` — Video processing patterns
- `audio-transcriber` — Whisper transcription
- `python-performance-optimization` — Encoding optimization

**Key files**:
- `core/video_pipeline.py` (1031 lines — Whisper, ASS, FFmpeg)
- `captiongod/` (caption rendering engine)
- `config.json` → `video_settings`

**Constraints**:
- FFmpeg commands must use list form (no shell=True)
- Always clean up temp ASS files
- Ensure even dimensions for libx264
- Use responsive scaling for fonts/margins
- Provide Whisper with initial_prompt from EPUB text

---

## `api-developer`

**Role**: FastAPI backend specialist. Works on `backend/` including routes, models, and middleware.

**When to dispatch**:
- Adding new API endpoints
- Fixing API bugs or validation issues
- Adding Pydantic models or OpenAPI schemas
- Configuring CORS, middleware, or static files
- Integrating new features with the React frontend

**Skills to load**:
- `fastapi-pro` — FastAPI patterns
- `python-fastapi-development` — Project-specific API workflow
- `api-patterns` — REST design principles
- `api-endpoint-builder` — Endpoint implementation

**Key files**:
- `backend/main.py` — FastAPI app, CORS, routers
- `backend/api/projects.py` — Project CRUD, queue, logs
- `backend/api/tts.py` — TTS preview endpoint
- `backend/models/project.py` — Pydantic models

**Constraints**:
- Use `sanitize_filename()` on all uploads
- Validate file extensions and sizes
- Return proper HTTP status codes (400, 404, 500)
- Use `CONFIG` from `core/config.py` for settings
- CORS origins via `CORS_ORIGINS` env var

---

## `frontend-developer`

**Role**: React frontend specialist. Works on `frontend/` with TypeScript, Vite, and Tailwind.

**When to dispatch**:
- Adding new UI components or pages
- Fixing frontend bugs or styling issues
- Improving UX (upload flow, progress display)
- Adding form validation or error handling
- Connecting frontend to backend API

**Skills to load**:
- `ui-ux-design` — Project UI/UX patterns
- `ui-ux-pro-max` — General design guidelines

**Key files**:
- `frontend/src/` — React components
- `frontend/src/App.tsx` — Main app
- `frontend/package.json` — Dependencies

**Constraints**:
- TypeScript for all props and state
- Error boundaries for crash protection
- Loading states for async operations
- Accessibility: labels, focus states, 4.5:1 contrast
- Touch targets minimum 44x44px

---

## `queue-manager`

**Role**: Queue processing specialist. Works on `features/queue_manager.py`, worker scripts, and job lifecycle.

**When to dispatch**:
- Fixing queue processing issues (stuck jobs, stale locks)
- Adding new job types or processing stages
- Improving queue reliability or worker management
- Migrating to Redis or Celery

**Skills to load**:
- `workflow-orchestration-patterns` — Queue architecture
- `error-handling-patterns` — Retry and recovery
- `python-patterns` — Background task patterns

**Key files**:
- `features/queue_manager.py` — Queue operations
- `processing_queue.json` — Job data
- `start_worker.sh` — Worker process
- `config.json` → `recovery_settings`

**Constraints**:
- File locking prevents concurrent access — verify fcntl usage
- Stale lock detection and cleanup required
- Write to temp file + rename for atomic updates
- Job status transitions: pending → processing → completed/failed

---

## `epub-parser`

**Role**: EPUB parsing and content extraction specialist. Works on `core/epub_io.py` and EPUB-related logic.

**When to dispatch**:
- Fixing EPUB parsing errors
- Improving text extraction quality
- Adding EPUB metadata handling
- Setting up project folder structures
- Sanitizing EPUB HTML content

**Skills to load**:
- `python-patterns` — Python architecture decisions
- `security-audit` — EPUB injection prevention

**Key files**:
- `core/epub_io.py` — EPUB parsing, project setup
- `core/path_utils.py` — Path utilities

**Constraints**:
- Strip `<script>` tags and event handlers from EPUB HTML
- Validate EPUB structure before parsing
- Sanitize filenames to prevent path traversal
- Create consistent project folder structure

---

## `devops-engineer`

**Role**: Infrastructure and deployment specialist. Works on Docker, CI/CD, shell scripts, and system configuration.

**When to dispatch**:
- Creating or fixing Docker configuration
- Setting up CI/CD pipelines
- Writing shell scripts for startup, backup, health checks
- Configuring system dependencies (FFmpeg, Piper, espeak)
- Setting up monitoring or log rotation

**Skills to load**:
- `devcontainer-setup` — DevContainer configuration
- `cicd-automation-workflow-automate` — CI/CD pipelines
- `linux-shell-scripting` — Shell scripts
- `appdeploy` — Deployment patterns

**Key files**:
- `Dockerfile` — Container definition
- `docker-compose.yml` — Multi-service setup
- `.github/workflows/` — GitHub Actions
- `start*.sh` — Startup scripts
- `requirements.txt`, `requirements-dev.txt`

**Constraints**:
- Docker: non-root user, multi-stage build
- Install FFmpeg and espeak-ng in containers
- Volume mounts for output directories
- Health check endpoint: `GET /api/health`

---

## `qa-engineer`

**Role**: Testing and quality assurance specialist. Writes tests, reviews code, and ensures quality gates.

**When to dispatch**:
- Writing unit or integration tests
- Reviewing code for bugs, security, or performance issues
- Setting up test fixtures or mocking
- Adding coverage reporting
- Before merging significant changes

**Skills to load**:
- `testing-qa` — Testing workflow
- `code-reviewer` — Code review patterns
- `systematic-debugging` — Debug methodology

**Key files**:
- `tests/` — Test suite
- `conftest.py` — Test fixtures
- `pytest.ini` — Test configuration

**Constraints**:
- Mock external services (edge-tts, Whisper, FFmpeg)
- Test happy path + error paths
- Use `pytest.mark.asyncio` for async tests
- Run `pytest tests/ -v --cov=core --cov=features --cov-report=html`

---

## `architect`

**Role**: Software architect for high-level design decisions, refactoring, and technical debt analysis.

**When to dispatch**:
- Making architecture decisions for new features
- Planning refactoring of large modules
- Analyzing technical debt and prioritizing fixes
- Evaluating trade-offs for technology choices
- Planning migration to new architectures

**Skills to load**:
- `architecture` — Decision framework
- `python-patterns` — Architecture principles
- `code-refactoring-tech-debt` — Debt analysis
- `python-development-python-scaffold` — Project structure

**Key files**:
- All `core/` modules
- `config.json` and `core/config_schema.py`
- `GEMINI.md` — Project context
- `conductor/` — Tech stack and workflow docs

**Constraints**:
- Start simple, add complexity only when proven necessary
- Write ADRs for significant decisions
- Consider team expertise when choosing patterns
- Document trade-offs for every decision
