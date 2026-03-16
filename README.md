# EPUB to Audiobook/Video Converter - Quick Start

This project converts EPUB files into audiobooks and videos with automated TTS and subtitle generation.

## Quick Start

### Option 1: Direct Run (Original)
```bash
python epub_project_manager.py
```

### Option 2: With Profiling and Logging (New)
```bash
# Basic usage with enhanced logging
python run.py

# Enable performance profiling
python run.py --profile

# Set logging level
python run.py --log-level DEBUG

# Use JSON log format
python run.py --log-format json

# Validate configuration
python run.py --validate-config
```

### Option 3: Docker
```bash
docker-compose up
```

## New Features

### 🐳 Docker Support
- Multi-stage build for minimal image size
- Non-root user for security
- Volume mounts for EPUBs, output, and logs
- See `docs/DOCKER.md` for details

### 📊 Performance Profiling
- HTML reports with timing and memory usage
- Function-level profiling
- Reports saved to `logs/profiling/`

### ✅ Testing Suite
- Pytest with coverage reporting
- Run: `pytest tests/ -v --cov=core --cov=features`

### 🔒 Config Validation
- JSON schema validation
- Detailed error messages
- Validate: `python run.py --validate-config`

### 📝 Structured Logging
- Component-specific log files in `logs/` directory
- Rotating file handlers (10MB max, 5 backups)
- Colored console output

## Installation

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies (optional, for testing/linting)
pip install -r requirements-dev.txt

# Verify installation
python run.py --validate-config
```

> **Note:** Always activate the virtual environment (`source venv/bin/activate`) before running any Python commands. The system Python on modern Debian/Ubuntu is externally managed and will reject direct `pip install` calls.

## Testing

```bash
# Make sure venv is active
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=core --cov=features --cov-report=html

# View coverage report
start htmlcov/index.html  # Windows
open htmlcov/index.html   # Mac
xdg-open htmlcov/index.html  # Linux
```

## Documentation

- **Docker Deployment**: `docs/DOCKER.md`
- **Full Documentation**: `docs/START_HERE_README.md`
- **Project Memory**: `GEMINI.md`

## Log Files

Logs are organized by component:
- `logs/main/app.log` - Main application logs
- `logs/tts/synthesis.log` - TTS-specific logs
- `logs/video/rendering.log` - Video rendering logs
- `logs/errors/errors.log` - Error-only logs
- `logs/profiling/performance.log` - Performance metrics
- `logs/recovery/recovery.log` - Auto-recovery actions

## Configuration

Edit `config.json` to customize:
- TTS settings (voice, speed, retry logic)
- Video quality presets
- Banned words and pronunciation fixes
- System resource limits

Validate your changes:
```bash
python run.py --validate-config
```

## Support

For issues or questions, check the logs in `logs/` directory first.
