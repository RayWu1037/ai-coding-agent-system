@echo off
setlocal

cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"
set "AGENT_BACKEND=cli"
set "PYTHON_EXE=C:\Users\yixin\AppData\Local\Programs\Python\Python313\python.exe"
set "FAST_FLAG="
set "DOCTOR_FLAG="
set "DOCTOR_LIVE_FLAG="
set "DOCTOR_OUTPUT_FLAG="

if /I "%~1"=="--fast" (
    set "FAST_FLAG=--fast"
    shift
)

if /I "%~1"=="--doctor" (
    set "DOCTOR_FLAG=--doctor"
    shift
)

if /I "%~1"=="--live" (
    set "DOCTOR_LIVE_FLAG=--doctor-live"
    shift
)

if /I "%~1"=="--output" (
    if "%~2"=="" (
        echo Error: --output requires a file path.
        exit /b 1
    )
    set "DOCTOR_OUTPUT_FLAG=--doctor-output \"%~2\""
    shift
    shift
)

if defined DOCTOR_FLAG (
    "%PYTHON_EXE%" -m agent_system %DOCTOR_FLAG% %DOCTOR_LIVE_FLAG% %DOCTOR_OUTPUT_FLAG%
    exit /b %ERRORLEVEL%
)

if "%~1"=="" (
    echo Usage: run_cli.bat [--fast] "your task here"
    echo Usage: run_cli.bat --doctor [--live] [--output report.md^|report.json]
    echo Example: run_cli.bat "Build a command-line todo app with unit tests"
    echo Example: run_cli.bat --fast "Write a minimal Python project for an Obsidian-style knowledge-base ingester"
    echo Example: run_cli.bat --doctor --live --output reports\doctor.md
    exit /b 1
)

"%PYTHON_EXE%" -m agent_system %FAST_FLAG% --task %*

endlocal
