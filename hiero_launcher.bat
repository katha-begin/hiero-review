@echo off
REM ============================================
REM Hiero Review Tool - Custom Launcher
REM ============================================
REM Usage:
REM   hiero_launcher.bat              - Launch with default project
REM   hiero_launcher.bat SWA          - Launch with SWA project config
REM   hiero_launcher.bat --list       - List available projects
REM ============================================

setlocal enabledelayedexpansion

REM Get the directory where this batch file is located
SET SCRIPT_DIR=%~dp0

REM Check if Python is available
where python >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7+ and add it to your PATH
    pause
    exit /b 1
)

REM Set default project or use command line argument
SET PROJECT_ARG=%1
IF "%PROJECT_ARG%"=="" SET PROJECT_ARG=default

REM Handle special arguments
IF "%PROJECT_ARG%"=="--list" (
    python "%SCRIPT_DIR%scripts\hiero_launcher.py" --list
    pause
    exit /b 0
)

IF "%PROJECT_ARG%"=="--help" (
    python "%SCRIPT_DIR%scripts\hiero_launcher.py" --help
    pause
    exit /b 0
)

REM Launch Hiero with the specified project
echo Launching Hiero with project: %PROJECT_ARG%
python "%SCRIPT_DIR%scripts\hiero_launcher.py" --project %PROJECT_ARG%

IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo Failed to launch Hiero. Check the error message above.
    pause
    exit /b 1
)

exit /b 0

