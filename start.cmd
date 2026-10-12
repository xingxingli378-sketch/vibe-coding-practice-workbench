@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Please run setup.cmd first.
  pause
  exit /b 1
)
.venv\Scripts\python.exe prepare.py
if errorlevel 1 goto fail
.venv\Scripts\python.exe server.py --open
if errorlevel 1 goto fail
exit /b 0
:fail
pause
exit /b 1
