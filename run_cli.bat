@echo off
setlocal

cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"
set "AGENT_BACKEND=cli"
set "PYTHON_EXE=C:\Users\yixin\AppData\Local\Programs\Python\Python313\python.exe"

if "%~1"=="" (
    echo Usage: run_cli.bat "your task here"
    echo Example: run_cli.bat "Build a command-line todo app with unit tests"
    exit /b 1
)

"%PYTHON_EXE%" -m agent_system --task %*

endlocal
