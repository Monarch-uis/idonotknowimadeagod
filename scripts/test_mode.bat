@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0.."
TITLE Fanfiction Legend Manager - TEST MODE

:: ============================================================
::                COLOR CONFIGURATION (ANSI)
:: ============================================================
for /F "tokens=1,2 delims=#" %%a in ('"prompt #$H#$E# & echo on & for %%b in (1) do rem"') do set "ESC=%%b"

set "RED=%ESC%[91m"
set "GREEN=%ESC%[92m"
set "YELLOW=%ESC%[93m"
set "BLUE=%ESC%[96m"
set "MAGENTA=%ESC%[95m"
set "WHITE=%ESC%[97m"
set "RESET=%ESC%[0m"

CLS

:: ============================================================
::                     TEST MODE BANNER
:: ============================================================
echo.
echo  %YELLOW%========================================================%RESET%
echo  %MAGENTA%      ______    __  ______  _______  __  __________
echo  %MAGENTA%     / __/  ^|  /  ^|/  /  ^|/  / _  ^|/  ^|/  /  _/  _/
echo  %MAGENTA%    / _/ / /__/ /^_/ / /^_/ / __ / /^_/ /_// // /  
echo  %MAGENTA%   /___/____/_/  /_/_/  /_/_/ ^|_/_/  /_/___/___/   
echo.
echo  %RED%            FANFICTION LEGEND AUTOMATION%RESET%
echo  %YELLOW%                  *** TEST MODE ***%RESET%
echo  %YELLOW%========================================================%RESET%
echo.
echo  %GREEN%  This is TEST MODE - No permanent data will be saved!%RESET%
echo  %GREEN%  All history and outputs go to temporary folders.%RESET%
echo  %GREEN%  Perfect for testing without cluttering your workspace.%RESET%
echo  %YELLOW%========================================================%RESET%
echo.

:: ============================================================
::                     SYSTEM CHECKS
:: ============================================================

:: 1. CHECK PYTHON
echo  %BLUE%[%time:~0,8%] %WHITE%Checking Python System...%RESET%
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo  %RED%[CRITICAL ERROR] Python is not found!%RESET%
    echo  %YELLOW%Please install Python and check "Add to PATH".%RESET%
    pause
    exit
)

:: 2. CREATE TEST FOLDERS
echo  %BLUE%[%time:~0,8%] %YELLOW%Setting up TEST environment...%RESET%

:: Create test input zone
if not exist "_NEW_EPUBS_HERE" (
    mkdir "_NEW_EPUBS_HERE"
)

:: Create temporary test directories
set "TEST_TIMESTAMP=%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TEST_TIMESTAMP=%TEST_TIMESTAMP: =0%"
set "TEST_DIR=_TEST_DATA_%TEST_TIMESTAMP%"
set "TEST_HISTORY_DIR=%TEST_DIR%\history"
set "TEST_NOVELS_DIR=%TEST_DIR%\novels"

mkdir "%TEST_DIR%"
mkdir "%TEST_HISTORY_DIR%"
mkdir "%TEST_NOVELS_DIR%"
mkdir "%TEST_NOVELS_DIR%\Active Novels"
mkdir "%TEST_NOVELS_DIR%\Archived Novels"

echo  %GREEN%  Created test workspace: %TEST_DIR%%RESET%
echo  %GREEN%  Test history: %TEST_HISTORY_DIR%%RESET%
echo  %GREEN%  Test novels: %TEST_NOVELS_DIR%%RESET%

:: 3. CHECK SCRIPT FILE
if not exist "epub_project_manager.py" (
    echo.
    echo  %RED%[ERROR] Script file missing!%RESET%
    echo  %WHITE%Could not find: %YELLOW%epub_project_manager.py%RESET%
    pause
    exit
)

:: 4. INSTALL REQUIREMENTS (Hidden unless error)
echo  %BLUE%[%time:~0,8%] %MAGENTA%Verifying Libraries (Silent)...%RESET%
pip install ebooklib beautifulsoup4 edge-tts moviepy pillow pyttsx3 >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo  %RED%[WARNING] Library install had issues. Trying to run anyway...%RESET%
) else (
    echo  %BLUE%[%time:~0,8%] %GREEN%Libraries Verified.%RESET%
)

:: ============================================================
::                     LAUNCH SEQUENCE
:: ============================================================
echo.
echo  %YELLOW%--------------------------------------------------------%RESET%
echo  %GREEN%   READY TO START TEST MODE. LAUNCHING ENGINE...%RESET%
echo  %YELLOW%--------------------------------------------------------%RESET%
echo.

:: Set environment variables to override default paths
set "EPUB_TEST_MODE=1"
set "EPUB_HISTORY_DIR=%CD%\%TEST_HISTORY_DIR%"
set "EPUB_NOVELS_DIR=%CD%\%TEST_NOVELS_DIR%"

:: Convert backslashes to forward slashes for Python argparse
set "HISTORY_DIR_PYTHON=%EPUB_HISTORY_DIR:\=/%"
set "NOVELS_DIR_PYTHON=%EPUB_NOVELS_DIR:\=/%"

:: Run the Python Script with test mode flag
python epub_project_manager.py --test-mode --history-dir "%HISTORY_DIR_PYTHON%" --novels-dir "%NOVELS_DIR_PYTHON%"

:: End State
echo.
echo  %YELLOW%========================================================%RESET%
echo  %WHITE%   Test Execution Finished.%RESET%
echo  %YELLOW%========================================================%RESET%
echo.
echo  %BLUE%  Test data location: %TEST_DIR%%RESET%
echo  %YELLOW%  You can delete this folder to clean up test data.%RESET%
echo.

:: Ask if user wants to clean up test data
set /p CLEANUP="  Do you want to delete test data now? (y/n, default n): "
if /i "%CLEANUP%"=="y" (
    echo.
    echo  %YELLOW%  Cleaning up test data...%RESET%
    rd /s /q "%TEST_DIR%" 2>nul
    if exist "%TEST_DIR%" (
        echo  %RED%  Could not delete test folder (files may be in use)%RESET%
        echo  %YELLOW%  Please delete manually: %TEST_DIR%%RESET%
    ) else (
        echo  %GREEN%  Test data cleaned successfully!%RESET%
    )
)

echo.
echo  %RED%========================================================%RESET%
pause
