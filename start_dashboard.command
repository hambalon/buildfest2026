#!/bin/bash
# Double-click this file (macOS) to open the 988 Training Insights dashboard.
# First run: creates a private Python environment and installs packages (~2-5 min).
# Later runs: opens in a few seconds. Close the Terminal window to stop the dashboard.
set -e
cd "$(dirname "$0")"

PY=""
for c in python3.13 python3.12 python3.11 python3.10 python3 python3.9; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "Python 3.9 or newer is needed. Install it from https://www.python.org/downloads/ and try again."
  read -r -p "Press Enter to close."; exit 1
fi

if [ ! -x .venv/bin/python ]; then
  echo "First-time setup: creating .venv with $PY ..."
  "$PY" -m venv .venv
fi
if [ ! -f .venv/.installed ] || [ requirements.txt -nt .venv/.installed ]; then
  echo "Installing packages (one time)..."
  .venv/bin/python -m pip install --quiet --upgrade pip
  .venv/bin/python -m pip install --quiet -r requirements.txt
  touch .venv/.installed
fi

echo "Opening the dashboard in your browser (http://localhost:8501) ..."
exec .venv/bin/python -m streamlit run app.py --browser.gatherUsageStats false
