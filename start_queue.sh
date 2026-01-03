#!/bin/bash

# Fanfiction Legend - Queue Manager Launcher
# Configure multiple books to be processed sequentially.

# Ensure script directory is project root
cd "$(dirname "$0")"

# UI Colors
PURPLE='\033[95m'
CYAN='\033[96m'
WHITE='\033[97m'
RESET='\033[0m'

clear
echo -e "${PURPLE}========================================================${RESET}"
echo -e "${PURPLE}             🎯 QUEUE MANAGER LAUNCHER${RESET}"
echo -e "${PURPLE}========================================================${RESET}"
echo -e "${WHITE}   Add multiple EPUBs to the sequential processing list.${RESET}"
echo -e "${PURPLE}========================================================${RESET}"
# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not found in PATH."
    exit 1
fi

# Check for virtual environment
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
python3 -m pip install --break-system-packages --user -r requirements.txt --quiet

# Run the manager in queue mode
python3 epub_project_manager.py --queue-manager "$@"

echo
echo -e "${PURPLE}--------------------------------------------------------${RESET}"
echo -e "${WHITE}   Queue Manager Session Finished.${RESET}"
echo -e "${PURPLE}--------------------------------------------------------${RESET}"
read -n 1 -s -r -p "Press any key to exit..."
echo
