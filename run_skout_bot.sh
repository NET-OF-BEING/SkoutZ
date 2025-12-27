#!/bin/bash
# SKOUT Bot Launcher - uses virtual environment

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/venv"
PYTHON="$VENV/bin/python3"

# Check venv exists
if [ ! -d "$VENV" ]; then
    echo "Error: Virtual environment not found. Run: python3 -m venv venv"
    exit 1
fi

# Run the bot
exec "$PYTHON" "$SCRIPT_DIR/SKOUT_MESSAGE_BOT.py" "$@"
