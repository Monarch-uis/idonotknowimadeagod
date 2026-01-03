#!/bin/bash

# Clean PyInstaller Build Artifacts (Linux)

echo
echo "===================================="
echo "  Cleaning Build Artifacts"
echo "===================================="
echo

# Ensure we are in project root (assuming script is in scripts/)
cd "$(dirname "$0")/.."

# Remove build directory
if [ -d "build" ]; then
    echo "Removing build/ directory..."
    rm -rf build
    if [ -d "build" ]; then
        echo "  WARNING: Could not remove build/ - files may be in use"
    else
        echo "  OK Removed build/"
    fi
else
    echo "  OK build/ does not exist"
fi

echo

# Remove dist directory
if [ -d "dist" ]; then
    echo "Removing dist/ directory..."
    rm -rf dist
    if [ -d "dist" ]; then
        echo "  WARNING: Could not remove dist/ - files may be in use"
    else
        echo "  OK Removed dist/"
    fi
else
    echo "  OK dist/ does not exist"
fi

echo
echo "===================================="
echo "  Build Artifacts Cleaned!"
echo "===================================="
echo
echo "PyInstaller build files removed."
echo
read -p "Press Enter to continue..."
