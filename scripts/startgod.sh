#!/bin/bash

# Fanfiction Legend Manager Launcher (Linux)

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

# Rainbow Banner
echo
echo -e "${RED}========================================================${RESET}"
echo -e "${YELLOW}      ______    __  ______  _______  __  __________${RESET}"
echo -e "${GREEN}     / __/  |  /  |/  /  |/  / _  |/  |/  /  _/  _/${RESET}"
echo -e "${BLUE}    / _/ / /__/ /_/ / /_/ / __ / /_/ /_// // /  ${RESET}"
echo -e "${MAGENTA}   /___/____/_/  /_/_/  /_/_/ |/_/  /_/___/___/   ${RESET}"
echo
echo -e "${RED}            FANFICTION LEGEND AUTOMATION${RESET}"
echo -e "${RED}========================================================${RESET}"
echo

# System Checks

# Check for virtual environment
if [ -f ".venv/bin/activate" ]; then
    echo -e "${BLUE}[$(date +%T)] ${WHITE}Activating virtual environment (.venv)...${RESET}"
    source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    echo -e "${BLUE}[$(date +%T)] ${WHITE}Activating virtual environment (venv)...${RESET}"
    source venv/bin/activate
fi

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
python3 -m pip install --break-system-packages --user -r requirements.txt >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}[WARNING] Library install had issues. Trying to run anyway...${RESET}"
else
    echo -e "${BLUE}[$(date +%T)] ${GREEN}Libraries Verified.${RESET}"
fi

# Launch Sequence
echo
echo -e "${YELLOW}--------------------------------------------------------${RESET}"
echo -e "${GREEN}   READY TO START. LAUNCHING ENGINE...${RESET}"
echo -e "${YELLOW}--------------------------------------------------------${RESET}"
echo

# Run the Python Script
python3 epub_project_manager.py "$@"

# End State
echo
echo -e "${RED}========================================================${RESET}"
echo -e "${WHITE}   Execution Finished.${RESET}"
echo -e "${RED}========================================================${RESET}"
read -p "Press Enter to exit..."
