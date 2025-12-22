# Contributing to EPUB to Audiobook/Video Converter

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## 🚀 Getting Started

### Prerequisites
- Python 3.9 or higher
- FFmpeg installed and in PATH
- Git
- Virtual environment tool (venv or conda)

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/idonotknowimadeagod.git
cd idonotknowimadeagod

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # Create this file with dev tools

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Verify setup
python run.py --validate-config
pytest tests/ -v
```

## 📋 How to Contribute

### Reporting Bugs
1. Check existing issues first
2. Create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (OS, Python version)
   - Relevant logs from `logs/` directory

### Suggesting Features
1. Open an issue with the "feature request" label
2. Describe the feature and use case
3. Explain why it would be valuable
4. Discuss implementation approaches

### Pull Requests

#### Branch Naming Convention
- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions/fixes

#### Process
1. Fork the repository
2. Create a feature branch
3. Make your changes following the code style
4. Write/update tests
5. Update documentation
6. Commit with clear messages
7. Push to your fork
8. Open a Pull Request

#### PR Checklist
- [ ] Tests pass locally (`pytest tests/ -v`)
- [ ] Code follows project style (black, isort, flake8)
- [ ] Documentation updated if needed
- [ ] Config schema updated if adding new settings
- [ ] Changelog entry added
- [ ] No security vulnerabilities introduced

## 🎨 Code Style

### Python Style Guide
- Follow PEP 8
- Use Black formatter (line length: 120)
- Use isort for import sorting
- Use type hints where appropriate
- Write docstrings for all public functions

### Example:
```python
from typing import Optional, List

def process_chapter(
    text: str,
    chapter_num: int,
    voice: str = "en-US-GuyNeural"
) -> Optional[str]:
    """
    Process a chapter through TTS.
    
    Args:
        text: Chapter text to process
        chapter_num: Chapter number
        voice: TTS voice to use
        
    Returns:
        Path to generated audio file, or None if failed
    """
    # Implementation
    pass
```

### Commit Messages
Follow conventional commits:
```
feat: add support for custom subtitle styles
fix: resolve FFmpeg encoding issue on Windows
docs: update Docker installation guide
refactor: simplify error recovery logic
test: add tests for chapter merging
chore: update dependencies
```

## 🧪 Testing

### Running Tests
```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=core --cov=features --cov-report=html

# Specific test file
pytest tests/test_epub_parsing.py -v

# With profiling
python run.py --profile --validate-config
```

### Writing Tests
- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies (TTS, FFmpeg)

### Test Example:
```python
import pytest
from core.epub_io import parse_full_epub

def test_parse_epub_valid_file(tmp_path):
    """Test parsing a valid EPUB file"""
    # Setup
    epub_path = tmp_path / "test.epub"
    # ... create test EPUB
    
    # Execute
    result = parse_full_epub(str(epub_path))
    
    # Assert
    assert result is not None
    assert "title" in result
    assert len(result["chapters"]) > 0

def test_parse_epub_invalid_file():
    """Test parsing an invalid EPUB file"""
    with pytest.raises(ValueError):
        parse_full_epub("nonexistent.epub")
```

## 📚 Documentation

### Update Documentation When:
- Adding new features
- Changing configuration options
- Modifying CLI arguments
- Adding new TTS engines
- Changing video quality presets

### Documentation Files
- `README.md` - Quick start and overview
- `docs/START_HERE_README.md` - Comprehensive guide
- `docs/DOCKER.md` - Docker-specific docs
- `SECURITY.md` - Security policy
- Inline code comments for complex logic

## 🔐 Security

- Never commit API keys or secrets
- Use environment variables for sensitive data
- Validate all user inputs
- Keep dependencies updated
- Report security issues privately (see SECURITY.md)

## 🏗️ Project Architecture

### Module Organization
```
core/              # Core functionality
├── config.py      # Configuration management
├── epub_io.py     # EPUB parsing and I/O
├── tts.py         # TTS engine integration
├── video_pipeline.py  # Video rendering
└── ...

features/          # Advanced features
├── auto_recovery.py   # Error recovery
├── checkpoint_manager.py  # Progress checkpoints
└── ...

tests/             # Test suite
docs/              # Documentation
```

### Design Principles
1. **Modularity**: Each module has a clear responsibility
2. **Configuration-driven**: Behavior controlled by `config.json`
3. **Resilience**: Graceful error handling and recovery
4. **Extensibility**: Easy to add new TTS engines, video effects
5. **Logging**: Comprehensive logging for debugging

## 🤝 Community

- Be respectful and constructive
- Help others in issues and discussions
- Share your use cases and improvements
- Provide feedback on PRs and features

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

## ❓ Questions?

- Open an issue with the "question" label
- Check existing documentation
- Review closed issues for similar questions

Thank you for contributing! 🎉
