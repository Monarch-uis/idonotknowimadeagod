#!/bin/bash

# Fanfiction Legend Manager - AI START SCRIPT
# This script enables AI features and runs the project manager

# Ensure script directory is project root
cd "$(dirname "$0")"

# ANSI Colors
GREEN='\033[92m'
YELLOW='\033[93m'
RESET='\033[0m'

echo -e "${GREEN}========================================${RESET}"
echo -e "${GREEN}      LAUNCHING WITH AI ENABLED        ${RESET}"
echo -e "${GREEN}========================================${RESET}"

# 0. Check dependencies
echo "🔍 Checking dependencies..."
PIP_FLAGS="--quiet"
if [ -z "$VIRTUAL_ENV" ]; then
    # Outside venv, add safety flags for PEP 668 systems
    PIP_FLAGS="$PIP_FLAGS --break-system-packages --user"
fi
python3 -m pip install $PIP_FLAGS -r requirements.txt better-ffmpeg-progress rich

# 1. Ensure Config is set for AI
if [ -f "config_gemini_enhanced.json" ]; then
    echo -e "${YELLOW}Loading AI Configuration...${RESET}"
    cp config_gemini_enhanced.json config.json
else
    echo -e "${YELLOW}AI Configuration file not found (config_gemini_enhanced.json).${RESET}"
    echo -e "${YELLOW}Using existing config.json. Make sure 'gemini_settings.enabled' is true.${RESET}"
fi

# 2. Run Python Script
# Passing arguments if any
echo -e "${GREEN}Starting Project Manager...${RESET}"
python3 epub_project_manager.py "$@"
