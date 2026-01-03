#!/bin/bash

# Fanfiction Legend - Standalone Worker Launcher
# Processes jobs from the queue sequentially.

# Ensure script directory is project root
cd "$(dirname "$0")"

# UI Colors
BLUE='\033[94m'
CYAN='\033[96m'
WHITE='\033[97m'
RESET='\033[0m'

clear
echo -e "${BLUE}========================================================${RESET}"
echo -e "${BLUE}             ⚙️ STANDALONE WORKER LAUNCHER${RESET}"
echo -e "${BLUE}========================================================${RESET}"
echo -e "${WHITE}   Processing tasks from processing_queue.json...${RESET}"
echo -e "${BLUE}========================================================${RESET}"
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

# Run the project in worker mode
python3 epub_project_manager.py --worker "$@"

echo
echo -e "${BLUE}--------------------------------------------------------${RESET}"
echo -e "${WHITE}   Worker Finished.${RESET}"
echo -e "${BLUE}--------------------------------------------------------${RESET}"
read -n 1 -s -r -p "Press any key to exit..."
echo
