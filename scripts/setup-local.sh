#!/bin/bash
# Neighborhood BBS - Local Setup Script for macOS and Linux
# This script automates the setup process

set -e  # Exit on error

COLOR_CYAN='\033[0;36m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_GRAY='\033[0;37m'
COLOR_RESET='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo ""
echo -e "${COLOR_CYAN}╔══════════════════════════════════════════╗${COLOR_RESET}"
echo -e "${COLOR_CYAN}║  Neighborhood BBS - Local Setup          ║${COLOR_RESET}"
echo -e "${COLOR_CYAN}╚══════════════════════════════════════════╝${COLOR_RESET}"
echo ""

# Check Python
echo -e "${COLOR_YELLOW}1️⃣  Checking Python...${COLOR_RESET}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} $PYTHON_VERSION"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1)
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} $PYTHON_VERSION"
else
    echo -e "${COLOR_RED}✗ Python not found${COLOR_RESET}"
    echo "  Install Python 3.10+ from: https://www.python.org/downloads/"
    exit 1
fi

cd "$PROJECT_ROOT"
echo "  Working directory: $PROJECT_ROOT"
echo ""

# Create virtual environment
echo -e "${COLOR_YELLOW}2️⃣  Setting up virtual environment...${COLOR_RESET}"

PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

if [ ! -d "venv" ]; then
    echo "  Creating venv..."
    $PYTHON_CMD -m venv venv
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} Virtual environment created"
else
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} Virtual environment already exists"
fi

# Activate virtual environment
echo "  Activating venv..."
source venv/bin/activate

echo -e "${COLOR_GREEN}✓${COLOR_RESET} Virtual environment activated"
echo ""

# Install dependencies
echo -e "${COLOR_YELLOW}3️⃣  Installing dependencies...${COLOR_RESET}"

echo "  Installing from requirements.txt..."
pip install -q --upgrade pip
pip install -r requirements.txt -q
echo -e "${COLOR_GREEN}✓${COLOR_RESET} Dependencies installed"

echo "  Installing dev dependencies..."
pip install -r requirements-dev.txt -q
echo -e "${COLOR_GREEN}✓${COLOR_RESET} Dev dependencies installed"
echo ""

# Create directories
echo -e "${COLOR_YELLOW}4️⃣  Creating directories...${COLOR_RESET}"

mkdir -p data logs data/backups
echo -e "${COLOR_GREEN}✓${COLOR_RESET} Directories created"
echo ""

# Create .env file
echo -e "${COLOR_YELLOW}5️⃣  Configuring environment...${COLOR_RESET}"

if [ ! -f ".env" ]; then
    echo "  Creating .env file..."
    SECRET=$(openssl rand -hex 16)
    cat > .env << EOF
# Neighborhood BBS - Local Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=$SECRET
DATABASE_PATH=data/neighborhood_bbs.db
LOG_PATH=logs/
PORT=8080
HOST=127.0.0.1
LOG_LEVEL=INFO
EOF
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} Created .env with default settings"
else
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} .env already exists"
fi
echo ""

# Initialize database
echo -e "${COLOR_YELLOW}6️⃣  Initializing database...${COLOR_RESET}"

if [ ! -f "data/neighborhood_bbs.db" ]; then
    echo "  Creating database..."
    python scripts/init-db-local.py > /dev/null
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} Database created"
else
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} Database already exists"
fi
echo ""

# Create admin user
echo -e "${COLOR_YELLOW}7️⃣  Admin account setup...${COLOR_RESET}"

ADMIN_EXISTS=$(python -c "
import sqlite3
try:
    conn = sqlite3.connect('data/neighborhood_bbs.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM admin_users WHERE username = \`admin\`')
    print(cursor.fetchone()[0] > 0)
except:
    print(False)
" 2>/dev/null)

if [ "$ADMIN_EXISTS" = "False" ] || [ -z "$ADMIN_EXISTS" ]; then
    echo "  No admin user found. Creating..."
    echo ""
    python scripts/create_admin_user.py
    echo ""
else
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} Admin user already exists"
fi
echo ""

# Final summary
echo -e "${COLOR_CYAN}╔══════════════════════════════════════════╗${COLOR_RESET}"
echo -e "${COLOR_GREEN}║  ✓ Setup Complete!                      ║${COLOR_RESET}"
echo -e "${COLOR_CYAN}╚══════════════════════════════════════════╝${COLOR_RESET}"
echo ""
echo -e "${COLOR_CYAN}🚀 Next steps:${COLOR_RESET}"
echo "   1. Run the app:"
echo -e "      ${COLOR_YELLOW}./scripts/run-local.sh${COLOR_RESET}"
echo ""
echo "   2. Open browser:"
echo -e "      ${COLOR_YELLOW}http://localhost:8080${COLOR_RESET}"
echo ""
echo "   3. Login:"
echo "      Username: admin"
echo "      Password: (as you set above)"
echo ""
echo -e "${COLOR_CYAN}📚 Documentation:${COLOR_RESET}"
echo "   • Local setup: LOCAL_SETUP.md"
echo "   • Admin panel: docs/ADMIN_PANEL.md"
echo ""
