#!/bin/bash

# Novel Lookup Tool Launcher (Linux/Mac)

# Ensure script directory is current working directory
cd "$(dirname "$0")"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not found in PATH."
    exit 1
fi

# Check for virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the lookup script
echo "Starting lookup tool..."
python3 scripts/lookup_novel.py
