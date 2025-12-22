@echo off
REM ============================================
REM Clean Cache and Run from Source
REM ============================================
setlocal enabledelayedexpansion
cd /d "%~dp0.."

echo.
echo ====================================
echo   Clean Cache and Run from Source
echo ====================================
echo.

:: Step 1: Clean Python bytecode cache
echo [1/4] Cleaning Python bytecode cache...
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" (
        rd /s /q "%%d" 2>nul
    )
)
del /s /q *.pyc 2>nul
echo       OK Cache cleaned

echo.

:: Step 2: Clean build artifacts
echo [2/4] Cleaning build artifacts...
if exist build rd /s /q build 2>nul
if exist dist rd /s /q dist 2>nul
echo       OK Build artifacts cleaned

echo.

:: Step 3: Verify source file exists
echo [3/4] Verifying source file...
if not exist "epub_project_manager.py" (
    echo       ERROR: epub_project_manager.py not found!
    pause
    exit /b 1
)
echo       OK Source file found

echo.

:: Step 4: Run from source with cache prevention
echo [4/4] Launching from source...
echo.
echo ====================================
echo   Running epub_project_manager.py
echo   Mode: SOURCE (no cache)
echo ====================================
echo.

REM Prevent bytecode cache
set PYTHONDONTWRITEBYTECODE=1

REM Run from source
python -B epub_project_manager.py

echo.
echo ====================================
echo   Execution Complete
echo ====================================
pause
