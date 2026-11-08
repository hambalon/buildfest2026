#!/bin/bash
# Double-click this file (macOS) to open the 988 Training Insights dashboard.
# First run: creates a private Python environment in .venv and installs packages (~2-5 min).
# Later runs: opens in a few seconds. Close the Terminal window to stop the dashboard.
cd "$(dirname "$0")" || exit 1

fail() {
  echo
  echo "Setup failed: $1"
  echo "Scroll up to read the error. To start over, delete the .venv folder and run this again."
  read -r -p "Press Enter to close."
  exit 1
}

PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3 python3.9; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "Python 3.9 or newer is needed. Install it from https://www.python.org/downloads/ and run this again."
  read -r -p "Press Enter to close."; exit 1
fi

if [ ! -x .venv/bin/python ]; then
  echo "First-time setup: creating a private Python environment in .venv with $PY ..."
  "$PY" -m venv .venv || fail "could not create .venv"
fi
if [ ! -f .venv/.installed ] || [ requirements.txt -nt .venv/.installed ]; then
  echo "Installing packages (one time, 2-5 minutes)..."
  .venv/bin/python -m pip install --quiet --upgrade pip
  .venv/bin/python -m pip install -r requirements.txt || fail "package install failed"
  touch .venv/.installed
fi

echo
echo "Starting the dashboard. Your browser opens at http://localhost:8501 in a few seconds."
echo "If it doesn't, open the 'Local URL' printed below. Close this window to stop."
echo
# Headless mode skips Streamlit's first-run e-mail prompt; open the browser ourselves.
( sleep 5; open "http://localhost:8501" ) &
.venv/bin/python -m streamlit run app.py --server.headless true --browser.gatherUsageStats false
echo
read -r -p "The dashboard has stopped. Press Enter to close."
