@echo off
setlocal

cd /d "%~dp0"
set "PYTHONPATH=%CD%\src"
set "AGENT_BACKEND=cli"
set "PYTHON_EXE=C:\Users\yixin\AppData\Local\Programs\Python\Python313\python.exe"
set "PORT=8000"

if not "%~1"=="" (
    set "PORT=%~1"
)

echo Starting Agent UI on http://127.0.0.1:%PORT%
"%PYTHON_EXE%" -m agent_system.ui --port %PORT%

endlocal
