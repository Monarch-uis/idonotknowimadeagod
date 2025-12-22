@echo off
REM Build executable using PyInstaller
REM Make sure PyInstaller is installed: pip install pyinstaller

echo Building EPUB Project Manager executable...
echo.

REM Check if PyInstaller is installed
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    python -m pip install pyinstaller
)

REM Build the executable
pyinstaller ..\epub_project_manager.spec

if errorlevel 1 (
    echo.
    echo Build failed! Check the error messages above.
    pause
    exit /b 1
)

echo.
echo Build complete! Executable is in the 'dist' folder.
echo File: dist\epub_project_manager.exe
echo.
pause

