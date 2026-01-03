#!/bin/bash

# EPUB to Audiobook/Video Converter Launcher (Linux/Mac)

# Ensure script directory is current working directory
cd "$(dirname "$0")"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not found in PATH."
    exit 1
fi

# Check for virtual environment (optional but recommended)
VENV_ACTIVE=false
if [ -f ".venv/bin/activate" ]; then
    echo "📦 Activating virtual environment (.venv)..."
    source .venv/bin/activate
    VENV_ACTIVE=true
elif [ -f "venv/bin/activate" ]; then
    echo "📦 Activating virtual environment (venv)..."
    source venv/bin/activate
    VENV_ACTIVE=true
fi

# Check requirements
echo "🔍 Checking dependencies..."
# Added better-ffmpeg-progress and rich for the new UI
python3 -m pip install --break-system-packages --user -r requirements.txt better-ffmpeg-progress rich --quiet

# Run the project manager
echo "🚀 Starting EPUB Project Manager..."
python3 epub_project_manager.py "$@"
