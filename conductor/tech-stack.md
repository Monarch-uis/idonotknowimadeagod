# Technology Stack

## Core Language & Runtime
- **Python 3.10+**: The backbone of the processing pipeline, chosen for its extensive multimedia and AI library ecosystem.
- **Docker & Docker Compose**: For consistent environment reproduction, simplified dependency management (especially for FFmpeg and TTS engines), and secure, non-root execution.

## Multimedia Processing
- **MoviePy & FFmpeg-python**: The primary engine for video composition, blurring effects, and audio-video muxing.
- **FFmpeg**: The underlying binary used for high-performance rendering and audio manipulation.
- **Pillow**: Used for image processing, including thumbnail manipulation and background preparation.

## AI & Speech Synthesis
- **faster-whisper**: Leverages CTranslate2 for ultra-fast, word-level speech-to-text transcription to ensure pixel-perfect subtitle synchronization.
- **Piper**: High-quality, local, neural TTS for private and offline synthesis.
- **Edge-TTS**: Provides natural-sounding, cloud-based Microsoft Azure voices.
- **Pyttsx3**: Fallback engine for cross-platform, offline SAPI5/NSSpeech/espeak synthesis.

## Data & Parsing
- **Ebooklib & BeautifulSoup4**: Used for structured extraction of text, images, and metadata from EPUB files.
- **lxml**: High-performance XML/HTML parser for ebook content processing.
- **jsonschema**: Validates project configurations and ensures data integrity.

## Web & GUI (Planned)
- **Frontend**: React.js with Tailwind CSS (Brutalist theme) for the modern, high-impact user interface.
- **Backend API**: Python-based (FastAPI or Flask) to bridge the UI with the existing processing logic.

## Quality Assurance & Performance
- **Pytest**: Comprehensive testing framework for unit and integration tests.
- **psutil**: Monitors system resource usage (CPU/RAM) during intensive rendering tasks.
- **Watchdog**: Real-time monitoring of file system changes for automated queue processing.
