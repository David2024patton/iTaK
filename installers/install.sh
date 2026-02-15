#!/bin/bash
# iTaK Universal Installer
# Auto-detects OS (Linux/macOS/WSL) and routes to appropriate installer

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 iTaK Universal Installer"
echo "════════════════════════════════════════"
echo ""
echo "Detecting environment..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect WSL
if grep -qi microsoft /proc/version 2>/dev/null || grep -qi microsoft /proc/sys/kernel/osrelease 2>/dev/null; then
    # Running in WSL
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        WSL_VERSION="WSL 2"
        if grep -qi "WSL1" /proc/version 2>/dev/null; then
            WSL_VERSION="WSL 1"
        fi
        echo -e "${GREEN}✅ Detected: $WSL_VERSION ($NAME)${NC}"
    else
        echo -e "${GREEN}✅ Detected: WSL${NC}"
    fi
    echo ""
    
# Detect macOS
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_VERSION=$(sw_vers -productVersion)
    ARCH=$(uname -m)
    if [[ "$ARCH" == "arm64" ]]; then
        echo -e "${GREEN}✅ Detected: macOS $OS_VERSION (Apple Silicon ARM)${NC}"
    else
        echo -e "${GREEN}✅ Detected: macOS $OS_VERSION (Intel x86_64)${NC}"
    fi
    echo ""
    
# Detect Linux
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        ARCH=$(uname -m)
        echo -e "${GREEN}✅ Detected: $NAME $VERSION_ID ($ARCH)${NC}"
    else
        echo -e "${GREEN}✅ Detected: Linux${NC}"
    fi
    echo ""
    
else
    echo "❌ Unsupported OS: $OSTYPE"
    echo ""
    echo "iTaK supports:"
    echo "  - Linux (Ubuntu, Debian, Fedora, etc.)"
    echo "  - macOS (Intel and Apple Silicon)"
    echo "  - WSL (Windows Subsystem for Linux)"
    echo ""
    echo "For Windows, please use: install.bat"
    exit 1
fi

# Prompt for installation type
echo "📦 Choose installation method:"
echo ""
echo "  1. Prerequisites Only (Docker, Python, Git)"
echo "  2. Quick Install (Minimal - iTaK only)"
echo "  3. Full Stack (iTaK + Neo4j + SearXNG + Weaviate)"
echo ""
read -p "Choose (1/2/3, default=2): " -n 1 -r
echo ""
echo ""

case $REPLY in
    1)
        echo "🔧 Installing prerequisites..."
        "$SCRIPT_DIR/install-prerequisites.sh"
        ;;
    3)
        echo "🚀 Installing full stack..."
        "$SCRIPT_DIR/install-full-stack.sh"
        ;;
    *)
        echo "⚡ Running quick install..."
        "$SCRIPT_DIR/quick-install.sh"
        ;;
esac
