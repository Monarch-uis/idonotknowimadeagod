# Project knowledge

EPUB to Audiobook/Video Converter — converts EPUB files into audiobooks and videos with automated TTS, subtitle generation, and content censoring. Targeted at fanfiction/anime content creators on YouTube.

## Quickstart
- Activate venv: `source venv/bin/activate` (required before running any Python commands)
- Setup (fresh clone): `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt -r requirements-dev.txt`
- Dev (backend API): `uvicorn backend.main:app --reload --port 8000`
- Dev (frontend): `cd frontend && npm run dev`
- Run CLI: `python epub_project_manager.py`
- Run via launcher: `./start.sh` (auto-activates venv)
- Run with profiling: `python run.py --profile`
- Validate config: `python run.py --validate-config`
- Test: `pytest tests/ -v`
- Test with coverage: `pytest tests/ --cov=core --cov=features --cov-report=html`
- Lint/format (dev): `black .`, `isort .`, `flake8`, `mypy`
- Frontend build: `cd frontend && tsc -b && vite build`
- Frontend lint: `cd frontend && eslint .`

## Architecture
- Key directories:
  - `core/` — Main processing pipeline: config, TTS, video rendering, subtitles, EPUB I/O, Gemini AI client
  - `features/` — Higher-level features: auto-recovery, chapter merging, checkpoints, queue management, multi-speaker TTS, Gemini processing
  - `backend/` — FastAPI REST API bridging frontend to processing logic
  - `frontend/` — React 19 + Tailwind CSS 4 + Vite + TypeScript UI
  - `piper/` & `piper_models/` — Local neural TTS engine binaries and voice models
  - `conductor/` — Project planning docs (product vision, tech stack, workflow)
  - `docs/` — Extended documentation and guides
- Data flow: EPUB → parse (ebooklib/bs4) → text cleanup/censoring → TTS (edge-tts/piper/pyttsx3/chatterbox) → audio → faster-whisper transcription → subtitle generation → video composition (moviepy/ffmpeg) → output
- Config loaded from `config.json`, validated against schema in `core/config_schema.py`, defaults in `core/config.py`
- EPUBs go in `_NEW_EPUBS_HERE/`, output goes to `Novels/Active Novels/`
- History stored in `~/.epub_project_history/`

## Conventions
- Python 3.10+, typed with TypedDict classes in `core/config.py`
- Formatting: Black, isort; Linting: flake8, pylint, mypy
- Frontend: React 19, Tailwind CSS v4, TypeScript ~5.9, Vite 7, motion (framer-motion)
- Testing: pytest with markers (`slow`, `integration`, `unit`, `requires_ffmpeg`, `requires_network`); fixtures in `conftest.py`
- Frontend testing: vitest + @testing-library/react
- Commit style: conventional commits (`feat(scope):`, `fix(scope):`, `test(scope):`, etc.)
- Config validation uses jsonschema; all settings have safe defaults and bounds-checking
- Pronunciation fixes and banned-word censoring use regex patterns in `config.json`

## Gotchas
- Always activate the venv (`source venv/bin/activate`) before running Python commands — system Python is externally managed (PEP 668) and will reject `pip install` without `--break-system-packages`
- The `start.sh` and other launcher scripts auto-activate the venv, but direct `python3`/`pytest` calls use system Python unless venv is active
- `moviepy<2.0.0` is pinned — do not upgrade to v2
- `Pillow>=11.3.0,<12.0` pinned for gradio compatibility
- `numpy<2.3` pinned for numba compatibility
- `lxml<6.0` pinned for lightnovel-crawler compatibility
- Piper TTS requires local binaries in `piper/` directory (not pip-installable)
- FFmpeg must be installed system-wide for video rendering
- Root `package.json` is minimal (opencode-ai + tailwind); frontend deps are in `frontend/package.json`
- `pytest.ini` sets `testpaths = tests` and `pythonpath = .`
