@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0.."
TITLE Fanfiction Legend Manager [SOURCE MODE]

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
::                     THE RAINBOW BANNER
:: ============================================================
echo.
echo  %RED%========================================================%RESET%
echo  %YELLOW%      ______    __  ______  _______  __  __________
echo  %GREEN%     / __/  ^|  /  ^|/  /  ^|/  / _  ^|/  ^|/  /  _/  _/
echo  %BLUE%    / _/ / /__/ /^_/ / /^_/ / __ / /^_/ /_// // /  
echo  %MAGENTA%   /___/____/_/  /_/_/  /_/_/ ^|_/_/  /_/___/___/   
echo.
echo  %RED%            FANFICTION LEGEND AUTOMATION%RESET%
echo  %YELLOW%            [DEVELOPMENT SOURCE MODE]%RESET%
echo  %RED%========================================================%RESET%
echo.

:: ============================================================
::              PREVENT BYTECODE CACHE (CRITICAL!)
:: ============================================================
echo  %BLUE%[%time:~0,8%] %MAGENTA%Configuring Python for source execution...%RESET%

REM Prevent Python from writing .pyc files
set PYTHONDONTWRITEBYTECODE=1

REM Ensure Python uses source files
set PYTHONPYCACHEPREFIX=NUL

echo  %GREEN%[%time:~0,8%] Source mode enabled - changes will be reflected immediately%RESET%
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

:: 2. CREATE FOLDERS
if not exist "_NEW_EPUBS_HERE" (
    echo  %BLUE%[%time:~0,8%] %YELLOW%Creating Input Zone...%RESET%
    mkdir "_NEW_EPUBS_HERE"
)

:: 3. CHECK SCRIPT FILE
if not exist "epub_project_manager.py" (
    echo.
    echo  %RED%[ERROR] Script file missing!%RESET%
    echo  %WHITE%Could not find: %YELLOW%epub_project_manager.py%RESET%
    pause
    exit
)

:: 4. CHECK FOR EXECUTABLE (WARNING)
if exist "dist\epub_project_manager.exe" (
    echo  %RED%[%time:~0,8%] WARNING: Compiled executable detected!%RESET%
    echo  %YELLOW%   This script will run from SOURCE, not the .exe%RESET%
    echo  %WHITE%   If you want to use the .exe, run it directly instead.%RESET%
    echo.
)

:: 5. INSTALL REQUIREMENTS (Hidden unless error)
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
echo  %GREEN%   READY TO START. LAUNCHING ENGINE FROM SOURCE...%RESET%
echo  %YELLOW%--------------------------------------------------------%RESET%
echo.

:: Run the Python Script with -B flag (no bytecode)
python -B epub_project_manager.py

:: End State
echo.
echo  %RED%========================================================%RESET%
echo  %WHITE%   Execution Finished.%RESET%
echo  %RED%========================================================%RESET%
pause
