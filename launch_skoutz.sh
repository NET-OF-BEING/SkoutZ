#!/bin/bash
# SkoutZ Launcher - Professional Marketing Automation GUI

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/venv"
PYTHON="$VENV/bin/python3"

# ANSI Color Codes (SKOUT.com theme)
PURPLE='\033[38;5;141m'    # Primary Purple
CYAN='\033[38;5;51m'       # Accent
GREEN='\033[38;5;82m'      # Success
YELLOW='\033[38;5;228m'    # Highlight
RESET='\033[0m'
BOLD='\033[1m'

# Clear screen for clean display
clear

# SKOUT Logo ASCII Art with Colors
echo -e "${PURPLE}${BOLD}"
cat << "EOF"
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     ███████╗██╗  ██╗ ██████╗ ██╗   ██╗████████╗███████╗ ║
    ║     ██╔════╝██║ ██╔╝██╔═══██╗██║   ██║╚══██╔══╝╚══███╔╝ ║
    ║     ███████╗█████╔╝ ██║   ██║██║   ██║   ██║     ███╔╝  ║
    ║     ╚════██║██╔═██╗ ██║   ██║██║   ██║   ██║    ███╔╝   ║
    ║     ███████║██║  ██╗╚██████╔╝╚██████╔╝   ██║   ███████╗ ║
    ║     ╚══════╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝    ╚═╝   ╚══════╝ ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${RESET}"

echo -e "${CYAN}           Marketing Automation Pro ${BOLD}v2.0${RESET}"
echo -e "${PURPLE}    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""
echo -e "${YELLOW}    🎮 Browse Profiles  |  Match Game Automation${RESET}"
echo ""

# Check venv exists
if [ ! -d "$VENV" ]; then
    echo -e "${YELLOW}❌ Virtual environment not found${RESET}"
    echo -e "${CYAN}📦 Creating virtual environment...${RESET}"
    python3 -m venv "$VENV"

    echo -e "${CYAN}📥 Installing dependencies...${RESET}"
    "$PYTHON" -m pip install --upgrade pip --quiet
    "$PYTHON" -m pip install selenium webdriver-manager --quiet

    echo -e "${GREEN}✅ Setup complete!${RESET}"
    echo ""
fi

# Launch GUI
echo -e "${GREEN}🚀 Launching SkoutZ GUI...${RESET}"
echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
echo ""

cd "$SCRIPT_DIR"
exec "$PYTHON" "$SCRIPT_DIR/skoutz_gui.py" "$@"
