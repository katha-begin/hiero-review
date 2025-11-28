@echo off
REM Hiero Review Tool Installer - Windows
REM ======================================

echo Hiero Review Tool Installer
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Run installer
python "%~dp0install.py" install %*

if errorlevel 1 (
    echo.
    echo Installation failed.
    pause
    exit /b 1
)

echo.
echo Installation successful!
pause

