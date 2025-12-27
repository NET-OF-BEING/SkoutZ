#!/bin/bash
# SkoutZ Launcher - Professional Marketing Automation GUI

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/venv"
PYTHON="$VENV/bin/python3"

# ASCII Art Banner
cat << "EOF"

  ███████╗██╗  ██╗ ██████╗ ██╗   ██╗████████╗███████╗
  ██╔════╝██║ ██╔╝██╔═══██╗██║   ██║╚══██╔══╝╚══███╔╝
  ███████╗█████╔╝ ██║   ██║██║   ██║   ██║     ███╔╝
  ╚════██║██╔═██╗ ██║   ██║██║   ██║   ██║    ███╔╝
  ███████║██║  ██╗╚██████╔╝╚██████╔╝   ██║   ███████╗
  ╚══════╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝    ╚═╝   ╚══════╝

  Marketing Automation Pro v2.0
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF

# Check venv exists
if [ ! -d "$VENV" ]; then
    echo "❌ Error: Virtual environment not found at $VENV"
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV"

    echo "📥 Installing dependencies..."
    "$PYTHON" -m pip install --upgrade pip
    "$PYTHON" -m pip install selenium webdriver-manager

    echo "✅ Setup complete!"
fi

# Launch GUI
echo "🚀 Launching SkoutZ GUI..."
cd "$SCRIPT_DIR"
exec "$PYTHON" "$SCRIPT_DIR/skoutz_gui.py" "$@"
