@echo off
cd /d "%~dp0"
python -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
call npm install
if errorlevel 1 goto fail
.venv\Scripts\python.exe prepare.py
if errorlevel 1 goto fail
echo Setup complete. Run login.cmd, then start.cmd.
pause
exit /b 0
:fail
echo Setup failed. Copy the error above for troubleshooting.
pause
exit /b 1
