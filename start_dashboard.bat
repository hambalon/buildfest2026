@echo off
setlocal
REM Double-click this file (Windows) to open the 988 Training Insights dashboard.
REM First run: creates a private Python environment in .venv and installs packages (2-5 min).
REM The window stays open on every error so the message can be read.
REM Note for editors: no parentheses inside IF blocks (they break batch parsing); use GOTO labels.
title 988 Training Insights
cd /d "%~dp0"

REM ---- 1. Find Python 3.9 or newer ------------------------------------------
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY goto nopython
%PY% -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" >nul 2>nul
if errorlevel 1 goto nopython

REM ---- 2. Create the private environment once --------------------------------
if exist ".venv\Scripts\python.exe" goto install
echo First-time setup: creating a private Python environment in the .venv folder...
%PY% -m venv .venv
if errorlevel 1 goto fail

REM ---- 3. Install packages once (marker written only if the install succeeds) --
:install
if exist ".venv\installed.txt" goto run
echo Installing packages, one time only. This takes 2-5 minutes...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo ok> ".venv\installed.txt"

REM ---- 4. Start the dashboard ------------------------------------------------
:run
echo.
echo Starting the dashboard. Your browser opens at http://localhost:8501 in a few seconds.
echo If it does not, open the "Local URL" printed below in your browser.
echo Keep this window open while you use the dashboard. Close it to stop.
echo.
REM Open the browser after a short delay; headless mode skips Streamlit's first-run e-mail prompt.
start "" /b powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 6; Start-Process 'http://localhost:8501'"
".venv\Scripts\python.exe" -m streamlit run app.py --server.headless true --browser.gatherUsageStats false
echo.
echo The dashboard has stopped. If you saw an error above, send a screenshot of this window.
pause
exit /b 0

:nopython
echo.
echo Python 3.9 or newer was not found on this computer.
echo   1. Download it from https://www.python.org/downloads/
echo   2. On the FIRST installer screen, tick "Add python.exe to PATH", then Install.
echo   3. Double-click start_dashboard.bat again.
echo If Windows opened the Microsoft Store instead, close it and use python.org.
echo.
pause
exit /b 1

:fail
echo.
echo Setup failed. Scroll up to read the error message.
echo To start over, delete the .venv folder next to this file and double-click this file again.
echo.
pause
exit /b 1
