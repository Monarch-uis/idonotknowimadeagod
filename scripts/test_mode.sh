#!/bin/bash

# Fanfiction Legend Manager - TEST MODE (Linux)

# Ensure script directory is project root
cd "$(dirname "$0")/.."

# ANSI Colors
RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
BLUE='\033[96m'
MAGENTA='\033[95m'
WHITE='\033[97m'
RESET='\033[0m'

clear

# Test Mode Banner
echo
echo -e "${YELLOW}========================================================${RESET}"
echo -e "${MAGENTA}      ______    __  ______  _______  __  __________${RESET}"
echo -e "${MAGENTA}     / __/  |  /  |/  /  |/  / _  |/  |/  /  _/  _/${RESET}"
echo -e "${MAGENTA}    / _/ / /__/ /_/ / /_/ / __ / /_/ /_// // /  ${RESET}"
echo -e "${MAGENTA}   /___/____/_/  /_/_/  /_/_/ |/_/  /_/___/___/   ${RESET}"
echo
echo -e "${RED}            FANFICTION LEGEND AUTOMATION${RESET}"
echo -e "${YELLOW}                  *** TEST MODE ***${RESET}"
echo -e "${YELLOW}========================================================${RESET}"
echo
echo -e "${GREEN}  This is TEST MODE - No permanent data will be saved!${RESET}"
echo -e "${GREEN}  All history and outputs go to temporary folders.${RESET}"
echo -e "${GREEN}  Perfect for testing without cluttering your workspace.${RESET}"
echo -e "${YELLOW}========================================================${RESET}"
echo

# System Checks

# 1. Check Python
echo -e "${BLUE}[$(date +%T)] ${WHITE}Checking Python System...${RESET}"
if ! command -v python3 &> /dev/null; then
    echo
    echo -e "${RED}[CRITICAL ERROR] Python is not found!${RESET}"
    echo -e "${YELLOW}Please install Python 3.${RESET}"
    read -p "Press Enter to exit..."
    exit 1
fi

# 2. Create Folders
if [ ! -d "_NEW_EPUBS_HERE" ]; then
    echo -e "${BLUE}[$(date +%T)] ${YELLOW}Creating Input Zone...${RESET}"
    mkdir "_NEW_EPUBS_HERE"
fi

# 3. Check Script File
if [ ! -f "epub_project_manager.py" ]; then
    echo
    echo -e "${RED}[ERROR] Script file missing!${RESET}"
    echo -e "${WHITE}Could not find: ${YELLOW}epub_project_manager.py${RESET}"
    read -p "Press Enter to exit..."
    exit 1
fi

# 4. Install Requirements
echo -e "${BLUE}[$(date +%T)] ${MAGENTA}Verifying Libraries (Silent)...${RESET}"
python3 -m pip install --break-system-packages --user -r requirements.txt better-ffmpeg-progress rich >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}[WARNING] Library install had issues. Trying to run anyway...${RESET}"
else
    echo -e "${BLUE}[$(date +%T)] ${GREEN}Libraries Verified.${RESET}"
fi

# Launch Sequence
echo
echo -e "${YELLOW}--------------------------------------------------------${RESET}"
echo -e "${GREEN}   READY TO START TEST MODE. LAUNCHING ENGINE...${RESET}"
echo -e "${YELLOW}--------------------------------------------------------${RESET}"
echo

# Setup directories
EPUB_TEST_DIR="_TEST_DATA"
EPUB_HISTORY_DIR="$(pwd)/${EPUB_TEST_DIR}/history"
EPUB_NOVELS_DIR="$(pwd)/${EPUB_TEST_DIR}/novels"

# Clean previous run to ensure fresh test state
if [ -d "${EPUB_TEST_DIR}" ]; then
    echo -e "${YELLOW}Cleaning previous test data...${RESET}"
    rm -rf "${EPUB_TEST_DIR}"
fi

mkdir -p "${EPUB_HISTORY_DIR}"
mkdir -p "${EPUB_NOVELS_DIR}"

echo -e "${BLUE}[$(date +%T)] ${MAGENTA}Starting in Test Mode...${RESET}"
echo -e "${WHITE}Place your real EPUB in: ${YELLOW}_NEW_EPUBS_HERE/${RESET}"

# Run the Python Script
python3 epub_project_manager.py --test-mode --history-dir "${EPUB_HISTORY_DIR}" --novels-dir "${EPUB_NOVELS_DIR}" "$@"

# End State
echo
echo -e "${YELLOW}========================================================${RESET}"
echo -e "${WHITE}   Test Execution Finished.${RESET}"
echo -e "${YELLOW}========================================================${RESET}"
echo

# Ask for cleanup
read -p "  Do you want to delete test data now? (y/n, default n): " CLEANUP
if [[ "$CLEANUP" =~ ^[Yy]$ ]]; then
    echo
    echo -e "${YELLOW}  Cleaning up test data...${RESET}"
    rm -rf "${EPUB_TEST_DIR}"
    if [ -d "${EPUB_TEST_DIR}" ]; then
        echo -e "${RED}  Could not delete test folder (files may be in use)${RESET}"
        echo -e "${YELLOW}  Please delete manually: ${EPUB_TEST_DIR}${RESET}"
    else
        echo -e "${GREEN}  Test data cleaned successfully!${RESET}"
    fi
fi

echo
echo -e "${RED}========================================================${RESET}"
read -p "Press Enter to exit..."
