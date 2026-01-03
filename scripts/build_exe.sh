#!/bin/bash

# Build executable using PyInstaller (Linux)

echo "Building EPUB Project Manager executable..."
echo

# Ensure script directory is current working directory
cd "$(dirname "$0")"

# Check if PyInstaller is installed
if ! python3 -m pip show pyinstaller >/dev/null 2>&1; then
    echo "PyInstaller not found. Installing..."
    python3 -m pip install pyinstaller
fi

# Build the executable
# Note: Using : separator for paths in Linux if needed, but spec file usually handles it.
pyinstaller ../epub_project_manager.spec

if [ $? -ne 0 ]; then
    echo
    echo "Build failed! Check the error messages above."
    read -p "Press Enter to exit..."
    exit 1
fi

echo
echo "Build complete! Executable is in the 'dist' folder."
echo "File: dist/epub_project_manager" # Linux exec usually has no extension or matches name
echo
read -p "Press Enter to continue..."
