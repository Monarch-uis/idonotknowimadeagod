# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CI/CD pipeline with GitHub Actions
- Pre-commit hooks for code quality
- Security scanning with Bandit and pip-audit
- Comprehensive .gitignore file
- CONTRIBUTING.md guide
- SECURITY.md policy
- Dependabot configuration
- Development requirements file

### Changed
- Updated Pillow to 11.3.0 to fix security vulnerabilities (CVE-2023-50447, CVE-2023-44271)

### Security
- Addressed known CVEs in Pillow dependency
- Added automated security scanning in CI/CD
- Implemented Dependabot for dependency updates

## [1.0.0] - YYYY-MM-DD (Previous work)

### Added
- EPUB to audiobook conversion
- Multiple TTS engine support (Edge-TTS, Pyttsx3, Piper)
- Video generation with subtitles
- Docker support
- Auto-recovery system
- Checkpoint management
- Comprehensive configuration system
- Testing framework
- Logging system
- Documentation

### Features
- Batch processing
- Custom pronunciation fixes
- Word censoring
- Multiple quality presets
- Subtitle generation with timing
- Chapter markers
- Memory monitoring
- Queue management

---

## Types of Changes
- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` for vulnerability fixes
