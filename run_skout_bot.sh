#!/bin/bash
# SKOUT Bot Launcher - uses virtual environment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/venv"
PYTHON="$VENV/bin/python3"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"

# Check venv exists
if [ ! -d "$VENV" ]; then
    echo "Virtual environment not found; creating one..."
    python3 -m venv "$VENV"
fi

if ! "$PYTHON" -c "import selenium, webdriver_manager" >/dev/null 2>&1; then
    echo "Installing dependencies..."
    "$PYTHON" -m pip install --upgrade pip --quiet
    "$PYTHON" -m pip install -r "$REQUIREMENTS" --quiet
fi

# Run the bot
exec "$PYTHON" "$SCRIPT_DIR/SKOUT_MESSAGE_BOT.py" "$@"
