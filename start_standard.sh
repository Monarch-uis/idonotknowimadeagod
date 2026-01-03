#!/bin/bash

# Fanfiction Legend Manager - STANDARD START SCRIPT
# This script disables AI features and runs the project manager

# Ensure script directory is project root
cd "$(dirname "$0")"

# ANSI Colors
BLUE='\033[96m'
YELLOW='\033[93m'
RESET='\033[0m'

echo -e "${BLUE}========================================${RESET}"
echo -e "${BLUE}    LAUNCHING IN STANDARD MODE (NO AI)  ${RESET}"
echo -e "${BLUE}========================================${RESET}"

# Check for virtual environment
if [ -f ".venv/bin/activate" ]; then
    echo "📦 Activating virtual environment (.venv)..."
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    echo "📦 Activating virtual environment (venv)..."
    source venv/bin/activate
fi

# 0. Check dependencies
echo "🔍 Checking dependencies..."
python3 -m pip install --break-system-packages --user -r requirements.txt better-ffmpeg-progress rich --quiet

# 1. Modify Config to Disable AI
if [ -f "config.json" ]; then
    echo -e "${YELLOW}Disabling AI in configuration...${RESET}"
    # Use python to safely edit JSON without external deps like jq
    python3 -c "import json; f=open('config.json','r+'); d=json.load(f); d['gemini_settings']['enabled']=False; f.seek(0); json.dump(d, f, indent=4); f.truncate(); f.close()"
else
    echo -e "${YELLOW}config.json not found. Using defaults (AI Disabled).${RESET}"
fi

# 2. Run Python Script
# Passing arguments if any
echo -e "${BLUE}Starting Project Manager...${RESET}"
python3 epub_project_manager.py "$@"
