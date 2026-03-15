#!/bin/bash
# Neighborhood BBS - Local Development Launcher
# Activates venv and runs the Flask development server

set -e

COLOR_CYAN='\033[0;36m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
COLOR_GRAY='\033[0;37m'
COLOR_RESET='\033[0m'

# Parse arguments
PORT=8080
HOST="127.0.0.1"
NETWORK=false
DEBUG=true
NO_DEBUG=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --network)
            NETWORK=true
            HOST="0.0.0.0"
            shift
            ;;
        --no-debug)
            NO_DEBUG=true
            DEBUG=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo -e "${COLOR_CYAN}╔════════════════════════════════════════════════╗${COLOR_RESET}"
echo -e "${COLOR_CYAN}║  Neighborhood BBS - Development Server        ║${COLOR_RESET}"
echo -e "${COLOR_CYAN}╚════════════════════════════════════════════════╝${COLOR_RESET}"
echo ""
echo -e "📁 Project root: ${COLOR_GRAY}$PROJECT_ROOT${COLOR_RESET}"
echo ""

# Check if venv exists
if [ ! -f "venv/bin/activate" ]; then
    echo -e "${COLOR_RED}❌ Virtual environment not found!${COLOR_RESET}"
    echo "   Run setup first: ./scripts/setup-local.sh"
    exit 1
fi

# Activate virtual environment
echo -e "${COLOR_CYAN}🔧 Activating virtual environment...${COLOR_RESET}"
source venv/bin/activate

# Check if database exists
if [ ! -f "data/neighborhood_bbs.db" ]; then
    echo -e "${COLOR_YELLOW}⚠️  Database not found!${COLOR_RESET}"
    echo "   Initializing database..."
    python scripts/init-db-local.py > /dev/null
    echo -e "${COLOR_GREEN}✓${COLOR_RESET} Database initialized"
fi

# Set network binding if requested
if [ "$NETWORK" = true ]; then
    echo -e "${COLOR_YELLOW}🌐 Network binding enabled (accept external connections)${COLOR_RESET}"
    echo "   Find your IP: ifconfig | grep inet"
    echo ""
fi

# Prepare environment variables
export FLASK_APP="src/main.py"
export FLASK_ENV="development"

if [ "$NO_DEBUG" = true ]; then
    export FLASK_DEBUG="False"
    echo -e "${COLOR_YELLOW}🔧 Debug mode disabled${COLOR_RESET}"
else
    export FLASK_DEBUG="True"
    echo -e "${COLOR_CYAN}🔧 Debug mode enabled (auto-reload on file changes)${COLOR_RESET}"
fi

echo ""
echo -e "${COLOR_GREEN}🚀 Starting Neighborhood BBS...${COLOR_RESET}"
echo "   Host: $HOST"
echo "   Port: $PORT"
echo ""
echo -e "${COLOR_CYAN}================================================${COLOR_RESET}"
echo -e "${COLOR_GREEN}✓ Server running!${COLOR_RESET}"
echo ""
echo -e "${COLOR_CYAN}📖 Access here:${COLOR_RESET}"

if [ "$NETWORK" = true ]; then
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    echo "   Local:    ${COLOR_GREEN}http://127.0.0.1:$PORT${COLOR_RESET}"
    echo "   Network:  ${COLOR_GREEN}http://$LOCAL_IP:$PORT${COLOR_RESET}"
else
    echo "   ${COLOR_GREEN}http://$HOST:$PORT${COLOR_RESET}"
fi

echo ""
echo -e "${COLOR_CYAN}🔐 Admin panel:${COLOR_RESET}"
echo -e "   ${COLOR_GREEN}http://$HOST:$PORT/admin/login${COLOR_RESET}"
echo ""
echo -e "${COLOR_CYAN}📊 API docs:${COLOR_RESET}"
echo -e "   ${COLOR_GREEN}http://$HOST:$PORT/api/docs${COLOR_RESET}"
echo ""
echo -e "${COLOR_YELLOW}⏹️  Press CTRL+C to stop the server${COLOR_RESET}"
echo -e "${COLOR_CYAN}================================================${COLOR_RESET}"
echo ""

# Run the Flask development server
python "src/main.py" --host "$HOST" --port "$PORT" $([ "$DEBUG" = false ] && echo "--no-debug" || echo "")

# Cleanup
echo ""
echo -e "${COLOR_YELLOW}🛑 Server stopped.${COLOR_RESET}"
