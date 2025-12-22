# Quick Fix Guide for Piper TTS Path Issue

## The Problem
When using `--voice` with Piper from CLI, Windows backslashes cause path issues.

## Solutions

### Option 1: Use just the model filename (RECOMMENDED)
```bash
python epub_project_manager.py --engine piper --voice en_US-amy-medium.onnx
```

### Option 2: Use forward slashes
```bash
python epub_project_manager.py --engine piper --voice ./piper_models/en_US-amy-medium.onnx
```

### Option 3: Use full absolute path with forward slashes
```bash
python epub_project_manager.py --engine piper --voice "C:/Users/DIBAKAR/Desktop/idonotknowimadeagod/piper_models/en_US-amy-medium.onnx"
```

## Available Models in your piper_models folder:
- en_US-amy-medium.onnx (Female, natural)
- en_US-joe-medium.onnx (Male, deep)
- en_US-lessac-medium.onnx (Male, clear)
- en_US-libritts-high.onnx (High quality, larger file)

## Example Full Command:
```bash
python epub_project_manager.py --engine piper --voice en_US-amy-medium.onnx --range 1-100 --batch-size 20 --speed +0%
```
