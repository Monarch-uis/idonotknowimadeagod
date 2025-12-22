@echo off
REM ============================================
REM Clean PyInstaller Build Artifacts
REM ============================================
echo.
echo ====================================
echo   Cleaning Build Artifacts
echo ====================================
echo.

REM Remove build directory
if exist build (
    echo Removing build/ directory...
    rd /s /q build 2>nul
    if exist build (
        echo   WARNING: Could not remove build/ - files may be in use
    ) else (
        echo   OK Removed build/
    )
) else (
    echo   OK build/ does not exist
)

echo.

REM Remove dist directory
if exist dist (
    echo Removing dist/ directory...
    rd /s /q dist 2>nul
    if exist dist (
        echo   WARNING: Could not remove dist/ - files may be in use
    ) else (
        echo   OK Removed dist/
    )
) else (
    echo   OK dist/ does not exist
)

echo.
echo ====================================
echo   Build Artifacts Cleaned!
echo ====================================
echo.
echo PyInstaller build files removed.
echo.
pause
