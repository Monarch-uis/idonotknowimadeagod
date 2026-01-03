#!/bin/bash

# EPUB AUTOMATION - POST-FIX SETUP (Linux)

echo "================================================"
echo " EPUB AUTOMATION - POST-FIX SETUP"
echo "================================================"
echo

cd "$(dirname "$0")/.."

echo "[1/3] Installing psutil (for RAM monitoring)..."
python3 -m pip install --break-system-packages --user psutil
echo

echo "[2/3] Verifying improvements..."
python3 -c "import psutil; print('  ✅ psutil installed successfully')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "   ⚠️  psutil installation failed - RAM monitoring will be disabled"
    echo "   Script will still work, just without RAM warnings"
else
    echo "   ✅ RAM monitoring ready!"
fi
echo

echo "[3/3] Testing script imports..."
python3 -c "import ebooklib, edge_tts, moviepy, PIL; print('  ✅ All dependencies OK')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "   ⚠️  Some dependencies missing"
    echo "   Run: python3 -m pip install --break-system-packages --user ebooklib edge-tts moviepy pillow beautifulsoup4"
fi
echo

echo "================================================"
echo " SETUP COMPLETE!"
echo "================================================"
echo
echo "📖 Read IMPROVEMENTS_APPLIED.md for details"
echo "🚀 Run: python3 epub_project_manager.py"
echo
read -p "Press Enter to continue..."
