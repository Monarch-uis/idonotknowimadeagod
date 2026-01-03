#!/bin/bash

# Clean Cache and Run from Source (Linux)

echo
echo "===================================="
echo "  Clean Cache and Run from Source"
echo "===================================="
echo

# Ensure script directory is current working directory
cd "$(dirname "$0")/.."

# Step 1: Clean Python bytecode cache
echo "[1/4] Cleaning Python bytecode cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
echo "      OK Cache cleaned"

echo

# Step 2: Clean build artifacts
echo "[2/4] Cleaning build artifacts..."
[ -d "build" ] && rm -rf build
[ -d "dist" ] && rm -rf dist
echo "      OK Build artifacts cleaned"

echo

# Step 3: Verify source file exists
echo "[3/4] Verifying source file..."
if [ ! -f "epub_project_manager.py" ]; then
    echo "      ERROR: epub_project_manager.py not found!"
    read -p "Press Enter to exit..."
    exit 1
fi
echo "      OK Source file found"

echo

# Step 4: Run from source with cache prevention
echo "[4/4] Launching from source..."
echo
echo "===================================="
echo "  Running epub_project_manager.py"
echo "  Mode: SOURCE (no cache)"
echo "===================================="
echo

# Prevent bytecode cache
export PYTHONDONTWRITEBYTECODE=1

# Run from source
python3 -B epub_project_manager.py

echo
echo "===================================="
echo "  Execution Complete"
echo "===================================="
read -p "Press Enter to continue..."
