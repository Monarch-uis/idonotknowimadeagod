# Example EPUB Files

Sample EPUB files for testing and development.

## Overview

This directory contains sample EPUB files of varying complexity:

| File | Chapters | Purpose |
|------|----------|---------|
| `minimal_test.epub` | 2 | Quick tests, CI/CD |
| `medium_test_novel.epub` | 10 | Standard testing |
| `large_epic_novel.epub` | 50 | Stress testing, performance |
| `special_characters_test.epub` | 2 | Edge cases, formatting |

## Generating Samples

### Generate All Samples

```bash
python examples/generate_samples.py
```

### Generate Specific Type

```bash
# Minimal (2 chapters)
python examples/generate_samples.py --type minimal

# Medium (10 chapters)
python examples/generate_samples.py --type medium

# Large (50 chapters)
python examples/generate_samples.py --type large

# Special characters
python examples/generate_samples.py --type special
```

### Using Makefile

```bash
# Generate all samples
make examples

# Or add to your Makefile:
examples:
	python examples/generate_samples.py
```

## Using Sample EPUBs

### Testing

```bash
# Copy to input folder
cp examples/sample_epubs/minimal_test.epub _NEW_EPUBS_HERE/

# Run converter
python epub_project_manager.py
```

### Integration Tests

Sample EPUBs are automatically used in integration tests:

```python
# tests/integration/test_epub_to_audiobook.py
from pathlib import Path

epub_path = Path("examples/sample_epubs/minimal_test.epub")
result = parse_full_epub(str(epub_path))
```

### Benchmarks

```python
# benchmarks/component_benchmarks.py
from core.epub_io import parse_full_epub

# Use medium sample for benchmarking
epub_data = parse_full_epub("examples/sample_epubs/medium_test_novel.epub")
```

## Sample Descriptions

### Minimal Test (2 chapters)
- **Use Case**: Quick smoke tests, CI/CD pipelines
- **Processing Time**: < 30 seconds
- **File Size**: ~5 KB
- **Content**: Basic text, simple structure

### Medium Test Novel (10 chapters)
- **Use Case**: Standard functional testing
- **Processing Time**: 2-5 minutes
- **File Size**: ~25 KB
- **Content**: Realistic chapter length, varied vocabulary

### Large Epic Novel (50 chapters)
- **Use Case**: Performance testing, memory usage
- **Processing Time**: 15-30 minutes
- **File Size**: ~150 KB
- **Content**: Extended narrative, stress test batching

### Special Characters Test (2 chapters)
- **Use Case**: Edge case testing, encoding issues
- **Processing Time**: < 1 minute
- **File Size**: ~8 KB
- **Content**: Special chars, HTML tags, formatting

## Test Scenarios

### Quick Validation
```bash
# Use minimal sample
python epub_project_manager.py
# Select: minimal_test.epub
# Mode: Batch (10)
# Expected: < 1 minute
```

### Standard Testing
```bash
# Use medium sample
python run.py --profile
# Select: medium_test_novel.epub
# Expected: 3-5 minutes
```

### Stress Testing
```bash
# Use large sample
python epub_project_manager.py
# Select: large_epic_novel.epub
# Batch size: 20
# Monitor: Memory usage, processing time
```

### Edge Case Testing
```bash
# Use special characters sample
python epub_project_manager.py
# Select: special_characters_test.epub
# Verify: Proper character handling
```

## Expected Outputs

After processing a sample EPUB, you should see:

```
Novels/
└── [Book-Title]/
    ├── audio/
    │   ├── chapter_001.mp3
    │   ├── chapter_002.mp3
    │   └── final_audiobook.m4b
    ├── video/
    │   ├── chapter_001.mp4
    │   └── final_video.mp4
    └── cache/
        └── progress.json
```

## Customizing Samples

Modify the generator script to create custom samples:

```python
from examples.generate_samples import EPUBGenerator

generator = EPUBGenerator()

# Create custom EPUB
book = epub.EpubBook()
book.set_title('My Custom Test')
# ... add chapters ...
```

## Troubleshooting

**Generator fails:**
```bash
# Install ebooklib if missing
pip install ebooklib
```

**Sample not found:**
```bash
# Generate samples
python examples/generate_samples.py
```

**Permission errors:**
```bash
# Check directory permissions
ls -la examples/sample_epubs/
```

## Contributing

When adding new features, consider:
1. Does it need a new sample EPUB?
2. Update generator script
3. Document in this README
4. Add to integration tests

## License

Sample EPUB files are provided for testing purposes only.
Content is placeholder text - not copyrighted material.
