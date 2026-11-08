@echo off
REM Double-click this file (Windows) to open the 988 Training Insights dashboard.
REM First run: creates a private Python environment and installs packages (~2-5 min).
REM Later runs: opens in a few seconds. Close this window to stop the dashboard.
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (set PY=py -3) else (set PY=python)
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>nul
if errorlevel 1 (
  echo Python 3.9 or newer is needed. Install it from https://www.python.org/downloads/
  echo During install, tick "Add python.exe to PATH". Then try again.
  pause
  exit /b 1
)

if not exist .venv\Scripts\python.exe (
  echo First-time setup: creating .venv ...
  %PY% -m venv .venv
)
if not exist .venv\installed.txt (
  echo Installing packages (one time)...
  .venv\Scripts\python -m pip install --quiet --upgrade pip
  .venv\Scripts\python -m pip install --quiet -r requirements.txt
  echo done> .venv\installed.txt
)

echo Opening the dashboard in your browser (http://localhost:8501) ...
.venv\Scripts\python -m streamlit run app.py --browser.gatherUsageStats false
pause
