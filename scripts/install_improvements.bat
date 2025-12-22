@echo off
echo ================================================
echo  EPUB AUTOMATION - POST-FIX SETUP
echo ================================================
echo.

echo [1/3] Installing psutil (for RAM monitoring)...
pip install psutil
echo.

echo [2/3] Verifying improvements...
python -c "import psutil; print('  ✅ psutil installed successfully')" 2>nul
if errorlevel 1 (
    echo   ⚠️  psutil installation failed - RAM monitoring will be disabled
    echo   Script will still work, just without RAM warnings
) else (
    echo   ✅ RAM monitoring ready!
)
echo.

echo [3/3] Testing script imports...
python -c "import ebooklib, edge_tts, moviepy, PIL; print('  ✅ All dependencies OK')" 2>nul
if errorlevel 1 (
    echo   ⚠️  Some dependencies missing
    echo   Run: pip install ebooklib edge-tts moviepy pillow beautifulsoup4
)
echo.

echo ================================================
echo  SETUP COMPLETE!
echo ================================================
echo.
echo 📖 Read IMPROVEMENTS_APPLIED.md for details
echo 🚀 Run: python epub_project_manager.py
echo.
pause
